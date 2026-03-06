# niveles.py
import json

class GestorNiveles:
    def __init__(self, archivo="niveles.json"):
        with open(archivo, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.nivel_actual = 0
        self.niveles = self.data["niveles"]
    
    def obtener_nivel(self, idx=None):
        if idx is None:
            idx = self.nivel_actual
        return self.niveles[idx]
    
    def siguiente_nivel(self):
        if self.nivel_actual + 1 < len(self.niveles):
            self.nivel_actual += 1
            return True
        return False
    
    def reiniciar_nivel(self):
        return self.obtener_nivel(self.nivel_actual)
    
    def es_introductorio(self):
        return self.obtener_nivel().get("tipo") == "introductorio"