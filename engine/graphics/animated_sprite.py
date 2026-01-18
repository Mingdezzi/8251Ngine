import pygame
from engine.core.node import Node
from engine.graphics.animation import AnimationPlayer

class AnimatedSprite(Node):
    def __init__(self, name="AnimatedSprite"):
        super().__init__(name)
        self.anim_player = AnimationPlayer()
        self.offset_y = 0 # For floating animations

    def update(self, dt, services):
        self.anim_player.update(dt)
        super().update(dt, services)

    def get_sprite(self):
        frame = self.anim_player.get_current_frame()
        if frame:
            if self.offset_y != 0:
                pass
            return frame
        return None
