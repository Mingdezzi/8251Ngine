import pygame
import math
import random
from engine.graphics.animated_sprite import AnimatedSprite
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT
from engine.core.status import StatusComponent
from engine.graphics.custom_renderer import CustomizationComponent
from engine.core.inventory import InventoryComponent

class GameEntity(AnimatedSprite):
    def __init__(self, name="Entity", skin_color=(255, 220, 180), clothes_color=(50, 100, 200), client_id=None):
        super().__init__(name)
        self.client_id = client_id
        self.is_moving = False
        
        # --- Components ---
        self.status = self.add_component(StatusComponent())
        self.custom = self.add_component(CustomizationComponent(skin_color, clothes_color))
        self.inventory = self.add_component(InventoryComponent())
        
        # Network Interpolation
        self.target_pos = None
        self.lerp_speed = 10.0
        
        self._setup_procedural_animations()

    def _setup_procedural_animations(self):
        from engine.graphics.animation import Animation
        
        def create_frame(height_mod, tilt):
            # 캐릭터 커스텀 컬러 가져오기
            skin = self.custom.skin_color
            clothes = self.custom.clothes_color
            
            surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + 40), pygame.SRCALPHA)
            # 발 밑 그림자
            pygame.draw.ellipse(surf, (0, 0, 0, 80), (16, 32, 32, 16))
            
            # 몸체 (의상)
            IsoGeometry.draw_cube(surf, 32, 25 + height_mod, TILE_WIDTH, 20, 20, clothes)
            # 머리 (피부)
            IsoGeometry.draw_cube(surf, 32, 10 + height_mod, 24, 16, 16, skin)
            
            return surf

        idle_frames = [create_frame(0, 0)]
        walk_frames = [create_frame(-2, 2), create_frame(0, 0), create_frame(-2, -2), create_frame(0, 0)]
        
        self.anim_player.add_animation("idle", Animation(idle_frames, 0.5))
        self.anim_player.add_animation("walk", Animation(walk_frames, 0.15))
        self.anim_player.play("idle")

    def update(self, dt, services):
        # 감정에 따른 떨림 효과 적용
        self.offset_y = self.status.shiver_offset[1] * 0.1

        # 네트워크 보간
        if self.target_pos:
            curr_pos = pygame.math.Vector2(self.position.x, self.position.y)
            new_pos = curr_pos.lerp(self.target_pos, min(1.0, dt * self.lerp_speed))
            self.position.x, self.position.y = new_pos.x, new_pos.y
            self.is_moving = curr_pos.distance_to(self.target_pos) > 0.05
            if not self.is_moving: self.target_pos = None

        if self.is_moving:
            self.anim_player.play("walk")
        else:
            self.anim_player.play("idle")
        
        super().update(dt, services)

    def set_network_pos(self, x, y):
        if self.target_pos is None:
            self.position.x, self.position.y = x, y
        self.target_pos = pygame.math.Vector2(x, y)

    def fire_weapon(self, direction, services):
        """총기 발사 로직"""
        combat = services.get("combat")
        if combat and self.status.ap >= 5:
            self.status.ap -= 5
            # 탄환 발사 위치 (머리 높이쯤)
            spawn_pos = self.position.copy()
            spawn_pos.z += 1.5
            combat.spawn_bullet(spawn_pos, direction, 20, self.client_id)
            # 소음 발생
            services["interaction"].emit_noise(self.position.x, self.position.y, 15, (255, 100, 50))
            return True
        return False
