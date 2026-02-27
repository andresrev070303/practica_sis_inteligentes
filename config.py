import math
# config.py
# Configuración básica del juego

# Dimensiones de la pantalla
ANCHO = 1200
ALTO = 800

# Configuración del tablero hexagonal
RADIO_TABLERO = 4   # Radio en celdas (4 → tablero de 61 hexágonos)
RADIO_HEX = 35      # Radio de cada hexágono en píxeles

# Colores básicos (RGB)
COLOR_FONDO = (10, 10, 30)      # Azul oscuro espacial
COLOR_TABLERO = (30, 30, 50)    # Gris azulado
COLOR_BORDE = (100, 100, 150)   # Azul claro
COLOR_TEXTO = (255, 255, 255)   # Blanco

# Direcciones para vecinos hexagonales (coordenadas axiales, flat-top)
DIRECCIONES_HEX = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]