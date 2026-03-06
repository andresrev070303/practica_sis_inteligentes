# main.py
import pygame
import sys
import math
import random
from config import ANCHO, ALTO, COLOR_FONDO, RADIO_HEX
from ProyectoViajero.tablero_hex import TableroHexagonal
from AgenteIA.AgenteHex import AgenteHex
from ProyectoViajero.ControlVoz import ControlVoz
from niveles import GestorNiveles


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
COLOR_GAME_OVER = (255, 0, 0, 200)
COLOR_VICTORIA = (0, 255, 0, 200)

# Colores para emociones y planetas
COLOR_EMOCIONES = {
    "tristeza": (0, 0, 255),      # Azul
    "miedo": (128, 0, 128),       # Morado
    "enojo": (255, 0, 0),          # Rojo
    "alegria": (255, 255, 0),      # Amarillo
    "ansiedad": (0, 255, 0)        # Verde
}

PLANETAS = {
    "tristeza": "Juego",
    "miedo": "Calma",
    "enojo": "Abrazo",
    "alegria": "Amigos",
    "ansiedad": "Respiración"
}

# Posiciones de los planetas (coordenadas)
POSICIONES_PLANETAS = {
    "tristeza": (3, -3),    # Planeta Juego
    "miedo": (-2, 2),        # Planeta Calma
    "enojo": (0, 4),         # Planeta Abrazo
    "alegria": (-3, 0),      # Planeta Amigos
    "ansiedad": (2, 2)       # Planeta Respiración
}


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
        
        # Configurar pantalla del tamaño de config.py (NO fullscreen)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Conexión Mental - Búsqueda No Informada")
        self.reloj = pygame.time.Clock()

        # Cámara - centrada
        self.offset_x = ANCHO // 2
        self.offset_y = ALTO // 2
        self.zoom     = 1.0

        # Fuentes
        self.fuente_sm = pygame.font.Font(None, 20)
        self.fuente_md = pygame.font.Font(None, 26)
        self.fuente_grande = pygame.font.Font(None, 36)

        # Control de voz
        self.voz = ControlVoz()

        # Gestor de niveles
        self.gestor_niveles = GestorNiveles()
        
        # Estado del juego
        self.estado = "SELECCION_EMOCION"  # SELECCION_EMOCION, BUSCANDO, COMPLETADO, GAME_OVER, VICTORIA
        self.emocion_seleccionada = None
        self.mensaje_estado = ""
        self.tiempo_mensaje = 0
        
        # Posiciones fijas
        self.inicio = (0, 0)
        
        # Tablero (se carga al iniciar)
        self.cargar_nivel(0)
        
        # Resultados
        self.resultado = None
        self.resultado_elegido = None
        self.estadisticas = None
        self.estadisticas_elegidas = None

        # Variables para búsqueda paso a paso
        self.busqueda_activa = False
        self.generador_busqueda = None
        self.velocidad_busqueda = 10
        self.contador_pasos = 0
        self.ultimo_tiempo = 0

        # Menús
        self.mostrar_menu_emociones = True
        self.botones_menu = []
        self.boton_elegir_rect = None
        self.mostrar_boton_elegir = False
        self.boton_siguiente_rect = None

        # Opciones de búsqueda
        self.opciones_busqueda = [
            ("B", "BFS", "Nave Exploradora", (0, 170, 255)),
            ("D", "DFS", "Nave Aventurera", (255, 170, 0)),
            ("U", "UCS", "Nave Estratega", (255, 100, 0))
        ]

    def cargar_nivel(self, idx):
        """Carga la configuración de un nivel"""
        nivel = self.gestor_niveles.obtener_nivel(idx)
        
        # Configurar tablero con radio del nivel
        radio = nivel.get("radio_tablero", 4)
        self.tablero = TableroHexagonal(radio)
        
        # Configurar el tablero con planetas y obstáculos desde el nivel
        self.tablero.configurar_desde_nivel(nivel)
        
        # Reiniciar agente con nuevo tablero
        self.agente = AgenteHex(self.tablero)
        
        # Energía (batería)
        self.bateria_infinita = nivel.get("bateria_infinita", False)
        if not self.bateria_infinita:
            self.energia_total = nivel.get("bateria_inicial", 15)
            self.energia_restante = self.energia_total
        else:
            self.energia_total = 999
            self.energia_restante = 999
        
        # Inicio del nivel (puede variar)
        inicio_coords = nivel.get("inicio", [0, 0])
        self.inicio = tuple(inicio_coords)
        
        # IMPORTANTE: NO definir meta aquí. Será cuando seleccione emoción
        self.meta = None
        
        # Reiniciar estados
        self.emocion_seleccionada = None
        self.resultado = None
        self.resultado_elegido = None
        self.estadisticas = None
        self.estadisticas_elegidas = None
        self.mostrar_menu_emociones = True
        self.estado = "SELECCION_EMOCION"
        
        print(f"📖 Nivel {idx}: {nivel['nombre']}")
        print(f"🚀 Inicio: {self.inicio}")
        print(f"🌍 Planetas disponibles: {list(nivel['planetas'].keys())}")
        if not self.bateria_infinita:
            print(f"🔋 Batería inicial: {self.energia_total}")
        else:
            print(f"🔋 Batería: INFINITA")

    # ── Menú de emociones ───────────────────────────────────────────────────

    def dibujar_menu_emociones(self):
        """Dibuja el menú para seleccionar emoción"""
        x_centro = ANCHO // 2
        y_base = 150
        
        # Fondo semitransparente
        fondo = pygame.Surface((500, 350), pygame.SRCALPHA)
        fondo.fill((0, 0, 0, 220))
        self.pantalla.blit(fondo, (x_centro - 250, y_base - 30))
        
        # Título
        titulo = self.fuente_grande.render("¿CÓMO TE SIENTES HOY?", True, (255, 255, 100))
        self.pantalla.blit(titulo, (x_centro - titulo.get_width() // 2, y_base - 20))
        
        # Subtítulo
        sub = self.fuente_sm.render("(Presiona V para hablar o haz clic en una emoción)", True, (200, 200, 200))
        self.pantalla.blit(sub, (x_centro - sub.get_width() // 2, y_base + 10))
        
        # Botones de emociones
        self.botones_menu = []
        emociones = [
            ("tristeza", "Tristeza", (0, 0, 255)),
            ("miedo", "Miedo", (128, 0, 128)),
            ("enojo", "Enojo", (255, 0, 0)),
            ("alegria", "Alegría", (255, 255, 0)),
            ("ansiedad", "Ansiedad", (0, 255, 0))
        ]
        
        for i, (key, nombre, color) in enumerate(emociones):
            y_boton = y_base + 70 + i * 45
            rect = pygame.Rect(x_centro - 150, y_boton, 300, 35)
            
            pygame.draw.rect(self.pantalla, color, rect)
            pygame.draw.rect(self.pantalla, (255, 255, 255), rect, 2)
            
            texto = f"{i+1}. {nombre} → Planeta {PLANETAS[key]}"
            sf = self.fuente_md.render(texto, True, (255, 255, 255))
            self.pantalla.blit(sf, (x_centro - 140, y_boton + 5))
            
            self.botones_menu.append({'rect': rect, 'emocion': key})
        
        # Instrucción voz
        voz_texto = "🎤 O presiona V y di: 'Estoy triste', 'Tengo miedo', etc."
        sf_voz = self.fuente_sm.render(voz_texto, True, (150, 255, 150))
        self.pantalla.blit(sf_voz, (x_centro - sf_voz.get_width() // 2, y_base + 320))

    # ── Manejo de selección ─────────────────────────────────────────────────

    def seleccionar_emocion(self, emocion):
        """Procesa la emoción seleccionada"""
        self.emocion_seleccionada = emocion
        
        # IMPORTANTE: La meta debe ser la posición del planeta de esa emoción
        nivel = self.gestor_niveles.obtener_nivel()
        self.meta = tuple(nivel["planetas"][emocion])  # <-- CORREGIDO: usa planetas[emocion]
        
        planeta = PLANETAS[emocion]
        print(f"🎯 Emoción: {emocion} → Planeta {planeta} en {self.meta}")
        
        self.voz.hablar(f"Tenemos que ir al planeta {planeta}")
        
        self.estado = "BUSCANDO"
        self.mostrar_menu_emociones = False
        self.estadisticas = None
        self.estadisticas_elegidas = None
        self.resultado_elegido = None
        
        # Restaurar energía
        if not self.bateria_infinita:
            self.energia_restante = self.energia_total
        
        pygame.time.wait(1500)
        self.voz.hablar("Elige una nave: B, D o U")

    # ── Búsqueda ───────────────────────────────────────────────────────────

    def _iniciar_busqueda_paso_a_paso(self, tecnica: str):
        """Inicia una búsqueda paso a paso"""
        # Verificar batería
        if not self.bateria_infinita and self.energia_restante <= 0:
            self.mostrar_mensaje("¡Sin batería! Presiona N para siguiente nivel", (255, 0, 0))
            return
        
        self.busqueda_activa = True
        self.generador_busqueda = self.agente.buscar_paso_a_paso(
            self.inicio, 
            self.meta, 
            tecnica,
            self.emocion_seleccionada  # Pasar la emoción destino
        )
        self.contador_pasos = 0
        self.ultimo_tiempo = pygame.time.get_ticks()
        self.resultado = None
        self.estadisticas = None
        self.mostrar_boton_elegir = False
        
        nombres = {'anchura': 'Exploradora', 'profundidad': 'Aventurera', 'costouniforme': 'Estratega'}
        print(f"🚀 Iniciando {nombres[tecnica]}...")
        self.voz.hablar(f"Usando nave {nombres[tecnica]}")

    def _avanzar_busqueda(self):
        """Ejecuta un paso de la búsqueda"""
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
                
                pasos_totales = self.contador_pasos
                casillas_camino = len(camino_final)
                energia_gastada = casillas_camino - 1
                
                self.estadisticas = {
                    'pasos_totales': pasos_totales,
                    'casillas_camino': casillas_camino,
                    'energia_gastada': energia_gastada,
                    'energia_restante': self.energia_restante - energia_gastada if not self.bateria_infinita else self.energia_restante,
                    'tecnica': self.resultado.get('tecnica', 'anchura')
                }
                
                self.resultado = self.agente._preparar_resultado_parcial(camino_final)
                self.resultado['camino_set'] = set(camino_final)
                
                print(f"✅ Búsqueda completada! Energía a gastar: {energia_gastada}")
                self.mostrar_boton_elegir = True
                
            elif estado == 'NO_ENCONTRADO':
                self.busqueda_activa = False
                self.generador_busqueda = None
                self.mostrar_mensaje("No se encontró camino. Prueba otra nave.", (255, 100, 0))
                
        except StopIteration:
            self.busqueda_activa = False
            self.generador_busqueda = None

    def elegir_nave_actual(self):
        """Elige la nave actual como definitiva"""
        if not self.estadisticas:
            return
        
        energia_gastada = self.estadisticas['energia_gastada']
        
        # Verificar si tiene suficiente batería
        if not self.bateria_infinita and energia_gastada > self.energia_restante:
            self.mostrar_mensaje("¡No tienes suficiente batería para esta ruta!", (255, 0, 0))
            self.voz.hablar("No tienes suficiente batería. Prueba otra nave.")
            return
        
        # Guardar resultado elegido
        self.resultado_elegido = self.resultado
        self.estadisticas_elegidas = self.estadisticas.copy()
        
        # Restar energía
        if not self.bateria_infinita:
            self.energia_restante -= energia_gastada
        
        self.mostrar_boton_elegir = False
        
        # Verificar si llegó a la meta
        if self.energia_restante >= 0:
            nivel = self.gestor_niveles.obtener_nivel()
            if "victoria" in nivel["mensajes"]:
                self.mostrar_mensaje(nivel["mensajes"]["victoria"], (0, 255, 0))
            else:
                self.mostrar_mensaje("¡Llegamos al planeta!", (0, 255, 0))
            self.voz.hablar("¡Llegamos al planeta!")
            self.estado = "COMPLETADO"
        else:
            self.estado = "GAME_OVER"
            nivel = self.gestor_niveles.obtener_nivel()
            self.mostrar_mensaje(nivel["mensajes"]["derrota"], (255, 0, 0))

    # ── Dibujo ─────────────────────────────────────────────────────────────

    def _color_celda(self, q, r):
        """Color de relleno según el estado de la búsqueda y obstáculos."""
        pos = (q, r)
        
        # Prioridad 1: Inicio y Meta
        if pos == self.inicio:
            return COLOR_INICIO
        if pos == self.meta:
            return COLOR_META

        # Prioridad: Mostrar obstáculos si no hay búsqueda activa
        if self.resultado is None and self.resultado_elegido is None:
            celda = self.tablero.obtener_celda(q, r)
            if celda and celda.obstaculo:
                color_obs = self.tablero.obtener_color_obstaculo(q, r)
                if color_obs:
                    return color_obs
            return COLOR_NORMAL

        # Resto igual que antes...
        resultado_actual = self.resultado_elegido if self.resultado_elegido else self.resultado
        
        if not resultado_actual:
            return COLOR_NORMAL

        if 'camino_set' in resultado_actual and pos in resultado_actual['camino_set']:
            return COLOR_CAMINO

        explorados = resultado_actual.get('explorados', [])
        if pos not in explorados:
            celda = self.tablero.obtener_celda(q, r)
            if celda and celda.obstaculo:
                color_obs = self.tablero.obtener_color_obstaculo(q, r)
                if color_obs:
                    return color_obs
            return COLOR_NORMAL

        idx = explorados.index(pos)
        t = idx / max(len(explorados) - 1, 1)
        tecnica = resultado_actual.get('tecnica', 'anchura')

        if tecnica == 'anchura':
            nivel_max = max(resultado_actual.get('nivel_bfs', {0:1}).values(), default=1)
            nivel = resultado_actual.get('nivel_bfs', {}).get(pos, 0)
            return _lerp_color(COLOR_BFS_LO, COLOR_BFS_HI, nivel / max(nivel_max, 1))
        elif tecnica == 'profundidad':
            return _lerp_color(COLOR_DFS_LO, COLOR_DFS_HI, t)
        elif tecnica == 'costouniforme':
            costos = resultado_actual.get('costo_acumulado', {})
            costo_mx = max(costos.values(), default=1)
            return _lerp_color(COLOR_UCS_LO, COLOR_UCS_HI, costos.get(pos, 0) / max(costo_mx, 1))
        
        return COLOR_NORMAL

    def _dibujar_camino_lineas(self):
        """Dibuja el camino final"""
        resultado_actual = self.resultado_elegido if self.resultado_elegido else self.resultado
        if not resultado_actual or len(resultado_actual.get('camino_lista', [])) < 2:
            return
        
        puntos = [self.hex_a_pantalla(*p) for p in resultado_actual['camino_lista']]
        for i in range(len(puntos) - 1):
            pygame.draw.line(self.pantalla, (255, 255, 60), puntos[i], puntos[i + 1], 3)

    def dibujar_tablero(self):
        """Dibuja el tablero hexagonal con planetas y obstáculos"""
        for (q, r), celda in self.tablero.celdas.items():
            x, y = self.hex_a_pantalla(q, r)
            
            # Obtener color base
            color_base = self._color_celda(q, r)
            
            # Si es un planeta y no es el destino, pintar de gris
            if celda.es_planeta and celda.planeta != self.emocion_seleccionada:
                color_base = (80, 80, 100)
            
            # Dibujar hexágono
            self._dibujar_hex(x, y, color_base)
            
            # Si es un planeta, dibujar círculo
            if celda.es_planeta:
                if celda.planeta == self.emocion_seleccionada:
                    # Planeta destino (resaltado)
                    color_planeta = COLOR_EMOCIONES.get(celda.planeta, (255, 255, 255))
                    pygame.draw.circle(self.pantalla, color_planeta, (x, y), 15)
                    pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y), 15, 3)
                    # Brillo alrededor del planeta destino
                    for i in range(3):
                        radio_brillo = 20 + i * 3
                        alpha = 100 - i * 30
                        brillo = pygame.Surface((radio_brillo*2, radio_brillo*2), pygame.SRCALPHA)
                        pygame.draw.circle(brillo, (*color_planeta, alpha), (radio_brillo, radio_brillo), radio_brillo)
                        self.pantalla.blit(brillo, (x - radio_brillo, y - radio_brillo))
                else:
                    # Otros planetas (normales)
                    color_planeta = COLOR_EMOCIONES.get(celda.planeta, (255, 255, 255))
                    pygame.draw.circle(self.pantalla, color_planeta, (x, y), 12)
                    pygame.draw.circle(self.pantalla, (200, 200, 200), (x, y), 12, 2)
                
                # Inicial del planeta
                letra = PLANETAS[celda.planeta][0]
                sf = self.fuente_sm.render(letra, True, (255, 255, 255))
                self.pantalla.blit(sf, (x - 5, y - 8))
            
            # Si tiene obstáculo, dibujar símbolo
            elif celda.obstaculo:
                if celda.obstaculo == 'asteroide':
                    pygame.draw.circle(self.pantalla, (200, 200, 200), (x, y), 5)
                    pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y), 5, 1)
                elif celda.obstaculo == 'tormenta':
                    for i in range(3):
                        pygame.draw.circle(self.pantalla, (200, 200, 200), (x + i*3, y - i*2), 2)
                elif celda.obstaculo == 'agujero_negro':
                    pygame.draw.circle(self.pantalla, (0, 0, 0), (x, y), 8)
                    pygame.draw.circle(self.pantalla, (255, 0, 255), (x, y), 8, 1)

    def _dibujar_hex(self, x, y, relleno, borde=(200, 200, 200), grosor=1):
        pts = []
        s = RADIO_HEX * self.zoom
        for i in range(6):
            angulo = math.radians(60 * i)
            pts.append((x + s * math.cos(angulo), y + s * math.sin(angulo)))
        pygame.draw.polygon(self.pantalla, relleno, pts)
        pygame.draw.polygon(self.pantalla, borde, pts, grosor)

    def hex_a_pantalla(self, q, r):
        """Coordenadas axiales a píxeles"""
        s = RADIO_HEX * self.zoom
        x = self.offset_x + s * 1.5 * q
        y = self.offset_y + s * math.sqrt(3) * (r + q / 2.0)
        return int(x), int(y)

    # ── HUD ────────────────────────────────────────────────────────────────

    def _dibujar_hud(self):
        """Dibuja toda la interfaz"""
        nivel = self.gestor_niveles.obtener_nivel()
        
        # Panel superior izquierdo - Nivel
        pygame.draw.rect(self.pantalla, (0, 0, 0, 160), (10, 10, 300, 90))
        pygame.draw.rect(self.pantalla, (100, 100, 100), (10, 10, 300, 90), 2)
        
        texto_nivel = f"NIVEL {nivel['id']}: {nivel['nombre']}"
        sf_nivel = self.fuente_md.render(texto_nivel, True, (255, 255, 150))
        self.pantalla.blit(sf_nivel, (20, 15))
        
        texto_inicio = f"🚀 Inicio: {self.inicio}"
        sf_inicio = self.fuente_sm.render(texto_inicio, True, (150, 255, 150))
        self.pantalla.blit(sf_inicio, (20, 45))
        
        if self.emocion_seleccionada:
            planeta = PLANETAS[self.emocion_seleccionada]
            texto_meta = f"🎯 Destino: Planeta {planeta} {self.meta}"
        else:
            texto_meta = f"🎯 Destino: {self.meta}"
        sf_meta = self.fuente_sm.render(texto_meta, True, (255, 150, 150))
        self.pantalla.blit(sf_meta, (20, 65))
        
        # Batería
        self._dibujar_bateria()
        
        # Botón siguiente nivel (si completado)
        if self.estado == "COMPLETADO" and nivel['id'] < len(self.gestor_niveles.niveles) - 1:
            self.boton_siguiente_rect = pygame.Rect(ANCHO - 200, 20, 180, 40)
            pygame.draw.rect(self.pantalla, (0, 150, 0), self.boton_siguiente_rect)
            pygame.draw.rect(self.pantalla, (255, 255, 255), self.boton_siguiente_rect, 2)
            sf_sig = self.fuente_md.render("➡️ SIGUIENTE", True, (255, 255, 255))
            self.pantalla.blit(sf_sig, (ANCHO - 180, 30))

    def _dibujar_bateria(self):
        """Dibuja el indicador de batería"""
        x = ANCHO - 250
        y = 20
        ancho = 200
        alto = 30
        
        pygame.draw.rect(self.pantalla, (0, 0, 0, 160), (x-5, y-5, ancho+10, alto+10))
        pygame.draw.rect(self.pantalla, (100, 100, 100), (x, y, ancho, alto), 2)
        
        if self.bateria_infinita:
            texto = "🔋 BATERÍA: ∞ INFINITA"
            sf = self.fuente_md.render(texto, True, (0, 255, 255))
            self.pantalla.blit(sf, (x + 10, y + 5))
        else:
            porcentaje = self.energia_restante / self.energia_total
            ancho_lleno = int(ancho * porcentaje)
            
            if porcentaje > 0.6:
                color = (0, 255, 0)
            elif porcentaje > 0.3:
                color = (255, 255, 0)
            else:
                color = (255, 0, 0)
            
            pygame.draw.rect(self.pantalla, color, (x, y, ancho_lleno, alto))
            texto = f"🔋 {self.energia_restante}/{self.energia_total}"
            sf = self.fuente_md.render(texto, True, (255, 255, 255))
            self.pantalla.blit(sf, (x + ancho + 10, y + 5))

    def _dibujar_hud_inferior(self):
        """Opciones de búsqueda"""
        y_base = ALTO - 80
        x_centro = ANCHO // 2
        
        pygame.draw.rect(self.pantalla, (0, 0, 0, 180), (x_centro - 300, y_base, 600, 60))
        pygame.draw.rect(self.pantalla, (100, 100, 100), (x_centro - 300, y_base, 600, 60), 2)
        
        titulo = self.fuente_md.render("🚀 PRUEBA NAVES:", True, (255, 255, 255))
        self.pantalla.blit(titulo, (x_centro - titulo.get_width() // 2, y_base - 25))
        
        for i, (tecla, nombre, desc, color) in enumerate(self.opciones_busqueda):
            x = x_centro - 200 + i * 200
            pygame.draw.circle(self.pantalla, color, (x, y_base + 30), 15)
            pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y_base + 30), 15, 2)
            
            sf_tecla = self.fuente_md.render(f"[{tecla}]", True, (255, 255, 100))
            self.pantalla.blit(sf_tecla, (x + 25, y_base + 15))

    def _dibujar_boton_elegir(self):
        """Botón para elegir nave"""
        if not self.mostrar_boton_elegir or not self.estadisticas:
            return
        
        x_centro = ANCHO // 2
        y_base = ALTO - 150
        ancho = 400
        alto = 60
        
        rect = pygame.Rect(x_centro - ancho // 2, y_base, ancho, alto)
        self.boton_elegir_rect = rect
        
        pygame.draw.rect(self.pantalla, (0, 150, 0), rect)
        pygame.draw.rect(self.pantalla, (255, 255, 255), rect, 3)
        
        texto = f"✨ ¡ESCOJO ESTA NAVE! (Gasta {self.estadisticas['energia_gastada']}⚡) ✨"
        sf = self.fuente_md.render(texto, True, (255, 255, 255))
        self.pantalla.blit(sf, (x_centro - sf.get_width() // 2, y_base + 20))

    def _dibujar_estadisticas(self):
        """Estadísticas de la nave elegida"""
        if not self.estadisticas_elegidas:
            return
        
        x = ANCHO - 320
        y = 100
        ancho = 300
        alto = 130
        
        pygame.draw.rect(self.pantalla, (0, 40, 0, 200), (x, y, ancho, alto))
        pygame.draw.rect(self.pantalla, (0, 255, 0), (x, y, ancho, alto), 2)
        
        nombres = {'anchura': 'EXPLORADORA', 'profundidad': 'AVENTURERA', 'costouniforme': 'ESTRATEGA'}
        titulo = f"✨ NAVE {nombres[self.estadisticas_elegidas['tecnica']]} ✨"
        sf_titulo = self.fuente_sm.render(titulo, True, (255, 255, 100))
        self.pantalla.blit(sf_titulo, (x + 10, y + 5))
        
        lineas = [
            f"📊 Pasos: {self.estadisticas_elegidas['pasos_totales']}",
            f"🛤️  Camino: {self.estadisticas_elegidas['casillas_camino']} casillas",
            f"⚡ Gasto: {self.estadisticas_elegidas['energia_gastada']}",
            f"🔋 Restante: {self.energia_restante}"
        ]
        
        for i, linea in enumerate(lineas):
            sf = self.fuente_sm.render(linea, True, (255, 255, 255))
            self.pantalla.blit(sf, (x + 20, y + 35 + i * 20))

    def mostrar_mensaje(self, texto, color):
        """Muestra un mensaje temporal"""
        self.mensaje_estado = texto
        self.color_mensaje = color
        self.tiempo_mensaje = pygame.time.get_ticks()

    def _dibujar_mensaje(self):
        """Dibuja mensaje temporal"""
        if not self.mensaje_estado or pygame.time.get_ticks() - self.tiempo_mensaje > 3000:
            return
        
        x_centro = ANCHO // 2
        y_base = 200
        
        fondo = pygame.Surface((600, 50), pygame.SRCALPHA)
        fondo.fill((*self.color_mensaje[:3], 200))
        self.pantalla.blit(fondo, (x_centro - 300, y_base))
        pygame.draw.rect(self.pantalla, (255, 255, 255), (x_centro - 300, y_base, 600, 50), 2)
        
        sf = self.fuente_md.render(self.mensaje_estado, True, (255, 255, 255))
        self.pantalla.blit(sf, (x_centro - sf.get_width() // 2, y_base + 15))

    # ── Eventos ────────────────────────────────────────────────────────────

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
                elif k in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.zoom *= 1.2
                elif k == pygame.K_MINUS:
                    self.zoom = max(0.3, self.zoom / 1.2)
                elif k == pygame.K_SPACE:
                    self.busqueda_activa = not self.busqueda_activa
                elif k == pygame.K_r:
                    self.velocidad_busqueda = max(1, self.velocidad_busqueda - 2)
                elif k == pygame.K_f:
                    self.velocidad_busqueda = min(30, self.velocidad_busqueda + 2)
                elif k == pygame.K_v and self.estado == "SELECCION_EMOCION":
                    self.activar_voz()
                elif k == pygame.K_n:
                    if self.gestor_niveles.siguiente_nivel():
                        self.cargar_nivel(self.gestor_niveles.nivel_actual)
                
                # Teclas de búsqueda
                elif self.estado in ["BUSCANDO", "COMPLETADO"]:
                    if k == pygame.K_b:
                        self._iniciar_busqueda_paso_a_paso('anchura')
                    elif k == pygame.K_d:
                        self._iniciar_busqueda_paso_a_paso('profundidad')
                    elif k == pygame.K_u:
                        self._iniciar_busqueda_paso_a_paso('costouniforme')
                
                # Teclas numéricas para emociones
                elif self.estado == "SELECCION_EMOCION":
                    if k == pygame.K_1:
                        self.seleccionar_emocion("tristeza")
                    elif k == pygame.K_2:
                        self.seleccionar_emocion("miedo")
                    elif k == pygame.K_3:
                        self.seleccionar_emocion("enojo")
                    elif k == pygame.K_4:
                        self.seleccionar_emocion("alegria")
                    elif k == pygame.K_5:
                        self.seleccionar_emocion("ansiedad")

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                # Clic en menú de emociones
                if self.estado == "SELECCION_EMOCION" and self.botones_menu:
                    for boton in self.botones_menu:
                        if boton['rect'].collidepoint(evento.pos):
                            self.seleccionar_emocion(boton['emocion'])
                            break
                
                # Clic en botón elegir
                if self.mostrar_boton_elegir and self.boton_elegir_rect:
                    if self.boton_elegir_rect.collidepoint(evento.pos):
                        self.elegir_nave_actual()
                
                # Clic en botón siguiente nivel
                if hasattr(self, 'boton_siguiente_rect') and self.boton_siguiente_rect:
                    if self.boton_siguiente_rect.collidepoint(evento.pos):
                        if self.gestor_niveles.siguiente_nivel():
                            self.cargar_nivel(self.gestor_niveles.nivel_actual)

        return True

    # ── Voz ────────────────────────────────────────────────────────────────

    def activar_voz(self):
        """Reconocimiento de voz"""
        if self.estado != "SELECCION_EMOCION":
            return
        
        self.voz.hablar("¿Cómo te sientes hoy?")
        pygame.time.wait(2000)
        
        texto = self.voz.escuchar()
        if not texto:
            self.voz.hablar("No te escuché bien. Intenta de nuevo.")
            return
        
        if "triste" in texto:
            self.seleccionar_emocion("tristeza")
        elif "miedo" in texto:
            self.seleccionar_emocion("miedo")
        elif "enojado" in texto:
            self.seleccionar_emocion("enojo")
        elif "alegre" in texto:
            self.seleccionar_emocion("alegria")
        elif "ansioso" in texto:
            self.seleccionar_emocion("ansiedad")
        else:
            self.voz.hablar("No reconozco esa emoción. Intenta de nuevo.")

    # ── Bucle principal ────────────────────────────────────────────────────

    def ejecutar(self):
        ejecutando = True
        while ejecutando:
            tiempo_actual = pygame.time.get_ticks()
            
            if self.busqueda_activa and self.generador_busqueda:
                paso_ms = 1000 // self.velocidad_busqueda
                if tiempo_actual - self.ultimo_tiempo >= paso_ms:
                    self._avanzar_busqueda()
                    self.ultimo_tiempo = tiempo_actual
            
            ejecutando = self.manejar_eventos()
            
            # Dibujar
            self.pantalla.fill(COLOR_FONDO)
            self.dibujar_tablero()
            self._dibujar_camino_lineas()
            
            if self.estado == "SELECCION_EMOCION":
                self.dibujar_menu_emociones()
            
            if self.estado in ["BUSCANDO", "COMPLETADO"]:
                self._dibujar_hud_inferior()
            
            self._dibujar_boton_elegir()
            self._dibujar_estadisticas()
            self._dibujar_hud()
            self._dibujar_mensaje()
            
            pygame.display.flip()
            self.reloj.tick(60)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()