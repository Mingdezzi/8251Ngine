class Component:
    """Base class for all components that can be attached to a Node"""
    def __init__(self):
        self.node = None

    def _on_added(self, node):
        self.node = node
        self.ready()

    def ready(self):
        pass

    def update(self, dt, services):
        pass
