import json
import os
import re

# 1. 타일 ID 매핑 데이터 파싱
def load_id_mapping(path):
    mapping = {}
    if not os.path.exists(path):
        return mapping
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                mapping[int(parts[0])] = int(parts[1])
    return mapping

# 2. 색상 데이터 추출 (PxANIC!/world/tiles.py 기반)
# 주요 색상만 수동 매핑 (복잡한 파싱 대신 정확성 기함)
COLOR_MAP = {
    'DIRT_BASE': (80, 65, 45), 'GRASS_BASE': (40, 70, 50), 'STONE_BASE': (70, 75, 85),
    'SAND_BASE': (170, 160, 110), 'WATER_BASE': (40, 60, 100), 'WOOD_LIGHT': (120, 80, 50),
    'BRICK_RED': (120, 50, 40), 'METAL_BASE': (90, 90, 95), 'WHITE': (200, 200, 205),
    'BLACK': (25, 25, 30), 'GREY_M': (100, 100, 110), 'RED': (150, 50, 50),
    'BLUE': (50, 70, 130), 'YELLOW': (170, 150, 40), 'ORANGE': (150, 80, 30)
}

# 기본 타일별 색상 추론 로직
def get_color_for_id(new_id):
    sid = str(new_id)
    A = sid[0]
    if A == '1': # 바닥
        if '111' in sid: return COLOR_MAP['DIRT_BASE']
        if '121' in sid: return COLOR_MAP['WOOD_LIGHT']
        return COLOR_MAP['GRASS_BASE']
    elif A == '2': # 벽
        if '212' in sid: return COLOR_MAP['BRICK_RED']
        return COLOR_MAP['GREY_M']
    elif A == '3': # 사물
        if '322' in sid: return COLOR_MAP['WOOD_LIGHT']
        return COLOR_MAP['METAL_BASE']
    return COLOR_MAP['GREY_M']

def convert():
    old_map_path = "PxANIC!/map.json"
    mapping_path = "PxANIC!/타일_ID_매핑_정리.txt"
    output_path = "engine/assets/pxanic_converted.json"
    
    print(f"Loading mapping from {mapping_path}...")
    id_map = load_id_mapping(mapping_path)
    
    print(f"Loading old map from {old_map_path}...")
    with open(old_map_path, 'r', encoding='utf-8') as f:
        old_map = json.load(f)
    
    width = old_map.get("width", 100)
    height = old_map.get("height", 100)
    layers = old_map.get("layers", {})
    
    new_blocks = []
    
    # 레이어 순차 처리: Z-Fighting 방지를 위해 낮은 Z부터 처리
    # size_z 값 조정: 바닥은 얇게, 벽은 시각적으로 높게, 사물은 적당히
    layer_settings = {
        "floor": {"z_offset": 0.0, "default_size_z": 0.05},
        "wall": {"z_offset": 0.0, "default_size_z": 1.8}, # 벽은 높게 (Block3D에서 얇게 렌더링)
        "object": {"z_offset": 0.01, "default_size_z": 0.6} # 사물은 바닥 위로 살짝 띄움
    }
    
    for layer_name in ["floor", "wall", "object"]:
        settings = layer_settings[layer_name]
        z_offset = settings["z_offset"]
        default_size_z = settings["default_size_z"]

        if layer_name not in layers: continue
        grid = layers[layer_name]
        
        for gy in range(len(grid)):
            for gx in range(len(grid[gy])):
                tile_data = grid[gy][gx]
                if isinstance(tile_data, list):
                    tid, rot = tile_data[0], tile_data[1]
                else:
                    tid, rot = tile_data, 0
                
                if tid == 0: continue
                
                new_id = id_map.get(tid, tid)
                sid = str(new_id)
                
                A = sid[0] if len(sid) >= 1 else '0'
                C = sid[2] if len(sid) >= 3 else '1' # 충돌 (3번째 자리)
                D = sid[3] if len(sid) >= 4 else '0' # 상호작용 (4번째 자리)
                
                block = {
                    "name": f"Tile_{new_id}",
                    "pos": [gx, gy, z_offset],
                    "size_z": default_size_z, # 컨버터에서 시각적 높이로 설정
                    "color": get_color_for_id(new_id),
                    "is_static": (C == '2'),
                    "tile_id": new_id,
                    "interact_type": "JOB" if D == '2' else ("INTERACT" if D == '1' else "NONE")
                }
                
                new_blocks.append(block)
                
    result = {
        "width": width,
        "height": height,
        "blocks": new_blocks
    }
    
    print(f"Saving converted map to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)
    print("Conversion Complete!")

if __name__ == "__main__":
    convert()