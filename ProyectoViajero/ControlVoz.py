# ProyectoViajero/ControlVoz.py
import speech_recognition as sr
import pyttsx3
import threading
import queue

class ControlVoz:
    """
    Maneja:
    - Reconocimiento de voz (STT)
    - Texto a voz (TTS)
    - Procesamiento básico de emociones
    """

    def __init__(self):
        # Reconocimiento
        self.recognizer = sr.Recognizer()
        self.microfono = sr.Microphone()

        # Texto a voz - Inicializar una sola vez
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 135)  # velocidad adecuada para niños
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
            "enojado": "enojo",
            "enojo": "enojo",
            "rabia": "enojo",
            "feliz": "alegria",
            "alegre": "alegria",
            "alegria": "alegria",
            "ansioso": "ansiedad",
            "ansiedad": "ansiedad",
            "nervioso": "ansiedad"
        }

    # ─────────────────────────────────────
    # TEXTO A VOZ (CORREGIDO)
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