import pygame
from config.settings import WIDTH, HEIGHT

class GameRenderer:
    """Отрисовка игры"""
    
    def __init__(self, screen):
        self.screen = screen

    def draw_frame(self, path, towers, enemies, projectiles):
        """Отрисовка кадра"""
        self.screen.fill((30, 40, 30))

        path.draw(self.screen)
        for tower in towers:
            tower.draw(self.screen)
        for enemy in enemies:
            enemy.draw(self.screen)
        for proj in projectiles:
            proj.draw(self.screen)

    def draw_tower_radius(self, tower):
        """Отрисовка полупрозрачных зон видимости для выбранной башни"""
        pygame.draw.circle(self.screen, tower.color, (tower.x, tower.y), tower.shoot_range, 2)
        radar_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(radar_surf, (*tower.color, 50), (tower.x, tower.y), tower.radar_range, 1)
        pygame.draw.circle(radar_surf, (*tower.color, 10), (tower.x, tower.y), tower.radar_range, 0)
        self.screen.blit(radar_surf, (0, 0))
