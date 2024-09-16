import os
import json
import re
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory
from werkzeug.utils import secure_filename
from markdown import markdown
from flask_basicauth import BasicAuth
import zipfile
import shutil

app = Flask(__name__)

# Configurazione Flask e autenticazione base
app.config['DATA_FOLDER'] = os.getenv('DATA_FOLDER', 'data')
app.config['UPLOAD_FOLDER'] = os.getenv('DATA_FOLDER', 'data') + '/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'md', 'zip'}

# Prendi le credenziali dal sistema di variabili d'ambiente
app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME', 'admin')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD', 'password')

app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')  # Anche la chiave segreta può essere impostata dall'ambiente

basic_auth = BasicAuth(app)
ALLOWED_MEDIA_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'pdf', 'css'}


# Funzione per controllare i tipi di file consentiti
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Funzione per creare nomi validi per le cartelle (senza spazi o caratteri speciali)
def sanitize_folder_name(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip().replace(' ', '_')).lower()


def allowed_media_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_MEDIA_EXTENSIONS


# Caricamento della lista degli argomenti
def load_topics():
    if not os.path.exists(app.config['DATA_FOLDER'] + '/argomenti.json'):
        return {}
    with open(app.config['DATA_FOLDER'] + '/argomenti.json', 'r', encoding='utf-8') as f:
        return json.load(f)


# Salvataggio della lista degli argomenti
def save_topics(data):
    with open(app.config['DATA_FOLDER'] + '/argomenti.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Rotta per la homepage: lista di argomenti e sottoargomenti
@app.route('/')
def index():
    argomenti = load_topics()
    return render_template('index.html', argomenti=argomenti)


# Rotta per visualizzare il contenuto markdown
@app.route('/view/<argomento>/<sottoargomento>')
@app.route('/view/<argomento>/<sottoargomento>/')
def view_md(argomento, sottoargomento):
    argomento_folder = argomento
    filename = 'index.md'
    # Carica il file markdown e convertilo in HTML
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], argomento_folder, sottoargomento, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = markdown(f.read())

    # Cerca il CSS opzionale nella cartella dell'argomento o sottoargomento
    css_file = None
    css_path = os.path.join(app.config['UPLOAD_FOLDER'], argomento_folder, 'style.css')
    if os.path.exists(css_path):
        css_file = f'{argomento_folder}/style.css'

    sottoargomento_css_path = os.path.join(app.config['UPLOAD_FOLDER'], argomento_folder, sottoargomento, 'style.css')
    if os.path.exists(sottoargomento_css_path):
        css_file = f'{argomento_folder}/{sottoargomento}/style.css'

    argomenti = load_topics()
    # Trova la label dell'argomento
    if argomento_folder in argomenti:
        argomento = argomenti[argomento_folder]
    else:
        abort(404, description="Argomento non trovato")

    # Trova la label del sottoargomento
    sottoargomenti = argomenti[argomento_folder]['sottoargomenti']
    for sotto in sottoargomenti:
        if sotto['folder'] == sottoargomento:
            sottoargomento = sotto
            break

    print(argomento)
    print(sottoargomento)
    return render_template('view_md.html', content=content, argomento=argomento,
                           sottoargomento=sottoargomento, sottoargomenti=sottoargomenti, css_file=css_file)


@app.route('/view/<argomento>/<sottoargomento>/<filename>')
def serve_media(argomento, sottoargomento, filename):
    """
    Serve file media dalla cartella del sottoargomento, solo se il file è tra quelli consentiti.
    """
    # Controlla se l'estensione del file è consentita
    if not allowed_media_file(filename):
        abort(403, description="Tipo di file non consentito")

    # Definisci il percorso del sottoargomento
    sottoargomento_path = os.path.join(app.config['UPLOAD_FOLDER'], argomento, sottoargomento)

    # Controlla se il file esiste
    if os.path.exists(os.path.join(sottoargomento_path, filename)):
        return send_from_directory(sottoargomento_path, filename)
    else:
        # Se il file non esiste, restituisce un errore 404
        abort(404, description="File non trovato")


