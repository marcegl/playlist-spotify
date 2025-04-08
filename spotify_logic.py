import os
import json
import spotipy
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
    try:
        result = sp.search(q=query, type="track", limit=1)
        items = result.get("tracks", {}).get("items", [])
        if items:
            return items[0]["uri"]
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error buscando track '{query}': {e}")
    return None

def search_with_retry(sp: spotipy.Spotify, track_info: dict) -> str:
    """
    1. Intenta la búsqueda "avanzada".
    2. Reintenta con track + artist.
    3. Reintenta con solo track.
    """
    advanced_query = build_advanced_query(track_info)
    uri = search_track(sp, advanced_query)
    if uri:
        return uri

    if track_info.get("track") and track_info.get("artist"):
        fallback_query_1 = f'track:"{track_info["track"]}" artist:"{track_info["artist"]}"'
        uri = search_track(sp, fallback_query_1)
        if uri:
            return uri

    if track_info.get("track"):
        fallback_query_2 = f'track:"{track_info["track"]}"'
        uri = search_track(sp, fallback_query_2)
        if uri:
            return uri

    return None

# ==========================
#  Función principal adaptada
# ==========================

def process_tracks(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    tracks_data: list[dict],
    playlist_name: str,
    playlist_url: str = None,
    duplicate_option: str = 'add_all', # Opciones: 'add_all', 'add_new'
    playlist_description: str = None # Nueva descripción personalizada
) -> dict:
    """
    Procesa una lista de tracks, los busca en Spotify y los añade a una playlist.
    Si se proporciona playlist_url, añade a esa playlist existente.
    Si no, crea una nueva playlist con playlist_name.
    duplicate_option controla si se añaden tracks ya existentes ('add_all') o solo nuevos ('add_new').
    Retorna un diccionario con los resultados: {found_uris: [], not_found_tracks: [], playlist_url: str}.
    """
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="playlist-modify-public playlist-modify-private"
            )
        )
        user_id = sp.current_user()["id"]
    except Exception as e:
        return {"error": f"Error de autenticación con Spotify: {e}"}

    found_track_uris = []
    not_found_tracks = []
    existing_track_uris = set() # Para guardar URIs existentes si es necesario

    for track_info in tracks_data:
        uri = search_with_retry(sp, track_info)
        if uri:
            found_track_uris.append(uri)
        else:
            # Guardamos la info original para mostrarla al usuario
            not_found_tracks.append({
                "track": track_info.get("track", "N/A"),
                "artist": track_info.get("artist", "N/A"),
                "album": track_info.get("album", "N/A")
            })

    target_playlist_id = None
    final_playlist_url = None

    if playlist_url:
        try:
            # Extraer ID de la URL
            playlist_id = playlist_url.split('/')[-1].split('?')[0]
            # Verificar si la playlist existe
            playlist_details = sp.playlist(playlist_id, fields='id,external_urls.spotify')
            if playlist_details:
                 target_playlist_id = playlist_id
                 final_playlist_url = playlist_details["external_urls"]["spotify"]

                 # Si la opción es añadir solo nuevos, obtener tracks existentes
                 if duplicate_option == 'add_new':
                     print(f"Opción 'add_new' seleccionada. Obteniendo tracks existentes de la playlist {target_playlist_id}...")
                     offset = 0
                     while True:
                         results = sp.playlist_items(target_playlist_id,
                                                     fields='items(track(uri)),next',
                                                     additional_types=['track'],
                                                     offset=offset)
                         items = results.get('items', [])
                         if not items:
                             break
                         for item in items:
                             if item and item.get('track') and item['track'].get('uri'):
                                 existing_track_uris.add(item['track']['uri'])
                         if results.get('next'):
                             offset += len(items)
                         else:
                             break
                     print(f"Se encontraron {len(existing_track_uris)} tracks existentes en la playlist.")

            else:
                return {"error": f"No se encontró o no se tiene acceso a la playlist: {playlist_url}"}
        except spotipy.exceptions.SpotifyException as se:
            if se.http_status == 404:
                 return {"error": f"Playlist no encontrada: {playlist_url}"}
            else:
                 return {"error": f"Error de Spotify al obtener playlist ({se.http_status}): {se.msg}"}
        except Exception as e:
            return {"error": f"Error al procesar URL de playlist existente: {e}"}
    else:
        # Crear nueva playlist
        try:
            description_to_use = playlist_description if playlist_description else "Playlist creada desde JSON vía web"
            new_playlist = sp.user_playlist_create(
                user=user_id,
                name=playlist_name,
                public=True,
                description=description_to_use # Usar descripción
            )
            target_playlist_id = new_playlist["id"]
            final_playlist_url = new_playlist["external_urls"]["spotify"]
        except Exception as e:
            return {"error": f"Error creando la nueva playlist: {e}"}

    # Filtrar URIs si es necesario (opción 'add_new')
    uris_to_add = found_track_uris
    if playlist_url and duplicate_option == 'add_new':
        uris_to_add = [uri for uri in found_track_uris if uri not in existing_track_uris]
        print(f"Filtrando URIs. Original: {len(found_track_uris)}, A añadir: {len(uris_to_add)}")

    # Agregar tracks a la playlist (nueva o existente)
    if uris_to_add and target_playlist_id:
        print(f"Añadiendo {len(uris_to_add)} tracks a la playlist {target_playlist_id}...")
        try:
            # Spotify permite añadir 100 items por llamada
            for i in range(0, len(uris_to_add), 100):
                batch = uris_to_add[i:i+100]
                sp.playlist_add_items(target_playlist_id, batch)
                print(f"  ...añadido lote de {len(batch)} tracks.")
        except Exception as e:
             return {"error": f"Error añadiendo tracks a la playlist {target_playlist_id}: {e}"}

    # Actualizar el contador de tracks encontrados basado en lo que realmente se intentó añadir
    final_added_count = len(uris_to_add)

    return {
        "found_tracks_count": final_added_count, # Ahora refleja los tracks realmente añadidos
        "not_found_tracks": not_found_tracks,
        "playlist_url": final_playlist_url
    } 