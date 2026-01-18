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
from engine.ui.gui import Control, Label, Panel, Button, LineEdit

# Components
from engine.core.status import StatusComponent
from engine.core.inventory import InventoryComponent
from engine.core.ai import AdvancedAIComponent

class EditorScene(Node):
    def __init__(self):
        super().__init__("EditorScene")
        self.layers = {0: {}, 1: {}, 2: {}}
        self.entities = {}
        self.ui_root = Control(0, 0, 1280, 720)
        
        self.selected_obj = None
        self.is_playing = False
        self.initialized = False
        
        self.panel_width = 280
        self.hierarchy_width = 200
        
        self.mode = "TILES"
        self.current_category = "FLOORS"
        self.map_width, self.map_height = 30, 30
        
        self.brush_tile_id = 1110000
        self.brush_size_z = 1.0
        self.tileset = {}
        self._load_tileset_data()
        
        self.hover_grid_pos = (0, 0)
        self.is_dragging = False
        self.drag_start = None
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
            launcher = Panel(mx, my, mw, mh, color=(40, 40, 50, 250))
            self.ui_root.add_child(launcher)
            launcher.add_child(Label("8251 ENGINE - IDE v1.2", mx + 20, my + 20, 20, (255, 200, 50)))
            btn_new = Button("NEW PROJECT", mx + 75, my + 100, 300, 50, color=(60, 120, 60))
            btn_new.on_click = self._init_editor
            launcher.add_child(btn_new)
            btn_load = Button("LOAD PROJECT", mx + 75, my + 170, 300, 50, color=(60, 60, 120))
            btn_load.on_click = self._load_all
            launcher.add_child(btn_load)
        else:
            self.hier_panel = Panel(0, 0, self.hierarchy_width, sh, color=(30, 30, 35, 220))
            self.ui_root.add_child(self.hier_panel)
            self._build_hierarchy_content()

            sb_x = sw - self.panel_width
            self.sidebar = Panel(sb_x, 0, self.panel_width, sh, color=(35, 35, 40, 245))
            self.ui_root.add_child(self.sidebar)
            self._build_sidebar_content(sb_x, sh)
            
            map_view_w = sw - self.panel_width - self.hierarchy_width
            self._services["renderer"].camera.offset = pygame.math.Vector2(self.hierarchy_width + map_view_w / 2, sh / 2)

    def _build_hierarchy_content(self):
        self.hier_panel.add_child(Label("HIERARCHY", 10, 10, 16, (200, 200, 200)))
        y = 45
        for i, child in enumerate(self.children):
            if i > 20: break
            btn_node = Button(f"{child.tag[:15]}", 5, y, 190, 25, color=(50, 50, 60) if self.selected_obj != child else (80, 80, 150))
            btn_node.on_click = (lambda c=child: lambda: self._select_object(c))()
            self.hier_panel.add_child(btn_node); y += 28

    def _build_sidebar_content(self, sb_x, sh):
        play_txt = "STOP GAME" if self.is_playing else "▶ PLAY GAME"
        btn_play = Button(play_txt, sb_x + 10, 10, 260, 40, color=(150, 50, 50) if self.is_playing else (50, 150, 50))
        btn_play.on_click = self._toggle_play_mode
        self.sidebar.add_child(btn_play)

        tabs = ["TILES", "INSPECT", "SETTINGS"]
        for i, t in enumerate(tabs):
            btn = Button(t[:7], sb_x + 10 + (i*85), 60, 80, 30, color=(70,70,80) if self.mode != t else (100,100,150))
            btn.on_click = (lambda m=t: lambda: self._set_mode(m))()
            self.sidebar.add_child(btn)
        
        self.palette_panel = Panel(sb_x + 10, 100, 260, sh - 150, color=(0,0,0,0))
        self.sidebar.add_child(self.palette_panel)
        self._refresh_palette()

    def _refresh_palette(self):
        if not self.palette_panel: return
        self.palette_panel.children.clear()
        px, py = self.palette_panel.rect.x + 10, self.palette_panel.rect.y + 10
        
        if self.mode == "TILES":
            # 1. Category Tabs (F, W, D, I)
            cat_list = ["FLOORS", "WALLS", "DECO", "INTERACT"]
            for i, c in enumerate(cat_list):
                btn_c = Button(c[:1], px + i*45, py, 40, 25, color=(80,80,100) if self.current_category != c else (150,150,255))
                btn_c.on_click = (lambda cat=c: lambda: self._set_category(cat))()
                self.palette_panel.add_child(btn_c)
            py += 40
            
            # 2. Tile Selection List
            tiles = self.tileset.get(self.current_category, {})
            for tid_str, name in list(tiles.items())[:10]:
                tid = int(tid_str); btn = Button(name[:15], px, py, 230, 30, color=(60,60,70))
                btn.on_click = (lambda t=tid: lambda: self._set_tile_brush(t))()
                self.palette_panel.add_child(btn); py += 35
        
        elif self.mode == "INSPECT":
            if not self.selected_obj:
                self.palette_panel.add_child(Label("Select a Node", px, py, 14, (150,150,150)))
                return
            obj = self.selected_obj
            self.palette_panel.add_child(Label(f"Node: {obj.tag}", px, py, 14, (100, 255, 100))); py += 35
            self.palette_panel.add_child(Label("Tag (ID):", px, py, 12)); py += 18
            le_tag = LineEdit(obj.tag, px, py, 230, 30); le_tag.on_text_changed = lambda val: setattr(obj, 'tag', val)
            self.palette_panel.add_child(le_tag); py += 45
            for comp in obj.components:
                self.palette_panel.add_child(Label(f"[{comp.__class__.__name__}]", px, py, 13, (255, 200, 50))); py += 25
                for attr in dir(comp):
                    if attr.startswith("_") or attr in ["update", "ready", "node"]: continue
                    val = getattr(comp, attr)
                    if isinstance(val, (int, float, str)) and not callable(val):
                        self.palette_panel.add_child(Label(f"{attr}:", px + 10, py, 11)); py += 15
                        le_v = LineEdit(str(val), px + 10, py, 210, 25)
                        def make_s(c, a, t): return lambda v: setattr(c, a, t(v)) if v else None
                        le_v.on_text_changed = make_s(comp, attr, type(val)); self.palette_panel.add_child(le_v); py += 30
            py += 10
            btn_add = Button("+ ADD AI COMPONENT", px, py, 230, 35, color=(60, 100, 150))
            btn_add.on_click = self._add_ai; self.palette_panel.add_child(btn_add)

    def _add_ai(self):
        if self.selected_obj and not self.selected_obj.get_component(AdvancedAIComponent):
            self.selected_obj.add_component(AdvancedAIComponent()); self._refresh_palette()

    def _toggle_play_mode(self): self.is_playing = not self.is_playing; self.selected_obj = None; self._update_layout()
    def _select_object(self, obj): self.selected_obj = obj; self.mode = "INSPECT"; self._refresh_palette()
    def _init_editor(self): self.initialized = True; self._update_layout()
    def _set_mode(self, m): self.mode = m; self._refresh_palette()
    def _set_category(self, c): self.current_category = c; self._refresh_palette()
    def _set_tile_brush(self, t): self.brush_tile_id = t

    def update(self, dt, services):
        sw, sh = pygame.display.get_surface().get_size()
        if (sw, sh) != self.last_screen_size: self.last_screen_size = (sw, sh); self._update_layout()
        for event in pygame.event.get():
            self.ui_root.handle_event(event)
            if event.type == pygame.QUIT: os._exit(0)

        if not self.initialized: return

        if self.is_playing:
            input_mgr = services["input"]; mv_x, mv_y = input_mgr.get_vector("move_left", "move_right", "move_up", "move_down")
            for child in self.children:
                if child.tag == "PLAYER":
                    child.position.x += mv_x * 5.0 * dt; child.position.y += mv_y * 5.0 * dt
                    child.is_moving = (mv_x != 0 or mv_y != 0)
                    services["renderer"].camera.follow(child.position.x, child.position.y)
            super().update(dt, services); return

        input_mgr = services["input"]; renderer = services["renderer"]
        mx, my = pygame.mouse.get_pos()
        if mx < self.hierarchy_width or mx >= sw - self.panel_width: return

        grid_pos = input_mgr.get_mouse_grid_pos(renderer.camera)
        gx, gy = int(round(grid_pos.x)), int(round(grid_pos.y))
        self.hover_grid_pos = (gx, gy)

        if pygame.mouse.get_pressed()[0] and not self.is_dragging:
            found = False
            for l in [2, 1, 0]:
                if (gx, gy) in self.layers[l]: self._select_object(self.layers[l][(gx, gy)]); found = True; break
            if not found: self.selected_obj = None; self._update_layout()

        if pygame.mouse.get_pressed()[0] and not self.selected_obj:
            if not self.is_dragging: self.is_dragging = True; self.drag_start = (gx, gy); self.drag_mode = 1
            self.drag_current = (gx, gy)
        elif pygame.mouse.get_pressed()[2]:
            if not self.is_dragging: self.is_dragging = True; self.drag_start = (gx, gy); self.drag_mode = 3
            self.drag_current = (gx, gy)
        else:
            if self.is_dragging: self._apply_drag_action(); self.is_dragging = False; self.drag_start = None

        if pygame.mouse.get_pressed()[1]:
            rel = pygame.mouse.get_rel(); renderer.camera.position.x -= rel[0] / renderer.camera.zoom; renderer.camera.position.y -= rel[1] / renderer.camera.zoom
        else: pygame.mouse.get_rel()

    def _apply_drag_action(self):
        if not self.drag_start or not self.drag_current: return
        x1, x2 = min(self.drag_start[0], self.drag_current[0]), max(self.drag_start[0], self.drag_current[0])
        y1, y2 = min(self.drag_start[1], self.drag_current[1]), max(self.drag_start[1], self.drag_current[1])
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                if self.drag_mode == 1: self._place_tile(x, y)
                else: self._remove_tile(x, y)
        self._update_layout()

    def _place_tile(self, gx, gy):
        hw, hh = self.map_width // 2, self.map_height // 2
        if abs(gx) > hw or abs(gy) > hh: return
        
        # Layer Auto-Decision: F->0, W->1, others->2
        layer = 0
        if self.current_category == "WALLS": layer = 1
        elif self.current_category in ["DECO", "INTERACT"]: layer = 2
        
        if (gx, gy) in self.layers[layer]:
            if self.layers[layer][(gx, gy)].tid == self.brush_tile_id: return
            self.remove_child(self.layers[layer][(gx, gy)])
            
        new_tile = TileNode(self.brush_tile_id, gx, gy, layer, self.brush_size_z if layer > 0 else 0.1)
        new_tile.tag = f"{self.current_category[:1]}_{gx}_{gy}"
        self.add_child(new_tile); self.layers[layer][(gx, gy)] = new_tile

    def _remove_tile(self, gx, gy):
        for l in range(3):
            if (gx, gy) in self.layers[l]: self.remove_child(self.layers[l][(gx, gy)]); del self.layers[l][(gx, gy)]

    def _save_all(self):
        data = {"width": self.map_width, "height": self.map_height, "layers": {0:[], 1:[], 2:[]}}
        for l_idx, l_data in self.layers.items():
            for tile in l_data.values(): data["layers"][str(l_idx)].append(tile.to_dict())
        with open("assets/maps/map_v2.json", "w") as f: json.dump(data, f, indent=4)
        print("Saved map_v2.json")

    def _load_all(self):
        path = "assets/maps/map_v2.json"
        if os.path.exists(path):
            with open(path, "r") as f: data = json.load(f)
            self.map_width, self.map_height = data.get("width", 30), data.get("height", 30)
            for l in range(3):
                for t in list(self.layers[l].values()): self.remove_child(t)
                self.layers[l].clear()
            for l_idx_str, tiles in data.get("layers", {}).items():
                l_idx = int(l_idx_str)
                for t in tiles:
                    nt = TileNode(t["tid"], t["pos"][0], t["pos"][1], t["layer"], t.get("size_z", 0.1))
                    nt.tag = t.get("tag", f"Node_{int(nt.position.x)}_{int(nt.position.y)}")
                    self.add_child(nt); self.layers[l_idx][(int(nt.position.x), int(nt.position.y))] = nt
        self._init_editor()

    def draw_gizmos(self, screen, camera):
        if not self.initialized: return
        hw, hh = self.map_width // 2, self.map_height // 2
        for x in range(-hw, hw + 2):
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(x-0.5, -hh-0.5)); p2 = camera.world_to_screen(*IsoMath.cart_to_iso(x-0.5, hh+0.5))
            pygame.draw.line(screen, (70, 70, 80), p1, p2, 1)
        for y in range(-hh, hh + 2):
            p1 = camera.world_to_screen(*IsoMath.cart_to_iso(-hw-0.5, y-0.5)); p2 = camera.world_to_screen(*IsoMath.cart_to_iso(hw+0.5, y-0.5))
            pygame.draw.line(screen, (70, 70, 80), p1, p2, 1)
        if not self.is_playing:
            hx, hy = self.hover_grid_pos
            if abs(hx) <= hw and abs(hy) <= hh:
                pts = [camera.world_to_screen(*IsoMath.cart_to_iso(hx-0.5, hy-0.5)), camera.world_to_screen(*IsoMath.cart_to_iso(hx+0.5, hy-0.5)), camera.world_to_screen(*IsoMath.cart_to_iso(hx+0.5, hy+0.5)), camera.world_to_screen(*IsoMath.cart_to_iso(hx-0.5, hy+0.5))]
                pygame.draw.polygon(screen, (255, 255, 0, 100), pts, 2)
            if self.selected_obj:
                sx, sy = camera.world_to_screen(*IsoMath.cart_to_iso(self.selected_obj.position.x, self.selected_obj.position.y))
                pygame.draw.circle(screen, (255, 255, 0), (int(sx), int(sy)), 20, 3)
            if self.is_dragging and self.drag_start:
                dx1, dx2 = min(self.drag_start[0], self.hover_grid_pos[0]), max(self.drag_start[0], self.hover_grid_pos[0])
                dy1, dy2 = min(self.drag_start[1], self.hover_grid_pos[1]), max(self.drag_start[1], self.hover_grid_pos[1])
                c1 = camera.world_to_screen(*IsoMath.cart_to_iso(dx1-0.5, dy1-0.5)); c3 = camera.world_to_screen(*IsoMath.cart_to_iso(dx2+0.5, dy2+0.5))
                c2 = camera.world_to_screen(*IsoMath.cart_to_iso(dx2+0.5, dy1-0.5)); c4 = camera.world_to_screen(*IsoMath.cart_to_iso(dx1-0.5, dy2+0.5))
                pygame.draw.lines(screen, (0, 255, 255) if self.drag_mode == 1 else (255, 50, 50), True, [c1, c2, c3, c4], 3)

    def _draw(self, services):
        super()._draw(services)
        self.game_ui_root.draw(services["renderer"].screen, services)
