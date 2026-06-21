from config.settings import BASE_HEALTH_MAX, START_MONEY
import random
from models.entities import Enemy, FastEnemy, TankEnemy, BossEnemy


class GameManager:
    """Состояние игры: волны, экономика, HP базы"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Сброс к началу партии"""
        self.money = START_MONEY
        self.kills = 0
        self.wave = 0
        self.wave_timer = 0
        self.wave_cooldown = 120
        self.enemies_in_wave = 0
        self.spawned_this_wave = 0
        self.game_over = False
        self.max_kills_per_wave = 0
        self.base_health = BASE_HEALTH_MAX
        self.wave_active = False

    def update(self):
        if self.wave_active:
            self.wave_timer += 1

    def is_wave_ready(self):
        return (
            self.wave_timer >= self.wave_cooldown
            and self.spawned_this_wave >= self.enemies_in_wave
        )

    def generate_dynamic_wave(self):
        """Динамический алгоритм генерации волны"""
        wave_queue = []
        
        if self.wave % 10 == 0:
            # Юбилейная волна: спавним Босса и немного поддержки
            wave_queue.append((BossEnemy, self.wave))
            for _ in range(self.wave // 5):
                wave_queue.append((FastEnemy, self.wave))
            random.shuffle(wave_queue)
            return wave_queue

        # 2. Расчет бюджета на волну
        budget = 10 + int(self.wave ** 1.5 * 3)
        
        # 3. Каталог врагов
        enemy_catalog = {
            "basic": {"class": Enemy, "cost": 1, "min_wave": 1},
            "fast":  {"class": FastEnemy, "cost": 2, "min_wave": 3},
            "tank":  {"class": TankEnemy, "cost": 5, "min_wave": 5}
        }
        
        # 4. Генерация волны
        while budget > 0:
            available_options = [
                data for data in enemy_catalog.values() 
                if data["cost"] <= budget and data["min_wave"] <= self.wave
            ]
            
            if not available_options:
                break 
                
            choice = random.choice(available_options)
            wave_queue.append((choice["class"], self.wave))
            budget -= choice["cost"]
            
        random.shuffle(wave_queue)
        
        return wave_queue
    
    def next_wave(self):
        self.wave += 1
        self.wave_timer = 0
        # Генерируем умную очередь врагов
        self.current_wave_queue = self.generate_dynamic_wave()
        
        # Количество врагов берется из длины сгенерированной очереди
        self.enemies_in_wave = len(self.current_wave_queue)
        self.spawned_this_wave = 0
        self.wave_active = True

    def register_spawn(self):
        self.spawned_this_wave += 1

    def add_kill_reward(self, amount):
        self.money += amount
        self.kills += 1

    def damage_base(self, amount=10):
        self.base_health -= amount
        if self.base_health <= 0:
            self.base_health = 0
            self.game_over = True

    def calculate_wave_efficiency(self):
        if self.enemies_in_wave == 0:
            return 0.0
        killed_this_wave = self.kills - self.max_kills_per_wave
        return (killed_this_wave / self.enemies_in_wave) * 100

    def get_hud_line(self):
        return f"Волна: {self.wave} | Деньги: {self.money}$ | Убито: {self.kills}"
