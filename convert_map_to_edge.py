import json
import os

def convert_to_edge_based():
    """
    기존의 셀 기반 맵 데이터를 '경계 기반(Edge-Based)' 데이터로 변환합니다.
    벽이 어느 타일의 어느 '경계'에 있는지를 추론하여 새로운 맵 포맷을 생성합니다.
    """
    input_map_path = "engine/assets/pxanic_converted.json" # 이전 변환 결과물 사용
    output_map_path = "engine/assets/pxanic_edge_map.json"

    print(f"Loading cell-based map from {input_map_path}...")
    with open(input_map_path, 'r', encoding='utf-8') as f:
        map_data = json.load(f)

    width = map_data["width"]
    height = map_data["height"]
    blocks = map_data["blocks"]

    # 벽 블록의 위치를 빠르게 찾기 위한 세트
    wall_positions = set()
    for block in blocks:
        if str(block.get("tile_id", ""))[0] == '2': # Category '2' is Wall
            pos = tuple(block["pos"])
            wall_positions.add((int(pos[0]), int(pos[1])))

    new_walls_data = {}
    floor_and_objects = []

    # 바닥과 사물만 먼저 분류
    for block in blocks:
        if str(block.get("tile_id", ""))[0] != '2':
            floor_and_objects.append(block)

    # 모든 타일 좌표를 순회하며 벽 경계를 추론
    for y in range(height):
        for x in range(width):
            # 현재 좌표가 벽이 아니어야 함 (바닥, 사물 등)
            if (x, y) not in wall_positions:
                edges = []
                # Case 1: 내 북동쪽(x+1, y)에 벽이 있는가? -> 나의 'NE' 경계에 벽이 있다.
                if (x + 1, y) in wall_positions:
                    edges.append("NE")
                # Case 2: 내 북서쪽(x, y+1)에 벽이 있는가? -> 나의 'NW' 경계에 벽이 있다.
                if (x, y + 1) in wall_positions:
                    edges.append("NW")
                
                if edges:
                    new_walls_data[f"({x},{y})"] = edges

    # 최종 결과물 조합
    final_map = {
        "width": width,
        "height": height,
        "blocks": floor_and_objects, # 벽이 제거된 블록 리스트
        "walls": new_walls_data      # 새로 생성된 경계 기반 벽 데이터
    }

    print(f"Saving edge-based map to {output_map_path}...")
    with open(output_map_path, 'w', encoding='utf-8') as f:
        json.dump(final_map, f, indent=4)
    print("Edge-based map conversion complete!")

if __name__ == "__main__":
    convert_to_edge_based()
