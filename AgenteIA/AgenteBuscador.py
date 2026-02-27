# **********************************************************
# * Clase: Agente buscador                                 *
# * Autor: Victor Estevez                                  *
# * Version: v2023.03.29                                   *
# * Descripcion: Implementacion de algoritmos de busqueda  *
# *              sin informacion y con informacion         *
# **********************************************************

from AgenteIA.Agente import Agente
from copy import deepcopy
import time


class AgenteBuscador(Agente):
    def __init__(self):
        Agente.__init__(self)
        self.__estado_inicial = None
        self.__estado_meta = None
        self.__funcion_sucesor = []
        self.__tecnica = None

    def set_estado_inicial(self, e0):
        self.__estado_inicial = e0

    def set_estado_meta(self, ef):
        self.__estado_meta = ef

    def get_estado_inicial(self):
        return self.__estado_inicial

    def get_estado_meta(self):
        return self.__estado_meta

    def set_tecnica(self, t):
        self.__tecnica = t

    def add_funcion(self, f):
        self.__funcion_sucesor.append(f)

    def test_objetivo(self, e):
        return e == self.__estado_meta

    def generar_hijos(self, e):
        hijos = [fun(e) for fun in self.__funcion_sucesor]
        return hijos

    def get_costo(self, camino):
        raise Exception("Error: No existe implementacion")

    def get_heuristica(self, camino):
        raise Exception("Error: No existe implementacion")

    def get_funcion_a(self, camino):
        return self.get_costo(camino) + self.get_heuristica(camino)

    def mide_tiempo(funcion):
        def funcion_medida(*args, **kwards):
            inicio = time.time()
            c = funcion(*args, **kwards)
            t = time.time()-inicio
            print("Tiempo de ejecucion: ", t)
            return c
        return funcion_medida

    @mide_tiempo
    def programa(self):
        frontera = [[self.__estado_inicial]]
        visitados = []
        cont = 0
        inicio_busqueda = time.time()
        self.get_medida_rendimiento()["max_profundidad"]=0
        self.get_medida_rendimiento()["nodos_expandidos"]=0
        while frontera:
            cont += 1
            if self.__tecnica == "profundidad":
                camino = frontera.pop()
            else:
                camino = frontera.pop(0)
            nodo = camino[-1]
            # Actualizar profundidad máxima
            self.get_medida_rendimiento()["max_profundidad"] = max( self.get_medida_rendimiento()["max_profundidad"], len(camino))

            visitados.append(nodo)
            self.get_medida_rendimiento()["nodos_expandidos"] += 1
            if self.test_objetivo(nodo):
                self.set_acciones(camino)
                self.get_medida_rendimiento()["pasos"] = len(camino)
                self.get_medida_rendimiento()["Costo"] = self.get_costo(camino)
                self.get_medida_rendimiento()["tiempo"] = time.time() - inicio_busqueda

                break
            else:
                for hijo in self.generar_hijos(nodo):
                    if hijo not in visitados:
                        aux = deepcopy(camino)
                        aux.append(hijo)
                        frontera.append(aux)
                if self.__tecnica == "costouniforme":
                    frontera.sort(key=lambda tup: self.get_costo(tup))
                elif self.__tecnica == "codicioso":
                    frontera.sort(key=lambda tup: self.get_heuristica(tup))
                elif self.__tecnica == "a_estrella":
                    frontera.sort(key=lambda tup: self.get_funcion_a(tup))