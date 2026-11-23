import itertools
import random
import time
from typing import Dict, List, Tuple, Any
import numpy as np


def calcular_distancia_ruta(ruta: List[int], matriz_distancias: np.ndarray) -> float:
    distancia = 0.0
    n = len(ruta)
    for i in range(n - 1):
        distancia += matriz_distancias[ruta[i], ruta[i + 1]]
    distancia += matriz_distancias[ruta[-1], ruta[0]]
    return distancia


def calcular_fitness(ruta: List[int], matriz_distancias: np.ndarray) -> float:
    d = calcular_distancia_ruta(ruta, matriz_distancias)
    return 1.0 / (d + 1e-9)


def cruce_ordenado_ox1(padre1: List[int], padre2: List[int]) -> List[int]:
    n = len(padre1)
    if n <= 2:
        return padre1.copy()

    corte1 = random.randint(0, n - 2)
    corte2 = random.randint(corte1 + 1, n - 1)

    hijo = [-1] * n
    hijo[corte1:corte2 + 1] = padre1[corte1:corte2 + 1]
    segmento_set = set(hijo[corte1:corte2 + 1])

    idx_hijo = (corte2 + 1) % n
    for gen in itertools.chain(padre2[corte2 + 1:], padre2[:corte2 + 1]):
        if gen not in segmento_set:
            hijo[idx_hijo] = gen
            idx_hijo = (idx_hijo + 1) % n

    return hijo


def mutacion_inversion(individuo: List[int], tasa_mutacion: float) -> List[int]:
    mutado = individuo.copy()
    if random.random() < tasa_mutacion and len(mutado) > 2:
        i = random.randint(0, len(mutado) - 2)
        j = random.randint(i + 1, len(mutado) - 1)
        mutado[i:j + 1] = reversed(mutado[i:j + 1])
    return mutado


def seleccion_torneo(poblacion: List[List[int]], aptitudes: List[float], k: int = 3) -> List[int]:
    candidatos_indices = random.sample(range(len(poblacion)), k)
    mejor_idx = max(candidatos_indices, key=lambda idx: aptitudes[idx])
    return poblacion[mejor_idx].copy()


def ejecutar_algoritmo_genetico(
    matriz_distancias: np.ndarray,
    tam_poblacion: int = 100,
    generaciones: int = 150,
    tasa_cruce: float = 0.85,
    tasa_mutacion: float = 0.15,
    tam_torneo: int = 3,
    elitismo: int = 2,
    seed: int = 42
) -> Dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    inicio_tiempo = time.perf_counter()

    num_nodos = matriz_distancias.shape[0]
    nodos_intermedios = list(range(1, num_nodos))

    poblacion = []
    for _ in range(tam_poblacion):
        ind = nodos_intermedios.copy()
        random.shuffle(ind)
        poblacion.append(ind)

    historial_mejor_distancia = []
    historial_promedio_distancia = []
    mejor_ruta_global = None
    mejor_distancia_global = float("inf")

    for gen in range(generaciones):
        distancias = [
            calcular_distancia_ruta([0] + ind, matriz_distancias)
            for ind in poblacion
        ]
        aptitudes = [1.0 / (d + 1e-9) for d in distancias]

        min_d = min(distancias)
        avg_d = sum(distancias) / len(distancias)
        historial_mejor_distancia.append(min_d)
        historial_promedio_distancia.append(avg_d)

        idx_mejor_gen = distancias.index(min_d)
        if min_d < mejor_distancia_global:
            mejor_distancia_global = min_d
            mejor_ruta_global = [0] + poblacion[idx_mejor_gen]

        orden_elitismo = sorted(range(len(poblacion)), key=lambda i: aptitudes[i], reverse=True)
        nueva_poblacion = [poblacion[i].copy() for i in orden_elitismo[:elitismo]]

        while len(nueva_poblacion) < tam_poblacion:
            padre1 = seleccion_torneo(poblacion, aptitudes, k=tam_torneo)
            padre2 = seleccion_torneo(poblacion, aptitudes, k=tam_torneo)

            if random.random() < tasa_cruce:
                hijo = cruce_ordenado_ox1(padre1, padre2)
            else:
                hijo = padre1.copy()

            hijo = mutacion_inversion(hijo, tasa_mutacion)
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    tiempo_total_ms = (time.perf_counter() - inicio_tiempo) * 1000

    return {
        "algoritmo": "Algoritmo Evolutivo (Genético)",
        "mejor_ruta": mejor_ruta_global,
        "mejor_distancia": mejor_distancia_global,
        "distancia_inicial": historial_mejor_distancia[0],
        "mejora_porcentaje": ((historial_mejor_distancia[0] - mejor_distancia_global) / historial_mejor_distancia[0]) * 100,
        "historial_mejor_distancia": historial_mejor_distancia,
        "historial_promedio_distancia": historial_promedio_distancia,
        "tiempo_ms": tiempo_total_ms,
        "generaciones": generaciones,
        "tam_poblacion": tam_poblacion
    }


