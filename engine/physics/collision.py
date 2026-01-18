from pygame.math import Vector3
import math

class CollisionWorld:
    def __init__(self):
        # Spatial Hash Map: Key=(grid_x, grid_y), Value=[Nodes]
        self.grid = {}
        self.cell_size = 1.0 # 1 Grid Unit

    def add_static(self, node):
        """Register a static object to the spatial grid"""
        gx, gy = int(node.position.x), int(node.position.y)
        
        # Object might span multiple cells, but for now assume 1x1 base
        if (gx, gy) not in self.grid:
            self.grid[(gx, gy)] = []
        self.grid[(gx, gy)].append(node)

    def remove_static(self, node):
        gx, gy = int(node.position.x), int(node.position.y)
        if (gx, gy) in self.grid:
            if node in self.grid[(gx, gy)]:
                self.grid[(gx, gy)].remove(node)

    def get_nearby_objects(self, pos):
        """Returns objects in the 3x3 grid around pos"""
        objects = []
        cx, cy = int(pos.x), int(pos.y)
        
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                key = (cx + dx, cy + dy)
                if key in self.grid:
                    objects.extend(self.grid[key])
        return objects

    def check_collision(self, pos, size=0.4):
        """
        Optimized collision check using Spatial Hashing.
        """
        nearby = self.get_nearby_objects(pos)
        
        for body in nearby:
            # AABB Check
            dist_x = abs(pos.x - body.position.x)
            dist_y = abs(pos.y - body.position.y)
            
            # Collision box size (0.5 is half block)
            # Check overlap
            if dist_x < (size + 0.4) and dist_y < (size + 0.4):
                # Z-Check (Height)
                # Assume standard wall height is ~2.0, floor is 0.1
                # If body has 'size_z', use it. Else default to 1.
                body_h = getattr(body, 'size_z', 1.0)
                
                # If player feet (pos.z) are below body top
                if pos.z < body.position.z + body_h:
                    # And player head (pos.z + height) is above body bottom
                    if pos.z + 1.8 > body.position.z: 
                        return True
        return False

    def raycast(self, start, end, step=0.1):
        """
        Casts a ray and returns the first hit object or None.
        start, end: Vector3
        """
        # Optimized traversal could be Bresenham, but stepping is easier for 3D logic
        dist = start.distance_to(end)
        direction = (end - start).normalize()
        current = Vector3(start)
        travelled = 0
        
        while travelled < dist:
            if self.check_collision(current, size=0.1):
                return current # Hit point
            
            current += direction * step
            travelled += step
            
        return None