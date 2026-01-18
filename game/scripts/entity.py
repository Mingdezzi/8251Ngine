import pygame
import math
from engine.graphics.animated_sprite import AnimatedSprite
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT

class GameEntity(AnimatedSprite):
    def __init__(self, name="Entity", color=(200, 200, 200), client_id=None):
        super().__init__(name)
        self.color = color
        self.walk_timer = 0.0
        self.is_moving = False
        self.client_id = client_id # 네트워크 ID
        
        self._setup_procedural_animations()

    def _setup_procedural_animations(self):
        from engine.graphics.animation import Animation
        
        def create_frame(height_mod, tilt):
            surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + 40), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (0, 0, 0, 80), (16, 32, 32, 16))
            IsoGeometry.draw_cube(surf, 32, 10 + height_mod, TILE_WIDTH, TILE_HEIGHT, 32, self.color)
            return surf

        idle_frames = [create_frame(0, 0)]
        walk_frames = [create_frame(-2, 2), create_frame(0, 0), create_frame(-2, -2), create_frame(0, 0)]
        
        self.anim_player.add_animation("idle", Animation(idle_frames, 0.5))
        self.anim_player.add_animation("walk", Animation(walk_frames, 0.15))
        self.anim_player.play("idle")

    def update(self, dt, services):
        if self.is_moving:
            self.anim_player.play("walk")
        else:
            self.anim_player.play("idle")
        
        super().update(dt, services)
        self.is_moving = False
