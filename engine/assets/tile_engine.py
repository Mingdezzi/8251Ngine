import pygame
import random
import math

class TileEngine:
    # --- PxANIC- Color Constants ---
    P = {
        'BLACK': (25, 25, 30), 'WHITE': (200, 200, 205),
        'GREY_L': (150, 150, 160), 'GREY_M': (100, 100, 110), 'GREY_D': (50, 50, 60),
        'RED': (150, 50, 50), 'GREEN': (50, 90, 50), 'BLUE': (50, 70, 130),
        'YELLOW': (170, 150, 40), 'ORANGE': (150, 80, 30),
        'BROWN_L': (130, 100, 60), 'BROWN_M': (90, 60, 40), 'BROWN_D': (50, 35, 20),
        'WOOD_BASE': (90, 50, 30), 'STONE_BASE': (70, 75, 85), 'CONCRETE': (110, 110, 115),
        'GRASS_BASE': (40, 70, 50), 'DIRT_BASE': (80, 65, 45), 'WATER_BASE': (40, 60, 100)
    }

    # --- Full TILE_DATA (Mapping ID to color and properties) ---
    TILE_DATA = {
        1110000: {'name': 'Dirt Floor', 'color': (80, 65, 45)},
        1110001: {'name': 'Grass Floor', 'color': (40, 70, 50)},
        1110002: {'name': 'Gravel Floor', 'color': (100, 100, 110)},
        1110003: {'name': 'Sand Floor', 'color': (170, 160, 110)},
        1110004: {'name': 'Water Floor', 'color': (40, 60, 100)},
        1110009: {'name': 'Marble Floor', 'color': (200, 200, 210)},
        1110010: {'name': 'Concrete', 'color': (110, 110, 115)},
        1110011: {'name': 'Asphalt Road', 'color': (25, 25, 30)},
        2110000: {'name': 'Checkered Tile', 'color': (200, 200, 205)},
        2110001: {'name': 'Red Carpet', 'color': (150, 50, 50)},
        3220000: {'name': 'Red Brick Wall', 'color': (120, 50, 40)},
        3220001: {'name': 'Grey Brick Wall', 'color': (70, 75, 85)},
        3220003: {'name': 'Wood Wall', 'color': (90, 50, 30)},
        3220005: {'name': 'White Wall', 'color': (200, 200, 205)},
        3220010: {'name': 'Glass Wall', 'color': (200, 220, 255)},
        3220012: {'name': 'Bookshelf Wall', 'color': (90, 60, 40)},
        5321206: {'name': 'Wood Door', 'color': (90, 50, 30)},
        5321025: {'name': 'Chest', 'color': (120, 80, 50)},
        6310000: {'name': 'Red Flower', 'color': (150, 50, 50)},
        6310001: {'name': 'Yellow Flower', 'color': (170, 150, 40)},
        6310106: {'name': 'Tree Trunk', 'color': (50, 35, 20)},
        7310010: {'name': 'Street Light', 'color': (90, 90, 95)},
        8320004: {'name': 'TV', 'color': (25, 25, 30)},
        8320205: {'name': 'Refrigerator', 'color': (200, 200, 205)},
        8321006: {'name': 'Vending Machine', 'color': (150, 50, 50)},
        9312000: {'name': 'Farm Field', 'color': (80, 65, 45)},
        9312003: {'name': 'Fishing Spot', 'color': (40, 60, 100)}
    }

    @staticmethod
    def get_collision(tid):
        """Returns True if the tile ID represents a solid object (digit 5 is 2)"""
        return ((tid // 10000) % 10) == 2

    @staticmethod
    def get_interaction(tid):
        """Returns interaction type from digit 4"""
        types = {0: "NONE", 1: "USE", 2: "ITEM", 3: "DOOR"}
        val = (tid // 1000) % 10
        return types.get(val, "NONE")

    @staticmethod
    def get_hiding(tid):
        """Returns hiding type from digit 3"""
        return (tid // 100) % 10

    @staticmethod
    def create_texture(tid):
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        color = TileEngine.TILE_DATA.get(tid, {}).get('color', (150, 150, 150))
        
        # 1. Base Procedural Noise (PxANIC- Core Visual)
        s.fill(color)
        for _ in range(120):
            x, y = random.randint(0, 31), random.randint(0, 31)
            var = random.randint(-15, 15)
            c = (max(0, min(255, color[0]+var)), max(0, min(255, color[1]+var)), max(0, min(255, color[2]+var)))
            s.set_at((x, y), c)

        # 2. Detailed Patterns
        if tid == 1110001: # Grass
            for _ in range(12):
                cx, cy = random.randint(2, 28), random.randint(2, 28)
                pygame.draw.line(s, (70, 110, 70), (cx, cy), (cx, cy+3))
        elif tid == 3220000: # Brick
            for y in range(0, 32, 8):
                pygame.draw.line(s, (50, 50, 50), (0, y), (31, y))
        elif tid == 2110000: # Checkered
            for y in range(0, 32, 16):
                for x in range(0, 32, 16):
                    if (x+y)%32 == 0: pygame.draw.rect(s, (255, 255, 255), (x, y, 16, 16))
        elif tid == 3220012: # Bookshelf
            for x in range(0, 32, 8): pygame.draw.line(s, (25, 25, 30), (x, 0), (x, 31))
        elif tid // 1000000 == 5: # Doors
            pygame.draw.rect(s, (200, 200, 200), (4, 4, 24, 24), 1)
            pygame.draw.circle(s, (255, 255, 0), (22, 16), 2)
            
        return s