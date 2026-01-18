import pygame
import sys
import random

# Ensure pygame is available globally
global pygame

from engine.graphics.renderer import Renderer
from engine.graphics.lighting import LightingManager
from engine.core.time import TimeManager
from engine.core.input import InputManager
from engine.net.network import NetworkManager
from engine.assets.loader import ResourceManager
from engine.audio.audio_manager import AudioManager
from engine.core.interaction import InteractionManager
from engine.systems.minigame import MinigameManager
from engine.systems.combat import CombatManager
from engine.ui.world_ui import WorldPopupManager
from engine.physics.navigation import NavigationManager

class App:
    instance = None

    def __init__(self, width=1280, height=720, title="8251Ngine", use_network=True):
        App.instance = self
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = True
        self.use_network = use_network
        
        # Core Engine Services
        self.services = {
            "input": InputManager(),
            "renderer": Renderer(self.screen),
            "lighting": LightingManager(width, height),
            "time": TimeManager(),
            "network": NetworkManager("ws://localhost:8765") if use_network else None,
            "assets": ResourceManager(),
            "audio": AudioManager(),
            "interaction": InteractionManager(),
            "minigame": MinigameManager(),
            "combat": CombatManager(),
            "popups": WorldPopupManager(),
            "nav": None,
            "app": self
        }
        
        self.ui_root = None
        self.root = None
        self.fov_polygon = None

    def set_ui(self, ui_root):
        self.ui_root = ui_root

    def set_scene(self, scene_root):
        self.root = scene_root
        if self.root:
            self.root._ready(self.services)

    def run(self):
        if self.use_network and self.services["network"]:
            self.services["network"].start()
            
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            
        if self.use_network and self.services["network"]:
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
            
            # [수정됨] 모든 이벤트를 UI와 Scene에 전달
            if self.ui_root:
                self.ui_root.handle_event(event)
            
            # Scene(Node)이 handle_event 메서드를 가지고 있다면 호출 (Zoom 처리를 위해)
            if self.root and hasattr(self.root, 'handle_event'):
                self.root.handle_event(event)

    def _update(self, dt):
        self.services["input"].update()
        self.services["time"].update(dt)
        self.services["lighting"].ambient_color = self.services["time"].current_ambient
        self.services["lighting"].update_weather(dt)
        self.services["interaction"].update()
        self.services["minigame"].update(dt, self.services)
        self.services["combat"].update(dt, self.services)
        self.services["popups"].update(dt)
        
        if self.root:
            self.root._update(dt, self.services)

    def _draw(self):
        self.screen.fill((20, 20, 25))
        renderer = self.services["renderer"]
        lighting = self.services["lighting"]
        interaction = self.services["interaction"]
        minigame = self.services["minigame"]
        combat = self.services["combat"]
        popups = self.services["popups"]
        
        if self.root:
            renderer.clear_queue()
            def _collect_nodes(node):
                if not node.visible: return
                renderer.submit(node)
                if hasattr(node, 'get_light_surface'):
                    if node not in lighting.lights: lighting.add_light(node)
                for child in node.children: _collect_nodes(child)
            _collect_nodes(self.root)
            
            # Draw Gizmos (Grids) BEFORE objects/shadows
            self.root.draw_gizmos(self.screen, renderer.camera)
            
            renderer.flush(self.services)
            interaction.draw(self.screen, renderer.camera)
            combat.draw(self.screen, renderer.camera)
            popups.draw(self.screen, renderer.camera)
            lighting.render(self.screen, renderer.camera, self.fov_polygon)
            minigame.draw(self.screen)
            
        if self.ui_root:
            self.ui_root.draw(self.screen, self.services)
        pygame.display.flip()