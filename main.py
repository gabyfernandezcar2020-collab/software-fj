# -*- coding: utf-8 -*-
"""
main.py
=======
Punto de entrada de Software FJ.

Simula más de 10 operaciones completas (válidas e inválidas) para demostrar
que el sistema sigue funcionando aunque ocurran errores graves.

Ejecución:
    python main.py
"""

import sys

from gestor import GestorSoftwareFJ
from logger import ARCHIVO_LOG, obtener_logger
from servicios import Servicio

logger = obtener_logger()

# Contador global para numerar las operaciones en pantalla
_numero_operacion = 0


def paso(gestor, descripcion, funcion, *args, **kwargs):
    """Ejecuta una operación del gestor e imprime si fue exitosa o falló de forma controlada."""
    global _numero_operacion
    _numero_operacion += 1
    print(f"\nOperación {_numero_operacion:02d}: {descripcion}")
    resultado = funcion(*args, **kwargs)
    if resultado is None:
        print(f"   [ERROR CONTROLADO] {gestor.ultima_cadena_error}")
    elif resultado is True:
        print("   [OK] Operación realizada correctamente.")
    elif isinstance(resultado, float):
        print(f"   [OK] Costo calculado: ${resultado:,.2f}")
    else:
        print(f"   [OK] {resultado}")
    return resultado


def demostrar_polimorfismo_y_sobrecarga(gestor):
    """Recorre los servicios con la misma interfaz y muestra las variantes de cotización."""
    print("\n" + "-" * 70)
    print("DEMOSTRACIÓN: POLIMORFISMO Y SOBRECARGA (cada servicio, 2 horas)")
    print("-" * 70)
    for servicio in gestor.servicios:
        print(servicio.describir())
        print(f"   costo base ............. ${servicio.calcular_costo(2):>12,.2f}")
        print(f"   con IVA 19 % ........... ${servicio.calcular_costo(2, 0.19):>12,.2f}")
        print(f"   con IVA y 10 % dto. .... ${servicio.calcular_costo(2, 0.19, 0.10):>12,.2f}")
        print(f"   cotizar(None) .......... ${servicio.cotizar(None, 2):>12,.2f}")
        print(f"   cotizar(10)  [int] ..... ${servicio.cotizar(10, 2):>12,.2f}")
        print(f"   cotizar('ESTUDIANTE') .. ${servicio.cotizar('ESTUDIANTE', 2):>12,.2f}")


