import pygame
import random
from engine.core.node import Node
from engine.graphics.block import Block3D
from engine.physics.collision import CollisionWorld
from engine.core.math_utils import IsoMath
from engine.graphics.lighting import LightSource, DirectionalLight
from game.scripts.entity import GameEntity
from engine.physics.fov import FOVSystem

class TestScene(Node):
    def _ready(self):
        print("TestScene Ready. Engine services are now injected.")
        self.collision_world = CollisionWorld()
        self.fov_system = FOVSystem(self.collision_world)
        self.blocks = {}
        self.camera_follow = True
        self.player = None
        self.remote_players = {}

        # --- UI Setup ---
        from engine.ui.gui import Control, Label, Panel
        self.ui_root = Control(0, 0, 1280, 720)
        panel = Panel(10, 10, 250, 150)
        self.lbl_time = Label("Time: 00:00", 20, 20)
        self.lbl_phase = Label("Phase: DAY", 20, 50)
        self.lbl_cam = Label("Cam: Following", 20, 80, color=(100, 255, 100))
        self.lbl_state = Label("State: IDLE", 20, 110, color=(200, 200, 255))
        panel.add_child(self.lbl_time); panel.add_child(self.lbl_phase)
        panel.add_child(self.lbl_cam); panel.add_child(self.lbl_state)
        self.ui_root.add_child(panel)
        self.ui_root.add_child(Label("[C] Toggle Camera [Shift] Run", 10, 680, 16))
        
        # --- 환경 광원 ---
        self.sun = DirectionalLight(name="Sun", intensity=0.3)
        self.add_child(self.sun)

        # --- 월드 생성 ---
        self._create_world()

    def _create_world(self):
        for x in range(20):
            for y in range(20):
                tile = Block3D(f"Tile_{x}_{y}", size_z=0.05, color=(40, 70, 40))
                tile.position.x, tile.position.y = x, y
                self.add_child(tile)
        for _ in range(40):
            wx, wy = random.randint(0, 19), random.randint(0, 19)
            if (1 <= wx <= 3 and 1 <= wy <= 3) or (wx, wy) in self.blocks: continue
            self._spawn_block(wx, wy)

    def _spawn_player(self, client_id):
        self.player = GameEntity(name="Player", color=(255, 100, 100), client_id=client_id)
        self.player.position.x, self.player.position.y = 2, 2
        self.add_child(self.player)
        player_light = LightSource("PlayerLight", radius=250, color=(255, 200, 100), intensity=0.5)
        self.player.add_child(player_light)

    def _spawn_block(self, x, y):
        wall = Block3D(f"Wall_{x}_{y}", size_z=random.uniform(0.5, 2.0), color=(100, 100, 110))
        wall.position.x, wall.position.y = x, y
        self.add_child(wall)
        self.collision_world.add_static(wall)
        self.blocks[(x, y)] = wall
    
    def update(self, dt, services):
        input_manager = services["input"]
        network_manager = services["network"]
        app = services["app"]

        # 1. 네트워크 메시지 처리
        if network_manager.client_id and not self.player:
            self._spawn_player(network_manager.client_id)
        
        self._handle_network_messages(network_manager)

        # 2. 로컬 플레이어 입력 및 로직
        state_str = "IDLE"
        if self.player:
            state_str = self._handle_player_input(dt, input_manager, network_manager)
            # FOV 업데이트
            app.fov_polygon = self.fov_system.calculate_fov(self.player.position)

        # 3. 카메라 제어
        if input_manager.is_action_just_pressed("toggle_camera"):
            self.camera_follow = not self.camera_follow
        self._update_camera(services["renderer"])
        
        # 4. 환경 및 UI 업데이트
        self._update_environment(services["time"], services["lighting"], state_str)
        
        super().update(dt, services)
        
    def _handle_network_messages(self, network_manager):
        messages = network_manager.get_messages()
        for msg in messages:
            msg_type = msg.get("type")
            client_id = msg.get("id")
            if not client_id: continue

            if msg_type == "state":
                if self.player and client_id == self.player.client_id: continue

                if client_id not in self.remote_players:
                    remote_player = GameEntity(f"Remote_{client_id}", color=(100, 100, 255), client_id=client_id)
                    self.remote_players[client_id] = remote_player
                    self.add_child(remote_player)
                
                pos = msg.get("pos")
                self.remote_players[client_id].position.x = pos[0]
                self.remote_players[client_id].position.y = pos[1]
                self.remote_players[client_id].is_moving = msg.get("is_moving", False)

            elif msg_type == "disconnect":
                if client_id in self.remote_players:
                    self.remove_child(self.remote_players[client_id])
                    del self.remote_players[client_id]

    def _handle_player_input(self, dt, input_manager, network_manager):
        move_x, move_y = input_manager.get_vector("move_left", "move_right", "move_up", "move_down")
        
        base_speed = 4.0
        state_str = "WALK"
        if input_manager.is_action_pressed("run"):
            base_speed = 7.0; state_str = "RUN"
        
        moved = False
        if move_x != 0 or move_y != 0:
            moved = True
            self.player.is_moving = True
            
            # 충돌 체크 후 이동
            tx = self.player.position.x + move_x * base_speed * dt
            if not self.collision_world.check_collision(pygame.math.Vector3(tx, self.player.position.y, 0)):
                self.player.position.x = tx
            ty = self.player.position.y + move_y * base_speed * dt
            if not self.collision_world.check_collision(pygame.math.Vector3(self.player.position.x, ty, 0)):
                self.player.position.y = ty
        else:
            self.player.is_moving = False

        # 네트워크로 상태 전송
        if network_manager and network_manager.client_id:
            network_manager.send({
                "type": "state",
                "id": self.player.client_id,
                "pos": [self.player.position.x, self.player.position.y],
                "is_moving": self.player.is_moving
            })

        return state_str if moved else "IDLE"
    
    def _update_camera(self, renderer):
        if self.camera_follow and self.player:
            ix, iy = IsoMath.cart_to_iso(self.player.position.x, self.player.position.y, 0)
            renderer.camera.follow(ix, iy)
            self.lbl_cam.set_text("Cam: Following")
            self.lbl_cam.color = (100, 255, 100)
        else:
            renderer.camera.stop_following()
            self.lbl_cam.set_text("Cam: Free")
            self.lbl_cam.color = (255, 100, 100)
    
    def _update_environment(self, time_manager, lighting_manager, state_str):
        self.lbl_time.set_text(f"Day {time_manager.day_count} - {int(time_manager.phase_timer)}s")
        self.lbl_phase.set_text(f"Phase: {time_manager.current_phase}")
        self.lbl_state.set_text(f"State: {state_str}")
        self.sun.intensity = 0.5 if time_manager.current_phase != 'NIGHT' else 0.05
        lighting_manager.set_directional_light(self.sun)
    
    # UI는 App 레벨에서 그려지므로 여기서는 draw 로직 불필요
    # def _draw(self, services):
    #     super()._draw(services)