# -*- coding: utf-8 -*-
"""
gestor.py
=========
GestorSoftwareFJ: administra las listas internas de clientes, servicios y
reservas (sin base de datos) y garantiza que NINGÚN error detenga el programa.

Idea clave: todas las operaciones públicas pasan por _ejecutar_seguro(), que
atrapa los errores, los registra en el log y devuelve None en vez de romper
la aplicación.
"""

from cliente import Cliente
from excepciones import (
    ErrorCliente,
    ErrorReserva,
    ErrorServicio,
    ErrorSoftwareFJ,
    ParametroFaltanteError,
)
from logger import obtener_logger
from reserva import EstadoReserva, Reserva
from servicios import AlquilerEquipo, AsesoriaEspecializada, SalaReuniones

logger = obtener_logger()


class GestorSoftwareFJ:
    """Administra clientes, servicios y reservas de la empresa Software FJ."""

    # Tipos de servicio que se pueden crear (clave de texto -> clase)
    TIPOS_SERVICIO = {
        "sala": SalaReuniones,
        "equipo": AlquilerEquipo,
        "asesoria": AsesoriaEspecializada,
    }

    def __init__(self):
        # Listas internas: reemplazan a la base de datos
        self._clientes = []
        self._servicios = []
        self._reservas = []
        # Contadores de la simulación
        self._operaciones = 0
        self._exitos = 0
        self._errores = 0
        # Último error ocurrido (texto) para mostrarlo en pantalla
        self._ultima_cadena_error = None
        logger.info("=== Sistema Software FJ iniciado ===")

    # ------------------------------------------------------------------
    # Acceso de solo lectura a las listas (tuplas = copia inmutable)
    # ------------------------------------------------------------------
    @property
    def clientes(self):
        return tuple(self._clientes)

    @property
    def servicios(self):
        return tuple(self._servicios)

    @property
    def reservas(self):
        return tuple(self._reservas)

    @property
    def ultima_cadena_error(self):
        return self._ultima_cadena_error

    # ------------------------------------------------------------------
    # Núcleo de estabilidad: ejecución segura
    # ------------------------------------------------------------------
    @staticmethod
    def _cadena_causas(error):
        """Recorre el encadenamiento (__cause__) y lo devuelve como un solo texto."""
        partes = []
        actual = error
        while actual is not None:
            partes.append(f"{type(actual).__name__}: {actual}")
            actual = actual.__cause__
        return "  <-causa-  ".join(partes)

    def _ejecutar_seguro(self, operacion, funcion, *args, **kwargs):
        """Ejecuta 'funcion' sin permitir que un error detenga el sistema.

        Devuelve el resultado, o None si hubo un error (ya registrado en el log).
        """
        self._ultima_cadena_error = None
        try:
            resultado = funcion(*args, **kwargs)
        except ErrorSoftwareFJ as error:
            # Error propio del sistema: se registra con toda su cadena de causas
            self._errores += 1
            self._ultima_cadena_error = self._cadena_causas(error)
            logger.error("[%s] %s", operacion, self._ultima_cadena_error)
            return None
        except Exception as error:  # red de seguridad para errores no previstos
            self._errores += 1
            self._ultima_cadena_error = self._cadena_causas(error)
            logger.critical("[%s] Error INESPERADO: %s", operacion, self._ultima_cadena_error, exc_info=True)
            return None
        else:
            # Solo se ejecuta si no hubo excepción
            self._exitos += 1
            logger.info("[%s] completada correctamente", operacion)
            return resultado
        finally:
            # Se ejecuta siempre: cuenta la operación y deja constancia
            self._operaciones += 1
            logger.debug("[%s] finalizada (operaciones totales: %d)", operacion, self._operaciones)

    # ------------------------------------------------------------------
    # Búsquedas
    # ------------------------------------------------------------------
    @staticmethod
    def _buscar(lista, id_buscado, excepcion, etiqueta):
        """Busca una entidad por id; si no existe lanza la excepción indicada."""
        for elemento in lista:
            if elemento.id == id_buscado:
                return elemento
        raise excepcion(f"No existe {etiqueta} con id '{id_buscado}'.")

    # ------------------------------------------------------------------
    # Clientes
    # ------------------------------------------------------------------
    def registrar_cliente(self, nombre=None, documento=None, correo=None, telefono=None):
        """Registra un cliente. Devuelve el Cliente o None si hubo error."""
        return self._ejecutar_seguro(
            "registrar_cliente", self._alta_cliente, nombre, documento, correo, telefono
        )

    def _alta_cliente(self, nombre, documento, correo, telefono):
        # Se normaliza el documento para comparar contra los ya registrados
        documento_norm = None if documento is None else str(documento).strip()
        if any(c.documento == documento_norm for c in self._clientes):
            raise ErrorCliente(
                f"Ya existe un cliente registrado con el documento {documento_norm}.", "SFJ-CLI-DUP"
            )
        cliente = Cliente(nombre, documento, correo, telefono)
        self._clientes.append(cliente)
        return cliente

    # ------------------------------------------------------------------
    # Servicios
    # ------------------------------------------------------------------
    def crear_servicio(self, tipo=None, **datos):
        """Crea un servicio ('sala', 'equipo' o 'asesoria'). Devuelve el Servicio o None."""
        return self._ejecutar_seguro("crear_servicio", self._alta_servicio, tipo, **datos)

    def _alta_servicio(self, tipo, **datos):
        clase = self.TIPOS_SERVICIO.get(str(tipo).lower())
        if clase is None:
            raise ErrorServicio(
                f"Tipo de servicio desconocido: '{tipo}'. Opciones: {', '.join(self.TIPOS_SERVICIO)}."
            )
        try:
            servicio = clase(**datos)
        except TypeError as error:
            # Faltan o sobran argumentos: se convierte en un error propio (encadenado)
            raise ParametroFaltanteError(
                f"Parámetros faltantes o inválidos para el servicio '{tipo}'."
            ) from error
        self._servicios.append(servicio)
        return servicio

    # ------------------------------------------------------------------
    # Reservas
    # ------------------------------------------------------------------
    def crear_reserva(self, id_cliente, id_servicio, horas, **opciones):
        """Crea una reserva PENDIENTE. Devuelve la Reserva o None."""
        return self._ejecutar_seguro(
            "crear_reserva", self._alta_reserva, id_cliente, id_servicio, horas, **opciones
        )

    def _alta_reserva(self, id_cliente, id_servicio, horas, **opciones):
        cliente = self._buscar(self._clientes, id_cliente, ErrorCliente, "un cliente")
        servicio = self._buscar(self._servicios, id_servicio, ErrorServicio, "un servicio")
        reserva = Reserva(cliente, servicio, horas, **opciones)
        self._reservas.append(reserva)
        return reserva

    def confirmar_reserva(self, id_reserva):
        """Confirma una reserva. Devuelve True o None."""
        return self._ejecutar_seguro(
            "confirmar_reserva",
            lambda: self._buscar(self._reservas, id_reserva, ErrorReserva, "una reserva").confirmar(),
        )

    def cancelar_reserva(self, id_reserva, motivo="Sin motivo especificado"):
        """Cancela una reserva. Devuelve True o None."""
        return self._ejecutar_seguro(
            "cancelar_reserva",
            lambda: self._buscar(self._reservas, id_reserva, ErrorReserva, "una reserva").cancelar(motivo),
        )

    def procesar_reserva(self, id_reserva, impuesto=None, descuento=None):
        """Procesa una reserva y devuelve su costo total, o None."""
        return self._ejecutar_seguro(
            "procesar_reserva",
            lambda: self._buscar(self._reservas, id_reserva, ErrorReserva, "una reserva").procesar(
                impuesto, descuento
            ),
        )

    # ------------------------------------------------------------------
    # Resumen
    # ------------------------------------------------------------------
    def mostrar_resumen(self):
        """Imprime el estado final del sistema."""
        print("\n" + "=" * 70)
        print("RESUMEN FINAL DEL SISTEMA")
        print("=" * 70)
        print(f"Operaciones ejecutadas : {self._operaciones}")
        print(f"  - Exitosas           : {self._exitos}")
        print(f"  - Con error controlado: {self._errores}")
        print(f"Clientes registrados   : {len(self._clientes)}")
        print(f"Servicios creados      : {len(self._servicios)}")
        print(f"Reservas totales       : {len(self._reservas)}")
        for estado in EstadoReserva:
            cantidad = sum(1 for r in self._reservas if r.estado is estado)
            print(f"  - {estado.value:<11}: {cantidad}")
        ingresos = sum(r.costo_total for r in self._reservas if r.costo_total is not None)
        print(f"Ingresos procesados    : ${ingresos:,.2f}")
        print("=" * 70)
        logger.info(
            "Resumen: %d operaciones, %d exitosas, %d con error controlado",
            self._operaciones, self._exitos, self._errores,
        )