def busqueda_heuristica_vecino_cercano(matriz_distancias: np.ndarray) -> Dict[str, Any]:
    inicio_tiempo = time.perf_counter()
    num_nodos = matriz_distancias.shape[0]

    no_visitados = set(range(1, num_nodos))
    ruta = [0]
    actual = 0

    while no_visitados:
        siguiente = min(no_visitados, key=lambda n: matriz_distancias[actual, n])
        ruta.append(siguiente)
        no_visitados.remove(siguiente)
        actual = siguiente

    distancia = calcular_distancia_ruta(ruta, matriz_distancias)
    tiempo_ms = (time.perf_counter() - inicio_tiempo) * 1000

    return {
        "algoritmo": "Búsqueda Heurística (Vecino más Cercano)",
        "mejor_ruta": ruta,
        "mejor_distancia": distancia,
        "tiempo_ms": tiempo_ms
    }


def heuristica_2opt_local_search(ruta_inicial: List[int], matriz_distancias: np.ndarray, max_iter: int = 500) -> Dict[str, Any]:
    inicio_tiempo = time.perf_counter()
    mejor_ruta = ruta_inicial.copy()
    mejor_distancia = calcular_distancia_ruta(mejor_ruta, matriz_distancias)
    n = len(mejor_ruta)

    mejora = True
    iteracion = 0
    while mejora and iteracion < max_iter:
        mejora = False
        iteracion += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                nueva_ruta = mejor_ruta[:i] + list(reversed(mejor_ruta[i:j + 1])) + mejor_ruta[j + 1:]
                d = calcular_distancia_ruta(nueva_ruta, matriz_distancias)
                if d < mejor_distancia - 1e-5:
                    mejor_distancia = d
                    mejor_ruta = nueva_ruta
                    mejora = True
                    break
            if mejora:
                break

    tiempo_ms = (time.perf_counter() - inicio_tiempo) * 1000
    return {
        "algoritmo": "Heurística 2-Opt (Búsqueda Local)",
        "mejor_ruta": mejor_ruta,
        "mejor_distancia": mejor_distancia,
        "tiempo_ms": tiempo_ms
    }


def busqueda_ciega_exhaustiva(matriz_distancias: np.ndarray, max_nodos: int = 9) -> Dict[str, Any]:
    inicio_tiempo = time.perf_counter()
    num_nodos = matriz_distancias.shape[0]

    if num_nodos > max_nodos:
        return {
            "algoritmo": "Búsqueda Ciega Exhaustiva (Fuerza Bruta)",
            "error": f"Inviable por explosión combinatoria: ({num_nodos}-1)! evaluaciones requerirían semanas/años de cómputo.",
            "mejor_ruta": None,
            "mejor_distancia": None,
            "tiempo_ms": 0.0
        }

    nodos_intermedios = list(range(1, num_nodos))
    mejor_ruta = None
    mejor_distancia = float("inf")
    permutaciones_revisadas = 0

    for perm in itertools.permutations(nodos_intermedios):
        permutaciones_revisadas += 1
        ruta_candidata = [0] + list(perm)
        d = calcular_distancia_ruta(ruta_candidata, matriz_distancias)
        if d < mejor_distancia:
            mejor_distancia = d
            mejor_ruta = ruta_candidata

    tiempo_ms = (time.perf_counter() - inicio_tiempo) * 1000

    return {
        "algoritmo": "Búsqueda Ciega Exhaustiva (Fuerza Bruta)",
        "mejor_ruta": mejor_ruta,
        "mejor_distancia": mejor_distancia,
        "permutaciones_evaluadas": permutaciones_revisadas,
        "tiempo_ms": tiempo_ms
    }


def busqueda_ciega_aleatoria(matriz_distancias: np.ndarray, num_muestras: int = 15000, seed: int = 42) -> Dict[str, Any]:
    random.seed(seed)
    inicio_tiempo = time.perf_counter()
    num_nodos = matriz_distancias.shape[0]
    nodos_intermedios = list(range(1, num_nodos))

    mejor_ruta = None
    mejor_distancia = float("inf")

    for _ in range(num_muestras):
        perm = nodos_intermedios.copy()
        random.shuffle(perm)
        ruta_candidata = [0] + perm
        d = calcular_distancia_ruta(ruta_candidata, matriz_distancias)
        if d < mejor_distancia:
            mejor_distancia = d
            mejor_ruta = ruta_candidata

    tiempo_ms = (time.perf_counter() - inicio_tiempo) * 1000

    return {
        "algoritmo": "Búsqueda Ciega Aleatoria (Muestreo no informado)",
        "mejor_ruta": mejor_ruta,
        "mejor_distancia": mejor_distancia,
        "muestras_evaluadas": num_muestras,
        "tiempo_ms": tiempo_ms
    }
