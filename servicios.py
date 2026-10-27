# -*- coding: utf-8 -*-
"""
servicios.py
============
Clase abstracta Servicio y tres servicios especializados:

    - SalaReuniones          (reserva de salas)
    - AlquilerEquipo         (alquiler de equipos)
    - AsesoriaEspecializada  (asesorías especializadas)

Conceptos aplicados:
    - Abstracción: Servicio no se puede instanciar; obliga a las hijas a
      implementar calcular_costo_base(), validar_parametros() y describir().
    - Herencia y polimorfismo: cada hija calcula el costo y valida a su manera,
      pero se usan todas igual desde Reserva y el gestor.
    - Sobrecarga: Python no tiene sobrecarga nativa, así que se simula con
      parámetros opcionales (calcular_costo) y con functools.singledispatchmethod
      (cotizar), que elige la variante según el TIPO del argumento.
"""

from abc import abstractmethod
from functools import singledispatchmethod

from entidad import EntidadBase
from excepciones import (
    CalculoInconsistenteError,
    ErrorServicio,
    ParametroFaltanteError,
    ServicioNoDisponibleError,
)


class Servicio(EntidadBase):
    """Clase abstracta que define el contrato común de todos los servicios."""

    PREFIJO = "SRV"
    # Tasa de IVA usada por defecto en las cotizaciones
    IVA_DEFECTO = 0.19
    # Códigos promocionales disponibles (código -> porcentaje de descuento)
    CODIGOS_PROMOCION = {"ESTUDIANTE": 0.15, "CORPORATIVO": 0.20}

    def __init__(self, nombre, tarifa_hora, disponible=True):
        # Se validan los datos comunes antes de generar el id
        self._nombre = self._validar_texto(nombre, "nombre del servicio")
        self._tarifa_hora = self._validar_tarifa(tarifa_hora)
        self._disponible = bool(disponible)
        super().__init__()

    # ------------------------------------------------------------------
    # Validaciones reutilizables por las clases hijas
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_texto(valor, campo):
        """El valor debe existir y ser un texto no vacío."""
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")
        if not isinstance(valor, str):
            raise ErrorServicio(f"El campo '{campo}' debe ser texto.")
        return valor.strip()

    @staticmethod
    def _validar_tarifa(tarifa):
        """La tarifa por hora debe ser un número mayor que cero."""
        if tarifa is None:
            raise ParametroFaltanteError("La tarifa por hora es obligatoria.")
        if isinstance(tarifa, bool) or not isinstance(tarifa, (int, float)):
            raise ErrorServicio(f"La tarifa debe ser numérica (recibido: {type(tarifa).__name__}).")
        if tarifa <= 0:
            raise ErrorServicio(f"La tarifa por hora debe ser mayor que cero (recibido: {tarifa}).")
        return float(tarifa)

    @staticmethod
    def _validar_horas(horas, minimo, maximo):
        """La duración debe ser numérica y estar dentro del rango del servicio."""
        if horas is None:
            raise ParametroFaltanteError("La duración (horas) es obligatoria.")
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            raise ErrorServicio(f"La duración debe ser numérica (recibido: {type(horas).__name__}).")
        if not minimo <= horas <= maximo:
            raise ErrorServicio(
                f"La duración debe estar entre {minimo} y {maximo} horas (recibido: {horas})."
            )

    @staticmethod
    def _validar_entero(valor, campo, minimo, maximo):
        """Valida un entero (personas, cantidad, capacidad, stock) dentro de un rango."""
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ErrorServicio(f"El campo '{campo}' debe ser un número entero.")
        if not minimo <= valor <= maximo:
            raise ErrorServicio(
                f"El campo '{campo}' debe estar entre {minimo} y {maximo} (recibido: {valor})."
            )

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------
    @property
    def nombre(self):
        return self._nombre

    @property
    def tarifa_hora(self):
        return self._tarifa_hora

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        self._disponible = bool(valor)

    def verificar_disponibilidad(self):
        """Lanza ServicioNoDisponibleError si el servicio no se puede reservar."""
        if not self._disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._nombre}' ({self.id}) no está disponible en este momento."
            )

    # ------------------------------------------------------------------
    # Métodos abstractos: cada servicio especializado DEBE implementarlos
    # ------------------------------------------------------------------
    @abstractmethod
    def calcular_costo_base(self, horas, **opciones):
        """Costo sin impuestos ni descuentos (polimorfismo)."""

    @abstractmethod
    def validar_parametros(self, horas, **opciones):
        """Valida duración y parámetros propios del servicio (polimorfismo)."""

    # ------------------------------------------------------------------
    # Sobrecarga 1: calcular_costo con parámetros opcionales
    #   calcular_costo(2)                      -> costo base
    #   calcular_costo(2, impuesto=0.19)       -> base + IVA
    #   calcular_costo(2, 0.19, 0.10)          -> base - descuento + IVA
    # ------------------------------------------------------------------
    def calcular_costo(self, horas, impuesto=None, descuento=None, **opciones):
        """Calcula el costo final aplicando (si se pide) descuento e impuesto."""
        # Primero se validan los parámetros propios de cada servicio
        self.validar_parametros(horas, **opciones)
        # Cada servicio calcula su costo base a su manera
        costo = self.calcular_costo_base(horas, **opciones)

        if descuento is not None:
            # Un descuento fuera de [0, 1) haría el costo negativo o cero: es inconsistente
            if not 0 <= descuento < 1:
                raise CalculoInconsistenteError(
                    f"El descuento debe estar entre 0 y 1 (recibido: {descuento})."
                )
            costo -= costo * descuento

        if impuesto is not None:
            if not 0 <= impuesto <= 1:
                raise CalculoInconsistenteError(
                    f"El impuesto debe estar entre 0 y 1 (recibido: {impuesto})."
                )
            costo += costo * impuesto

        # Verificación final: un costo no positivo nunca debería ocurrir
        if costo <= 0:
            raise CalculoInconsistenteError(f"El costo calculado no es válido: {costo}.")
        return round(costo, 2)

    # ------------------------------------------------------------------
    # Sobrecarga 2: cotizar() elige la variante según el TIPO de 'promocion'
    #   cotizar(None, 2)          -> sin promoción, con IVA
    #   cotizar(10, 2)            -> 10 % de descuento, con IVA
    #   cotizar("ESTUDIANTE", 2)  -> descuento según el código, con IVA
    # ------------------------------------------------------------------
    @singledispatchmethod
    def cotizar(self, promocion, horas, **opciones):
        """Variante por defecto: el tipo de promoción no está soportado."""
        raise ErrorServicio(f"Tipo de promoción no soportado: {type(promocion).__name__}.")

    @cotizar.register(type(None))
    def _cotizar_sin_promocion(self, promocion, horas, **opciones):
        return self.calcular_costo(horas, impuesto=self.IVA_DEFECTO, **opciones)

    @cotizar.register(int)
    @cotizar.register(float)
    def _cotizar_porcentaje(self, promocion, horas, **opciones):
        # Un número se interpreta como porcentaje de descuento (10 -> 10 %)
        return self.calcular_costo(
            horas, impuesto=self.IVA_DEFECTO, descuento=promocion / 100, **opciones
        )

    @cotizar.register(str)
    def _cotizar_codigo(self, promocion, horas, **opciones):
        # Un texto se interpreta como código promocional
        codigo = promocion.strip().upper()
        if codigo not in self.CODIGOS_PROMOCION:
            raise ErrorServicio(f"El código promocional '{promocion}' no existe.")
        return self.calcular_costo(
            horas, impuesto=self.IVA_DEFECTO, descuento=self.CODIGOS_PROMOCION[codigo], **opciones
        )

    # ------------------------------------------------------------------
    # Método abstracto heredado de EntidadBase implementado a medias aquí
    # ------------------------------------------------------------------
    def validar(self):
        """Revalida los datos comunes del servicio."""
        self._validar_texto(self._nombre, "nombre del servicio")
        self._validar_tarifa(self._tarifa_hora)
        return True


