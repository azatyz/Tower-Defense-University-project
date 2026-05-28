import pygame
import sys

from entities import Enemy, Projectile, Tower
from game_manager import GameManager
from path import create_default_path
from settings import *


class MessageHUD:
    """Сообщения игроку на экране (без print — совместимо с Windows)."""

    def __init__(self, font):
        self.font = font
        self.text = ""
        self.timer = 0
        self.color = WHITE

    def show(self, text, color=WHITE, duration=120):
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


def can_place_tower(x, y, path, towers):
    if path.is_position_on_path(x, y, TOWER_PLACEMENT_RADIUS):
        return False, "Нельзя строить на дороге"
    for tower in towers:
        dist = ((x - tower.x) ** 2 + (y - tower.y) ** 2) ** 0.5
        if dist < MIN_TOWER_DISTANCE:
            return False, "Слишком близко к башне"
    return True, ""


def move_enemies(enemies):
    for enemy in enemies:
        enemy.update()


def draw_enemies(screen, enemies):
    for enemy in enemies:
        enemy.draw(screen)


def check_collisions(enemies, game_manager):
    leaked = False
    out_of_bounds = []
    for enemy in enemies:
        if enemy.is_out_of_bounds():
            game_manager.damage_base(10)
            leaked = True
            out_of_bounds.append(enemy)
    for enemy in out_of_bounds:
        enemies.remove(enemy)
    return leaked


def game_loop():
    """ Главный игровой цикл """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower Defense Project")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22)
    font_large = pygame.font.SysFont("arial", 72)
    hud = MessageHUD(font)

    path = create_default_path()

    enemies = []
    projectiles = []
    towers = []
    game_manager = GameManager()

    def restart_game():
        """Полный перезапуск без выхода из pygame."""
        nonlocal game_manager
        enemies.clear()
        projectiles.clear()
        towers.clear()
        game_manager = GameManager()
        hud.show("Новая игра! ЛКМ — башня (150$), вне серой дороги.", (200, 220, 100), 200)

    hud.show("ЛКМ — поставить башню (150$). Кликай вне серой дороги.", (200, 220, 100), 200)

    running = True
    auto_spawn = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    enemies.append(Enemy(path))
                if event.key == pygame.K_e:
                    game_manager.next_wave()
                if event.key == pygame.K_r and game_manager.game_over:
                    restart_game()
                if event.key == pygame.K_q and game_manager.game_over:
                    running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not game_manager.game_over:
                    mx, my = event.pos
                    if game_manager.money < TOWER_COST:
                        hud.show(f"Мало денег! Нужно {TOWER_COST}$", RED)
                    else:
                        ok, reason = can_place_tower(mx, my, path, towers)
                        if ok:
                            towers.append(Tower(mx, my))
                            game_manager.money -= TOWER_COST
                            hud.show("Башня построена!", (100, 255, 100))
                        else:
                            hud.show(reason, RED)

        game_manager.update()
        hud.update()

        if not game_manager.game_over:
            if auto_spawn and game_manager.spawned_this_wave < game_manager.enemies_in_wave:
                if game_manager.wave_timer % 30 == 0:
                    enemies.append(Enemy(path))
                    game_manager.spawn_enemy_this_wave()

            if auto_spawn and game_manager.is_wave_ready():
                game_manager.next_wave()
                hud.show(f"Волна {game_manager.wave}!", WHITE, 90)

            move_enemies(enemies)
            leaked = check_collisions(enemies, game_manager)
            if leaked:
                hud.show(f"База -10 HP! Осталось {game_manager.base_health}", RED, 90)

            for tower in towers:
                tower.update()
                target = tower.find_target(enemies)
                if target and tower.can_shoot():
                    projectiles.append(
                        Projectile(tower.x, tower.y, target.x, target.y, tower.damage)
                    )
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
                            game_manager.add_money(KILL_REWARD)

        screen.fill(BLACK)
        path.draw(screen)
        draw_enemies(screen, enemies)
        for tower in towers:
            tower.draw(screen)
        for projectile in projectiles:
            projectile.draw(screen)

        info_text = game_manager.get_info_text()
        text_surface = font.render(info_text, True, WHITE)
        screen.blit(text_surface, (10, 10))

        hp_text = f"HP базы: {game_manager.base_health}/{BASE_HEALTH_MAX}"
        hp_surface = font.render(
            hp_text, True, RED if game_manager.base_health < 30 else WHITE
        )
        screen.blit(hp_surface, (10, 40))

        build_hint = font.render(
            f"ЛКМ — башня ({TOWER_COST}$) | Построено: {len(towers)}", True, (200, 200, 100)
        )
        screen.blit(build_hint, (10, 68))
        hud.draw(screen)

        if game_manager.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            game_over_text = font_large.render("GAME OVER", True, RED)
            text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(game_over_text, text_rect)

            stats_text = (
                f"Волны: {game_manager.wave} | Убито: {game_manager.kills} | "
                f"Деньги: {game_manager.money}"
            )
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
