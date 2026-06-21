import pygame
import sys

from config.save_manager import load_highscore, save_highscore
from config.settings import WIDTH, HEIGHT, FPS, GREEN, YELLOW, RED, WHITE, BLACK
from models.path import create_default_path
from models.entities import BossEnemy
from models.entities import can_place_tower, Projectile, BasicTower, SniperTower, FastTower, BombTower
from models.game_manager import GameManager
from view.ui import BuildUI, WaveUI, TowerInfoPanel, PauseMenu, MessageHUD
from view.renderer import GameRenderer
from view.audio import SoundManager

TOWER_TYPES = {
    pygame.K_1: BasicTower,
    pygame.K_2: SniperTower,
    pygame.K_3: FastTower,
    pygame.K_4: BombTower,
}


def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower Defense Project")
    renderer = GameRenderer(screen)
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 28)
    font_large = pygame.font.Font(None, 72)

    path = create_default_path()
    manager = GameManager()

    enemies = []
    towers = []
    projectiles = []

    # Инициализация UI
    build_ui = BuildUI(font)
    wave_ui = WaveUI(font)
    info_panel = TowerInfoPanel(font)
    pause_menu = PauseMenu(font, font_large)
    msg_hud = MessageHUD(font_large)
    sound_manager = SoundManager()

    paused = False
    selected_tower = None
    show_radius = True
    highscore = load_highscore()

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # 1. Обработка паузы
                if event.key == pygame.K_ESCAPE:
                    sound_manager.play("click")
                    paused = not paused
                if paused:
                    if event.key == pygame.K_t:
                        sound_manager.play("click")
                        show_radius = not show_radius
                    if event.key == pygame.K_r:
                        sound_manager.play("click")
                        pygame.time.delay(100)
                        return game_loop()
                    if event.key == pygame.K_q:
                        sound_manager.play("click")
                        pygame.time.delay(200)
                        running = False
                    continue

                # 2. Обработка горячих клавиш для строительства и управления башнями
                if not manager.game_over:
                    if event.key in TOWER_TYPES:
                        sound_manager.play("click")
                        build_ui.set_tower_type(TOWER_TYPES[event.key])
                        selected_tower = None
                    if event.key == pygame.K_u and selected_tower:
                        cost = selected_tower.get_damage_upgrade_cost()
                        if cost and manager.money >= cost:
                            manager.money -= cost
                            selected_tower.upgrade_damage()
                            sound_manager.play("upgrade")
                            msg_hud.show("Урон улучшен!", GREEN)
                        else:
                            sound_manager.play("error")
                    if event.key == pygame.K_f and selected_tower:
                        cost = selected_tower.get_radar_upgrade_cost()
                        if cost and manager.money >= cost:
                            manager.money -= cost
                            selected_tower.upgrade_radar()
                            sound_manager.play("upgrade")
                            msg_hud.show("Радар улучшен!", GREEN)
                    if event.key == pygame.K_s and selected_tower:
                        manager.money += selected_tower.cost // 2
                        towers.remove(selected_tower)
                        selected_tower = None
                        sound_manager.play("upgrade")
                        msg_hud.show("Башня продана!", YELLOW)
                    if event.key == pygame.K_e and not manager.wave_active:
                        sound_manager.play("click")
                        manager.next_wave()

                if manager.game_over:
                    if event.key == pygame.K_r:
                        sound_manager.play("click")
                        return game_loop()
                    if event.key == pygame.K_q:
                        sound_manager.play("click")
                        running = False

            # 3. Обработка кликов мышью
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                sound_manager.play("click")
                build_ui.set_tower_type(None)
                selected_tower = None
                continue

            is_mouse_click = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
            is_space_click = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)

            if is_mouse_click or is_space_click:
                if paused:
                    action = pause_menu.handle_click(mouse_pos)
                    if action:
                        sound_manager.play("click")
                        if action in ["restart", "quit"]:
                            pygame.time.delay(150)
                    if action == "resume":
                        paused = False
                    elif action == "restart":
                        return game_loop()
                    elif action == "quit":
                        running = False
                    elif action == "toggle_radius":
                        show_radius = not show_radius
                    continue

                if manager.game_over:
                    continue

                if wave_ui.handle_click(mouse_pos, manager) == "next_wave":
                    sound_manager.play("click")
                    manager.next_wave()
                    continue

                click_action = info_panel.handle_click(mouse_pos)
                if click_action == "sell" and selected_tower:
                    manager.money += selected_tower.cost // 2
                    towers.remove(selected_tower)
                    selected_tower = None
                    sound_manager.play("upgrade")
                    msg_hud.show("Башня продана!", YELLOW)
                    continue

                if click_action == "upgrade_damage" and selected_tower:
                    cost = selected_tower.get_damage_upgrade_cost()
                    if cost and manager.money >= cost:
                        manager.money -= cost
                        selected_tower.upgrade_damage()
                        sound_manager.play("upgrade")
                        msg_hud.show("Урон улучшен!", GREEN)
                    else:
                        sound_manager.play("error")
                    continue

                if click_action == "upgrade_radar" and selected_tower:
                    cost = selected_tower.get_radar_upgrade_cost()
                    if cost and manager.money >= cost:
                        manager.money -= cost
                        selected_tower.upgrade_radar()
                        sound_manager.play("upgrade")
                        msg_hud.show("Радар улучшен!", GREEN)
                    else:
                        sound_manager.play("error")
                    continue

                # Проверяем, кликнули ли мы по башне для выбора
                clicked_on_tower = False
                for t in towers:
                    if t.contains_point(mouse_pos):
                        sound_manager.play("click")
                        selected_tower = t
                        build_ui.set_tower_type(None)
                        clicked_on_tower = True
                        break

                # Проверяем, кликнули ли мы по интерфейсу
                clicked_on_ui = False
                if is_mouse_click:
                    clicked_on_ui = build_ui.handle_click(mouse_pos)
                    if clicked_on_ui:
                        sound_manager.play("click")

                # Постройка новой башни
                if not clicked_on_ui and not clicked_on_tower and build_ui.selected_class:
                    ok, reason = can_place_tower(mouse_pos[0], mouse_pos[1], path, towers)
                    cost = build_ui.selected_class(0, 0).cost
                    if ok and manager.money >= cost:
                        towers.append(build_ui.selected_class(mouse_pos[0], mouse_pos[1]))
                        manager.money -= cost
                        sound_manager.play("build")
                        selected_tower = None
                    elif not ok:
                        sound_manager.play("error")
                        msg_hud.show(reason, RED)
                    else:
                        sound_manager.play("error")
                        msg_hud.show("Недостаточно денег!", RED)

        # Обновление логики
        if not paused and not manager.game_over:
            manager.update()

            # Спавн врагов
            if manager.wave_active and manager.spawned_this_wave < manager.enemies_in_wave:
                if manager.wave_timer % 40 == 0:
                    # Достаем класс врага и номер волны из нашей сгенерированной очереди
                    enemy_class, wave_num = manager.current_wave_queue[manager.spawned_this_wave]

                    # Для Босса передаем номер волны, чтобы он мог масштабироваться, для остальных врагов просто путь
                    if enemy_class == BossEnemy:
                        new_enemy = BossEnemy(path, wave_num)
                    else:
                        new_enemy = enemy_class(path)

                    enemies.append(new_enemy)
                    manager.register_spawn()

            # Конец волны
            if manager.wave_active and manager.spawned_this_wave >= manager.enemies_in_wave and not enemies:
                manager.wave_active = False
                manager.money += 100 + manager.wave * 20 # Бонус за прохождение волны
                msg_hud.show(f"Волна {manager.wave} пройдена!", GREEN)

            # Обновление врагов и проверка достижения базы
            for enemy in enemies[:]:
                enemy.update()
                if enemy.reached_end():
                    manager.damage_base(10)
                    enemies.remove(enemy)
                    if manager.game_over:
                        save_highscore(manager.wave)

            # Обновление башен и стрельбы
            for tower in towers:
                tower.update()
                target = tower.find_target(enemies)
                if target and tower.can_shoot():
                    proj = Projectile(tower.x, tower.y, target, tower.damage, tower.splash_radius, tower.color)
                    projectiles.append(proj)
                    tower.shoot()

            # Обновление снарядов и попаданий
            for proj in projectiles[:]:
                proj.update()
                if proj.is_done():
                    projectiles.remove(proj)
                    continue

                # Попадание в цель
                if proj.target in enemies:
                    dist = proj.get_distance_to(proj.target.x, proj.target.y)
                    if dist < proj.target.radius + proj.radius:
                        # Урон по площади или одиночный урон
                        if proj.splash_radius > 0:
                            for e in enemies:
                                dist_to_explosion = e.get_distance_to(proj.x, proj.y)
                                if dist_to_explosion <= proj.splash_radius:
                                    falloff_factor = 1.0 - (dist_to_explosion / proj.splash_radius)
                                    actual_damage = max(1, int(proj.damage * falloff_factor))
                                    e.hp -= actual_damage
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

        # Отрисовка игрового мира
        if not paused and not manager.game_over:
            renderer.draw_frame(path, towers, enemies, projectiles)

            if selected_tower and show_radius:
                renderer.draw_tower_radius(selected_tower)

        # Отрисовка UI
        build_ui.draw_preview(screen, mouse_pos, path, towers, manager.money, manager.game_over)
        build_ui.draw_toolbar(screen)
        wave_ui.draw(screen, manager, enemies)
        info_panel.draw(screen, selected_tower, manager.money)
        msg_hud.draw(screen)

        # HUD
        hud_bg = pygame.Surface((350, 100))
        hud_bg.set_alpha(150)
        hud_bg.fill((0, 0, 0))
        screen.blit(hud_bg, (5, 5))

        if manager.base_health > 60:
            hp_color = GREEN
        elif manager.base_health > 30:
            hp_color = YELLOW
        else:
            hp_color = RED

        screen.blit(font.render(f"HP Базы: {manager.base_health}", True, hp_color), (15, 15))
        screen.blit(font.render(manager.get_hud_line(), True, WHITE), (15, 45))
        screen.blit(font.render(f"Рекорд: {highscore} Волн", True, (200, 200, 200)), (15, 75))

        if paused and not manager.game_over:
            pause_menu.draw(screen, show_radius)

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
