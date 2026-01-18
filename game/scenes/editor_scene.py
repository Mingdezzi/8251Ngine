import pygame
import json
import os
from engine.core.node import Node
from engine.core.math_utils import IsoMath, TILE_WIDTH, TILE_HEIGHT
from engine.graphics.tilemap import TileMap
from engine.graphics.wall import WallNode
from engine.graphics.block import Block3D
from engine.ui.gui import Panel, Button, Label, LineEdit # LineEdit 추가

class EditorScene(Node):
    def __init__(self):
        super().__init__("EditorScene")
        self.is_initialized = False
        self.map_data = {}
        self.tile_map = TileMap()
        self.add_child(self.tile_map)
        
        self.wall_nodes = {}
        self.object_nodes = {}
        
        self.mode = "WALL" # WALL, OBJECT, FLOOR
        self.ui_root = None
        self.camera = None

        self.tileset = {}
        self.brush_tile_id = 212000000
        self._load_tileset_data()

    def _load_tileset_data(self):
        path = "engine/data/tileset.json"
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: self.tileset = json.load(f)
        if "WALLS" in self.tileset and self.tileset["WALLS"]:
            self.brush_tile_id = int(list(self.tileset["WALLS"].keys())[0])

    def _ready(self, services):
        self.services = services # 서비스 객체 저장
        self.camera = services["renderer"].camera
        self._setup_ui(services)

    def _setup_ui(self, services):
        sw, sh = pygame.display.get_surface().get_size()
        self.ui_root = Panel(0, 0, sw, sh, color=(30, 30, 35, 255))
        services["app"].set_ui(self.ui_root)
        
        if not self.is_initialized:
            self._show_launcher()
        else:
            self._show_editor_ui()

    def _show_launcher(self):
        self.ui_root.children.clear()
        sw, sh = pygame.display.get_surface().get_size()
        
        # Panel을 화면 중앙에 배치
        panel_w, panel_h = 400, 300
        panel = Panel(sw/2 - panel_w/2, sh/2 - panel_h/2, panel_w, panel_h)
        self.ui_root.add_child(panel)
        
        # 자식 위젯들은 Panel의 (0,0)을 기준으로 한 상대좌표
        title = Label("Map Editor", 0, 20, size=32)
        title.rect.centerx = panel_w / 2
        panel.add_child(title)
        
        btn_new = Button("New Map", 50, 100, 300, 50)
        panel.add_child(btn_new)
        btn_new.on_click = self._show_new_map_dialog
        
        btn_load = Button("Load Map", 50, 170, 300, 50)
        panel.add_child(btn_load)
        btn_load.on_click = self._load_map

    def _show_new_map_dialog(self):
        self.ui_root.children.clear()
        sw, sh = pygame.display.get_surface().get_size()
        
        panel_w, panel_h = 300, 200
        dialog = Panel(sw/2 - panel_w/2, sh/2 - panel_h/2, panel_w, panel_h)
        self.ui_root.add_child(dialog)
        
        title = Label("Map Size", 0, 20, size=24)
        title.rect.centerx = panel_w / 2
        dialog.add_child(title)
        
        dialog.add_child(Label("Width:", 20, 70))
        self.width_input = LineEdit("50", 90, 65, 180, 30)
        dialog.add_child(self.width_input)
        
        dialog.add_child(Label("Height:", 20, 110))
        self.height_input = LineEdit("50", 90, 105, 180, 30)
        dialog.add_child(self.height_input)
        
        btn_create = Button("Create", 75, 150, 150, 40)
        dialog.add_child(btn_create)
        def create_action():
            w = int(self.width_input.text) if self.width_input.text.isdigit() else 50
            h = int(self.height_input.text) if self.height_input.text.isdigit() else 50
            self._create_new_map(w, h)
        btn_create.on_click = create_action

    def _create_new_map(self, width, height):
        self.map_data = {"width": width, "height": height, "blocks": [], "walls": {}}
        self.is_initialized = True
        self._setup_ui(self.services) # 저장된 서비스 객체 사용
        self._rebuild_map_visuals()

    def _load_map(self):
        path = "assets/maps/new_edge_map.json"
        if os.path.exists(path):
            with open(path, "r") as f: self.map_data = json.load(f)
            self.is_initialized = True
            self._setup_ui(self.camera.services)
            self._rebuild_map_visuals()
            # 로드된 맵의 중심을 카메라가 바라보도록 설정
            self.camera.position.x = self.map_data["width"] / 2
            self.camera.position.y = self.map_data["height"] / 2
        else:
            print(f"Map file not found: {path}")

    def _show_editor_ui(self):
        sw, sh = pygame.display.get_surface().get_size()
        self.ui_root.children.clear()
        
        editor_sidebar = Panel(sw - 220, 0, 220, sh, color=(35, 35, 40, 245))
        self.ui_root.add_child(editor_sidebar)
        
        # 모드 전환 버튼
        btn_wall = Button("Walls", 10, 10, 90, 30)
        btn_wall.on_click = lambda: self._set_mode("WALL")
        editor_sidebar.add_child(btn_wall)
        
        btn_obj = Button("Objects", 105, 10, 90, 30)
        btn_obj.on_click = lambda: self._set_mode("OBJECT")
        editor_sidebar.add_child(btn_obj)

        # 타일 팔레트
        self.palette_panel = Panel(10, 50, 200, sh - 120, color=(0,0,0,0))
        editor_sidebar.add_child(self.palette_panel)
        self._build_palette()

        # 저장 버튼
        btn_save = Button("Save Map", 10, sh - 60, 200, 40, color=(60, 120, 60))
        btn_save.on_click = self._save_map
        editor_sidebar.add_child(btn_save)

    def _build_palette(self):
        self.palette_panel.children.clear()
        y_offset = 10
        
        category = "WALLS" if self.mode == "WALL" else "OBJECTS"
        tiles = self.tileset.get(category, {})

        for tid_str, name in tiles.items():
            tid = int(tid_str)
            btn = Button(name, 5, y_offset, 190, 25, color=(70,70,80))
            btn.on_click = (lambda t=tid, n=name: lambda: self._set_brush(t, n))()
            self.palette_panel.add_child(btn)
            y_offset += 28

    def _set_brush(self, tid, name):
        self.brush_tile_id = tid
        print(f"Brush set to: {name} ({tid})")

    def _set_mode(self, mode):
        self.mode = mode
        self._build_palette()
        print(f"Editor mode set to: {self.mode}")

    def handle_event(self, event):
        if self.ui_root.handle_event(event): return

        if not self.is_initialized: return # 맵 로드/생성 전에는 조작 불가

        # 드래그하여 벽/사물 그리기/지우기
        if event.type == pygame.MOUSEMOTION and (event.buttons[0] or event.buttons[2]):
            self._handle_map_click(event.buttons[0] or event.buttons[2])
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_map_click(event.button)
        
        # Camera Pan
        if pygame.mouse.get_pressed()[1]:
            rel = pygame.mouse.get_rel()
            self.camera.position.x -= rel[0] / self.camera.zoom
            self.camera.position.y -= rel[1] / self.camera.zoom

    def _handle_map_click(self, button):
        mx, my = pygame.mouse.get_pos()
        # UI 영역 클릭 시 맵 조작 방지
        if self.ui_root.children and self.ui_root.children[0].rect.collidepoint((mx, my)): return
        
        world_x, world_y = self.camera.screen_to_world(mx, my)
        gx, gy, edge = self._find_nearest_grid_or_edge(world_x, world_y)

        # 맵 범위 체크
        if not (0 <= gx < self.map_data["width"] and 0 <= gy < self.map_data["height"]):
            return

        if self.mode == "WALL" and edge != "CENTER":
            key = (gx, gy, edge)
            pos_key = f"({gx},{gy})"

            if button == 1: # 좌클릭: 벽 추가
                if key not in self.wall_nodes:
                    if pos_key not in self.map_data["walls"]: self.map_data["walls"][pos_key] = []
                    self.map_data["walls"][pos_key].append(edge)
                    self._add_wall_node(gx, gy, edge)
            
            elif button == 3: # 우클릭: 벽 삭제
                if key in self.wall_nodes:
                    if pos_key in self.map_data["walls"] and edge in self.map_data["walls"][pos_key]:
                        self.map_data["walls"][pos_key].remove(edge)
                        if not self.map_data["walls"][pos_key]: del self.map_data["walls"][pos_key]
                        self._remove_wall_node(gx, gy, edge)
        
        elif self.mode == "OBJECT" and edge == "CENTER":
            key = (gx, gy)
            if button == 1: # 좌클릭: 사물 추가
                if key not in self.object_nodes: # 중복 추가 방지
                    obj_data = {"pos": [gx, gy, 0], "tile_id": self.brush_tile_id}
                    self.map_data["blocks"].append(obj_data)
                    self._add_object_node(gx, gy, self.brush_tile_id)
            
            elif button == 3: # 우클릭: 사물 삭제
                if key in self.object_nodes:
                    self.map_data["blocks"] = [b for b in self.map_data["blocks"] if not (b["pos"][0] == gx and b["pos"][1] == gy)]
                    self._remove_object_node(gx, gy)

    def _find_nearest_grid_or_edge(self, world_x, world_y):
        cart_x, cart_y = IsoMath.iso_to_cart(world_x, world_y)
        gx, gy = round(cart_x), round(cart_y)
        frac_x = cart_x - gx
        frac_y = cart_y - gy
        threshold = 0.3
        if frac_x > threshold and abs(frac_y) < threshold:
            return gx, gy, "NE"
        if frac_y > threshold and abs(frac_x) < threshold:
            return gx, gy, "NW"
        return gx, gy, "CENTER"

    def _add_wall_node(self, gx, gy, wall_type):
        key = (gx, gy, wall_type)
        wall = WallNode(wall_type=wall_type, tile_id=self.brush_tile_id)
        wall.position.x, wall.position.y = gx, gy
        self.add_child(wall)
        self.wall_nodes[key] = wall

    def _remove_wall_node(self, gx, gy, wall_type):
        key = (gx, gy, wall_type)
        if key in self.wall_nodes:
            node = self.wall_nodes.pop(key)
            self.remove_child(node)
    
    def _add_object_node(self, gx, gy, tile_id):
        key = (gx, gy)
        node = Block3D(tile_id=tile_id, size_z=0.8)
        node.position.x, node.position.y = gx, gy
        self.add_child(node)
        self.object_nodes[key] = node

    def _remove_object_node(self, gx, gy):
        key = (gx, gy)
        if key in self.object_nodes:
            node = self.object_nodes.pop(key)
            self.remove_child(node)

    def _rebuild_map_visuals(self):
        for node in list(self.wall_nodes.values()) + list(self.object_nodes.values()):
            if node.parent: self.remove_child(node)
        self.wall_nodes.clear()
        self.object_nodes.clear()

        # 맵 데이터에서 벽 노드 재생성
        if "walls" in self.map_data:
            for pos_str, wall_types in self.map_data["walls"].items():
                pos = tuple(map(int, pos_str.strip("()").split(",")))
                for wall_type in wall_types:
                    self._add_wall_node(pos[0], pos[1], wall_type)

        # 맵 데이터에서 사물 노드 재생성
        if "blocks" in self.map_data:
            for b_data in self.map_data["blocks"]:
                gx, gy = b_data["pos"][0], b_data["pos"][1]
                tid = b_data["tile_id"]
                self._add_object_node(gx, gy, tid)

        self.tile_map.load_from_blocks(self.map_data.get("blocks", []), self.map_data["width"], self.map_data["height"])

        print(f"Rebuilt visuals: {len(self.wall_nodes)} walls, {len(self.object_nodes)} objects.")

    def _save_map(self):
        path = "assets/maps/new_edge_map.json"
        with open(path, "w") as f:
            json.dump(self.map_data, f, indent=4)
        print(f"Saved map to {path}")

    def draw_gizmos(self, screen, camera):
        if not self.is_initialized: return

        w, h = self.map_data["width"], self.map_data["height"]

        # 1. 계층적 그리드 그리기
        for x in range(w + 1):
            thickness = 3 if x == w / 2 else (2 if x % 10 == 0 else 1)
            color = (100, 100, 120) if thickness < 3 else (150, 150, 180)
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(x, 0))
            p2 = camera.world_to_screen(*IsoMath.cart_to_iso(x, h))
            pygame.draw.line(screen, color, p1, p2, thickness)
        for y in range(h + 1):
            thickness = 3 if y == h / 2 else (2 if y % 10 == 0 else 1)
            color = (100, 100, 120) if thickness < 3 else (150, 150, 180)
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(0, y))
            p2 = camera.world_to_screen(*IsoMath.cart_to_iso(w, y))
            pygame.draw.line(screen, color, p1, p2, thickness)
            
        # 2. 맵 경계선 (붉은색)
        border_points = [
            camera.world_to_screen(*IsoMath.cart_to_iso(0, 0)),
            camera.world_to_screen(*IsoMath.cart_to_iso(w, 0)),
            camera.world_to_screen(*IsoMath.cart_to_iso(w, h)),
            camera.world_to_screen(*IsoMath.cart_to_iso(0, h))
        ]
        pygame.draw.polygon(screen, (255, 80, 80), border_points, 3)

        # 3. 호버된 경계선 및 미리보기
        mx, my = pygame.mouse.get_pos()
        if self.ui_root.rect.collidepoint((mx, my)): return
        
        wx, wy = self.camera.screen_to_world(mx, my)
        gx, gy, edge = self._find_nearest_grid_or_edge(wx, wy)

        # 맵 범위 체크
        if not (0 <= gx < w and 0 <= gy < h):
            return
        
        preview_node = None
        if self.mode == "WALL" and edge != "CENTER":
            preview_node = WallNode(wall_type=edge, tile_id=self.brush_tile_id)
        elif self.mode == "OBJECT" and edge == "CENTER":
            preview_node = Block3D(tile_id=self.brush_tile_id, size_z=0.8)

        if preview_node:
            preview_surf = preview_node.get_sprite()
            if preview_surf:
                preview_surf.set_alpha(150)
                iso_x, iso_y = IsoMath.cart_to_iso(gx, gy)
                screen_x, screen_y = camera.world_to_screen(iso_x, iso_y)
                
                # WallNode와 Block3D의 렌더링 기준점 보정
                if isinstance(preview_node, WallNode):
                    # WallNode는 TILE_HEIGHT/2만큼 위로 올라와 그려지므로 y 보정
                    screen_y -= TILE_HEIGHT / 2 
                else: # Block3D (사물)
                    # 사물은 바닥 기준이므로 z-offset을 고려하여 보정
                    screen_y -= int(preview_node.size_z * HEIGHT_SCALE) # 사물의 시각적 높이만큼 위로 보정

                # 미리보기는 중앙에 위치하도록 보정
                screen.blit(preview_surf, (screen_x - preview_surf.get_width() / 2, screen_y - preview_surf.get_height() / 2))