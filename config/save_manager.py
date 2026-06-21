import json
from pathlib import Path


SAVE_FILE = Path("save.json")


def load_highscore():
    """Загрузка максимально пройденной волны"""
    if not SAVE_FILE.exists():
        return 0

    try:
        with SAVE_FILE.open("r", encoding="utf-8") as file:
            return json.load(file).get("max_wave", 0)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0


def save_highscore(wave):
    """Сохранение рекорда, если он побит"""
    current_max = load_highscore()
    if wave > current_max:
        with SAVE_FILE.open("w", encoding="utf-8") as file:
            json.dump({"max_wave": wave}, file)
