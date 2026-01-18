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
        self.facing_direction = pygame.math.Vector2(0, 1) # 초기 방향 (아래)
        
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
        # 감정/불안도에 따른 떨림 효과 적용 (Anxiety가 높을수록 심해짐)
        shiver = self.status.anxiety * 0.05
        self.offset_y = random.uniform(-shiver, shiver)
        self.offset_x = random.uniform(-shiver, shiver)

        # 네트워크 보간 및 이동 상태 업데이트
        if self.target_pos:
            prev_pos = pygame.math.Vector2(self.position.x, self.position.y)
            curr_pos = pygame.math.Vector2(self.position.x, self.position.y)
            new_pos = curr_pos.lerp(self.target_pos, min(1.0, dt * self.lerp_speed))
            
            # 이동 방향에 따른 좌우 반전 (Flip)
            move_dir = new_pos - prev_pos
            if move_dir.x > 0.01: self.flip_h = False # 오른쪽 방향
            elif move_dir.x < -0.01: self.flip_h = True # 왼쪽 방향
            
            self.position.x, self.position.y = new_pos.x, new_pos.y
            self.is_moving = curr_pos.distance_to(self.target_pos) > 0.05
            if not self.is_moving: self.target_pos = None
        else:
            # 로컬 이동 시 방향 감지 (PxAnicScene 등에서 직접 이동시킬 때 대응)
            # 여기서는 Scene에서 위치를 직접 수정하므로, 이전 프레임 위치와 비교
            if not hasattr(self, "_prev_pos"): self._prev_pos = self.position.copy()
            move_delta = self.position - self._prev_pos
            if move_delta.x > 0.001: self.flip_h = False
            elif move_delta.x < -0.001: self.flip_h = True
            self._prev_pos = self.position.copy()

        if self.is_moving:
            self.anim_player.play("walk")
            # 걷는 속도에 따라 애니메이션 속도 조절
            self.anim_player.speed_scale = 1.5 if services["input"].is_action_pressed("run") else 1.0
        else:
            self.anim_player.play("idle")
            self.anim_player.speed_scale = 1.0
        
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
