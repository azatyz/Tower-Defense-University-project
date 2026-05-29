from settings import BASE_HEALTH_MAX, START_MONEY


class GameManager:
    """Состояние игры: волны, экономика, HP базы."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Сброс к началу партии."""
        self.money = START_MONEY
        self.kills = 0
        self.wave = 1
        self.wave_timer = 0
        self.wave_cooldown = 120
        self.enemies_in_wave = 3
        self.spawned_this_wave = 0
        self.game_over = False
        self.max_kills_per_wave = 0
        self.base_health = BASE_HEALTH_MAX

    def update(self):
        self.wave_timer += 1

    def is_wave_ready(self):
        return (
            self.wave_timer >= self.wave_cooldown
            and self.spawned_this_wave >= self.enemies_in_wave
        )

    def next_wave(self):
        self.wave += 1
        self.enemies_in_wave = 3 + self.wave
        self.max_kills_per_wave = self.kills
        self.wave_timer = 0
        self.spawned_this_wave = 0

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
        return f"Волна: {self.wave} | Деньги: {self.money} | Убито: {self.kills}"
