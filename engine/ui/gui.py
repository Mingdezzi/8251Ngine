import pygame

class Control:
    def __init__(self, x=0, y=0, w=100, h=50, tag=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.visible = True
        self.children = []
        self.parent = None
        self.is_hovered = False
        self.on_click = None
        self.tag = tag

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def handle_event(self, event):
        if not self.visible: return False
        
        # 자식 요소들부터 이벤트 처리 (레이어 순서 고려)
        for child in reversed(self.children):
            if child.handle_event(event):
                return True

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and self.on_click:
                self.on_click()
                return True
        
        return self.is_hovered

    def draw(self, screen, services):
        if not self.visible: return
        self._draw_self(screen, services)
        for child in self.children:
            child.draw(screen, services)

    def _draw_self(self, screen, services):
        pass

    def center_in_screen(self, screen_w, screen_h):
        self.rect.x = (screen_w - self.rect.width) // 2
        self.rect.y = (screen_h - self.rect.height) // 2
        return self

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "rect": [self.rect.x, self.rect.y, self.rect.width, self.rect.height],
            "visible": self.visible,
            "tag": self.tag,
            "children": [c.to_dict() for c in self.children]
        }

class Label(Control):
    def __init__(self, text="Label", x=0, y=0, size=20, color=(255, 255, 255), tag=""):
        super().__init__(x, y, 100, size, tag)
        self.text = text
        self.color = color
        self.size = size
        self.font = pygame.font.SysFont("arial", size, bold=True)
        self._surf = None
        self._render_text()

    def set_text(self, text):
        if self.text != text:
            self.text = text
            self._render_text()

    def _render_text(self):
        self._surf = self.font.render(self.text, True, self.color)
        self.rect.width, self.rect.height = self._surf.get_size()

    def _draw_self(self, screen, services):
        if self._surf:
            screen.blit(self._surf, (self.rect.x, self.rect.y))

    def to_dict(self):
        d = super().to_dict()
        d.update({"text": self.text, "size": self.size, "color": list(self.color)})
        return d

class Panel(Control):
    def __init__(self, x, y, w, h, color=(50, 50, 50, 200), tag=""):
        super().__init__(x, y, w, h, tag)
        self.color = color
        self._regen_surf()

    def _regen_surf(self):
        self.surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.surf.fill(self.color)

    def _draw_self(self, screen, services):
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)
        screen.blit(self.surf, (self.rect.x, self.rect.y))

    def to_dict(self):
        d = super().to_dict()
        d.update({"color": list(self.color)})
        return d

class Button(Control):
    def __init__(self, text, x, y, w, h, color=(70, 70, 70), hover_color=(100, 100, 100), tag=""):
        super().__init__(x, y, w, h, tag)
        self.text = text
        self.base_color = color
        self.hover_color = hover_color
        self.label = Label(text, 0, 0, size=16)
        self.add_child(self.label)

    def _draw_self(self, screen, services):
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1)
        
        # 텍스트 중앙 정렬
        tw, th = self.label._surf.get_size()
        self.label.rect.x = self.rect.x + (self.rect.width - tw) // 2
        self.label.rect.y = self.rect.y + (self.rect.height - th) // 2

    def to_dict(self):
        d = super().to_dict()
        d.update({"text": self.text, "base_color": list(self.base_color), "hover_color": list(self.hover_color)})
        return d
