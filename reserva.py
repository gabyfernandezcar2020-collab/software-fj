# -*- coding: utf-8 -*-
"""
reserva.py
==========
Clase Reserva: integra cliente, servicio, duración y estado.

Implementa confirmar(), cancelar() y procesar() usando los bloques:
    try / except / else / finally   y   encadenamiento de excepciones (raise ... from ...)

Ciclo de vida del estado:
    PENDIENTE -> CONFIRMADA -> PROCESADA
         |            |
         |            +-> CANCELADA
         +-> FALLIDA (si la confirmación no pasa las validaciones)
"""

from enum import Enum

from cliente import Cliente
from entidad import EntidadBase
from excepciones import (
    ErrorReserva,
    ErrorSoftwareFJ,
    OperacionNoPermitidaError,
    ParametroFaltanteError,
)
from logger import obtener_logger
from servicios import Servicio

# Logger compartido del sistema
logger = obtener_logger()


class EstadoReserva(Enum):
    """Estados posibles de una reserva."""

    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    PROCESADA = "PROCESADA"
    CANCELADA = "CANCELADA"
    FALLIDA = "FALLIDA"


class Reserva(EntidadBase):
    """Reserva de un servicio por parte de un cliente."""

    PREFIJO = "RES"

    def __init__(self, cliente, servicio, horas, **opciones):
        # Se verifica que los objetos recibidos sean del tipo correcto
        if not isinstance(cliente, Cliente):
            raise ErrorReserva("Se requiere un Cliente válido para crear la reserva.")
        if not isinstance(servicio, Servicio):
            raise ErrorReserva("Se requiere un Servicio válido para crear la reserva.")
        if horas is None:
            raise ParametroFaltanteError("La duración (horas) de la reserva es obligatoria.")

        self._cliente = cliente
        self._servicio = servicio
        self._horas = horas
        # Parámetros extra del servicio (personas, cantidad, etc.)
        self._opciones = opciones
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total = None
        self._motivo_cancelacion = None
        super().__init__()

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------
    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def horas(self):
        return self._horas

    @property
    def estado(self):
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    # ------------------------------------------------------------------
    # Confirmar: try / except / else / finally + encadenamiento
    # ------------------------------------------------------------------
    def confirmar(self):
        """Confirma la reserva si el servicio está disponible y los parámetros son válidos."""
        # Solo se puede confirmar una reserva pendiente
        if self._estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"La reserva {self.id} no se puede confirmar desde el estado {self._estado.value}."
            )
        try:
            # Se comprueba disponibilidad y parámetros del servicio
            self._servicio.verificar_disponibilidad()
            self._servicio.validar_parametros(self._horas, **self._opciones)
        except ErrorSoftwareFJ as error:
            # La reserva queda marcada como fallida y se registra el motivo
            self._estado = EstadoReserva.FALLIDA
            logger.error("Reserva %s fallida al confirmar: %s", self.id, error)
            # Encadenamiento: se lanza un error de reserva conservando la causa original
            raise ErrorReserva(
                f"No se pudo confirmar la reserva {self.id}: {error.mensaje}"
            ) from error
        else:
            # Este bloque solo se ejecuta si NO hubo excepción
            self._estado = EstadoReserva.CONFIRMADA
            logger.info("Reserva %s confirmada (%s, %s h)", self.id, self._servicio.nombre, self._horas)
            return True
        finally:
            # Este bloque se ejecuta SIEMPRE, haya o no error
            logger.debug("Intento de confirmación de %s finalizado (estado=%s)", self.id, self._estado.value)

    # ------------------------------------------------------------------
    # Cancelar
    # ------------------------------------------------------------------
    def cancelar(self, motivo="Sin motivo especificado"):
        """Cancela una reserva pendiente o confirmada."""
        # No se puede cancelar lo que ya fue procesado, cancelado o falló
        if self._estado not in (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA):
            raise OperacionNoPermitidaError(
                f"La reserva {self.id} no se puede cancelar desde el estado {self._estado.value}."
            )
        self._estado = EstadoReserva.CANCELADA
        self._motivo_cancelacion = motivo
        logger.warning("Reserva %s cancelada. Motivo: %s", self.id, motivo)
        return True

    # ------------------------------------------------------------------
    # Procesar: try / except / else / finally + encadenamiento
    # ------------------------------------------------------------------
    def procesar(self, impuesto=None, descuento=None):
        """Calcula el costo final y deja la reserva como PROCESADA."""
        # Solo una reserva confirmada puede procesarse
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"La reserva {self.id} debe estar CONFIRMADA para procesarse (estado actual: {self._estado.value})."
            )
        try:
            # Uso de la sobrecarga: impuesto y descuento son opcionales
            costo = self._servicio.calcular_costo(
                self._horas, impuesto, descuento, **self._opciones
            )
        except ErrorSoftwareFJ as error:
            logger.error("Reserva %s: fallo al procesar: %s", self.id, error)
            # La reserva sigue CONFIRMADA para poder reintentar con otros valores
            raise ErrorReserva(
                f"No se pudo procesar la reserva {self.id}: {error.mensaje}"
            ) from error
        else:
            self._costo_total = costo
            self._estado = EstadoReserva.PROCESADA
            logger.info("Reserva %s procesada. Costo total: $%s", self.id, f"{costo:,.2f}")
            return costo
        finally:
            logger.debug("Intento de procesamiento de %s finalizado (estado=%s)", self.id, self._estado.value)

    # ------------------------------------------------------------------
    # Métodos abstractos de EntidadBase
    # ------------------------------------------------------------------
    def describir(self):
        costo = f"${self._costo_total:,.2f}" if self._costo_total is not None else "por calcular"
        return (
            f"Reserva {self.id} | {self._cliente.nombre} -> {self._servicio.nombre} | "
            f"{self._horas} h | Estado: {self._estado.value} | Costo: {costo}"
        )

    def validar(self):
        """Verifica que cliente y servicio sigan siendo válidos."""
        self._cliente.validar()
        self._servicio.validar()
        return True