@app.route('/admin', methods=['GET', 'POST'])
@basic_auth.required
def admin():
    if request.method == 'POST':
        argomento_label = request.form['argomento']
        sottoargomento_label = request.form['sottoargomento']
        file = request.files['file']

        if file and allowed_file(file.filename):
            # Crea nomi validi per le cartelle
            argomento_folder = sanitize_folder_name(argomento_label)
            sottoargomento_folder = sanitize_folder_name(sottoargomento_label)

            # Crea le cartelle se non esistono
            argomento_path = os.path.join(app.config['UPLOAD_FOLDER'], argomento_folder)
            sottoargomento_path = os.path.join(argomento_path, sottoargomento_folder)
            os.makedirs(sottoargomento_path, exist_ok=True)

            # Se è uno zip, gestisci l'estrazione
            filename = secure_filename(file.filename)
            if filename.endswith('.zip'):
                # Estrai i file in una cartella temporanea
                temp_extract_path = os.path.join(sottoargomento_path, 'temp')
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_path)

                # Sposta i file dalla cartella intermedia se necessario
                extracted_items = [f for f in os.listdir(temp_extract_path) if not f.startswith('__')]

                if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_path, extracted_items[0])):
                    # Se c'è una sola cartella estratta, sposta il suo contenuto
                    intermedio_path = os.path.join(temp_extract_path, extracted_items[0])
                    for item in os.listdir(intermedio_path):
                        shutil.move(os.path.join(intermedio_path, item), sottoargomento_path)
                    # Rimuovi la cartella intermedia
                    shutil.rmtree(intermedio_path)
                else:
                    # Se non c'è una cartella intermedia, sposta tutto il contenuto direttamente
                    for item in extracted_items:
                        shutil.move(os.path.join(temp_extract_path, item), sottoargomento_path)

                # Rimuovi la cartella temporanea
                shutil.rmtree(temp_extract_path)
                # Cerca i file markdown nella cartella estratta
                md_files = [f for f in os.listdir(sottoargomento_path) if f.endswith('.md')]

                # Se non c'è nessun file .md, segnala un errore
                if not md_files:
                    flash('Errore: Nessun file .md trovato nel file zip!', 'error')
                    return redirect(url_for('admin'))

                # Se c'è più di un file .md e nessuno si chiama index.md, segnala un errore
                if len(md_files) > 1 and 'index.md' not in md_files:
                    flash('Errore: Più file .md trovati, ma nessuno è index.md!', 'error')
                    return redirect(url_for('admin'))

                # Se c'è un solo file .md, rinominalo in index.md
                if len(md_files) == 1:
                    os.rename(
                        os.path.join(sottoargomento_path, md_files[0]),
                        os.path.join(sottoargomento_path, 'index.md')
                    )

                # Se c'è già un file index.md, non fare nulla (è già corretto)
                flash('File zip caricato con successo e contenuto estratto!', 'success')
            else:
                # Se è un file singolo, salvalo nella cartella del sottoargomento
                file.save(os.path.join(sottoargomento_path, 'index.md'))

            # Aggiorna l'elenco degli argomenti nel file JSON
            argomenti = load_topics()
            if argomento_folder not in argomenti:
                argomenti[argomento_folder] = {
                    'label': argomento_label,
                    'folder': argomento_folder,
                    'sottoargomenti': []
                }
            if sottoargomento_folder not in [s['folder'] for s in argomenti[argomento_folder]['sottoargomenti']]:
                argomenti[argomento_folder]['sottoargomenti'].append({
                    'label': sottoargomento_label,
                    'folder': sottoargomento_folder
                })
            save_topics(argomenti)

            return redirect(url_for('admin'))

    argomenti = load_topics()
    return render_template('admin.html', argomenti=argomenti)


if __name__ == '__main__':
    if not os.path.exists(app.config['DATA_FOLDER']):
        os.makedirs(app.config['DATA_FOLDER'])
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if not os.path.exists(app.config['DATA_FOLDER'] + '/argomenti.json'):
        save_topics({})
    app.run(host='0.0.0.0', port=5000)
