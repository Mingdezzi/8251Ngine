import pygame
from engine.core.node import Node
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT, HEIGHT_SCALE
from engine.assets.tile_engine import TileEngine

# Global cache to prevent redundant surface creation
BLOCK_CACHE = {}

class Block3D(Node):
    def __init__(self, name="Block", size_z=1.0, color=(150, 150, 150), zone_id=0, interact_type="NONE", tile_id=None):
        super().__init__(name)
        self.size_z = size_z # 시각적 높이
        self.color = color
        self.zone_id = zone_id
        self.interact_type = interact_type
        self.tile_id = tile_id
        self.cached_surf = None
        self._regen_texture()

    def _regen_texture(self):
        cache_key = (self.size_z, self.color, self.tile_id)
        
        if cache_key in BLOCK_CACHE:
            self.cached_surf = BLOCK_CACHE[cache_key]
            return

        sid = str(self.tile_id) if self.tile_id else ""
        category = sid[0] if len(sid) >= 1 else "0"
        
        is_floor = category == '1' or self.size_z < 0.1
        is_wall = category == '2'
        
        visual_height_px = 0 if is_floor else int(self.size_z * HEIGHT_SCALE)
        
        surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + visual_height_px), pygame.SRCALPHA)
        
        draw_color = self.color
        if self.tile_id and self.tile_id in TileEngine.TILE_DATA:
            draw_color = TileEngine.TILE_DATA[self.tile_id]['color']

        if is_floor:
            # --- 바닥 (Flat Zomboid Style) ---
            tile_tex = TileEngine.create_texture(self.tile_id)
            iso_tex = pygame.transform.smoothscale(tile_tex, (TILE_WIDTH, TILE_HEIGHT))
            
            top_mask = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
            points = [(TILE_WIDTH // 2, 0), (TILE_WIDTH, TILE_HEIGHT // 2), (TILE_WIDTH // 2, TILE_HEIGHT), (0, TILE_HEIGHT // 2)]
            pygame.draw.polygon(top_mask, (255, 255, 255, 255), points)
            pygame.draw.polygon(top_mask, (0, 0, 0, 60), points, 1) 
            
            iso_tex.blit(top_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(iso_tex, (0, visual_height_px))
            
        else: # 벽 또는 사물
            # --- 얇은 벽 / 입체 사물 공통 로직 ---
            depth_px = int(0.1 * HEIGHT_SCALE) if is_wall else visual_height_px # 벽은 얇게, 사물은 두껍게
            
            # 1. 기본 큐브 형태 그리기
            IsoGeometry.draw_cube(surf, TILE_WIDTH // 2, visual_height_px, TILE_WIDTH, TILE_HEIGHT, depth_px, draw_color)
            
            # 2. 윗면에 텍스처 합성
            if self.tile_id:
                tile_tex = TileEngine.create_texture(self.tile_id)
                iso_tex = pygame.transform.smoothscale(tile_tex, (TILE_WIDTH, TILE_HEIGHT))
                top_mask = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
                points = [(TILE_WIDTH // 2, 0), (TILE_WIDTH, TILE_HEIGHT // 2), (TILE_WIDTH // 2, TILE_HEIGHT), (0, TILE_HEIGHT // 2)]
                pygame.draw.polygon(top_mask, (255, 255, 255, 255), points)
                iso_tex.blit(top_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(iso_tex, (0, 0)) # 윗면은 항상 y=0 에서 시작

            # 3. 벽일 경우, 측면에 텍스처 타일링 (Zomboid 스타일)
            if is_wall and self.tile_id:
                wall_tex = TileEngine.create_texture(self.tile_id)
                side_darken = pygame.Surface((32, 32), pygame.SRCALPHA)
                side_darken.fill((0, 0, 0, 100)) # 측면을 어둡게 할 오버레이
                
                # 텍스처 시트 만들기
                tiled_texture = pygame.Surface((TILE_WIDTH, visual_height_px), pygame.SRCALPHA)
                for y in range(0, visual_height_px, 32):
                    tiled_texture.blit(wall_tex, (0, y))
                    tiled_texture.blit(side_darken, (0, y), special_flags=pygame.BLEND_RGBA_MULT)

                # This gets tricky. Revert to `draw_cube` with very small depth, then darken the sides after.

                # Let's just use `draw_cube` and rely on `wall_depth_px` being small for thinness.
                # The subtle shadow effect will be important.
                left_side_color = tuple(int(c * 0.6) for c in draw_color)
                right_side_color = tuple(int(c * 0.8) for c in draw_color)
                
                # 좌측면 덮어쓰기
                left_poly = [(0, TILE_HEIGHT//2), (TILE_WIDTH//2, 0), (TILE_WIDTH//2, visual_height_px), (0, TILE_HEIGHT//2 + visual_height_px)]
                pygame.draw.polygon(surf, left_side_color, left_poly)
                # 우측면 덮어쓰기
                right_poly = [(TILE_WIDTH, TILE_HEIGHT//2), (TILE_WIDTH//2, 0), (TILE_WIDTH//2, visual_height_px), (TILE_WIDTH, TILE_HEIGHT//2 + visual_height_px)]
                pygame.draw.polygon(surf, right_side_color, right_poly)

        BLOCK_CACHE[cache_key] = surf
        self.cached_surf = surf

    def get_sprite(self):
        return self.cached_surf

# Clear cache on module reload to ensure changes take effect
BLOCK_CACHE.clear()
