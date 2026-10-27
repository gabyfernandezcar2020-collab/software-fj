# -*- coding: utf-8 -*-
"""
logger.py
=========
Configuración centralizada del archivo de logs de Software FJ.

Todos los errores y eventos relevantes del sistema se escriben en
logs/software_fj.log. Es el ÚNICO uso de archivos del proyecto (no hay base
de datos), tal como lo exige el enunciado.
"""

import logging
from pathlib import Path

# Carpeta "logs" junto a este archivo (se crea automáticamente si no existe)
RUTA_LOGS = Path(__file__).resolve().parent / "logs"
# Archivo donde quedan registrados los eventos y errores
ARCHIVO_LOG = RUTA_LOGS / "software_fj.log"


def obtener_logger(nombre="software_fj"):
    """Devuelve el logger del sistema, configurándolo solo la primera vez."""
    logger = logging.getLogger(nombre)

    # Si ya tiene manejadores, ya fue configurado: se devuelve tal cual
    if logger.handlers:
        return logger

    # Se registran todos los niveles (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    logger.setLevel(logging.DEBUG)

    # Se asegura que la carpeta de logs exista
    RUTA_LOGS.mkdir(exist_ok=True)

    # Formato de cada línea: fecha | nivel | módulo.función | mensaje
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)s.%(funcName)s | %(message)s"
    )

    # Manejador que escribe en el archivo (UTF-8 para tildes y eñes)
    manejador_archivo = logging.FileHandler(ARCHIVO_LOG, mode="a", encoding="utf-8")
    manejador_archivo.setFormatter(formato)
    logger.addHandler(manejador_archivo)

    # Evita que los mensajes se dupliquen en el logger raíz
    logger.propagate = False
    return logger
