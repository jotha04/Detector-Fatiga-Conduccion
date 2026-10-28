# Sistema de Detección de Fatiga y Somnolencia (Cabina & Conductor)

Sistema integral de visión por computador y telemetría en tiempo real para la detección temprana de signos de fatiga, somnolencia (caída de párpados / EAR), cabeceo y bostezos en conductores.

Diseñado para operar 100% offline en cabina o estaciones de monitoreo, con visualización Web App interactiva y alertas sonoras instantáneas.

---

## 🎯 Características Principales

1. **Detección Facial de Alta Precisión (MediaPipe Mesh):**
   * Rastreo de 478 puntos faciales tridimensionales.
   * Tolerante al uso de gafas de montura tradicional y variaciones de iluminación.
2. **Métricas Biomecánicas Continuas:**
   * **EAR (Eye Aspect Ratio):** Monitoreo continuo de apertura ocular y detección de microsueños.
   * **MAR (Mouth Aspect Ratio):** Detección de patrones de bostezo sostenido.
   * **Pose de Cabeza (Pitch / Yaw):** Detección de cabeceo por sueño o distracciones laterales prolongadas.
3. **Servidor Web Ultraligero (FastAPI + WebSockets):**
   * Streaming de video MJPEG de baja latencia.
   * Transmisión de telemetría por WebSocket al panel gráfico en el navegador.
4. **Alertas Acústicas y Visuales Autónomas:**
   * Alarma sonora inmediata en cabina ante eventos críticos.
   * Panel visual con gráficas dinámicas (Chart.js local) y controles de umbral en tiempo real.

---

## 📁 Estructura del Repositorio

```text
detector_sanchez_polo/
├── iniciar.command             # 🚀 Lanzador automático para macOS (servidor + Chrome)
├── requirements.txt            # Dependencias de Python
├── README.md                   # Documentación del proyecto
├── LEEME.txt                   # Resumen rápido de operación
├── scripts/
│   └── simulate_click.py       # Simulación de interacción física para desbloquear audio en navegador
├── src/
│   ├── __init__.py
│   └── fatigue_analyzer.py     # Lógica matemática de EAR, MAR, cabeceo y persistencia de eventos
└── web_app/
    ├── server.py               # Servidor FastAPI y WebSocket
    ├── better_detector.py      # Detector facial MediaPipe (478 landmarks)
    ├── config.yaml             # Configuración de umbrales, cámara y backend
    ├── face_landmarker.task    # Modelo binario de MediaPipe Face Landmarker
    └── static/                 # Frontend 100% offline (HTML, CSS, JS, Chart.js, audio, fuentes)
```

---

## 🛠️ Instalación y Requisitos

### Requisitos Previos
* **Python 3.10 o 3.11**
* Cámara web USB o cámara integrada
* Navegador moderno (Google Chrome recomendado)

### Paso 1: Clonar o Descargar el Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd detector_sanchez_polo
```

### Paso 2: Crear el Entorno Virtual
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Paso 3: Instalar Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Ejecución del Sistema

### Opción A (macOS con un solo clic):
Haz doble clic sobre el archivo `iniciar.command`.  
*Iniciará el servidor en segundo plano y abrirá Google Chrome maximizado en `http://localhost:8000` con el audio activo.*

### Opción B (Desde la Terminal en macOS / Linux / Windows):
```bash
# Activar entorno virtual
source .venv/bin/activate  # o .venv\Scripts\activate en Windows

# Iniciar servidor
python web_app/server.py
```
Abre tu navegador en: **`http://localhost:8000`**

---

## ⚙️ Configuración y Calibración

Los umbrales se pueden ajustar en caliente desde la interfaz web o editando [`web_app/config.yaml`](file:///web_app/config.yaml):

* **`FATIGUE_EAR_THRESHOLD`** (por defecto `0.22`): Umbral de apertura de ojos. Si el EAR cae por debajo durante `FATIGUE_EYE_CLOSED_CONSEC_FRAMES`, se dispara la alarma de microsueño.
* **`FATIGUE_HEAD_PITCH_DOWN_THRESHOLD`** (por defecto `32`): Inclinación de la cabeza hacia abajo (grados).
* **`FATIGUE_MAR_THRESHOLD`** (por defecto `0.80`): Umbral de apertura bucal para detección de bostezo.
