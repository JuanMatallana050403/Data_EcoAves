import requests
import json
import os
import pandas as pd
from tqdm import tqdm
import time

# Configuración
API_KEY = "0d59b24ba612026fb4efda058eb96ff5fc61b7f0"
MAX_PER_SPECIES = 40
QUALITIES_ACCEPTED = ['A', 'B']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
AUDIO_DIR = os.path.join(DATA_DIR, 'dataset_audios')
METADATA_DIR = os.path.join(DATA_DIR, 'metadata')

# Archivo original para sacar la lista de especies
CSV_ORIGINAL = os.path.join(METADATA_DIR, 'aves_tarapoto_lamas.csv')
CSV_AMPLIADO = os.path.join(METADATA_DIR, 'aves_ampliado.csv')

def obtener_metadatos_especie(gen, sp):
    # Buscamos en todo Perú
    query = f'gen:{gen} sp:{sp} cnt:Peru'
    base_url = "https://xeno-canto.org/api/3/recordings"
    
    response = requests.get(base_url, params={"query": query, "key": API_KEY})
    if response.status_code != 200:
        return []
    
    data = response.json()
    num_pages = data.get('numPages', 1)
    recordings = data.get('recordings', [])
    
    # Para no saturar, limitamos a un máximo de 2 páginas (200 audios) por especie
    max_pages = min(num_pages, 2)
    for page in range(2, max_pages + 1):
        resp = requests.get(base_url, params={"query": query, "page": page, "key": API_KEY})
        if resp.status_code == 200:
            recordings.extend(resp.json().get('recordings', []))
        time.sleep(0.5) 
        
    return recordings

def descargar_ampliado():
    if not os.path.exists(CSV_ORIGINAL):
        print("No se encontró el CSV original.")
        return
        
    # Omitimos la búsqueda de metadatos y solo cargamos el CSV ampliado existente
    if os.path.exists(CSV_AMPLIADO):
        df_existente = pd.read_csv(CSV_AMPLIADO)
        all_valid_recordings = df_existente.to_dict('records')
        print(f"--- REANUDANDO DESCARGA FÍSICA PARA {len(all_valid_recordings)} AUDIOS (SALTANDO BÚSQUEDA API) ---")
    else:
        print(f"Error: No se encontró el archivo de metadatos {CSV_AMPLIADO}")
        return
    print("Iniciando descarga física de los archivos MP3...")
    
    # Descarga física de los audios
    for rec in tqdm(all_valid_recordings, desc="Descargando MP3"):
        species_dir = os.path.join(AUDIO_DIR, rec['nombre_cientifico'])
        os.makedirs(species_dir, exist_ok=True)
        
        filepath = os.path.join(species_dir, f"{rec['id']}.mp3")
        if os.path.exists(filepath):
            continue # Ya existe
            
        file_url = rec['url_descarga']
        if not file_url.startswith('http'):
            file_url = f"https:{file_url}" if file_url.startswith('//') else f"https://xeno-canto.org{file_url}"
            
        try:
            r = requests.get(file_url, stream=True)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: f.write(chunk)
            time.sleep(0.5)
        except Exception as e:
            pass # Ignoramos errores de descarga por ahora

    print("--- PROCESO AMPLIADO TERMINADO ---")

if __name__ == "__main__":
    descargar_ampliado()