# ======================================================================
# Servicio 1: sala de reuniones
# ======================================================================
class SalaReuniones(Servicio):
    """Reserva de salas por hora, con capacidad máxima y proyector opcional."""

    # Recargo aplicado cuando la sala incluye proyector
    RECARGO_PROYECTOR = 0.10

    def __init__(self, nombre, tarifa_hora, capacidad, tiene_proyector=False, disponible=True):
        # Se valida lo propio de la sala antes de inicializar la clase padre
        self._validar_entero(capacidad, "capacidad", 1, 500)
        self._capacidad = capacidad
        self._tiene_proyector = bool(tiene_proyector)
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas, personas=1, **_):
        # Una sala se reserva entre 1 y 12 horas
        self._validar_horas(horas, 1, 12)
        # El número de asistentes no puede superar la capacidad de la sala
        self._validar_entero(personas, "personas", 1, self._capacidad)

    def calcular_costo_base(self, horas, personas=1, **_):
        # Costo = tarifa por hora x horas
        costo = self._tarifa_hora * horas
        # Si tiene proyector se suma el recargo
        if self._tiene_proyector:
            costo *= 1 + self.RECARGO_PROYECTOR
        return costo

    def describir(self):
        proyector = "Sí" if self._tiene_proyector else "No"
        return (
            f"Sala '{self._nombre}' ({self.id}) | Capacidad: {self._capacidad} personas | "
            f"Proyector: {proyector} | Tarifa: ${self._tarifa_hora:,.0f}/h"
        )


