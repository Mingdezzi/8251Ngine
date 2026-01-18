import json
import os
from engine.graphics.block import Block3D

class MapLoader:
    @staticmethod
    def load_map(path, scene, collision_world):
        if not os.path.exists(path):
            print(f"MapLoader: File not found {path}")
            return None # Return None to indicate failure or no metadata

        with open(path, 'r') as f:
            data = json.load(f)

        # 1. Load Metadata (New)
        metadata = {
            "width": data.get("width", 20),
            "height": data.get("height", 20)
        }

        # 2. Load Blocks
        for b_data in data.get("blocks", []):
            block = Block3D(
                name=b_data.get("name", "Wall"),
                size_z=b_data.get("size_z", 1.0),
                color=tuple(b_data.get("color", (100, 100, 110))),
                zone_id=b_data.get("zone_id", 0),
                interact_type=b_data.get("interact_type", "NONE"),
                tile_id=b_data.get("tile_id", None)
            )
            block.position.x = b_data["pos"][0]
            block.position.y = b_data["pos"][1]
            block.position.z = b_data["pos"][2]
            scene.add_child(block)
            if collision_world and b_data.get("is_static", True):
                collision_world.add_static(block)

        print(f"MapLoader: Successfully loaded {path}")
        return metadata

    @staticmethod
    def save_map(path, scene, width=20, height=20):
        # Implementation for Game Editor to save changes
        data = {
            "width": width,
            "height": height,
            "blocks": []
        }
        for child in scene.children:
            if isinstance(child, Block3D):
                data["blocks"].append({
                    "name": child.name,
                    "pos": [child.position.x, child.position.y, child.position.z],
                    "size_z": child.size_z,
                    "color": list(child.color),
                    "zone_id": child.zone_id,
                    "interact_type": child.interact_type,
                    "tile_id": child.tile_id
                })
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
