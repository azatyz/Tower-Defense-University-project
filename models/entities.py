from abc import ABC, abstractmethod

import pygame

from config.settings import (
    BLUE,
    GREEN,
    HEIGHT,
    MIN_TOWER_DISTANCE,
    ORANGE,
    RED,
    TOWER_PLACEMENT_RADIUS,
    WIDTH,
    YELLOW,
)


class GameObject(ABC):
    """Базовый класс игровых объектов"""

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, screen):
        pass


class Enemy(GameObject):
    """Класс для представления врага"""

    def __init__(self, path):
        self.path = path
        self.path_index = 0
        self.x, self.y = path.get_point_at_index(0)
        self.speed = 3
        self.hp = 100
        self.max_hp = self.hp
        self.reward = 50
        self.damage = 10
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

    def reached_end(self):
        return self.path_index >= self.path.get_total_points() - 1

    def get_distance_to(self, other_x, other_y):
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5

    def path_progress_score(self):
        return self.path_index + self.progress

    def draw(self, screen):
        self._draw_body(screen)
        self._draw_health_bar(screen)

    def _draw_body(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def _draw_health_bar(self, screen):
        bar_w = int(self.radius * 2)
        bar_h = 6
        ratio = 0.0 if self.max_hp <= 0 else max(0.0, min(1.0, self.hp / self.max_hp))

        bar_x = int(self.x - bar_w // 2)
        bar_y = int(self.y - self.radius - 12)

        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
        fill_color = RED if ratio < 0.35 else GREEN
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, int(bar_w * ratio), bar_h))


class TargetStrategy(ABC):
    """Абстрактная стратегия выбора цели для башни"""

    @abstractmethod
    def select(self, enemies, tower):
        pass

    def _targets_in_range(self, enemies, tower):
        return [
            enemy
            for enemy in enemies
            if enemy.get_distance_to(tower.x, tower.y) <= tower.radar_range
        ]


class NearestTargetStrategy(TargetStrategy):
    """Выбирает ближайшего врага"""

    def select(self, enemies, tower):
        targets = self._targets_in_range(enemies, tower)
        if not targets:
            return None
        return min(targets, key=lambda enemy: enemy.get_distance_to(tower.x, tower.y))


class StrongestTargetStrategy(TargetStrategy):
    """Выбирает самого живучего врага в радиусе"""

    def select(self, enemies, tower):
        targets = self._targets_in_range(enemies, tower)
        if not targets:
            return None
        return max(targets, key=lambda enemy: (enemy.hp, enemy.path_progress_score()))


class FirstInPathTargetStrategy(TargetStrategy):
    """Выбирает врага, который дальше всех прошёл по маршруту"""

    def select(self, enemies, tower):
        targets = self._targets_in_range(enemies, tower)
        if not targets:
            return None
        return max(targets, key=lambda enemy: enemy.path_progress_score())


class Tower(GameObject):
    """Базовый класс башни с раздельной прокачкой и захватом цели"""

    cost = 0
    kind_name = "Tower"
    color = GREEN
    range = 150
    damage = 25
    cooldown_max = 30
    splash_radius = 0
    target_strategy = NearestTargetStrategy()
    max_level = 3

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cooldown = 0
        self.width = 40 
        self.height = 40 
        
        self.damage_level = 1
        self.radar_level = 1
        
        self.shoot_range = self.range
        self.radar_range = int(self.range * 1.25)
        
        self.current_target = None

    def contains_point(self, pos):
        px, py = pos
        return (
            self.x - self.width // 2 <= px <= self.x + self.width // 2
            and self.y - self.height // 2 <= py <= self.y + self.height // 2
        )

    def can_upgrade_damage(self):
        return self.damage_level < self.max_level

    def get_damage_upgrade_cost(self):
        if not self.can_upgrade_damage(): return None
        return int(self.cost * (0.5 + self.damage_level * 0.3))

    def upgrade_damage(self):
        if self.can_upgrade_damage():
            self.damage_level += 1
            self.damage = int(self.damage * 1.35)
            if self.splash_radius > 0:
                self.splash_radius = int(self.splash_radius * 1.15)
            return True
        return False

    def can_upgrade_radar(self):
        return self.radar_level < self.max_level

    def get_radar_upgrade_cost(self):
        if not self.can_upgrade_radar(): return None
        return int(self.cost * (0.4 + self.radar_level * 0.3))

    def upgrade_radar(self):
        if self.can_upgrade_radar():
            self.radar_level += 1
            self.shoot_range = int(self.shoot_range * 1.15)
            self.radar_range = int(self.radar_range * 1.15)
            self.cooldown_max = max(8, int(self.cooldown_max * 0.95))
            return True
        return False

    def find_target(self, enemies):
        if self.current_target in enemies:
            dist = self.current_target.get_distance_to(self.x, self.y)
            if dist <= self.radar_range:
                return self.current_target
        
        self.current_target = self.target_strategy.select(enemies, self)
        return self.current_target

    def can_shoot(self):
        if self.cooldown > 0 or not self.current_target:
            return False
        dist = self.current_target.get_distance_to(self.x, self.y)
        return dist <= self.shoot_range

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def shoot(self):
        if self.can_shoot():
            self.cooldown = self.cooldown_max

    def draw(self, screen):
        base_rect = (
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height,
        )
        pygame.draw.rect(screen, (40, 40, 40), base_rect, border_radius=8)
        pygame.draw.rect(screen, self.color, base_rect, 3, border_radius=8)
        pygame.draw.circle(screen, self.color, (self.x, self.y), 10)

        if not self.current_target:
            return

        dist = self.current_target.get_distance_to(self.x, self.y)
        if dist > self.radar_range:
            return

        laser_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        start_pos = (self.x, self.y)
        end_pos = (int(self.current_target.x), int(self.current_target.y))
        pygame.draw.line(laser_surf, (*self.color, 90), start_pos, end_pos, 2)
        if dist <= self.shoot_range:
            pygame.draw.circle(laser_surf, RED, end_pos, 4)
        screen.blit(laser_surf, (0, 0))


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
    target_strategy = StrongestTargetStrategy()


