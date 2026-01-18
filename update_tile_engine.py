import os
import re

def update_tile_engine():
    mapping_path = "PxANIC!/타일_ID_매핑_정리.txt"
    engine_path = "engine/assets/tile_engine.py"
    
    new_tile_data = {}
    with open(mapping_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split('\t')
            if len(parts) >= 3 and parts[1].strip().isdigit():
                new_id = int(parts[1].strip())
                name = parts[2].strip()
                color = (100, 100, 110)
                if "Dirt" in name: color = (80, 65, 45)
                elif "Grass" in name: color = (40, 70, 50)
                elif "Wood" in name: color = (90, 50, 30)
                elif "Brick" in name: color = (120, 50, 40)
                elif "Water" in name: color = (40, 60, 100)
                elif "Marble" in name: color = (200, 200, 210)
                elif "White" in name: color = (200, 200, 205)
                elif "Black" in name or "Asphalt" in name: color = (25, 25, 30)
                elif "Metal" in name: color = (140, 140, 150)
                elif "Flower" in name and "Red" in name: color = (150, 50, 50)
                elif "Flower" in name and "Yellow" in name: color = (170, 150, 40)
                new_tile_data[new_id] = {'name': name, 'color': color}

    with open(engine_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # TILE_DATA 교체
    lines = ["TILE_DATA = {"]
    for tid in sorted(new_tile_data.keys()):
        d = new_tile_data[tid]
        lines.append(f"        {tid}: {{'name': '{d['name']}', 'color': {d['color']}}},\n")
    lines.append("    }")
    new_data_str = "\n".join(lines)
    content = re.sub(r"TILE_DATA = \{{.*?\}}", new_data_str, content, flags=re.DOTALL)

    # 메서드 교체 (9자리 ID 대응)
    collision_method = """    @staticmethod
    def get_collision(tid):
        sid = str(tid)
        if len(sid) >= 9: return sid[2] == '2'
        return ((tid // 10000) % 10) == 2"""
    
    interaction_method = """    @staticmethod
    def get_interaction(tid):
        sid = str(tid)
        if len(sid) >= 9:
            types = {'0': "NONE", '1': "USE", '2': "JOB"}
            return types.get(sid[3], "NONE")
        types = {0: "NONE", 1: "USE", 2: "ITEM", 3: "DOOR"}
        val = (tid // 1000) % 10
        return types.get(val, "NONE")"""

    content = re.sub(r"    @staticmethod\s+def get_collision.*?return \(\(\s*tid // 10000\s*\)% 10\s*\)\s*==\s*2", collision_method, content, flags=re.DOTALL)
    content = re.sub(r"    @staticmethod\s+def get_interaction.*?return types\.get\(val, \"NONE\"
", interaction_method, content, flags=re.DOTALL)

    with open(engine_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Update Complete: {len(new_tile_data)} tiles.")

if __name__ == "__main__":
    update_tile_engine()
