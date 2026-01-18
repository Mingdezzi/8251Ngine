import pygame
from engine.core.component import Component

class Item:
    def __init__(self, id, name, desc, price=0, icon=None):
        self.id = id
        self.name = name
        self.desc = desc
        self.price = price
        self.icon = icon

# Global Item Database (Based on PxANIC-)
ITEM_DB = {
    'TANGERINE': Item('TANGERINE', '귤', 'HP +20', 3),
    'CHOCOBAR': Item('CHOCOBAR', '초코바', 'AP +20', 3),
    'MEDKIT': Item('MEDKIT', '구급키트', 'HP Full Recovery', 15),
    'BATTERY': Item('BATTERY', '건전지', 'Battery +50%', 3),
}

class InventoryComponent(Component):
    def __init__(self, capacity=10):
        super().__init__()
        self.capacity = capacity
        self.items = {} # ID: Count
        self.gold = 10
        
        # Stats tied to inventory/status
        self.hp = 100
        self.ap = 100

    def _on_added(self, node):
        self.node = node

    def add_item(self, item_id, count=1):
        if item_id not in ITEM_DB: return False
        self.items[item_id] = self.items.get(item_id, 0) + count
        print(f"Inventory: Added {item_id} x{count}")
        return True

    def use_item(self, item_id):
        if self.items.get(item_id, 0) <= 0: return False
        
        # Application logic
        success = False
        if item_id == 'TANGERINE':
            self.hp = min(100, self.hp + 20); success = True
        elif item_id == 'CHOCOBAR':
            self.ap = min(100, self.ap + 20); success = True
        elif item_id == 'MEDKIT':
            self.hp = 100; success = True
            
        if success:
            self.items[item_id] -= 1
            print(f"Inventory: Used {item_id}. HP:{self.hp}, AP:{self.ap}")
        return success

    def update(self, dt, services):
        # Quick use keys (1, 2, 3...)
        input_mgr = services["input"]
        keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        item_ids = ['TANGERINE', 'CHOCOBAR', 'MEDKIT', 'BATTERY']
        
        for i, key in enumerate(keys):
            if pygame.key.get_pressed()[key]: # Using raw key for now as index
                # Debounce logic should be in InputManager, 
                # but for now we check if it's a just_pressed if we had an action
                pass

    def draw_hud(self, screen):
        # Draw basic status bar
        sw, sh = screen.get_size()
        pygame.draw.rect(screen, (30, 30, 35), (20, sh - 80, 200, 60))
        pygame.draw.rect(screen, (200, 50, 50), (30, sh - 70, int(180 * (self.hp/100)), 15)) # HP
        pygame.draw.rect(screen, (50, 200, 50), (30, sh - 45, int(180 * (self.ap/100)), 15)) # AP
        
        # Draw items
        for i, (iid, count) in enumerate(self.items.items()):
            if count > 0:
                pygame.draw.rect(screen, (60, 60, 70), (230 + i * 50, sh - 70, 45, 45))
                # Text for count
                font = pygame.font.SysFont("arial", 12)
                txt = font.render(f"{iid[:1]} x{count}", True, (255, 255, 255))
                screen.blit(txt, (235 + i * 50, sh - 65))
