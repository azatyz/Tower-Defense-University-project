from config.save_manager import save_highscore
from models.entities import BossEnemy, Projectile, can_place_tower


def try_start_next_wave(manager):
    if manager.wave_active or manager.game_over:
        return False
    manager.next_wave()
    return True


def try_upgrade_tower_damage(manager, tower):
    if tower is None:
        return False

    cost = tower.get_damage_upgrade_cost()
    if not cost or manager.money < cost:
        return False

    manager.money -= cost
    tower.upgrade_damage()
    return True


def try_upgrade_tower_radar(manager, tower):
    if tower is None:
        return False

    cost = tower.get_radar_upgrade_cost()
    if not cost or manager.money < cost:
        return False

    manager.money -= cost
    tower.upgrade_radar()
    return True


def sell_tower(manager, towers, tower):
    if tower is None or tower not in towers:
        return False

    manager.money += tower.cost // 2
    towers.remove(tower)
    return True


def find_clicked_tower(towers, mouse_pos):
    for tower in towers:
        if tower.contains_point(mouse_pos):
            return tower
    return None


def try_build_tower(manager, tower_class, mouse_pos, path, towers):
    if tower_class is None:
        return False, ""

    x, y = mouse_pos
    can_build, reason = can_place_tower(x, y, path, towers)
    tower_cost = tower_class(0, 0).cost

    if not can_build:
        return False, reason

    if manager.money < tower_cost:
        return False, "Недостаточно денег!"

    towers.append(tower_class(x, y))
    manager.money -= tower_cost
    return True, ""


def update_game(manager, path, enemies, towers, projectiles):
    events = []

    manager.update()
    _spawn_enemies(manager, path, enemies)
    _complete_wave_if_needed(manager, enemies, events)
    _update_enemies(manager, enemies)
    _update_towers(towers, enemies, projectiles)
    _update_projectiles(projectiles, enemies)
    _remove_dead_enemies(manager, enemies)

    return events


def _spawn_enemies(manager, path, enemies):
    if not manager.wave_active or manager.spawned_this_wave >= manager.enemies_in_wave:
        return

    if manager.wave_timer % 40 != 0:
        return

    enemy_class, wave_num = manager.current_wave_queue[manager.spawned_this_wave]
    new_enemy = BossEnemy(path, wave_num) if enemy_class == BossEnemy else enemy_class(path)
    enemies.append(new_enemy)
    manager.register_spawn()


def _complete_wave_if_needed(manager, enemies, events):
    if not manager.wave_active:
        return

    if manager.spawned_this_wave < manager.enemies_in_wave or enemies:
        return

    manager.wave_active = False
    manager.money += 100 + manager.wave * 20
    events.append({"message": f"Волна {manager.wave} пройдена!", "kind": "success"})


def _update_enemies(manager, enemies):
    for enemy in enemies[:]:
        enemy.update()
        if enemy.reached_end():
            manager.damage_base(10)
            enemies.remove(enemy)
            if manager.game_over:
                save_highscore(manager.wave)


def _update_towers(towers, enemies, projectiles):
    for tower in towers:
        tower.update()
        target = tower.find_target(enemies)
        if target and tower.can_shoot():
            projectiles.append(
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


def _update_projectiles(projectiles, enemies):
    for projectile in projectiles[:]:
        projectile.update()
        if projectile.is_done():
            projectiles.remove(projectile)
            continue

        if projectile.target not in enemies:
            continue

        distance = projectile.get_distance_to(projectile.target.x, projectile.target.y)
        if distance >= projectile.target.radius + projectile.radius:
            continue

        if projectile.splash_radius > 0:
            _apply_splash_damage(projectile, enemies)
        else:
            projectile.target.hp -= projectile.damage

        if projectile in projectiles:
            projectiles.remove(projectile)


def _apply_splash_damage(projectile, enemies):
    for enemy in enemies:
        distance = enemy.get_distance_to(projectile.x, projectile.y)
        if distance > projectile.splash_radius:
            continue

        falloff = 1.0 - (distance / projectile.splash_radius)
        actual_damage = max(1, int(projectile.damage * falloff))
        enemy.hp -= actual_damage


def _remove_dead_enemies(manager, enemies):
    for enemy in enemies[:]:
        if enemy.hp <= 0:
            manager.add_kill_reward(enemy.reward)
            enemies.remove(enemy)
