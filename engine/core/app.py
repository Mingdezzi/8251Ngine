import pygame
import sys
from engine.graphics.renderer import Renderer
from engine.graphics.lighting import LightingManager
from engine.core.time import TimeManager
from engine.core.input import InputManager
from engine.net.network import NetworkManager

class App:
    def __init__(self, width=1280, height=720, title="8251Ngine"):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Core Engine Services
        self.services = {
            "input": InputManager(),
            "renderer": Renderer(self.screen),
            "lighting": LightingManager(width, height),
            "time": TimeManager(),
            "network": NetworkManager("ws://localhost:8765"),
            "app": self # Allow access to app-level properties like fov_polygon
        }
        
        self.ui_root = None
        self.root = None # Active scene
        self.fov_polygon = None # TODO: This should be managed by a better system

    def set_ui(self, ui_root):
        self.ui_root = ui_root

    def set_scene(self, scene_root):
        self.root = scene_root
        if self.root:
            self.root._ready()

    def run(self):
        self.services["network"].start()
        
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            self._handle_events()
            self._update(dt)
            self._draw()
        
        self.services["network"].stop()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.services["renderer"]._update_screen(self.screen)
                self.services["lighting"].update_resolution(event.w, event.h)

    def _update(self, dt):
        self.services["input"].update()
        self.services["time"].update(dt)
        self.services["lighting"].ambient_color = self.services["time"].current_ambient
        
        if self.root:
            self.root._update(dt, self.services)

    def _draw(self):
        self.screen.fill((20, 20, 25))
        
        renderer = self.services["renderer"]
        lighting = self.services["lighting"]
        
        if self.root:
            renderer.clear_queue()
            
            # Scene graph traversal for rendering and light collection
            def _collect_nodes(node):
                if not node.visible: return
                renderer.submit(node)
                if hasattr(node, 'get_light_surface'):
                    if node not in lighting.lights:
                        lighting.add_light(node)
                for child in node.children:
                    _collect_nodes(child)
            
            _collect_nodes(self.root)
            
            renderer.flush(self.services)
            lighting.render(self.screen, renderer.camera, self.fov_polygon)
            
        if self.ui_root:
            self.ui_root.draw(self.screen)
            
        pygame.display.flip()
