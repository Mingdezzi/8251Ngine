import pygame
from engine.core.node import Node
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT

class Block3D(Node):
    def __init__(self, name="Block", size_z=1.0, color=(150, 150, 150)):
        super().__init__(name)
        self.size_z = size_z
        self.color = color
        self.cached_surf = None
        self._regen_texture()

    def _regen_texture(self):
        # Calculate surface size needed
        # height of sides in pixels
        h_px = self.size_z * 32 
        
        # Surface must be large enough for diamond + height
        self.cached_surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + h_px), pygame.SRCALPHA)
        
        # Draw the cube onto this surface
        # Pivot point is mid-bottom of the surface
        
        # 1. Draw Shadow (Optimized Blob)
        # Shadow is drawn relative to the base position
        shadow_rect = pygame.Rect(
            TILE_WIDTH // 4, 
            TILE_HEIGHT // 4, 
            TILE_WIDTH // 2, 
            TILE_HEIGHT // 2
        )
        # Shift shadow based on Z height to fake light direction or keep centered?
        # Centered blob is standard for 'fake' shadow.
        # Draw transparent black ellipse
        pygame.draw.ellipse(self.cached_surf, (0, 0, 0, 100), shadow_rect)

        # 2. Draw Cube (Offset by height)
        # We draw the cube 'above' the shadow
        # The 'y' argument in draw_cube is the top-corner of the BOTTOM face.
        # Top face is drawn at y - height.
        # So we must start drawing at y = h_px to allow space for the side faces above.
        IsoGeometry.draw_cube(
            self.cached_surf, 
            TILE_WIDTH // 2, h_px, 
            TILE_WIDTH, TILE_HEIGHT, 
            h_px, 
            self.color
        )

    def get_sprite(self):
        return self.cached_surf