# ======================================================================
# Servicio 2: alquiler de equipos
# ======================================================================
class AlquilerEquipo(Servicio):
    """Alquiler de equipos (portátiles, cámaras, etc.) con stock limitado."""

    # Alquileres de más de 24 horas reciben un 10 % de descuento automático
    UMBRAL_HORAS_PROLONGADO = 24
    DESCUENTO_PROLONGADO = 0.10

    def __init__(self, nombre, tarifa_hora, tipo_equipo, stock, disponible=True):
        self._tipo_equipo = self._validar_texto(tipo_equipo, "tipo de equipo")
        self._validar_entero(stock, "stock", 1, 1000)
        self._stock = stock
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas, cantidad=1, **_):
        # Un equipo se alquila entre 1 hora y 7 días (168 horas)
        self._validar_horas(horas, 1, 168)
        # No se pueden pedir más unidades de las que hay en stock
        self._validar_entero(cantidad, "cantidad", 1, self._stock)

    def calcular_costo_base(self, horas, cantidad=1, **_):
        # Costo = tarifa x horas x unidades
        costo = self._tarifa_hora * horas * cantidad
        # Descuento automático por alquiler prolongado
        if horas > self.UMBRAL_HORAS_PROLONGADO:
            costo *= 1 - self.DESCUENTO_PROLONGADO
        return costo

    def describir(self):
        return (
            f"Equipo '{self._nombre}' ({self.id}) | Tipo: {self._tipo_equipo} | "
            f"Stock: {self._stock} | Tarifa: ${self._tarifa_hora:,.0f}/h por unidad"
        )


# ======================================================================
# Servicio 3: asesoría especializada
# ======================================================================
class AsesoriaEspecializada(Servicio):
    """Asesoría por horas; el nivel del asesor multiplica la tarifa."""

    # Multiplicador de tarifa según el nivel del asesor
    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre, tarifa_hora, especialidad, nivel="junior", disponible=True):
        self._especialidad = self._validar_texto(especialidad, "especialidad")
        nivel = self._validar_texto(nivel, "nivel").lower()
        if nivel not in self.NIVELES:
            raise ErrorServicio(
                f"Nivel '{nivel}' no válido. Opciones: {', '.join(self.NIVELES)}."
            )
        self._nivel = nivel
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas, **_):
        # Una asesoría dura entre 1 y 8 horas
        self._validar_horas(horas, 1, 8)

    def calcular_costo_base(self, horas, **_):
        # Costo = tarifa x horas x multiplicador del nivel
        return self._tarifa_hora * horas * self.NIVELES[self._nivel]

    def describir(self):
        return (
            f"Asesoría '{self._nombre}' ({self.id}) | Especialidad: {self._especialidad} | "
            f"Nivel: {self._nivel} | Tarifa: ${self._tarifa_hora:,.0f}/h"
        )
