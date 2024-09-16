# Caricamento della lista degli argomenti
import json
import os

from utils import DATA_FOLDER


def load_topics():
    if not os.path.exists(os.path.join(DATA_FOLDER, 'argomenti.json')):
        return {}
    with open(os.path.join(DATA_FOLDER, 'argomenti.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


# Salvataggio della lista degli argomenti
def save_topics(data):
    with open(os.path.join(DATA_FOLDER, 'argomenti.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
