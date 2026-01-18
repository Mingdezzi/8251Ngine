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
        self.size_z = size_z
        self.color = color
        self.zone_id = zone_id
        self.interact_type = interact_type
        self.tile_id = tile_id
        self.cached_surf = None
        self._regen_texture()

    def _regen_texture(self):
        # Generate a unique key for this block appearance
        cache_key = (self.size_z, self.color, self.tile_id)
        
        if cache_key in BLOCK_CACHE:
            self.cached_surf = BLOCK_CACHE[cache_key]
            return

        h_px = int(self.size_z * HEIGHT_SCALE)
        surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + h_px), pygame.SRCALPHA)
        
        # 1. Shadow (Optimized)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (TILE_WIDTH // 4, TILE_HEIGHT // 4, TILE_WIDTH // 2, TILE_HEIGHT // 2))

        # 2. Get Color from Tile ID if exists
        draw_color = self.color
        if self.tile_id and self.tile_id in TileEngine.TILE_DATA:
            draw_color = TileEngine.TILE_DATA[self.tile_id]['color']

        # 3. Draw Cube
        IsoGeometry.draw_cube(
            surf, 
            TILE_WIDTH // 2, h_px, 
            TILE_WIDTH, TILE_HEIGHT, 
            h_px, 
            draw_color
        )
        
        # Optional: Overlay the procedural texture from TileEngine on top face?
        # For now, we keep it simplified for performance.
        
        BLOCK_CACHE[cache_key] = surf
        self.cached_surf = surf

    def get_sprite(self):
        return self.cached_surf