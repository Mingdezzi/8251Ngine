import pygame
import random
from engine.core.node import Node
from engine.graphics.block import Block3D
from engine.physics.collision import CollisionWorld
from engine.core.math_utils import IsoMath
from engine.graphics.lighting import LightSource, DirectionalLight
from engine.core.input import Input
from game.scripts.entity import GameEntity
from engine.physics.fov import FOVSystem
from engine.core.app import App

class TestScene(Node):
    def _ready(self):
        print("8251Ngine 5.0 - PRO Features Ready!")
        self.collision_world = CollisionWorld()
        self.fov_system = FOVSystem(self.collision_world)
        self.blocks = {} 
        
        # --- UI Setup ---
        from engine.ui.gui import Control, Label, Panel
        ui_root = Control(0, 0, 1280, 720)
        panel = Panel(10, 10, 250, 150)
        self.lbl_time = Label("Time: 00:00", 20, 20)
        self.lbl_phase = Label("Phase: DAY", 20, 50)
        self.lbl_cam = Label("Cam: Following", 20, 80, color=(100, 255, 100))
        self.lbl_state = Label("State: WALK", 20, 110, color=(200, 200, 255))
        panel.add_child(self.lbl_time); panel.add_child(self.lbl_phase)
        panel.add_child(self.lbl_cam); panel.add_child(self.lbl_state)
        ui_root.add_child(panel)
        
        help_lbl = Label("[C] Toggle Camera  [Shift] Run  [Ctrl] Crouch  [L/R-Click] Edit", 10, 680, 16)
        ui_root.add_child(help_lbl)
        if App.instance: App.instance.set_ui(ui_root)
        
        # --- 환경 광원 ---
        self.sun = DirectionalLight(name="Sun", intensity=0.3)
        self.add_child(self.sun)
        if App.instance: App.instance.lighting.set_directional_light(self.sun)
        
        # 1. 월드 바닥
        for x in range(20):
            for y in range(20):
                tile = Block3D(name=f"Tile_{x}_{y}", size_z=0.05, color=(40, 70, 40))
                tile.position.x, tile.position.y = x, y
                self.add_child(tile)

        # 2. 장애물
        for _ in range(40):
            wx, wy = random.randint(0, 19), random.randint(0, 19)
            if 1 <= wx <= 3 and 1 <= wy <= 3: continue 
            self._spawn_block(wx, wy)

        # 3. 플레이어
        self.player = GameEntity(name="Player", color=(255, 100, 100))
        self.player.position.x, self.player.position.y = 2, 2
        self.add_child(self.player)
        
        player_light = LightSource(name="PlayerLight", radius=250, color=(255, 200, 100), intensity=0.5)
        self.player.add_child(player_light)

    def _spawn_block(self, x, y):
        if (x, y) in self.blocks: return
        wall = Block3D(name="Wall", size_z=random.uniform(0.5, 2.0), color=(100, 100, 110))
        wall.position.x, wall.position.y = x, y
        self.add_child(wall); self.collision_world.add_static(wall)
        self.blocks[(x, y)] = wall

    def _remove_block(self, x, y):
        if (x, y) in self.blocks:
            wall = self.blocks[(x, y)]; self.remove_child(wall)
            self.collision_world.remove_static(wall); del self.blocks[(x, y)]

    def update(self, dt):
        # --- 캐릭터 컨트롤 ---
        move_x, move_y = Input.get_vector("move_left", "move_right", "move_up", "move_down")
        
        # 속도 상태 결정
        base_speed = 4.0
        state_str = "WALK"
        if Input.is_action_pressed("run"):
            base_speed = 7.0; state_str = "RUN"
        elif Input.is_action_pressed("crouch"):
            base_speed = 2.0; state_str = "CROUCH"
            
        if move_x != 0 or move_y != 0:
            self.player.is_moving = True
            tx = self.player.position.x + move_x * base_speed * dt
            if not self.collision_world.check_collision(pygame.math.Vector3(tx, self.player.position.y, self.player.position.z)):
                self.player.position.x = tx
            ty = self.player.position.y + move_y * base_speed * dt
            if not self.collision_world.check_collision(pygame.math.Vector3(self.player.position.x, ty, self.player.position.z)):
                self.player.position.y = ty

        # 카메라 토글 (탭 하듯이 한번만 입력 받기 위해 App의 이벤트 핸들러가 좋지만, 여기선 간단히)
        if Input.is_action_pressed("toggle_camera"):
            # 토글 로직은 입력 매니저 개선 후 정교하게 다듬을 수 있음
            pass 

        # --- 환경 업데이트 ---
        if App.instance:
            t = App.instance.time
            self.lbl_time.set_text(f"Day {t.day_count} - {int(t.phase_timer)}s")
            self.lbl_phase.set_text(f"Phase: {t.current_phase}")
            self.lbl_state.set_text(f"State: {state_str}")
            # 태양 강도 조절 (밤엔 약하게)
            self.sun.intensity = 0.5 if t.current_phase != 'NIGHT' else 0.05
            
        # FOV
        if App.instance:
            App.instance.fov_polygon = self.fov_system.calculate_fov(self.player.position)

    def _draw(self, renderer):
        # 카메라 상태 업데이트
        if Input.is_action_pressed("toggle_camera"):
            renderer.camera.stop_following()
            self.lbl_cam.set_text("Cam: Free")
            self.lbl_cam.color = (255, 100, 100)
        else:
            ix, iy = IsoMath.cart_to_iso(self.player.position.x, self.player.position.y, 0)
            renderer.camera.follow(ix, iy)
            self.lbl_cam.set_text("Cam: Following")
            self.lbl_cam.color = (100, 255, 100)
            
        super()._draw(renderer)