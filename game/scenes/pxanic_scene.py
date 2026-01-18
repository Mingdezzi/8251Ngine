import pygame
from engine.core.app import App
from engine.core.node import Node
from engine.physics.collision import CollisionWorld
from engine.assets.map_loader import MapLoader
from engine.graphics.tilemap import TileMap
from engine.graphics.block import Block3D
from engine.graphics.wall import WallNode # WallNode 임포트
from engine.core.math_utils import IsoMath
from game.scripts.entity import GameEntity
from engine.graphics.lighting import LightSource, DirectionalLight
from engine.physics.fov import FOVSystem
from engine.ui.gui import Control, Label, Panel, ProgressBar
from engine.graphics.fog_of_war import FogOfWar

class PxAnicScene(Node):
    def _ready(self, services):
        print("--- PxANIC! Zomboid Style Renderer ---")
        app = services.get("app")
        self.collision_world = CollisionWorld()
        self.fov_system = FOVSystem(self.collision_world)
        self.player = None
        self.move_target = None 
        self.block_grid = {}

        # 1. 시야 시스템(FogOfWar) 추가
        self.fog_of_war = FogOfWar(name="FogOfWar")
        self.fog_of_war.update_resolution(app.screen.get_width(), app.screen.get_height())
        self.add_child(self.fog_of_war)

        # 2. 맵 로드 및 노드 생성 (경계 기반)
        map_path = "engine/assets/pxanic_edge_map.json"
        map_data = MapLoader.load_map_data(map_path)
        
        if map_data:
            metadata = {
                "width": map_data.get("width", 100),
                "height": map_data.get("height", 100)
            }
            blocks_data = map_data.get("blocks", [])
            walls_data = map_data.get("walls", {})

            # 바닥과 사물은 TileMap과 Block3D로 생성
            floor_blocks = [b for b in blocks_data if str(b.get("tile_id", ""))[0] == '1']
            object_blocks = [b for b in blocks_data if str(b.get("tile_id", ""))[0] > '2']
            
            floor_map = TileMap(name="FloorMap")
            floor_map.load_from_blocks(floor_blocks, metadata["width"], metadata["height"])
            self.add_child(floor_map)
            
            for b_data in object_blocks:
                node = Block3D(
                    name=b_data.get("name", "Object"), size_z=b_data.get("size_z", 0.6),
                    color=tuple(b_data.get("color", (100, 100, 110))),
                    tile_id=b_data.get("tile_id", None)
                )
                node.position.x, node.position.y, node.position.z = b_data["pos"]
                self.add_child(node)
                gx, gy = int(node.position.x), int(node.position.y)
                self.block_grid[(gx, gy)] = node
                if b_data.get("is_static", True):
                    self.collision_world.add_static(node)
            
            # 새로운 'walls' 데이터에서 WallNode 생성
            for pos_str, wall_types in walls_data.items():
                pos = tuple(map(int, pos_str.strip("()").split(",")))
                for wall_type in wall_types:
                    wall = WallNode(
                        wall_type=wall_type,
                        tile_id=212000000 # 기본 벽돌 ID, 추후 타일 정보 연동
                    )
                    wall.position.x, wall.position.y = pos
                    self.add_child(wall)
                    # self.collision_world.add_static(wall) # 3단계에서 구현

        # 3. 광원 및 플레이어
        self.sun = DirectionalLight(name="Sun", intensity=0.5)
        self.add_child(self.sun)
        self.player = GameEntity(name="Player", clothes_color=(255, 100, 100))
        self.player.position.x, self.player.position.y = 50, 50 
        self.player.status.hp, self.player.status.max_hp = 8, 10
        self.player.status.ap, self.player.status.max_ap = 10, 10
        self.add_child(self.player)
        self.player_light = LightSource("PlayerLight", radius=250)
        self.player.add_child(self.player_light)
        
        # 4. UI
        self._setup_ui(services)
        print("PxAnicScene Ready. FogOfWar system is active.")

    def _setup_ui(self, services):
        self.ui_root = Control(0, 0, 1280, 720)
        time_panel = Panel(10, 10, 220, 80)
        self.lbl_day = Label("DAY 1", 15, 15, size=24)
        self.lbl_phase = Label("PHASE: NOON", 15, 45, size=18)
        time_panel.add_child(self.lbl_day); time_panel.add_child(self.lbl_phase)
        status_panel = Panel(10, 600, 300, 110)
        status_panel.add_child(Label("HEALTH", 15, 15, 14))
        self.bar_hp = ProgressBar(15, 35, 270, 15, color=(255, 50, 50))
        status_panel.add_child(self.bar_hp)
        status_panel.add_child(Label("ACTION POINTS", 15, 60, 14))
        self.bar_ap = ProgressBar(15, 80, 270, 15, color=(50, 150, 255))
        status_panel.add_child(self.bar_ap)
        self.ui_root.add_child(time_panel); self.ui_root.add_child(status_panel)
        services["app"].set_ui(self.ui_root)

    def handle_event(self, event):
        if self.ui_root: self.ui_root.handle_event(event)
        if event.type == pygame.VIDEORESIZE:
            self.fog_of_war.update_resolution(event.w, event.h)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3: self._update_move_target()
            elif event.button == 1: self._handle_interaction()

    def _update_move_target(self):
        app = App.instance
        if app and self.player:
            input_mgr = app.services["input"]
            renderer = app.services["renderer"]
            grid_pos = input_mgr.get_mouse_grid_pos(renderer.camera)
            self.move_target = pygame.math.Vector2(grid_pos.x, grid_pos.y)

    def _handle_interaction(self):
        app = App.instance
        if not app: return
        input_mgr = app.services["input"]; renderer = app.services["renderer"]; popups = app.services["popups"]
        grid_pos = input_mgr.get_mouse_grid_pos(renderer.camera)
        gx, gy = int(grid_pos.x), int(grid_pos.y)
        block = self.block_grid.get((gx, gy))
        if block and block.tile_id:
            sid = str(block.tile_id)
            if sid[0] == '3' and len(sid) >= 4 and sid[3] == '1':
                # WallNode도 상호작용 가능해야 하므로 get_tile_id() 확인
                if isinstance(block, WallNode):
                    print("WallNode interaction - Toggling...")
                    # WallNode의 상호작용 로직은 추후 구현 필요 (문 등)
                    popups.add_popup("Wall!", gx, gy, block.position.z, (255, 255, 0), 1.0)
                else: # Block3D (사물) 상호작용
                    self._toggle_door(block, gx, gy) # 현재는 문 토글만 구현
                    popups.add_popup("CLACK!", gx, gy, block.position.z, (200, 200, 255), 1.0)
            else: 
                popups.add_popup("Nothing", gx, gy, block.position.z, (150, 150, 150), 0.5)

    def _toggle_door(self, block, gx, gy):
        sid = list(str(block.tile_id))
        if len(sid) < 9: return
        is_closed = (sid[2] == '2')
        sid[2] = '1' if is_closed else '2'
        if is_closed:
            self.collision_world.remove_static(block)
        else:
            self.collision_world.add_static(block)
        new_id = int("".join(sid))
        block.tile_id = new_id
        from engine.assets.tile_engine import TileEngine
        if new_id in TileEngine.TILE_DATA:
            block.color = TileEngine.TILE_DATA[new_id]['color']
        block._regen_texture()

    def update(self, dt, services):
        time_manager = services["time"]; lighting_manager = services["lighting"]
        renderer = services["renderer"]
        interaction = services["interaction"]; popups = services["popups"]

        # UI 업데이트
        self.lbl_day.set_text(f"DAY {time_manager.day_count}")
        self.lbl_phase.set_text(f"PHASE: {time_manager.current_phase}")
        if self.player:
            self.bar_hp.progress = self.player.status.hp / self.player.status.max_hp
            self.bar_ap.progress = self.player.status.ap / self.player.status.max_ap

        # 조명 업데이트
        phase = time_manager.current_phase
        self.sun.intensity = 0.05 if phase == 'NIGHT' else (0.2 if phase in ['DAWN', 'EVENING'] else 0.6)
        lighting_manager.set_directional_light(self.sun)

        # 플레이어 이동 업데이트
        if pygame.mouse.get_pressed()[2]: self._update_move_target()
        if self.player and self.move_target:
            curr = pygame.math.Vector2(self.player.position.x, self.player.position.y)
            diff = self.move_target - curr
            if diff.length() > 0.1:
                direction = diff.normalize()
                self.player.facing_direction = direction
                
                is_running = services["input"].is_action_pressed("run")
                speed = 10.0 if is_running else 7.0
                vel = direction * speed * dt

                noise_radius = 10 if is_running else 5
                interaction.emit_noise(self.player.position.x, self.player.position.y, noise_radius)
                
                if pygame.time.get_ticks() % 15 == 0:
                    popups.add_popup("", self.player.position.x, self.player.position.y, 
                                     0, (255, 255, 255, 100), 0.5)

                if not self.collision_world.check_collision(pygame.math.Vector3(self.player.position.x + vel.x, self.player.position.y, 0)):
                    self.player.position.x += vel.x
                if not self.collision_world.check_collision(pygame.math.Vector3(self.player.position.x, self.player.position.y + vel.y, 0)):
                    self.player.position.y += vel.y
                self.player.is_moving = True
            else:
                self.move_target = None
                self.player.is_moving = False
        elif self.player:
            self.player.is_moving = False

        # FOV 및 카메라 업데이트
        if self.player:
            ix, iy = IsoMath.cart_to_iso(self.player.position.x, self.player.position.y, 0)
            renderer.camera.follow(ix, iy)
            
            self.fov_system.view_radius = 12.0 if phase != 'NIGHT' else 7.0
            
            fov_poly_cartesian = self.fov_system.calculate_fov(
                self.player.position, 
                facing_dir=self.player.facing_direction
            )
            fov_poly_iso = [IsoMath.cart_to_iso(x, y) for x, y in fov_poly_cartesian]
            self.fog_of_war.set_fov_polygon(fov_poly_iso)

        super().update(dt, services)
