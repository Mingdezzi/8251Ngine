import pygame
import math
import random
from engine.core.component import Component

class StatusComponent(Component):
    def __init__(self, hp=100, ap=100):
        super().__init__()
        # Core Stats
        self.max_hp = hp
        self.hp = hp
        self.max_ap = ap
        self.ap = ap
        self.stamina = 100.0
        
        # Emotions (0.0 to 1.0)
        self.anxiety = 0.0
        self.fear = 0.0
        self.pain = 0.0
        
        # Feedback
        self.shiver_offset = [0, 0]
        self.is_dead = False

    def _on_added(self, node):
        self.node = node

    def update(self, dt, services):
        if self.hp <= 0:
            self.is_dead = True
            return

        # 떨림 효과 계산
        if self.anxiety > 0.5 or self.fear > 0.3:
            intensity = (self.anxiety + self.fear) * 2.0
            self.shiver_offset[0] = random.uniform(-intensity, intensity)
            self.shiver_offset[1] = random.uniform(-intensity, intensity)
        else:
            self.shiver_offset = [0, 0]

        # 자연 회복
        self.stamina = min(100.0, self.stamina + dt * 5.0)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        self.pain = min(1.0, self.pain + amount * 0.05)
        self.fear = min(1.0, self.fear + 0.2)
