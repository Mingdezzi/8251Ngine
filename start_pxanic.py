from engine.core.app import App
from game.scenes.pxanic_scene import PxAnicScene
import pygame

def main():
    # 8251Ngine 초기화
    app = App(width=1280, height=720, title="8251Ngine - PxANIC! Isometric Port", use_network=False)
    
    # PxANIC! 전용 씬 생성
    scene = PxAnicScene(name="PxAnicWorld")
    
    # 씬 설정 및 실행
    app.set_scene(scene)
    
    print("--- 8251Ngine: PxANIC! Isometric Port Started ---")
    print("Controls: WASD (Move), Shift (Run)")
    print("-------------------------------------------------")
    
    app.run()

if __name__ == "__main__":
    main()
