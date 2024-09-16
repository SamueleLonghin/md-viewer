import os
import shutil
import zipfile

from flask import request, flash, redirect, url_for
from werkzeug.utils import secure_filename

from topics import save_topics, load_topics
from utils import UPLOAD_FOLDER, sanitize_folder_name, allowed_file


def method_upload_file():
    argomento_label = request.form['argomento']
    sottoargomento_label = request.form['sottoargomento']
    file = request.files['file']

    # Carica gli argomenti esistenti
    argomenti = load_topics()

    # Controlla se l'argomento esiste già cercando per label
    argomento_esistente = None
    for folder_name, argomento in argomenti.items():
        print(argomenti)
        if argomento['label'].lower() == argomento_label.lower():
            argomento_esistente = argomento
            break

    if argomento_esistente:
        # Se l'argomento esiste, usiamo la sua 'folder'
        argomento_folder = argomento_esistente['folder']
    else:
        # Se l'argomento non esiste, creiamo una nuova 'folder' basata sulla label
        argomento_folder = sanitize_folder_name(argomento_label)
        argomenti[argomento_folder] = {
            'label': argomento_label,
            'folder': argomento_folder,
            'sottoargomenti': []
        }

    # Verifica se il sottoargomento esiste già
    sottoargomento_folder = sanitize_folder_name(sottoargomento_label)
    if argomento_esistente:
        if any(s['folder'] == sottoargomento_folder for s in argomento_esistente['sottoargomenti']):
            flash(f"Il sottoargomento '{sottoargomento_label}' esiste già per l'argomento '{argomento_label}'.",
                  'danger')
            return redirect(url_for('admin'))

    # Controllo che l'estensione vada bene
    if not file or not allowed_file(file.filename):
        flash(f"Il formato del file non è consentito, cortesemente carica solamete file MarkDown o ZIP", 'danger')
        return redirect(url_for('admin'))
    # Crea le cartelle per l'argomento e il sottoargomento se non esistono
    argomento_path = os.path.join(UPLOAD_FOLDER, argomento_folder)
    sottoargomento_path = os.path.join(argomento_path, sottoargomento_folder)
    os.makedirs(sottoargomento_path, exist_ok=True)

    # Gestisci il caricamento del file (logica rimasta invariata)
    filename = secure_filename(file.filename)
    if filename.endswith('.zip'):
        temp_extract_path = os.path.join(sottoargomento_path, 'temp')
        try:
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_path)
            extracted_items = [f for f in os.listdir(temp_extract_path) if not f.startswith('__')]
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_path, extracted_items[0])):
                intermedio_path = os.path.join(temp_extract_path, extracted_items[0])
                for item in os.listdir(intermedio_path):
                    shutil.move(os.path.join(intermedio_path, item), sottoargomento_path)
            else:
                for item in extracted_items:
                    shutil.move(os.path.join(temp_extract_path, item), sottoargomento_path)
            shutil.rmtree(temp_extract_path)

            md_files = [f for f in os.listdir(sottoargomento_path) if f.endswith('.md')]
            if not md_files:
                flash('Errore: Nessun file .md trovato nel file zip!', 'danger')
                return redirect(url_for('admin'))
            if len(md_files) > 1 and 'index.md' not in md_files:
                flash('Errore: Più file .md trovati, ma nessuno è index.md!', 'danger')
                return redirect(url_for('admin'))
            if len(md_files) == 1:
                os.rename(os.path.join(sottoargomento_path, md_files[0]), os.path.join(sottoargomento_path, 'index.md'))
            flash('File zip caricato con successo e contenuto estratto!', 'success')
        finally:
            if os.path.exists(temp_extract_path):
                shutil.rmtree(temp_extract_path)
    else:
        file.save(os.path.join(sottoargomento_path, 'index.md'))

    # Aggiorna l'elenco degli argomenti nel file JSON
    if not argomento_esistente:
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


def method_rename_argomento():
    argomento = request.form['argomento']
    nuovo_nome = request.form['nuovo_nome']

    argomenti = load_topics()
    if argomento in argomenti:
        argomenti[argomento]['label'] = nuovo_nome
        save_topics(argomenti)
        flash(f"Argomento '{argomento}' rinominato in '{nuovo_nome}'", 'success')

    return redirect(url_for('admin'))


def method_rename_sottoargomento():
    argomento = request.form['argomento']
    sottoargomento = request.form['sottoargomento']
    nuovo_nome = request.form['nuovo_nome']

    argomenti = load_topics()
    for sotto in argomenti[argomento]['sottoargomenti']:
        if sotto['folder'] == sottoargomento:
            sotto['label'] = nuovo_nome
            save_topics(argomenti)
            flash(f"Sottoargomento '{sottoargomento}' rinominato in '{nuovo_nome}'", 'success')
            break

    return redirect(url_for('admin'))


def method_delete_argomento():
    argomento = request.form['argomento']

    argomenti = load_topics()
    if argomento in argomenti:
        # Rimuovi dal file system
        argomento_path = os.path.join(UPLOAD_FOLDER, argomenti[argomento]['folder'])
        if os.path.exists(argomento_path):
            shutil.rmtree(argomento_path)
        # Rimuovi dal file JSON
        del argomenti[argomento]
        save_topics(argomenti)
        flash(f"Argomento '{argomento}' rimosso", 'success')

    return redirect(url_for('admin'))


def method_delete_sottoargomento():
    argomento = request.form['argomento']
    sottoargomento = request.form['sottoargomento']

    argomenti = load_topics()
    argomento_path = os.path.join(UPLOAD_FOLDER, argomenti[argomento]['folder'], sottoargomento)
    if os.path.exists(argomento_path):
        shutil.rmtree(argomento_path)

    # Rimuovi dal file JSON
    argomenti[argomento]['sottoargomenti'] = [
        sotto for sotto in argomenti[argomento]['sottoargomenti'] if sotto['folder'] != sottoargomento
    ]
    save_topics(argomenti)
    flash(f"Sottoargomento '{sottoargomento}' rimosso", 'success')

    return redirect(url_for('admin'))
