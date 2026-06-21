import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from config.save_manager import load_highscore
from controller.game_controller import _persist_highscore
from controller.game_logic import (
    _apply_splash_damage,
    sell_tower,
    try_build_tower,
    try_start_next_wave,
    try_upgrade_tower_damage,
    try_upgrade_tower_radar,
    update_game,
)
from models.entities import (
    BasicTower,
    BossEnemy,
    BombTower,
    Enemy,
    SniperTower,
    TankEnemy,
    can_place_tower
)
from models.game_manager import GameManager
from models.path import create_default_path


class TowerPlacementTests(unittest.TestCase):
    def test_cannot_build_on_enemy_path(self):
        path = create_default_path()

        can_build, reason = can_place_tower(50, 200, path, [])

        self.assertFalse(can_build)
        self.assertIn("дороге", reason)

    def test_cannot_build_too_close_to_existing_tower(self):
        path = create_default_path()
        existing_tower = BasicTower(480, 300)

        can_build, reason = can_place_tower(520, 300, path, [existing_tower])

        self.assertFalse(can_build)
        self.assertIn("башне", reason)

    def test_build_tower_spends_money_and_adds_tower(self):
        path = create_default_path()
        manager = GameManager()
        towers = []

        built, reason = try_build_tower(manager, BasicTower, (450, 300), path, towers)

        self.assertTrue(built)
        self.assertEqual(reason, "Башня построена!")
        self.assertEqual(len(towers), 1)
        self.assertIsInstance(towers[0], BasicTower)
        self.assertEqual(manager.money, 130)

    def test_build_tower_fails_when_money_is_not_enough(self):
        path = create_default_path()
        manager = GameManager()
        manager.money = 100
        towers = []

        built, reason = try_build_tower(manager, BasicTower, (450, 300), path, towers)

        self.assertFalse(built)
        self.assertIn("Недостаточно", reason)
        self.assertEqual(len(towers), 0)

    def test_sell_tower_returns_half_of_cost(self):
        manager = GameManager()
        manager.money = 0
        tower = BasicTower(450, 300)
        towers = [tower]

        sold, message = sell_tower(manager, towers, tower)

        self.assertTrue(sold)
        self.assertEqual(message, "Башня продана!")
        self.assertEqual(manager.money, tower.cost // 2)
        self.assertEqual(towers, [])


class TargetStrategyTests(unittest.TestCase):
    def test_sniper_targets_enemy_with_highest_hp(self):
        path = create_default_path()
        weak_enemy = Enemy(path)
        tank_enemy = TankEnemy(path)
        tower = SniperTower(50, 200)

        self.assertIs(tower.find_target([weak_enemy, tank_enemy]), tank_enemy)

    def test_bomb_tower_targets_enemy_closest_to_base(self):
        path = create_default_path()
        early_enemy = Enemy(path)
        
        advanced_enemy = Enemy(path)
        advanced_enemy.progress = 0.5
        advanced_enemy.x = 150 
        
        tower = BombTower(50, 200)

        self.assertIs(tower.find_target([early_enemy, advanced_enemy]), advanced_enemy)


class GameManagerTests(unittest.TestCase):
    def test_next_wave_initializes_wave_state(self):
        manager = GameManager()

        manager.next_wave()

        self.assertEqual(manager.wave, 1)
        self.assertEqual(manager.enemies_in_wave, 13) 
        self.assertTrue(manager.wave_active)
        self.assertEqual(manager.spawned_this_wave, 0)

    def test_next_wave_resets_wave_timer(self):
        manager = GameManager()

        manager.next_wave()
        manager.update()
        manager.update()
        manager.next_wave()

        self.assertEqual(manager.wave_timer, 0)

    def test_boss_uses_custom_base_damage(self):
        path = create_default_path()
        manager = GameManager()
        boss = BossEnemy(path, 10)
        boss.path_index = path.get_total_points() - 1

        update_game(manager, path, [boss], [], [])

        self.assertEqual(manager.base_health, 75)

    def test_completed_wave_disables_wave_and_grants_bonus(self):
        path = create_default_path()
        manager = GameManager()
        manager.wave = 3
        manager.money = 0
        manager.wave_active = True
        manager.enemies_in_wave = 0
        manager.spawned_this_wave = 0

        events = update_game(manager, path, [], [], [])

        self.assertFalse(manager.wave_active)
        self.assertEqual(manager.money, 160)
        self.assertEqual(events[0]["kind"], "success")
        self.assertIn("Волна 3", events[0]["message"])

    def test_start_wave_returns_warning_when_wave_already_active(self):
        manager = GameManager()
        manager.next_wave()

        started, message = try_start_next_wave(manager)

        self.assertFalse(started)
        self.assertEqual(message, "Волна уже идет")

class TowerUpgradeTests(unittest.TestCase):
    def test_radar_upgrade_increases_ranges(self):
        tower = BasicTower(100, 100)
        initial_shoot = tower.shoot_range
        initial_radar = tower.radar_range
        
        upgraded = tower.upgrade_radar()
        
        self.assertTrue(upgraded)
        self.assertEqual(tower.radar_level, 2)
        self.assertGreater(tower.shoot_range, initial_shoot)
        self.assertGreater(tower.radar_range, initial_radar)

    def test_damage_upgrade_returns_reason_when_tower_not_selected(self):
        manager = GameManager()

        upgraded, message = try_upgrade_tower_damage(manager, None)

        self.assertFalse(upgraded)
        self.assertEqual(message, "Сначала выберите башню")

    def test_radar_upgrade_returns_reason_when_money_is_not_enough(self):
        manager = GameManager()
        manager.money = 10
        tower = BasicTower(100, 100)

        upgraded, message = try_upgrade_tower_radar(manager, tower)

        self.assertFalse(upgraded)
        self.assertIn("Недостаточно денег", message)


class ProjectileTests(unittest.TestCase):
    def test_bomb_projectile_applies_splash_damage_with_falloff(self):
        path = create_default_path()
        center_enemy = Enemy(path)
        near_enemy = Enemy(path)
        far_enemy = Enemy(path)

        center_enemy.x = 300
        center_enemy.y = 300
        center_enemy.speed = 0
        near_enemy.x = 330
        near_enemy.y = 300
        near_enemy.speed = 0
        far_enemy.x = 390
        far_enemy.y = 300
        far_enemy.speed = 0

        projectile = SimpleNamespace(
            x=300,
            y=300,
            damage=40,
            splash_radius=100,
        )

        _apply_splash_damage(projectile, [center_enemy, near_enemy, far_enemy])

        self.assertLess(center_enemy.hp, near_enemy.hp)
        self.assertLess(near_enemy.hp, far_enemy.hp)


class SaveManagerTests(unittest.TestCase):
    def test_persist_highscore_saves_progress_on_exit(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                os.chdir(tmp_dir)
                state = SimpleNamespace(
                    manager=SimpleNamespace(wave=7),
                    highscore=3,
                )

                _persist_highscore(state)

                self.assertEqual(load_highscore(), 7)
                self.assertEqual(state.highscore, 7)
            finally:
                os.chdir(original_cwd)

    def test_highscore_is_not_overwritten_by_lower_wave(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                os.chdir(tmp_dir)
                first_state = SimpleNamespace(
                    manager=SimpleNamespace(wave=9),
                    highscore=0,
                )
                second_state = SimpleNamespace(
                    manager=SimpleNamespace(wave=4),
                    highscore=9,
                )

                _persist_highscore(first_state)
                _persist_highscore(second_state)

                self.assertEqual(load_highscore(), 9)
                self.assertEqual(second_state.highscore, 9)
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pygame.init()
    unittest.main()


