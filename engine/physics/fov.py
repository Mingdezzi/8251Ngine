import math
import pygame

class FOVSystem:
    def __init__(self, collision_world):
        self.world = collision_world
        self.ray_count = 120 # 레이 개수 (높을수록 정교하지만 느림)
        self.view_radius = 8.0 # 그리드 단위

    def calculate_fov(self, origin_pos, facing_dir=None, fov_angle=360):
        """
        origin_pos: Vector3 (x, y, z)
        facing_dir: (dx, dy) normalized (Optional)
        Return: List of points (Grid Coords) forming the visible polygon
        """
        points = []
        points.append((origin_pos.x, origin_pos.y)) # Center
        
        start_angle = 0
        end_angle = 360
        
        if facing_dir:
            base_angle = math.degrees(math.atan2(facing_dir[1], facing_dir[0]))
            start_angle = base_angle - fov_angle / 2
            end_angle = base_angle + fov_angle / 2

        step = (end_angle - start_angle) / self.ray_count
        
        for i in range(self.ray_count + 1):
            angle_deg = start_angle + step * i
            angle_rad = math.radians(angle_deg)
            
            dx = math.cos(angle_rad)
            dy = math.sin(angle_rad)
            
            hit_pos = self._cast_ray(origin_pos.x, origin_pos.y, dx, dy, self.view_radius)
            points.append(hit_pos)
            
        return points

    def _cast_ray(self, ox, oy, dx, dy, max_dist):
        """DDA or Step-based Raycast"""
        x, y = ox, oy
        step_size = 0.5 # Precision
        dist = 0
        
        while dist < max_dist:
            x += dx * step_size
            y += dy * step_size
            dist += step_size
            
            # Check collision with walls
            # CollisionWorld is optimized for AABB, simple check here:
            if self.world.check_collision(pygame.math.Vector3(x, y, 0), size=0.1):
                return (x, y)
                
        return (x, y)
