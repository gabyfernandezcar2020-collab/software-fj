# -*- coding: utf-8 -*-
"""
cliente.py
==========
Clase Cliente: encapsula los datos personales y los valida de forma estricta.

Encapsulación:
    - Los atributos son privados (doble guion bajo) y se exponen con @property.
    - El documento es de solo lectura una vez creado el cliente.
    - Correo y teléfono se pueden modificar, pero siempre pasan por validación.
"""

import re

from entidad import EntidadBase
from excepciones import ErrorCliente, ParametroFaltanteError


class Cliente(EntidadBase):
    """Cliente de Software FJ con datos personales validados."""

    PREFIJO = "CLI"

    # Solo letras (con tildes y ñ) y espacios, entre 3 y 60 caracteres
    _PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]{3,60}$")
    # Formato básico de correo: usuario@dominio.ext
    _PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
    # Celular colombiano: 10 dígitos que empiezan por 3
    _PATRON_TELEFONO = re.compile(r"^3\d{9}$")

    def __init__(self, nombre, documento, correo, telefono):
        # Se valida todo ANTES de generar el id: si algo falla, no se consume un id
        self.__nombre = self._validar_nombre(nombre)
        self.__documento = self._validar_documento(documento)
        self.__correo = self._validar_correo(correo)
        self.__telefono = self._validar_telefono(telefono)
        # Con los datos correctos se genera el identificador (CLI-001, ...)
        super().__init__()

    # ------------------------------------------------------------------
    # Validaciones (métodos estáticos reutilizados por constructor y setters)
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_nombre(nombre):
        """Verifica que el nombre exista y tenga un formato razonable."""
        if nombre is None or (isinstance(nombre, str) and not nombre.strip()):
            raise ParametroFaltanteError("El nombre del cliente es obligatorio.")
        if not isinstance(nombre, str):
            raise ErrorCliente(f"El nombre debe ser texto (recibido: {type(nombre).__name__}).")
        nombre = " ".join(nombre.split())  # quita espacios repetidos
        if not Cliente._PATRON_NOMBRE.match(nombre):
            raise ErrorCliente(
                f"El nombre '{nombre}' no es válido: use solo letras y espacios (3 a 60 caracteres)."
            )
        return nombre

    @staticmethod
    def _validar_documento(documento):
        """Verifica que el documento sea numérico y de 6 a 12 dígitos."""
        texto = "" if documento is None else str(documento).strip()
        if not texto:
            raise ParametroFaltanteError("El documento del cliente es obligatorio.")
        try:
            # int() lanza ValueError si hay letras; se encadena a un error propio
            int(texto)
        except ValueError as error:
            raise ErrorCliente(f"El documento '{texto}' debe contener solo dígitos.") from error
        if not (texto.isascii() and texto.isdigit()):
            raise ErrorCliente(f"El documento '{texto}' debe contener solo dígitos.")
        if not 6 <= len(texto) <= 12:
            raise ErrorCliente(f"El documento debe tener entre 6 y 12 dígitos (recibido: {len(texto)}).")
        return texto

    @staticmethod
    def _validar_correo(correo):
        """Verifica que el correo tenga formato usuario@dominio.ext."""
        if correo is None or (isinstance(correo, str) and not correo.strip()):
            raise ParametroFaltanteError("El correo del cliente es obligatorio.")
        if not isinstance(correo, str) or not Cliente._PATRON_CORREO.match(correo.strip()):
            raise ErrorCliente(f"El correo '{correo}' no tiene un formato válido.")
        return correo.strip().lower()

    @staticmethod
    def _validar_telefono(telefono):
        """Verifica que sea un celular de 10 dígitos que empiece por 3."""
        texto = "" if telefono is None else str(telefono).replace(" ", "")
        if not texto:
            raise ParametroFaltanteError("El teléfono del cliente es obligatorio.")
        if not Cliente._PATRON_TELEFONO.match(texto):
            raise ErrorCliente(f"El teléfono '{telefono}' no es válido (10 dígitos, inicia en 3).")
        return texto

    # ------------------------------------------------------------------
    # Propiedades (acceso controlado a los atributos privados)
    # ------------------------------------------------------------------
    @property
    def nombre(self):
        return self.__nombre

    @property
    def documento(self):
        # Solo lectura: no hay setter, el documento no cambia
        return self.__documento

    @property
    def correo(self):
        return self.__correo

    @correo.setter
    def correo(self, nuevo_correo):
        # El nuevo valor pasa por la misma validación del constructor
        self.__correo = self._validar_correo(nuevo_correo)

    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, nuevo_telefono):
        self.__telefono = self._validar_telefono(nuevo_telefono)

    # ------------------------------------------------------------------
    # Métodos abstractos implementados
    # ------------------------------------------------------------------
    def describir(self):
        # Se enmascara el documento para proteger el dato personal
        documento_oculto = "*" * (len(self.__documento) - 3) + self.__documento[-3:]
        return f"Cliente {self.id}: {self.__nombre} | Doc: {documento_oculto} | {self.__correo}"

    def validar(self):
        # Se vuelven a ejecutar todas las validaciones sobre los datos actuales
        self._validar_nombre(self.__nombre)
        self._validar_documento(self.__documento)
        self._validar_correo(self.__correo)
        self._validar_telefono(self.__telefono)
        return True
