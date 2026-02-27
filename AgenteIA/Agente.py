# *************************************************************
# * Clase: Agente                                             *
# * Autor: Victor Estevez                                     *
# * Version: v2023.03.29                                      *
# * Descripcion: Implementacion de agente, percibe de su      *
# *              entorno, mapea las percepciones y modifica   *
# *              su entorno para resolucion de problema       *
# *************************************************************


class Agente:

    def __init__(self):
        # necesitaos aber que percibe el agente
        self.__percepciones = None
        # necesitamos saber que acciones realzia el agente
        self.__acciones = []
        # debemos saber en que medida el agente resuelve el problema
        self._medida_rendimiento = {}
        # bandera si el agente esta activado
        self.__habilitado = True

    def set_percepciones(self, p):
        self.__percepciones = p

    def get_percepciones(self):
        return self.__percepciones

    def get_acciones(self):
        return self.__acciones

    def set_acciones(self, a):
        self.__acciones = a

    def inhabilitar(self):
        self.__habilitado = False

    def habilitar(self):
        self.__habilitado = True

    def esta_habilitado(self):
        return self.__habilitado
    
    
    def get_medida_rendimiento(self):
        return self._medida_rendimiento

    # como planifico mis acciones para resolver el problema
    def programa(self):
        raise Exception("No existe implementacion")