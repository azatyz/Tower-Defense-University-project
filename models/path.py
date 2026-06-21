import pygame


class Path:
    """Класс для управления тропинкой врагов"""

    def __init__(self, points):
        self.points = points
        self.path_width = 59
        self.path_color = (80, 80, 80)

    def get_point_at_index(self, index):
        """Получение точки пути по индексу"""
        if 0 <= index < len(self.points):
            return self.points[index]
        return self.points[-1]

    def get_total_points(self):
        """Количество точек на пути"""
        return len(self.points)

    def is_position_on_path(self, x, y, tower_radius):
        """Проверка расстояния башни от тропинки"""
        min_clearance = tower_radius + self.path_width / 2 + 4
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            distance = self._distance_to_segment(x, y, x1, y1, x2, y2)
            if distance < min_clearance:
                return True
        return False

    def draw(self, screen):
        """Отрисовка пути на экране"""
        if len(self.points) < 2:
            return

        for i in range(len(self.points) - 1):
            start = (int(self.points[i][0]), int(self.points[i][1]))
            end = (int(self.points[i + 1][0]), int(self.points[i + 1][1]))
            pygame.draw.line(screen, self.path_color, start, end, self.path_width)

        for point in self.points:
            pygame.draw.circle(
                screen,
                self.path_color,
                (int(point[0]), int(point[1])),
                self.path_width // 2,
            )

    @staticmethod
    def _distance_to_segment(x, y, x1, y1, x2, y2):
        """Расстояние от точки до отрезка"""
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return ((x - closest_x) ** 2 + (y - closest_y) ** 2) ** 0.5


def create_default_path():
    """Лабиринт-путь"""
    return Path([
        (50, 200),
        (300, 200),
        (300, 450),
        (600, 450),
        (600, 100),
        (900, 100),
        (900, 600),
        (1200, 600),
        (1200, 300),
        (1350, 300),
    ])
