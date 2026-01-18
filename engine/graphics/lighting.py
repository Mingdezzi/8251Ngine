import pygame
from engine.core.node import Node
from engine.core.math_utils import IsoMath

class LightSource(Node):
    def __init__(self, name="Light", radius=200, color=(255, 255, 200), intensity=1.0):
        super().__init__(name)
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self._cache_surf = None
        self._cache_key = None

    def get_light_surface(self):
        """Returns a cached light circle surface with smooth gradient"""
        key = (self.radius, self.color, self.intensity)
        if self._cache_surf and self._cache_key == key:
            return self._cache_surf
        
        size = int(self.radius * 2)
        # Low-res texture creation for smoothness performance
        # Create at 1/2 size then upscale? No, gradients are better drawn directly.
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        
        # High Quality Gradient: 20 steps
        steps = 20
        max_alpha = int(255 * self.intensity)
        
        for i in range(steps):
            r = self.radius * (1 - i/steps)
            # Quadratic falloff for natural light
            progress = i / steps
            alpha = int(max_alpha * (1 - progress * progress)) 
            pygame.draw.circle(surf, (*self.color, alpha // steps), center, int(r))
            
        self._cache_surf = surf
        self._cache_key = key
        return surf

class DirectionalLight(Node):
    def __init__(self, name="Sun", direction=(1, 1), color=(255, 255, 255), intensity=0.0):
        super().__init__(name)
        self.direction = pygame.math.Vector2(direction).normalize()
        self.color = color
        self.intensity = intensity

class LightingManager:
    def __init__(self, width, height, ambient_color=(20, 20, 30)):
        self.width = width
        self.height = height
        self.ambient_color = ambient_color
        
        self.scale_factor = 0.5 
        self.lightmap_w = int(width * self.scale_factor)
        self.lightmap_h = int(height * self.scale_factor)
        
        self.lightmap = pygame.Surface((self.lightmap_w, self.lightmap_h))
        self.lights = [] # Point Lights
        self.directional_light = None # Single Sun/Moon

    def set_directional_light(self, light):
        self.directional_light = light

    def render(self, screen, camera, fov_polygon=None):
        # 1. Fill with ambient darkness
        self.lightmap.fill(self.ambient_color)
        
        # 2. Apply Directional Light (Global Tint)
        # In 2D, directional light just brightens the whole map evenly?
        # Or casts shadows?
        # Shadows are handled by ShadowRenderer.
        # Here we just add global brightness if intensity > 0
        if self.directional_light and self.directional_light.intensity > 0:
            # Additive blend a color over the whole map
            # Intensity 1.0 = Add full color
            r = int(self.directional_light.color[0] * self.directional_light.intensity)
            g = int(self.directional_light.color[1] * self.directional_light.intensity)
            b = int(self.directional_light.color[2] * self.directional_light.intensity)
            self.lightmap.fill((r, g, b), special_flags=pygame.BLEND_RGB_ADD)
        
        # 3. Draw Point Lights
        for light in self.lights:
            if not light.visible: continue
            # ... (Existing point light logic) ...
            gpos = light.get_global_position()
            sx, sy = camera.world_to_screen(*IsoMath.cart_to_iso(gpos.x, gpos.y, gpos.z))
            lx = int(sx * self.scale_factor)
            ly = int(sy * self.scale_factor)
            l_rad = light.radius * self.scale_factor
            if not (-l_rad < lx < self.lightmap_w + l_rad and -l_rad < ly < self.lightmap_h + l_rad): continue

            lsurf = light.get_light_surface()
            l_w, l_h = lsurf.get_size()
            target_w = int(l_w * self.scale_factor)
            target_h = int(l_h * self.scale_factor)
            if target_w < 1 or target_h < 1: continue
            
            scaled_light = pygame.transform.smoothscale(lsurf, (target_w, target_h))
            dest_rect = scaled_light.get_rect(center=(lx, ly))
            self.lightmap.blit(scaled_light, dest_rect, special_flags=pygame.BLEND_RGB_ADD)

        # 4. Apply FOV (Vision Mask)
        if fov_polygon:
            mask_surf = pygame.Surface((self.lightmap_w, self.lightmap_h), pygame.SRCALPHA)
            screen_poly = []
            for px, py in fov_polygon:
                sx, sy = camera.world_to_screen(*IsoMath.cart_to_iso(px, py))
                screen_poly.append((int(sx * self.scale_factor), int(sy * self.scale_factor)))
            
            if len(screen_poly) > 2:
                pygame.draw.polygon(mask_surf, (255, 255, 255), screen_poly)
                pygame.draw.lines(mask_surf, (255, 255, 255, 100), True, screen_poly, width=6)
                pygame.draw.lines(mask_surf, (255, 255, 255, 50), True, screen_poly, width=12)
                self.lightmap.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # 5. Upscale and Apply to Screen
        full_lightmap = pygame.transform.smoothscale(self.lightmap, (self.width, self.height))
        screen.blit(full_lightmap, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)