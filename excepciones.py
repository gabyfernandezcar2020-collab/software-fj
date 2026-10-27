# -*- coding: utf-8 -*-
"""
excepciones.py
==============
Jerarquía de excepciones personalizadas del sistema Software FJ.

Todas heredan de ErrorSoftwareFJ, de modo que el resto del programa puede
capturar "cualquier error propio del sistema" con un solo except, o bien
capturar un tipo específico cuando necesite tratarlo de forma distinta.

Jerarquía:
    ErrorSoftwareFJ
    ├── ErrorValidacion
    │   ├── ParametroFaltanteError
    │   └── ErrorCliente
    ├── ErrorServicio
    │   └── ServicioNoDisponibleError
    ├── ErrorReserva
    │   └── OperacionNoPermitidaError
    └── CalculoInconsistenteError
"""


class ErrorSoftwareFJ(Exception):
    """Excepción base de la que heredan todos los errores del sistema."""

    # Código de error por defecto; cada subclase define el suyo propio
    codigo_defecto = "SFJ-000"

    def __init__(self, mensaje, codigo=None):
        # Se envía el mensaje a Exception para que str(error) y los traceback funcionen
        super().__init__(mensaje)
        # Se conserva el mensaje por separado para usarlo en logs y en pantalla
        self.mensaje = mensaje
        # Si no llega un código específico se usa el código definido en la clase
        self.codigo = codigo or self.codigo_defecto

    def __str__(self):
        # Representación legible: [CODIGO] mensaje
        return f"[{self.codigo}] {self.mensaje}"


class ErrorValidacion(ErrorSoftwareFJ):
    """Datos que no cumplen las reglas de validación (formato, rango, tipo)."""

    codigo_defecto = "SFJ-VAL"


class ParametroFaltanteError(ErrorValidacion):
    """Falta un parámetro obligatorio (o llegó vacío / None)."""

    codigo_defecto = "SFJ-VAL-FALTA"


class ErrorCliente(ErrorValidacion):
    """Error relacionado con los datos o la gestión de un cliente."""

    codigo_defecto = "SFJ-CLI"


class ErrorServicio(ErrorSoftwareFJ):
    """Error al crear, configurar o usar un servicio."""

    codigo_defecto = "SFJ-SRV"


class ServicioNoDisponibleError(ErrorServicio):
    """El servicio existe, pero en este momento no se puede reservar."""

    codigo_defecto = "SFJ-SRV-DISP"


class ErrorReserva(ErrorSoftwareFJ):
    """Error durante la creación, confirmación o procesamiento de una reserva."""

    codigo_defecto = "SFJ-RES"


class OperacionNoPermitidaError(ErrorReserva):
    """La operación no es válida para el estado actual de la reserva."""

    codigo_defecto = "SFJ-RES-OP"


class CalculoInconsistenteError(ErrorSoftwareFJ):
    """El cálculo de un costo produjo un resultado inválido o incoherente."""

    codigo_defecto = "SFJ-CAL"
