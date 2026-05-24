import os
from PIL import Image

DATASET_IMG_DIR = os.path.join("data", "dataset_imagenes")

def limpiar_espectrogramas():
    if not os.path.exists(DATASET_IMG_DIR):
        print(f"Error: No se encontró la carpeta {DATASET_IMG_DIR}")
        return

    eliminadas = 0
    revisadas = 0

    for especie in os.listdir(DATASET_IMG_DIR):
        ruta_especie = os.path.join(DATASET_IMG_DIR, especie)
        if not os.path.isdir(ruta_especie):
            continue

        for archivo in os.listdir(ruta_especie):
            ruta_archivo = os.path.join(ruta_especie, archivo)
            revisadas += 1
            
            try:
                with Image.open(ruta_archivo) as img:
                    ancho, alto = img.size
                    
                    # Los espectrogramas de Macaulay Library / eBird 
                    # siempre son tiras horizontales muy anchas (proporción mayor a 2.2)
                    proporcion = ancho / alto
                    es_espectrograma = proporcion > 2.2

                if es_espectrograma:
                    os.remove(ruta_archivo)
                    eliminadas += 1
                    print(f"Eliminado (posible espectrograma - proporción {proporcion:.1f}): {archivo}")
                    
            except Exception as e:
                # Si la imagen está corrupta y no se puede abrir, también la borramos
                os.remove(ruta_archivo)
                eliminadas += 1
                print(f"Eliminado (archivo corrupto): {archivo}")

    print("-" * 30)
    print(f"Limpieza completada.")
    print(f"Imágenes revisadas: {revisadas}")
    print(f"Espectrogramas o corruptas eliminadas: {eliminadas}")
    print(f"Imágenes válidas restantes: {revisadas - eliminadas}")

if __name__ == "__main__":
    limpiar_espectrogramas()
