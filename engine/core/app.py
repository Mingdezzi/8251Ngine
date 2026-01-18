import pygame
import sys
from engine.graphics.renderer import Renderer
from engine.graphics.lighting import LightingManager
from engine.core.time import TimeManager

class App:
    instance = None

    def __init__(self, width=1280, height=720, title="8251Ngine"):
        App.instance = self
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Engine Components
        self.renderer = Renderer(self.screen)
        self.lighting = LightingManager(width, height)
        self.time = TimeManager()
        self.ui_root = None # Root for UI elements
        
        self.root = None # The active scene
        self.fov_polygon = None 

    def set_ui(self, ui_root):
        self.ui_root = ui_root

    def _draw(self):
        self.screen.fill((20, 20, 25)) # Dark Grey BG
        
        if self.root:
            self.renderer.clear_queue()
            self._collect_nodes(self.root)
            self.renderer.flush()
            self.lighting.render(self.screen, self.renderer.camera, self.fov_polygon)
            
        # 4. Render UI (Topmost)
        if self.ui_root:
            self.ui_root.draw(self.screen)
            
        pygame.display.flip() # Current frame visibility polygon

    def set_scene(self, scene_root):
        self.root = scene_root
        if self.root:
            self.root._ready()

    def run(self):
        from engine.core.input import Input
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            Input.update()
            self._handle_events()
            self._update(dt)
            self._draw()
        
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                # Handle resize
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.renderer = Renderer(self.screen) # Re-init renderer camera bounds
                self.lighting.update_resolution(event.w, event.h)

    def _update(self, dt):
        self.time.update(dt)
        self.lighting.ambient_color = self.time.current_ambient
        
        if self.root:
            self.root._update(dt)

    def _draw(self):
        self.screen.fill((20, 20, 25)) # Dark Grey BG
        
        if self.root:
            # 1. Clear Queues
            self.renderer.clear_queue()
            # Note: We need to collect lights too. 
            # A proper scene graph traversal would collect renderables AND lights.
            # For now, let's assume lights register themselves to App.lighting or we traverse.
            # Simple Traversal for this engine stage:
            self._collect_nodes(self.root)
            
            # 2. Render Geometry
            self.renderer.flush()
            
            # 3. Render Lighting Overlay
            self.lighting.render(self.screen, self.renderer.camera, self.fov_polygon)
            
        pygame.display.flip()

    def _collect_nodes(self, node):
        """Recursive node collection for rendering systems"""
        if not node.visible: return
        
        # Submit to Renderer if it's a visual object
        # (Duck typing: has get_sprite)
        self.renderer.submit(node)
        
        # Submit to Lighting if it's a light
        # (Duck typing: is LightSource instance or has get_light_surface)
        if hasattr(node, 'get_light_surface'):
            if node not in self.lighting.lights:
                self.lighting.add_light(node)
                
        for child in node.children:
            self._collect_nodes(child)
