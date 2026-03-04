import speech_recognition as sr
import pyttsx3
import threading

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

        # Texto a voz
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 135)  # velocidad adecuada para niños
        self.engine.setProperty('volume', 1.0)

        # Diccionario emocional simple
        self.emociones = {
            "triste": "tristeza",
            "miedo": "miedo",
            "enojado": "enojo",
            "feliz": "alegria",
            "ansioso": "ansiedad"
        }

    # ─────────────────────────────────────
    # TEXTO A VOZ
    # ─────────────────────────────────────

    def hablar(self, texto):
        """Habla sin bloquear el juego."""
        def _hablar():
            self.engine.say(texto)
            self.engine.runAndWait()

        hilo = threading.Thread(target=_hablar)
        hilo.start()

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

        for palabra, emocion in self.emociones.items():
            if palabra in texto:
                return emocion

        return None
    
    def hablar_y_esperar(self, texto):
        self.engine.say(texto)
        self.engine.runAndWait()