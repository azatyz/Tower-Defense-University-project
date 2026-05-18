import pygame
import sys
import random
from settings import *


class Enemy:
    """Класс для представления врага"""
    def __init__(self, x=0, y=None):
        self.x = x
        self.y = y if y is not None else random.randint(100, HEIGHT - 100)
        self.speed = random.randint(2, 5)
        self.hp = 100
        self.radius = 15

    def update(self):
        self.x += self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (self.x, self.y), self.radius)

    def is_out_of_bounds(self):
        return self.x >= WIDTH - 60


# _global_
base_health = 100 

def move_enemies(enemies):
    for enemy in enemies:
        enemy.update()


def draw_enemies(screen, enemies):
    for enemy in enemies:
        enemy.draw(screen)


def check_collisions(enemies):
    global base_health
    
    out_of_bounds = []
    for enemy in enemies:
        if enemy.is_out_of_bounds():
            base_health -= 10
            print(f"База атакована! Осталось HP: {base_health}")
            out_of_bounds.append(enemy)
    
    # Удалить врагов, дошедших до базы
    for enemy in out_of_bounds:
        enemies.remove(enemy)


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
                    enemies.append(Enemy())

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