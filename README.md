# Sistema de Detección de Fatiga, Caída de Párpados y Somnolencia para Conductores

Plataforma inteligente de visión artificial y telemetría biomécanica en tiempo real diseñada para la **detección temprana y no invasiva de fatiga, somnolencia (caída de párpados / microsueños), cabeceo y bostezos en cabinas de transporte**.

El sistema opera de forma 100% offline, procesando video localmente mediante redes neuronales de malla facial (**MediaPipe Face Mesh**) e integrando un panel de visualización web interactivo con alertas sonoras inmediatas en cabina.

---

## 🎯 ¿Para qué sirve el Sistema?

El cansancio al volante y los microsueños son responsables de un alto porcentaje de siniestros viales en transporte de carga y pasajeros. Este sistema actúa como un copiloto digital de seguridad activa:

1. **Detección Continua de Caída de Párpados (EAR):**
   * Calcula cuadro a cuadro el índice **EAR (*Eye Aspect Ratio*)** a partir de las coordenadas euclidianas de los párpados.
   * Si el conductor cierra los ojos o pestañea con lentitud anormal durante más de un umbral temporal configurable (e.g. 2.5 segundos consecutivos), el sistema activa de inmediato la **alarma acústica de cabina**.
2. **Detección de Bostezos Sostenidos (MAR):**
   * Mide la apertura vertical y horizontal de los labios mediante el índice **MAR (*Mouth Aspect Ratio*)**, diferenciando entre el habla normal y un bostezo prolongado (>0.9 segundos).
3. **Análisis de Cabeceo y Distracción (Pose 3D):**
   * Estima los ángulos de orientación de la cabeza (**Pitch** para inclinación vertical / cabeceo por sueño, y **Yaw** para giros laterales de distracción).
4. **Tolerancia a Lentes y Condiciones de Cabina:**
   * Al utilizar la malla densa de 478 puntos de MediaPipe, el modelo mantiene el rastreo de ojos incluso con gafas de montura tradicional y variaciones de iluminación.
5. **Streaming Web de Baja Latencia y Telemetría:**
   * Servidor integrado FastAPI + WebSockets que transmite video fluido en tiempo real y actualiza gráficas dinámicas de fatiga en el navegador mediante Chart.js local.

---

## 📁 Estructura del Repositorio

```text
detector_sanchez_polo/
├── iniciar.command             # 🚀 Lanzador automático para macOS (inicia servidor y abre Chrome)
├── requirements.txt            # Dependencias de Python
├── README.md                   # Documentación técnica completa
├── LEEME.txt                   # Resumen rápido de operación
├── scripts/
│   └── simulate_click.py       # Desbloqueador automático de audio en el navegador
├── src/
│   ├── __init__.py
│   └── fatigue_analyzer.py     # Algoritmos matemáticos de EAR, MAR, cabeceo y persistencia de eventos
└── web_app/
    ├── server.py               # Servidor FastAPI y WebSocket de telemetría y streaming MJPEG
    ├── better_detector.py      # Detector facial MediaPipe (478 puntos tridimensionales)
    ├── config.yaml             # Configuración central de umbrales, cámara y alertas
    ├── face_landmarker.task    # Modelo neuronal MediaPipe Face Landmarker
    └── static/                 # Panel web 100% offline (HTML5, CSS3, JS, Chart.js, audio WAV, fuentes)
        ├── chart.js
        ├── index.html
        ├── music.wav           # Alarma acústica de advertencia
        ├── script.js
        ├── style.css
        └── sanches_left.mov    # Video demostrativo lateral en loop
```

---

## 💻 Requisitos del Sistema

* **Sistemas Operativos:** macOS (Apple Silicon M1/M2/Intel), Windows 10/11 (x64) o Linux.
* **Hardware:**
  * Cámara web USB o cámara integrada (apuntando al rostro del conductor).
  * Altavoces o salida de audio habilitada para la alarma.
* **Software:**
  * **Python 3.10 o 3.11**.
  * Navegador moderno (Google Chrome recomendado para el modo kiosco y audio automático).

---

## 🛠️ Instalación Paso a Paso

### 1. Clonar el Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd detector_sanchez_polo
```

### 2. Configurar el Entorno Virtual
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Instalar Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Cómo Correr el Programa

### Opción 1 (macOS - Doble Clic):
Haz doble clic sobre el archivo:
```text
iniciar.command
```
*Iniciará automáticamente el servidor en segundo plano, abrirá Google Chrome a pantalla completa en `http://localhost:8000` y desbloqueará el audio de alerta de inmediato.*

### Opción 2 (Desde la Terminal en Windows / Linux / macOS):
```bash
# Con el entorno virtual activado:
python web_app/server.py
```
Abre tu navegador web en: **`http://localhost:8000`**

---

## ⚙️ Calibración y Ajuste de Umbrales

Todos los parámetros pueden ajustarse tanto desde los deslizadores interactivos en el panel web como editando [`web_app/config.yaml`](file:///web_app/config.yaml):

* **`FATIGUE_EAR_THRESHOLD`** (por defecto `0.22`): Umbral de apertura de ojos. Valores menores a 0.22 indican ojos cerrados.
* **`FATIGUE_EYE_CLOSED_CONSEC_FRAMES`** (por defecto `50` frames $\approx 2.5$ s a 20 FPS): Tiempo continuo con ojos cerrados requerido para disparar la alarma (evita falsos positivos por parpadeo natural).
* **`FATIGUE_MAR_THRESHOLD`** (por defecto `0.80`): Umbral de apertura de boca para detectar bostezo sostenido.
* **`FATIGUE_HEAD_PITCH_DOWN_THRESHOLD`** (por defecto `32` grados): Inclinación hacia abajo para detectar cabeceo por pérdida de consciencia.
