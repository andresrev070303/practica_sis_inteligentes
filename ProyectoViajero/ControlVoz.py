# ProyectoViajero/ControlVoz.py
import speech_recognition as sr
import pyttsx3
import threading
import queue
import random

class ControlVoz:
    """
    Maneja:
    - Reconocimiento de voz (STT)
    - Texto a voz (TTS) con frases dinámicas
    - Procesamiento de emociones
    """

    def __init__(self):
        # Reconocimiento
        self.recognizer = sr.Recognizer()
        self.microfono = sr.Microphone()

        # Texto a voz - Inicializar una sola vez
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 130)  # velocidad para niños
        self.engine.setProperty('volume', 1.0)
        
        # Cola para mensajes de voz (evita hilos simultáneos)
        self.cola_voz = queue.Queue()
        self.hilo_voz = threading.Thread(target=self._procesar_cola, daemon=True)
        self.hilo_voz.start()
        self.ocupado = False

        # Diccionario emocional simple
        self.emociones = {
            "triste": "tristeza",
            "tristeza": "tristeza",
            "miedo": "miedo",
            "asustado": "miedo",
            "temeroso": "miedo",
            "enojado": "enojo",
            "enojo": "enojo",
            "rabia": "enojo",
            "enfadado": "enojo",
            "feliz": "alegria",
            "alegre": "alegria",
            "alegria": "alegria",
            "contento": "alegria",
            "ansioso": "ansiedad",
            "ansiedad": "ansiedad",
            "nervioso": "ansiedad",
            "preocupado": "ansiedad"
        }
        
        # ─────────────────────────────────────
        # FRASES DINÁMICAS PARA PERSONALIZAR LA VOZ
        # ─────────────────────────────────────
        
        self.frases_bienvenida = [
            "¡Hola pequeño astronauta!",
            "¡Bienvenido a Conexión Mental!",
            "¿Listo para una aventura espacial?",
            "Hola, soy tu guía en esta misión."
        ]
        
        self.frases_pregunta_emocion = [
            "¿Cómo te sientes hoy?",
            "Cuéntame, ¿qué emoción tienes?",
            "¿Qué está pasando en tu corazón?",
            "Dime, ¿cómo te sientes?",
            "¿Qué emoción quieres explorar hoy?"
        ]
        
        self.frases_energia = [
            "Tienes {energia} de batería. ¡Úsala sabiamente!",
            "Batería: {energia}. Cada paso cuenta.",
            "Recuerda, gastas 1 de batería por cada movimiento.",
            "Tu nave tiene {energia} de energía disponible.",
            "Con {energia} de batería podemos llegar lejos."
        ]
        
        self.frases_nave = [
            "Elige una nave: B para Exploradora, D para Aventurera, U para Estratega.",
            "¿Qué nave prefieres?",
            "Presiona B, D o U para seleccionar tu nave.",
            "Ahora elige con qué nave quieres viajar.",
            "¿Cuál de mis naves te gusta más?"
        ]
        
        self.frases_exito = [
            "¡Lo logramos! Llegamos al planeta {planeta}.",
            "¡Misión cumplida! Llegamos a {planeta}.",
            "¡Bien hecho astronauta! Conectamos con {planeta}.",
            "¡Excelente! Hemos llegado a {planeta}.",
            "Misión completada. Planeta {planeta} alcanzado."
        ]
        
        self.frases_bateria_baja = [
            "¡Cuidado! Batería baja: {energia} restante.",
            "Te queda poca batería: {energia}. Elige bien.",
            "Solo {energia} de batería. ¡Concéntrate!",
            "Alerta: {energia} de batería. Cada paso cuenta.",
            "Batería crítica: {energia}. Piensa tu estrategia."
        ]
        
        self.frases_obstaculo = [
            "¡Cuidado con los obstáculos!",
            "Evita los asteroides y tormentas.",
            "No puedes pasar por otros planetas.",
            "Los obstáculos gastan mucha batería.",
            "¡Atención! Hay obstáculos en el camino."
        ]
        
        self.frases_emocion_detectada = {
            "tristeza": [
                "Entiendo, te sientes triste. Vamos al planeta Juego a alegrarnos.",
                "La tristeza es normal. Vamos al planeta Juego.",
                "Te acompaño al planeta Juego para sentirte mejor."
            ],
            "miedo": [
                "Tranquilo, el miedo se pasa. Busquemos el planeta Calma.",
                "El miedo nos protege. Vamos al planeta Calma.",
                "Respira hondo, vamos al planeta Calma."
            ],
            "enojo": [
                "Respira hondo. El planeta Abrazo nos espera.",
                "El enojo pasa. Vamos al planeta Abrazo.",
                "Te ayudo a encontrar el planeta Abrazo."
            ],
            "alegria": [
                "¡Qué bien! Compartamos esa alegría en el planeta Amigos.",
                "La alegría es contagiosa. Vamos al planeta Amigos.",
                "Excelente, celebremos en el planeta Amigos."
            ],
            "ansiedad": [
                "Vamos al planeta Respiración a calmarnos.",
                "La ansiedad se calma. Vamos al planeta Respiración.",
                "Respira conmigo. Vamos al planeta Respiración."
            ]
        }
        
        self.frases_eleccion_nave = [
            "Buena elección. La nave {nave} nos llevará al destino.",
            "¡Me encanta esa nave! La {nave} es muy especial.",
            "La {nave} es una excelente opción.",
            "Preparando la {nave} para el viaje."
        ]
        
        self.frases_camino_encontrado = [
            "¡Encontré un camino! Gasta {gasto} de batería.",
            "Tengo una ruta. Consume {gasto} de energía.",
            "Camino disponible. Necesitamos {gasto} de batería.",
            "Podemos llegar gastando {gasto} de energía."
        ]
        
        self.frases_despues_victoria = [
            "Nos quedan {energia} de batería. ¿Siguiente nivel?",
            "Excelente trabajo. Batería restante: {energia}.",
            "Misión cumplida con {energia} de batería sobrante.",
            "¡Bien hecho! Aún tenemos {energia} de energía."
        ]

    # ─────────────────────────────────────
    # TEXTO A VOZ
    # ─────────────────────────────────────

    def _procesar_cola(self):
        """Procesa la cola de mensajes de voz en un solo hilo"""
        while True:
            texto = self.cola_voz.get()
            self.ocupado = True
            self.engine.say(texto)
            self.engine.runAndWait()
            self.ocupado = False
            self.cola_voz.task_done()

    def hablar(self, texto):
        """Añade texto a la cola de voz (no bloquea)"""
        print(f"🗣️ {texto}")
        self.cola_voz.put(texto)

    def hablar_y_esperar(self, texto):
        """Habla y espera a que termine (bloqueante)"""
        print(f"🗣️ {texto}")
        # Vaciar cola actual
        while not self.cola_voz.empty():
            try:
                self.cola_voz.get_nowait()
            except:
                pass
        
        # Hablar directamente
        self.engine.say(texto)
        self.engine.runAndWait()
        
    # ─────────────────────────────────────
    # FRASES DINÁMICAS
    # ─────────────────────────────────────
    
    def hablar_frase(self, categoria, **kwargs):
        """
        Habla una frase aleatoria de una categoría
        Categorías: bienvenida, pregunta_emocion, energia, nave, 
                   exito, bateria_baja, obstaculo, emocion_detectada,
                   eleccion_nave, camino_encontrado, despues_victoria
        """
        if categoria == "bienvenida":
            frase = random.choice(self.frases_bienvenida)
            
        elif categoria == "pregunta_emocion":
            frase = random.choice(self.frases_pregunta_emocion)
            
        elif categoria == "energia":
            frase = random.choice(self.frases_energia).format(**kwargs)
            
        elif categoria == "nave":
            frase = random.choice(self.frases_nave)
            
        elif categoria == "exito":
            frase = random.choice(self.frases_exito).format(**kwargs)
            
        elif categoria == "bateria_baja":
            frase = random.choice(self.frases_bateria_baja).format(**kwargs)
            
        elif categoria == "obstaculo":
            frase = random.choice(self.frases_obstaculo)
            
        elif categoria == "emocion_detectada":
            emocion = kwargs.get("emocion", "")
            if emocion in self.frases_emocion_detectada:
                frase = random.choice(self.frases_emocion_detectada[emocion])
            else:
                frase = f"Vamos al planeta {kwargs.get('planeta', '')}."
                
        elif categoria == "eleccion_nave":
            frase = random.choice(self.frases_eleccion_nave).format(**kwargs)
            
        elif categoria == "camino_encontrado":
            frase = random.choice(self.frases_camino_encontrado).format(**kwargs)
            
        elif categoria == "despues_victoria":
            frase = random.choice(self.frases_despues_victoria).format(**kwargs)
            
        else:
            frase = kwargs.get("texto", "Hola")
        
        self.hablar(frase)

    # ─────────────────────────────────────
    # VOZ A TEXTO
    # ─────────────────────────────────────

    def escuchar(self, timeout=5):
        """Escucha y devuelve texto reconocido."""
        try:
            with self.microfono as source:
                print("🎤 Escuchando...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)

            texto = self.recognizer.recognize_google(audio, language="es-ES")
            print(f"📝 Reconocido: {texto}")
            return texto.lower()

        except sr.WaitTimeoutError:
            print("⏳ Tiempo de espera agotado")
            return None

        except sr.UnknownValueError:
            print("❓ No entendí")
            return None

        except sr.RequestError:
            print("🌐 Error de conexión")
            return None

    # ─────────────────────────────────────
    # PROCESAMIENTO EMOCIONAL
    # ─────────────────────────────────────

    def detectar_emocion(self, texto):
        """Detecta emoción clave en el texto."""
        if not texto:
            return None

        texto = texto.lower()
        for palabra, emocion in self.emociones.items():
            if palabra in texto:
                return emocion

        return None