import math
from typing import List, Dict
import pandas as pd
import numpy as np

PUNTOS_PUEBLA: List[Dict[str, any]] = [
    {
        "id": 0,
        "nombre": "UTP - Almacén Central (Hub de Distribución)",
        "categoria": "Hub Central",
        "lat": 19.0583,
        "lon": -98.1517,
        "demanda_paquetes": 0,
        "direccion": "Antiguo Camino a La Resurrección 1002-A, Puebla"
    },
    {
        "id": 1,
        "nombre": "Parque Industrial FINSA",
        "categoria": "Parque Industrial",
        "lat": 19.1245,
        "lon": -98.2436,
        "demanda_paquetes": 28,
        "direccion": "Autopista México-Puebla Km 115, Cuautlancingo"
    },
    {
        "id": 2,
        "nombre": "Planta Armadora Volkswagen de México",
        "categoria": "Industria Automotriz",
        "lat": 19.1302,
        "lon": -98.2489,
        "demanda_paquetes": 35,
        "direccion": "Km 116 Autopista México-Puebla, San Lorenzo Almecatla"
    },
    {
        "id": 3,
        "nombre": "Parque Industrial Puebla 2000",
        "categoria": "Parque Industrial",
        "lat": 19.0768,
        "lon": -98.1654,
        "demanda_paquetes": 22,
        "direccion": "Av. 18 de Noviembre, Puebla"
    },
    {
        "id": 4,
        "nombre": "Central de Abasto de Puebla",
        "categoria": "Centro de Abasto",
        "lat": 19.0987,
        "lon": -98.1823,
        "demanda_paquetes": 40,
        "direccion": "Vía Corta a Santa Ana Chiautempan, Puebla"
    },
    {
        "id": 5,
        "nombre": "CAPU (Central de Autobuses de Puebla)",
        "categoria": "Terminal Logística",
        "lat": 19.0718,
        "lon": -98.2045,
        "demanda_paquetes": 18,
        "direccion": "Blvd. Carmen Serdán 199, Las Cuartillas, Puebla"
    },
    {
        "id": 6,
        "nombre": "Centro Histórico (Zócalo de Puebla)",
        "categoria": "Comercio Urbano",
        "lat": 19.0437,
        "lon": -98.1983,
        "demanda_paquetes": 15,
        "direccion": "Palacio Municipal, Av. Juan de Palafox y Mendoza, Puebla"
    },
    {
        "id": 7,
        "nombre": "Centro Comercial Angelópolis",
        "categoria": "Centro Comercial",
        "lat": 19.0325,
        "lon": -98.2325,
        "demanda_paquetes": 25,
        "direccion": "Blvd. del Niño Poblano 2510, Concepción de la Cruz"
    },
    {
        "id": 8,
        "nombre": "Ciudad Judicial Siglo XXI",
        "categoria": "Sector Público",
        "lat": 19.0064,
        "lon": -98.2612,
        "demanda_paquetes": 12,
        "direccion": "Periférico Ecológico 4000, San Andrés Cholula"
    },
    {
        "id": 9,
        "nombre": "Parque Industrial La Resurrección",
        "categoria": "Parque Industrial",
        "lat": 19.0831,
        "lon": -98.1402,
        "demanda_paquetes": 20,
        "direccion": "Corredor Industrial La Resurrección, Puebla"
    },
    {
        "id": 10,
        "nombre": "San Pedro Cholula (Plaza de la Concordia)",
        "categoria": "Población Conurbada",
        "lat": 19.0622,
        "lon": -98.3045,
        "demanda_paquetes": 16,
        "direccion": "Calle 4 Pte., Centro, San Pedro Cholula"
    },
    {
        "id": 11,
        "nombre": "San Andrés Cholula (Zócalo Municipal)",
        "categoria": "Población Conurbada",
        "lat": 19.0531,
        "lon": -98.2978,
        "demanda_paquetes": 14,
        "direccion": "Av. 16 de Septiembre 102, Centro, San Andrés Cholula"
    },
    {
        "id": 12,
        "nombre": "Parque Ecológico Revolución Mexicana",
        "categoria": "Punto Urbano",
        "lat": 19.0348,
        "lon": -98.1812,
        "demanda_paquetes": 10,
        "direccion": "Calle 24 Sur s/n, Azcárate, Puebla"
    },
    {
        "id": 13,
        "nombre": "Centro Comercial Galerías Serdán",
        "categoria": "Centro Comercial",
        "lat": 19.0792,
        "lon": -98.2256,
        "demanda_paquetes": 24,
        "direccion": "Blvd. Hermanos Serdán 270, Posadas, Puebla"
    },
    {
        "id": 14,
        "nombre": "Triángulo Las Ánimas",
        "categoria": "Centro Comercial",
        "lat": 19.0416,
        "lon": -98.2281,
        "demanda_paquetes": 18,
        "direccion": "Calle 39 Pte. 3515, Las Ánimas, Puebla"
    },
    {
        "id": 15,
        "nombre": "Hospital de Traumatología y Ortopedia (Rafael Moreno Valle)",
        "categoria": "Sector Salud",
        "lat": 19.0882,
        "lon": -98.2014,
        "demanda_paquetes": 8,
        "direccion": "Lateral Autopista México-Puebla 284, San Pablo Xochimehuacan"
    },
    {
        "id": 16,
        "nombre": "Plaza Dorada Puebla",
        "categoria": "Centro Comercial",
        "lat": 19.0278,
        "lon": -98.2056,
        "demanda_paquetes": 20,
        "direccion": "Blvd. Héroes del 5 de Mayo 3126, Ladrillera de Benítez, Puebla"
    },
    {
        "id": 17,
        "nombre": "Parque Industrial Chachapa",
        "categoria": "Parque Industrial",
        "lat": 19.0655,
        "lon": -98.0985,
        "demanda_paquetes": 26,
        "direccion": "Carretera Federal a Tehuacán Km 12.5, Amozoc"
    },
    {
        "id": 18,
        "nombre": "Centro Expositor y de Convenciones (Los Fuertes)",
        "categoria": "Recinto de Eventos",
        "lat": 19.0573,
        "lon": -98.1852,
        "demanda_paquetes": 15,
        "direccion": "Ejército de Oriente s/n, Centro Cívico 5 de Mayo, Puebla"
    },
    {
        "id": 19,
        "nombre": "Corredor Comercial Vía Atlixcáyotl",
        "categoria": "Zona Corporativa",
        "lat": 19.0152,
        "lon": -98.2450,
        "demanda_paquetes": 22,
        "direccion": "Vía Atlixcáyotl 5208, Reserva Territorial Atlixcáyotl"
    },
    {
        "id": 20,
        "nombre": "Plaza San Diego (Forjadores)",
        "categoria": "Centro Comercial",
        "lat": 19.0745,
        "lon": -98.2789,
        "demanda_paquetes": 17,
        "direccion": "Blvd. Forjadores de Puebla 3401, San Diego Manzanilla"
    },
    {
        "id": 21,
        "nombre": "Complejo Cultural Universitario BUAP",
        "categoria": "Sector Educativo",
        "lat": 19.0185,
        "lon": -98.2415,
        "demanda_paquetes": 11,
        "direccion": "Vía Atlixcáyotl 2299, Corredor Comercial Desarrollo Atlixcáyotl"
    },
    {
        "id": 22,
        "nombre": "Plaza Cristal Puebla",
        "categoria": "Centro Comercial",
        "lat": 19.0203,
        "lon": -98.2178,
        "demanda_paquetes": 19,
        "direccion": "Av. San Claudio y Calle 16 de Septiembre, Puebla"
    },
    {
        "id": 23,
        "nombre": "Hospital General del Norte",
        "categoria": "Sector Salud",
        "lat": 19.0915,
        "lon": -98.1762,
        "demanda_paquetes": 9,
        "direccion": "Calle 88 Pte. s/n, Infonavit San Pedro, Puebla"
    },
    {
        "id": 24,
        "nombre": "Parque Industrial Bicentenario",
        "categoria": "Parque Industrial",
        "lat": 19.1021,
        "lon": -98.1524,
        "demanda_paquetes": 23,
        "direccion": "Carretera a La Resurrección Km 3.5, Puebla"
    }
]


def distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    RADIO_TIERRA_KM = 6371.0088

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return RADIO_TIERRA_KM * c


def calcular_matriz_distancias(puntos: List[Dict[str, any]]) -> np.ndarray:
    n = len(puntos)
    matriz = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = distancia_haversine(
                puntos[i]["lat"], puntos[i]["lon"],
                puntos[j]["lat"], puntos[j]["lon"]
            )
            d_vial = d * 1.25
            matriz[i, j] = d_vial
            matriz[j, i] = d_vial
    return matriz


def obtener_subconjunto_puntos(n_puntos: int) -> List[Dict[str, any]]:
    total = len(PUNTOS_PUEBLA)
    n = max(3, min(n_puntos, total))
    return PUNTOS_PUEBLA[:n]


def generar_puntos_sinteticos(n_puntos: int, centro_lat: float = 19.0583, centro_lon: float = -98.1517) -> List[Dict[str, any]]:
    np.random.seed(42)
    puntos = [
        {
            "id": 0,
            "nombre": "UTP - Almacén Central (Hub de Distribución)",
            "categoria": "Hub Central",
            "lat": centro_lat,
            "lon": centro_lon,
            "demanda_paquetes": 0,
            "direccion": "Antiguo Camino a La Resurrección 1002-A, Puebla"
        }
    ]
    for i in range(1, n_puntos):
        lat = centro_lat + np.random.uniform(-0.08, 0.08)
        lon = centro_lon + np.random.uniform(-0.15, 0.15)
        puntos.append({
            "id": i,
            "nombre": f"Cliente Logístico #{i:02d}",
            "categoria": "Cliente Dinámico",
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "demanda_paquetes": int(np.random.randint(5, 45)),
            "direccion": f"Zona Conurbada Puebla #{i}"
        })
    return puntos
