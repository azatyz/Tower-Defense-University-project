import pygame
import sys
import random
from settings import *

def init_game():
    """Инициализация"""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("My Tower Defense Project")
    clock = pygame.time.Clock()
    return screen, clock

def game_loop():
    """Главный цикл"""
    screen, clock = init_game()
    running = True

    while running:
        # 1. Обработка событий (нажатия клавиш, выход)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Обновление логики (пока пусто)
        
        # 3. Отрисовка
        screen.fill(BLACK) # Фон
        
        # Рисуем "заглушку" башни (просто квадрат)
        pygame.draw.rect(screen, GREEN, (WIDTH//2 - 25, HEIGHT//2 - 25, 50, 50))
        
        pygame.display.flip()
        clock.tick(FPS)

def create_enemies():
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

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()