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

    def get_distance_to(self, other_x, other_y):
        """Вычислить расстояние до точки (сложная функция)"""
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5


class Tower:
    """Класс для представления башни"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 40  # Радиус обстрела
        self.damage = 25
        self.cooldown = 0  # Текущая перезарядка
        self.cooldown_max = 30  # Максимальная перезарядка (в кадрах)
        self.width = 50
        self.height = 100

    def can_shoot(self):
        """Проверить, может ли башня стрелять"""
        return self.cooldown <= 0

    def find_target(self, enemies):
        """Найти ближайшего врага в радиусе (алгоритм поиска целей)"""
        targets = []
        for enemy in enemies:
            distance = enemy.get_distance_to(self.x, self.y)
            if distance <= self.radius:
                targets.append((distance, enemy))
        
        if targets:
            # Возвращаем врага с наименьшим расстоянием
            return min(targets, key=lambda t: t[0])[1]
        return None

    def update(self):
        """Обновить башню (перезарядка)"""
        if self.cooldown > 0:
            self.cooldown -= 1

    def shoot(self):
        """Выстрелить"""
        if self.can_shoot():
            self.cooldown = self.cooldown_max

    def draw(self, screen):
        """Нарисовать башню"""
        pygame.draw.rect(screen, GREEN, (self.x - self.width // 2, self.y - self.height // 2, 
                                         self.width, self.height))
        # Радиус обстрела
        pygame.draw.circle(screen, (0, 200, 0), (self.x, self.y), self.radius, 1)


class Projectile:
    """Класс для представления снаряда"""
    def __init__(self, start_x, start_y, target_x, target_y, damage):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.damage = damage
        self.speed = 8
        self.radius = 5
        
        # Вычисляем направление (сложная функция)
        dx = target_x - start_x
        dy = target_y - start_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        if distance > 0:
            self.vx = (dx / distance) * self.speed
            self.vy = (dy / distance) * self.speed
        else:
            self.vx = 0
            self.vy = 0

    def update(self):
        """Обновить позицию снаряда"""
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        """Нарисовать снаряд"""
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), self.radius)

    def is_out_of_bounds(self):
        """Проверить, вышел ли снаряд за границы экрана"""
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

    def get_distance_to(self, other_x, other_y):
        """Вычислить расстояние до точки"""
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5
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
    projectiles = []
    # Создаём башню в центре-справа экрана
    tower = Tower(WIDTH - 60, HEIGHT // 2)
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
        tower.update()               # Обновляем башню (перезарядка)

        # Башня ищет цель и стреляет
        target = tower.find_target(enemies)
        if target and tower.can_shoot():
            projectile = Projectile(tower.x, tower.y, target.x, target.y, tower.damage)
            projectiles.append(projectile)
            tower.shoot()

        # Обновляем снаряды
        for projectile in projectiles[:]:
            projectile.update()
            if projectile.is_out_of_bounds():
                projectiles.remove(projectile)

        # Проверяем попадания снарядов в врагов
        for projectile in projectiles[:]:
            for enemy in enemies[:]:
                distance = projectile.get_distance_to(enemy.x, enemy.y)
                if distance < enemy.radius + projectile.radius:
                    # Попадание!
                    enemy.hp -= projectile.damage
                    if projectile in projectiles:
                        projectiles.remove(projectile)
                    
                    # Враг умер
                    if enemy.hp <= 0:
                        enemies.remove(enemy)
                    break

        screen.fill(BLACK) # Чистим экран в черный цвет
        
        draw_enemies(screen, enemies)
        tower.draw(screen)
        
        # Рисуем снаряды
        for projectile in projectiles:
            projectile.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()