# ProyectoViajero/tablero_hex.py
import math
from config import RADIO_TABLERO, DIRECCIONES_HEX


class Celda:
    """Representa una celda hexagonal del tablero"""

    def __init__(self, q, r):
        self.q = q
        self.r = r
        self.tipo = 'espacio'
        self.color = (50, 50, 80)
        self.emocion = None
        self.planeta = None
        self.costo = 1
        self.obstaculo = None
        self.es_planeta = False
        self.planeta_emocion = None

    def __repr__(self):
        return f"Celda({self.q},{self.r})"


class TableroHexagonal:
    """
    Tablero con FORMA HEXAGONAL usando coordenadas axiales centradas en (0,0).
    """

    def __init__(self, radio: int = 4):
        self.radio = radio
        self.celdas: dict[tuple[int, int], Celda] = {}
        self._crear_tablero()
        self.colores_obstaculos = {
            'asteroide': (139, 69, 19),      # Marrón
            'tormenta': (128, 128, 128),      # Gris
            'agujero_negro': (0, 0, 0)         # Negro
        }
        self.planetas = {}  # Guardar posiciones de planetas

    def _crear_tablero(self):
        """Genera todas las celdas en forma de hexágono."""
        for q in range(-self.radio, self.radio + 1):
            r_min = max(-self.radio, -q - self.radio)
            r_max = min(self.radio, -q + self.radio)
            for r in range(r_min, r_max + 1):
                self.celdas[(q, r)] = Celda(q, r)
        total = len(self.celdas)
        print(f"✅ Tablero hexagonal creado: radio={self.radio}, {total} celdas")

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
        """Distancia hexagonal mínima entre dos celdas."""
        dq, dr = q2 - q1, r2 - r1
        return (abs(dq) + abs(dr) + abs(dq + dr)) // 2

    def colocar_planeta(self, emocion: str, q: int, r: int):
        """Coloca un planeta destino en una celda."""
        if (q, r) in self.celdas:
            celda = self.celdas[(q, r)]
            celda.planeta = emocion
            celda.es_planeta = True
            celda.planeta_emocion = emocion
            celda.costo = 1  # El planeta en sí no tiene costo extra
            self.planetas[emocion] = (q, r)

    def colocar_obstaculo(self, tipo: str, q: int, r: int, costo: int):
        """Coloca un obstáculo en una celda."""
        if (q, r) in self.celdas:
            celda = self.celdas[(q, r)]
            celda.obstaculo = tipo
            celda.costo = costo
            celda.tipo = tipo

    def configurar_desde_nivel(self, nivel):
        """Configura el tablero según el nivel."""
        self.radio = nivel.get("radio_tablero", 4)
        self._crear_tablero()
        self.planetas = {}
        
        # Establecer costo normal por defecto
        costo_normal = 1
        
        # Si existe la clave "costos", obtener valores
        if "costos" in nivel:
            costo_normal = nivel["costos"].get("normal", 1)
        
        # Asignar costo normal a todas las celdas
        for celda in self.celdas.values():
            celda.costo = costo_normal
        
        # Colocar planetas
        for emocion, pos in nivel["planetas"].items():
            self.colocar_planeta(emocion, pos[0], pos[1])
        
        # Colocar obstáculos (si existen)
        for obs in nivel.get("obstaculos", []):
            tipo = obs["tipo"]
            q, r = obs["posicion"]
            # Los obstáculos tienen costo alto pero NO se puede pasar
            self.colocar_obstaculo(tipo, q, r, 999)

    def obtener_costo_celda(self, q: int, r: int, emocion_destino: str = None) -> int:
        """
        Obtiene el costo de una celda.
        Si es un planeta y NO es el destino, cuesta 5.
        """
        celda = self.obtener_celda(q, r)
        if not celda:
            return 999  # Costo infinito si no existe
        
        # Si es un planeta y NO es el destino, cuesta 5
        if celda.es_planeta and celda.planeta != emocion_destino:
            return 5
        
        # Si tiene obstáculo, usar su costo
        if celda.obstaculo:
            return celda.costo
        
        # Costo normal
        return 1

    def obtener_color_celda(self, q, r, emocion_destino=None):
        """Devuelve el color de la celda para dibujar."""
        celda = self.obtener_celda(q, r)
        if not celda:
            return (50, 50, 80)
        
        # Si es el planeta destino, usar color especial (se dibuja aparte)
        if celda.es_planeta and celda.planeta == emocion_destino:
            return None  # None indica que se dibujará como planeta
        
        # Si es otro planeta, color gris con borde
        if celda.es_planeta:
            return (80, 80, 100)  # Color para otros planetas
        
        # Si tiene obstáculo
        if celda.obstaculo:
            return self.colores_obstaculos.get(celda.obstaculo, (255, 0, 255))
        
        return (50, 50, 80)  # Color normal
    
    # En ProyectoViajero/tablero_hex.py, añade este método:

    def obtener_color_obstaculo(self, q, r):
        """Devuelve el color del obstáculo en la celda (q,r)"""
        celda = self.obtener_celda(q, r)
        if celda and celda.obstaculo:
            return self.colores_obstaculos.get(celda.obstaculo, (255, 0, 255))
        return None
    
    def es_transitable(self, q: int, r: int, emocion_destino: str = None) -> bool:
        """
        Determina si una celda es transitable para el camino final.
        No se puede pasar por:
        - Obstáculos (asteroides, tormentas, agujeros negros)
        - Otros planetas (que no sean el destino)
        """
        celda = self.obtener_celda(q, r)
        if not celda:
            return False
        
        # No se puede pasar por obstáculos
        if celda.obstaculo:
            return False
        
        # No se puede pasar por otros planetas (excepto el destino)
        if celda.es_planeta and celda.planeta != emocion_destino:
            return False
        
        return True
