import pygame
import sys
import random
from settings import *


class Path:
    """Класс для управления тропинкой"""
    def __init__(self, points):
        self.points = points
        self.path_width = 60  # Ширина тропинки
        self.path_color = (80, 80, 80)  # Цвет дорожки
        
    def draw(self, screen):
        """Нарисовать тропинку на экране"""
        if len(self.points) > 1:
            # Рисуем линию между каждыми двумя точками
            for i in range(len(self.points) - 1):
                start = (int(self.points[i][0]), int(self.points[i][1]))
                end = (int(self.points[i + 1][0]), int(self.points[i + 1][1]))
                pygame.draw.line(screen, self.path_color, start, end, self.path_width)
            
            for point in self.points:
                pygame.draw.circle(screen, self.path_color, 
                                 (int(point[0]), int(point[1])), 
                                 self.path_width // 2)
            
    def get_point_at_index(self, index):
        """Получить точку пути по индексу"""
        if 0 <= index < len(self.points):
            return self.points[index]
        return self.points[-1]  # Последняя точка - конец пути
    
    def get_total_points(self):
        """Получить количество точек на пути"""
        return len(self.points)


def create_default_path():
    """Создать стандартный лабиринт-путь"""
    return Path([
        (50, 200),      
        (300, 200),     
        (300, 450),    
        (600, 450),   
        (600, 100),     
        (900, 100),     
        (900, 600),     
        (1200, 600),    
        (1200, 300),   
        (1350, 300),])

class GameManager:
    """Класс для управления состоянием игры (волны, деньги, статистика)"""
    def __init__(self):
        self.money = 200
        self.kills = 0
        self.wave = 1
        self.wave_timer = 0
        self.wave_cooldown = 120  # Кадры между волнами
        self.enemies_in_wave = 3
        self.spawned_this_wave = 0
        self.game_over = False
        self.max_kills_per_wave = 0

    def update(self):
        """Обновить состояние игры"""
        self.wave_timer += 1

    def is_wave_ready(self):
        """Проверить, пора ли начинать новую волну"""
        return self.wave_timer >= self.wave_cooldown and self.spawned_this_wave >= self.enemies_in_wave

    def next_wave(self):
        """Перейти на следующую волну"""
        self.wave += 1
        self.enemies_in_wave = 3 + self.wave  # Больше врагов с каждой волной
        self.max_kills_per_wave = self.kills  # Сохраняем максимум убитых
        self.wave_timer = 0
        self.spawned_this_wave = 0
        print(f"⚔️ Волна {self.wave}! Врагов: {self.enemies_in_wave}")

    def spawn_enemy_this_wave(self):
        """Отметить спавн врага в текущей волне"""
        self.spawned_this_wave += 1

    def add_money(self, amount):
        """Добавить деньги за убитого врага"""
        self.money += amount
        self.kills += 1

    def calculate_wave_efficiency(self):
        """Вычислить эффективность волны"""
        if self.enemies_in_wave == 0:
            return 0.0

        killed_this_wave = self.kills - self.max_kills_per_wave
        efficiency = (killed_this_wave / self.enemies_in_wave) * 100
        return efficiency

    def is_game_over(self, base_health):
        """Проверить, проиграл ли игрок"""
        if base_health <= 0:
            self.game_over = True
            return True
        return False

    def get_info_text(self):
        """Получить информацию для отображения на экране"""
        return f"Волна: {self.wave} | Деньги: {self.money} | Убито: {self.kills}"


class Enemy:
    """Класс для представления врага"""
    def __init__(self, path):
        self.path = path
        self.path_index = 0  # Индекс текущей точки пути
        self.x, self.y = path.get_point_at_index(0)  # Начальная позиция
        self.speed = random.randint(2, 4)
        self.hp = 100
        self.radius = 15
        self.progress = 0  # Прогресс между текущей и следующей точкой (0-1)

    def update(self):
        """Обновить позицию врага вдоль пути"""
        if self.path_index < self.path.get_total_points() - 1:
            current_point = self.path.get_point_at_index(self.path_index)
            next_point = self.path.get_point_at_index(self.path_index + 1)
            
            # Вычисляем расстояние между точками
            dx = next_point[0] - current_point[0]
            dy = next_point[1] - current_point[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if distance > 0:
                # Движемся по пути
                self.progress += self.speed / distance
                
                if self.progress >= 1.0:
                    # Переходим на следующую точку пути
                    self.path_index += 1
                    self.progress = 0
                else:
                    # Интерполируем позицию между двумя точками
                    self.x = current_point[0] + dx * self.progress
                    self.y = current_point[1] + dy * self.progress

    def draw(self, screen):
        pygame.draw.circle(screen, (200, 0, 0), (int(self.x), int(self.y)), self.radius)

    def is_out_of_bounds(self):
        """Враг достиг конца пути"""
        return self.path_index >= self.path.get_total_points() - 1

    def get_distance_to(self, other_x, other_y):
        """Вычислить расстояние до точки"""
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5


class Tower:
    """Класс для представления башни"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 150  # Радиус обстрела 
        self.damage = 25
        self.cooldown = 0  # Текущая перезарядка
        self.cooldown_max = 30  # Максимальная перезарядка
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
    
    for enemy in out_of_bounds:
        enemies.remove(enemy)


def game_loop():
    """ Главный игровой цикл """
    global base_health
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower Defense Project")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    font_large = pygame.font.Font(None, 72)

    # Создаём тропинку
    path = create_default_path()
    
    enemies = []
    projectiles = []
    tower = Tower(WIDTH - 60, HEIGHT // 2)
    game_manager = GameManager()
    
    running = True
    auto_spawn = True 
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Пробел - ручной спавн врага (для тестирования)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    enemies.append(Enemy(path))
                # E - начать новую волну вручную
                if event.key == pygame.K_e:
                    game_manager.next_wave()
                # R - перезагрузить игру
                if event.key == pygame.K_r and game_manager.game_over:
                    pygame.quit()
                    return game_loop()
                # Q - выход из игры
                if event.key == pygame.K_q and game_manager.game_over:
                    running = False

        game_manager.update()


        if game_manager.is_game_over(base_health):
            pass

  
        if not game_manager.game_over:
            if auto_spawn and game_manager.spawned_this_wave < game_manager.enemies_in_wave:
                if game_manager.wave_timer % 30 == 0:  # Спавн каждые 0.5 сек
                    enemies.append(Enemy(path))
                    game_manager.spawn_enemy_this_wave()

            if auto_spawn and game_manager.is_wave_ready():
                game_manager.next_wave()

            move_enemies(enemies)
            check_collisions(enemies)
            tower.update()

  
            target = tower.find_target(enemies)
            if target and tower.can_shoot():
                projectile = Projectile(tower.x, tower.y, target.x, target.y, tower.damage)
                projectiles.append(projectile)
                tower.shoot()


            for projectile in projectiles[:]:
                projectile.update()
                if projectile.is_out_of_bounds():
                    projectiles.remove(projectile)


            for projectile in projectiles[:]:
                for enemy in enemies[:]:
                    distance = projectile.get_distance_to(enemy.x, enemy.y)
                    if distance < enemy.radius + projectile.radius:
                        enemy.hp -= projectile.damage
                        if projectile in projectiles:
                            projectiles.remove(projectile)
                        
                        if enemy.hp <= 0:
                            enemies.remove(enemy)
                            game_manager.add_money(50) 

        screen.fill(BLACK)
        
        # Рисуем тропинку
        path.draw(screen)
        
        draw_enemies(screen, enemies)
        tower.draw(screen)
        

        for projectile in projectiles:
            projectile.draw(screen)
        

        info_text = game_manager.get_info_text()
        text_surface = font.render(info_text, True, WHITE)
        screen.blit(text_surface, (10, 10))
        

        hp_text = f"HP: {base_health}/100"
        hp_surface = font.render(hp_text, True, RED if base_health < 30 else WHITE)
        screen.blit(hp_surface, (10, 40))
        

        if game_manager.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            game_over_text = font_large.render("GAME OVER", True, RED)
            text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(game_over_text, text_rect)
            
            stats_text = f"Волны: {game_manager.wave} | Убито: {game_manager.kills} | Деньги: {game_manager.money}"
            stats_surface = font.render(stats_text, True, WHITE)
            stats_rect = stats_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(stats_surface, stats_rect)
            
            restart_text = font.render("Нажми R для перезагрузки или Q для выхода", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
            screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()