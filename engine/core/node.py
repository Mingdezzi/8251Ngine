from pygame.math import Vector3

class Node:
    def __init__(self, name="Node"):
        self.name = name
        self.tag = name # [NEW] Tag for IDE identification
        self.parent = None
        self.children = []
        self.components = [] # New: Component list
        
        # Transform (3D Logic in 2.5D world)
        self.position = Vector3(0, 0, 0)
        self.scale = Vector3(1, 1, 1)
        self.visible = True
        self.z_index = 0

    def add_component(self, component):
        self.components.append(component)
        component._on_added(self)
        return component

    def get_component(self, component_type):
        for c in self.components:
            if isinstance(c, component_type):
                return c
        return None

    def add_child(self, node):
        if node.parent:
            node.parent.remove_child(node)
        node.parent = self
        self.children.append(node)
        node._ready()

    def remove_child(self, node):
        if node in self.children:
            self.children.remove(node)
            node.parent = None

    def get_global_position(self):
        """Recursively calculates global position based on parents"""
        if self.parent and isinstance(self.parent, Node):
            return self.parent.get_global_position() + self.position
        return self.position

    # --- Lifecycle Methods ---
    def _ready(self):
        """Called when added to the scene tree"""
        pass

    def _update(self, dt, services):
        """Called every frame by the App loop"""
        # Update components first
        for comp in self.components:
            comp.update(dt, services)
            
        for child in self.children:
            child._update(dt, services)
        self.update(dt, services)

    def _draw(self, services):
        """Called every frame for rendering"""
        if not self.visible: return
        
        # Renderer is now a service
        renderer = services.get("renderer")
        if renderer:
            renderer.submit(self)
        
        for child in self.children:
            child._draw(services)

    # --- User Override Methods ---
    def update(self, dt, services):
        """User-overridable update method"""
        pass

    def draw_gizmos(self, screen, camera):
        """Draw debug info or editor grids. Called directly by App."""
        pass
