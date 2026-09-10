# Aqua Control System - Sistema de Control de O2 Disuelto para Acuicultura

Sistema modular, profesional y basado en IoT para monitoreo y control de oxígeno disuelto en sistemas de acuicultura.

## Visión General

Este sistema permite:

- **Monitoreo en tiempo real** de oxígeno disuelto en agua mediante 2 sensores RS485 Modbus RTU
- **Control automático** de inyección de gases mediante electroválvulas controladas por relés
- **Experimentos configurables** con perfiles de saturación personalizados (hasta 5 perfiles por experimento)
- **Almacenamiento local** de datos en CSV para análisis posterior
- **Publicación en AWS IoT Core** para monitoreo remoto y análisis en la nube
- **API REST** para integración con aplicaciones externas
- **Dashboard web** para visualización y control

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│               Raspberry Pi 4/5 (Orquestador)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Web API      │  │ Experiment   │  │ AWS IoT      │       │
│  │ (FastAPI)    │  │ Executor     │  │ Publisher    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                 │                   │              │
│         └─────────────────┼───────────────────┘              │
│                           ▼                                  │
│         ┌─────────────────────────────────────┐             │
│         │  Serial Manager & Protocol Handler  │             │
│         └─────────────────────────────────────┘             │
│                   │              │                           │
└───────────────────┼──────────────┼───────────────────────────┘
                    │              │
         ┌──────────▼─┐    ┌───────▼─────────┐
         │ESP32-S3    │    │ ESP32           │
         │Sensor      │    │ Relay Control   │
         │Reader      │    │                 │
         └──────────┬─┘    └────────┬────────┘
                    │               │
        ┌───────────┴─┐  ┌──────────┴─────────┐
        │ RS485 Mod   │  │ Relay Module #1    │
        ├─────────────┤  │ Relay Module #2    │
        │ O2 Sensor 1 │  └────────────────────┘
        │ O2 Sensor 2 │           │
        └─────────────┘           │
                            ┌─────┴─────┐
                            │ Válvula 1  │
                            │ Válvula 2  │
                            └────────────┘
```

## Requisitos del Sistema

### Hardware

- **Raspberry Pi**: 4 o 5 (recomendado 2GB RAM mínimo)
- **ESP32-S3**: Para lectura de sensores RS485
- **ESP32**: Para control de relés
- **Módulo RS485**: Para comunicación Modbus RTU con sensores
- **2x Módulos Relé**: Para control de electroválvulas
- **2x Sensores de O2 disuelto**: Modbus RTU, 9600 baud

### Software

- Python 3.9+
- pip (gestor de paquetes)
- PlatformIO (para compilar firmware ESP32)

## Instalación

### 1. Preparar Raspberry Pi

```bash
# Actualizar sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias
sudo apt-get install -y python3-dev python3-pip git
sudo pip3 install --upgrade pip

# Clonar repositorio
git clone <your-repo-url> ~/aqua-control-system
cd ~/aqua-control-system
```

### 2. Instalar dependencias Python

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar paquetes
pip install -r requirements.txt
```

### 3. Configurar Puertos Seriales

```bash
# Identificar puertos
ls -la /dev/ttyUSB*

# Dar permisos
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# (Reloguear para aplicar cambios)
```

### 4. Configurar Variables de Entorno

Crear `.env` en la raíz del proyecto:

```bash
# Serial Ports
ESP32_SENSOR_PORT=/dev/ttyUSB0
ESP32_RELAY_PORT=/dev/ttyUSB1
SERIAL_BAUDRATE=115200

# AWS IoT Core
AWS_IOT_ENDPOINT=<your-endpoint>.iot.us-east-1.amazonaws.com
AWS_IOT_THING_NAME=aqua-control-1
AWS_REGION=us-east-1

# Certificados (ver sección AWS IoT Setup)
AWS_CERT_PATH=./config/certs/certificate.pem.crt
AWS_KEY_PATH=./config/certs/private.pem.key
AWS_CA_PATH=./config/certs/AmazonRootCA1.pem

# API Web
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Logging
LOG_LEVEL=INFO
JSON_LOGS=False
```

### 5. Compilar y Subir Firmware ESP32

#### Para ESP32-S3 (Sensor Reader)

