import pygame
import os

class Assets:
    _textures = {}

    @staticmethod
    def load_texture(name, path):
        if name not in Assets._textures:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                Assets._textures[name] = img
            else:
                print(f"[Error] Asset path not found: {path}")
                return None
        return Assets._textures[name]

    @staticmethod
    def get(name):
        return Assets._textures.get(name)
