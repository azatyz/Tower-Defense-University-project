import random
from abc import ABC, abstractmethod

import pygame

from settings import (
    BLUE,
    GREEN,
    MIN_TOWER_DISTANCE,
    RED,
    TOWER_PLACEMENT_RADIUS,
    YELLOW,
    WIDTH,
    HEIGHT,
)


class GameObject(ABC):
    """Базовый класс игровых объектов."""

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
        self.speed = 3
        self.hp = 100
        self.max_hp = self.hp
        self.reward = 50
        self.radius = 15
        self.color = RED
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
            self.x, self.y = self.path.get_point_at_index(self.path_index)
        else:
            self.x = current_point[0] + dx * self.progress
            self.y = current_point[1] + dy * self.progress

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        bar_w = 36
        bar_h = 6
        ratio = 0.0 if self.max_hp <= 0 else max(0.0, min(1.0, self.hp / self.max_hp))
        bar_x = int(self.x - bar_w // 2)
        bar_y = int(self.y - self.radius - 12)
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
        fill_color = RED if ratio < 0.35 else GREEN
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, int(bar_w * ratio), bar_h))

    def reached_end(self):
        return self.path_index >= self.path.get_total_points() - 1

    def get_distance_to(self, other_x, other_y):
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5


class Tower(GameObject):
    """Базовый класс башни."""

    cost = 0
    kind_name = "Tower"
    color = GREEN
    range = 150
    damage = 25
    cooldown_max = 30

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cooldown = 0
        self.width = 50
        self.height = 100

    def can_shoot(self):
        return self.cooldown <= 0

    def find_target(self, enemies):
        targets = []
        for enemy in enemies:
            distance = enemy.get_distance_to(self.x, self.y)
            if distance <= self.range:
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
            self.color,
            (self.x - self.width // 2, self.y - self.height // 2, self.width, self.height),
        )
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.range, 1)


class BasicTower(Tower):
    cost = 120
    kind_name = "Basic"
    color = GREEN
    range = 150
    damage = 20
    cooldown_max = 25


class SniperTower(Tower):
    cost = 200
    kind_name = "Sniper"
    color = BLUE
    range = 240
    damage = 50
    cooldown_max = 60


class FastTower(Tower):
    cost = 160
    kind_name = "Fast"
    color = YELLOW
    range = 130
    damage = 15
    cooldown_max = 15


class Projectile(GameObject):
    """Класс для представления снаряда."""

    def __init__(self, start_x, start_y, target, damage):
        self.x = start_x
        self.y = start_y
        self.target = target
        self.damage = damage
        self.speed = 10
        self.radius = 5
        self.vx = 0
        self.vy = 0
        self._update_velocity()

    def _update_velocity(self):
        if self.target is None:
            self.vx = 0
            self.vy = 0
            return
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance > 0:
            self.vx = (dx / distance) * self.speed
            self.vy = (dy / distance) * self.speed
        else:
            self.vx = 0
            self.vy = 0

    def update(self):
        if self.target is not None:
            self._update_velocity()
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)

    def is_done(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

    def get_distance_to(self, other_x, other_y):
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5


TOWER_TYPES = {
    pygame.K_1: BasicTower,
    pygame.K_2: SniperTower,
    pygame.K_3: FastTower,
}


def can_place_tower(x, y, path, towers):
    if path.is_position_on_path(x, y, TOWER_PLACEMENT_RADIUS):
        return False, "Нельзя строить на дороге"
    for tower in towers:
        dist = ((x - tower.x) ** 2 + (y - tower.y) ** 2) ** 0.5
        if dist < MIN_TOWER_DISTANCE:
            return False, "Слишком близко к башне"
    return True, ""


class FastEnemy(Enemy):
    def __init__(self, path):
        super().__init__(path)
        self.speed = 6
        self.hp = 70
        self.max_hp = self.hp
        self.reward = 40
        self.radius = 12
        self.color = YELLOW


class TankEnemy(Enemy):
    def __init__(self, path):
        super().__init__(path)
        self.speed = 2
        self.hp = 180
        self.max_hp = self.hp
        self.reward = 80
        self.radius = 20
        self.color = (180, 40, 40)


def create_enemy_for_wave(path, wave):
    if wave % 5 == 0:
        enemy = TankEnemy(path)
    elif random.random() < min(0.25 + wave * 0.02, 0.5):
        enemy = FastEnemy(path)
    else:
        enemy = Enemy(path)

    enemy.hp += wave * 5
    enemy.max_hp = enemy.hp
    enemy.speed += wave // 3
    enemy.reward += wave * 2
    return enemy

