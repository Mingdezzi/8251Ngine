import pygame

class Control:
    def __init__(self, x=0, y=0, w=100, h=50):
        self.rect = pygame.Rect(x, y, w, h)
        self.visible = True
        self.children = []
        self.parent = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def draw(self, screen):
        if not self.visible: return
        self._draw_self(screen)
        for child in self.children:
            child.draw(screen)

    def _draw_self(self, screen):
        pass

class Label(Control):
    def __init__(self, text="Label", x=0, y=0, size=20, color=(255, 255, 255)):
        super().__init__(x, y, 100, size)
        self.text = text
        self.color = color
        self.font = pygame.font.SysFont("arial", size, bold=True)
        self._surf = None
        self._render_text()

    def set_text(self, text):
        if self.text != text:
            self.text = text
            self._render_text()

    def _render_text(self):
        self._surf = self.font.render(self.text, True, self.color)

    def _draw_self(self, screen):
        if self._surf:
            screen.blit(self._surf, (self.rect.x, self.rect.y))

class Panel(Control):
    def __init__(self, x, y, w, h, color=(50, 50, 50, 200)):
        super().__init__(x, y, w, h)
        self.color = color
        self.surf = pygame.Surface((w, h), pygame.SRCALPHA)
        self.surf.fill(color)

    def _draw_self(self, screen):
        screen.blit(self.surf, (self.rect.x, self.rect.y))
