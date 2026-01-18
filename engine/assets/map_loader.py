import json
import os
from engine.graphics.block import Block3D

class MapLoader:
    @staticmethod
    def load_scene(path, scene_root):
        """Loads a JSON map file into the scene"""
        if not os.path.exists(path):
            print(f"[Error] Map file not found: {path}")
            return

        with open(path, 'r') as f:
            data = json.load(f)

        width = data.get('width', 10)
        height = data.get('height', 10)
        layers = data.get('layers', {})

        print(f"[Loader] Loading Map: {width}x{height}")

        # PxANIC map format: layers -> floor -> 2D array of [id, rot]
        # We need to convert ID to Block3D properties
        
        # Floor Layer
        if 'floor' in layers:
            for y, row in enumerate(layers['floor']):
                for x, cell in enumerate(row):
                    tid = cell[0] if isinstance(cell, list) else cell
                    if tid != 0:
                        # Map ID to Color/Size (Placeholder logic)
                        color = (100, 100, 100)
                        if tid == 1110001: color = (60, 120, 60) # Grass
                        elif tid == 1110000: color = (100, 80, 50) # Dirt
                        
                        tile = Block3D(name=f"Floor_{x}_{y}", size_z=0.1, color=color)
                        tile.position.x = x
                        tile.position.y = y
                        scene_root.add_child(tile)

        # Wall/Object Layer
        if 'wall' in layers:
            for y, row in enumerate(layers['wall']):
                for x, cell in enumerate(row):
                    tid = cell[0] if isinstance(cell, list) else cell
                    if tid != 0:
                        wall = Block3D(name=f"Wall_{x}_{y}", size_z=1.5, color=(120, 120, 130))
                        wall.position.x = x
                        wall.position.y = y
                        scene_root.add_child(wall)
                        
                        # Add to physics? Scene needs reference to CollisionWorld
                        # This part needs decoupling in full engine.
