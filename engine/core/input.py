import pygame

class Input:
    _actions = {
        "move_left": [pygame.K_LEFT, pygame.K_a],
        "move_right": [pygame.K_RIGHT, pygame.K_d],
        "move_up": [pygame.K_UP, pygame.K_w],
        "move_down": [pygame.K_DOWN, pygame.K_s],
        "jump": [pygame.K_SPACE],
        "run": [pygame.K_LSHIFT, pygame.K_RSHIFT],
        "crouch": [pygame.K_LCTRL, pygame.K_RCTRL],
        "toggle_camera": [pygame.K_c],
    }
    
    _pressed_keys = []

    @staticmethod
    def update():
        Input._pressed_keys = pygame.key.get_pressed()

    @staticmethod
    def is_action_pressed(action_name):
        if action_name not in Input._actions: return False
        for key in Input._actions[action_name]:
            if Input._pressed_keys[key]:
                return True
        return False

    @staticmethod
    def get_vector(left, right, up, down):
        """Returns a normalized direction vector based on actions"""
        x = 0
        y = 0
        if Input.is_action_pressed(right): x += 1
        if Input.is_action_pressed(left): x -= 1
        if Input.is_action_pressed(down): y += 1
        if Input.is_action_pressed(up): y -= 1
        return x, y

    @staticmethod
    def get_mouse_grid_pos(camera):
        """
        Returns the Grid Coordinate (x, y) under the mouse cursor.
        """
        from engine.core.math_utils import IsoMath, TILE_HEIGHT
        mx, my = pygame.mouse.get_pos()
        
        # [Offset Correction]
        # Reverting manual offset. Standard math should align with midbottom pivot.
        adj_my = my 
        
        # Screen to World (Undo Camera)
        wx = (mx - camera.offset.x) / camera.zoom + camera.position.x
        wy = (adj_my - camera.offset.y) / camera.zoom + camera.position.y
        
        return IsoMath.iso_to_cart(wx, wy)
