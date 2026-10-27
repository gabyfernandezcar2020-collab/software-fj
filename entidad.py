# -*- coding: utf-8 -*-
"""
entidad.py
==========
Clase abstracta EntidadBase: representa las "entidades generales" del sistema
(clientes, servicios y reservas). Define lo que TODA entidad debe saber hacer:
tener un identificador único, describirse y validarse.
"""

from abc import ABC, abstractmethod


class EntidadBase(ABC):
    """Clase abstracta de la que heredan Cliente, Servicio y Reserva."""

    # Prefijo del identificador (cada subclase define el suyo: CLI, SRV, RES)
    PREFIJO = "ENT"

    # Contadores compartidos por prefijo, para que los ids no se repitan
    _contadores = {}

    def __init__(self):
        # Se incrementa el contador asociado al prefijo de la subclase
        EntidadBase._contadores[self.PREFIJO] = EntidadBase._contadores.get(self.PREFIJO, 0) + 1
        # Se construye el id con formato PREFIJO-001, PREFIJO-002, ...
        self._id = f"{self.PREFIJO}-{EntidadBase._contadores[self.PREFIJO]:03d}"

    @property
    def id(self):
        """Identificador único de solo lectura (encapsulación)."""
        return self._id

    @abstractmethod
    def describir(self):
        """Devuelve un texto que resume la entidad (cada subclase lo implementa)."""

    @abstractmethod
    def validar(self):
        """Verifica la coherencia de la entidad; lanza una excepción si hay error."""

    def __str__(self):
        # Al imprimir cualquier entidad se muestra su descripción
        return self.describir()
