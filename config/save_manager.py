import json
import os


def load_highscore():
    """Загрузка максимально пройденной волны"""
    if os.path.exists("save.json"):
        try:
            with open("save.json", "r") as f:
                return json.load(f).get("max_wave", 0)
        except:
            return 0
    return 0


def save_highscore(wave):
    """Сохранение рекорда, если он побит"""
    current_max = load_highscore()
    if wave > current_max:
        with open("save.json", "w") as f:
            json.dump({"max_wave": wave}, f)
