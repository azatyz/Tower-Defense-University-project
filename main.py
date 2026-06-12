import pygame
import sys
import json
import os

from settings import *
from path import create_default_path
from game_manager import GameManager
from entities import TOWER_TYPES, can_place_tower, create_enemy_for_wave, Projectile
from ui import BuildUI, WaveUI, TowerInfoPanel, PauseMenu, MessageHUD

def load_highscore():
    """Загрузка максимальной пройденную волны из файла."""
    if os.path.exists("save.json"):
        try:
            with open("save.json", "r") as f:
                return json.load(f).get("max_wave", 0)
        except:
            return 0
    return 0

def save_highscore(wave):
    """Сохранение рекорда, если он побит."""
    current_max = load_highscore()
    if wave > current_max:
        with open("save.json", "w") as f:
            json.dump({"max_wave": wave}, f)

def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower Defense Project")
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 28)
    font_large = pygame.font.Font(None, 72)

    # Инициализация объектов из твоей архитектуры
    path = create_default_path()
    manager = GameManager()
    
    enemies = []
    towers = []
    projectiles = []

    # Инициализация UI
    build_ui = BuildUI(font)
    wave_ui = WaveUI(font)
    info_panel = TowerInfoPanel(font)
    pause_menu = PauseMenu(font_large)
    msg_hud = MessageHUD(font_large)

    paused = False
    selected_tower = None  # Уже построенная башня, которую мы выбрали для апгрейда
    highscore = load_highscore()

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Пауза
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                
                if not paused and not manager.game_over:
                    # Выбор башни для постройки
                    if event.key in TOWER_TYPES:
                        build_ui.set_tower_type(TOWER_TYPES[event.key])
                        selected_tower = None
                    # Апгрейд (горячая клавиша)
                    if event.key == pygame.K_u and selected_tower:
                        cost = selected_tower.get_upgrade_cost()
                        if cost and manager.money >= cost:
                            manager.money -= cost
                            selected_tower.upgrade()
                            msg_hud.show("Башня улучшена!", GREEN)
                    # Следующая волна (горячая клавиша)
                    if event.key == pygame.K_e and not manager.wave_active:
                        manager.next_wave()

                # Управление после проигрыша
                if manager.game_over:
                    if event.key == pygame.K_r:
                        return game_loop() # Рестарт
                    if event.key == pygame.K_q:
                        running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if paused:
                    action = pause_menu.handle_click(mouse_pos)
                    if action == "resume": paused = False
                    elif action == "restart": return game_loop()
                    elif action == "quit": running = False
                    continue

                if manager.game_over:
                    continue

                # Проверка кликов по UI
                if wave_ui.handle_click(mouse_pos, manager) == "next_wave":
                    manager.next_wave()
                    continue
                if info_panel.handle_click(mouse_pos) == "upgrade" and selected_tower:
                    cost = selected_tower.get_upgrade_cost()
                    if cost and manager.money >= cost:
                        manager.money -= cost
                        selected_tower.upgrade()
                        msg_hud.show("Успешный апгрейд!", GREEN)
                    continue

                # Клик по построенной башне (выбор)
                clicked_on_tower = False
                for t in towers:
                    if t.contains_point(mouse_pos):
                        selected_tower = t
                        build_ui.set_tower_type(None) # Сбрасываем режим стройки
                        clicked_on_tower = True
                        break
                
                # Постройка новой башни
                if not clicked_on_tower and build_ui.selected_class:
                    ok, reason = can_place_tower(mouse_pos[0], mouse_pos[1], path, towers)
                    cost = build_ui.selected_class(0,0).cost
                    if ok and manager.money >= cost:
                        towers.append(build_ui.selected_class(mouse_pos[0], mouse_pos[1]))
                        manager.money -= cost
                        selected_tower = None
                    elif not ok:
                        msg_hud.show(reason, RED)
                    else:
                        msg_hud.show("Недостаточно денег!", RED)

        # --- ОБНОВЛЕНИЕ ЛОГИКИ ---
        if not paused and not manager.game_over:
            manager.update()

            # Спавн врагов
            if manager.wave_active and manager.spawned_this_wave < manager.enemies_in_wave:
                if manager.wave_timer % 40 == 0:
                    enemies.append(create_enemy_for_wave(path, manager.wave))
                    manager.register_spawn()

            # Конец волны
            if manager.wave_active and manager.spawned_this_wave >= manager.enemies_in_wave and not enemies:
                manager.wave_active = False
                manager.money += 100 + manager.wave * 20 # Бонус за волну

            # Обновление врагов
            for enemy in enemies[:]:
                enemy.update()
                if enemy.reached_end():
                    manager.damage_base(10)
                    enemies.remove(enemy)
                    if manager.game_over:
                        save_highscore(manager.wave)

            # Обновление башен и стрельба
            for tower in towers:
                tower.update()
                target = tower.find_target(enemies)
                if target and tower.can_shoot():
                    proj = Projectile(tower.x, tower.y, target, tower.damage, tower.splash_radius, tower.color)
                    projectiles.append(proj)
                    tower.shoot()

            # Обновление снарядов и попадания
            for proj in projectiles[:]:
                proj.update()
                if proj.is_done():
                    projectiles.remove(proj)
                    continue
                
                # Попадание
                if proj.target in enemies:
                    dist = proj.get_distance_to(proj.target.x, proj.target.y)
                    if dist < proj.target.radius + proj.radius:
                        # Урон по площади или одиночный
                        if proj.splash_radius > 0:
                            for e in enemies:
                                if e.get_distance_to(proj.x, proj.y) <= proj.splash_radius:
                                    e.hp -= proj.damage
                        else:
                            proj.target.hp -= proj.damage

                        if proj in projectiles:
                            projectiles.remove(proj)

            # Проверка мертвых врагов
            for enemy in enemies[:]:
                if enemy.hp <= 0:
                    manager.add_kill_reward(enemy.reward)
                    enemies.remove(enemy)

            msg_hud.update()

        # --- ОТРИСОВКА ---
        # Фоновый цвет
        screen.fill((30, 40, 30)) 

        path.draw(screen)
        
        # Радиус выбранной башни (для наглядности)
        if selected_tower:
            pygame.draw.circle(screen, (255, 255, 255, 50), (selected_tower.x, selected_tower.y), selected_tower.range, 1)

        for tower in towers:
            tower.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for proj in projectiles:
            proj.draw(screen)

        # Отрисовка UI
        build_ui.draw_preview(screen, mouse_pos, path, towers, manager.money, manager.game_over)
        build_ui.draw_toolbar(screen, build_ui.selected_class)
        wave_ui.draw(screen, manager, enemies)
        info_panel.draw(screen, selected_tower, manager.money)
        msg_hud.draw(screen)

        # Текст HUD
        screen.blit(font.render(f"HP Базы: {manager.base_health}", True, RED if manager.base_health < 30 else GREEN), (10, 10))
        screen.blit(font.render(manager.get_hud_line(), True, WHITE), (10, 40))
        screen.blit(font.render(f"Рекорд: {highscore} волн", True, (200, 200, 200)), (10, 70))

        if paused and not manager.game_over:
            pause_menu.draw(screen)

        if manager.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            screen.blit(font_large.render("GAME OVER", True, RED), (WIDTH // 2 - 150, HEIGHT // 2 - 100))
            screen.blit(font.render(f"Вы дошли до {manager.wave} волны!", True, WHITE), (WIDTH // 2 - 120, HEIGHT // 2))
            screen.blit(font.render("Нажми [R] для рестарта или [Q] для выхода", True, YELLOW), (WIDTH // 2 - 180, HEIGHT // 2 + 50))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()