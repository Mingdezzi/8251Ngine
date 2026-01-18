import pygame
from engine.core.node import Node
from engine.graphics.animation import AnimationPlayer

class AnimatedSprite(Node):
    def __init__(self, name="AnimatedSprite"):
        super().__init__(name)
        self.anim_player = AnimationPlayer()
        self.offset_y = 0 # For floating animations

    def update(self, dt):
        self.anim_player.update(dt)
        super().update(dt)

    def get_sprite(self):
        frame = self.anim_player.get_current_frame()
        if frame:
            # Check if we need to apply additional offsets (like bounce)
            if self.offset_y != 0:
                # This logic could be complex, for now just return frame
                pass
            return frame
        return None
