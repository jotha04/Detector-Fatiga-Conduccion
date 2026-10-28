[Español](#español) | [English](#english)

---

<div id="español"></div>

# Detector de Fatiga y Somnolencia

Sistema de vision artificial para la deteccion en tiempo real de signos tempranos de fatiga al volante, caida de parpados (microsueños), cabeceo y bostezos mediante camara web.

## Caracteristicas

- Malla facial de 478 puntos tridimensionales con MediaPipe Face Mesh (compatible con lentes de montura normal).
- Calculo de EAR (Eye Aspect Ratio) en tiempo real para medicion de apertura de ojos y deteccion de microsueños.
- Calculo de MAR (Mouth Aspect Ratio) para deteccion de bostezos sostenidos.
- Estimacion de angulos de orientacion de la cabeza (pitch/yaw) para detectar cabeceo por sueño o distracciones laterales.
- Alarma acustica integrada.
- Servidor web FastAPI con streaming de video y graficas dinamicas en Chart.js local.

## Requisitos

- Python 3.10 o 3.11
- Camara web USB
- Dependencias indicadas en `requirements.txt`

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
- `FATIGUE_EYE_CLOSED_CONSEC_FRAMES`: Cuadros consecutivos de ojos cerrados para disparar la alarma (default: 50 cuadros, ~2.5s a 20 FPS).
- `FATIGUE_MAR_THRESHOLD`: Umbral de apertura de boca para bostezo (default: 0.80).
- `FATIGUE_HEAD_PITCH_DOWN_THRESHOLD`: Inclinacion hacia abajo para detectar cabeceo (default: 32 grados).

---

<div id="english"></div>

# Driver Fatigue and Drowsiness Detector

Real-time computer vision system designed to monitor and detect early signs of driver fatigue, eyelid closure (microsleep), head nodding, and yawning using a standard webcam.

## Features

- 478 3D facial landmarks powered by MediaPipe Face Mesh (resilient to standard prescription glasses).
- Real-time EAR (Eye Aspect Ratio) computation to monitor eye closure and trigger microsleep alerts.
- Real-time MAR (Mouth Aspect Ratio) computation to detect sustained yawning.
- Head pose estimation (pitch/yaw angles) to detect drowsiness nodding and side distractions.
- Built-in audible cabin alarm.
- FastAPI web server streaming live video and telemetry with local Chart.js visualizations.

## Requirements

- Python 3.10 or 3.11
- USB webcam
- Python dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jotha04/Detector-Fatiga-Conduccion.git
cd Detector-Fatiga-Conduccion
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

### Quick launch on macOS
Double-click `iniciar.command`. Automatically launches the background server and opens Google Chrome maximized with active audio.

### Manual launch (macOS / Windows / Linux)
```bash
python web_app/server.py
```
Open in your browser: `http://localhost:8000`

## Configuration

Thresholds can be adjusted via the web dashboard or inside `web_app/config.yaml`:
- `FATIGUE_EAR_THRESHOLD`: Eye closure threshold (default: 0.22).
- `FATIGUE_EYE_CLOSED_CONSEC_FRAMES`: Consecutive frames with closed eyes required to trigger the alarm (default: 50 frames, ~2.5s at 20 FPS).
- `FATIGUE_MAR_THRESHOLD`: Mouth openness threshold for yawning (default: 0.80).
- `FATIGUE_HEAD_PITCH_DOWN_THRESHOLD`: Downward tilt angle for nodding detection (default: 32 degrees).
