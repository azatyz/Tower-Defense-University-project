import pygame
import sys
import random
from settings import *

# _global_
base_health = 100 

def create_enemy():
    return {
        'x': 0,
        'y': random.randint(100, HEIGHT - 100),
        'speed': random.randint(2, 5),
        'hp': 100
    }

def move_enemies(enemies):
    for enemy in enemies:
        enemy['x'] += enemy['speed']

def draw_enemies(screen, enemies):
    for enemy in enemies:
        pygame.draw.circle(screen, RED, (enemy["x"], enemy["y"]), 15)

def check_collisions(enemies):
    global base_health
    
    for enemy in enemies:
        if enemy["x"] >= WIDTH - 60:
            base_health -= 10
            print(f"База атакована! Осталось HP: {base_health}")

    enemies[:] = [e for e in enemies if e["x"] < WIDTH - 60]


def game_loop():
    """ Главный игровой цикл """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower Defense Project")
    clock = pygame.time.Clock()   

    enemies = []     
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Пробел - спавн врага
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    enemies.append(create_enemy())

        move_enemies(enemies)        # Двигаем мобов
        check_collisions(enemies)    # Проверяем, не дошел ли кто-то до базы

        screen.fill(BLACK) # Чистим экран в черный цвет
        
        pygame.draw.rect(screen, GREEN, (WIDTH - 60, HEIGHT // 2 - 50, 50, 100))
        
        draw_enemies(screen, enemies)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()