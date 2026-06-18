import pygame
import os

class SoundManager:
    """
    Безопасный менеджер звуков (Паттерн: Graceful Degradation).
    Перехватывает ошибки загрузки, чтобы игра не вылетала при отсутствии файлов.
    """
    def __init__(self):
        try:
            pygame.mixer.init()
            self.enabled = True
        except Exception:
            self.enabled = False

        self.sounds = {}
        
        # Пытаемся загрузить звуки (файлы нужно положить в папку assets)
        self._load_sound("click", "assets/click.wav")
        self._load_sound("build", "assets/build.wav")
        self._load_sound("error", "assets/error.wav")
        self._load_sound("upgrade", "assets/upgrade.wav")

    def _load_sound(self, name, path):
        if not self.enabled:
            return
            
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(0.3)  # Делаем звуки тихими (30% громкости), чтобы не раздражали
                self.sounds[name] = sound
            except Exception:
                self.sounds[name] = None
        else:
            self.sounds[name] = None

    def play(self, name):
        """Безопасное воспроизведение звука по имени."""
        if self.enabled and name in self.sounds and self.sounds[name]:
            self.sounds[name].play()