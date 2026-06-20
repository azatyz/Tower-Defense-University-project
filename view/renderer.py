import pygame
from config.settings import WIDTH, HEIGHT, RED, GREEN

class GameRenderer:
    """Отрисовка игры"""
    
    def __init__(self, screen):
        self.screen = screen

    def draw_frame(self, path, towers, enemies, projectiles):
        """Отрисовка кадра"""
        # 1. Заливка фона
        self.screen.fill((30, 40, 30))
        
        # 2. Отрисовка слоев снизу вверх
        self.draw_path(path)
        for tower in towers:
            self.draw_tower(tower)
        for enemy in enemies:
            self.draw_enemy(enemy)
        for proj in projectiles:
            self.draw_projectile(proj)

    def draw_path(self, path):
        if len(path.points) < 2: return
        for i in range(len(path.points) - 1):
            start = (int(path.points[i][0]), int(path.points[i][1]))
            end = (int(path.points[i+1][0]), int(path.points[i+1][1]))
            pygame.draw.line(self.screen, path.path_color, start, end, path.path_width)
        for point in path.points:
            pygame.draw.circle(self.screen, path.path_color, (int(point[0]), int(point[1])), path.path_width // 2)

    def draw_enemy(self, enemy):
        pygame.draw.circle(self.screen, enemy.color, (int(enemy.x), int(enemy.y)), enemy.radius)
        bar_w = 36
        bar_h = 6
        ratio = 0.0 if enemy.max_hp <= 0 else max(0.0, min(1.0, enemy.hp / enemy.max_hp))
        bar_x = int(enemy.x - bar_w // 2)
        bar_y = int(enemy.y - enemy.radius - 12)
        pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
        fill_color = RED if ratio < 0.35 else GREEN
        pygame.draw.rect(self.screen, fill_color, (bar_x, bar_y, int(bar_w * ratio), bar_h))

    def draw_tower(self, tower):
        base_rect = (tower.x - tower.width // 2, tower.y - tower.height // 2, tower.width, tower.height)
        pygame.draw.rect(self.screen, (40, 40, 40), base_rect, border_radius=8)
        pygame.draw.rect(self.screen, tower.color, base_rect, 3, border_radius=8)
        pygame.draw.circle(self.screen, tower.color, (tower.x, tower.y), 10)
        
        # Лазер прицеливания
        if tower.current_target:
            dist = tower.current_target.get_distance_to(tower.x, tower.y)
            if dist <= tower.radar_range:
                laser_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                start_pos = (tower.x, tower.y) 
                end_pos = (int(tower.current_target.x), int(tower.current_target.y))
                pygame.draw.line(laser_surf, (*tower.color, 90), start_pos, end_pos, 2)
                if dist <= tower.shoot_range:
                    pygame.draw.circle(laser_surf, RED, end_pos, 4)
                self.screen.blit(laser_surf, (0, 0))

    def draw_projectile(self, proj):
        pygame.draw.circle(self.screen, proj.color, (int(proj.x), int(proj.y)), proj.radius)
        if proj.splash_radius > 0:
            pygame.draw.circle(self.screen, proj.color, (int(proj.x), int(proj.y)), proj.radius + 3, 1)

    def draw_tower_radius(self, tower):
        """Отрисовка полупрозрачных зон видимости для выбранной башни"""
        pygame.draw.circle(self.screen, tower.color, (tower.x, tower.y), tower.shoot_range, 2)
        radar_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(radar_surf, (*tower.color, 50), (tower.x, tower.y), tower.radar_range, 1)
        pygame.draw.circle(radar_surf, (*tower.color, 10), (tower.x, tower.y), tower.radar_range, 0)
        self.screen.blit(radar_surf, (0, 0))