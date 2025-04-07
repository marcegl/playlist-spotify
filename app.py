import os
import json
from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Importar la lógica de Spotify
from spotify_logic import process_tracks

# Cargar variables de entorno iniciales (si existen)
load_dotenv()

app = Flask(__name__)
# Necesitamos una clave secreta para usar sesiones en Flask
app.secret_key = os.urandom(24)

# Carpeta para subir archivos temporalmente
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Asegurarse de que la carpeta de subidas exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Recoger datos del formulario
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
        redirect_uri = request.form.get('redirect_uri')
        playlist_option = request.form.get('playlist_option') # 'new' or 'existing'
        playlist_name = request.form.get('playlist_name')
        playlist_url = request.form.get('playlist_url')
        track_source = request.form.get('track_source') # 'file' or 'paste'
        json_content_paste = request.form.get('json_content')
        duplicate_option = request.form.get('duplicate_option', 'add_all') # 'add_all' or 'add_new'

        # Validar credenciales básicas
        if not all([client_id, client_secret, redirect_uri]):
            flash("Por favor, completa las credenciales de Spotify.", "error")
            return redirect(url_for('index'))

        # Validar opciones de playlist
        if playlist_option == 'new' and not playlist_name:
             flash("Por favor, introduce un nombre para la nueva playlist.", "error")
             return redirect(url_for('index'))
        if playlist_option == 'existing' and not playlist_url:
            flash("Por favor, introduce la URL de la playlist existente.", "error")
            return redirect(url_for('index'))

        # Manejar fuente de tracks (archivo o texto pegado)
        tracks_data = None
        filepath_to_remove = None # Para borrar el archivo si se subió

        if track_source == 'file':
            if 'json_file' not in request.files:
                flash('No se encontró el archivo JSON.', "error")
                return redirect(url_for('index'))
            file = request.files['json_file']
            if file.filename == '':
                flash('No se seleccionó ningún archivo JSON.', "error")
                return redirect(url_for('index'))

            if file and file.filename.endswith('.json'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                filepath_to_remove = filepath # Marcar para borrar después

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        tracks_data = json.load(f)
                except json.JSONDecodeError:
                    flash("Error al leer el archivo JSON. Asegúrate de que tenga el formato correcto.", "error")
                    if filepath_to_remove and os.path.exists(filepath_to_remove):
                        os.remove(filepath_to_remove)
                    return redirect(url_for('index'))
                except Exception as e:
                     flash(f"Ocurrió un error inesperado al leer el archivo: {e}", "error")
                     if filepath_to_remove and os.path.exists(filepath_to_remove):
                         os.remove(filepath_to_remove)
                     return redirect(url_for('index'))
            else:
                 flash("Por favor, sube un archivo .json válido.", "error")
                 return redirect(url_for('index'))

        elif track_source == 'paste':
            if not json_content_paste:
                 flash("Por favor, pega el contenido JSON de los tracks.", "error")
                 return redirect(url_for('index'))
            try:
                tracks_data = json.loads(json_content_paste)
                if not isinstance(tracks_data, list): # Simple validación de formato
                     raise ValueError("El JSON debe ser una lista de objetos.")
            except json.JSONDecodeError:
                flash("Error al decodificar el JSON pegado. Asegúrate de que el formato sea correcto.", "error")
                return redirect(url_for('index'))
            except ValueError as ve:
                 flash(f"Error en el contenido JSON: {ve}", "error")
                 return redirect(url_for('index'))
            except Exception as e:
                 flash(f"Ocurrió un error inesperado al procesar el JSON pegado: {e}", "error")
                 return redirect(url_for('index'))

        else:
            # Esto no debería ocurrir si el HTML está bien
             flash("Selecciona una fuente para los tracks (archivo o pegar).", "error")
             return redirect(url_for('index'))

        # Si llegamos aquí, tenemos tracks_data
        if tracks_data is None:
            flash("No se pudieron obtener los datos de los tracks.", "error")
            if filepath_to_remove and os.path.exists(filepath_to_remove): # Limpieza si hubo error antes
                os.remove(filepath_to_remove)
            return redirect(url_for('index'))

        # Limpiar archivo subido si existe, ya hemos leído su contenido
        if filepath_to_remove and os.path.exists(filepath_to_remove):
            os.remove(filepath_to_remove)

        # Llamar a la lógica de Spotify
        result = process_tracks(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            tracks_data=tracks_data,
            playlist_name=playlist_name if playlist_option == 'new' else None,
            playlist_url=playlist_url if playlist_option == 'existing' else None,
            duplicate_option=duplicate_option if playlist_option == 'existing' else 'add_all' # Pasar opción de duplicados solo si es relevante
        )

        if "error" in result:
            flash(f"Error en el proceso de Spotify: {result['error']}", "error")
        else:
            # Guardar resultado en sesión para mostrar en la página de resultados
            session['result'] = result
            return redirect(url_for('results'))

    # Método GET: mostrar el formulario
    # Cargar credenciales desde .env si existen, para pre-rellenar el formulario
    initial_credentials = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID', ''),
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET', ''),
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI', '')
    }
    return render_template('index.html', credentials=initial_credentials)

@app.route('/results')
def results():
    result = session.pop('result', None)
    if not result:
        # Si no hay resultados en la sesión, redirigir a la página principal
        return redirect(url_for('index'))
    return render_template('results.html', result=result)

# Ruta para manejar la autenticación de Spotify (callback)
# Esta ruta es necesaria para que SpotifyOAuth funcione
@app.route('/callback')
def callback():
    # Spotipy maneja el intercambio de código por token automáticamente
    # a través de su auth_manager cuando se hace la primera llamada API.
    # Normalmente redirigimos al usuario a una página de éxito o de vuelta a la app.
    # En este caso, como el proceso se inicia desde el formulario principal,
    # podemos simplemente redirigir allí o mostrar un mensaje.
    flash("Autenticación con Spotify completada. Puedes volver a enviar el formulario.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Usar un puerto diferente al 8080 si ese es tu redirect URI
    # para evitar conflictos.
    app.run(debug=True, port=5000) 