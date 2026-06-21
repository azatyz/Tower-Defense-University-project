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
from controller.game_logic import update_game
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


if __name__ == "__main__":
    pygame.init()
    unittest.main()


