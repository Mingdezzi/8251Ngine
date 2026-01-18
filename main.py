from engine.core.app import App
from game.scenes.test_scene import TestScene

if __name__ == "__main__":
    app = App(title="8251Ngine - Isometric Core")
    scene = TestScene(name="MainScene")
    app.set_scene(scene)
    app.run()
