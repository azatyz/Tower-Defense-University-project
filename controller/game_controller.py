from dataclasses import dataclass, field
import sys

import pygame

from config.save_manager import load_highscore, save_highscore
from config.settings import FPS, GREEN, HEIGHT, RED, WIDTH, YELLOW
from controller import game_logic
from models.entities import BasicTower, BombTower, FastTower, SniperTower
from models.game_manager import GameManager
from models.path import create_default_path
from view.audio import SoundManager
from view.renderer import GameRenderer
from view.ui import BuildUI, MessageHUD, PauseMenu, TowerInfoPanel, WaveUI, draw_game_ui

WINDOW_TITLE = "Tower Defense - Игра"
DEFAULT_FONT_SIZE = 28
TITLE_FONT_SIZE = 72
RESTART_DELAY_MS = 100
QUIT_DELAY_MS = 200
PAUSE_ACTION_DELAY_MS = 150

TOWER_TYPES = {
    pygame.K_1: BasicTower,
    pygame.K_2: SniperTower,
    pygame.K_3: FastTower,
    pygame.K_4: BombTower,
}

MESSAGE_COLORS = {
    "success": GREEN,
    "warning": YELLOW,
    "error": RED,
}


@dataclass
class GameState:
    path: object = field(default_factory=create_default_path)
    manager: GameManager = field(default_factory=GameManager)
    enemies: list = field(default_factory=list)
    towers: list = field(default_factory=list)
    projectiles: list = field(default_factory=list)
    paused: bool = False
    selected_tower: object = None
    show_radius: bool = True
    highscore: int = field(default_factory=load_highscore)


def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    renderer = GameRenderer(screen)
    sound_manager = SoundManager()
    font = pygame.font.Font(None, DEFAULT_FONT_SIZE)
    font_large = pygame.font.Font(None, TITLE_FONT_SIZE)

    while True:
        state = GameState()
        ui = _create_ui(font, font_large)
        action = _run_session(screen, clock, renderer, sound_manager, font, font_large, state, ui)
        if action != "restart":
            break

    pygame.quit()
    sys.exit()


def _create_ui(font, font_large):
    return {
        "build": BuildUI(font),
        "wave": WaveUI(font),
        "info": TowerInfoPanel(font),
        "pause": PauseMenu(font, font_large),
        "message": MessageHUD(font_large),
    }


def _run_session(screen, clock, renderer, sound_manager, font, font_large, state, ui):
    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            action = _handle_event(event, mouse_pos, state, ui, sound_manager)
            if action == "quit":
                return "quit"
            if action == "restart":
                return "restart"

        if not state.paused and not state.manager.game_over:
            events = game_logic.update_game(
                state.manager,
                state.path,
                state.enemies,
                state.towers,
                state.projectiles,
            )
            _show_logic_events(events, ui["message"])
            ui["message"].update()
            if state.manager.game_over:
                state.highscore = max(state.highscore, state.manager.wave)

        draw_game_ui(
            screen,
            renderer,
            ui["build"],
            ui["wave"],
            ui["info"],
            ui["pause"],
            ui["message"],
            font,
            font_large,
            state,
            mouse_pos,
        )
        clock.tick(FPS)


def _handle_event(event, mouse_pos, state, ui, sound_manager):
    if event.type == pygame.QUIT:
        return _finish_session("quit", state)

    if event.type == pygame.KEYDOWN:
        action = _handle_keydown(event.key, state, ui, sound_manager)
        if action:
            return action

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        sound_manager.play("click")
        ui["build"].set_tower_type(None)
        state.selected_tower = None
        return None

    is_mouse_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
    is_space_click = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
    if is_mouse_click or is_space_click:
        return _handle_primary_action(mouse_pos, state, ui, sound_manager, is_mouse_click)

    return None


def _handle_keydown(key, state, ui, sound_manager):
    if key == pygame.K_ESCAPE:
        sound_manager.play("click")
        state.paused = not state.paused
        return None

    if key == pygame.K_t:
        sound_manager.play("click")
        state.show_radius = not state.show_radius

    if state.paused:
        if key == pygame.K_r:
            sound_manager.play("click")
            pygame.time.delay(RESTART_DELAY_MS)
            return _finish_session("restart", state)
        elif key == pygame.K_q:
            sound_manager.play("click")
            pygame.time.delay(QUIT_DELAY_MS)
            return _finish_session("quit", state)
        return None

    if state.manager.game_over:
        return None

    if key in TOWER_TYPES:
        sound_manager.play("click")
        ui["build"].set_tower_type(TOWER_TYPES[key])
        state.selected_tower = None
    elif key == pygame.K_u:
        _handle_damage_upgrade(state, ui["message"], sound_manager)
    elif key == pygame.K_f:
        _handle_radar_upgrade(state, ui["message"], sound_manager)
    elif key == pygame.K_s:
        _handle_sell(state, ui["message"], sound_manager)
    elif key == pygame.K_e:
        _handle_wave_start(state.manager, ui["message"], sound_manager)

    return None


