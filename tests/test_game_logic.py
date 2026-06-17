import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from entities import (
    BasicTower,
    BombTower,
    Enemy,
    SniperTower,
    TankEnemy,
    can_place_tower,
)
from game_manager import GameManager
from path import create_default_path


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
        self.assertEqual(manager.enemies_in_wave, 4)
        self.assertTrue(manager.wave_active)
        self.assertEqual(manager.spawned_this_wave, 0)


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


if __name__ == "__main__":
    pygame.init()
    unittest.main()


