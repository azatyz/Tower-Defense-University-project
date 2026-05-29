import pygame

from settings import (
    BLACK,
    HEIGHT,
    PREVIEW_BAD,
    PREVIEW_OK,
    RED,
    TOWER_PLACEMENT_RADIUS,
    WHITE,
    WIDTH,
)
from entities import BasicTower, SniperTower, can_place_tower


class MessageHUD:
    """Всплывающие сообщения на экране."""

    def __init__(self, font):
        self.font = font
        self.text = ""
        self.timer = 0
        self.color = WHITE

    def show(self, text, color=WHITE, duration=150):
        self.text = text
        self.color = color
        self.timer = duration

    def update(self):
        if self.timer > 0:
            self.timer -= 1

    def draw(self, screen):
        if self.timer <= 0 or not self.text:
            return
        surface = self.font.render(self.text, True, self.color)
        rect = surface.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        pygame.draw.rect(screen, (30, 30, 30), rect.inflate(20, 10))
        screen.blit(surface, rect)


class BuildUI:
    """Превью башни под курсором и панель выбора типа."""

    def __init__(self, font):
        self.font = font
        self.selected_class = None

    def set_tower_type(self, tower_class):
        self.selected_class = tower_class

    def draw_preview(self, screen, mouse_pos, path, towers, money, game_over):
        if game_over or self.selected_class is None:
            return

        mx, my = mouse_pos
        cost = self.selected_class(0, 0).cost
        ok_place, reason = can_place_tower(mx, my, path, towers)
        can_afford = money >= cost
        valid = ok_place and can_afford

        color = PREVIEW_OK if valid else PREVIEW_BAD
        surf = pygame.Surface((TOWER_PLACEMENT_RADIUS * 2, TOWER_PLACEMENT_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            surf,
            color,
            (TOWER_PLACEMENT_RADIUS, TOWER_PLACEMENT_RADIUS),
            TOWER_PLACEMENT_RADIUS,
        )
        screen.blit(surf, (mx - TOWER_PLACEMENT_RADIUS, my - TOWER_PLACEMENT_RADIUS))

        tower_preview = self.selected_class(mx, my)
        pygame.draw.rect(
            screen,
            tower_preview.color,
            (mx - 25, my - 50, 50, 100),
            2,
        )
        pygame.draw.circle(screen, tower_preview.color, (mx, my), tower_preview.range, 1)

        if not can_afford:
            hint = f"Нужно {cost}$, есть {money}"
        elif not ok_place:
            hint = reason
        else:
            hint = "ЛКМ — построить"

        hint_surf = self.font.render(hint, True, WHITE if valid else RED)
        screen.blit(hint_surf, (mx + 15, my - 60))

    def draw_toolbar(self, screen, selected_class):
        y = HEIGHT - 35
        options = [
            (BasicTower, "[1] Basic (120$) — быстрая"),
            (SniperTower, "[2] Sniper (200$) — дальний бой"),
        ]
        for index, (tower_cls, line) in enumerate(options):
            x = 10 + index * 320
            color = (255, 255, 100) if selected_class is tower_cls else WHITE
            screen.blit(self.font.render(line, True, color), (x, y))
