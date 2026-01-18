import pygame
from engine.core.node import Node
from engine.assets.tile_engine import TileEngine
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT, HEIGHT_SCALE

class TileNode(Node):
    def __init__(self, tid, x, y, layer=0, size_z=0.1):
        super().__init__(f"Tile_{tid}")
        self.tid = tid
        self.position.x = x
        self.position.y = y
        self.position.z = 0 # Base is always on floor
        self.layer = layer # 0: Floor, 1: Wall, 2: Furniture
        self.size_z = size_z # [NEW] Height of the wall
        
        self.sprite = None
        self._regen_sprite()
        
        # Y-sorting: layer * 100 + grid depth
        self.z_index = layer * 100

    def _regen_sprite(self):
        # Determine properties from ID
        draw_color = TileEngine.TILE_DATA.get(self.tid, {}).get('color', (150, 150, 150))
        
        if self.layer == 0: # Flat Floor
            self.sprite = TileEngine.create_texture(self.tid)
            self.size_z = 0.05 # Near flat
        else: # Wall or Furniture (3D Cube)
            h_px = int(self.size_z * HEIGHT_SCALE)
            self.sprite = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + h_px), pygame.SRCALPHA)
            
            # Shadow
            pygame.draw.ellipse(self.sprite, (0, 0, 0, 80), (TILE_WIDTH // 4, TILE_HEIGHT // 4, TILE_WIDTH // 2, TILE_HEIGHT // 2))
            
            # Draw Cube with Tile color
            IsoGeometry.draw_cube(
                self.sprite, 
                TILE_WIDTH // 2, h_px, 
                TILE_WIDTH, TILE_HEIGHT, 
                h_px, 
                draw_color
            )

    def get_sprite(self):
        return self.sprite

    def to_dict(self):
        return {
            "tid": self.tid,
            "pos": [self.position.x, self.position.y],
            "layer": self.layer,
            "size_z": self.size_z
        }