from libs.notion import NotionClient
from libs.getdb import extract_album_info  
from libs.utils import Utils 

from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session
from flask import send_from_directory
import pandas as pd
import random
import json

# Read Notion config
with open("notion-keys.json", "r") as f:
    notion_keys = json.load(f)

# APP Secret 
APP_SECRET = notion_keys["APP_SECRET"]

# create instance of NotionClient
notion_client = NotionClient(NOTION_TOKEN = notion_keys["NOTION_TOKEN"])

# Get DB
album_db = notion_client.get_db_pages(DATABASE_ID=notion_keys["RATING_DATABASE_ID"])

# Load album data
albums_data = [extract_album_info(page) for page in album_db]

# Query Dataframe
df = pd.DataFrame(albums_data)

# Some preprocessing
df["unique_genre"] = df["Genre"].apply(lambda x: Utils.map_genres(x))

# Non costruiamo più un path assoluto, ma teniamo solo nome file o URL
# In Notion: se c’è Picname → è un file locale in /static/covers/, altrimenti URL in Cover
df["final_cover"] = df.apply(
    lambda row: row["Picname"] if pd.notna(row["Picname"]) else row["Cover"], axis=1
)

app = Flask(__name__)
app.secret_key = notion_keys["APP_SECRET"]  # needed for session

# 🔧 Configura Flask-Session per salvare su filesystem
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = './.flask_session/'  # o una cartella a tua scelta

Session(app)

COVERS_PATH = notion_keys["COVER_PATH"]

# We tell flask to use the given path as static/ folder to allows the Browser to access
# to album covers
@app.route('/covers/<path:filename>')
def covers(filename):
    return send_from_directory(COVERS_PATH, filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    genres = sorted(df['unique_genre'].dropna().unique())
    languages = sorted(df['Language'].dropna().unique())

    # 🧹 Clean up old game session data
    for key in ['round', 'albums', 'next_round', 'battle_index', 'pair', 'winner']:
        session.pop(key, None)

    if request.method == 'POST':
        num_albums = int(request.form['num_albums'])
        selected_genres = request.form.getlist('genres')
        selected_languages = request.form.getlist('languages')

        # Filter dataframe
        filtered_df = df.copy()
        if selected_genres:
            filtered_df = filtered_df[filtered_df['unique_genre'].isin(selected_genres)]
        if selected_languages:
            filtered_df = filtered_df[filtered_df['Language'].isin(selected_languages)]

        if len(filtered_df) < num_albums:
            return render_template('index.html', error="Not enough albums for the selected filters.",
                                   genres=genres, languages=languages)

        selected = filtered_df.sample(num_albums).to_dict(orient='records')
        
        session['round'] = 1
        session['albums'] = selected
        session['next_round'] = []
        session['battle_index'] = 0
        session['pair'] = []
        return redirect(url_for('battle'))
    return render_template('index.html', genres=genres, languages=languages)

@app.route('/battle', methods=['GET', 'POST'])
def battle():
    # Controllo iniziale
    if 'albums' not in session or not session['albums']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Recupera indice e salva il vincitore del duello corrente
        winner_index = int(request.form['choice'])
        session['next_round'].append(session['pair'][winner_index])
        session['battle_index'] += 2
        return redirect(url_for('battle'))

    # GET
    albums = session['albums']
    battle_index = session['battle_index']

    # Se abbiamo finito gli scontri del round corrente
    if battle_index >= len(albums):
        if len(session['next_round']) == 1:
            # Unico vincitore
            session['winner'] = session['next_round'][0]
            return redirect(url_for('winner'))
        elif len(session['next_round']) < 2:
            # Errore: impossibile continuare
            return redirect(url_for('index'))

        # Prepara il prossimo round
        session['albums'] = session['next_round']
        session['next_round'] = []
        session['battle_index'] = 0
        session['round'] += 1
        return redirect(url_for('battle'))

    # Se ancora dentro il round corrente, mostra il prossimo scontro
    pair = albums[battle_index:battle_index + 2]
    session['pair'] = pair
    return render_template('round.html', pair=pair, round_num=session['round'])

@app.route('/winner')
def winner():
    album = session.get('winner')
    if not album:  # fallback in caso di problemi
        album = session['albums'][0]
    return render_template('winner.html', album=album)
