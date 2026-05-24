import tensorflow as tf
from tensorflow.keras.utils import image_dataset_from_directory
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import os

# Desactivar advertencias de TF para consola limpia
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Configuración
DATASET_DIR = os.path.join("data", "dataset_imagenes")
BATCH_SIZE = 16
IMG_SIZE = (224, 224)
EPOCHS = 15  # 15 épocas suelen ser suficientes con Transfer Learning
MODEL_PATH = "modelo_vision_aves.keras"
TFLITE_PATH = "modelo_vision_aves.tflite"

def entrenar():
    if not os.path.exists(DATASET_DIR):
        print(f"Error: No se encontró la carpeta {DATASET_DIR}")
        return

    print("Cargando imágenes...")
    # Cargar el dataset (80% entrenamiento, 20% validación)
    train_dataset = image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    val_dataset = image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    class_names = train_dataset.class_names
    num_classes = len(class_names)
    print(f"\nDetectadas {num_classes} especies para entrenar.")

    # Guardar los nombres de las clases en un archivo de texto
    with open("clases_vision.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(class_names))
    print("-> Nombres de especies guardados en 'clases_vision.txt'")

    # Optimizar rendimiento de carga de datos
    AUTOTUNE = tf.data.AUTOTUNE
    train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
    val_dataset = val_dataset.prefetch(buffer_size=AUTOTUNE)

    # Crear la arquitectura del Modelo Dual (Base + Nueva Cabeza)
    print("\nConstruyendo modelo MobileNetV2...")
    base_model = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base_model.trainable = False  # Congelamos la base para aprovechar su conocimiento general

    # IMPORTANTE: Data Augmentation
    # Como hay muy pocas fotos por especie, rotamos y giramos las fotos aleatoriamente
    # para que la IA aprenda a reconocer al ave en distintas posiciones.
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = tf.keras.layers.RandomFlip("horizontal")(inputs)
    x = tf.keras.layers.RandomRotation(0.15)(x)
    x = tf.keras.layers.RandomZoom(0.15)(x)
    
    # IMPORTANTE: MobileNetV2 espera que los píxeles estén escalados entre -1 y 1.
    x = tf.keras.layers.Rescaling(1./127.5, offset=-1)(x)
    
    x = base_model(x, training=False)
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.2)(x) # Previene sobreajuste
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=inputs, outputs=predictions)

    model.compile(optimizer='adam', 
                  loss='sparse_categorical_crossentropy', 
                  metrics=['accuracy'])

    # Callbacks
    callbacks = [
        ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='val_accuracy'),
        EarlyStopping(patience=3, monitor='val_loss', restore_best_weights=True)
    ]

    print("\nIniciando el entrenamiento...")
    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    print("\nExportando modelo a formato ligero TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    with open(TFLITE_PATH, 'wb') as f:
        f.write(tflite_model)

    print(f"\n¡Misión cumplida! El modelo está listo para EcoAves.")
    print(f"- Archivo del modelo: {TFLITE_PATH}")

if __name__ == "__main__":
    entrenar()
