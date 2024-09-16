import os
import re

DATA_FOLDER = os.getenv('DATA_FOLDER', 'data')

# Ottieni il percorso della directory in cui si trova app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Verifica se il percorso è relativo o assoluto
if not os.path.isabs(DATA_FOLDER):
    # Se è relativo, convertilo in assoluto rispetto alla posizione di app.py
    DATA_FOLDER = os.path.join(BASE_DIR, DATA_FOLDER)
else:
    # Se è assoluto, usalo così com'è
    DATA_FOLDER = DATA_FOLDER

UPLOAD_FOLDER = DATA_FOLDER + '/uploads'

ALLOWED_MEDIA_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'pdf', 'css'}
ALLOWED_UPLOAD_EXTENSIONS = {'md', 'zip'}


# Funzione per controllare i tipi di file consentiti
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_UPLOAD_EXTENSIONS


# Funzione per creare nomi validi per le cartelle (senza spazi o caratteri speciali)
def sanitize_folder_name(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip().replace(' ', '_')).lower()


def allowed_media_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_MEDIA_EXTENSIONS
