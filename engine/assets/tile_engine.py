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

    # --- Full TILE_DATA (Auto-Generated from Mapping) ---
    TILE_DATA = {
        111001000: {'name': 'Dirt Floor (흙 바닥)', 'color': (80, 65, 45)},
        111001001: {'name': 'Grass Floor (풀 바닥)', 'color': (40, 70, 50)},
        111001002: {'name': 'Gravel Floor (자갈 바닥)', 'color': (70, 75, 85)},
        111001003: {'name': 'Sand Floor (모래 바닥)', 'color': (170, 160, 110)},
        111001004: {'name': 'Shallow Water (얕은 물)', 'color': (40, 60, 100)},
        111001005: {'name': 'Cave Floor (동굴 바닥)', 'color': (50, 50, 60)},
        111001006: {'name': 'Mossy Stone (이끼 낀 돌)', 'color': (70, 75, 85)},
        111001011: {'name': 'Asphalt Road (아스팔트)', 'color': (25, 25, 30)},
        111001012: {'name': 'Road Line (차선)', 'color': (200, 200, 205)},
        111001013: {'name': 'Broken Concrete (깨진 바닥)', 'color': (110, 110, 115)},
        111001015: {'name': 'Ice (얼음)', 'color': (180, 210, 230)},
        111101000: {'name': 'Empty Field (빈 밭)', 'color': (80, 65, 45)},
        111101002: {'name': 'Grown Field (수확)', 'color': (150, 80, 30)},
        111101003: {'name': 'Fishing Spot (낚시터)', 'color': (40, 60, 100)},
        112001016: {'name': 'Deep Water (깊은 물)', 'color': (20, 30, 60)},
        112001018: {'name': 'Cliff (절벽)', 'color': (50, 35, 20)},
        112001117: {'name': 'Lava (용암)', 'color': (150, 50, 50)},
        121001000: {'name': 'Checkered Tile (체크무늬)', 'color': (200, 200, 205)},
        121001001: {'name': 'Red Carpet (레드 카펫)', 'color': (150, 50, 50)},
        121001002: {'name': 'Blue Carpet (블루 카펫)', 'color': (50, 70, 130)},
        121001003: {'name': 'Lab Tile (실험실 바닥)', 'color': (200, 200, 205)},
        121001007: {'name': 'Wood Floor L (밝은 나무)', 'color': (120, 80, 50)},
        121001008: {'name': 'Wood Floor D (어두운 나무)', 'color': (90, 50, 30)},
        121001009: {'name': 'Marble Floor (대리석)', 'color': (200, 200, 210)},
        121001010: {'name': 'Concrete Floor (콘크리트)', 'color': (110, 110, 115)},
        121001014: {'name': 'Iron Grate (철창 바닥)', 'color': (90, 90, 95)},
        212000000: {'name': 'Red Brick Wall (붉은 벽돌)', 'color': (120, 50, 40)},
        212000001: {'name': 'Grey Brick Wall (회색 벽돌)', 'color': (70, 75, 85)},
        212000002: {'name': 'Mossy Wall (이끼 벽)', 'color': (70, 75, 85)},
        212000009: {'name': 'Rusty Wall (녹슨 벽)', 'color': (150, 80, 30)},
        212000013: {'name': 'Cave Wall (동굴 벽)', 'color': (50, 50, 60)},
        212001000: {'name': 'Wood Fence (나무 울타리)', 'color': (120, 80, 50)},
        212001001: {'name': 'Iron Fence (철 울타리)', 'color': (90, 90, 95)},
        222000003: {'name': 'Wood Wall (나무 벽)', 'color': (90, 50, 30)},
        222000004: {'name': 'Log Wall (통나무 벽)', 'color': (50, 35, 20)},
        222000005: {'name': 'White Wall (흰 벽)', 'color': (200, 200, 205)},
        222000006: {'name': 'Wallpaper (벽지)', 'color': (150, 50, 50)},
        222000007: {'name': 'Toilet Tile Wall (타일 벽)', 'color': (50, 70, 130)},
        222000008: {'name': 'Lab Metal Wall (금속 벽)', 'color': (140, 140, 150)},
        222000012: {'name': 'Bookshelf Wall (책장 벽)', 'color': (90, 60, 40)},
        222001002: {'name': 'Prison Bars (창살)', 'color': (50, 50, 60)},
        222001010: {'name': 'Glass Wall (유리 벽)', 'color': (200, 220, 255)},
        222001011: {'name': 'Reinforced Glass (강화 유리)', 'color': (150, 180, 200)},
        311001000: {'name': 'Red Flower (빨간 꽃)', 'color': (150, 50, 50)},
        311001001: {'name': 'Yellow Flower (노란 꽃)', 'color': (170, 150, 40)},
        311001002: {'name': 'Weed (잡초)', 'color': (50, 90, 50)},
        311001003: {'name': 'Lotus (연잎)', 'color': (40, 70, 50)},
        311001008: {'name': 'Cactus (선인장)', 'color': (50, 90, 50)},
        311011004: {'name': 'Tall Bush (덤불)', 'color': (40, 70, 50)},
        311011005: {'name': 'Corn Field (옥수수)', 'color': (170, 150, 40)},
        312000004: {'name': 'Rock (바위)', 'color': (70, 75, 85)},
        312000006: {'name': 'Tree Trunk (나무)', 'color': (50, 35, 20)},
        312000007: {'name': 'Dead Tree (죽은 나무)', 'color': (50, 35, 20)},
        312001005: {'name': 'Fountain (분수)', 'color': (70, 75, 85)},
        312001006: {'name': 'Well (우물)', 'color': (70, 75, 85)},
        312001011: {'name': 'CCTV Camera (CCTV)', 'color': (140, 140, 150)},
        312001110: {'name': 'Street Light (가로등)', 'color': (90, 90, 95)},
        312100004: {'name': 'Iron Ore (철광석)', 'color': (50, 50, 60)},
        312100005: {'name': 'Rubble (잔해)', 'color': (70, 75, 85)},
        321001005: {'name': 'Broken Door', 'color': (50, 35, 20)},
        321001008: {'name': 'Exit Mark (출구)', 'color': (170, 150, 40)},
        321001116: {'name': 'Lamp (램프)', 'color': (170, 150, 40)},
        321101000: {'name': 'Wood Door Open', 'color': (120, 80, 50)},
        321101001: {'name': 'Iron Door Open', 'color': (90, 90, 95)},
        321101002: {'name': 'Glass Door Open', 'color': (200, 220, 255)},
        321101003: {'name': 'Prison Door Open', 'color': (50, 50, 60)},
        321101004: {'name': 'Lab Door Open', 'color': (200, 200, 205)},
        321101107: {'name': 'Portal (포털)', 'color': (150, 50, 50)},
        322000003: {'name': 'Bookshelf (책장)', 'color': (90, 60, 40)},
        322000005: {'name': 'Refrigerator (냉장고)', 'color': (200, 200, 205)},
        322000117: {'name': 'Fireplace (벽난로)', 'color': (120, 50, 40)},
        322001000: {'name': 'Dining Table (식탁)', 'color': (90, 50, 30)},
        322001004: {'name': 'TV (텔레비전)', 'color': (25, 25, 30)},
        322001007: {'name': 'Piano (피아노)', 'color': (25, 25, 30)},
        322001010: {'name': 'Desk (책상)', 'color': (90, 50, 30)},
        322001012: {'name': 'Trash Can (쓰레기통)', 'color': (90, 90, 95)},
        322001013: {'name': 'Vent (환풍구)', 'color': (90, 90, 95)},
        322001015: {'name': 'Toilet (변기)', 'color': (200, 200, 205)},
        322001018: {'name': 'Exit Sign (비상구)', 'color': (50, 90, 50)},
        322100006: {'name': 'Vending Machine (자판기)', 'color': (150, 50, 50)},
        322100010: {'name': 'Lab Door Closed', 'color': (200, 200, 205)},
        322101001: {'name': 'Wood Chair (의자)', 'color': (120, 80, 50)},
        322101002: {'name': 'Sofa (소파)', 'color': (150, 50, 50)},
        322101008: {'name': 'Microscope (현미경)', 'color': (200, 200, 205)},
        322101009: {'name': 'Surgery Table (수술대)', 'color': (140, 140, 150)},
        322101010: {'name': 'Broken Panel (고장난 패널)', 'color': (90, 90, 95)},
        322101011: {'name': 'Bed (침대)', 'color': (50, 70, 130)},
        322101011: {'name': 'Computer (컴퓨터)', 'color': (90, 90, 95)},
        322120008: {'name': 'Box (상자)', 'color': (120, 80, 50)},
        322120009: {'name': 'Closet (옷장)', 'color': (90, 50, 30)},
        322120014: {'name': 'Drum Barrel (드럼통)', 'color': (150, 50, 50)},
    }

    @staticmethod
    def get_collision(tid):
        sid = str(tid)
        if len(sid) >= 9:
            return sid[2] == '2'
        return ((tid // 10000) % 10) == 2

    @staticmethod
    def get_interaction(tid):
        sid = str(tid)
        if len(sid) >= 9:
            types = {'0': "NONE", '1': "USE", '2': "JOB"}
            return types.get(sid[3], "NONE")
        types = {0: "NONE", 1: "USE", 2: "ITEM", 3: "DOOR"}
        val = (tid // 1000) % 10
        return types.get(val, "NONE")

    @staticmethod
    def get_hiding(tid):
        """Returns hiding type from digit 3"""
        sid = str(tid)
        if len(sid) >= 9:
            return int(sid[4])
        return (tid // 100) % 10

    @staticmethod
    def create_texture(tid):
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        color = TileEngine.TILE_DATA.get(tid, {}).get('color', (150, 150, 150))
        sid = str(tid)
        
        # 기본 배경색 채우기
        s.fill(color)
        
        # 1. 공통적으로 적용되는 거친 노이즈/먼지 효과 (좀보이드의 황폐한 느낌)
        for _ in range(400): # 노이즈 밀도 증가
            x, y = random.randint(0, 31), random.randint(0, 31)
            var = random.randint(-30, 30) # 더 넓은 범위의 변동성
            c = (max(0, min(255, color[0]+var)), max(0, min(255, color[1]+var)), max(0, min(255, color[2]+var)))
            s.set_at((x, y), c)

        # 2. 타일 카테고리/ID별 상세 패턴
        # 바닥 (Category '1') - 미세한 그리드, 얼룩, 균열
        if sid.startswith('1'):
            # 미세한 그리드 라인 (매우 어둡고 투명하게)
            for i in range(0, 32, 8):
                pygame.draw.line(s, (0, 0, 0, 20), (i, 0), (i, 31), 1)
                pygame.draw.line(s, (0, 0, 0, 20), (0, i), (31, i), 1)
            # 더 많은 얼룩과 균열
            for _ in range(15):
                lx, ly = random.randint(0, 31), random.randint(0, 31)
                lw, lh = random.randint(5, 15), random.randint(5, 15)
                temp_s = pygame.Surface((lw, lh), pygame.SRCALPHA)
                pygame.draw.ellipse(temp_s, (0, 0, 0, random.randint(30, 80)), (0, 0, lw, lh))
                s.blit(temp_s, (lx, ly))
            # 아스팔트/도로의 균열
            if "Asphalt" in sid or tid == 111001011:
                for _ in range(5):
                    p1 = (random.randint(0, 31), random.randint(0, 31))
                    p2 = (p1[0] + random.randint(-7, 7), p1[1] + random.randint(-7, 7))
                    pygame.draw.line(s, (0, 0, 0, 150), p1, p2, 1)
            # 풀밭
            elif "Grass" in sid or tid == 111001001:
                for _ in range(25):
                    gx, gy = random.randint(2, 28), random.randint(2, 28)
                    pygame.draw.line(s, (20, 50, 20, 200), (gx, gy), (gx + random.randint(-1, 1), gy - random.randint(2, 4)), 1)

        # 벽 (Category '2') - 세로 줄무늬, 거친 질감
        elif sid.startswith('2'):
            base_color = color
            dark_color = tuple(max(0, c - 40) for c in base_color)
            
            # 벽돌 벽 (Red Brick, Grey Brick...)
            if "Brick" in sid:
                s.fill(dark_color)
                for y in range(0, 32, 8):
                    offset = 16 if (y // 8) % 2 else 0
                    for x in range(0, 32, 16):
                        pygame.draw.rect(s, base_color, (x - offset, y, 15, 7))
                        pygame.draw.rect(s, base_color, (x - offset + 16, y, 15, 7))
            
            # 나무 벽 (Wood Wall, Log Wall...)
            elif "Wood" in sid or "Log" in sid:
                for x in range(0, 32, 8):
                    plank_color = tuple(max(0,min(255, c + random.randint(-10,10))) for c in base_color)
                    pygame.draw.line(s, plank_color, (x, 0), (x, 31), 8)
                    pygame.draw.line(s, dark_color, (x+7, 0), (x+7, 31), 1)
            
            # 일반 벽지 (Wallpaper, White Wall...)
            else:
                 for x in range(0, 32, 16):
                    pygame.draw.line(s, dark_color, (x, 0), (x, 31), 1)
        
        # 나무 계열 (벽, 사물 등) - 나뭇결
        if "Wood" in sid:
            for x in range(0, 32, 8):
                pygame.draw.line(s, (0, 0, 0, 40), (x, 0), (x, 31), 1)
                for _ in range(3):
                    v = random.randint(0, 31)
                    pygame.draw.line(s, (0, 0, 0, 30), (x + random.randint(1, 3), v), (x + random.randint(1, 3), v + random.randint(5, 15)), 1)
        
        return s
