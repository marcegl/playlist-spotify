# Gestor de Playlists de Spotify con IA

Este proyecto te permite crear o actualizar playlists de Spotify de forma dinámica utilizando listas de canciones generadas, por ejemplo, por un Modelo de Lenguaje Grande (LLM) como Gemini, ChatGPT, etc. Simplemente describe la playlist que deseas a tu IA favorita, obtén la lista en formato JSON y usa esta herramienta para crearla en tu cuenta de Spotify.

## Características

*   **Creación de Playlists Nuevas:** Genera una nueva playlist en tu cuenta de Spotify.
*   **Actualización de Playlists Existentes:** Añade canciones a una playlist que ya tengas.
*   **Múltiples Fuentes de Input:**
    *   Sube un archivo `.json` con la lista de tracks.
    *   Pega directamente el contenido JSON en la interfaz web.
*   **Manejo Inteligente de Duplicados:** Al añadir a una playlist existente, puedes elegir:
    *   Añadir todas las canciones encontradas (incluso si ya están).
    *   Añadir solo las canciones que aún no están en la playlist.
*   **Búsqueda Flexible:** Intenta encontrar las canciones en Spotify usando la información proporcionada (track, artista, álbum, año, etc.) con reintentos automáticos.
*   **Interfaz Web Sencilla:** Gestiona todo el proceso fácilmente desde tu navegador.

## Flujo de Trabajo con LLM (Ejemplo)

La idea principal es aprovechar la capacidad de los LLMs para generar listas de música basadas en descripciones creativas.

1.  **Crea tu Prompt:** Pídele a tu LLM preferido que genere una lista de canciones. Sé descriptivo sobre el ambiente, género, o la secuencia que buscas. **¡Importante!** Asegúrate de incluir al final del prompt la instrucción sobre el formato de salida.

    *Ejemplo de Prompt:*

    ```text
    Crea una lista de reproducción con música genial para disfrutar con amigos en una reunión. Quiero que empiece con canciones energéticas y animadas para levantar el ánimo durante la primera hora, y luego cambie a algo más chill y relajado para conversar, pero manteniendo un buen rollo.

    **Instrucción Obligatoria (añadir al final de tu prompt):**
    El output debe ser en formato JSON, específicamente un array de objetos. Cada objeto representa una canción y debe contener obligatoriamente la clave "track" con el nombre de la canción. Opcionalmente, puede incluir las claves "artist", "album" y "year".
    ```

2.  **Obtén el JSON:** El LLM debería devolverte un resultado similar a este:

    ```json
    [
      {
        "track": "Don't Stop Me Now",
        "artist": "Queen",
        "year": 1978
      },
      {
        "track": "Uptown Funk",
        "artist": "Mark Ronson ft. Bruno Mars",
        "year": 2014
      },
      {
        "track": "Good Days",
        "artist": "SZA"
      },
      {
        "track": "Amber",
        "artist": "311",
        "album": "From Chaos"
      }
    ]
    ```

3.  **Usa esta Herramienta:**
    *   Ejecuta la aplicación `Spotify Playlist Manager`.
    *   Abre la interfaz web.
    *   Pega el JSON obtenido en el área de texto correspondiente (o guarda el JSON en un archivo `.json` y súbelo).
    *   Configura tus credenciales de Spotify.
    *   Elige si quieres crear una nueva playlist o añadir a una existente.
    *   ¡Procesa y disfruta!

## Requisitos

*   **Python:** Versión 3.7 o superior.
*   **Dependencias:** Las librerías listadas en `requeriments.txt`. Puedes instalarlas con pip.
*   **Credenciales de API de Spotify:** Necesitas registrar una aplicación en el [Dashboard de Desarrollador de Spotify](https://developer.spotify.com/dashboard/) para obtener:
    *   `Client ID`: Identificador único de tu aplicación.
    *   `Client Secret`: Clave secreta para tu aplicación.
    *   `Redirect URI`: La URI a la que Spotify redirigirá después de la autenticación. **Importante:** Debes añadir la URI que uses en la configuración de tu aplicación en el dashboard de Spotify. Por defecto, esta herramienta usa `http://localhost:5000/callback`, pero puedes cambiarla.

## Instalación

1.  **Clona el repositorio (si aplica):**
    ```bash
    git clone <url-del-repositorio>
    cd <directorio-del-proyecto>
    ```
2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
3.  **Instala las dependencias:**
    ```bash
    pip install -r requeriments.txt
    ```
4.  **(Opcional) Crea un archivo `.env`:** Para no tener que introducir las credenciales cada vez, puedes crear un archivo llamado `.env` en la raíz del proyecto con el siguiente contenido:
    ```env
    SPOTIFY_CLIENT_ID=TU_CLIENT_ID
    SPOTIFY_CLIENT_SECRET=TU_CLIENT_SECRET
    SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
    ```
    *Reemplaza `TU_CLIENT_ID` y `TU_CLIENT_SECRET` con tus credenciales.*

## Uso

1.  **Ejecuta la aplicación Flask:**
    ```bash
    flask run
    ```
    O alternativamente:
    ```bash
    python app.py
    ```
    La aplicación estará disponible por defecto en `http://localhost:5000`.

2.  **Abre tu navegador:** Ve a `http://localhost:5000`.

3.  **Configura:**
    *   Haz clic en "Mostrar/Ocultar Credenciales Spotify" e introduce tu `Client ID`, `Client Secret` y `Redirect URI` (si no usaste el archivo `.env`).
    *   Elige si quieres "Crear nueva playlist" (y dale un nombre) o "Añadir a playlist existente" (y pega la URL de la playlist).
    *   Selecciona la fuente de los tracks: "Subir archivo JSON" o "Pegar contenido JSON". Proporciona el archivo o pega el texto JSON generado por el LLM.
    *   Si elegiste añadir a una playlist existente, selecciona cómo quieres manejar los duplicados.

4.  **Procesa:** Haz clic en "Procesar Playlist".

5.  **Autenticación (la primera vez):** Es posible que se te redirija a Spotify para autorizar la aplicación. Inicia sesión y concede los permisos. Serás redirigido de nuevo a la aplicación. Puede que necesites volver a enviar el formulario después de la autenticación inicial.

6.  **Resultados:** Verás un resumen de las canciones añadidas y las que no se pudieron encontrar, junto con un enlace a la playlist creada o actualizada.

## Formato JSON Esperado

Recuerda, la aplicación espera un array JSON `[...]` donde cada elemento es un objeto `{...}`. Cada objeto debe tener al menos la clave `"track"`.

```json
[
  {
    "track": "Nombre de la Canción 1",
    "artist": "Artista Opcional 1",
    "album": "Álbum Opcional 1",
    "year": 2023
  },
  {
    "track": "Nombre de la Canción 2"
  },
  {
    "track": "Nombre Canción 3",
    "artist": "Artista Opcional 3"
  }
]
``` 