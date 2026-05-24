import os
import requests
from pygbif import occurrences
import time

# Configuración
DATASET_AUDIO_DIR = os.path.join("data", "dataset_audios")
DATASET_IMG_DIR = os.path.join("data", "dataset_imagenes")
IMAGENES_POR_AVE = 150  # Aumentado de 40 a 150 para que la IA aprenda mejor

# Geometría para Tarapoto, Morales, La Banda de Shilcayo y Lamas (aprox)
# Polígono WKT: Longitud Min, Latitud Min -> Longitud Max, Latitud Max
GEOMETRY_LOCAL = 'POLYGON((-76.7 -6.6, -76.2 -6.6, -76.2 -6.3, -76.7 -6.3, -76.7 -6.6))'

# Asegurar que el directorio base de imágenes exista
os.makedirs(DATASET_IMG_DIR, exist_ok=True)

def descargar_imagen(url, ruta_destino):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(ruta_destino, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        # Silenciar errores de red individuales para no llenar la consola
        pass
    return False

def buscar_y_descargar(especie, cantidad_necesaria):
    ruta_especie = os.path.join(DATASET_IMG_DIR, especie)
    os.makedirs(ruta_especie, exist_ok=True)
    
    # Reemplazar guiones bajos por espacios para el nombre científico
    nombre_cientifico = especie.replace("_", " ")
    
    imagenes_descargadas = 0
    urls_descargadas = set() # Para evitar duplicados

    print(f"\nProcesando: {nombre_cientifico}")

    # ESTRATEGIA 1: Búsqueda Local (Tarapoto, Lamas, etc.)
    print("  -> Buscando en la zona local...")
    try:
        res_local = occurrences.search(
            scientificName=nombre_cientifico, 
            mediaType='StillImage', 
            geometry=GEOMETRY_LOCAL,
            limit=cantidad_necesaria
        )
        imagenes_descargadas += procesar_resultados(res_local, ruta_especie, especie, imagenes_descargadas, urls_descargadas, cantidad_necesaria)
    except Exception as e:
        print(f"  -> Error en búsqueda local: {e}")

    # ESTRATEGIA 2: Búsqueda Nacional (Perú) si faltan imágenes
    if imagenes_descargadas < cantidad_necesaria:
        faltantes = cantidad_necesaria - imagenes_descargadas
        print(f"  -> Obtenidas {imagenes_descargadas}/{cantidad_necesaria}. Buscando en resto de Perú...")
        try:
            res_peru = occurrences.search(
                scientificName=nombre_cientifico, 
                mediaType='StillImage', 
                country='PE',
                limit=100  # Pedimos más para filtrar las que ya tenemos
            )
            imagenes_descargadas += procesar_resultados(res_peru, ruta_especie, especie, imagenes_descargadas, urls_descargadas, cantidad_necesaria)
        except Exception as e:
            print(f"  -> Error en búsqueda nacional: {e}")

    # ESTRATEGIA 3: Búsqueda Global si aún faltan imágenes
    if imagenes_descargadas < cantidad_necesaria:
        faltantes = cantidad_necesaria - imagenes_descargadas
        print(f"  -> Obtenidas {imagenes_descargadas}/{cantidad_necesaria}. Buscando a nivel global...")
        try:
            res_global = occurrences.search(
                scientificName=nombre_cientifico, 
                mediaType='StillImage', 
                limit=100
            )
            imagenes_descargadas += procesar_resultados(res_global, ruta_especie, especie, imagenes_descargadas, urls_descargadas, cantidad_necesaria)
        except Exception as e:
            print(f"  -> Error en búsqueda global: {e}")

    print(f"  => Finalizado {nombre_cientifico}: {imagenes_descargadas}/{cantidad_necesaria} imágenes descargadas.")

def procesar_resultados(resultados, ruta_especie, especie, inicio_idx, urls_descargadas, objetivo):
    descargadas_en_esta_ronda = 0
    if not resultados or 'results' not in resultados:
        return 0
        
    for occ in resultados['results']:
        if inicio_idx + descargadas_en_esta_ronda >= objetivo:
            break
            
        if 'media' in occ:
            for media in occ['media']:
                if media.get('type') == 'StillImage' and 'identifier' in media:
                    url_img = media['identifier']
                    
                    if url_img in urls_descargadas:
                        continue
                        
                    ext = url_img.split('.')[-1][:4] # intentar obtener extensión
                    if ext.lower() not in ['jpg', 'jpeg', 'png']:
                        ext = 'jpg'
                        
                    nombre_archivo = f"{especie}_{inicio_idx + descargadas_en_esta_ronda + 1}.{ext}"
                    ruta_destino = os.path.join(ruta_especie, nombre_archivo)
                    
                    if descargar_imagen(url_img, ruta_destino):
                        urls_descargadas.add(url_img)
                        descargadas_en_esta_ronda += 1
                        break # Una foto por ocurrencia suele ser suficiente para evitar fotos repetidas del mismo ángulo
    
    return descargadas_en_esta_ronda

# Bloque principal
if __name__ == "__main__":
    if not os.path.exists(DATASET_AUDIO_DIR):
        print(f"Error: No se encontró el directorio {DATASET_AUDIO_DIR}")
        exit(1)

    especies_a_procesar = [d for d in os.listdir(DATASET_AUDIO_DIR) if os.path.isdir(os.path.join(DATASET_AUDIO_DIR, d))]
    
    print(f"Se encontraron {len(especies_a_procesar)} especies para descargar imágenes.")
    
    for especie in especies_a_procesar:
        buscar_y_descargar(especie, IMAGENES_POR_AVE)
        time.sleep(1) # Pequeña pausa para no saturar la API de GBIF
        
    print("\nProceso de descarga de imágenes completado.")