```bash
# Instalar PlatformIO
pip install platformio

# Compilar
cd firmware/esp32_s3_sensor_reader
pio run

# Subir (reemplazar puerto)
pio run -t upload --upload-port /dev/ttyUSB0
```

#### Para ESP32 (Relay Controller)

```bash
cd ../esp32_relay_controller
pio run
pio run -t upload --upload-port /dev/ttyUSB1
```

### 6. Configurar AWS IoT Core (Opcional)

```bash
# Crear carpeta de certificados
mkdir -p config/certs

# Descargar certificados de AWS IoT Console:
# 1. Device certificate (certificate.pem.crt)
# 2. Private key (private.pem.key)
# 3. CA certificate (AmazonRootCA1.pem)

# Copiar a config/certs/
cp ~/Downloads/*.pem config/certs/

# Establecer permisos
chmod 600 config/certs/*
```

## Uso

### Iniciar Sistema

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar aplicación
python3 src/main.py
```

El sistema iniciará:
- API REST en `http://localhost:8000`
- Lectura de sensores (cada 1 segundo)
- Publicación a AWS IoT Core (si está configurado)
- Dashboard web en `http://localhost:8000`

### API REST Endpoints

#### Salud del Sistema

```bash
curl http://localhost:8000/health
```

#### Obtener Lecturas Actuales

```bash
curl http://localhost:8000/api/sensors/current
```

#### Crear Experimento

```bash
curl -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Inyección de O2 Test",
    "description": "Prueba de control automático",
    "saturation_profiles": [
      {"target_saturation": 30, "duration_seconds": 600},
      {"target_saturation": 60, "duration_seconds": 600},
      {"target_saturation": 90, "duration_seconds": 600}
    ],
    "valve_1_enabled": true,
    "valve_2_enabled": false
  }'
```

#### Listar Experimentos

```bash
curl http://localhost:8000/api/experiments
```

#### Iniciar Experimento

```bash
curl -X POST http://localhost:8000/api/experiments/{experiment_id}/start
```

#### Obtener Datos

```bash
curl http://localhost:8000/api/data/latest
```

#### Descargar CSV

```bash
curl http://localhost:8000/api/data/download/{experiment_id} -o data.csv
```

## Estructura del Proyecto

```
aqua-control-system/
├── README.md
├── requirements.txt
├── setup.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py              # Configuración centralizada
│   └── certs/                   # Certificados AWS (gitignored)
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # Punto de entrada
│   │
│   ├── hardware/
│   │   ├── serial_manager.py    # Gestor de conexiones seriales
│   │   └── esp32_protocol.py    # Protocolo de comunicación
│   │
│   ├── sensors/
│   │   ├── dissolved_oxygen.py  # Driver de sensor O2 (Modbus)
│   │   └── calibration.py       # Gestión de calibración
│   │
│   ├── actuators/
│   │   └── relay_controller.py  # Controlador de relés
│   │
│   ├── experiments/
│   │   ├── saturation_controller.py  # Lógica de control PID
│   │   ├── experiment_executor.py    # Motor de ejecución
│   │   └── profiles/
│   │       └── saturation_profile.py # Perfiles de saturación
│   │
│   ├── data_management/
│   │   ├── csv_writer.py        # Almacenamiento local
│   │   └── database.py          # Metadatos (SQLite)
│   │
│   ├── cloud/
│   │   └── aws_iot_client.py    # Cliente AWS IoT Core
│   │
│   ├── interface/
│   │   └── web_api.py           # API REST (FastAPI)
│   │
│   └── utils/
│       ├── helpers.py
│       ├── validators.py
│       └── exceptions.py
│
├── firmware/
│   ├── esp32_s3_sensor_reader/
│   │   ├── main.cpp             # Firmware ESP32-S3
│   │   └── platformio.ini       # Configuración PlatformIO
│   │
│   └── esp32_relay_controller/
│       ├── main.cpp             # Firmware ESP32
│       └── platformio.ini
│
├── tests/
│   ├── test_sensors.py
│   ├── test_actuators.py
│   ├── test_experiments.py
│   └── test_api.py
│
├── data/
│   ├── experiments/             # Resultados de experimentos
│   ├── calibration/             # Datos de calibración
│   └── logs/                    # Logs del sistema
│
└── docker/
    ├── Dockerfile              # Para deployment en container
    └── docker-compose.yml
```

