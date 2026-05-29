import sys

import pygame

from entities import (
    BasicTower,
    Projectile,
    SniperTower,
    TOWER_TYPES,
    can_place_tower,
    create_enemy_for_wave,
)
from game_manager import GameManager
from path import create_default_path
from settings import BASE_HEALTH_MAX, BLACK, FPS, HEIGHT, RED, WHITE, WIDTH
from ui import BuildUI, MessageHUD, PauseMenu


class Game:
    """Главный класс: связывает систему игры и UI."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tower Defense — University Project")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22)
        self.font_large = pygame.font.SysFont("arial", 72)
        self.hud = MessageHUD(self.font)
        self.build_ui = BuildUI(self.font)
        self.pause_menu = PauseMenu(self.font)
        self.reset()

    def reset(self):
        self.path = create_default_path()
        self.manager = GameManager()
        self.enemies = []
        self.projectiles = []
        self.towers = []
        self.auto_spawn = True
        self.paused = False
        self.build_ui.set_tower_type(BasicTower)
        self.hud.show("Клавиши 1/2/3 — тип башни. Esc — пауза", (200, 220, 100), 240)

    def try_build_tower(self, pos):
        tower_cls = self.build_ui.selected_class
        if tower_cls is None:
            self.hud.show("Сначала выбери башню (1, 2 или 3)", RED)
            return

        mx, my = pos
        cost = tower_cls(mx, my).cost
        if self.manager.money < cost:
            self.hud.show(f"Мало денег! Нужно {cost}$, есть {self.manager.money}", RED)
            return

        ok, reason = can_place_tower(mx, my, self.path, self.towers)
        if not ok:
            self.hud.show(reason, RED)
            return

        self.towers.append(tower_cls(mx, my))
        self.manager.money -= cost
        self.hud.show(f"Башня {tower_cls.kind_name} построена!", (100, 255, 100))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and not self.manager.game_over:
                    self.paused = not self.paused
                    self.hud.show("PAUSE" if self.paused else "RESUME", WHITE, 90)
                if event.key in TOWER_TYPES and not self.paused:
                    self.build_ui.set_tower_type(TOWER_TYPES[event.key])
                    name = TOWER_TYPES[event.key].kind_name
                    self.hud.show(f"Выбрана: {name}", WHITE, 90)
                # TODO: временно отключен спавн тестового врага по пробелу
                # if event.key == pygame.K_SPACE and not self.paused:
                #     self.enemies.append(create_enemy_for_wave(self.path, self.manager.wave))
                if event.key == pygame.K_e and not self.paused:
                    self.manager.next_wave()
                    self.hud.show(f"Волна {self.manager.wave}!", WHITE, 90)
                if event.key == pygame.K_r and (self.manager.game_over or self.paused):
                    self.reset()
                if event.key == pygame.K_q and self.manager.game_over:
                    return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.paused and not self.manager.game_over:
                        action = self.pause_menu.handle_click(event.pos)
                        if action == "resume":
                            self.paused = False
                            self.hud.show("RESUME", WHITE, 90)
                        elif action == "restart":
                            self.reset()
                        elif action == "quit":
                            return False
                    elif not self.paused and not self.manager.game_over:
                        self.try_build_tower(event.pos)
        return True

    def update_gameplay(self):
        if self.manager.game_over or self.paused:
            return

        if self.auto_spawn and self.manager.spawned_this_wave < self.manager.enemies_in_wave:
            if self.manager.wave_timer % 30 == 1:
                self.enemies.append(create_enemy_for_wave(self.path, self.manager.wave))
                self.manager.register_spawn()

        if self.auto_spawn and self.manager.is_wave_ready():
            self.manager.next_wave()
            self.hud.show(f"Волна {self.manager.wave}! Врагов: {self.manager.enemies_in_wave}", WHITE, 120)

        for enemy in self.enemies:
            enemy.update()

        leaked = [enemy for enemy in self.enemies if enemy.reached_end()]
        for enemy in leaked:
            self.manager.damage_base(10)
            self.enemies.remove(enemy)
            self.hud.show(f"База −10 HP! Осталось {self.manager.base_health}", RED, 90)

        for tower in self.towers:
            tower.update()
            target = tower.find_target(self.enemies)
            if target and tower.can_shoot():
                self.projectiles.append(Projectile(tower.x, tower.y, target, tower.damage))
                tower.shoot()

        for projectile in self.projectiles[:]:
            projectile.update()
            if projectile.is_done():
                self.projectiles.remove(projectile)
                continue

            for enemy in self.enemies[:]:
                if projectile.get_distance_to(enemy.x, enemy.y) < enemy.radius + projectile.radius:
                    enemy.hp -= projectile.damage
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    break

        for enemy in self.enemies[:]:
            if enemy.hp <= 0:
                self.manager.add_kill_reward(enemy.reward)
                self.enemies.remove(enemy)

    def draw(self):
        self.screen.fill(BLACK)
        self.path.draw(self.screen)

        for tower in self.towers:
            tower.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for projectile in self.projectiles:
            projectile.draw(self.screen)

        if not self.manager.game_over and not self.paused:
            self.build_ui.draw_preview(
                self.screen,
                pygame.mouse.get_pos(),
                self.path,
                self.towers,
                self.manager.money,
                self.manager.game_over,
            )

        self.screen.blit(self.font.render(self.manager.get_hud_line(), True, WHITE), (10, 10))
        hp_color = RED if self.manager.base_health < 30 else WHITE
        self.screen.blit(
            self.font.render(f"HP базы: {self.manager.base_health}/{BASE_HEALTH_MAX}", True, hp_color),
            (10, 38),
        )
        sel = self.build_ui.selected_class
        cost = sel(0, 0).cost if sel else 0
        self.screen.blit(
            self.font.render(
                f"Выбрано: {sel.kind_name if sel else '-'} ({cost}$) | ЛКМ — построить",
                True,
                (200, 200, 100),
            ),
            (10, 66),
        )
        self.build_ui.draw_toolbar(self.screen, sel)
        self.hud.draw(self.screen)

        if self.paused and not self.manager.game_over:
            self.pause_menu.draw(self.screen)

        if self.manager.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            game_over_text = self.font_large.render("GAME OVER", True, RED)
            self.screen.blit(game_over_text, game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
            stats = self.font.render(
                f"Волны: {self.manager.wave} | Убито: {self.manager.kills} | Деньги: {self.manager.money}",
                True,
                WHITE,
            )
            self.screen.blit(stats, stats.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))
            hint = self.font.render("R — заново | Q — выход", True, WHITE)
            self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90)))


    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.manager.update()
            self.update_gameplay()
            self.hud.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
