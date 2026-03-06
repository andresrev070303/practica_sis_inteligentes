# ui_renderer.py
# ─────────────────────────────────────────────────────────────────────────────
# Toda la lógica visual / de dibujado del juego.
# La clase UIRenderer recibe la instancia de Juego y dibuja sobre su pantalla.
# ─────────────────────────────────────────────────────────────────────────────
import pygame
import math
import random
import config

# ─────────────────────────────────────────────────────────────────────────────
# Constantes de color y datos de planetas (centralizadas aquí)
# ─────────────────────────────────────────────────────────────────────────────
COLOR_NORMAL    = (30,  30,  60)
COLOR_INICIO    = (0,  220,  80)
COLOR_META      = (220,  50,  50)
COLOR_CAMINO    = (255, 215,   0)
COLOR_BFS_LO    = (10,  60,  100)
COLOR_BFS_HI    = (0,  220,  255)
COLOR_DFS_LO    = (50,   0,   80)
COLOR_DFS_HI    = (200,  0,  255)
COLOR_UCS_LO    = (80,  40,    0)
COLOR_UCS_HI    = (255, 160,   0)
COLOR_GAME_OVER = (255,   0,   0, 200)
COLOR_VICTORIA  = (0,   255,   0, 200)
COLOR_ASTAR_LO = (0, 100, 100)    # Verde azulado oscuro
COLOR_ASTAR_HI = (0, 255, 255)    # Cian brillante

COLOR_EMOCIONES = {
    "tristeza": (0,   0, 255),
    "miedo":    (128, 0, 128),
    "enojo":    (255, 0,   0),
    "alegria":  (255, 255, 0),
    "ansiedad": (0,  255,  0),
}

PLANETAS = {
    "tristeza": "Juego",
    "miedo":    "Calma",
    "enojo":    "Abrazo",
    "alegria":  "Amigos",
    "ansiedad": "Respiración",
}

POSICIONES_PLANETAS = {
    "tristeza": ( 3, -3),
    "miedo":    (-2,  2),
    "enojo":    ( 0,  4),
    "alegria":  (-3,  0),
    "ansiedad": ( 2,  2),
}

