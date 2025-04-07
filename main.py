import os
import json
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

# ==========================
#    Funciones auxiliares
# ==========================

def build_advanced_query(track_info: dict) -> str:
    """
    Construye la cadena de búsqueda avanzada a partir de
    los campos disponibles en track_info.
    """
    query_parts = []

    # Mapeo directo campo -> formateo
    if track_info.get("track"):
        query_parts.append(f'track:"{track_info["track"]}"')
    if track_info.get("artist"):
        query_parts.append(f'artist:"{track_info["artist"]}"')
    if track_info.get("album"):
        query_parts.append(f'album:"{track_info["album"]}"')
    if track_info.get("year"):
        query_parts.append(f'year:{track_info["year"]}')
    if track_info.get("upc"):
        query_parts.append(f'upc:{track_info["upc"]}')
    if track_info.get("tag"):
        query_parts.append(f'tag:{track_info["tag"]}')
    if track_info.get("isrc"):
        query_parts.append(f'isrc:{track_info["isrc"]}')
    if track_info.get("genre"):
        query_parts.append(f'genre:"{track_info["genre"]}"')

    return " ".join(query_parts).strip()

def search_track(sp: spotipy.Spotify, query: str) -> str:
    """
    Realiza la búsqueda de un track en Spotify (limit=1).
    Retorna el URI si existe o None en caso contrario.
    """
    if not query:
        return None
    result = sp.search(q=query, type="track", limit=1)
    items = result.get("tracks", {}).get("items", [])
    if items:
        return items[0]["uri"]
    return None

def search_with_retry(sp: spotipy.Spotify, track_info: dict) -> str:
    """
    1. Intenta la búsqueda "avanzada" usando todos los campos disponibles.
    2. En caso de no encontrar resultados, reintenta con track + artist.
    3. Si aún no encuentra, reintenta con solo track.
    Retorna el URI si lo encuentra, o None si no.
    """
    # 1. Búsqueda avanzada
    advanced_query = build_advanced_query(track_info)
    uri = search_track(sp, advanced_query)

    # Si se encontró, retornamos
    if uri:
        return uri

    # 2. Reintento: track + artist
    if track_info.get("track") and track_info.get("artist"):
        fallback_query_1 = f'track:"{track_info["track"]}" artist:"{track_info["artist"]}"'
        uri = search_track(sp, fallback_query_1)
        if uri:
            return uri

    # 3. Reintento final: solo track
    if track_info.get("track"):
        fallback_query_2 = f'track:"{track_info["track"]}"'
        uri = search_track(sp, fallback_query_2)
        if uri:
            return uri

    # No se encontró de ningún modo
    return None

# ==========================
#  Función principal
# ==========================

def create_spotify_playlist_from_file(json_file_path: str):
    """
    Lee un archivo JSON (ej. tracks.json) con un array de canciones.
      Cada objeto puede contener: 
          album, artist, track, year, upc, tag, isrc, genre.
    Crea una playlist y agrega los tracks encontrados.
    Si no encuentra un track con la búsqueda avanzada, hace un retry con:
      (1) track + artist, (2) solo track.
    Informa en el log si hay canciones que no se encontraron tras reintentos.
    """

    # 1. Cargar variables de entorno desde .env
    load_dotenv()
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

    # 2. Inicializar Spotipy con OAuth
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="playlist-modify-public playlist-modify-private"
        )
    )

    # Obtener ID de usuario
    user_id = sp.current_user()["id"]

    # 3. Leer el contenido del JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        tracks_data = json.load(f)

    # 4. Crear la playlist
    playlist_name = "My Dynamic JSON Playlist evolution"
    new_playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=True,
        description="Playlist creada a partir de un archivo JSON"
    )

    found_track_uris = []
    not_found_tracks = []

    # 5. Procesar cada track e intentar encontrar su URI
    for track_info in tracks_data:
        uri = search_with_retry(sp, track_info)
        if uri:
            found_track_uris.append(uri)
        else:
            not_found_tracks.append(track_info)

    # 6. Agregar los tracks encontrados a la playlist
    if found_track_uris:
        sp.playlist_add_items(new_playlist["id"], found_track_uris)

    # 7. Logs de resultado
    print(f"\nPlaylist creada: {new_playlist['name']}")
    print(f"Tracks agregados: {len(found_track_uris)}")
    print("URL de la playlist:", new_playlist["external_urls"]["spotify"])

    if not_found_tracks:
        print("\nNo se encontraron coincidencias para los siguientes items:")
        for nf in not_found_tracks:
            print(" -", nf)

# ==========================
#   Punto de entrada
# ==========================
if __name__ == "__main__":
    create_spotify_playlist_from_file("tracks.json")