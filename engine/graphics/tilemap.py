import pygame
from engine.core.node import Node
from engine.graphics.block import Block3D
from engine.core.math_utils import IsoMath, TILE_WIDTH, TILE_HEIGHT

class Chunk(Node):
    def __init__(self, cx, cy, size=16):
        super().__init__(f"Chunk_{cx}_{cy}")
        self.cx = cx
        self.cy = cy
        self.size = size
        self.tiles = {} # (lx, ly): Block3D
        self.dirty = True
        self.baked_surf = None
        # 청크의 월드 기준 시작 좌표
        self.world_x = cx * size
        self.world_y = cy * size

    def add_tile(self, lx, ly, tile_node):
        self.tiles[(lx, ly)] = tile_node
        self.add_child(tile_node)
        self.dirty = True

    def bake(self):
        """정적 바닥 타일들을 하나의 서피스로 병합하여 렌더링 부하 절감"""
        if not self.dirty and self.baked_surf: return
        
        # 청크의 대략적인 아이소메트릭 범위 계산
        # 16x16 청크는 화면상에서 꽤 넓으므로 충분한 크기의 서피스 생성
        surf_w = self.size * TILE_WIDTH
        surf_h = self.size * TILE_HEIGHT + 64
        self.baked_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        
        # 이 청크의 기준점 (가장 왼쪽 위 타일의 화면 좌표)
        # 모든 타일을 이 상대 좌표로 그립니다.
        
        # 타일들을 정렬해서 그리기 (Baking 시에도 순서 중요)
        sorted_keys = sorted(self.tiles.keys(), key=lambda k: k[0] + k[1])
        
        for lx, ly in sorted_keys:
            tile = self.tiles[(lx, ly)]
            # 청크 내 상대 좌표 -> 화면 좌표 변환
            # (lx, ly)는 0~15 범위
            # 기준점 보정: lx, ly가 0,0 일 때 서피스의 중앙 위쪽 쯤에 오도록
            rx, ry = IsoMath.cart_to_iso(lx, ly, tile.position.z)
            
            # Surface 내에서 타일이 잘리지 않도록 오프셋 (중앙 기준)
            # lx-ly 가 음수일 수 있으므로 (size*half_width) 만큼 더함
            draw_x = rx + (self.size * TILE_WIDTH // 2)
            draw_y = ry + 32 # 상단 여유
            
            sprite = tile.get_sprite()
            if sprite:
                # 타일의 midbottom을 (draw_x, draw_y)에 맞춤
                rect = sprite.get_rect(midbottom=(draw_x, draw_y + 16))
                self.baked_surf.blit(sprite, rect)
        
        self.dirty = False

    def _draw(self, renderer):
        # 청크는 직접 그려지지 않고 렌더러가 관리하거나,
        # 구역 렌더링 최적화에 사용됩니다.
        pass

class TileMap(Node):
    def __init__(self, chunk_size=16):
        super().__init__("TileMap")
        self.chunk_size = chunk_size
        self.chunks = {} # (cx, cy): Chunk

    def set_tile(self, x, y, tile_node):
        cx, cy = x // self.chunk_size, y // self.chunk_size
        lx, ly = x % self.chunk_size, y % self.chunk_size
        
        if (cx, cy) not in self.chunks:
            chunk = Chunk(cx, cy, self.chunk_size)
            self.chunks[(cx, cy)] = chunk
            self.add_child(chunk)
            
        tile_node.position.x = x
        tile_node.position.y = y
        self.chunks[(cx, cy)].add_tile(lx, ly, tile_node)

    def get_visible_chunks(self, camera):
        # 카메라 위치를 기반으로 현재 화면에 보이는 청크 좌표들 반환
        # (간단하게 구현: 카메라 중심 기준 주변 3x3)
        # TODO: 정확한 아이소메트릭 컬링 로직
        pass