# ─────────────────────────────────────────────────────────────────────────────
# Utilidad
# ─────────────────────────────────────────────────────────────────────────────
def _lerp_color(c1, c2, t: float):
    """Interpolación lineal entre dos colores RGB, t ∈ [0, 1]."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Renderer principal
# ─────────────────────────────────────────────────────────────────────────────
class UIRenderer:
    """
    Gestiona todo el dibujado del juego.
    Recibe la instancia `juego` y lee/escribe su estado donde sea necesario
    (por ejemplo, los rectángulos de botones que el manejador de eventos usa).
    """

    def __init__(self, juego):
        self.juego = juego
        self.pantalla = juego.pantalla
        self._init_fondo_espacial()

    # ── Accesos rápidos a las fuentes del juego ───────────────────────────
    @property
    def _fuente_sm(self):
        return self.juego.fuente_sm

    @property
    def _fuente_md(self):
        return self.juego.fuente_md

    @property
    def _fuente_grande(self):
        return self.juego.fuente_grande

    # ── Fondo espacial ────────────────────────────────────────────────────

    def _init_fondo_espacial(self):
        """Genera la superficie estática de fondo (nebulosas + estrellas) y los asteroides."""
        ANCHO = config.ANCHO
        ALTO  = config.ALTO

        # Superficie estática pre-renderizada
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

        # Capa de estrellas tenues
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

        # Estrellas brillantes con cruz (parpadean en runtime)
        self._estrellas_brillantes = []
        for _ in range(50):
            x = random.randint(0, ANCHO - 1)
            y = random.randint(0, ALTO - 1)
            b = random.randint(200, 255)
            pygame.draw.circle(self._fondo_surf, (b, b, 255), (x, y), 2)
            self._estrellas_brillantes.append((x, y, b, random.uniform(0, math.pi * 2)))

        # Asteroides animados
        self._asteroides = []
        for _ in range(25):
            n_pts = random.randint(6, 9)
            forma_base = []
            for i in range(n_pts):
                rb  = random.randint(4, 14)
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

    def dibujar_fondo_espacial(self):
        """Dibuja nebulosa, estrellas con parpadeo y asteroides flotantes."""
        ANCHO = config.ANCHO
        ALTO  = config.ALTO

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

    # ── Tablero hexagonal ─────────────────────────────────────────────────

    def hex_a_pantalla(self, q, r):
        """Convierte coordenadas axiales a píxeles en pantalla."""
        j = self.juego
        s = config.RADIO_HEX * j.zoom
        x = j.offset_x + s * 1.5 * q
        y = j.offset_y + s * math.sqrt(3) * (r + q / 2.0)
        return int(x), int(y)

    def _dibujar_hex(self, x, y, relleno, borde=(200, 200, 200), grosor=1):
        pts = []
        s = config.RADIO_HEX * self.juego.zoom
        for i in range(6):
            angulo = math.radians(60 * i)
            pts.append((x + s * math.cos(angulo), y + s * math.sin(angulo)))
        pygame.draw.polygon(self.pantalla, relleno, pts)
        pygame.draw.polygon(self.pantalla, borde, pts, grosor)

    def _color_celda(self, q, r):
        j   = self.juego
        pos = (q, r)

        if pos == j.inicio:
            return COLOR_INICIO
        if pos == j.meta:
            return COLOR_META

        if j.resultado is None and j.resultado_elegido is None:
            celda = j.tablero.obtener_celda(q, r)
            if celda and celda.obstaculo:
                color_obs = j.tablero.obtener_color_obstaculo(q, r)
                if color_obs:
                    return color_obs
            return COLOR_NORMAL

        resultado_actual = j.resultado_elegido if j.resultado_elegido else j.resultado
        if not resultado_actual:
            return COLOR_NORMAL

        if 'camino_set' in resultado_actual and pos in resultado_actual['camino_set']:
            return COLOR_CAMINO

        explorados = resultado_actual.get('explorados', [])
        if pos not in explorados:
            celda = j.tablero.obtener_celda(q, r)
            if celda and celda.obstaculo:
                color_obs = j.tablero.obtener_color_obstaculo(q, r)
                if color_obs:
                    return color_obs
            return COLOR_NORMAL

        idx = explorados.index(pos)
        t   = idx / max(len(explorados) - 1, 1)
        tecnica = resultado_actual.get('tecnica', 'anchura')

        if tecnica == 'anchura':
            nivel_max = max(resultado_actual.get('nivel_bfs', {0: 1}).values(), default=1)
            nivel = resultado_actual.get('nivel_bfs', {}).get(pos, 0)
            return _lerp_color(COLOR_BFS_LO, COLOR_BFS_HI, nivel / max(nivel_max, 1))
        elif tecnica == 'profundidad':
            return _lerp_color(COLOR_DFS_LO, COLOR_DFS_HI, t)
        elif tecnica == 'costouniforme':
            costos   = resultado_actual.get('costo_acumulado', {})
            costo_mx = max(costos.values(), default=1)
            return _lerp_color(COLOR_UCS_LO, COLOR_UCS_HI, costos.get(pos, 0) / max(costo_mx, 1))
        elif tecnica == 'a_star':  # NUEVO
            # Para A* usamos el costo acumulado + factor de heurística
            costos = resultado_actual.get('costo_acumulado', {})
            costo_mx = max(costos.values(), default=1)
            return _lerp_color(COLOR_ASTAR_LO, COLOR_ASTAR_HI, costos.get(pos, 0) / max(costo_mx, 1))

        return COLOR_NORMAL

    def dibujar_tablero(self):
        """Dibuja el tablero hexagonal con planetas y obstáculos."""
        j = self.juego
        for (q, r), celda in j.tablero.celdas.items():
            x, y = self.hex_a_pantalla(q, r)
            color_base = self._color_celda(q, r)

            if celda.es_planeta and celda.planeta != j.emocion_seleccionada:
                color_base = (80, 80, 100)

            self._dibujar_hex(x, y, color_base)

            if celda.es_planeta:
                if celda.planeta == j.emocion_seleccionada:
                    color_planeta = COLOR_EMOCIONES.get(celda.planeta, (255, 255, 255))
                    pygame.draw.circle(self.pantalla, color_planeta, (x, y), 15)
                    pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y), 15, 3)
                    for i in range(3):
                        radio_brillo = 20 + i * 3
                        alpha        = 100 - i * 30
                        brillo = pygame.Surface((radio_brillo * 2, radio_brillo * 2), pygame.SRCALPHA)
                        pygame.draw.circle(brillo, (*color_planeta, alpha),
                                           (radio_brillo, radio_brillo), radio_brillo)
                        self.pantalla.blit(brillo, (x - radio_brillo, y - radio_brillo))
                else:
                    color_planeta = COLOR_EMOCIONES.get(celda.planeta, (255, 255, 255))
                    pygame.draw.circle(self.pantalla, color_planeta, (x, y), 12)
                    pygame.draw.circle(self.pantalla, (200, 200, 200), (x, y), 12, 2)

                letra = PLANETAS[celda.planeta][0]
                sf = self._fuente_sm.render(letra, True, (255, 255, 255))
                self.pantalla.blit(sf, (x - 5, y - 8))

            elif celda.obstaculo:
                if celda.obstaculo == 'asteroide':
                    pygame.draw.circle(self.pantalla, (200, 200, 200), (x, y), 5)
                    pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y), 5, 1)
                elif celda.obstaculo == 'tormenta':
                    for i in range(3):
                        pygame.draw.circle(self.pantalla, (200, 200, 200), (x + i * 3, y - i * 2), 2)
                elif celda.obstaculo == 'agujero_negro':
                    pygame.draw.circle(self.pantalla, (0, 0, 0), (x, y), 8)
                    pygame.draw.circle(self.pantalla, (255, 0, 255), (x, y), 8, 1)

    def dibujar_camino_lineas(self):
        """Dibuja las líneas del camino encontrado."""
        j = self.juego
        resultado_actual = j.resultado_elegido if j.resultado_elegido else j.resultado
        if not resultado_actual or len(resultado_actual.get('camino_lista', [])) < 2:
            return
        puntos = [self.hex_a_pantalla(*p) for p in resultado_actual['camino_lista']]
        for i in range(len(puntos) - 1):
            pygame.draw.line(self.pantalla, (255, 255, 60), puntos[i], puntos[i + 1], 3)

    # ── Menú de emociones ────────────────────────────────────────────────

    def dibujar_menu_emociones(self):
        """Dibuja el menú para seleccionar emoción."""
        j        = self.juego
        ANCHO    = config.ANCHO
        x_centro = ANCHO // 2
        y_base   = 150

        fondo = pygame.Surface((500, 350), pygame.SRCALPHA)
        fondo.fill((0, 0, 0, 220))
        self.pantalla.blit(fondo, (x_centro - 250, y_base - 30))

        titulo = self._fuente_grande.render("¿CÓMO TE SIENTES HOY?", True, (255, 255, 100))
        self.pantalla.blit(titulo, (x_centro - titulo.get_width() // 2, y_base - 20))

        sub = self._fuente_sm.render("(Presiona V para hablar o haz clic en una emoción)",
                                     True, (200, 200, 200))
        self.pantalla.blit(sub, (x_centro - sub.get_width() // 2, y_base + 10))

        # Botones — se escriben en juego.botones_menu para que el evento los lea
        j.botones_menu = []
        emociones = [
            ("tristeza", "Tristeza", (0,   0, 255)),
            ("miedo",    "Miedo",    (128, 0, 128)),
            ("enojo",    "Enojo",    (255, 0,   0)),
            ("alegria",  "Alegría",  (255, 255, 0)),
            ("ansiedad", "Ansiedad", (0,  255,  0)),
        ]
        for i, (key, nombre, color) in enumerate(emociones):
            y_boton = y_base + 70 + i * 45
            rect = pygame.Rect(x_centro - 150, y_boton, 300, 35)
            pygame.draw.rect(self.pantalla, color, rect)
            pygame.draw.rect(self.pantalla, (255, 255, 255), rect, 2)
            texto = f"{i + 1}. {nombre} → Planeta {PLANETAS[key]}"
            sf = self._fuente_md.render(texto, True, (255, 255, 255))
            self.pantalla.blit(sf, (x_centro - 140, y_boton + 5))
            j.botones_menu.append({'rect': rect, 'emocion': key})

        voz_texto = "🎤 O presiona V y di: 'Estoy triste', 'Tengo miedo', etc."
        sf_voz = self._fuente_sm.render(voz_texto, True, (150, 255, 150))
        self.pantalla.blit(sf_voz, (x_centro - sf_voz.get_width() // 2, y_base + 320))

    # ── HUD ───────────────────────────────────────────────────────────────

    def dibujar_hud(self):
        """Panel de información superior."""
        j     = self.juego
        ANCHO = config.ANCHO
        nivel = j.gestor_niveles.obtener_nivel()

        pygame.draw.rect(self.pantalla, (0, 0, 0, 160), (10, 10, 300, 90))
        pygame.draw.rect(self.pantalla, (100, 100, 100), (10, 10, 300, 90), 2)

        sf_nivel = self._fuente_md.render(f"NIVEL {nivel['id']}: {nivel['nombre']}",
                                          True, (255, 255, 150))
        self.pantalla.blit(sf_nivel, (20, 15))

        sf_inicio = self._fuente_sm.render(f"🚀 Inicio: {j.inicio}", True, (150, 255, 150))
        self.pantalla.blit(sf_inicio, (20, 45))

        if j.emocion_seleccionada:
            planeta   = PLANETAS[j.emocion_seleccionada]
            texto_meta = f"🎯 Destino: Planeta {planeta} {j.meta}"
        else:
            texto_meta = f"🎯 Destino: {j.meta}"
        sf_meta = self._fuente_sm.render(texto_meta, True, (255, 150, 150))
        self.pantalla.blit(sf_meta, (20, 65))

        self._dibujar_bateria()

        # Botón siguiente nivel
        if j.estado == "COMPLETADO" and nivel['id'] < len(j.gestor_niveles.niveles) - 1:
            j.boton_siguiente_rect = pygame.Rect(ANCHO - 200, 20, 180, 40)
            pygame.draw.rect(self.pantalla, (0, 150, 0), j.boton_siguiente_rect)
            pygame.draw.rect(self.pantalla, (255, 255, 255), j.boton_siguiente_rect, 2)
            sf_sig = self._fuente_md.render("➡️ SIGUIENTE", True, (255, 255, 255))
            self.pantalla.blit(sf_sig, (ANCHO - 180, 30))

    def _dibujar_bateria(self):
        """Indicador de batería/energía."""
        j     = self.juego
        ANCHO = config.ANCHO
        x     = ANCHO - 250
        y     = 20
        ancho = 200
        alto  = 30

        pygame.draw.rect(self.pantalla, (0, 0, 0, 160), (x - 5, y - 5, ancho + 10, alto + 10))
        pygame.draw.rect(self.pantalla, (100, 100, 100), (x, y, ancho, alto), 2)

        if j.bateria_infinita:
            sf = self._fuente_md.render("🔋 BATERÍA: ∞ INFINITA", True, (0, 255, 255))
            self.pantalla.blit(sf, (x + 10, y + 5))
        else:
            porcentaje   = j.energia_restante / j.energia_total
            ancho_lleno  = int(ancho * porcentaje)
            color = (0, 255, 0) if porcentaje > 0.6 else ((255, 255, 0) if porcentaje > 0.3 else (255, 0, 0))
            pygame.draw.rect(self.pantalla, color, (x, y, ancho_lleno, alto))
            sf = self._fuente_md.render(f"🔋 {j.energia_restante}/{j.energia_total}", True, (255, 255, 255))
            self.pantalla.blit(sf, (x + ancho + 10, y + 5))

    def dibujar_hud_inferior(self):
        """Opciones de búsqueda en la parte inferior."""
        j     = self.juego
        ANCHO = config.ANCHO
        ALTO  = config.ALTO
        y_base   = ALTO - 80
        x_centro = ANCHO // 2

        pygame.draw.rect(self.pantalla, (0, 0, 0, 180), (x_centro - 350, y_base, 700, 60))
        pygame.draw.rect(self.pantalla, (100, 100, 100), (x_centro - 350, y_base, 700, 60), 2)

        titulo = self._fuente_md.render("🚀 PRUEBA NAVES:", True, (255, 255, 255))
        self.pantalla.blit(titulo, (x_centro - titulo.get_width() // 2, y_base - 25))

        # Distribuir 4 opciones equitativamente
        for i, (tecla, sigla, nombre, color) in enumerate(j.opciones_busqueda):
            x = x_centro - 300 + i * 150  # 150 píxeles entre cada una
            pygame.draw.circle(self.pantalla, color, (x, y_base + 30), 15)
            pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y_base + 30), 15, 2)
            sf_tecla = self._fuente_md.render(f"[{tecla}]", True, (255, 255, 100))
            self.pantalla.blit(sf_tecla, (x + 25, y_base + 15))

    def dibujar_boton_elegir(self):
        """Botón para confirmar la nave seleccionada."""
        j = self.juego
        if not j.mostrar_boton_elegir or not j.estadisticas:
            return
        ANCHO    = config.ANCHO
        ALTO     = config.ALTO
        x_centro = ANCHO // 2
        y_base   = ALTO - 150
        ancho    = 400
        alto     = 60

        rect = pygame.Rect(x_centro - ancho // 2, y_base, ancho, alto)
        j.boton_elegir_rect = rect

        pygame.draw.rect(self.pantalla, (0, 150, 0), rect)
        pygame.draw.rect(self.pantalla, (255, 255, 255), rect, 3)
        texto = f"✨ ¡ESCOJO ESTA NAVE! (Gasta {j.estadisticas['energia_gastada']}⚡) ✨"
        sf = self._fuente_md.render(texto, True, (255, 255, 255))
        self.pantalla.blit(sf, (x_centro - sf.get_width() // 2, y_base + 20))

    def dibujar_estadisticas(self):
        """Panel con estadísticas de la nave elegida."""
        j = self.juego
        if not j.estadisticas_elegidas:
            return
        ANCHO = config.ANCHO
        x     = ANCHO - 320
        y     = 100
        ancho = 300
        alto  = 130

        pygame.draw.rect(self.pantalla, (0, 40, 0, 200), (x, y, ancho, alto))
        pygame.draw.rect(self.pantalla, (0, 255, 0), (x, y, ancho, alto), 2)

        nombres = {'anchura': 'EXPLORADORA', 'profundidad': 'AVENTURERA', 'costouniforme': 'ESTRATEGA'}
        titulo  = f"✨ NAVE {nombres[j.estadisticas_elegidas['tecnica']]} ✨"
        sf_titulo = self._fuente_sm.render(titulo, True, (255, 255, 100))
        self.pantalla.blit(sf_titulo, (x + 10, y + 5))

        lineas = [
            f"📊 Pasos: {j.estadisticas_elegidas['pasos_totales']}",
            f"🛤️  Camino: {j.estadisticas_elegidas['casillas_camino']} casillas",
            f"⚡ Gasto: {j.estadisticas_elegidas['energia_gastada']}",
            f"🔋 Restante: {j.energia_restante}",
        ]
        for i, linea in enumerate(lineas):
            sf = self._fuente_sm.render(linea, True, (255, 255, 255))
            self.pantalla.blit(sf, (x + 20, y + 35 + i * 20))

    def dibujar_mensaje(self):
        """Mensaje temporal centrado en pantalla."""
        j = self.juego
        if not j.mensaje_estado or pygame.time.get_ticks() - j.tiempo_mensaje > 3000:
            return
        ANCHO    = config.ANCHO
        x_centro = ANCHO // 2
        y_base   = 200

        fondo = pygame.Surface((600, 50), pygame.SRCALPHA)
        fondo.fill((*j.color_mensaje[:3], 200))
        self.pantalla.blit(fondo, (x_centro - 300, y_base))
        pygame.draw.rect(self.pantalla, (255, 255, 255), (x_centro - 300, y_base, 600, 50), 2)

        sf = self._fuente_md.render(j.mensaje_estado, True, (255, 255, 255))
        self.pantalla.blit(sf, (x_centro - sf.get_width() // 2, y_base + 15))
