from pathlib import Path

# La ruta base será el directorio actual (la raíz del proyecto Proyecto_DataEcoAves)
ruta_base = Path('.')

# rglob('*.png') busca todos los archivos .png de forma recursiva (incluyendo subcarpetas)
archivos_png = list(ruta_base.rglob('*.png'))

if not archivos_png:
    print("No se encontraron archivos .png en el directorio actual ni en sus subcarpetas.")
else:
    print(f"Se encontraron {len(archivos_png)} archivos .png. Procediendo a eliminar...")
    
    for archivo in archivos_png:
        try:
            archivo.unlink() # Elimina el archivo de forma permanente
            print(f"Eliminado: {archivo}")
        except Exception as e:
            print(f"Error al eliminar {archivo}: {e}")
            
    print("Operación finalizada.")
