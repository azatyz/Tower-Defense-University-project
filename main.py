import pygame
import sys
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

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()