import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
import warnings

# Ignorar advertencias de audios MP3 que a veces genera librosa
warnings.filterwarnings('ignore')

# Configuración
AUDIO_DIR = os.path.join("data", "dataset_audios")
SPEC_DIR = os.path.join("data", "dataset_espectrogramas")
DURATION = 5.0 # Segundos por cada imagen de espectrograma
SR = 22050     # Sample rate estándar

os.makedirs(SPEC_DIR, exist_ok=True)

def generar_espectrograma(audio_path, output_path):
    try:
        # Cargar audio. 
        y, sr = librosa.load(audio_path, sr=SR)
        
        # Calcular cuántos trozos de 'DURATION' segundos podemos extraer
        chunk_length = int(DURATION * SR)
        num_chunks = len(y) // chunk_length
        
        # Si el audio dura menos de 5 segundos, lo rellenamos con silencio (ceros)
        if num_chunks == 0:
            y = librosa.util.fix_length(y, size=chunk_length)
            num_chunks = 1
            
        # Para cada pedazo de 5 segundos, generamos una imagen separada
        for i in range(num_chunks):
            start = i * chunk_length
            end = start + chunk_length
            y_chunk = y[start:end]
            
            # 1. Transformar audio a Mel-Espectrograma
            S = librosa.feature.melspectrogram(y=y_chunk, sr=sr, n_mels=128, fmax=8000)
            
            # 2. Convertir a Decibeles (log scale) para que el contraste sea visible
            S_dB = librosa.power_to_db(S, ref=np.max)
            
            # 3. Normalizar valores entre 0 y 1 para convertirlo en imagen
            S_norm = (S_dB - S_dB.min()) / (S_dB.max() - S_dB.min() + 1e-6)
            
            # Construir el nombre de la imagen: nombreOriginal_0.png, nombreOriginal_1.png...
            chunk_output_path = f"{output_path.replace('.png', f'_{i}.png')}"
            
            # Guardar como imagen usando el mapa de color 'viridis' (tonos azul, verde, amarillo)
            plt.imsave(chunk_output_path, S_norm, origin='lower', cmap='viridis')
            
    except Exception as e:
        print(f"  [X] Error procesando {os.path.basename(audio_path)}: {e}")

if __name__ == "__main__":
    if not os.path.exists(AUDIO_DIR):
        print(f"Error: No se encontró la carpeta {AUDIO_DIR}")
        exit(1)
        
    especies = [d for d in os.listdir(AUDIO_DIR) if os.path.isdir(os.path.join(AUDIO_DIR, d))]
    print(f"Iniciando conversión para {len(especies)} especies...\n")
    
    for especie in especies:
        ruta_especie_audio = os.path.join(AUDIO_DIR, especie)
        ruta_especie_spec = os.path.join(SPEC_DIR, especie)
        os.makedirs(ruta_especie_spec, exist_ok=True)
        
        archivos = [f for f in os.listdir(ruta_especie_audio) if f.endswith('.mp3') or f.endswith('.wav')]
        print(f"Convirtiendo {especie} ({len(archivos)} audios originales)...")
        
        for archivo in archivos:
            ruta_audio = os.path.join(ruta_especie_audio, archivo)
            ruta_output = os.path.join(ruta_especie_spec, f"{archivo.split('.')[0]}.png")
            generar_espectrograma(ruta_audio, ruta_output)
            
    print("\n¡Todos los audios han sido convertidos a espectrogramas exitosamente!")
    print("Ahora tenemos imágenes del sonido para entrenar el modelo.")
