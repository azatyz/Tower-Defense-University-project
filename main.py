import sys

import pygame

from entities import (
    BasicTower,
    Projectile,
    TOWER_TYPES,
    can_place_tower,
    create_enemy_for_wave,
)
from game_manager import GameManager
from path import create_default_path
from settings import BASE_HEALTH_MAX, BLACK, FPS, HEIGHT, RED, WHITE, WIDTH, YELLOW
from ui import BuildUI, MessageHUD, PauseMenu, TowerInfoPanel, WaveUI


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
        self.wave_ui = WaveUI(self.font)
        self.tower_info_panel = TowerInfoPanel(self.font)
        self.reset()

    def reset(self):
        self.path = create_default_path()
        self.manager = GameManager()
        self.enemies = []
        self.projectiles = []
        self.towers = []
        self.selected_tower = None
        self.paused = False
        self.build_ui.set_tower_type(BasicTower)
        self.hud.show("Клавиши 1/2/3/4 — тип башни. Esc — пауза", (200, 220, 100), 240)

    def try_build_tower(self, pos):
        tower_cls = self.build_ui.selected_class
        if tower_cls is None:
            self.hud.show("Сначала выбери башню (1, 2, 3 или 4)", RED)
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

        tower = tower_cls(mx, my)
        self.towers.append(tower)
        self.selected_tower = tower
        self.manager.money -= cost
        self.hud.show(f"Башня {tower_cls.kind_name} построена!", (100, 255, 100))

    def find_tower_at(self, pos):
        for tower in reversed(self.towers):
            if tower.contains_point(pos):
                return tower
        return None

    def try_upgrade_selected_tower(self):
        tower = self.selected_tower
        if tower is None:
            self.hud.show("Сначала выбери построенную башню", RED)
            return
        if not tower.can_upgrade():
            self.hud.show(f"{tower.kind_name} уже максимального уровня", YELLOW)
            return

        cost = tower.get_upgrade_cost()
        if self.manager.money < cost:
            self.hud.show(f"На апгрейд нужно {cost}$, есть {self.manager.money}", RED)
            return

        self.manager.money -= cost
        tower.upgrade()
        self.hud.show(f"{tower.kind_name} улучшена до уровня {tower.level}", (100, 255, 100))

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
                if event.key == pygame.K_u and not self.paused and not self.manager.game_over:
                    self.try_upgrade_selected_tower()
                # TODO: временно отключен спавн тестового врага по пробелу
                # if event.key == pygame.K_SPACE and not self.paused:
                #     self.enemies.append(create_enemy_for_wave(self.path, self.manager.wave))
                if event.key == pygame.K_e and not self.paused:
                    if not self.manager.wave_active:
                        self.manager.next_wave()
                        self.hud.show(f"Волна {self.manager.wave}!", WHITE, 90)
                    else:
                        self.hud.show("Волна уже идёт — дождись завершения", (220, 180, 50), 90)
                if event.key == pygame.K_r and (self.manager.game_over or self.paused):
                    self.reset()
                if event.key == pygame.K_q and (self.manager.game_over or self.paused):
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
                        action = self.tower_info_panel.handle_click(event.pos)
                        if action == "upgrade":
                            self.try_upgrade_selected_tower()
                            continue

                        action = self.wave_ui.handle_click(event.pos, self.manager)
                        if action == "next_wave":
                            self.manager.next_wave()
                            self.hud.show(f"Волна {self.manager.wave}!", WHITE, 90)
                        else:
                            tower = self.find_tower_at(event.pos)
                            if tower is not None:
                                self.selected_tower = tower
                                self.hud.show(f"Выбрана башня {tower.kind_name} ур. {tower.level}", WHITE, 90)
                            else:
                                self.try_build_tower(event.pos)
        return True

    def update_gameplay(self):
        if self.manager.game_over or self.paused:
            return

        if self.manager.wave_active and self.manager.spawned_this_wave < self.manager.enemies_in_wave:
            if self.manager.wave_timer % 30 == 1:
                self.enemies.append(create_enemy_for_wave(self.path, self.manager.wave))
                self.manager.register_spawn()

        if self.manager.wave_active and self.manager.spawned_this_wave >= self.manager.enemies_in_wave and not self.enemies:
            self.manager.wave_active = False
            self.hud.show("Волна завершена! Нажми E для следующей.", (100, 220, 100), 180)

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
                self.projectiles.append(
                    Projectile(
                        tower.x,
                        tower.y,
                        target,
                        tower.damage,
                        tower.splash_radius,
                        tower.color,
                    )
                )
                tower.shoot()

        for projectile in self.projectiles[:]:
            projectile.update()

            # If projectile reached its assigned target, apply damage and remove it.
            target = projectile.target
            if target is not None:
                # If target died meanwhile, discard projectile.
                if getattr(target, "hp", None) is not None and target.hp <= 0:
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    continue
                # If close enough to the target, apply damage and remove projectile.
                if projectile.get_distance_to(target.x, target.y) <= (getattr(target, "radius", 0) + projectile.radius):
                    self.apply_projectile_damage(projectile, target.x, target.y, target)
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    continue

            # If projectile is out of bounds, remove it.
            if projectile.is_done():
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)
                continue

            # Fallback: check collision against any enemy (covers redirected/missing targets).
            for enemy in self.enemies[:]:
                if projectile.get_distance_to(enemy.x, enemy.y) < enemy.radius + projectile.radius:
                    self.apply_projectile_damage(projectile, enemy.x, enemy.y, enemy)
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    break

        for enemy in self.enemies[:]:
            if enemy.hp <= 0:
                self.manager.add_kill_reward(enemy.reward)
                self.enemies.remove(enemy)

    def apply_projectile_damage(self, projectile, hit_x, hit_y, direct_enemy=None):
        if projectile.splash_radius <= 0:
            target = direct_enemy or projectile.target
            if target in self.enemies:
                target.hp -= projectile.damage
            return

        for enemy in self.enemies:
            distance = enemy.get_distance_to(hit_x, hit_y)
            if distance <= projectile.splash_radius:
                splash_factor = max(0.35, 1 - distance / projectile.splash_radius)
                enemy.hp -= max(1, int(projectile.damage * splash_factor))

    def draw(self):
        self.screen.fill(BLACK)
        self.path.draw(self.screen)

        for tower in self.towers:
            tower.draw(self.screen)
        if self.selected_tower is not None:
            pygame.draw.circle(
                self.screen,
                YELLOW,
                (self.selected_tower.x, self.selected_tower.y),
                self.selected_tower.range,
                2,
            )
            pygame.draw.rect(
                self.screen,
                YELLOW,
                (
                    self.selected_tower.x - self.selected_tower.width // 2 - 4,
                    self.selected_tower.y - self.selected_tower.height // 2 - 4,
                    self.selected_tower.width + 8,
                    self.selected_tower.height + 8,
                ),
                2,
            )
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
        self.wave_ui.draw(self.screen, self.manager, self.enemies)
        self.tower_info_panel.draw(self.screen, self.selected_tower, self.manager.money)
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