class FastTower(Tower):
    cost = 160
    kind_name = "Fast"
    color = YELLOW
    range = 130
    damage = 15
    cooldown_max = 15


class BombTower(Tower):
    cost = 230
    kind_name = "Bomb"
    color = ORANGE
    range = 180
    damage = 45
    cooldown_max = 80
    splash_radius = 70
    target_strategy = FirstInPathTargetStrategy()


class Projectile(GameObject):
    """Класс для представления снаряда"""

    def __init__(self, start_x, start_y, target, damage, splash_radius=0, color=YELLOW):
        self.x = start_x
        self.y = start_y
        self.target = target
        self.damage = damage
        self.splash_radius = splash_radius
        self.color = color
        self.speed = 10
        self.radius = 5
        
        #Упреждающее прицеливание
        
        # 1. Считаем сколько времени понадобится пуле чтобы долететь до текущей позиции врага
        dist_to_target = ((target.x - start_x) ** 2 + (target.y - start_y) ** 2) ** 0.5
        time_to_reach = dist_to_target / self.speed
        
        # 2. Узнаем вектор скорости врага
        current_point = target.path.get_point_at_index(target.path_index)
        next_point = target.path.get_point_at_index(target.path_index + 1)
        
        seg_dx = next_point[0] - current_point[0]
        seg_dy = next_point[1] - current_point[1]
        seg_dist = (seg_dx ** 2 + seg_dy ** 2) ** 0.5
        
        if seg_dist > 0:
            enemy_vx = (seg_dx / seg_dist) * target.speed
            enemy_vy = (seg_dy / seg_dist) * target.speed
        else:
            enemy_vx, enemy_vy = 0, 0
            
        # 3. Вычисляем точку в будущем, где окажется враг через время time_to_reach
        future_x = target.x + enemy_vx * time_to_reach
        future_y = target.y + enemy_vy * time_to_reach
        
        # 4. Направляем пулю ровно в эту будущую точку
        proj_dx = future_x - start_x
        proj_dy = future_y - start_y
        proj_dist = (proj_dx ** 2 + proj_dy ** 2) ** 0.5
        
        if proj_dist > 0:
            self.vx = (proj_dx / proj_dist) * self.speed
            self.vy = (proj_dy / proj_dist) * self.speed
        else:
            self.vx, self.vy = 0, 0

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def is_done(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

    def get_distance_to(self, other_x, other_y):
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        if self.splash_radius > 0:
            pygame.draw.circle(
                screen,
                self.color,
                (int(self.x), int(self.y)),
                self.radius + 3,
                1,
            )

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


class BossEnemy(Enemy):
    """Юбилейный Босс"""
    def __init__(self, path, current_wave):
        super().__init__(path)
        
        # Вычисляем множитель босса
        multiplier = max(1, current_wave // 10)
        
        # Базовые 500 ХП умножаются на 1.5 с каждым юбилеем
        self.max_hp = int(500 * (1.5 ** (multiplier - 1)))
        self.hp = self.max_hp
        
        self.speed = 0.5 
        self.radius = 25
        
        self.reward = 150 * multiplier
        
        self.damage = 25

    def _draw_body(self, screen):
        pygame.draw.circle(screen, (138, 43, 226), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius + 2, 3)


