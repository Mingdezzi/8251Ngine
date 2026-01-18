import pygame
from engine.core.node import Node
from engine.assets.tile_engine import TileEngine
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT, HEIGHT_SCALE

class WallNode(Node):
    def __init__(self, name="Wall", size_z=1.8, tile_id=None, color=(120, 120, 120), wall_type="NE"):
        super().__init__(name)
        self.size_z = size_z
        self.tile_id = tile_id
        self.color = color
        self.wall_type = wall_type # "NE" or "NW"
        self.cached_surf = None
        self._regen_texture()

    def _regen_texture(self):
        visual_height_px = int(self.size_z * HEIGHT_SCALE)
        
        # 서피스 크기는 벽 전체를 담을 수 있도록 계산
        # WallNode의 (0,0)은 아이소메트릭 타일의 최상단 꼭짓점(Top Corner)에 위치함
        # 따라서 너비는 TILE_WIDTH, 높이는 TILE_HEIGHT/2 + visual_height_px
        surf_height = TILE_HEIGHT / 2 + visual_height_px
        surf = pygame.Surface((TILE_WIDTH, surf_height), pygame.SRCALPHA)
        
        base_color = self.color
        if self.tile_id and self.tile_id in TileEngine.TILE_DATA:
            base_color = TileEngine.TILE_DATA[self.tile_id]['color']
        
        # wall_type에 따라 해당 면만 그림
        if self.wall_type == "NE":
            # 오른쪽 벽면 (밝은 면)
            # 폴리곤 좌표는 서피스 내의 상대 좌표
            right_face_poly = [
                (TILE_WIDTH / 2, 0),                           # Top-Center
                (TILE_WIDTH, TILE_HEIGHT / 2),                 # Middle-Right
                (TILE_WIDTH, TILE_HEIGHT / 2 + visual_height_px), # Bottom-Right
                (TILE_WIDTH / 2, visual_height_px)             # Bottom-Center
            ]
            pygame.draw.polygon(surf, base_color, right_face_poly)
        
        elif self.wall_type == "NW":
            # 왼쪽 벽면 (어두운 면)
            left_face_poly = [
                (TILE_WIDTH / 2, 0),                           # Top-Center
                (0, TILE_HEIGHT / 2),                          # Middle-Left
                (0, TILE_HEIGHT / 2 + visual_height_px),         # Bottom-Left
                (TILE_WIDTH / 2, visual_height_px)             # Bottom-Center
            ]
            darker_color = tuple(max(0, c - 40) for c in base_color)
            pygame.draw.polygon(surf, darker_color, left_face_poly)
            
        self.cached_surf = surf

    def get_sprite(self):
        return self.cached_surf
