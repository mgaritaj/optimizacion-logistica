"""
Herramienta de optimización logística basada en cálculo multivariable
Universidad Cenfotec - Cálculo Diferencial e Integral - Grupo 01

Este módulo implementa el algoritmo de descenso de gradiente para resolver
el problema de localización óptima de un centro de distribución (problema
de Weber), dado un conjunto de clientes con coordenadas y pesos (ej. volumen
de demanda).

También incluye el método del centro de gravedad (solución analítica directa)
como caso de comparación, válido quiero minimizar la suma de distancias AL
CUADRADO en vez de la distancia normal.
"""

import math
from pyproj import Transformer

# -------------------------------------------------
# CONVERSIÓN DE COORDENADAS
# -------------------------------------------------

# GPS (longitud, latitud) -> CRTM05 (metros)
a_metros = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:5367",
    always_xy=True
)

# CRTM05 (metros) -> GPS (longitud, latitud)
a_gps = Transformer.from_crs(
    "EPSG:5367",
    "EPSG:4326",
    always_xy=True
)

# ---------------------------------------------------------------------------
# 1. Punto inicial (promedio simple de las coordenadas)
# ---------------------------------------------------------------------------
def calcular_punto_inicial(lista_coordenadas):
    """Calcula el promedio simple de las coordenadas como punto de partida."""
    cantidad = len(lista_coordenadas)
    suma_x = sum(coord[0] for coord in lista_coordenadas)
    suma_y = sum(coord[1] for coord in lista_coordenadas)
    return [suma_x / cantidad, suma_y / cantidad]


# ---------------------------------------------------------------------------
# 2. Distancia euclidiana entre dos puntos
# ---------------------------------------------------------------------------
def distancia_euclidiana(punto1, punto2):
    """Distancia en línea recta entre dos puntos (x, y)."""
    dx = punto1[0] - punto2[0]
    dy = punto1[1] - punto2[1]
    return math.sqrt(dx**2 + dy**2)


# ---------------------------------------------------------------------------
# 3. Función de costo: suma de distancias ponderadas a cada cliente
# ---------------------------------------------------------------------------
def funcion_costo(punto_centro, lista_coordenadas, pesos=None):
    """
    f(x, y) = suma( w_i * distancia(centro, cliente_i) )
    Si no se especifican pesos, se usa peso 1 para todos los clientes.
    """
    if pesos is None:
        pesos = [1] * len(lista_coordenadas)

    costo = 0.0
    for cliente, peso in zip(lista_coordenadas, pesos):
        costo += peso * distancia_euclidiana(punto_centro, cliente)
    return costo


# ---------------------------------------------------------------------------
# 4. Gradiente de la función de costo (derivadas parciales respecto a x, y)
# ---------------------------------------------------------------------------
def calcular_gradiente(punto_centro, lista_coordenadas, pesos=None, epsilon=1e-9):
    """
    df/dx = suma( w_i * (x - x_i) / d_i )
    df/dy = suma( w_i * (y - y_i) / d_i )
    epsilon evita división entre cero si el centro coincide con un cliente.
    """
    if pesos is None:
        pesos = [1] * len(lista_coordenadas)

    x, y = punto_centro
    grad_x = 0.0
    grad_y = 0.0

    for (xi, yi), peso in zip(lista_coordenadas, pesos):
        d = distancia_euclidiana(punto_centro, (xi, yi))
        d_seguro = d if d > epsilon else epsilon  # evita dividir entre 0
        grad_x += peso * (x - xi) / d_seguro
        grad_y += peso * (y - yi) / d_seguro

    return [grad_x, grad_y]


def magnitud_vector(vector):
    """Magnitud (norma) de un vector 2D: usada para el criterio de convergencia."""
    return math.sqrt(vector[0]**2 + vector[1]**2)


# ---------------------------------------------------------------------------
# 5. Método del centro de gravedad (solución analítica directa)
#    Válido para minimizar la suma de distancias AL CUADRADO.
#    Se usa como caso de comparación/validación del descenso de gradiente.
# ---------------------------------------------------------------------------
def centro_de_gravedad(lista_coordenadas, pesos=None):
    """x* = suma(w_i * x_i) / suma(w_i);  y* = suma(w_i * y_i) / suma(w_i)"""
    if pesos is None:
        pesos = [1] * len(lista_coordenadas)

    suma_pesos = sum(pesos)
    x = sum(w * c[0] for c, w in zip(lista_coordenadas, pesos)) / suma_pesos
    y = sum(w * c[1] for c, w in zip(lista_coordenadas, pesos)) / suma_pesos
    return [x, y]


