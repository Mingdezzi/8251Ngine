from pygame.math import Vector3

class Node:
    def __init__(self, name="Node"):
        self.name = name
        self.parent = None
        self.children = []
        
        # Transform (3D Logic in 2.5D world)
        self.position = Vector3(0, 0, 0)
        self.scale = Vector3(1, 1, 1)
        self.visible = True
        self.z_index = 0 # Manual layer override

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

    # --- Lifecycle Methods (Godot Style) ---
    def _ready(self):
        """Called when added to the scene tree"""
        pass

    def _update(self, dt):
        """Called every frame"""
        for child in self.children:
            child._update(dt)
        self.update(dt)

    def _draw(self, renderer):
        """Called every frame for rendering"""
        if not self.visible: return
        
        # Pre-order traversal? 
        # Actually for Iso, we don't draw recursively immediately.
        # We submit ourselves to the Renderer's Queue.
        renderer.submit(self)
        
        for child in self.children:
            child._draw(renderer)

    # User Override Methods
    def update(self, dt):
        pass
