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
        
        # Pantalla completa con la resolución real del monitor
        self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Conexión Mental - Búsqueda No Informada")

        # Actualizar ANCHO y ALTO globales con el tamaño real de la pantalla
        import config as _cfg
        _cfg.ANCHO = self.pantalla.get_width()
        _cfg.ALTO  = self.pantalla.get_height()
        global ANCHO, ALTO
        ANCHO = _cfg.ANCHO
        ALTO  = _cfg.ALTO

        self.reloj = pygame.time.Clock()

        # Cámara - centrada (ajustada hacia arriba para dejar espacio al panel inferior)
        self.offset_x = ANCHO // 2
        self.offset_y = (ALTO // 2) - 50
        self.zoom     = 1.0

        # Fuentes (Intentar usar Segoe UI Emoji para soporte de emojis en Windows)
        try:
            self.fuente_sm = pygame.font.SysFont("segoeuiemoji", 20)
            self.fuente_md = pygame.font.SysFont("segoeuiemoji", 26)
            self.fuente_grande = pygame.font.SysFont("segoeuiemoji", 36)
        except:
             # Fallback
            self.fuente_sm = pygame.font.Font(None, 20)
            self.fuente_md = pygame.font.Font(None, 26)
            self.fuente_grande = pygame.font.Font(None, 36)

        # Fondo espacial (generado una sola vez)
        self._init_fondo_espacial()

        # Imágenes de planetas
        self._cargar_imagenes_planetas()

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
        """Dibuja el menú para seleccionar emoción estilo HOLOGRAMA"""
        x_centro = ANCHO // 2
        y_base = 150
        w_menu, h_menu = 600, 480
        
        # Fondo Panel Glass
        self._dibujar_panel_glass(x_centro - w_menu//2, y_base - 50, w_menu, h_menu, color_borde=(100, 100, 255))
        
        # Título con sombra
        titulo_txt = "¿CÓMO TE SIENTES HOY?"
        titulo = self.fuente_grande.render(titulo_txt, True, (255, 255, 100))
        titulo_sombra = self.fuente_grande.render(titulo_txt, True, (0, 0, 0))
        
        self.pantalla.blit(titulo_sombra, (x_centro - titulo.get_width() // 2 + 3, y_base - 17))
        self.pantalla.blit(titulo, (x_centro - titulo.get_width() // 2, y_base - 20))
        
        # Subtítulo
        sub = self.fuente_sm.render("(Selecciona una misión para tu astronauta)", True, (200, 240, 255))
        self.pantalla.blit(sub, (x_centro - sub.get_width() // 2, y_base + 30))
        
        # Botones de emociones
        self.botones_menu = []
        emociones = [
            ("tristeza", "Tristeza", (50, 50, 200), "💧"),   # Azul oscuro
            ("miedo", "Miedo", (100, 0, 150), "👻"),      # Morado
            ("enojo", "Enojo", (200, 50, 50), "🔥"),      # Rojo
            ("alegria", "Alegría", (220, 220, 0), "☀️"),    # Amarillo
            ("ansiedad", "Ansiedad", (0, 150, 100), "🌀")   # Verde azulado
        ]
        
        for i, (key, nombre, color_base, emoji) in enumerate(emociones):
            y_boton = y_base + 70 + i * 60 # Más espacio
            ancho_boton = 480
            rect = pygame.Rect(x_centro - ancho_boton // 2, y_boton, ancho_boton, 45)
            
            # Chequear hover
            mouse_pos = pygame.mouse.get_pos()
            hover = rect.collidepoint(mouse_pos)
            
            # Dibujar botón pro
            self._dibujar_boton_pro(rect, "", color_base, hover=hover)
            
            # --- SOLO EMOJIS Y TEXTO ---
            # Intentar renderizar emoji grande
            try:
                # Usar la fuente grande para el emoji si es posible, o la misma
                sf_emoji = self.fuente_grande.render(emoji, True, (255, 255, 255))
                self.pantalla.blit(sf_emoji, (rect.left + 20, rect.centery - sf_emoji.get_height()//2))
                offset_x = 20 + sf_emoji.get_width() + 10
            except:
                offset_x = 20
            
            # Nombre de la emoción
            sf_nombre = self.fuente_md.render(nombre, True, (255, 255, 255))
            self.pantalla.blit(sf_nombre, (rect.left + offset_x, rect.centery - sf_nombre.get_height()//2))
            
            # Texto Planeta destino
            nombre_planeta = PLANETAS[key]
            sf_dest = self.fuente_sm.render(f"→ Planeta {nombre_planeta}", True, (220, 220, 220))
            self.pantalla.blit(sf_dest, (rect.right - sf_dest.get_width() - 20, rect.centery - sf_dest.get_height()//2))

            self.botones_menu.append({'rect': rect, 'emocion': key})
        
        # Panel Voz inferior
        rect_voz = pygame.Rect(x_centro - 200, y_base + 380, 400, 40)
        pygame.draw.rect(self.pantalla, (0, 0, 0, 150), rect_voz, border_radius=20)
        pygame.draw.rect(self.pantalla, (0, 255, 0), rect_voz, 1, border_radius=20)
        
        voz_texto = "🎤 O presiona V para hablar"
        sf_voz = self.fuente_sm.render(voz_texto, True, (0, 255, 0))
        self.pantalla.blit(sf_voz, (rect_voz.centerx - sf_voz.get_width() // 2, rect_voz.centery - sf_voz.get_height() // 2))

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
                
                # Verificar si hay suficiente batería
                if not self.bateria_infinita and energia_gastada > self.energia_restante:
                    self.voz.hablar("No tenemos suficiente batería para esta ruta. Prueba otra nave.")
                    self.mostrar_boton_elegir = False
                    return
                
                self.estadisticas = {
                    'pasos_totales': pasos_totales,
                    'casillas_camino': casillas_camino,
                    'energia_gastada': energia_gastada,
                    'energia_restante': self.energia_restante - energia_gastada if not self.bateria_infinita else self.energia_restante,
                    'tecnica': self.resultado.get('tecnica', 'anchura') if self.resultado else 'anchura'
                }
                
                self.resultado = self.agente._preparar_resultado_parcial(camino_final)
                self.resultado['camino_set'] = set(camino_final)
                
                print(f"✅ Búsqueda completada! Energía a gastar: {energia_gastada}")
                
                # Mensaje de éxito con opción
                if energia_gastada <= self.energia_restante or self.bateria_infinita:
                    self.voz.hablar(f"¡Encontré un camino! Gasta {energia_gastada} de batería. ¿Te gusta esta nave?")
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
        
        if not self.bateria_infinita and energia_gastada > self.energia_restante:
            self.mostrar_mensaje("¡No tienes suficiente batería!", (255, 0, 0))
            self.voz.hablar("No tenemos batería suficiente. Prueba otra nave.")
            return
        
        # Guardar resultado
        self.resultado_elegido = self.resultado
        self.estadisticas_elegidas = self.estadisticas.copy()
        
        if not self.bateria_infinita:
            self.energia_restante -= energia_gastada
        
        self.mostrar_boton_elegir = False
        
        # Mensaje de éxito
        planeta = PLANETAS[self.emocion_seleccionada]
        if self.energia_restante >= 0:
            # Frase de éxito
            frases_exito = [
                f"¡Lo logramos pequeño astronauta! Llegamos al planeta {planeta}.",
                f"¡Misión cumplida! Conectamos con {planeta}. Nos quedan {self.energia_restante} de batería.",
                f"¡Bien hecho! Llegamos a {planeta}. Aún tenemos {self.energia_restante} de energía."
            ]
            self.voz.hablar(random.choice(frases_exito))
            
            nivel = self.gestor_niveles.obtener_nivel()
            if "victoria" in nivel["mensajes"]:
                self.mostrar_mensaje(nivel["mensajes"]["victoria"], (0, 255, 0))
            else:
                self.mostrar_mensaje("¡Llegamos al planeta!", (0, 255, 0))
            
            self.estado = "COMPLETADO"
            
            # Advertencia de batería baja
            if not self.bateria_infinita and self.energia_restante < 5:
                self.voz.hablar_frase("bateria_baja", energia=self.energia_restante)
        else:
            self.estado = "GAME_OVER"
            self.voz.hablar("¡Oh no! Nos quedamos sin batería. Intenta de nuevo.")

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
        """Dibuja el camino final con un efecto de rayo láser / neón"""
        resultado_actual = self.resultado_elegido if self.resultado_elegido else self.resultado
        
        if not resultado_actual or 'camino_lista' not in resultado_actual:
             return
             
        camino = resultado_actual['camino_lista']
        if not camino or len(camino) < 2:
            return
        
        # Convertir todo a pixeles
        puntos = [self.hex_a_pantalla(*p) for p in camino]
        
        # 1. Crear superficie para el resplandor (una vez por frame)
        surf_glow = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        color_glow = (255, 200, 0, 100) # Amarillo/Dorado semitransparente
        
        if len(puntos) > 1:
            pygame.draw.lines(surf_glow, color_glow, False, puntos, 12)
        
        self.pantalla.blit(surf_glow, (0,0))

        # 2. Línea central brillante
        if len(puntos) > 1:
            pygame.draw.lines(self.pantalla, (255, 255, 100), False, puntos, 4)
        
        # 3. Nodos conectores (puntos en cada hex del camino)
        for x, y in puntos:
            pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y), 3)
            pygame.draw.circle(self.pantalla, (255, 200, 0), (x, y), 6, 1)

    # ── Fondo espacial ───────────────────────────────────────────────────

    def _init_fondo_espacial(self):
        """Genera la superficie estática de fondo (nebulosas + estrellas) y los asteroides."""
        # ── Superficie estática ──────────────────────────────────────────────
        self._fondo_surf = pygame.Surface((ANCHO, ALTO))
        self._fondo_surf.fill((5, 5, 20))

        # Nebulosas: manchas suaves de color
        nebulosas = [
            (ANCHO * 0.12, ALTO * 0.22, (25,  0, 70),  380),
            (ANCHO * 0.78, ALTO * 0.14, ( 0, 30, 90),  300),
            (ANCHO * 0.88, ALTO * 0.72, (50,  0, 60),  340),
            (ANCHO * 0.28, ALTO * 0.82, ( 0, 25, 70),  270),
            (ANCHO * 0.52, ALTO * 0.48, (15,  0, 50),  430),
            (ANCHO * 0.60, ALTO * 0.30, ( 0, 40, 60),  200),
        ]
        for nx, ny, nc, nr in nebulosas:
            for r in range(nr, 0, -10):
                alpha = int(55 * (1 - r / nr))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*nc, alpha), (r, r), r)
                self._fondo_surf.blit(s, (int(nx) - r, int(ny) - r))

        # Capa de estrellas tenues (fondo)
        for _ in range(600):
            x = random.randint(0, ANCHO - 1)
            y = random.randint(0, ALTO - 1)
            b = random.randint(50, 120)
            pygame.draw.circle(self._fondo_surf, (b, b, b + 10), (x, y), 1)

        # Capa de estrellas medianas
        for _ in range(200):
            x = random.randint(0, ANCHO - 1)
            y = random.randint(0, ALTO - 1)
            b = random.randint(140, 210)
            pygame.draw.circle(self._fondo_surf, (b, b, min(255, b + 40)), (x, y), 1)

        # Estrellas brillantes con cruz (animadas por parpadeo)
        self._estrellas_brillantes = []
        for _ in range(50):
            x = random.randint(0, ANCHO - 1)
            y = random.randint(0, ALTO - 1)
            b = random.randint(200, 255)
            pygame.draw.circle(self._fondo_surf, (b, b, 255), (x, y), 2)
            self._estrellas_brillantes.append((x, y, b, random.uniform(0, math.pi * 2)))

        # ── Asteroides animados ──────────────────────────────────────────────
        self._asteroides = []
        for _ in range(25):
            n_pts = random.randint(6, 9)
            forma_base = []
            for i in range(n_pts):
                rb = random.randint(4, 14)
                ang = 2 * math.pi * i / n_pts
                forma_base.append((rb * math.cos(ang), rb * math.sin(ang)))
            gris = random.randint(90, 175)
            self._asteroides.append({
                'x':       random.uniform(0, ANCHO),
                'y':       random.uniform(0, ALTO),
                'vx':      random.uniform(-0.35, 0.35),
                'vy':      random.uniform(-0.25, 0.25),
                'rot':     random.uniform(0, math.pi * 2),
                'rot_vel': random.uniform(-0.006, 0.006),
                'forma':   forma_base,
                'color':   (gris, gris - 10, max(0, gris - 25)),
            })

        self._t_parpadeo = 0.0

    def _dibujar_fondo_espacial(self):
        """Dibuja nebulosa, estrellas (con parpadeo) y asteroides drifting."""
        # Fondo estático pre-renderizado
        self.pantalla.blit(self._fondo_surf, (0, 0))

        # Parpadeo de estrellas brillantes
        self._t_parpadeo += 0.025
        for (sx, sy, sb, fase) in self._estrellas_brillantes:
            factor = 0.55 + 0.45 * math.sin(self._t_parpadeo + fase)
            brillo = int(sb * factor)
            L = int(5 + 5 * factor)
            col = (brillo, brillo, min(255, brillo + 30))
            pygame.draw.line(self.pantalla, col, (sx - L, sy), (sx + L, sy), 1)
            pygame.draw.line(self.pantalla, col, (sx, sy - L), (sx, sy + L), 1)

        # Asteroides flotantes
        for ast in self._asteroides:
            ast['x'] = (ast['x'] + ast['vx']) % ANCHO
            ast['y'] = (ast['y'] + ast['vy']) % ALTO
            ast['rot'] += ast['rot_vel']
            ang = ast['rot']
            pts = []
            for (px, py) in ast['forma']:
                rx = px * math.cos(ang) - py * math.sin(ang)
                ry = px * math.sin(ang) + py * math.cos(ang)
                pts.append((int(ast['x'] + rx), int(ast['y'] + ry)))
            if len(pts) >= 3:
                pygame.draw.polygon(self.pantalla, ast['color'], pts)
                pygame.draw.polygon(self.pantalla, (210, 210, 210), pts, 1)

    def _hacer_circular(self, img_original, diametro):
        """Escala proporcionalmente (center crop) y recorta en círculo."""
        w, h = img_original.get_size()
        
        # 1. Calcular escala para cubrir todo el diámetro (Center Crop)
        scale = max(diametro / w, diametro / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 2. Escalar imagen manteniendo aspect ratio
        img_scaled = pygame.transform.smoothscale(img_original, (new_w, new_h)).convert_alpha()
        
        # 3. Crear superficie cuadrada final y centrar la imagen escalada
        dx = (new_w - diametro) // 2
        dy = (new_h - diametro) // 2
        superficie_final = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
        superficie_final.blit(img_scaled, (0, 0), (dx, dy, diametro, diametro))
        
        # 4. Máscara circular
        mascara = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
        pygame.draw.circle(mascara, (255, 255, 255, 255), (diametro // 2, diametro // 2), diametro // 2)
        superficie_final.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return superficie_final

    def _cargar_imagenes_planetas(self):
        """Carga las imágenes originales sin escalar. El escalado ocurre según el zoom."""
        import os
        base = os.path.join(os.path.dirname(__file__), 'images')
        archivos = {
            'tristeza': 'tierra_triste.png',
            'miedo':    'tierra_asustado.jpg',
            'enojo':    'tierra_enojado.jpg',
            'alegria':  'tierra_feliz.jpg',
            'ansiedad': 'tierra_ansiedad.jpg',
        }
        self._imgs_originales = {}
        for emocion, archivo in archivos.items():
            ruta = os.path.join(base, archivo)
            try:
                self._imgs_originales[emocion] = pygame.image.load(ruta).convert()
            except Exception as e:
                print(f'[WARN] No se pudo cargar {ruta}: {e}')
                self._imgs_originales[emocion] = None
        
        # Cargar astronauta
        try:
            ruta_astro = os.path.join(base, 'astronauta.png')
            self._img_astro_original = pygame.image.load(ruta_astro).convert_alpha()
        except Exception as e:
            print(f'[WARN] No se pudo cargar astronauta: {e}')
            self._img_astro_original = None

        # Cache: se regenera solo cuando cambia el zoom
        self._zoom_cache          = None
        self.imgs_planetas        = {}
        self.imgs_planetas_grande = {}
        self.img_astronauta       = None

    def _actualizar_cache_planetas(self):
        """Regenera las imágenes circulares solo si cambió el zoom."""
        if self._zoom_cache == self.zoom:
            return
        self._zoom_cache = self.zoom
        s = RADIO_HEX * self.zoom
        # Círculo inscrito del hex: diámetro = s*sqrt(3) ≈ s*1.732
        # Normal: llena exactamente el espacio interior del hexágono
        d_normal = max(10, int(s * 1.70))   # ~60px al zoom=1
        # Destino: igual pero con halo, la imagen no crece más
        d_grande = max(14, int(s * 1.73))   # ~61px al zoom=1
        
        for emocion, img in self._imgs_originales.items():
            if img:
                self.imgs_planetas[emocion]        = self._hacer_circular(img, d_normal)
                self.imgs_planetas_grande[emocion] = self._hacer_circular(img, d_grande)
            else:
                self.imgs_planetas[emocion]        = None
                self.imgs_planetas_grande[emocion] = None
        
        # Escalar astronauta (ligeramente más pequeño que el hexágono para que quepa bien)
        if self._img_astro_original:
            d_astro = int(s * 1.4)
            self.img_astronauta = pygame.transform.smoothscale(self._img_astro_original, (d_astro, d_astro))
        else:
            self.img_astronauta = None

    def dibujar_tablero(self):
        """Dibuja el tablero hexagonal con planetas y obstáculos"""
        self._actualizar_cache_planetas()  # reescala si cambió el zoom
        for (q, r), celda in self.tablero.celdas.items():
            x, y = self.hex_a_pantalla(q, r)
            
            # Obtener color base
            color_base = self._color_celda(q, r)
            
            # Si es un planeta y no es el destino, pintar de gris
            if celda.es_planeta and celda.planeta != self.emocion_seleccionada:
                color_base = (80, 80, 100)
            
            # Dibujar hexágono
            self._dibujar_hex(x, y, color_base)
            
            # Si es la posición actual del jugador (inicio o búsqueda en curso)
            # Prioridad: 
            # 1. Si hay búsqueda activa → mostrar en el paso actual
            # 2. Si no, mostrar en inicio
            
            # Aquí dibujamos el contenido estático de la celda (planeta/obs)
            # La parte dinámica (astronauta) la dibujamos DESPUÉS del bucle para que quede encima

            # Si es un planeta, dibujar imagen circular
            if celda.es_planeta:
                if celda.planeta == self.emocion_seleccionada:
                    # Planeta destino: imagen grande + halo de brillo
                    img = self.imgs_planetas_grande.get(celda.planeta)
                    r_img = (img.get_width() // 2) if img else int(RADIO_HEX * self.zoom * 1.05)
                    color_planeta = COLOR_EMOCIONES.get(celda.planeta, (255, 255, 255))
                    for i in range(4):
                        radio_brillo = r_img + 5 + i * 7
                        alpha = 90 - i * 20
                        brillo = pygame.Surface((radio_brillo*2, radio_brillo*2), pygame.SRCALPHA)
                        pygame.draw.circle(brillo, (*color_planeta, alpha), (radio_brillo, radio_brillo), radio_brillo)
                        self.pantalla.blit(brillo, (x - radio_brillo, y - radio_brillo))
                    if img:
                        self.pantalla.blit(img, (x - r_img, y - r_img))
                    else:
                        pygame.draw.circle(self.pantalla, color_planeta, (x, y), r_img)
                    # Borde eliminado (transparente)

                else:
                    # Planeta no seleccionado (grisáceo o tenue)
                    img = self.imgs_planetas.get(celda.planeta)
                    # r_img recalculado para no depender de variables del if anterior
                    r_img = (img.get_width() // 2) if img else int(RADIO_HEX * self.zoom * 0.77)

                    if img:
                        # Dibujar imagen con transparencia si no es el objetivo
                        img_alpha = img.copy()
                        img_alpha.set_alpha(150) # Semi-transparente
                        self.pantalla.blit(img_alpha, (x - r_img, y - r_img))
                    else:
                        color_planeta = COLOR_EMOCIONES.get(celda.planeta, (255, 255, 255))
                        pygame.draw.circle(self.pantalla, color_planeta, (x, y), r_img)
                    
                    # NO DIBUJAR NOMBRE para planetas no seleccionados

            
            # Si tiene obstáculo, dibujar símbolo pro
            elif celda.obstaculo:
                s = RADIO_HEX * self.zoom
                if celda.obstaculo == 'asteroide':
                    # Asteroide rocoso
                    pts = [
                        (x - s*0.5, y - s*0.3), (x - s*0.2, y - s*0.6),
                        (x + s*0.4, y - s*0.4), (x + s*0.6, y),
                        (x + s*0.3, y + s*0.5), (x - s*0.4, y + s*0.4)
                    ]
                    pygame.draw.polygon(self.pantalla, (120, 100, 100), pts)
                    pygame.draw.polygon(self.pantalla, (180, 160, 160), pts, 2)
                    # Crater
                    pygame.draw.circle(self.pantalla, (90, 70, 70), (x - s*0.1, y - s*0.1), s*0.15)
                    
                elif celda.obstaculo == 'tormenta':
                    # Nube eléctrica
                    color_nube = (100, 100, 120)
                    pygame.draw.circle(self.pantalla, color_nube, (x - 8, y), 10)
                    pygame.draw.circle(self.pantalla, color_nube, (x + 8, y), 10)
                    pygame.draw.circle(self.pantalla, color_nube, (x, y - 8), 12)
                    # Rayo
                    rayo = [(x-5, y+5), (x, y+15), (x-2, y+15), (x+5, y+25)]
                    pygame.draw.lines(self.pantalla, (255, 255, 0), False, rayo, 2)
                    
                elif celda.obstaculo == 'agujero_negro':
                    # Agujero negro con disco de acreción
                    # Disco
                    pygame.draw.circle(self.pantalla, (100, 0, 100), (x, y), s * 0.7)
                    pygame.draw.circle(self.pantalla, (50, 0, 50), (x, y), s * 0.5)
                    # Centro
                    pygame.draw.circle(self.pantalla, (0, 0, 0), (x, y), s * 0.3)
                    pygame.draw.circle(self.pantalla, (200, 200, 255), (x, y), s * 0.32, 1)

            # Marcador de INICIO (Base)
            if (q, r) == self.inicio:
                # Dibujar base espacial pequeña
                base_color = (0, 255, 255)
                # Plataforma
                pygame.draw.ellipse(self.pantalla, (50, 50, 50), (x - 20, y + 10, 40, 15))
                pygame.draw.ellipse(self.pantalla, base_color, (x - 20, y + 10, 40, 15), 2)
                # Texto "BASE" flotante
                sf_base = self.fuente_sm.render("BASE", True, (0, 255, 255))
                self.pantalla.blit(sf_base, (x - sf_base.get_width()//2, y + 25))

        # Dibujar Astronauta al final (para que siempre esté encima)
        pos_astronauta = self.inicio
        
        # Si ya se completó (nave elegida), ponerlo en la meta
        if self.estado == "COMPLETADO":
            pos_astronauta = self.meta
        
        # Si hay resultado de búsqueda (en progreso o terminada pero no elegida)
        elif self.resultado:
            # Si tenemos un camino (parcial o final), el astronauta está al final de ese camino
            if 'camino_lista' in self.resultado and self.resultado['camino_lista']:
                pos_astronauta = self.resultado['camino_lista'][-1]
            # Si no hay camino pero sí explorados, usar último explorado
            elif 'explorados' in self.resultado and self.resultado['explorados']:
                 pos_astronauta = self.resultado['explorados'][-1]

        xa, ya = self.hex_a_pantalla(*pos_astronauta)
        
        # Efecto de pulso / radar en el astronauta para indicar posición activa
        t_pulse = pygame.time.get_ticks()
        radius_pulse = 25 + 4 * math.sin(t_pulse * 0.008)
        surf_pulse = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(surf_pulse, (0, 255, 0, 80), (50, 50), int(radius_pulse), 4) # Verde radar
        pygame.draw.circle(surf_pulse, (255, 255, 255, 150), (50, 50), int(radius_pulse - 5), 1)
        self.pantalla.blit(surf_pulse, (xa - 50, ya - 50))

        if self.img_astronauta:
            wa, ha = self.img_astronauta.get_size()
            # Pequeña oscilación vertical flotando
            float_y = 3 * math.sin(t_pulse * 0.003)
            self.pantalla.blit(self.img_astronauta, (xa - wa//2, ya - ha//2 + float_y))
        else:
            # Fallback si no hay imagen
            pygame.draw.circle(self.pantalla, (255, 255, 255), (xa, ya), 10)
            pygame.draw.circle(self.pantalla, (0, 0, 0), (xa, ya), 10, 2)

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

    # ── Utilidades UI ──────────────────────────────────────────────────────

    def _dibujar_panel_glass(self, x, y, w, h, color_borde=(100, 200, 255), alpha=180, grosor_borde=2):
        """Dibuja un panel con efecto de cristal (semi-transparente y bordes redondeados)"""
        # Sombra
        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 100), (5, 5, w, h), border_radius=15)
        self.pantalla.blit(sombra, (x, y))

        # Fondo semi-transparente
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(sup, (20, 30, 50, alpha), (0, 0, w, h), border_radius=15)
        self.pantalla.blit(sup, (x, y))

        # Borde brillante
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.pantalla, color_borde, rect, grosor_borde, border_radius=15)
        
        # Brillo superior (efecto cristal)
        pygame.draw.line(self.pantalla, (255, 255, 255, 100), (x + 15, y + 2), (x + w - 15, y + 2), 2)

    def _dibujar_boton_pro(self, rect, texto, color_base, activo=False, hover=False):
        """Dibuja un botón con estilo 'candy' o 'glossy'"""
        color = color_base
        if hover:
            color = (min(255, color_base[0] + 30), min(255, color_base[1] + 30), min(255, color_base[2] + 30))
        if activo:
             color = (255, 255, 255) # Invertido si activo

        # Sombra botón
        pygame.draw.rect(self.pantalla, (0, 0, 0, 100), (rect.x + 4, rect.y + 4, rect.w, rect.h), border_radius=10)

        # Cuerpo botón
        pygame.draw.rect(self.pantalla, color, rect, border_radius=10)
        
        # Borde
        pygame.draw.rect(self.pantalla, (255, 255, 255), rect, 2, border_radius=10)

        # Texto
        color_texto = (255, 255, 255)
        if activo: color_texto = color_base
        
        sf = self.fuente_md.render(texto, True, color_texto)
        self.pantalla.blit(sf, (rect.centerx - sf.get_width() // 2, rect.centery - sf.get_height() // 2))

        # Brillo
        pygame.draw.line(self.pantalla, (255, 255, 255, 150), (rect.x + 10, rect.y + 5), (rect.right - 10, rect.y + 5), 2)

    # ── HUD ────────────────────────────────────────────────────────────────

    def _dibujar_hud(self):
        """Dibuja toda la interfaz con estilo PRO bonito"""
        nivel = self.gestor_niveles.obtener_nivel()
        
        # --- Panel Superior Izquierdo: Misión y Estado ---
        w_panel, h_panel = 360, 110 
        x_panel, y_panel = 20, 20
        self._dibujar_panel_glass(x_panel, y_panel, w_panel, h_panel, color_borde=(0, 255, 255))
        
        # Nivel Título
        texto_nivel = f"🌟 NIVEL {nivel['id'] + 1}: {nivel['nombre'].upper()}"
        
        # Usar fuente escalada si el texto es muy largo
        fuente_usar = self.fuente_md
        if len(texto_nivel) > 23: 
             fuente_usar = self.fuente_sm # Usar fuente pequeña si es muy largo

        sf_nivel = fuente_usar.render(texto_nivel, True, (0, 255, 255)) # Cyan neon
        # Sombra texto
        sf_sombra = fuente_usar.render(texto_nivel, True, (0, 0, 0))
        
        self.pantalla.blit(sf_sombra, (x_panel + 17, y_panel + 17))
        self.pantalla.blit(sf_nivel, (x_panel + 15, y_panel + 15))

        # Info Inicio
        texto_inicio = f"🚀 BASE: {self.inicio}"
        sf_inicio = self.fuente_sm.render(texto_inicio, True, (200, 200, 200))
        self.pantalla.blit(sf_inicio, (x_panel + 15, y_panel + 50))
        
        # Info Meta
        if self.emocion_seleccionada:
            planeta = PLANETAS[self.emocion_seleccionada]
            texto_meta = f"🎯 MISIÓN: Ir a {planeta} {self.meta}"
            color_meta = (255, 100, 255) # Pink neon
        else:
            texto_meta = "🎯 MISIÓN: Selecciona una emoción..."
            color_meta = (150, 150, 150)
            
        sf_meta = self.fuente_sm.render(texto_meta, True, color_meta)
        self.pantalla.blit(sf_meta, (x_panel + 15, y_panel + 75))
        
        # --- Batería ---
        self._dibujar_bateria()
        
        # --- Botón Siguiente Nivel ---
        if self.estado == "COMPLETADO" and nivel['id'] < len(self.gestor_niveles.niveles) - 1:
            # MOVIDO: A la derecha, debajo del panel de estadísticas
            # Aumentado el ancho a 320 para encajar con el resto
            # x = ANCHO - 320 - 20 = ANCHO - 340
            rect_sig = pygame.Rect(ANCHO - 340, 270, 320, 50)
            self.boton_siguiente_rect = rect_sig
            
            self._dibujar_boton_pro(rect_sig, "➡️ SIGUIENTE GALAXIA", (0, 180, 0), hover=True)

    def _dibujar_bateria(self):
        """Dibuja el indicador de batería estilo barra de energía"""
        # AUMENTADO: Ancho a 320 para mayor holgura
        w, h = 320, 50
        x, y = ANCHO - w - 20, 20
        
        self._dibujar_panel_glass(x, y, w, h, color_borde=(255, 255, 0))
        
        # Icono batería (texto simple simulado)
        sf_icono = self.fuente_grande.render("⚡", True, (255, 255, 0))
        self.pantalla.blit(sf_icono, (x + 10, y + 5))
        
        # Barra fondo
        bar_x, bar_y = x + 40, y + 15
        bar_w, bar_h = 160, 20
        pygame.draw.rect(self.pantalla, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        
        if self.bateria_infinita:
            # Barra infinita arcoiris o azul
            pygame.draw.rect(self.pantalla, (0, 255, 255), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            sf_texto = self.fuente_sm.render("∞ INFINITA", True, (0, 0, 0))
            self.pantalla.blit(sf_texto, (bar_x + 35, bar_y + 2))
        else:
            pct = self.energia_restante / self.energia_total
            fill_w = int(bar_w * pct)
            
            # Color dinámico
            if pct > 0.6: color = (57, 255, 20) # Neon Green
            elif pct > 0.3: color = (255, 255, 0) # Yellow
            else: color = (255, 0, 0) # Red
            
            if fill_w > 0:
                pygame.draw.rect(self.pantalla, color, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
            
            # Texto
            sf_val = self.fuente_sm.render(f"{self.energia_restante} / {self.energia_total}", True, (255, 255, 255))
            self.pantalla.blit(sf_val, (bar_x + bar_w + 10, bar_y + 2))

    def _dibujar_hud_inferior(self):
        """Panel inferior de control de naves"""
        h_panel = 110
        y_base = ALTO - h_panel
        
        # Dibujar fondo panel completo en la parte inferior
        sup = pygame.Surface((ANCHO, h_panel), pygame.SRCALPHA)
        sup.fill((10, 15, 30, 240)) # Azul muy oscuro casi opaco
        self.pantalla.blit(sup, (0, y_base))
        
        # Líneas decorativas neón
        pygame.draw.line(self.pantalla, (0, 255, 255), (0, y_base), (ANCHO, y_base), 2) # Superior
        pygame.draw.line(self.pantalla, (0, 100, 180), (0, ALTO-2), (ANCHO, ALTO-2), 1) # Inferior
        
        x_centro = ANCHO // 2
        
        # Título centrado
        titulo = self.fuente_md.render("🎮  CENTRO DE MANDO: SELECCIONA TU NAVE  🎮", True, (150, 230, 255))
        self.pantalla.blit(titulo, (x_centro - titulo.get_width() // 2, y_base + 12))
        
        # Distribución amplia usando PROPORCIONES de pantalla (20%, 50%, 80%)
        # Esto separa las opciones y aprovecha el ancho completo
        centros_x = [int(ANCHO * 0.20), int(ANCHO * 0.50), int(ANCHO * 0.80)]
        
        for i, (tecla, sigla, nombre, color) in enumerate(self.opciones_busqueda):
            # Posición base de cada grupo
            cx = centros_x[i]
            cy = y_base + 65
            
            # --- 1. Icono Circular con Tecla ---
            radio = 24
            # Círculo relleno color nave
            pygame.draw.circle(self.pantalla, color, (cx - 70, cy), radio)
            # Anillo blanco
            pygame.draw.circle(self.pantalla, (255, 255, 255), (cx - 70, cy), radio + 2, 2)
            
            # Tecla (Negra para contraste)
            sf_k = self.fuente_md.render(tecla, True, (0, 0, 0))
            self.pantalla.blit(sf_k, (cx - 70 - sf_k.get_width()//2, cy - sf_k.get_height()//2))
            
            # --- 2. Información Texto (A la derecha del icono) ---
            # Nombre Nave
            sf_nom = self.fuente_md.render(nombre, True, color)
            self.pantalla.blit(sf_nom, (cx - 35, cy - 20))
            
            # Nombre Algoritmo (gris claro)
            sf_algo = self.fuente_sm.render(f"Motor: {sigla}", True, (200, 200, 200))
            self.pantalla.blit(sf_algo, (cx - 35, cy + 5))

    def _dibujar_boton_elegir(self):
        """Botón gigante y brillante para confirmar"""
        if not self.mostrar_boton_elegir or not self.estadisticas:
            return
        
        x_centro = ANCHO // 2
        y_base = ALTO - 160
        w, h = 500, 50
        
        rect = pygame.Rect(x_centro - w // 2, y_base, w, h)
        self.boton_elegir_rect = rect
        
        # Efecto de pulso en el botón
        t = pygame.time.get_ticks()
        offset = int(3 * math.sin(t * 0.01))
        rect_animado = rect.inflate(offset, offset)
        
        self._dibujar_boton_pro(rect_animado, 
                               f"✅ ¡CONFIRMAR RUTA! (Costo: {self.estadisticas['energia_gastada']} Batería)", 
                               (0, 200, 50), 
                               hover=True)

    def _dibujar_estadisticas(self):
        """Panel flotante de stats"""
        if not self.estadisticas_elegidas:
            return
        
        # AUMENTADO: Ancho a 320 para que quepa todo el texto bien
        w, h = 320, 160
        x, y = ANCHO - w - 20, 90
        
        self._dibujar_panel_glass(x, y, w, h, color_borde=(0, 255, 100))
        
        nombres = {'anchura': 'EXPLORADORA', 'profundidad': 'AVENTURERA', 'costouniforme': 'ESTRATEGA'}
        tecnica = self.estadisticas_elegidas.get('tecnica', 'anchura')
        nombre_nave = nombres.get(tecnica, 'DESCONOCIDA')

        # Título panel
        sf_tit = self.fuente_md.render(f"📊 REPORTE DE VUELO", True, (0, 255, 100))
        self.pantalla.blit(sf_tit, (x + 20, y + 15))
        
        # Datos
        datos = [
            (f"Nave:", nombre_nave, (255, 255, 0)),
            (f"Pasos calc:", f"{self.estadisticas_elegidas['pasos_totales']}", (200, 200, 200)),
            (f"Largo camino:", f"{self.estadisticas_elegidas['casillas_camino']} hex", (200, 200, 200)),
            (f"Energía usada:", f"-{self.estadisticas_elegidas['energia_gastada']} ⚡", (255, 100, 100)),
        ]
        
        dy = 45
        for label, val, col in datos:
            sf_l = self.fuente_sm.render(label, True, (150, 150, 150))
            sf_v = self.fuente_sm.render(val, True, col)
            self.pantalla.blit(sf_l, (x + 20, y + dy))
            # Ajustado un poco más a la derecha para dar aire al label
            self.pantalla.blit(sf_v, (x + 140, y + dy))
            dy += 22

    def mostrar_mensaje(self, texto, color):
        """Muestra un mensaje temporal"""
        self.mensaje_estado = texto
        self.color_mensaje = color
        self.tiempo_mensaje = pygame.time.get_ticks()

    def _dibujar_mensaje(self):
        """Dibuja mensaje temporal"""
        # Duración reducida de 3000ms a 2000ms
        if not self.mensaje_estado or pygame.time.get_ticks() - self.tiempo_mensaje > 2000:
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
        """Activa reconocimiento de voz con tecla V"""
        if self.estado != "SELECCION_EMOCION":
            return
        
        self.voz.hablar_frase("pregunta_emocion")
        pygame.time.wait(2000)
        
        texto = self.voz.escuchar()
        
        if not texto:
            self.voz.hablar("No te escuché bien. ¿Puedes repetir? Presiona V otra vez.")
            return
        
        emocion = self.voz.detectar_emocion(texto)
        
        if emocion:
            # Mensaje personalizado según emoción
            mensajes_emocion = {
                "tristeza": "Entiendo, te sientes triste. Vamos al planeta Juego a alegrarnos.",
                "miedo": "Tranquilo, el miedo se pasa. Busquemos el planeta Calma.",
                "enojo": "Respira hondo. El planeta Abrazo nos espera.",
                "alegria": "¡Qué bien! Compartamos esa alegría en el planeta Amigos.",
                "ansiedad": "Vamos al planeta Respiración a calmarnos."
            }
            self.voz.hablar(mensajes_emocion[emocion])
            pygame.time.wait(2000)
            self.seleccionar_emocion(emocion)
        else:
            self.voz.hablar("No reconocí esa emoción. Intenta con: triste, miedo, enojado, alegre o ansioso.")

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
            self._dibujar_fondo_espacial()
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