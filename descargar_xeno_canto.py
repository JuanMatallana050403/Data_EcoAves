import requests
import json
import os
import pandas as pd
from tqdm import tqdm
import time

# Configuración
API_KEY = "0d59b24ba612026fb4efda058eb96ff5fc61b7f0"  # ¡IMPORTANTE! Reemplaza esto con tu API Key de Xeno-Canto
MAX_PER_SPECIES = 40 # Número máximo de audios por especie (Ideal para IA ligero)
QUALITIES_ACCEPTED = ['A', 'B']  # Solo queremos audios de alta calidad
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
AUDIO_DIR = os.path.join(DATA_DIR, 'dataset_audios')
METADATA_DIR = os.path.join(DATA_DIR, 'metadata')

# Crear carpetas si no existen
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

def obtener_metadatos_api(query):
    if not API_KEY:
        print("ERROR: Falta configurar el API_KEY. Por favor, obtenla en tu cuenta de Xeno-Canto y ponla en el script.")
        return []
        
    print(f"Consultando API de Xeno-Canto para: {query}")
    base_url = "https://xeno-canto.org/api/3/recordings"
    
    # Primera petición para saber cuántas páginas hay
    response = requests.get(base_url, params={"query": query, "key": API_KEY})
    if response.status_code != 200:
        print(f"Error al conectar con la API (Código {response.status_code})")
        return []
    
    data = response.json()
    num_pages = data.get('numPages', 1)
    recordings = data.get('recordings', [])
    
    print(f"Se encontraron {data.get('numRecordings')} grabaciones en {num_pages} páginas.")
    
    # Si hay más de una página, las iteramos (limitado a unas cuantas para no saturar si son muchas)
    # Para este script, recorreremos todas las páginas disponibles
    for page in range(2, num_pages + 1):
        print(f"Obteniendo página {page} de {num_pages}...")
        resp = requests.get(base_url, params={"query": query, "page": page, "key": API_KEY})
        if resp.status_code == 200:
            recordings.extend(resp.json().get('recordings', []))
        time.sleep(1) # Pausa amigable para no saturar el servidor
        
    return recordings

def filtrar_y_descargar(recordings):
    species_count = {}
    valid_recordings = []
    
    print("\nFiltrando audios por calidad y límite por especie...")
    for rec in recordings:
        # Nombre científico de la especie para la carpeta
        species_name = f"{rec['gen']}_{rec['sp']}".replace(" ", "_")
        quality = rec.get('q', '')
        
        # Filtro de calidad
        if quality not in QUALITIES_ACCEPTED:
            continue
            
        if species_name not in species_count:
            species_count[species_name] = 0
            
        # Filtro de cantidad máxima por especie
        if species_count[species_name] < MAX_PER_SPECIES:
            species_count[species_name] += 1
            valid_recordings.append({
                'id': rec['id'],
                'nombre_cientifico': species_name,
                'nombre_comun': rec.get('en', ''),
                'calidad': quality,
                'locacion': rec.get('loc', ''),
                'latitud': rec.get('lat', ''),
                'longitud': rec.get('lng', ''),
                'fecha': rec.get('date', ''),
                'hora': rec.get('time', ''),
                'autor': rec.get('rec', ''),
                'url_descarga': rec.get('file', ''),
                'url_sonograma': rec.get('sono', {}).get('full', '')
            })
            
    print(f"Quedaron {len(valid_recordings)} grabaciones útiles después del filtro.")
    
    # Guardar metadatos en CSV
    if valid_recordings:
        df = pd.DataFrame(valid_recordings)
        csv_path = os.path.join(METADATA_DIR, 'aves_tarapoto_lamas.csv')
        df.to_csv(csv_path, index=False)
        print(f"Metadatos guardados en: {csv_path}")
    else:
        print("No se encontraron grabaciones que cumplan los criterios.")
        return

    # Descargar audios
    print("\nIniciando descarga de audios...")
    for rec in tqdm(valid_recordings, desc="Descargando"):
        species_dir = os.path.join(AUDIO_DIR, rec['nombre_cientifico'])
        os.makedirs(species_dir, exist_ok=True)
        
        file_url = rec['url_descarga']
        if not file_url.startswith('http'):
            file_url = f"https:{file_url}" if file_url.startswith('//') else f"https://xeno-canto.org{file_url}"
            
        # Extensión del archivo (usualmente mp3, a veces wav)
        ext = '.mp3' # Por defecto xeno-canto entrega mp3
        
        filepath = os.path.join(species_dir, f"{rec['id']}{ext}")
        
        # Evitar re-descargar si ya existe
        if not os.path.exists(filepath):
            try:
                r = requests.get(file_url, stream=True)
                if r.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                time.sleep(0.5) # Pausa amigable
            except Exception as e:
                print(f"Error descargando {rec['id']}: {e}")

if __name__ == "__main__":
    # Queries: Aves en Perú, en Tarapoto y Lamas
    queries = ['cnt:Peru loc:"Tarapoto"', 'cnt:Peru loc:"Lamas"']
    
    print("--- INICIANDO RECOLECCIÓN DE DATOS DE XENO-CANTO ---")
    all_recordings = []
    
    for q in queries:
        recs = obtener_metadatos_api(q)
        if recs:
            all_recordings.extend(recs)
            
    if all_recordings:
        filtrar_y_descargar(all_recordings)
    else:
        print("No se obtuvieron resultados de la API para estas ubicaciones.")
    print("--- PROCESO TERMINADO ---")
