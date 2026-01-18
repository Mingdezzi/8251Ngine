import pygame
from engine.graphics.camera import Camera
from engine.core.math_utils import IsoMath

from engine.graphics.shadow_renderer import ShadowRenderer

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.camera = Camera()
        self.render_queue = []
        
        # Initial viewport setup
        self.camera.update_viewport(screen.get_width(), screen.get_height())

    def clear_queue(self):
        self.render_queue.clear()

    def submit(self, node):
        """
        Submits a node to be rendered.
        """
        if hasattr(node, 'get_sprite'):
            sprite = node.get_sprite()
            if sprite:
                gpos = node.get_global_position()
                iso_x, iso_y = IsoMath.cart_to_iso(gpos.x, gpos.y, gpos.z)
                depth = IsoMath.get_depth(gpos.x, gpos.y, gpos.z)
                
                self.render_queue.append({
                    'depth': depth,
                    'sprite': sprite,
                    'pos': (iso_x, iso_y),
                    'scale': node.scale,
                    'node': node # Keep ref for shadow calc
                })

    def flush(self, services):
        # 1. Update Camera
        self.camera.update()
        
        # [Soft Shadow Pass]
        shadow_scale = 0.5
        sw = int(self.screen.get_width() * shadow_scale)
        sh = int(self.screen.get_height() * shadow_scale)
        shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        
        time_manager = services.get("time")
        lighting_manager = services.get("lighting")
        
        # --- A. Directional Shadows (Sun/Moon) ---
        if time_manager and time_manager.current_phase != 'NIGHT':
            sun_dir = time_manager.sun_direction
            for item in self.render_queue:
                node = item['node']
                ShadowRenderer.draw_directional_shadow(shadow_surf, self.camera, node, sun_dir, scale=shadow_scale)
        
        # --- B. Point Light Shadows ---
        main_light = None
        if lighting_manager:
            for l in lighting_manager.lights:
                if l.name == "PlayerLight": # TODO: Don't hardcode this
                    main_light = l
                    break
        
        if main_light:
            light_pos = main_light.get_global_position()
            if light_pos.z < 2: light_pos.z = 3.0
            
            for item in self.render_queue:
                node = item['node']
                if hasattr(node, 'size_z') and node.size_z > 0.2:
                    ShadowRenderer.draw_shadow_volume(shadow_surf, self.camera, node, light_pos, scale=shadow_scale)

        # Blit all shadows
        full_shadow = pygame.transform.smoothscale(shadow_surf, self.screen.get_size())
        self.screen.blit(full_shadow, (0, 0))

        # 3. Sort by Depth
        self.render_queue.sort(key=lambda x: x['depth'])
        
        # 4. Draw Objects (Pass 2)
        for item in self.render_queue:
            sx, sy = self.camera.world_to_screen(*item['pos'])
            img = item['sprite']
            
            # [Pivot Correction]
            from engine.core.math_utils import TILE_HEIGHT
            rect = img.get_rect(midbottom=(sx, sy + TILE_HEIGHT // 2))
            
            # Final Screen Bound Check (Frustum Culling)
            if self.screen.get_rect().colliderect(rect):
                self.screen.blit(img, rect)
