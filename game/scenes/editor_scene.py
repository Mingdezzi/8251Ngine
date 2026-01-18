import pygame
import json
import os
from engine.core.node import Node
from engine.core.math_utils import IsoMath, TILE_WIDTH, TILE_HEIGHT
from engine.graphics.tilemap import TileMap
from engine.graphics.wall import WallNode
from engine.graphics.block import Block3D
from engine.ui.gui import Panel, Button, Label, LineEdit, Control

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
        self.map_data = {"width": width, "height": height, "blocks": {}, "walls": {}}
        # 기본 바닥 타일 추가
        default_floor_id = 111001010 # 콘크리트 바닥
        for y in range(height):
            for x in range(width):
                self.map_data["blocks"].update({(x, y): {"tile_id": default_floor_id}})

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
        # 1. Handle UI events. If UI consumed it, stop processing.
        if self.ui_root.handle_event(event):
            return

        # 2. Handle specific global events (e.g., VIDEORESIZE).
        if event.type == pygame.VIDEORESIZE:
            self._setup_ui()
            return
        
        # 3. If the editor is not initialized, ignore further input.
        if not self.is_initialized: 
            return

        # 4. Process mouse events strictly.
        # Check if the event is a recognized mouse event type.
        is_mouse_event = event.type in [
            pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, 
            pygame.MOUSEMOTION, pygame.MOUSEWHEEL
        ]

        if is_mouse_event:
            # Ensure event.pos is valid before using it. This is a safeguard.
            if hasattr(event, 'pos') and event.pos is not None:
                
                # If the mouse is over the editor panel, consume the event and return.
                if self.editor_panel and self.editor_panel.rect.collidepoint(event.pos):
                    return

                # Mouse is NOT over the editor panel. Process map interactions.
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_map_click(event.button)
                elif event.type == pygame.MOUSEMOTION:
                    # Handle camera panning if middle mouse button is held down
                    if pygame.mouse.get_pressed()[1]: # Middle mouse button state
                        rel = pygame.mouse.get_rel()
                        self.camera.position.x -= rel[0] / self.camera.zoom
                        self.camera.position.y -= rel[1] / self.camera.zoom
                    else:
                        # If not panning, check for drawing buttons and pass the correct button number
                        pressed_buttons = pygame.mouse.get_pressed()
                        if pressed_buttons[0]: # Left mouse button is pressed
                            self._handle_map_click(1)
                        elif pressed_buttons[2]: # Right mouse button is pressed
                            self._handle_map_click(3)

                elif event.type == pygame.MOUSEBUTTONUP:
                    pass

        # 5. Handle other event types like KEYDOWN, etc.
        elif event.type == pygame.KEYDOWN:
            pass

    def _rebuild_map_visuals(self):
        print("\n--- DEBUG: _rebuild_map_visuals called ---") # Debug print statement to confirm execution
        for node in list(self.wall_nodes.values()): # Only iterate wall_nodes now
            if node.parent: self.remove_child(node)
        self.wall_nodes.clear()
        
        if "walls" in self.map_data:
            for pos_str, wall_types in self.map_data["walls"].items():
                pos = tuple(map(int, pos_str.strip("()[]").split(",")))
                for wall_type in wall_types:
                    self._add_wall_node(pos[0], pos[1], wall_type)

        blocks_for_tilemap = []
        if "blocks" in self.map_data:
            for (gx, gy), data in self.map_data["blocks"].items():
                blocks_for_tilemap.append({"pos": [gx, gy, 0], "tile_id": data["tile_id"]})

        self.tile_map.load_from_blocks(blocks_for_tilemap, self.map_data["width"], self.map_data["height"])

        print(f"Rebuilt visuals: {len(self.wall_nodes)} walls.")

    def _save_map(self):
        path = "assets/maps/new_edge_map.json"
        blocks_list = []
        for (gx, gy), data in self.map_data["blocks"].items():
            blocks_list.append({"pos": [gx, gy, 0], "tile_id": data["tile_id"]})
        self.map_data["blocks"] = blocks_list

        with open(path, "w") as f: json.dump(self.map_data, f, indent=4)
        print(f"Saved map to {path}")

    def draw_gizmos(self, screen, camera):
        if not self.is_initialized: return
        w, h = self.map_data["width"], self.map_data["height"]