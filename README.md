# Detector de Fatiga y Somnolencia

Sistema de vision artificial para la deteccion de signos tempranos de fatiga al volante, caida de parpados (microsueños), cabeceo y bostezos mediante camara web.

## Caracteristicas

- Malla facial de 478 puntos tridimensionales con MediaPipe Face Mesh.
- Calculo de EAR (Eye Aspect Ratio) en tiempo real para medicion de apertura de parpados y deteccion de ojos cerrados.
- Calculo de MAR (Mouth Aspect Ratio) para deteccion de bostezos sostenidos.
- Estimacion de angulos de cabeza (pitch/yaw) para cabeceo frontal o distracciones laterales.
- Alarma acustica integrada.
- Servidor web FastAPI con streaming de video y graficas en tiempo real.

## Requisitos

- Python 3.10 o 3.11
- Camara web USB
- Dependencias listadas en `requirements.txt`

## Instalacion

1. Clonar el repositorio:
```bash
git clone https://github.com/jotha04/Detector-Fatiga-Conduccion.git
cd Detector-Fatiga-Conduccion
```

2. Crear entorno virtual e instalar librerias:
```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion

### Modo rapido en macOS
Doble clic en `iniciar.command`. Inicia el servidor y abre Google Chrome maximizado con audio activo.

### Modo manual (macOS / Windows / Linux)
```bash
python web_app/server.py
```
Abrir en el navegador: `http://localhost:8000`

## Configuracion

Parametros ajustables en `web_app/config.yaml`:
- `FATIGUE_EAR_THRESHOLD`: Umbral de ojos cerrados (default: 0.22).
- `FATIGUE_EYE_CLOSED_CONSEC_FRAMES`: Cuadros consecutivos de ojos cerrados para disparar la alarma (default: 50 cuadros).
- `FATIGUE_MAR_THRESHOLD`: Umbral de apertura bucal para bostezo (default: 0.80).
- `FATIGUE_HEAD_PITCH_DOWN_THRESHOLD`: Grados de inclinacion hacia abajo para cabeceo (default: 32).
