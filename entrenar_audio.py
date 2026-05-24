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
DATASET_DIR = os.path.join("data", "dataset_espectrogramas")
BATCH_SIZE = 16
IMG_SIZE = (224, 224)
EPOCHS = 15
MODEL_PATH = "modelo_audio_aves.keras"
TFLITE_PATH = "modelo_audio_aves.tflite"

def entrenar():
    if not os.path.exists(DATASET_DIR):
        print(f"Error: No se encontró la carpeta {DATASET_DIR}")
        return

    print("Cargando espectrogramas...")
    # Cargar el dataset de audio (convertido a imágenes)
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
    print(f"\nDetectadas {num_classes} especies para entrenar el modelo de audio.")

    # Guardar los nombres de las clases
    with open("clases_audio.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(class_names))
    print("-> Nombres guardados en 'clases_audio.txt'")

    # Optimizar rendimiento
    AUTOTUNE = tf.data.AUTOTUNE
    train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
    val_dataset = val_dataset.prefetch(buffer_size=AUTOTUNE)

    # Crear la arquitectura del Modelo (usamos CNN visual porque le pasaremos espectrogramas)
    print("\nConstruyendo modelo MobileNetV2 (adaptado para audio)...")
    base_model = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base_model.trainable = False  

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.2)(x) 
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)

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

    print(f"\n¡Misión cumplida! El modelo de AUDIO está listo para EcoAves.")
    print(f"- Archivo del modelo: {TFLITE_PATH}")

if __name__ == "__main__":
    entrenar()
