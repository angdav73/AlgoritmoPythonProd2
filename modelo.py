"""
Lógica del clasificador de algoritmos de búsqueda.

Aquí viven las funciones para entrenar, guardar, cargar y usar el modelo.
La interfaz (app.py) y el script de entrenamiento (entrenar.py) las usan.
"""
import json
import os
from pathlib import Path

import joblib
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union

BASE_DIR = Path(__file__).resolve().parent
RUTA_DATOS = BASE_DIR / "training.json"
RUTA_MODELO = BASE_DIR / "modelo.joblib"

# Nombres legibles para mostrar en la app
NOMBRES_ALGORITMOS = {
    "busqueda_hash": "Búsqueda por hash",
    "busqueda_binaria": "Búsqueda binaria",
    "busqueda_no_informada": "Búsqueda no informada",
    "busqueda_informada": "Búsqueda informada",
}


def cargar_datos(ruta=RUTA_DATOS):
    """Lee training.json (formato de Machine Learning for Kids) y devuelve textos y etiquetas."""
    with open(ruta, encoding="utf-8") as f:
        ejemplos = json.load(f)
    textos = [ejemplo["textdata"] for ejemplo in ejemplos]
    etiquetas = [ejemplo["label"] for ejemplo in ejemplos]
    return textos, etiquetas


def crear_pipeline():
    """
    Pipeline sin entrenar: texto -> TF-IDF (palabras + caracteres) -> regresión logística.
    Los n-gramas de caracteres ayudan con variaciones y tildes faltantes.
    """
    vectorizador = make_union(
        TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
    )
    return make_pipeline(vectorizador, LogisticRegression(max_iter=5000, C=10))


def entrenar(ruta=RUTA_DATOS):
    """Entrena el pipeline con todos los ejemplos de training.json."""
    textos, etiquetas = cargar_datos(ruta)
    pipeline = crear_pipeline()
    pipeline.fit(textos, etiquetas)
    return pipeline


def guardar(pipeline, ruta=RUTA_MODELO):
    joblib.dump(pipeline, ruta)


def cargar(ruta=RUTA_MODELO):
    return joblib.load(ruta)


def predecir(pipeline, texto):
    """
    Clasifica un texto.
    Devuelve una lista de (etiqueta, probabilidad), de la más probable a la menos probable.
    """
    probabilidades = pipeline.predict_proba([texto])[0]
    resultados = list(zip(pipeline.classes_, probabilidades))
    resultados.sort(key=lambda par: par[1], reverse=True)
    return resultados


# Dirección de la API de Machine Learning for Kids para tu proyecto
URL_ML4K = "https://machinelearningforkids.co.uk/api/scratch/{clave}/classify"
VARIABLE_CLAVE_ML4K = "ML4K_API_KEY"
os.environ.setdefault(
    VARIABLE_CLAVE_ML4K,
    "231bb9e0-dee6-11f1-92a1-db0daa3843b7566c96b5-07c2-4a37-b2a5-030cdddbde9e",
)


def clasificar_en_linea(texto, clave=None):
    """
    Clasifica el texto con el modelo entrenado en Machine Learning for Kids.
    La clave se toma de la variable de entorno ML4K_API_KEY si no se pasa como argumento.
    Devuelve la misma forma que predecir(): lista de (etiqueta, probabilidad) ordenada.
    """
    clave = clave or os.environ.get(VARIABLE_CLAVE_ML4K)
    if not clave:
        raise ValueError(
            f"Falta la clave de API. Define la variable de entorno {VARIABLE_CLAVE_ML4K}."
        )

    # Los mensajes de error no incluyen la URL, porque la URL contiene la clave
    try:
        respuesta = requests.get(
            URL_ML4K.format(clave=clave), params={"data": texto}, timeout=15
        )
    except requests.RequestException:
        raise RuntimeError("No se pudo conectar con Machine Learning for Kids.") from None

    if not respuesta.ok:
        raise RuntimeError(
            f"Machine Learning for Kids respondió con error {respuesta.status_code}. "
            "Revisa que la clave sea correcta."
        )

    try:
        resultados = []
        for item in respuesta.json():
            # El código de ejemplo de ML4K muestra la confianza como porcentaje (0-100).
            # La pasamos a 0-1 para usar el mismo formato que predecir().
            confianza = float(item["confidence"]) / 100
            resultados.append((item["class_name"], confianza))
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("La respuesta de Machine Learning for Kids no tiene el formato esperado.") from None

    resultados.sort(key=lambda par: par[1], reverse=True)
    return resultados
