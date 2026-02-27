# ProyectoViajero/tablero_hex.py
import math
from config import RADIO_TABLERO, DIRECCIONES_HEX


class Celda:
    """Representa una celda hexagonal del tablero"""

    def __init__(self, q, r):
        self.q = q  # Coordenada axial q  (positivo → derecha)
        self.r = r  # Coordenada axial r  (positivo → abajo-derecha)
        self.tipo = 'espacio'        # Por defecto, espacio vacío
        self.color = (50, 50, 80)    # Color por defecto
        self.emocion = None          # Personaje/emoción en esta celda
        self.planeta = None          # Planeta destino en esta celda
        self.costo = 1               # Costo de traversal (1 = normal, 2+ = difícil)

    def __repr__(self):
        return f"Celda({self.q},{self.r})"


class TableroHexagonal:
    """
    Tablero con FORMA HEXAGONAL usando coordenadas axiales centradas en (0,0).

    Todas las celdas (q, r) que cumplen  max(|q|, |r|, |q+r|) <= radio
    forman un hexágono perfecto de 'radio' anillos.
    """

    def __init__(self, radio: int = RADIO_TABLERO):
        self.radio = radio
        self.celdas: dict[tuple[int, int], Celda] = {}
        self._crear_tablero()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _crear_tablero(self):
        """Genera todas las celdas en forma de hexágono."""
        for q in range(-self.radio, self.radio + 1):
            r_min = max(-self.radio, -q - self.radio)
            r_max = min(self.radio, -q + self.radio)
            for r in range(r_min, r_max + 1):
                self.celdas[(q, r)] = Celda(q, r)
        total = len(self.celdas)
        print(f"✅ Tablero hexagonal creado: radio={self.radio}, {total} celdas")

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def obtener_vecinos(self, q: int, r: int) -> list[tuple[int, int]]:
        """Devuelve los vecinos válidos (que existen en el tablero)."""
        return [
            (q + dq, r + dr)
            for dq, dr in DIRECCIONES_HEX
            if (q + dq, r + dr) in self.celdas
        ]

    def obtener_celda(self, q: int, r: int) -> "Celda | None":
        """Obtiene la celda en (q, r) o None si no existe."""
        return self.celdas.get((q, r))

    def obtener_distancia(self, q1: int, r1: int, q2: int, r2: int) -> int:
        """
        Distancia hexagonal mínima entre dos celdas.
        Fórmula: (|dq| + |dr| + |dq+dr|) / 2
        """
        dq, dr = q2 - q1, r2 - r1
        return (abs(dq) + abs(dr) + abs(dq + dr)) // 2

    # ------------------------------------------------------------------
    # Colocación de elementos
    # ------------------------------------------------------------------

    def colocar_personaje(self, emocion: str, q: int, r: int):
        """Coloca un personaje (emoción) en una celda."""
        if (q, r) in self.celdas:
            self.celdas[(q, r)].emocion = emocion
            print(f"👤 Personaje '{emocion}' colocado en ({q},{r})")
        else:
            print(f"⚠️  ({q},{r}) está fuera del tablero hexagonal")

    def colocar_planeta(self, planeta: str, q: int, r: int):
        """Coloca un planeta destino en una celda."""
        if (q, r) in self.celdas:
            self.celdas[(q, r)].planeta = planeta
            print(f"🪐 Planeta '{planeta}' colocado en ({q},{r})")
        else:
            print(f"⚠️  ({q},{r}) está fuera del tablero hexagonal")

    # ------------------------------------------------------------------

    def asignar_costos_aleatorios(self, semilla: int = 42):
        """
        Asigna costos variados a las celdas para demostrar la Búsqueda de
        Costo Uniforme.  Distribución: 60% costo 1, 25% costo 2, 15% costo 3.
        El inicio y la meta siempre conservan costo 1.
        """
        import random
        rng = random.Random(semilla)
        pesos = [1] * 6 + [2] * 3 + [3] * 1  # distribución 60/30/10
        for celda in self.celdas.values():
            celda.costo = rng.choice(pesos)
        print("⚡ Costos asignados aleatoriamente a las celdas")

    def __repr__(self):
        return f"TableroHexagonal(radio={self.radio}, celdas={len(self.celdas)})"
