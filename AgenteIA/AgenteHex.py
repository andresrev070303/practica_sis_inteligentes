# ************************************************************
# * Clase: AgenteHex                                         *
# * Descripción: Agente buscador especializado para el       *
# *              tablero hexagonal del juego.                *
# *              Implementa BFS, DFS y Costo Uniforme        *
# *              con trazabilidad para visualización.        *
# ************************************************************

import time
import heapq
from AgenteIA.Agente import Agente
from ProyectoViajero.tablero_hex import TableroHexagonal


class AgenteHex(Agente):
    """
    Agente buscador para el tablero hexagonal.

    Algoritmos disponibles (parámetro 'tecnica'):
        'anchura'       →  BFS  – camino más corto en pasos
        'profundidad'   →  DFS  – exploración profunda
        'costouniforme' →  UCS  – camino de mínimo costo
    """

    def __init__(self, tablero: TableroHexagonal):
        super().__init__()
        self.tablero = tablero

        # Configuración de la búsqueda
        self._inicio: tuple | None = None
        self._meta: tuple | None = None
        self._tecnica: str | None = None

        # ── Resultados expuestos para visualización ──────────────────
        self.camino: list[tuple] = []          # camino final [inicio, ..., meta]
        self.explorados: list[tuple] = []      # orden de expansión de nodos
        self.nivel_bfs: dict[tuple, int] = {}  # (q,r) → onda BFS
        self.costo_acumulado: dict[tuple, float] = {}  # (q,r) → costo UCS
        self.metricas: dict = {}

    # ─────────────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────────────

    def buscar(self, inicio: tuple, meta: tuple, tecnica: str) -> list[tuple]:
        """
        Ejecuta la búsqueda y devuelve el camino encontrado (o [] si no hay).
        También llena self.explorados, self.nivel_bfs / self.costo_acumulado
        y self.metricas para que main.py pueda dibujar la visualización.
        """
        self._inicio = inicio
        self._meta   = meta
        self._tecnica = tecnica

        # Reset
        self.camino = []
        self.explorados = []
        self.nivel_bfs = {}
        self.costo_acumulado = {}
        self.metricas = {}

        t0 = time.time()
        resultado = self.programa()
        self.metricas['tiempo'] = round(time.time() - t0, 6)

        self.camino = resultado if resultado else []
        self.set_acciones(self.camino)

        if not resultado:
            print(f"⚠️  [{tecnica.upper()}] No se encontró camino de {inicio} a {meta}")
        else:
            print(
                f"✅  [{tecnica.upper()}]  "
                f"Pasos={self.metricas.get('pasos',0)}  "
                f"Costo={self.metricas.get('costo',0)}  "
                f"Expandidos={self.metricas.get('nodos_expandidos',0)}  "
                f"Tiempo={self.metricas['tiempo']:.4f}s"
            )

        return self.camino

    def programa(self):
        """Despacha al algoritmo indicado por self._tecnica."""
        if self._tecnica == 'anchura':
            return self._bfs()
        elif self._tecnica == 'profundidad':
            return self._dfs()
        elif self._tecnica == 'costouniforme':
            return self._ucs()
        else:
            raise ValueError(f"Técnica desconocida: '{self._tecnica}'")

    # ─────────────────────────────────────────────────────────────────
    # Helpers internos
    # ─────────────────────────────────────────────────────────────────

    def _costo_celda(self, q: int, r: int) -> int:
        """Devuelve el costo de atravesar la celda (q, r)."""
        celda = self.tablero.obtener_celda(q, r)
        return celda.costo if celda else 1

    def _heuristica(self, q: int, r: int) -> int:
        """Distancia hexagonal desde (q,r) hasta la meta (útil para A*)."""
        mq, mr = self._meta
        return self.tablero.obtener_distancia(q, r, mq, mr)

    # ─────────────────────────────────────────────────────────────────
    # BFS – Breadth-First Search
    # Complejidad: O(V + E)
    # Garantiza el camino más corto en número de pasos.
    # ─────────────────────────────────────────────────────────────────

    def _bfs(self) -> list | None:
        from collections import deque

        inicio, meta = self._inicio, self._meta

        frontera   = deque([[inicio]])   # cola FIFO de caminos
        visitados  = {inicio}            # conjunto para O(1) lookup
        self.nivel_bfs[inicio] = 0
        nodos_expandidos = 0

        while frontera:
            camino = frontera.popleft()
            nodo   = camino[-1]
            nodos_expandidos += 1
            self.explorados.append(nodo)

            if nodo == meta:
                self.metricas.update({
                    'pasos'            : len(camino) - 1,
                    'costo'            : len(camino) - 1,  # costo uniforme en BFS
                    'nodos_expandidos' : nodos_expandidos,
                })
                return camino

            for vecino in self.tablero.obtener_vecinos(*nodo):
                if vecino not in visitados:
                    visitados.add(vecino)
                    self.nivel_bfs[vecino] = self.nivel_bfs[nodo] + 1
                    frontera.append(camino + [vecino])

        self.metricas['nodos_expandidos'] = nodos_expandidos
        return None

    # ─────────────────────────────────────────────────────────────────
    # DFS – Depth-First Search
    # Complejidad: O(V + E)
    # No garantiza el camino más corto; explora profundamente.
    # ─────────────────────────────────────────────────────────────────

    def _dfs(self) -> list | None:
        inicio, meta = self._inicio, self._meta

        frontera   = [[inicio]]   # pila LIFO
        visitados  = set()
        nodos_expandidos = 0

        while frontera:
            camino = frontera.pop()
            nodo   = camino[-1]

            if nodo in visitados:
                continue
            visitados.add(nodo)
            nodos_expandidos += 1
            self.explorados.append(nodo)

            if nodo == meta:
                costo = sum(self._costo_celda(*n) for n in camino[1:])
                self.metricas.update({
                    'pasos'            : len(camino) - 1,
                    'costo'            : costo,
                    'nodos_expandidos' : nodos_expandidos,
                })
                return camino

            # Invertir para explorar en orden natural (primer vecino primero)
            for vecino in reversed(self.tablero.obtener_vecinos(*nodo)):
                if vecino not in visitados:
                    frontera.append(camino + [vecino])

        self.metricas['nodos_expandidos'] = nodos_expandidos
        return None

    # ─────────────────────────────────────────────────────────────────
    # UCS – Uniform Cost Search (Dijkstra sin heurística)
    # Complejidad: O((V + E) log V)
    # Garantiza el camino de menor costo acumulado.
    # ─────────────────────────────────────────────────────────────────

    def _ucs(self) -> list | None:
        inicio, meta = self._inicio, self._meta

        # heap: (costo_acumulado, contador_desempate, camino)
        contador = 0
        heap     = [(0, contador, [inicio])]
        visitados: dict[tuple, float] = {}  # nodo → menor costo conocido
        nodos_expandidos = 0
        self.costo_acumulado[inicio] = 0

        while heap:
            costo, _, camino = heapq.heappop(heap)
            nodo = camino[-1]

            # Si ya expandimos este nodo con menor costo, saltar
            if nodo in visitados and visitados[nodo] <= costo:
                continue
            visitados[nodo] = costo
            self.costo_acumulado[nodo] = costo
            nodos_expandidos += 1
            self.explorados.append(nodo)

            if nodo == meta:
                self.metricas.update({
                    'pasos'            : len(camino) - 1,
                    'costo'            : costo,
                    'nodos_expandidos' : nodos_expandidos,
                })
                return camino

            for vecino in self.tablero.obtener_vecinos(*nodo):
                nuevo_costo = costo + self._costo_celda(*vecino)
                if vecino not in visitados or visitados[vecino] > nuevo_costo:
                    contador += 1
                    heapq.heappush(heap, (nuevo_costo, contador, camino + [vecino]))

        self.metricas['nodos_expandidos'] = nodos_expandidos
        return None
