import os
import pygame
from engine.core.app import App
from game.scenes.editor_scene import EditorScene

def main():
    # Ensure assets directory exists
    if not os.path.exists("assets/maps"):
        os.makedirs("assets/maps")

    # Create App
    app = App(title="8251Ngine - LEVEL EDITOR", use_network=False)
    
    # Create Editor Scene
    editor_scene = EditorScene()
    
    # Set Scene
    app.set_scene(editor_scene)
    
    print("--- 8251Ngine Editor Started ---")
    print("Left Click: Place/Update Block")
    print("Right Click: Delete Block")
    print("Middle Mouse: Pan Camera")
    print("---------------------------------")
    
    app.run()

if __name__ == "__main__":
    main()
