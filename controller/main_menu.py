import pygame
import sys

from config.save_manager import load_highscore
from config.settings import WIDTH, HEIGHT, FPS, YELLOW, WHITE
from view.audio import SoundManager


def main_menu():
    """Стартовое меню с анимацией и статистикой"""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower Defense - Главное меню")
    clock = pygame.time.Clock()
    sound_manager = SoundManager()

    font_title = pygame.font.Font(None, 120)
    font_hint = pygame.font.Font(None, 56)
    font_controls = pygame.font.Font(None, 30)
    font_stats = pygame.font.Font(None, 40)

    # Загружаем рекорд, чтобы показать его на стартете
    highscore = load_highscore()

    offset = 0  # Переменная для движения фона

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                sound_manager.play("click")
                pygame.time.delay(150)
                return

            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                sound_manager.play("click")
                pygame.time.delay(150)
                return

        # 1. Анимированный фон
        screen.fill((20, 25, 30))
        offset = (offset + 0.5) % 50 # Сдвигаем линии каждый кадр

        # Рисуем ползущую сетку
        for i in range(0, WIDTH + 50, 50):
            pygame.draw.line(screen, (30, 40, 45), (i - offset, 0), (i - offset, HEIGHT), 2)
        for i in range(0, HEIGHT + 50, 50):
            pygame.draw.line(screen, (30, 40, 45), (0, i - offset), (WIDTH, i - offset), 2)

        # 2. Заголовок с эффектом тени
        title = font_title.render("TOWER DEFENSE", True, (50, 200, 100))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 3))

        # Тень
        title_shadow = font_title.render("TOWER DEFENSE", True, (10, 50, 20))
        screen.blit(title_shadow, title_rect.move(4, 4))
        screen.blit(title, title_rect)

        # 3. Интерактивная кнопка
        hover_zone = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 20, 300, 60)
        if hover_zone.collidepoint(mouse_pos):
            hint_text = "Начать игру"
            hint_color = YELLOW
        else:
            hint_text = "Начать игру"
            hint_color = WHITE

        hint = font_hint.render(hint_text, True, hint_color)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(hint, hint_rect)

        controls = font_controls.render("Enter / Space / ЛКМ", True, (170, 170, 170))
        controls_rect = controls.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 95))
        screen.blit(controls, controls_rect)

        # 4. Вывод рекорда
        stats = font_stats.render(f"Ваш рекорд: {highscore} волн", True, (150, 150, 150))
        stats_rect = stats.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 155))
        screen.blit(stats, stats_rect)

        pygame.display.flip()
        clock.tick(FPS)
