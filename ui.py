import pygame

from settings import (
    BLACK,
    HEIGHT,
    ORANGE,
    PREVIEW_BAD,
    PREVIEW_OK,
    RED,
    TOWER_PLACEMENT_RADIUS,
    WHITE,
    WIDTH,
    YELLOW,
)
from entities import BasicTower, BombTower, FastTower, SniperTower, can_place_tower


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
        if tower_preview.splash_radius > 0:
            pygame.draw.circle(screen, ORANGE, (mx, my), tower_preview.splash_radius, 1)

        if not can_afford:
            hint = f"Нужно {cost}$, есть {money}"
        elif not ok_place:
            hint = reason
        else:
            hint = "ЛКМ — построить"

        hint_surf = self.font.render(hint, True, WHITE if valid else RED)
        screen.blit(hint_surf, (mx + 15, my - 60))

    def draw_toolbar(self, screen, selected_class):
        panel_height = 60
        panel_rect = pygame.Rect(0, HEIGHT - panel_height, WIDTH, panel_height)
        pygame.draw.rect(screen, (20, 20, 20), panel_rect)
        pygame.draw.line(screen, (80, 80, 80), (0, HEIGHT - panel_height), (WIDTH, HEIGHT - panel_height), 2)

        options = [
            (BasicTower, "[1] Basic 120$"),
            (SniperTower, "[2] Sniper 200$"),
            (FastTower, "[3] Fast 160$"),
            (BombTower, "[4] Bomb 230$ AoE"),
        ]
        
        segment_width = WIDTH // len(options)
        
        for index, (tower_cls, line) in enumerate(options):
            color = YELLOW if selected_class is tower_cls else WHITE
            text_surf = self.font.render(line, True, color)
            
            center_x = (index * segment_width) + (segment_width // 2)
            center_y = HEIGHT - (panel_height // 2)
            text_rect = text_surf.get_rect(center=(center_x, center_y))
            
            screen.blit(text_surf, text_rect)


class WaveUI:
    """Интерфейс для запуска следующей волны и отображения прогресса."""

    def __init__(self, font):
        self.font = font
        self.button_rect = pygame.Rect(0, 0, 240, 40)

    def draw(self, screen, manager, enemies):
        if manager.game_over:
            return

        status = ""
        if manager.wave_active:
            left = len(enemies) + manager.enemies_in_wave - manager.spawned_this_wave
            status = f"Волна {manager.wave} — осталось врагов: {left}"
            text_color = WHITE
        else:
            status = f"Нажми E или кнопку, чтобы начать волну {manager.wave + 1}"
            text_color = YELLOW

        status_surf = self.font.render(status, True, text_color)
        screen.blit(status_surf, (WIDTH - status_surf.get_width() - 20, 18))

        self.button_rect = pygame.Rect(WIDTH - 260, 60, 240, 40)
        pygame.draw.rect(screen, WHITE, self.button_rect, border_radius=8)
        button_text = (
            "Start wave" if not manager.wave_active else "Wave in progress"
        )
        button_surf = self.font.render(button_text, True, BLACK if not manager.wave_active else (120, 120, 120))
        screen.blit(button_surf, button_surf.get_rect(center=self.button_rect.center))

    def handle_click(self, pos, manager):
        if self.button_rect.collidepoint(pos) and not manager.wave_active:
            return "next_wave"
        return None


class TowerInfoPanel:
    """Панель выбранной башни и кнопка улучшения."""

    def __init__(self, font):
        self.font = font
        self.upgrade_rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, screen, tower, money):
        if tower is None:
            self.upgrade_rect = pygame.Rect(0, 0, 0, 0)
            return

        panel_rect = pygame.Rect(WIDTH - 300, HEIGHT - 225, 280, 165)
        pygame.draw.rect(screen, (25, 25, 25), panel_rect, border_radius=8)
        pygame.draw.rect(screen, tower.color, panel_rect, 2, border_radius=8)

        lines = [
            f"{tower.kind_name} Tower | LVL {tower.level}/{tower.max_level}",
            f"Урон: {tower.damage}",
            f"Радиус: {tower.range}",
            f"Перезарядка: {tower.cooldown_max}",
        ]
        if tower.splash_radius > 0:
            lines.append(f"Взрыв: {tower.splash_radius}")

        for index, line in enumerate(lines):
            color = YELLOW if index == 0 else WHITE
            screen.blit(self.font.render(line, True, color), (panel_rect.x + 14, panel_rect.y + 12 + index * 24))

        self.upgrade_rect = pygame.Rect(panel_rect.x + 14, panel_rect.bottom - 48, panel_rect.width - 28, 34)
        can_upgrade = tower.can_upgrade()
        cost = tower.get_upgrade_cost()
        can_afford = cost is not None and money >= cost
        button_color = WHITE if can_upgrade and can_afford else (90, 90, 90)
        pygame.draw.rect(screen, button_color, self.upgrade_rect, border_radius=6)

        if can_upgrade:
            label = f"Upgrade: {cost}$  (U)"
        else:
            label = "Max level"
        text_color = BLACK if can_upgrade and can_afford else WHITE
        label_surf = self.font.render(label, True, text_color)
        screen.blit(label_surf, label_surf.get_rect(center=self.upgrade_rect.center))

    def handle_click(self, pos):
        if self.upgrade_rect.collidepoint(pos):
            return "upgrade"
        return None


class PauseMenu:
    """Меню паузы с кнопками Resume, Restart, Quit."""

    def __init__(self, font, title_font):
        self.font = font
        self.title_font = title_font
        self.buttons = {}

    def draw(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.title_font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120))
        screen.blit(title, title_rect)

        options = [
            ("Resume", "Esc", (WIDTH // 2, HEIGHT // 2 - 20)),
            ("Restart", "R", (WIDTH // 2, HEIGHT // 2 + 50)),
            ("Quit", "Q", (WIDTH // 2, HEIGHT // 2 + 120)),
        ]
        self.buttons = {}

        for text, key_text, center in options:
            rect = pygame.Rect(0, 0, 260, 40)
            rect.center = center
            pygame.draw.rect(screen, WHITE, rect, border_radius=8)
            pygame.draw.rect(screen, BLACK, rect.inflate(-6, -6), border_radius=8)
            label = self.font.render(f"{text} ({key_text})", True, WHITE)
            screen.blit(label, label.get_rect(center=rect.center))
            self.buttons[text.lower()] = rect

        hint = self.font.render("Click button or press Esc to resume", True, WHITE)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 190))
        screen.blit(hint, hint_rect)
