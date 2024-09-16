import os

from flask import Flask, render_template, request, abort, send_from_directory
from flask_basicauth import BasicAuth
from markdown import markdown

from admin import method_upload_file, method_rename_argomento, method_rename_sottoargomento, method_delete_argomento, \
    method_delete_sottoargomento
from topics import load_topics, save_topics
from utils import DATA_FOLDER, UPLOAD_FOLDER, allowed_media_file

app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME', 'admin')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD', 'password')

app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')  # Anche la chiave segreta può essere impostata dall'ambiente
print("Config:", app.config)

basic_auth = BasicAuth(app)


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
    file_path = os.path.join(UPLOAD_FOLDER, argomento_folder, sottoargomento, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = markdown(f.read())

    # Cerca il CSS opzionale nella cartella dell'argomento o sottoargomento
    css_file = None
    css_path = os.path.join(UPLOAD_FOLDER, argomento_folder, 'style.css')
    if os.path.exists(css_path):
        css_file = f'{argomento_folder}/style.css'

    sottoargomento_css_path = os.path.join(UPLOAD_FOLDER, argomento_folder, sottoargomento, 'style.css')
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
    sottoargomento_path = os.path.join(UPLOAD_FOLDER, argomento, sottoargomento)

    # Controlla se il file esiste
    if os.path.exists(os.path.join(sottoargomento_path, filename)):
        return send_from_directory(sottoargomento_path, filename)
    else:
        # Se il file non esiste, restituisce un errore 404
        abort(404, description="File non trovato")


@app.route('/admin', methods=['GET', 'POST'])
@basic_auth.required
def admin():
    argomenti = load_topics()
    return render_template('admin.html', argomenti=argomenti)


@app.route('/admin/upload', methods=['POST'])
@basic_auth.required
def upload_file():
    return method_upload_file()


@app.route('/admin/rename_argomento', methods=['POST'])
@basic_auth.required
def rename_argomento():
    return method_rename_argomento()


@app.route('/admin/rename_sottoargomento', methods=['POST'])
@basic_auth.required
def rename_sottoargomento():
    return method_rename_sottoargomento()


@app.route('/admin/delete_argomento', methods=['POST'])
@basic_auth.required
def delete_argomento():
    return method_delete_argomento()


@app.route('/admin/delete_sottoargomento', methods=['POST'])
@basic_auth.required
def delete_sottoargomento():
    return method_delete_sottoargomento()


if __name__ == '__main__':
    print("Creo", DATA_FOLDER, UPLOAD_FOLDER)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if not os.path.exists(DATA_FOLDER + '/argomenti.json'):
        save_topics({})
    app.run(host='0.0.0.0', port=5000)
