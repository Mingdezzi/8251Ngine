import pygame
import random
import json
import os
import math
from engine.core.node import Node
from engine.graphics.tile_node import TileNode
from engine.core.math_utils import IsoMath
from engine.assets.map_loader import MapLoader
from engine.assets.ui_loader import UILoader
from engine.assets.tile_engine import TileEngine
from engine.ui.gui import Control, Label, Panel, Button

class EditorScene(Node):
    def __init__(self):
        super().__init__("EditorScene")
        self.layers = {0: {}, 1: {}, 2: {}}
        self.ui_root = Control(0, 0, 1280, 720)
        
        # Map Settings
        self.map_width = 30
        self.map_height = 30
        self.panel_width = 280
        
        # State
        self.initialized = False
        self.current_layer = 0 # 0: FLOOR, 1: WALL, 2: FURN
        self.mode = "TILES"
        self.launcher_state = "MAIN"
        
        # Brush
        self.brush_tile_id = 1110000
        self.brush_size_z = 1.0 # Default wall height (1 tile high)
        
        self.tileset = {}
        self._load_tileset_data()
        
        # Interaction
        self.hover_grid_pos = (0, 0)
        self.is_dragging = False
        self.drag_start = None
        self.drag_current = None
        self.drag_mode = 0 
        self.last_screen_size = (0, 0)

    def _load_tileset_data(self):
        path = "engine/data/tileset.json"
        if os.path.exists(path):
            with open(path, 'r') as f: self.tileset = json.load(f)

    def _ready(self, services):
        self._services = services
        if services.get("app"): services["app"].set_ui(self.ui_root)
        self._update_layout()

    def _update_layout(self):
        sw, sh = pygame.display.get_surface().get_size()
        self.ui_root.rect.width, self.ui_root.rect.height = sw, sh
        self.ui_root.children.clear()
        
        if not self.initialized:
            mw, mh = 450, 350
            mx, my = (sw - mw)//2, (sh - mh)//2
            self.launcher_panel = Panel(mx, my, mw, mh, color=(40, 40, 50, 250))
            self.ui_root.add_child(self.launcher_panel)
            if self.launcher_state == "MAIN": self._build_launcher_main(mx, my)
            else: self._build_launcher_settings(mx, my)
        else:
            sb_x = sw - self.panel_width
            self.editor_panel = Panel(sb_x, 0, self.panel_width, sh, color=(35, 35, 40, 245))
            self.ui_root.add_child(self.editor_panel)
            self._build_sidebar_content(sb_x, sh)
            self._services["renderer"].camera.offset = pygame.math.Vector2((sw - self.panel_width) / 2, sh / 2)

    def _build_launcher_main(self, mx, my):
        self.launcher_panel.add_child(Label("8251 ENGINE - PROJECT", mx + 20, my + 20, 22, (255, 200, 50)))
        btn_new = Button("NEW PROJECT", mx + 75, my + 100, 300, 50, color=(60, 120, 60))
        btn_new.on_click = lambda: self._set_launcher_state("SETTINGS")
        self.launcher_panel.add_child(btn_new)
        btn_load = Button("LOAD PROJECT", mx + 75, my + 170, 300, 50, color=(60, 60, 120))
        btn_load.on_click = self._load_all
        self.launcher_panel.add_child(btn_load)

    def _build_launcher_settings(self, mx, my):
        self.launcher_panel.add_child(Label("SET MAP DIMENSIONS", mx + 20, my + 20, 18, (100, 255, 100)))
        self.launcher_panel.add_child(Label("WIDTH", mx + 50, my + 100, 14))
        self.lbl_w = Label(str(self.map_width), mx + 210, my + 100, 16)
        self.launcher_panel.add_child(self.lbl_w)
        btn_w_up = Button("+", mx + 280, my + 95, 40, 30); btn_w_up.on_click = lambda: self._mod_w(10)
        btn_w_dn = Button("-", mx + 140, my + 95, 40, 30); btn_w_dn.on_click = lambda: self._mod_w(-10)
        self.launcher_panel.add_child(btn_w_up); self.launcher_panel.add_child(btn_w_dn)
        self.launcher_panel.add_child(Label("HEIGHT", mx + 50, my + 170, 14))
        self.lbl_h = Label(str(self.map_height), mx + 210, my + 170, 16)
        self.launcher_panel.add_child(self.lbl_h)
        btn_h_up = Button("+", mx + 280, my + 165, 40, 30); btn_h_up.on_click = lambda: self._mod_h(10)
        btn_h_dn = Button("-", mx + 140, my + 165, 40, 30); btn_h_dn.on_click = lambda: self._mod_h(-10)
        self.launcher_panel.add_child(btn_h_up); self.launcher_panel.add_child(btn_h_dn)
        btn_create = Button("CREATE", mx + 125, my + 260, 200, 50, color=(50, 150, 50))
        btn_create.on_click = self._init_editor
        self.launcher_panel.add_child(btn_create)

    def _build_sidebar_content(self, sb_x, sh):
        self.editor_panel.add_child(Label("8251 EDITOR v7.0", sb_x + 20, 15, 18, (100, 255, 100)))
        
        # Layer Tabs
        layers_txt = ["FLOOR", "WALL", "FURN"]
        for i, t in enumerate(layers_txt):
            btn = Button(t, sb_x + 10 + (i*85), 50, 80, 30, color=(70,70,80) if self.current_layer != i else (100,100,150))
            btn.on_click = (lambda l=i: lambda: self._set_layer(l))()
            self.editor_panel.add_child(btn)

        self.palette_panel = Panel(sb_x + 10, 100, 260, sh - 250, color=(30, 30, 35, 150))
        self.editor_panel.add_child(self.palette_panel)
        
        btn_save = Button("SAVE", sb_x + 10, sh - 100, 260, 40, color=(50, 100, 50)); btn_save.on_click = self._save_all
        self.editor_panel.add_child(btn_save)
        self._refresh_palette()

    def _refresh_palette(self):
        if not self.palette_panel: return
        self.palette_panel.children.clear()
        px, py = self.palette_panel.rect.x + 15, self.palette_panel.rect.y + 15
        
        cat = ["FLOORS", "WALLS", "INTERACT"][self.current_layer]
        self.palette_panel.add_child(Label(f"Category: {cat}", px, py, 14, (200, 200, 200))); py += 30
        
        # Wall Height Control
        if self.current_layer >= 1:
            self.palette_panel.add_child(Label(f"Stack Height: {self.brush_size_z:.1f}", px, py, 12))
            btn_up = Button("+", px + 150, py, 30, 20); btn_up.on_click = lambda: self._mod_brush_height(0.5)
            btn_dn = Button("-", px + 190, py, 30, 20); btn_dn.on_click = lambda: self._mod_brush_height(-0.5)
            self.palette_panel.add_child(btn_up); self.palette_panel.add_child(btn_dn)
            py += 35

        tiles = self.tileset.get(cat, {})
        for tid_str, name in list(tiles.items())[:10]:
            tid = int(tid_str)
            btn = Button(name[:15], px, py, 230, 30, color=(60,60,70))
            btn.on_click = (lambda t=tid: lambda: self._set_tile_brush(t))()
            self.palette_panel.add_child(btn); py += 35

    def _set_launcher_state(self, s): self.launcher_state = s; self._update_layout()
    def _mod_w(self, v): self.map_width = max(10, min(100, self.map_width + v)); self.lbl_w.set_text(str(self.map_width))
    def _mod_h(self, v): self.map_height = max(10, min(100, self.map_height + v)); self.lbl_h.set_text(str(self.map_height))
    def _init_editor(self): self.initialized = True; self._update_layout()
    def _set_layer(self, l): self.current_layer = l; self._update_layout()
    def _set_tile_brush(self, tid): self.brush_tile_id = tid
    def _mod_brush_height(self, a): self.brush_size_z = max(0.5, self.brush_size_z + a); self._refresh_palette()

    def update(self, dt, services):
        sw, sh = pygame.display.get_surface().get_size()
        if (sw, sh) != self.last_screen_size:
            self.last_screen_size = (sw, sh); self._update_layout()

        if not self.initialized:
            for event in pygame.event.get(): self.ui_root.handle_event(event)
            return

        input_mgr = services["input"]; renderer = services["renderer"]
        mx, my = pygame.mouse.get_pos()
        if mx >= sw - self.panel_width: return

        # Exact Snap (Centered in grid cell)
        grid_pos = input_mgr.get_mouse_grid_pos(renderer.camera)
        gx, gy = int(round(grid_pos.x)), int(round(grid_pos.y))
        self.hover_grid_pos = (gx, gy)

        l_click = pygame.mouse.get_pressed()[0]
        r_click = pygame.mouse.get_pressed()[2]
        
        if l_click or r_click:
            if not self.is_dragging:
                self.is_dragging = True; self.drag_start = (gx, gy); self.drag_mode = 1 if l_click else 3
            self.drag_current = (gx, gy)
        else:
            if self.is_dragging:
                self._apply_drag_action(); self.is_dragging = False; self.drag_start = None

        if pygame.mouse.get_pressed()[1]:
            rel = pygame.mouse.get_rel()
            renderer.camera.position.x -= rel[0] / renderer.camera.zoom
            renderer.camera.position.y -= rel[1] / renderer.camera.zoom
        else: pygame.mouse.get_rel()

    def _apply_drag_action(self):
        if not self.drag_start or not self.drag_current: return
        x1, x2 = min(self.drag_start[0], self.drag_current[0]), max(self.drag_start[0], self.drag_current[0])
        y1, y2 = min(self.drag_start[1], self.drag_current[1]), max(self.drag_start[1], self.drag_current[1])
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                if self.drag_mode == 1: self._place_tile(x, y)
                else: self._remove_tile(x, y)

    def _place_tile(self, gx, gy):
        hw, hh = self.map_width // 2, self.map_height // 2
        if abs(gx) > hw or abs(gy) > hh: return
        layer = self.current_layer
        if (gx, gy) in self.layers[layer]:
            old = self.layers[layer][(gx, gy)]
            if old.tid == self.brush_tile_id and old.size_z == self.brush_size_z: return
            self.remove_child(old)
        new_tile = TileNode(self.brush_tile_id, gx, gy, layer, self.brush_size_z)
        self.add_child(new_tile); self.layers[layer][(gx, gy)] = new_tile

    def _remove_tile(self, gx, gy):
        layer = self.current_layer
        if (gx, gy) in self.layers[layer]:
            self.remove_child(self.layers[layer][(gx, gy)]); del self.layers[layer][(gx, gy)]

    def _save_all(self):
        data = {"width": self.map_width, "height": self.map_height, "layers": {0:[], 1:[], 2:[]}}
        for l_idx, l_data in self.layers.items():
            for tile in l_data.values(): data["layers"][l_idx].append(tile.to_dict())
        with open("assets/maps/map_v2.json", "w") as f: json.dump(data, f, indent=4)
        print("Saved map_v2.json")

    def _load_all(self):
        self.initialized = True; self._update_layout()

    def draw_gizmos(self, screen, camera):
        if not self.initialized: return
        hw, hh = self.map_width // 2, self.map_height // 2
        # Grid
        for x in range(-hw, hw + 1):
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(x-0.5, -hh-0.5))
            p2 = camera.world_to_screen(*IsoMath.cart_to_iso(x-0.5, hh+0.5))
            pygame.draw.line(screen, (70, 70, 80), p1, p2, 1)
        for y in range(-hh, hh + 1):
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(-hw-0.5, y-0.5))
            p2 = camera.world_to_screen(*IsoMath.cart_to_iso(hw+0.5, y-0.5))
            pygame.draw.line(screen, (70, 70, 80), p1, p2, 1)
        # Boundary
        corners = [(-hw-0.5, -hh-0.5), (hw+0.5, -hh-0.5), (hw+0.5, hh+0.5), (-hw-0.5, hh+0.5)]
        pts = [camera.world_to_screen(*IsoMath.cart_to_iso(c[0], c[1])) for c in corners]
        pygame.draw.lines(screen, (255, 50, 50), True, pts, 3)
        # Highlight (Aligned to Grid Cell)
        hx, hy = self.hover_grid_pos
        if abs(hx) <= hw and abs(hy) <= hh:
            pts = [camera.world_to_screen(*IsoMath.cart_to_iso(hx-0.5, hy-0.5)), camera.world_to_screen(*IsoMath.cart_to_iso(hx+0.5, hy-0.5)), camera.world_to_screen(*IsoMath.cart_to_iso(hx+0.5, hy+0.5)), camera.world_to_screen(*IsoMath.cart_to_iso(hx-0.5, hy+0.5))]
            pygame.draw.polygon(screen, (255, 255, 0, 100), pts, 2)