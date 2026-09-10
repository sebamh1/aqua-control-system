#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de control de O2
Demuestra cómo usar los componentes principales
"""

import logging
import time
import sys
from pathlib import Path

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from config import SerialConfig, SensorConfig, AWSConfig
from src.hardware.serial_manager import SerialManager
from src.sensors.dissolved_oxygen import DissolvedOxygenSensor
from src.actuators.relay_controller import RelayController
from src.experiments.saturation_controller import SaturationController
from src.cloud.aws_iot_client import AWSIoTClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def example_1_basic_sensor_reading():
    """Ejemplo 1: Lectura básica de sensores"""
    logger.info("=== Ejemplo 1: Lectura básica de sensores ===")

    # Crear serial manager
    serial_manager = SerialManager(
        sensor_port=SerialConfig.ESP32_SENSOR_PORT,
        relay_port=SerialConfig.ESP32_RELAY_PORT
    )

    # Conectar
    if not serial_manager.connect():
        logger.error("No se pudo conectar a los dispositivos")
        return

    # Crear sensores
    sensor_1 = DissolvedOxygenSensor(
        slave_id=SensorConfig.SENSOR_1_SLAVE_ID,
        serial_manager=serial_manager,
        name="Sensor O2 #1"
    )

    sensor_2 = DissolvedOxygenSensor(
        slave_id=SensorConfig.SENSOR_2_SLAVE_ID,
        serial_manager=serial_manager,
        name="Sensor O2 #2"
    )

    # Leer sensores 5 veces
    for i in range(5):
        logger.info(f"\n--- Lectura {i+1} ---")

        reading_1 = sensor_1.read_raw()
        if reading_1 and reading_1.is_valid:
            logger.info(f"Sensor 1: {reading_1.raw_o2:.2f} mg/L, Temp: {reading_1.temperature:.1f}°C")
        else:
            logger.warning(f"Sensor 1: Error - {reading_1.error_message if reading_1 else 'No response'}")

        reading_2 = sensor_2.read_raw()
        if reading_2 and reading_2.is_valid:
            logger.info(f"Sensor 2: {reading_2.raw_o2:.2f} mg/L, Temp: {reading_2.temperature:.1f}°C")
        else:
            logger.warning(f"Sensor 2: Error - {reading_2.error_message if reading_2 else 'No response'}")

        time.sleep(2)

    serial_manager.disconnect()
    logger.info("Desconectado\n")


def example_2_relay_control():
    """Ejemplo 2: Control de relés"""
    logger.info("=== Ejemplo 2: Control de relés ===")

    serial_manager = SerialManager(
        sensor_port=SerialConfig.ESP32_SENSOR_PORT,
        relay_port=SerialConfig.ESP32_RELAY_PORT
    )

    if not serial_manager.connect():
        logger.error("No se pudo conectar a los dispositivos")
        return

    # Crear controlador de relés
    relay_controller = RelayController(serial_manager)

    # Secuencia de prueba
    logger.info("Activando relé 1...")
    relay_controller.activate_relay(1)
    time.sleep(2)

    logger.info("Desactivando relé 1...")
    relay_controller.deactivate_relay(1)
    time.sleep(1)

    logger.info("Activando relé 2...")
    relay_controller.activate_relay(2)
    time.sleep(2)

    logger.info("Desactivando relé 2...")
    relay_controller.deactivate_relay(2)

    serial_manager.disconnect()
    logger.info("Desconectado\n")


def example_3_saturation_control():
    """Ejemplo 3: Control de saturación con histéresis"""
    logger.info("=== Ejemplo 3: Control de saturación ===")

    serial_manager = SerialManager(
        sensor_port=SerialConfig.ESP32_SENSOR_PORT,
        relay_port=SerialConfig.ESP32_RELAY_PORT
    )

    if not serial_manager.connect():
        logger.error("No se pudo conectar a los dispositivos")
        return

    # Crear componentes
    relay_controller = RelayController(serial_manager)
    saturation_controller = SaturationController(relay_controller)

    # Configurar objetivo
    saturation_controller.set_target_saturation(75.0)

    # Simular lecturas de saturación
    simulated_saturations = [30, 40, 50, 65, 75, 78, 76, 74, 73, 75, 76, 74]

    for i, current_sat in enumerate(simulated_saturations):
        logger.info(f"\n--- Iteración {i+1} (Saturación actual: {current_sat}%) ---")

        # Actualizar controlador
        control_state = saturation_controller.update(current_sat)

        logger.info(f"Acción: {control_state.action.name}")
        logger.info(f"Válvula 1: {'ABIERTA' if control_state.valve_1_open else 'CERRADA'}")
        logger.info(f"Estabilidad: {control_state.stability_percentage:.1f}%")

        if control_state.is_stable:
            logger.info("✓ Sistema ESTABLE")

        time.sleep(1)

    # Mostrar métricas
    metrics = saturation_controller.get_metrics()
    logger.info("\n=== Métricas Finales ===")
    logger.info(f"Target: {metrics['target']:.1f}%")
    logger.info(f"Media: {metrics['current_mean']:.1f}%")
    logger.info(f"Desv. Est: {metrics['current_std']:.2f}%")
    logger.info(f"Min: {metrics['min']:.1f}%, Max: {metrics['max']:.1f}%")

    serial_manager.disconnect()
    logger.info("Desconectado\n")


def example_4_aws_iot():
    """Ejemplo 4: Publicación en AWS IoT Core"""
    logger.info("=== Ejemplo 4: AWS IoT Core ===")

    # Crear cliente AWS
    aws_client = AWSIoTClient()

    # Conectar (puede fallar si no hay certificados)
    if aws_client.connect():
        logger.info("Conectado a AWS IoT Core")

        # Publicar telemetría
        telemetry = {
            "sensor_1_o2": 7.5,
            "sensor_2_o2": 7.4,
            "temperature": 18.2,
            "saturation": 75.3,
            "timestamp": time.time()
        }

        logger.info("Publicando telemetría...")
        aws_client.publish_telemetry(telemetry)

        # Actualizar shadow
        reported_state = {
            "current_o2": 7.45,
            "target_saturation": 75.0,
            "is_running": False,
            "aws_connection": "ONLINE"
        }

        logger.info("Actualizando device shadow...")
        aws_client.update_device_shadow(reported_state=reported_state)

        # Desconectar
        aws_client.disconnect()
        logger.info("Desconectado de AWS IoT Core")
    else:
        logger.warning("No se pudo conectar a AWS IoT (verifique certificados)")

    logger.info()


def example_5_full_experiment():
    """Ejemplo 5: Experimento completo"""
    logger.info("=== Ejemplo 5: Experimento Completo ===")

    serial_manager = SerialManager(
        sensor_port=SerialConfig.ESP32_SENSOR_PORT,
        relay_port=SerialConfig.ESP32_RELAY_PORT
    )

    if not serial_manager.connect():
        logger.error("No se pudo conectar a los dispositivos")
        return

    # Crear componentes
    sensor_1 = DissolvedOxygenSensor(
        slave_id=SensorConfig.SENSOR_1_SLAVE_ID,
        serial_manager=serial_manager,
        name="Sensor O2 #1"
    )

    relay_controller = RelayController(serial_manager)
    saturation_controller = SaturationController(relay_controller)

    # Configurar perfil de experimento
    perfiles = [
        {"target": 50.0, "duracion_s": 10},
        {"target": 75.0, "duracion_s": 10},
        {"target": 50.0, "duracion_s": 10},
    ]

    logger.info(f"Iniciando experimento con {len(perfiles)} perfiles")

    tiempo_inicio = time.time()
    perfil_actual = 0

    while perfil_actual < len(perfiles):
        perfil = perfiles[perfil_actual]
        tiempo_perfil = time.time() - tiempo_inicio

        # Cambiar objetivo cada ciclo
        if perfil_actual == 0 or tiempo_perfil > sum(p["duracion_s"] for p in perfiles[:perfil_actual]):
            saturation_controller.set_target_saturation(perfil["target"])
            logger.info(f"\n>>> Perfil {perfil_actual+1}: Target = {perfil['target']}%")
            perfil_actual += 1

        # Leer sensor (simulado)
        import random
        sat_actual = perfil["target"] + random.uniform(-5, 5)

        # Controlar
        control_state = saturation_controller.update(sat_actual)

        logger.info(f"Sat: {sat_actual:.1f}% | Acción: {control_state.action.name} | Estable: {control_state.is_stable}")

        time.sleep(0.5)

    logger.info("\nExperimento completado")
    serial_manager.disconnect()
    logger.info("Desconectado\n")


def main():
    """Menú principal"""
    print("\n=== Ejemplos de Uso - Aqua Control System ===\n")
    print("1. Lectura básica de sensores")
    print("2. Control de relés")
    print("3. Control de saturación")
    print("4. Publicación en AWS IoT Core")
    print("5. Experimento completo")
    print("0. Salir\n")

    choice = input("Seleccione un ejemplo (0-5): ").strip()

    try:
        if choice == "1":
            example_1_basic_sensor_reading()
        elif choice == "2":
            example_2_relay_control()
        elif choice == "3":
            example_3_saturation_control()
        elif choice == "4":
            example_4_aws_iot()
        elif choice == "5":
            example_5_full_experiment()
        elif choice == "0":
            logger.info("Saliendo...")
            return
        else:
            logger.error("Opción inválida")

    except KeyboardInterrupt:
        logger.info("\nInterrumpido por usuario")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
