import os
import shutil

# Ruta a la carpeta de dataset_audios
dataset_dir = os.path.join("data", "dataset_audios")

if not os.path.exists(dataset_dir):
    print(f"Error: No se encontró el directorio {dataset_dir}")
    exit(1)

# Contadores para el reporte final
carpetas_evaluadas = 0
carpetas_eliminadas = 0

print(f"Evaluando carpetas en: {dataset_dir}...\n")

# Iterar sobre las carpetas dentro de dataset_audios
for nombre_carpeta in os.listdir(dataset_dir):
    ruta_carpeta = os.path.join(dataset_dir, nombre_carpeta)
    
    # Asegurarse de que sea un directorio
    if os.path.isdir(ruta_carpeta):
        carpetas_evaluadas += 1
        
        # Contar archivos (archivos de audio) en el directorio
        archivos = [f for f in os.listdir(ruta_carpeta) if os.path.isfile(os.path.join(ruta_carpeta, f))]
        cantidad_audios = len(archivos)
        
        # Si tiene menos de 10 audios, eliminar la carpeta
        if cantidad_audios < 10:
            print(f"Eliminando '{nombre_carpeta}' (Contiene {cantidad_audios} audios)...")
            try:
                shutil.rmtree(ruta_carpeta)
                carpetas_eliminadas += 1
            except Exception as e:
                print(f"  -> Error al eliminar {nombre_carpeta}: {e}")

print(f"\nResumen:")
print(f"  Carpetas evaluadas: {carpetas_evaluadas}")
print(f"  Carpetas eliminadas: {carpetas_eliminadas}")
print("Limpieza completada.")