def _handle_primary_action(mouse_pos, state, ui, sound_manager, is_mouse_click):
    if state.paused:
        action = ui["pause"].handle_click(mouse_pos)
        if action:
            sound_manager.play("click")
            if action in ("restart", "quit"):
                pygame.time.delay(PAUSE_ACTION_DELAY_MS)
        if action == "resume":
            state.paused = False
        elif action == "restart":
            return _finish_session("restart", state)
        elif action == "quit":
            return _finish_session("quit", state)
        elif action == "toggle_radius":
            state.show_radius = not state.show_radius
        return None

    if state.manager.game_over:
        return None

    if ui["wave"].handle_click(mouse_pos, state.manager) == "next_wave":
        _handle_wave_start(state.manager, ui["message"], sound_manager)
        return None

    if _handle_info_panel_action(mouse_pos, state, ui["info"], ui["message"], sound_manager):
        return None

    clicked_tower = game_logic.find_clicked_tower(state.towers, mouse_pos)
    if clicked_tower is not None:
        sound_manager.play("click")
        state.selected_tower = clicked_tower
        ui["build"].set_tower_type(None)
        return None

    if is_mouse_click and ui["build"].handle_click(mouse_pos):
        sound_manager.play("click")
        return None

    if ui["build"].selected_class:
        if _handle_build(state, ui["build"], mouse_pos, ui["message"], sound_manager):
            state.selected_tower = None

    return None


def _handle_info_panel_action(mouse_pos, state, info_panel, message_hud, sound_manager):
    action = info_panel.handle_click(mouse_pos)
    if action == "sell":
        _handle_sell(state, message_hud, sound_manager)
        return True
    if action == "upgrade_damage":
        _handle_damage_upgrade(state, message_hud, sound_manager)
        return True
    if action == "upgrade_radar":
        _handle_radar_upgrade(state, message_hud, sound_manager)
        return True
    return False


def _handle_damage_upgrade(state, message_hud, sound_manager):
    upgraded, message = game_logic.try_upgrade_tower_damage(state.manager, state.selected_tower)
    _show_action_feedback(message_hud, sound_manager, upgraded, message, "upgrade")


def _handle_radar_upgrade(state, message_hud, sound_manager):
    upgraded, message = game_logic.try_upgrade_tower_radar(state.manager, state.selected_tower)
    _show_action_feedback(message_hud, sound_manager, upgraded, message, "upgrade")


def _handle_sell(state, message_hud, sound_manager):
    sold, message = game_logic.sell_tower(state.manager, state.towers, state.selected_tower)
    if sold:
        state.selected_tower = None
    _show_action_feedback(message_hud, sound_manager, sold, message, "upgrade", success_color=YELLOW)


def _handle_wave_start(manager, message_hud, sound_manager):
    started, message = game_logic.try_start_next_wave(manager)
    _show_action_feedback(message_hud, sound_manager, started, message, "click")


def _handle_build(state, build_ui, mouse_pos, message_hud, sound_manager):
    built, message = game_logic.try_build_tower(
        state.manager,
        build_ui.selected_class,
        mouse_pos,
        state.path,
        state.towers,
    )
    _show_action_feedback(message_hud, sound_manager, built, message, "build")
    return built


def _show_action_feedback(message_hud, sound_manager, success, message, success_sound, success_color=GREEN):
    if success:
        sound_manager.play(success_sound)
        message_hud.show(message, success_color)
        return

    sound_manager.play("error")
    message_hud.show(message, RED)


def _show_logic_events(events, message_hud):
    for event in events:
        message_hud.show(event["message"], MESSAGE_COLORS[event["kind"]])


def _finish_session(action, state):
    _persist_highscore(state)
    return action


def _persist_highscore(state):
    save_highscore(state.manager.wave)
    state.highscore = max(state.highscore, state.manager.wave)