def ejecutar_simulacion():
    """Ejecuta las operaciones de la simulación."""
    gestor = GestorSoftwareFJ()

    print("=" * 70)
    print("SOFTWARE FJ - SISTEMA INTEGRAL DE CLIENTES, SERVICIOS Y RESERVAS")
    print("=" * 70)

    # ------------------------------ CLIENTES ------------------------------
    ana = paso(gestor, "Registrar cliente VÁLIDO (Ana María López)",
               gestor.registrar_cliente, "Ana María López", "1098765432", "ana.lopez@correo.com", "3101234567")
    carlos = paso(gestor, "Registrar cliente VÁLIDO (Carlos Ruiz)",
                  gestor.registrar_cliente, "Carlos Ruiz", "80123456", "carlos.ruiz@correo.com", "3209876543")
    paso(gestor, "Registrar cliente INVÁLIDO: correo mal formado",
         gestor.registrar_cliente, "Luis Pérez", "1234567", "luis@@correo", "3001112233")
    paso(gestor, "Registrar cliente INVÁLIDO: documento con letras (error encadenado)",
         gestor.registrar_cliente, "Marta Gómez", "12AB45", "marta@correo.com", "3001112233")
    paso(gestor, "Registrar cliente INVÁLIDO: falta el nombre (parámetro faltante)",
         gestor.registrar_cliente, None, "55667788", "sin.nombre@correo.com", "3001112233")
    paso(gestor, "Registrar cliente DUPLICADO (mismo documento de Ana)",
         gestor.registrar_cliente, "Ana Duplicada", "1098765432", "otra@correo.com", "3101234567")

    # ------------------------------ SERVICIOS -----------------------------
    sala = paso(gestor, "Crear servicio VÁLIDO: sala de reuniones",
                gestor.crear_servicio, "sala", nombre="Sala Innovación", tarifa_hora=60000,
                capacidad=10, tiene_proyector=True)
    equipo = paso(gestor, "Crear servicio VÁLIDO: alquiler de portátiles",
                  gestor.crear_servicio, "equipo", nombre="Portátiles Dell", tarifa_hora=8000,
                  tipo_equipo="Portátil", stock=5)
    asesoria = paso(gestor, "Crear servicio VÁLIDO: asesoría en nube (nivel senior)",
                    gestor.crear_servicio, "asesoria", nombre="Asesoría Cloud", tarifa_hora=90000,
                    especialidad="Computación en la nube", nivel="senior")
    paso(gestor, "Crear servicio INVÁLIDO: tarifa negativa",
         gestor.crear_servicio, "sala", nombre="Sala Fantasma", tarifa_hora=-500, capacidad=4)
    paso(gestor, "Crear servicio INVÁLIDO: falta la capacidad (TypeError encadenado)",
         gestor.crear_servicio, "sala", nombre="Sala Incompleta", tarifa_hora=40000)
    paso(gestor, "Crear servicio INVÁLIDO: tipo inexistente ('drones')",
         gestor.crear_servicio, "drones", nombre="Drones", tarifa_hora=1000)

    # Intento directo de instanciar la clase abstracta (debe fallar y registrarse)
    global _numero_operacion
    _numero_operacion += 1
    print(f"\nOperación {_numero_operacion:02d}: Instanciar directamente la clase abstracta Servicio")
    try:
        Servicio("Genérico", 1000)
    except TypeError as error:
        logger.error("[instanciar_abstracta] %s: %s", type(error).__name__, error)
        print(f"   [ERROR CONTROLADO] TypeError: {error}")

    # ------------------------------ RESERVAS ------------------------------
    # Reserva exitosa de sala: crear -> confirmar -> procesar (IVA 19 % y 10 % de descuento)
    r1 = paso(gestor, "Crear reserva de sala (Ana, 3 h, 5 personas)",
              gestor.crear_reserva, ana.id, sala.id, 3, personas=5)
    paso(gestor, "Confirmar reserva de sala", gestor.confirmar_reserva, r1.id)
    paso(gestor, "Procesar reserva de sala con IVA 19 % y 10 % de descuento",
         gestor.procesar_reserva, r1.id, 0.19, 0.10)

    # Reserva exitosa de equipos con descuento automático por alquiler prolongado
    r2 = paso(gestor, "Crear reserva de equipos (Carlos, 3 portátiles, 30 h)",
              gestor.crear_reserva, carlos.id, equipo.id, 30, cantidad=3)
    paso(gestor, "Confirmar reserva de equipos", gestor.confirmar_reserva, r2.id)
    paso(gestor, "Procesar reserva de equipos con IVA 19 %",
         gestor.procesar_reserva, r2.id, 0.19)

    # Reservas fallidas
    r3 = paso(gestor, "Crear reserva de asesoría con 20 horas (excede el máximo de 8)",
              gestor.crear_reserva, ana.id, asesoria.id, 20)
    paso(gestor, "Confirmar reserva de asesoría inválida (debe fallar)", gestor.confirmar_reserva, r3.id)

    r4 = paso(gestor, "Crear reserva de sala con 25 personas (capacidad 10)",
              gestor.crear_reserva, carlos.id, sala.id, 2, personas=25)
    paso(gestor, "Confirmar reserva con exceso de personas (debe fallar)", gestor.confirmar_reserva, r4.id)

    paso(gestor, "Crear reserva con cliente INEXISTENTE (CLI-999)",
         gestor.crear_reserva, "CLI-999", sala.id, 2)

    # Servicio no disponible
    equipo.disponible = False
    r5 = paso(gestor, "Crear reserva de equipos que ahora NO están disponibles",
              gestor.crear_reserva, ana.id, equipo.id, 4, cantidad=1)
    paso(gestor, "Confirmar reserva de servicio no disponible (debe fallar)", gestor.confirmar_reserva, r5.id)
    equipo.disponible = True

    # Cancelaciones y operaciones no permitidas
    r6 = paso(gestor, "Crear reserva de asesoría válida (Carlos, 3 h)",
              gestor.crear_reserva, carlos.id, asesoria.id, 3)
    paso(gestor, "Confirmar reserva de asesoría", gestor.confirmar_reserva, r6.id)
    paso(gestor, "Cancelar reserva confirmada", gestor.cancelar_reserva, r6.id, "El cliente reprogramó la cita")
    paso(gestor, "Cancelar de nuevo la misma reserva (operación no permitida)",
         gestor.cancelar_reserva, r6.id, "Intento repetido")
    r7 = paso(gestor, "Crear reserva de sala sin confirmar (Ana, 1 h)",
              gestor.crear_reserva, ana.id, sala.id, 1, personas=2)
    paso(gestor, "Procesar una reserva PENDIENTE (operación no permitida)", gestor.procesar_reserva, r7.id)

    # Cálculo inconsistente y recuperación
    paso(gestor, "Confirmar reserva de sala (Ana, 1 h)", gestor.confirmar_reserva, r7.id)
    paso(gestor, "Procesar con descuento de 150 % (cálculo inconsistente)",
         gestor.procesar_reserva, r7.id, 0.19, 1.5)
    paso(gestor, "Reintentar el procesamiento con valores correctos (el sistema se recupera)",
         gestor.procesar_reserva, r7.id, 0.19, 0.05)

    # ---------------------- DEMOSTRACIONES Y RESUMEN ----------------------
    demostrar_polimorfismo_y_sobrecarga(gestor)

    print("\n" + "-" * 70)
    print("RESERVAS REGISTRADAS")
    print("-" * 70)
    for reserva in gestor.reservas:
        print(reserva.describir())

    gestor.mostrar_resumen()
    print(f"\nEl detalle de errores y eventos quedó en: {ARCHIVO_LOG}")


if __name__ == "__main__":
    # Se fuerza UTF-8 en la consola para que se vean bien tildes y eñes
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    try:
        ejecutar_simulacion()
    except Exception as error:  # última red de seguridad: nada debe cerrar el programa sin registro
        logger.critical("Error fatal fuera del gestor: %r", error, exc_info=True)
        print(f"Error inesperado registrado en el log: {error!r}")
