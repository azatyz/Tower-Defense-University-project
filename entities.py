import random
from abc import ABC, abstractmethod

import pygame

from settings import GREEN, RED, WIDTH, HEIGHT, YELLOW


class GameObject(ABC):
    """Базовый класс игровых объектов (полиморфизм: общие update/draw)."""

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, screen):
        pass


class Enemy(GameObject):
    """Класс для представления врага."""

    def __init__(self, path):
        self.path = path
        self.path_index = 0
        self.x, self.y = path.get_point_at_index(0)
        self.speed = random.randint(2, 4)
        self.hp = 100
        self.max_hp = self.hp
        self.radius = 15
        self.progress = 0

    def update(self):
        if self.path_index >= self.path.get_total_points() - 1:
            return
        current_point = self.path.get_point_at_index(self.path_index)
        next_point = self.path.get_point_at_index(self.path_index + 1)
        dx = next_point[0] - current_point[0]
        dy = next_point[1] - current_point[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance <= 0:
            return
        self.progress += self.speed / distance
        if self.progress >= 1.0:
            self.path_index += 1
            self.progress = 0
        else:
            self.x = current_point[0] + dx * self.progress
            self.y = current_point[1] + dy * self.progress

    def draw(self, screen):
        pygame.draw.circle(screen, (200, 0, 0), (int(self.x), int(self.y)), self.radius)
        bar_w = 36
        bar_h = 6
        ratio = 0.0 if self.max_hp <= 0 else max(0.0, min(1.0, self.hp / self.max_hp))
        bar_x = int(self.x - bar_w // 2)
        bar_y = int(self.y - self.radius - 12)
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
        fill_color = RED if ratio < 0.35 else GREEN
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, int(bar_w * ratio), bar_h))

    def is_out_of_bounds(self):
        return self.path_index >= self.path.get_total_points() - 1

    def get_distance_to(self, other_x, other_y):
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5


class Tower(GameObject):
    """Класс для представления башни."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 150
        self.damage = 25
        self.cooldown = 0
        self.cooldown_max = 30
        self.width = 50
        self.height = 100

    def can_shoot(self):
        return self.cooldown <= 0

    def find_target(self, enemies):
        targets = []
        for enemy in enemies:
            distance = enemy.get_distance_to(self.x, self.y)
            if distance <= self.radius:
                targets.append((distance, enemy))
        if targets:
            return min(targets, key=lambda t: t[0])[1]
        return None

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def shoot(self):
        if self.can_shoot():
            self.cooldown = self.cooldown_max

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            GREEN,
            (self.x - self.width // 2, self.y - self.height // 2, self.width, self.height),
        )
        pygame.draw.circle(screen, (0, 200, 0), (self.x, self.y), self.radius, 1)


class Projectile(GameObject):
    """Класс для представления снаряда."""

    def __init__(self, start_x, start_y, target_x, target_y, damage):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.damage = damage
        self.speed = 8
        self.radius = 5
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
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)

    def is_out_of_bounds(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

    def get_distance_to(self, other_x, other_y):
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5
