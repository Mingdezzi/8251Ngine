import pygame

class Control:
    def __init__(self, x=0, y=0, w=100, h=50, tag=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.visible = True
        self.children = []
        self.parent = None
        self.is_hovered = False
        self.is_focused = False
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
            was_focused = self.is_focused
            self.is_focused = self.is_hovered
            if self.is_hovered:
                if self.on_click: self.on_click()
                return True
            return was_focused # Return true if we were focused but clicked away (to consume event)
        
        return False

    def draw(self, screen, services):
        if not self.visible: return
        self._draw_self(screen, services)
        for child in self.children:
            child.draw(screen, services)

    def _draw_self(self, screen, services):
        pass

    def get_child_by_tag(self, tag):
        for child in self.children:
            if child.tag == tag: return child
            res = child.get_child_by_tag(tag)
            if res: return res
        return None

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
        self._surf = self.font.render(str(self.text), True, self.color)
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
        self.surf = pygame.Surface((max(1, self.rect.width), max(1, self.rect.height)), pygame.SRCALPHA)
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
        
        tw, th = self.label._surf.get_size()
        self.label.rect.x = self.rect.x + (self.rect.width - tw) // 2
        self.label.rect.y = self.rect.y + (self.rect.height - th) // 2

    def to_dict(self):
        d = super().to_dict()
        d.update({"text": self.text, "base_color": list(self.base_color), "hover_color": list(self.hover_color)})
        return d

class LineEdit(Control):
    def __init__(self, text="", x=0, y=0, w=200, h=30, tag=""):
        super().__init__(x, y, w, h, tag)
        self.text = str(text)
        self.on_text_changed = None # Callback (text) -> None
        self.font = pygame.font.SysFont("arial", 18)
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if super().handle_event(event): return True
        
        if self.is_focused and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.is_focused = False
            else:
                if event.unicode.isprintable():
                    self.text += event.unicode
            
            if self.on_text_changed:
                self.on_text_changed(self.text)
            return True
        return False

    def _draw_self(self, screen, services):
        # Draw background
        bg_col = (40, 40, 45) if not self.is_focused else (60, 60, 70)
        pygame.draw.rect(screen, bg_col, self.rect)
        border_col = (100, 100, 255) if self.is_focused else (100, 100, 100)
        pygame.draw.rect(screen, border_col, self.rect, 2)
        
        # Draw text
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surf, (self.rect.x + 5, self.rect.y + (self.rect.height - txt_surf.get_height()) // 2))
        
        # Draw cursor
        if self.is_focused:
            self.cursor_timer += 1
            if (self.cursor_timer // 30) % 2 == 0:
                cx = self.rect.x + 8 + txt_surf.get_width()
                pygame.draw.line(screen, (255, 255, 255), (cx, self.rect.y + 5), (cx, self.rect.bottom - 5), 2)
