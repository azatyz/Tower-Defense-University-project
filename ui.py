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
    """Всплывающие сообщения на экране"""

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
        
        rect = surface.get_rect(center=(WIDTH // 2, HEIGHT - 110))
        
        padding_x, padding_y = 30, 15
        bg_surf = pygame.Surface((rect.width + padding_x * 2, rect.height + padding_y * 2), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 180), bg_surf.get_rect(), border_radius=12)
        
        screen.blit(bg_surf, (rect.x - padding_x, rect.y - padding_y))
        screen.blit(surface, rect)

class BuildUI:
    """Превью башни под курсором и панель выбора типа"""

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

        preview_rect = (mx - 20, my - 20, 40, 40)
        pygame.draw.rect(screen, (40, 40, 40), preview_rect, border_radius=8)
        pygame.draw.rect(screen, tower_preview.color, preview_rect, 3, border_radius=8)
        pygame.draw.circle(screen, tower_preview.color, (mx, my), 10)
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
    """Интерфейс для запуска следующей волны и отображения прогресса"""

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
    """Панель выбранной башни с раздельной прокачкой"""

    def __init__(self, font):
        self.font = font
        self.upg_dmg_rect = pygame.Rect(0, 0, 0, 0)
        self.upg_rad_rect = pygame.Rect(0, 0, 0, 0)
        self.sell_rect = pygame.Rect(0, 0, 0, 0) 

    def draw(self, screen, tower, money):
        if tower is None:
            self.upg_dmg_rect = pygame.Rect(0, 0, 0, 0)
            self.upg_rad_rect = pygame.Rect(0, 0, 0, 0)
            self.sell_rect = pygame.Rect(0, 0, 0, 0)
            return

        panel_rect = pygame.Rect(20, HEIGHT - 310, 280, 240)
        pygame.draw.rect(screen, (25, 25, 25), panel_rect, border_radius=8)
        pygame.draw.rect(screen, tower.color, panel_rect, 2, border_radius=8)

        dmg_lvl = tower.damage_level
        rad_lvl = tower.radar_level
        radar_range = tower.radar_range
        shoot_range = tower.shoot_range
        
        lines = [
            f"{tower.kind_name} Tower",
            f"Урон (LVL {dmg_lvl}): {tower.damage}",
            f"Радар (LVL {rad_lvl}): {radar_range}",
            f"Орудие: {shoot_range}",
            f"Перезарядка: {tower.cooldown_max}",
        ]
        if tower.splash_radius > 0:
            lines.append(f"Взрыв: {tower.splash_radius}")

        for index, line in enumerate(lines):
            color = YELLOW if index == 0 else WHITE
            screen.blit(self.font.render(line, True, color), (panel_rect.x + 14, panel_rect.y + 12 + index * 22))

        self.upg_dmg_rect = pygame.Rect(panel_rect.x + 14, panel_rect.bottom - 118, panel_rect.width - 28, 30)
        self.upg_rad_rect = pygame.Rect(panel_rect.x + 14, panel_rect.bottom - 80, panel_rect.width - 28, 30)
        self.sell_rect = pygame.Rect(panel_rect.x + 14, panel_rect.bottom - 42, panel_rect.width - 28, 30)

        cost_dmg = tower.get_damage_upgrade_cost()
        cost_rad = tower.get_radar_upgrade_cost()
        
        can_upg_dmg = tower.can_upgrade_damage()
        can_upg_rad = tower.can_upgrade_radar()

        # 1. Отрисовка кнопки урона [U]
        color_dmg = WHITE if can_upg_dmg and cost_dmg and money >= cost_dmg else (90, 90, 90)
        pygame.draw.rect(screen, color_dmg, self.upg_dmg_rect, border_radius=6)
        label_dmg = f"Урон: {cost_dmg}$ (U)" if can_upg_dmg else "Урон: MAX"
        text_col_dmg = BLACK if color_dmg == WHITE else WHITE
        surf_dmg = self.font.render(label_dmg, True, text_col_dmg)
        screen.blit(surf_dmg, surf_dmg.get_rect(center=self.upg_dmg_rect.center))

        # 2. Отрисовка кнопки радара [F]
        color_rad = WHITE if can_upg_rad and cost_rad and money >= cost_rad else (90, 90, 90)
        pygame.draw.rect(screen, color_rad, self.upg_rad_rect, border_radius=6)
        label_rad = f"Радар: {cost_rad}$ (F)" if can_upg_rad else "Радар: MAX"
        text_col_rad = BLACK if color_rad == WHITE else WHITE
        surf_rad = self.font.render(label_rad, True, text_col_rad)
        screen.blit(surf_rad, surf_rad.get_rect(center=self.upg_rad_rect.center))

        # 3. Отрисовка кнопки продажи [S]
        sell_price = tower.cost // 2
        pygame.draw.rect(screen, (180, 50, 50), self.sell_rect, border_radius=6)
        label_sell = f"Продать: {sell_price}$ (S)"
        surf_sell = self.font.render(label_sell, True, WHITE)
        screen.blit(surf_sell, surf_sell.get_rect(center=self.sell_rect.center))

    def handle_click(self, pos):
        if self.upg_dmg_rect.collidepoint(pos):
            return "upgrade_damage"
        if self.upg_rad_rect.collidepoint(pos):
            return "upgrade_radar"
        if self.sell_rect.collidepoint(pos):
            return "sell"
        return None

class PauseMenu:
    """Меню паузы"""

    def __init__(self, font, title_font):
        self.font = font
        self.title_font = title_font
        self.buttons = {}

    def draw(self, screen, show_radius=True):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.title_font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120))
        screen.blit(title, title_rect)

        radius_text = "Радиус: ВКЛ" if show_radius else "Радиус: ВЫКЛ"
        
        options = [
            ("Продолжить", "Esc", (WIDTH // 2, HEIGHT // 2 - 40), "resume"),
            (radius_text, "T", (WIDTH // 2, HEIGHT // 2 + 30), "toggle_radius"),
            ("Рестарт", "R", (WIDTH // 2, HEIGHT // 2 + 100), "restart"),
            ("Выход", "Q", (WIDTH // 2, HEIGHT // 2 + 170), "quit"),
        ]
        self.buttons = {}

        for text, key_text, center, action in options:
            rect = pygame.Rect(0, 0, 320, 40)
            rect.center = center
            pygame.draw.rect(screen, WHITE, rect, border_radius=8)
            pygame.draw.rect(screen, BLACK, rect.inflate(-6, -6), border_radius=8)
            label = self.font.render(f"{text} ({key_text})", True, WHITE)
            screen.blit(label, label.get_rect(center=rect.center))
            self.buttons[action] = rect 

        hint = self.font.render("Нажми кнопку на экране или клавиатуре", True, WHITE)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 240))
        screen.blit(hint, hint_rect)

    def handle_click(self, pos):
        for action, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return action
        return None
