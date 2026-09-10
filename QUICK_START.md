# Guía Rápida - Aqua Control System

## Instalación Express (10 minutos)

### 1. Clonar y preparar

```bash
cd ~
git clone <repo-url> aqua-control-system
cd aqua-control-system

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Identificar puertos seriales

```bash
# Ver dispositivos conectados
ls -la /dev/ttyUSB*

# Típicamente:
# /dev/ttyUSB0 → ESP32-S3 (sensores)
# /dev/ttyUSB1 → ESP32 (relés)
```

### 3. Crear archivo .env

```bash
cat > .env << 'EOF'
ESP32_SENSOR_PORT=/dev/ttyUSB0
ESP32_RELAY_PORT=/dev/ttyUSB1
SERIAL_BAUDRATE=115200
API_PORT=8000
DEBUG=False
LOG_LEVEL=INFO
EOF
```

### 4. Probar instalación

```bash
# Ejecutar ejemplo interactivo
python3 example_usage.py

# Seleccionar opción 1 (Lectura básica de sensores)
# Si todo funciona, deberías ver las lecturas de los sensores
```

### 5. Iniciar sistema completo

```bash
# Terminal 1: Ejecutar servidor
python3 src/main.py

# Terminal 2: Probar API
curl http://localhost:8000/health
```

## Uso Rápido

### Crear experimento

```bash
curl -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi primer experimento",
    "saturation_profiles": [
      {"target_saturation": 50, "duration_seconds": 600},
      {"target_saturation": 75, "duration_seconds": 600}
    ],
    "valve_1_enabled": true,
    "valve_2_enabled": false
  }' | jq
```

### Iniciar experimento

```bash
# Copiar el experiment_id del resultado anterior
curl -X POST http://localhost:8000/api/experiments/{experiment_id}/start
```

### Monitorear en tiempo real

```bash
# Ver lecturas actuales
curl http://localhost:8000/api/sensors/current | jq

# Ver estado del control
curl http://localhost:8000/api/control/status | jq

# Ver progreso del experimento
curl http://localhost:8000/api/experiments/{experiment_id} | jq
```

### Descargar datos

```bash
curl http://localhost:8000/api/data/download/{experiment_id} -o mi_experimento.csv
```

## Firmware ESP32

### Flash del firmware

```bash
# Instalar herramientas
pip install platformio

# ESP32-S3 (sensores)
cd firmware/esp32_s3_sensor_reader
pio run -t upload --upload-port /dev/ttyUSB0

# ESP32 (relés)
cd ../esp32_relay_controller
pio run -t upload --upload-port /dev/ttyUSB1
```

### Verificar conexión

```bash
# Monitor serial (ESP32-S3)
pio device monitor -p /dev/ttyUSB0 -b 115200

# Deberías ver:
# [ESP32-S3] Sistema de lectura de sensores O2 iniciado
```

## Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| **No reconoce puertos USB** | `sudo usermod -a -G dialout $USER` (reloguear) |
| **Error "Permission denied"** | `sudo chmod 666 /dev/ttyUSB*` |
| **Sensor no responde** | Verificar voltaje RS485, revisar conexiones |
| **API no inicia** | Cambiar puerto: `API_PORT=8001` en .env |
| **Certificados AWS no encontrados** | Copiar a `config/certs/` y revisar permisos |

## Estructura Mínima del Proyecto

```
aqua-control-system/
├── .env                          # ← Crear este archivo
├── config/
│   ├── settings.py              # Editar puertos aquí
│   └── certs/                   # ← Poner certificados AWS aquí
├── src/
│   ├── main.py                  # ← Ejecutar esto
│   ├── hardware/
│   ├── sensors/
│   ├── actuators/
│   ├── experiments/
│   ├── cloud/
│   └── interface/
├── firmware/                     # Subir a ESP32
│   ├── esp32_s3_sensor_reader/
│   └── esp32_relay_controller/
├── data/                         # ← Se crea automáticamente
│   ├── experiments/
│   └── logs/
└── example_usage.py             # ← Para probar
```

## Próximos Pasos

1. **Configurar AWS IoT** (opcional)
   - Crear device en AWS IoT Console
   - Copiar certificados a `config/certs/`
   - Editar `AWS_IOT_ENDPOINT` en `.env`

2. **Calibrar sensores**
   ```bash
   python3 -c "
   from src.sensors.dissolved_oxygen import DissolvedOxygenSensor
   # Implementar rutina de calibración
   "
   ```

3. **Crear dashboard web**
   - Ver `src/interface/web_api.py`
   - Agregar rutas de visualización

4. **Deployment en producción**
   - Ver sección "Deployment" en README.md
   - Configurar como servicio systemd

## Cheatsheet de Comandos API

```bash
# Health check
curl http://localhost:8000/health

# Sensores
curl http://localhost:8000/api/sensors/current
curl http://localhost:8000/api/sensors/status

# Experimentos
curl http://localhost:8000/api/experiments                              # Listar
curl -X POST http://localhost:8000/api/experiments -d {...}           # Crear
curl http://localhost:8000/api/experiments/{id}                        # Obtener
curl -X POST http://localhost:8000/api/experiments/{id}/start          # Iniciar
curl -X POST http://localhost:8000/api/experiments/{id}/stop           # Parar

# Datos
curl http://localhost:8000/api/data/latest
curl http://localhost:8000/api/data/download/{id} -o data.csv

# Sistema
curl http://localhost:8000/api/system/status
```

## Logs

```bash
# Ver en tiempo real
tail -f logs/aqua_system.log

# Últimas 100 líneas
tail -100 logs/aqua_system.log

# Filtrar errores
grep ERROR logs/aqua_system.log
```

---

**¿Problemas?** Revisar `logs/aqua_system.log` y la sección Troubleshooting en README.md
