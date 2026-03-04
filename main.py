# main.py
import pygame
import sys
import math
from config import ANCHO, ALTO, COLOR_FONDO, RADIO_HEX
from ProyectoViajero.tablero_hex import TableroHexagonal
from AgenteIA.AgenteHex import AgenteHex
from ProyectoViajero.ControlVoz import ControlVoz


# ─────────────────────────────────────────────────────────────────────────────
# Paletas de colores para visualización
# ─────────────────────────────────────────────────────────────────────────────
COLOR_NORMAL  = (30,  30,  60)
COLOR_INICIO  = (0,  220,  80)
COLOR_META    = (220,  50,  50)
COLOR_CAMINO  = (255, 215,   0)
COLOR_BFS_LO  = (10,  60,  100)
COLOR_BFS_HI  = (0,  220,  255)
COLOR_DFS_LO  = (50,   0,   80)
COLOR_DFS_HI  = (200,  0,  255)
COLOR_UCS_LO  = (80,  40,    0)
COLOR_UCS_HI  = (255, 160,   0)


def _lerp_color(c1, c2, t: float):
    """Interpolación lineal entre dos colores RGB, t ∈ [0, 1]."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )

class Juego:
    """Clase principal del juego con visualización de búsquedas."""

    # ── Inicialización ────────────────────────────────────────────────────────

    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Explorador Hexagonal – BFS / DFS / Costo Uniforme")
        self.reloj = pygame.time.Clock()

        # Tablero
        self.tablero = TableroHexagonal()
        self.tablero.asignar_costos_aleatorios()   # costos 1-3 para UCS

        # Cámara
        self.offset_x = ANCHO // 2
        self.offset_y = ALTO  // 2
        self.zoom     = 1.0

        # Fuentes
        self.fuente_sm = pygame.font.Font(None, 20)
        self.fuente_md = pygame.font.Font(None, 26)

        # Agente buscador
        self.agente = AgenteHex(self.tablero)

        # Control de voz
        self.voz = ControlVoz()

        # Posiciones inicio/meta (coordenadas axiales)
        self.inicio = (0,  0)
        self.meta   = (3, -3)

        # Resultado de la última búsqueda
        self.resultado = None   # dict con tecnica, camino, explorados, etc.

        # Variables para búsqueda paso a paso
        self.busqueda_activa = False
        self.generador_busqueda = None
        self.velocidad_busqueda = 10  # pasos por segundo
        self.contador_pasos = 0
        self.ultimo_tiempo = 0

        # Instrucciones HUD
        self.instrucciones = [
            "Flechas / +  -  : camara / zoom",
            "B  : BFS  (ondas concentricas)",
            "D  : DFS  (exploracion profunda)",
            "U  : Costo Uniforme",
            "C  : limpiar resultado",
            "ESPACIO : pausa/reanuda busqueda",
            "R / F : velocidad - / +",
            "Clic izq  :  mover INICIO",
            "Clic der  :  mover META",
            "ESC : salir",
            "V  : activar control por voz",
        ]

    # ── Coordenadas ───────────────────────────────────────────────────────────

    def _iniciar_busqueda_paso_a_paso(self, tecnica: str):
        """Inicia una búsqueda que se ejecutará paso a paso."""
        self.busqueda_activa = True
        self.generador_busqueda = self.agente.buscar_paso_a_paso(self.inicio, self.meta, tecnica)
        self.contador_pasos = 0
        self.ultimo_tiempo = pygame.time.get_ticks()
        
        # Limpiar resultado anterior pero mantener visualización
        self.resultado = None
        print(f"🔍 Iniciando búsqueda {tecnica} paso a paso...")

    # Avanzar un paso en la búsqueda
    def _avanzar_busqueda(self):
        """Ejecuta un paso de la búsqueda y actualiza visualización."""
        if not self.busqueda_activa or not self.generador_busqueda:
            return
        
        try:
            resultado_paso = next(self.generador_busqueda)
            estado = resultado_paso[0]
            
            if estado == 'EXPLORANDO':
                _, resultado_parcial = resultado_paso
                self.contador_pasos += 1
                resultado_parcial['paso_actual'] = self.contador_pasos
                self.resultado = resultado_parcial
                
            elif estado == 'ENCONTRADO':
                _, camino_final = resultado_paso
                self.busqueda_activa = False
                self.generador_busqueda = None
                
                self.resultado = self.agente._preparar_resultado_parcial(camino_final)
                self.resultado['en_progreso'] = False
                self.resultado['camino_set'] = set(camino_final)
                print(f"✅ Búsqueda completada en {self.contador_pasos} pasos")
                
            elif estado == 'NO_ENCONTRADO':
                self.busqueda_activa = False
                self.generador_busqueda = None
                print("❌ No se encontró camino")
                
        except StopIteration:
            self.busqueda_activa = False
            self.generador_busqueda = None

    def hex_a_pantalla(self, q, r):
        """Axial (q,r) → píxeles (x,y). Flat-top."""
        s = RADIO_HEX * self.zoom
        x = self.offset_x + s * 1.5 * q
        y = self.offset_y + s * math.sqrt(3) * (r + q / 2.0)
        return int(x), int(y)

    def pantalla_a_hex(self, px, py):
        """
        Píxeles (px,py) → coordenada axial (q,r) más cercana.
        Usa redondeo de coordenadas cúbicas.
        """
        s  = RADIO_HEX * self.zoom
        q  = (px - self.offset_x) / (s * 1.5)
        r  = (py - self.offset_y) / (s * math.sqrt(3)) - q / 2.0

        x_c, z_c = q, r
        y_c = -x_c - z_c
        rx, ry, rz = round(x_c), round(y_c), round(z_c)
        dx, dy, dz = abs(rx - x_c), abs(ry - y_c), abs(rz - z_c)
        if dx > dy and dx > dz:
            rx = -ry - rz
        elif dy > dz:
            ry = -rx - rz
        return (rx, rz)

    # ── Dibujo ────────────────────────────────────────────────────────────────

    def _vertices_hex(self, x, y):
        s = RADIO_HEX * self.zoom
        return [
            (x + s * math.cos(math.radians(60 * i)),
             y + s * math.sin(math.radians(60 * i)))
            for i in range(6)
        ]

    def _dibujar_hex(self, x, y, relleno, borde=(200, 200, 200), grosor=1):
        pts = self._vertices_hex(x, y)
        pygame.draw.polygon(self.pantalla, relleno, pts)
        pygame.draw.polygon(self.pantalla, borde,   pts, grosor)

    def _color_celda(self, q, r):
        """Color de relleno según el estado de la búsqueda."""
        pos = (q, r)
        if pos == self.inicio:
            return COLOR_INICIO
        if pos == self.meta:
            return COLOR_META

        if self.resultado is None:
            return COLOR_NORMAL

        tecnica    = self.resultado['tecnica']
        en_camino  = self.resultado['camino_set']
        explorados = self.resultado['explorados']

        if pos in en_camino:
            return COLOR_CAMINO

        if pos not in explorados:
            return COLOR_NORMAL

        idx = explorados.index(pos)
        t   = idx / max(len(explorados) - 1, 1)

        if tecnica == 'anchura':
            nivel_max = max(self.resultado['nivel_bfs'].values(), default=1)
            nivel     = self.resultado['nivel_bfs'].get(pos, 0)
            return _lerp_color(COLOR_BFS_LO, COLOR_BFS_HI,
                               nivel / max(nivel_max, 1))
        elif tecnica == 'profundidad':
            return _lerp_color(COLOR_DFS_LO, COLOR_DFS_HI, t)
        elif tecnica == 'costouniforme':
            costos   = self.resultado['costo_acumulado']
            costo_mx = max(costos.values(), default=1)
            return _lerp_color(COLOR_UCS_LO, COLOR_UCS_HI,
                               costos.get(pos, 0) / max(costo_mx, 1))
        return COLOR_NORMAL

    def _borde_celda(self, celda):
        """Para UCS, borde coloreado y más grueso en celdas caras."""
        if (self.resultado and
                self.resultado['tecnica'] == 'costouniforme' and
                celda.costo > 1):
            t = (celda.costo - 1) / 2.0
            color  = _lerp_color((180, 180, 180), (255, 80, 0), t)
            grosor = celda.costo
            return color, grosor
        return (200, 200, 200), 1

    def dibujar_tablero(self):
        for (q, r), celda in self.tablero.celdas.items():
            x, y   = self.hex_a_pantalla(q, r)
            relleno = self._color_celda(q, r)
            borde, grosor = self._borde_celda(celda)
            self._dibujar_hex(x, y, relleno, borde, grosor)

            # Coordenadas pequeñas
            txt = self.fuente_sm.render(f"{q},{r}", True, (150, 150, 190))
            self.pantalla.blit(txt, (x - 18, y - 8))

    def _dibujar_camino_lineas(self):
        """Traza el camino encontrado con líneas entre centros."""
        if not self.resultado or len(self.resultado['camino_lista']) < 2:
            return
        puntos = [self.hex_a_pantalla(*p) for p in self.resultado['camino_lista']]
        for i in range(len(puntos) - 1):
            pygame.draw.line(self.pantalla, (255, 255, 60),
                             puntos[i], puntos[i + 1], 3)
        for p in puntos:
            pygame.draw.circle(self.pantalla, (255, 255, 0), p, 4)

    def _dibujar_hud(self):
        # Instrucciones (izquierda)
        y = 10
        for linea in self.instrucciones:
            sf = self.fuente_sm.render(linea, True, (170, 170, 210))
            self.pantalla.blit(sf, (10, y))
            y += 18

        # Panel de métricas (derecha) si hay resultado
        if self.resultado:
            m       = self.resultado['metricas']
            nombres = {'anchura': 'BFS', 'profundidad': 'DFS',
                       'costouniforme': 'Costo Uniforme'}
            nombre  = nombres.get(self.resultado['tecnica'], '?')
            lineas  = [
                f"[ {nombre} ]",
                f"Pasos      : {m.get('pasos', '—')}",
                f"Costo      : {m.get('costo', '—')}",
                f"Expandidos : {m.get('nodos_expandidos', '—')}",
                f"Tiempo     : {m.get('tiempo', 0):.4f} s",
            ]
            bx, by = ANCHO - 230, 10
            fondo  = pygame.Surface((220, len(lineas) * 22 + 10), pygame.SRCALPHA)
            fondo.fill((10, 10, 30, 190))
            self.pantalla.blit(fondo, (bx - 5, by - 5))
            for i, linea in enumerate(lineas):
                color = (255, 220, 60) if i == 0 else (210, 210, 255)
                sf    = self.fuente_md.render(linea, True, color)
                self.pantalla.blit(sf, (bx, by))
                by += 22

        # Posiciones actuales (pie de pantalla)
        info = f"INICIO {self.inicio}     META {self.meta}"
        sf   = self.fuente_sm.render(info, True, (150, 255, 150))
        self.pantalla.blit(sf, (ANCHO // 2 - sf.get_width() // 2, ALTO - 22))

        # Leyenda de colores (esquina inferior derecha)
        leyenda = [
            (COLOR_INICIO, "INICIO  (clic izq)"),
            (COLOR_META,   "META    (clic der)"),
            (COLOR_CAMINO, "Camino"),
            (COLOR_BFS_HI, "BFS  explorado"),
            (COLOR_DFS_HI, "DFS  explorado"),
            (COLOR_UCS_HI, "UCS  explorado"),
        ]
        ly = ALTO - len(leyenda) * 20 - 14
        for color, etiqueta in leyenda:
            pygame.draw.rect(self.pantalla, color, (ANCHO - 168, ly, 13, 13))
            sf = self.fuente_sm.render(etiqueta, True, (200, 200, 200))
            self.pantalla.blit(sf, (ANCHO - 152, ly))
            ly += 20

    # ── Búsquedas ─────────────────────────────────────────────────────────────

    def _ejecutar_busqueda(self, tecnica: str):
        camino = self.agente.buscar(self.inicio, self.meta, tecnica)
        self.resultado = {
            'tecnica'        : tecnica,
            'camino_set'     : set(camino),
            'camino_lista'   : camino,
            'explorados'     : self.agente.explorados,
            'nivel_bfs'      : dict(self.agente.nivel_bfs),
            'costo_acumulado': dict(self.agente.costo_acumulado),
            'metricas'       : dict(self.agente.metricas),
        }

    # ── Eventos ───────────────────────────────────────────────────────────────

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False

            elif evento.type == pygame.KEYDOWN:
                k = evento.key
                if k == pygame.K_ESCAPE:
                    return False
                elif k == pygame.K_LEFT:
                    self.offset_x += 50
                elif k == pygame.K_RIGHT:
                    self.offset_x -= 50
                elif k == pygame.K_UP:
                    self.offset_y += 50
                elif k == pygame.K_DOWN:
                    self.offset_y -= 50
                elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    self.zoom *= 1.2
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.zoom = max(0.3, self.zoom / 1.2)
                elif k == pygame.K_b:
                    self._iniciar_busqueda_paso_a_paso('anchura')
                elif k == pygame.K_d:
                    self._iniciar_busqueda_paso_a_paso('profundidad')
                elif k == pygame.K_u:
                    self._iniciar_busqueda_paso_a_paso('costouniforme')
                elif k == pygame.K_v:
                    self.activar_voz()
                elif k == pygame.K_c:
                    self.resultado = None
                    self.busqueda_activa = False
                    self.generador_busqueda = None
                    print("🧹 Visualización limpiada")
                elif k == pygame.K_SPACE:
                    self.busqueda_activa = not self.busqueda_activa
                    estado = "REANUDADA" if self.busqueda_activa else "PAUSADA"
                    print(f"⏸️ Búsqueda {estado}")
                elif k == pygame.K_r:
                    self.velocidad_busqueda = max(1, self.velocidad_busqueda - 2)
                    print(f"🐢 Velocidad: {self.velocidad_busqueda} pasos/s")
                elif k == pygame.K_f:
                    self.velocidad_busqueda = min(30, self.velocidad_busqueda + 2)
                    print(f"🐇 Velocidad: {self.velocidad_busqueda} pasos/s")

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if self.busqueda_activa:
                    print("⏸️ Búsqueda pausada para mover posición")
                    self.busqueda_activa = False
                
                q, r = self.pantalla_a_hex(*evento.pos)
                if (q, r) in self.tablero.celdas:
                    if evento.button == 1:
                        self.inicio = (q, r)
                        self.resultado = None
                        print(f"🟢 INICIO → {self.inicio}")
                    elif evento.button == 3:
                        self.meta = (q, r)
                        self.resultado = None
                        print(f"🔴 META   → {self.meta}")

        return True

    # ── Bucle principal ───────────────────────────────────────────────────────

    def ejecutar(self):
        ejecutando = True
        while ejecutando:
            tiempo_actual = pygame.time.get_ticks()
            
            # Control de velocidad de búsqueda
            if self.busqueda_activa and self.generador_busqueda:
                paso_ms = 1000 // self.velocidad_busqueda
                if tiempo_actual - self.ultimo_tiempo >= paso_ms:
                    self._avanzar_busqueda()
                    self.ultimo_tiempo = tiempo_actual
            
            ejecutando = self.manejar_eventos()
            self.pantalla.fill(COLOR_FONDO)
            self.dibujar_tablero()
            self._dibujar_camino_lineas()
            self._dibujar_hud_paso_a_paso()  # Nueva función
            self._dibujar_hud()
            pygame.display.flip()
            self.reloj.tick(60)
        
        pygame.quit()
        sys.exit()

    def _dibujar_hud_paso_a_paso(self):
        """Muestra información de la búsqueda en progreso."""
        if self.busqueda_activa or (self.resultado and self.resultado.get('en_progreso')):
            # Barra de progreso
            y_base = 80
            ancho_barra = 300
            alto_barra = 20
            x_barra = 10
            
            # Fondo de la barra
            pygame.draw.rect(self.pantalla, (50, 50, 50), (x_barra, y_base, ancho_barra, alto_barra))
            
            # Progreso (aproximado)
            if hasattr(self.agente, 'explorados'):
                total_celdas = len(self.tablero.celdas)
                progreso = min(1.0, len(self.agente.explorados) / total_celdas)
                ancho_progreso = int(ancho_barra * progreso)
                pygame.draw.rect(self.pantalla, (0, 200, 0), (x_barra, y_base, ancho_progreso, alto_barra))
            
            # Texto de estado
            estado = "▶️ EN PROGRESO" if self.busqueda_activa else "⏸️ PAUSADA"
            if self.resultado and self.resultado.get('en_progreso'):
                texto = f"{estado} - Paso {self.contador_pasos}"
            else:
                texto = f"{estado}"
            
            sf = self.fuente_sm.render(texto, True, (255, 255, 100))
            self.pantalla.blit(sf, (x_barra, y_base - 20))
            
            # Velocidad
            vel_texto = f"Vel: {self.velocidad_busqueda} pasos/s (R/F)"
            sf_vel = self.fuente_sm.render(vel_texto, True, (180, 180, 180))
            self.pantalla.blit(sf_vel, (x_barra + ancho_barra + 20, y_base))

    def activar_voz(self):
        """Activa interacción por voz sin interferencia TTS-STT."""
        print("🎤 Activando control por voz...")

        # Pausar búsqueda si estaba activa
        if self.busqueda_activa:
            self.busqueda_activa = False

        # Habla y espera a que termine
        self.voz.hablar_y_esperar("Hola. ¿Cómo te sientes hoy?")

        # Ahora sí escucha
        texto = self.voz.escuchar()

        if not texto:
            self.voz.hablar("No pude escucharte bien. Intenta nuevamente.")
            return

        emocion = self.voz.detectar_emocion(texto)

        if emocion == "tristeza":
            self.voz.hablar("Vamos a buscar la zona de juego para ayudarte.")
            self._iniciar_busqueda_paso_a_paso('anchura')

        elif emocion == "miedo":
            self.voz.hablar("Busquemos un lugar tranquilo.")
            self._iniciar_busqueda_paso_a_paso('costouniforme')

        elif emocion == "enojo":
            self.voz.hablar("Te ayudaré a encontrar un abrazo.")
            self._iniciar_busqueda_paso_a_paso('profundidad')

        elif emocion == "alegria":
            self.voz.hablar("¡Qué bueno! Vamos a explorar.")
            self._iniciar_busqueda_paso_a_paso('anchura')

        elif emocion == "ansiedad":
            self.voz.hablar("Respiremos y busquemos un camino tranquilo.")
            self._iniciar_busqueda_paso_a_paso('costouniforme')

        else:
            self.voz.hablar("No entendí bien la emoción. ¿Puedes repetirlo?")

if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()