# ---------------------------------------------------------------------------
# 6. Descenso de gradiente: algoritmo principal, con historial completo
# ---------------------------------------------------------------------------
def descenso_gradiente(lista_coordenadas, pesos=None, alpha=1.0,
                        max_iteraciones=100, tolerancia=1e-4):
    """
    Ejecuta el descenso de gradiente y devuelve un diccionario con:
    - punto_optimo: [x, y] final
    - costo_final: valor de la función de costo en el punto óptimo
    - iteraciones: cuántas iteraciones tomó converger
    - historial_puntos, historial_costos, historial_gradientes: la "película"
      completa del proceso, para graficar convergencia y trayectoria.
    """
    punto_actual = calcular_punto_inicial(lista_coordenadas)

    historial_puntos = []
    historial_costos = []
    historial_gradientes = []
    convergio = False

    for iteracion in range(max_iteraciones):
        costo_actual = funcion_costo(punto_actual, lista_coordenadas, pesos)
        gradiente_actual = calcular_gradiente(punto_actual, lista_coordenadas, pesos)
        mag_gradiente = magnitud_vector(gradiente_actual)

        historial_puntos.append(list(punto_actual))
        historial_costos.append(costo_actual)
        historial_gradientes.append(mag_gradiente)

        if mag_gradiente < tolerancia:
            convergio = True
            break

        # Paso de descenso: nuevo_punto = punto_actual - alpha * gradiente
        punto_actual = [
            punto_actual[0] - alpha * gradiente_actual[0],
            punto_actual[1] - alpha * gradiente_actual[1],
        ]

    return {
        "punto_optimo": punto_actual,
        "costo_final": historial_costos[-1],
        "iteraciones": len(historial_puntos),
        "historial_puntos": historial_puntos,
        "historial_costos": historial_costos,
        "historial_gradientes": historial_gradientes,
        "convergio": convergio,
        "gradiente_final": historial_gradientes[-1]
    }


def optimizar_coordenadas_geograficas(
    clientes,
    pesos,
    alpha=0.3,
    max_iteraciones=100,
    tolerancia=0.0001
    ):
    """
    Convierte coordenadas GPS a CRTM05,
    realiza la optimización en metros
    y devuelve el punto óptimo nuevamente
    en coordenadas GPS.
    """

    # Convertir clientes a coordenadas métricas
    clientes_metros = []

    for longitud, latitud in clientes:

        x, y = a_metros.transform(
            longitud,
            latitud
        )

        clientes_metros.append((x, y))

    # Optimización original
    resultado = descenso_gradiente(
        clientes_metros,
        pesos,
        alpha=alpha,
        max_iteraciones=max_iteraciones,
        tolerancia=tolerancia
    )

    # Punto óptimo obtenido en metros
    x_optimo, y_optimo = resultado["punto_optimo"]

    # Convertir nuevamente a GPS
    longitud, latitud = a_gps.transform(
        x_optimo,
        y_optimo
    )

    # Guardamos ambos resultados
    resultado["punto_optimo_metros"] = (
        x_optimo,
        y_optimo
    )

    resultado["punto_optimo"] = (
        longitud,
        latitud
    )

    # El costo ahora está basado en metros
    resultado["costo_km"] = (
        resultado["costo_final"] / 1000
    )

    return resultado


# ---------------------------------------------------------------------------
# Ejecución de ejemplo (se usa también para generar los resultados del informe)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Clientes de ejemplo (coordenadas ficticias, unidades relativas / grados decimales)
    clientes = [
        (2.0, 3.0),
        (8.0, 2.0),
        (5.0, 9.0),
        (1.0, 7.0),
        (9.0, 8.0),
    ]
    pesos = [3, 5, 2, 4, 6]  # ej. volumen de demanda de cada cliente

    resultado = descenso_gradiente(clientes, pesos, alpha=0.3)

    print("Punto óptimo (descenso de gradiente):", resultado["punto_optimo"])
    print("Costo final:", resultado["costo_final"])
    print("Iteraciones:", resultado["iteraciones"])

    punto_cg = centro_de_gravedad(clientes, pesos)
    print("\nPunto de comparación (centro de gravedad, solución analítica):", punto_cg)
