import pygame
from config.settings import (
    BLACK,
    GREEN,
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

from models.entities import BasicTower, SniperTower, FastTower, BombTower, can_place_tower

MESSAGE_HUD_Y_OFFSET = 110
MESSAGE_HUD_PADDING_X = 30
MESSAGE_HUD_PADDING_Y = 15
TOOLBAR_HEIGHT = 60
WAVE_BUTTON_WIDTH = 240
WAVE_BUTTON_HEIGHT = 40
WAVE_BUTTON_MARGIN = 20
INFO_PANEL_WIDTH = 280
INFO_PANEL_HEIGHT = 240
INFO_PANEL_BOTTOM_OFFSET = 310
HUD_WIDTH = 350
HUD_HEIGHT = 100
HUD_PADDING = 15
HUD_LINE_SPACING = 30
PAUSE_OVERLAY_ALPHA = 120
GAME_OVER_OVERLAY_ALPHA = 120
OVERLAY_PANEL_ALPHA = 185
PAUSE_TITLE_OFFSET_Y = 120
PAUSE_BUTTON_WIDTH = 460
PAUSE_BUTTON_HEIGHT = 64
PAUSE_BUTTON_START_OFFSET_Y = -40
PAUSE_BUTTON_STEP_Y = 70
PAUSE_HINT_OFFSET_Y = 240
GAME_OVER_PANEL_WIDTH = 540
GAME_OVER_PANEL_HEIGHT = 240
GAME_OVER_TITLE_OFFSET_Y = 70
GAME_OVER_SUBTITLE_OFFSET_Y = 10
GAME_OVER_HINT_OFFSET_Y = 70


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

        rect = surface.get_rect(center=(WIDTH // 2, HEIGHT - MESSAGE_HUD_Y_OFFSET))

        bg_surf = pygame.Surface(
            (
                rect.width + MESSAGE_HUD_PADDING_X * 2,
                rect.height + MESSAGE_HUD_PADDING_Y * 2,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(bg_surf, (0, 0, 0, 180), bg_surf.get_rect(), border_radius=12)

        screen.blit(
            bg_surf,
            (rect.x - MESSAGE_HUD_PADDING_X, rect.y - MESSAGE_HUD_PADDING_Y),
        )
        screen.blit(surface, rect)


class BuildUI:
    """Превью башни под курсором и панель выбора типа"""

    def __init__(self, font):
        self.font = font
        self.selected_class = None
        self.buttons = []

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

    def draw_toolbar(self, screen):
        self.buttons.clear()

        panel_rect = pygame.Rect(0, HEIGHT - TOOLBAR_HEIGHT, WIDTH, TOOLBAR_HEIGHT)
        pygame.draw.rect(screen, (20, 20, 20), panel_rect)
        pygame.draw.line(
            screen,
            (80, 80, 80),
            (0, HEIGHT - TOOLBAR_HEIGHT),
            (WIDTH, HEIGHT - TOOLBAR_HEIGHT),
            2,
        )

        options = [
            (BasicTower, "[1] Базовая - 120$"),
            (SniperTower, "[2] Снайпер - 200$"),
            (FastTower, "[3] Быстрая - 160$"),
            (BombTower, "[4] Бомба - 230$"),
        ]

        segment_width = WIDTH // len(options)
        mouse_pos = pygame.mouse.get_pos()

        for index, (tower_cls, line) in enumerate(options):
            button_rect = pygame.Rect(
                index * segment_width,
                HEIGHT - TOOLBAR_HEIGHT,
                segment_width,
                TOOLBAR_HEIGHT,
            )
            self.buttons.append((button_rect, tower_cls))

            if self.selected_class is tower_cls:
                pygame.draw.rect(screen, (60, 60, 60), button_rect)
            elif button_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (40, 40, 40), button_rect)

            if index > 0:
                pygame.draw.line(
                    screen,
                    (50, 50, 50),
                    (index * segment_width, HEIGHT - TOOLBAR_HEIGHT),
                    (index * segment_width, HEIGHT),
                )

            color = YELLOW if self.selected_class is tower_cls else WHITE
            text_surf = self.font.render(line, True, color)

            center_x = (index * segment_width) + (segment_width // 2)
            center_y = HEIGHT - (TOOLBAR_HEIGHT // 2)
            text_rect = text_surf.get_rect(center=(center_x, center_y))

            screen.blit(text_surf, text_rect)

    def handle_click(self, mouse_pos):
        """Проверяет, кликнули ли мы в какую-то из кнопок на тулбаре"""
        for rect, tower_class in self.buttons:
            if rect.collidepoint(mouse_pos):
                self.selected_class = tower_class
                return True
        return False


class WaveUI:
    """Интерфейс для запуска следующей волны и отображения прогресса"""

    def __init__(self, font):
        self.font = font
        self.button_rect = pygame.Rect(0, 0, WAVE_BUTTON_WIDTH, WAVE_BUTTON_HEIGHT)

    def draw(self, screen, manager, enemies):
        if manager.game_over:
            return

        if manager.wave_active:
            left = len(enemies) + manager.enemies_in_wave - manager.spawned_this_wave
            status = f"Волна {manager.wave} — осталось врагов: {left}"
            text_color = WHITE
        else:
            status = f"Нажми E или кнопку, чтобы начать волну {manager.wave + 1}"
            text_color = YELLOW

        status_surf = self.font.render(status, True, text_color)
        screen.blit(status_surf, (WIDTH - status_surf.get_width() - 20, 18))

        self.button_rect = pygame.Rect(
            WIDTH - WAVE_BUTTON_WIDTH - WAVE_BUTTON_MARGIN,
            60,
            WAVE_BUTTON_WIDTH,
            WAVE_BUTTON_HEIGHT,
        )
        pygame.draw.rect(screen, WHITE, self.button_rect, border_radius=8)
        button_text = "Начать волну" if not manager.wave_active else "Волна идет"
        button_surf = self.font.render(
            button_text,
            True,
            BLACK if not manager.wave_active else (120, 120, 120),
        )
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

        panel_rect = pygame.Rect(
            20,
            HEIGHT - INFO_PANEL_BOTTOM_OFFSET,
            INFO_PANEL_WIDTH,
            INFO_PANEL_HEIGHT,
        )
        pygame.draw.rect(screen, (25, 25, 25), panel_rect, border_radius=8)
        pygame.draw.rect(screen, tower.color, panel_rect, 2, border_radius=8)

        dmg_lvl = tower.damage_level
        rad_lvl = tower.radar_level
        radar_range = tower.radar_range
        shoot_range = tower.shoot_range

        lines = [
            f"Башня: {tower.kind_name}",
            f"Урон [{dmg_lvl}/{tower.max_level}]: {tower.damage}",
            f"Радар [{rad_lvl}/{tower.max_level}]: {radar_range}",
            f"Дальность атаки: {shoot_range}",
            f"Перезарядка: {tower.cooldown_max}",
        ]
        if tower.splash_radius > 0:
            lines.append(f"Радиус взрыва: {tower.splash_radius}")

        for index, line in enumerate(lines):
            color = YELLOW if index == 0 else WHITE
            screen.blit(
                self.font.render(line, True, color),
                (panel_rect.x + 14, panel_rect.y + 12 + index * 22),
            )

        self.upg_dmg_rect = pygame.Rect(panel_rect.x + 14, panel_rect.bottom - 118, panel_rect.width - 28, 30)
        self.upg_rad_rect = pygame.Rect(panel_rect.x + 14, panel_rect.bottom - 80, panel_rect.width - 28, 30)
        self.sell_rect = pygame.Rect(panel_rect.x + 14, panel_rect.bottom - 42, panel_rect.width - 28, 30)

        cost_dmg = tower.get_damage_upgrade_cost()
        cost_rad = tower.get_radar_upgrade_cost()

        can_upg_dmg = tower.can_upgrade_damage()
        can_upg_rad = tower.can_upgrade_radar()

        color_dmg = WHITE if can_upg_dmg and cost_dmg and money >= cost_dmg else (90, 90, 90)
        pygame.draw.rect(screen, color_dmg, self.upg_dmg_rect, border_radius=6)
        label_dmg = f"Улучшить урон: {cost_dmg}$ [U]" if can_upg_dmg else "Урон: максимум"
        text_col_dmg = BLACK if color_dmg == WHITE else WHITE
        surf_dmg = self.font.render(label_dmg, True, text_col_dmg)
        screen.blit(surf_dmg, surf_dmg.get_rect(center=self.upg_dmg_rect.center))

        color_rad = WHITE if can_upg_rad and cost_rad and money >= cost_rad else (90, 90, 90)
        pygame.draw.rect(screen, color_rad, self.upg_rad_rect, border_radius=6)
        label_rad = f"Улучшить радар: {cost_rad}$ [F]" if can_upg_rad else "Радар: максимум"
        text_col_rad = BLACK if color_rad == WHITE else WHITE
        surf_rad = self.font.render(label_rad, True, text_col_rad)
        screen.blit(surf_rad, surf_rad.get_rect(center=self.upg_rad_rect.center))

        sell_price = tower.cost // 2
        pygame.draw.rect(screen, (180, 50, 50), self.sell_rect, border_radius=6)
        label_sell = f"Продать за {sell_price}$ [S]"
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
        _draw_overlay(screen, PAUSE_OVERLAY_ALPHA)

        title = self.title_font.render("ПАУЗА", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - PAUSE_TITLE_OFFSET_Y))
        screen.blit(title, title_rect)

        options = [
            ("Продолжить", "Esc", (WIDTH // 2, HEIGHT // 2 + PAUSE_BUTTON_START_OFFSET_Y), "resume"),
            (
                "Показать радиус" if not show_radius else "Скрыть радиус",
                "T",
                (WIDTH // 2, HEIGHT // 2 + PAUSE_BUTTON_START_OFFSET_Y + PAUSE_BUTTON_STEP_Y),
                "toggle_radius",
            ),
            ("Рестарт", "R", (WIDTH // 2, HEIGHT // 2 + PAUSE_BUTTON_START_OFFSET_Y + PAUSE_BUTTON_STEP_Y * 2), "restart"),
            ("Выход", "Q", (WIDTH // 2, HEIGHT // 2 + PAUSE_BUTTON_START_OFFSET_Y + PAUSE_BUTTON_STEP_Y * 3), "quit"),
        ]
        self.buttons = {}

        for text, key_text, center, action in options:
            rect = pygame.Rect(0, 0, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT)
            rect.center = center
            _draw_overlay_panel(screen, rect, WHITE)
            label = self.font.render(f"{text} ({key_text})", True, WHITE)
            screen.blit(label, label.get_rect(center=rect.center))
            self.buttons[action] = rect

        hint = self.font.render("Нажмите кнопку мышью или клавишу на клавиатуре", True, WHITE)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + PAUSE_HINT_OFFSET_Y))
        screen.blit(hint, hint_rect)

    def handle_click(self, pos):
        for action, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return action
        return None


def draw_game_ui(
    screen,
    renderer,
    build_ui,
    wave_ui,
    info_panel,
    pause_menu,
    message_hud,
    font,
    font_large,
    state,
    mouse_pos,
):
    renderer.draw_frame(state.path, state.towers, state.enemies, state.projectiles)
    if state.selected_tower and state.show_radius and not state.manager.game_over:
        renderer.draw_tower_radius(state.selected_tower)

    if not state.paused:
        build_ui.draw_preview(
            screen,
            mouse_pos,
            state.path,
            state.towers,
            state.manager.money,
            state.manager.game_over,
        )
    build_ui.draw_toolbar(screen)
    wave_ui.draw(screen, state.manager, state.enemies)
    info_panel.draw(screen, state.selected_tower, state.manager.money)
    message_hud.draw(screen)
    _draw_hud(screen, font, state)

    if state.paused:
        pause_menu.draw(screen, state.show_radius)
    elif state.manager.game_over:
        _draw_game_over(screen, font, font_large, state)

    pygame.display.flip()


def _draw_hud(screen, font, state):
    hud_bg = pygame.Surface((HUD_WIDTH, HUD_HEIGHT))
    hud_bg.set_alpha(150)
    hud_bg.fill((0, 0, 0))
    screen.blit(hud_bg, (5, 5))

    if state.manager.base_health > 60:
        hp_color = GREEN
    elif state.manager.base_health > 30:
        hp_color = YELLOW
    else:
        hp_color = RED

    screen.blit(font.render(f"Здоровье базы: {state.manager.base_health}", True, hp_color), (HUD_PADDING, HUD_PADDING))
    screen.blit(font.render(state.manager.get_hud_line(), True, WHITE), (HUD_PADDING, HUD_PADDING + HUD_LINE_SPACING))
    screen.blit(
        font.render(f"Рекорд: {state.highscore} волн", True, (200, 200, 200)),
        (HUD_PADDING, HUD_PADDING + HUD_LINE_SPACING * 2),
    )


def _draw_game_over(screen, font, font_large, state):
    _draw_overlay(screen, GAME_OVER_OVERLAY_ALPHA)

    panel_rect = pygame.Rect(0, 0, GAME_OVER_PANEL_WIDTH, GAME_OVER_PANEL_HEIGHT)
    panel_rect.center = (WIDTH // 2, HEIGHT // 2)
    _draw_overlay_panel(screen, panel_rect, (90, 90, 90))

    title = font_large.render("ПОРАЖЕНИЕ", True, RED)
    subtitle = font.render(f"Вы дошли до {state.manager.wave} волны!", True, WHITE)
    hint = font.render("Нажми [Esc], чтобы открыть меню действий", True, YELLOW)

    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - GAME_OVER_TITLE_OFFSET_Y)))
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 + GAME_OVER_SUBTITLE_OFFSET_Y)))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + GAME_OVER_HINT_OFFSET_Y)))


def _draw_overlay(screen, alpha):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    screen.blit(overlay, (0, 0))


def _draw_overlay_panel(screen, rect, border_color):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, OVERLAY_PANEL_ALPHA), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, border_color, panel.get_rect(), width=2, border_radius=16)
    screen.blit(panel, rect.topleft)
