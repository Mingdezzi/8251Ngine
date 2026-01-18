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

    def handle_event(self, event, parent_abs_pos=(0, 0)):
        if not self.visible: return False

        self_abs_rect = self.rect.move(parent_abs_pos)

        # 자식부터 역순으로 처리해야 올바르게 클릭 이벤트를 소비함
        for child in reversed(self.children):
            if child.handle_event(event, self_abs_rect.topleft):
                return True

        # 현재 컨트롤의 이벤트 처리
        if hasattr(event, 'pos'):
            if self_abs_rect.collidepoint(event.pos):
                if event.type == pygame.MOUSEMOTION:
                    self.is_hovered = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.is_focused = True
                    if self.on_click:
                        self.on_click()
                    return True
            else:
                self.is_hovered = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.is_focused = False # 다른 곳 클릭 시 포커스 해제

        if self.is_focused and event.type == pygame.KEYDOWN:
            # LineEdit와 같은 자식 클래스에서 오버라이드하여 처리
            return False

        return False

    def draw(self, screen, services, parent_abs_pos=(0, 0)):
        if not self.visible: return
        
        self_abs_pos = (self.rect.x + parent_abs_pos[0], self.rect.y + parent_abs_pos[1])
        
        self._draw_self(screen, services, self_abs_pos)
        
        for child in self.children:
            child.draw(screen, services, self_abs_pos)

    def _draw_self(self, screen, services, abs_pos):
        pass

class Label(Control):
    def __init__(self, text, x, y, size=20, color=(255, 255, 255), **kwargs):
        super().__init__(x, y, 1, 1, **kwargs)
        self.text = text; self.color = color; self.size = size
        self.font = pygame.font.SysFont("arial", size, bold=True)
        self._render_text()

    def _render_text(self):
        self.surf = self.font.render(self.text, True, self.color)
        self.rect.size = self.surf.get_size()

    def _draw_self(self, screen, services, abs_pos):
        screen.blit(self.surf, abs_pos)

class Panel(Control):
    def __init__(self, x, y, w, h, color=(50, 50, 60, 200), **kwargs):
        super().__init__(x, y, w, h, **kwargs)
        self.color = color

    def _draw_self(self, screen, services, abs_pos):
        pygame.draw.rect(screen, self.color, (*abs_pos, *self.rect.size))
        pygame.draw.rect(screen, (100, 100, 110), (*abs_pos, *self.rect.size), 2)

class Button(Control):
    def __init__(self, text, x, y, w, h, color=(70, 70, 80), **kwargs):
        super().__init__(x, y, w, h, **kwargs)
        self.text = text
        self.base_color = color
        self.label = Label(text, 0, 0, size=16)
        # 라벨의 위치는 draw 시점에 부모(버튼)의 중앙으로 계산
        self.add_child(self.label)

    def _draw_self(self, screen, services, abs_pos):
        color = (100, 100, 110) if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, (*abs_pos, *self.rect.size))
        pygame.draw.rect(screen, (120, 120, 130), (*abs_pos, *self.rect.size), 1)

        # 라벨을 버튼의 중앙에 위치시키기
        text_w, text_h = self.label.rect.size
        self.label.rect.x = self.rect.w / 2 - text_w / 2
        self.label.rect.y = self.rect.h / 2 - text_h / 2

class LineEdit(Control):
    def __init__(self, text, x, y, w, h, **kwargs):
        super().__init__(x, y, w, h, **kwargs)
        self.text = text
        self.last_input_time = 0
        self.input_cooldown = 100 # 100ms 쿨다운

    def handle_event(self, event, parent_abs_pos=(0, 0)):
        self_abs_rect = self.rect.move(parent_abs_pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.is_focused = self_abs_rect.collidepoint(event.pos)
            return self.is_focused

        if self.is_focused and event.type == pygame.KEYDOWN:
            now = pygame.time.get_ticks()
            if now - self.last_input_time < self.input_cooldown:
                return True # 쿨다운 중이면 이벤트 소비만 함

            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.last_input_time = now
            elif event.key == pygame.K_RETURN:
                self.is_focused = False
            elif event.unicode.isprintable():
                self.text += event.unicode
                self.last_input_time = now
            return True
        return False

    def _draw_self(self, screen, services, abs_pos):
        bg = (80, 80, 90) if self.is_focused else (50, 50, 60)
        pygame.draw.rect(screen, bg, (*abs_pos, *self.rect.size))
        pygame.draw.rect(screen, (120, 120, 130), (*abs_pos, *self.rect.size), 1)
        
        font = pygame.font.SysFont("arial", 18)
        text_surf = font.render(self.text, True, (220, 220, 230))
        screen.blit(text_surf, (abs_pos[0] + 5, abs_pos[1] + self.rect.h / 2 - text_surf.get_height() / 2))