## Configuración Avanzada

### Compensación de Salinidad

El sistema implementa la ecuación de Weiss (1970) para compensar el efecto de la salinidad en la medición de O2:

```python
ln(DO) = A1 + A2(100/T) + A3*ln(T/100) + S(B1 + B2*T + B3*T²)
```

Donde:
- T: Temperatura en Kelvin
- S: Salinidad en PSU (Practical Salinity Units)
- Coeficientes de Weiss preestablecidos

Configurar en `config/settings.py`:

```python
class SensorConfig:
    WEISS_COEFFICIENTS = {
        "A1": -173.4292,
        "A2": 249.6339,
        "A3": 143.3483,
        # ...
    }
```

### Control de Saturación

Sistema de control con histéresis para evitar oscilaciones:

```python
Hysteresis Band = Target ± (Target × 5%)

IF current < lower_threshold:
    ACTIVATE valve (aumentar O2)
ELIF current > upper_threshold:
    DEACTIVATE valve (disminuir O2)
ELSE:
    HOLD (mantener)
```

Ajustar en `config/settings.py`:

```python
class ControlConfig:
    HYSTERESIS_PERCENT = 5.0  # ±5% del target
    STABILITY_WINDOW_SECONDS = 30.0
    STABILITY_THRESHOLD = 2.0  # % desviación máxima
```

### Publicación en AWS IoT Core

El sistema publica automáticamente:

- **Telemetría bruta** cada segundo a `aqua/sensor/{device_id}/telemetry`
- **Estado de experimentos** a `aqua/experiment/{id}/status`
- **Device Shadow** con estado reportado

Topics MQTT:

```
aqua/device/{thing_name}/telemetry
aqua/device/{thing_name}/commands
aqua/device/{thing_name}/status
$aws/things/{thing_name}/shadow/update
```

## Troubleshooting

### Conexión serial fallida

```bash
# Verificar puertos disponibles
ls -la /dev/ttyUSB*

# Comprobar permisos
groups $USER  # Debe incluir 'dialout' y 'tty'

# Resetear permisos
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER
```

### Sensor no responde

```bash
# Comprobar comunicación Modbus
python3 -c "
from src.hardware.serial_manager import SerialManager
sm = SerialManager('/dev/ttyUSB0', '/dev/ttyUSB1')
sm.connect()
print('Dispositivos:', sm.get_connected_devices())
"

# Ver logs
tail -f logs/aqua_system.log
```

### AWS IoT no conecta

```bash
# Verificar certificados
ls -la config/certs/

# Probar conectividad
openssl s_client -connect <endpoint>:8883 \
  -cert config/certs/certificate.pem.crt \
  -key config/certs/private.pem.key \
  -CAfile config/certs/AmazonRootCA1.pem
```

## Logging

Los logs se guardan en `logs/aqua_system.log`:

```bash
# Ver últimos logs
tail -100 logs/aqua_system.log

# Filtrar por nivel
grep "ERROR" logs/aqua_system.log

# Seguir en tiempo real
tail -f logs/aqua_system.log
```

## Deployment en Producción

### Como Servicio Systemd

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/aqua-control.service

[Unit]
Description=Aqua Control System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/aqua-control-system
Environment="PATH=/home/pi/aqua-control-system/venv/bin"
ExecStart=/home/pi/aqua-control-system/venv/bin/python3 src/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# Habilitar y comenzar
sudo systemctl enable aqua-control
sudo systemctl start aqua-control

# Ver estado
sudo systemctl status aqua-control
```

### Con Docker

```bash
# Compilar imagen
docker-compose build

# Ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## Mejoras Futuras

- [ ] Dashboard web mejorado con gráficos en tiempo real
- [ ] Controlador PID adaptativo en lugar de histéresis
- [ ] Sincronización de experimentos entre múltiples dispositivos
- [ ] ML para predicción y optimización de control
- [ ] Alertas y notificaciones por anomalías
- [ ] Calibración remota vía AWS IoT
- [ ] Sincronización con Grafana para visualización

## Licencia

MIT

## Soporte

Para preguntas o problemas, contactar a: s.messina@bluemetricsiot.com

---

**Última actualización:** Septiembre 2026  
**Versión:** 1.0.0
