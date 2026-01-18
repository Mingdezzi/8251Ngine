import pygame
import json
import os
from engine.core.node import Node
from engine.core.math_utils import IsoMath, TILE_WIDTH, TILE_HEIGHT
from engine.graphics.tilemap import TileMap
from engine.graphics.wall import WallNode
from engine.graphics.block import Block3D
from engine.ui.gui import Panel, Button, Label, LineEdit

class EditorScene(Node):
    def __init__(self):
        super().__init__("EditorScene")
        self.is_initialized = False
        self.map_data = {}
        self.tile_map = TileMap()
        self.add_child(self.tile_map)
        
        self.wall_nodes = {}
        self.object_nodes = {}
        
        self.mode = "WALL"
        self.ui_root = Control(0, 0, 1, 1)
        self.editor_panel = None
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
        self.services = services
        self.camera = services["renderer"].camera
        self._setup_ui()

    def _setup_ui(self):
        sw, sh = pygame.display.get_surface().get_size()
        self.ui_root.rect.size = (sw, sh)
        self.ui_root.children.clear()
        
        self.services["app"].set_ui(self.ui_root)
        
        if not self.is_initialized:
            self._show_launcher(sw, sh)
        else:
            self._show_editor_ui(sw, sh)

    def _show_launcher(self, sw, sh):
        panel_w, panel_h = 400, 300
        launcher = Panel(sw/2 - panel_w/2, sh/2 - panel_h/2, panel_w, panel_h)
        self.ui_root.add_child(launcher)
        
        title = Label("Map Editor", panel_w/2, 30, size=32)
        title.rect.centerx = panel_w/2
        launcher.add_child(title)
        
        btn_new = Button("New Map", 50, 100, 300, 50, on_click=self._show_new_map_dialog)
        launcher.add_child(btn_new)
        
        btn_load = Button("Load Map", 50, 170, 300, 50, on_click=self._load_map)
        launcher.add_child(btn_load)

    def _show_new_map_dialog(self):
        sw, sh = pygame.display.get_surface().get_size()
        self.ui_root.children.clear()
        
        panel_w, panel_h = 300, 200
        dialog = Panel(sw/2 - panel_w/2, sh/2 - panel_h/2, panel_w, panel_h)
        self.ui_root.add_child(dialog)
        
        title = Label("Map Size", panel_w/2, 20, size=24)
        title.rect.centerx = panel_w / 2
        dialog.add_child(title)
        
        dialog.add_child(Label("Width:", 20, 70))
        self.width_input = LineEdit("50", 90, 65, 180, 30)
        dialog.add_child(self.width_input)
        
        dialog.add_child(Label("Height:", 20, 110))
        self.height_input = LineEdit("50", 90, 105, 180, 30)
        dialog.add_child(self.height_input)

        def create_action():
            w = int(self.width_input.text) if self.width_input.text.isdigit() else 50
            h = int(self.height_input.text) if self.height_input.text.isdigit() else 50
            self._create_new_map(w, h)
        
        btn_create = Button("Create", 75, 150, 150, 40, on_click=create_action)
        dialog.add_child(btn_create)

    def _create_new_map(self, width, height):
        self.map_data = {"width": width, "height": height, "blocks": [], "walls": {}}
        # 기본 바닥 타일 추가
        default_floor_id = 111001010 # 콘크리트 바닥
        for y in range(height):
            for x in range(width):
                self.map_data["blocks"].append({"pos": [x, y, 0], "tile_id": default_floor_id})

        self.is_initialized = True
        self._setup_ui()
        self._rebuild_map_visuals()
        map_center_x, map_center_y = IsoMath.cart_to_iso(width / 2, height / 2)
        self.camera.position.x = map_center_x
        self.camera.position.y = map_center_y

    def _load_map(self):
        path = "assets/maps/new_edge_map.json"
        if os.path.exists(path):
            with open(path, "r") as f: self.map_data = json.load(f)
            self.is_initialized = True
            self._setup_ui()
            self._rebuild_map_visuals()
            self.camera.position.x = self.map_data["width"] / 2
            self.camera.position.y = self.map_data["height"] / 2
        else:
            print(f"Map file not found: {path}")

    def _show_editor_ui(self, sw, sh):
        panel_width = 220
        map_view_width = sw - panel_width

        self.editor_panel = Panel(map_view_width, 0, panel_width, sh)
        self.ui_root.add_child(self.editor_panel)
        
        self.camera.offset.x = map_view_width / 2
        self.camera.offset.y = sh / 2

        self.editor_panel.add_child(Button("Walls", 10, 10, 60, 30, on_click=lambda: self._set_mode("WALL")))
        self.editor_panel.add_child(Button("Floors", 75, 10, 60, 30, on_click=lambda: self._set_mode("FLOOR")))
        self.editor_panel.add_child(Button("Objects", 140, 10, 60, 30, on_click=lambda: self._set_mode("OBJECT")))
        
        self.palette_panel = Panel(10, 50, 200, sh - 120, color=(0,0,0,0))
        self.editor_panel.add_child(self.palette_panel)
        self._build_palette()

        self.editor_panel.add_child(Button("Save Map", 10, sh - 60, 200, 40, color=(60, 120, 60), on_click=self._save_map))

    def _build_palette(self):
        self.palette_panel.children.clear()
        y_offset = 10
        
        tiles = {}
        if self.mode == "WALL": category = "WALLS"
        elif self.mode == "FLOOR": category = "FLOORS"
        else: # OBJECT 모드는 DECO와 INTERACT 합침
            tiles.update(self.tileset.get("DECO", {}))
            tiles.update(self.tileset.get("INTERACT", {}))
            category = None

        if category:
            tiles = self.tileset.get(category, {})

        for tid_str, name in tiles.items():
            tid = int(tid_str)
            btn = Button(name, 5, y_offset, 190, 25, color=(70,70,80), on_click=(lambda t=tid, n=name: lambda: self._set_brush(t, n))())
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
        if self.ui_root.handle_event(event):
            return

        if event.type == pygame.VIDEORESIZE:
            self._setup_ui()
            return
        
        if not self.is_initialized: return

        if self.editor_panel and self.editor_panel.rect.collidepoint(event.pos):
            return

        if pygame.mouse.get_pressed()[1]:
            rel = pygame.mouse.get_rel()
            self.camera.position.x -= rel[0] / self.camera.zoom
            self.camera.position.y -= rel[1] / self.camera.zoom

        elif event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
            if event.type == pygame.MOUSEMOTION and (event.buttons[0] or event.buttons[2]):
                self._handle_map_click(event.buttons[0] or event.buttons[2])
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_map_click(event.button)

    def _handle_map_click(self, button):
        mx, my = pygame.mouse.get_pos()
        world_x, world_y = self.camera.screen_to_world(mx, my)
        gx, gy, edge = self._find_nearest_grid_or_edge(world_x, world_y)

        if not (0 <= gx < self.map_data["width"] and 0 <= gy < self.map_data["height"]):
            return

        if self.mode == "WALL" and edge != "CENTER":
            if button == 1: self._add_wall(gx, gy, edge)
            elif button == 3: self._remove_wall(gx, gy, edge)
        
        elif self.mode == "FLOOR" and edge == "CENTER":
            if button == 1:
                self.map_data["blocks"] = [b for b in self.map_data["blocks"] if not (b["pos"][0] == gx and b["pos"][1] == gy and str(b["tile_id"]).startswith('1'))]
                new_block = {"pos": [gx, gy, 0], "tile_id": self.brush_tile_id}
                self.map_data["blocks"].append(new_block)
                self._rebuild_map_visuals()
            elif button == 3:
                self.map_data["blocks"] = [b for b in self.map_data["blocks"] if not (b["pos"][0] == gx and b["pos"][1] == gy and str(b["tile_id"]).startswith('1'))]
                self._rebuild_map_visuals()

        elif self.mode == "OBJECT" and edge == "CENTER":
            key = (gx, gy)
            if button == 1:
                if key not in self.object_nodes:
                    obj_data = {"pos": [gx, gy, 0], "tile_id": self.brush_tile_id}
                    self.map_data["blocks"].append(obj_data)
                    self._add_object_node(gx, gy, self.brush_tile_id)
            elif button == 3:
                if key in self.object_nodes:
                    self.map_data["blocks"] = [b for b in self.map_data["blocks"] if not (b["pos"][0] == gx and b["pos"][1] == gy and not str(b["tile_id"]).startswith('1'))]
                    self._remove_object_node(gx, gy)

    def _find_nearest_grid_or_edge(self, world_x, world_y):
        cart_x, cart_y = IsoMath.iso_to_cart(world_x, world_y)
        gx, gy = round(cart_x), round(cart_y)
        frac_x = cart_x - gx
        frac_y = cart_y - gy
        threshold = 0.3
        if frac_x > threshold and abs(frac_y) < threshold: return gx, gy, "NE"
        if frac_y > threshold and abs(frac_x) < threshold: return gx, gy, "NW"
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

        if "walls" in self.map_data:
            for pos_str, wall_types in self.map_data["walls"].items():
                pos = tuple(map(int, pos_str.strip("()").split(",")))
                for wall_type in wall_types:
                    self._add_wall_node(pos[0], pos[1], wall_type)

        if "blocks" in self.map_data:
            for b_data in self.map_data["blocks"]:
                gx, gy = b_data["pos"][0], b_data["pos"][1]
                tid = b_data["tile_id"]
                if str(tid).startswith('1'): continue
                self._add_object_node(gx, gy, tid)

        self.tile_map.load_from_blocks(self.map_data.get("blocks", []), self.map_data["width"], self.map_data["height"])

        print(f"Rebuilt visuals: {len(self.wall_nodes)} walls, {len(self.object_nodes)} objects.")

    def _save_map(self):
        path = "assets/maps/new_edge_map.json"
        with open(path, "w") as f: json.dump(self.map_data, f, indent=4)
        print(f"Saved map to {path}")

    def draw_gizmos(self, screen, camera):
        if not self.is_initialized: return
        w, h = self.map_data["width"], self.map_data["height"]
        
        # 그리드 ...
        for x in range(w + 1):
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(x, 0)); p2 = camera.world_to_screen(*IsoMath.cart_to_iso(x, h))
            pygame.draw.line(screen, (70,70,80), p1, p2, 1)
        for y in range(h + 1):
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(0, y)); p2 = camera.world_to_screen(*IsoMath.cart_to_iso(w, y))
            pygame.draw.line(screen, (70,70,80), p1, p2, 1)

        # 미리보기 ...
        mx, my = pygame.mouse.get_pos()
        if self.editor_panel and self.editor_panel.rect.collidepoint((mx, my)): return
        
        wx, wy = self.camera.screen_to_world(mx, my)
        gx, gy, edge = self._find_nearest_grid_or_edge(wx, wy)

        if not (0 <= gx < w and 0 <= gy < h): return
        
        preview_node = None
        if self.mode == "WALL" and edge != "CENTER":
            preview_node = WallNode(wall_type=edge, tile_id=self.brush_tile_id)
        elif (self.mode == "OBJECT" or self.mode == "FLOOR") and edge == "CENTER":
            if self.mode == "OBJECT":
                preview_node = Block3D(tile_id=self.brush_tile_id, size_z=0.8)
            else: # FLOOR
                # 바닥 미리보기는 단순한 사각형으로
                points = [
                    camera.world_to_screen(*IsoMath.cart_to_iso(gx, gy)),
                    camera.world_to_screen(*IsoMath.cart_to_iso(gx + 1, gy)),
                    camera.world_to_screen(*IsoMath.cart_to_iso(gx + 1, gy + 1)),
                    camera.world_to_screen(*IsoMath.cart_to_iso(gx, gy + 1))
                ]
                pygame.draw.polygon(screen, (255, 255, 0, 100), points, 2)
                return

        if preview_node:
            preview_surf = preview_node.get_sprite()
            if preview_surf:
                preview_surf.set_alpha(150)
                iso_x, iso_y = IsoMath.cart_to_iso(gx, gy)
                screen_x, screen_y = camera.world_to_screen(iso_x, iso_y)
                
                if isinstance(preview_node, WallNode):
                    screen_y -= TILE_HEIGHT / 2 
                else: 
                    screen_y -= int(getattr(preview_node, 'size_z', 0.8) * HEIGHT_SCALE)

                screen.blit(preview_surf, (screen_x - preview_surf.get_width() / 2, screen_y - preview_surf.get_height() / 2))
