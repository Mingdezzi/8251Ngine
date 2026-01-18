from engine.core.node import Node

class Interactable(Node):
    def __init__(self, name="Interactable", radius=1.2):
        super().__init__(name)
        self.radius = radius # 상호작용 가능 거리 (그리드 단위)
        self.on_interact_callback = None
        self.enabled = True

    def interact(self, actor):
        """actor: 상호작용을 시도하는 엔티티 (예: Player)"""
        if not self.enabled: return False
        
        # 거리 체크
        dist = self.get_global_position().distance_to(actor.get_global_position())
        if dist <= self.radius:
            if self.on_interact_callback:
                self.on_interact_callback(actor)
                return True
        return False

# 예시: 문 노드
class Door(Node):
    def __init__(self, name="Door"):
        super().__init__(name)
        self.is_open = False
        
        # 상호작용 노드 자식으로 추가
        self.trigger = Interactable("DoorTrigger")
        self.trigger.on_interact_callback = self.toggle
        self.add_child(self.trigger)

    def toggle(self, actor):
        self.is_open = not self.is_open
        print(f"Door is now {'Open' if self.is_open else 'Closed'}")
        # 여기서 애니메이션 재생이나 스프라이트 변경 로직
