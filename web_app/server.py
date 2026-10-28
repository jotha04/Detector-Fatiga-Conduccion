import os
import sys
os.environ["OPENCV_AVFOUNDATION_SKIP_AUTH"] = "1"

import cv2
import time
import yaml
import asyncio
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import imutils
import uvicorn
import os
import sys

# Ensure we can import from the parent edge directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fatigue_analyzer import FatigueAnalyzer
from better_detector import MediaPipeDetector

app = FastAPI()

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(static_dir, "favicon.ico"))

# Global variables for shared state
class AppState:
    def __init__(self):
        self.frame = None
        self.frame_id = 0
        self.analyzer = None  # Referencia al analyzer para cambiar umbrales en vivo
        self.metrics = {
            "ear": 0.0,
            "mar": 0.0,
            "head_pitch": 0.0,
            "fatigueLevel": "NONE",
            "fatigueType": "NONE",
            "fps_real": 0.0,
            "camera_status": "Desconectada",
            "threshold_ear": 0.22,
            "threshold_mar": 0.80,
        }
        self.active_clients = []
        
state = AppState()

@app.post("/set_threshold")
async def set_threshold(data: dict = None):
    """Endpoint para cambiar el umbral EAR desde el slider del frontend."""
    if data and "threshold" in data:
        new_val = float(data["threshold"])
        new_val = max(0.10, min(0.30, new_val))  # Limitar rango
        state.metrics["threshold_ear"] = new_val
        if state.analyzer:
            state.analyzer.EAR_THRESHOLD = new_val
        return {"ok": True, "threshold": new_val}
    return {"ok": False}

def run_camera():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    config_path = os.path.join(current_dir, "config.yaml")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Defaults and limits
    config.setdefault('fps', 30)
    config.setdefault('FATIGUE_EAR_THRESHOLD', 0.20)
    config.setdefault('FATIGUE_EYE_CLOSED_CONSEC_FRAMES', 40)
    config['shape_predictor_path'] = os.path.join(base_dir, config.get('shape_predictor_path', 'models/shape_predictor_68_face_landmarks.dat'))
    
    state.metrics['threshold_ear'] = config['FATIGUE_EAR_THRESHOLD']
    state.metrics['threshold_mar'] = config.get('FATIGUE_MAR_THRESHOLD', 0.80)
    
    # Usar MediaPipe Face Mesh - funciona con gafas y es ultra estable
    detector = MediaPipeDetector(config)
    analyzer = FatigueAnalyzer(config)
    state.analyzer = analyzer  # Guardar referencia para el slider
    
    print("[INFO] Iniciando el flujo de video con cámara nativa panorámica 16:9...")
    target_width = config.get('frame_width', 960)
    
    cap = cv2.VideoCapture(config.get('camera_index', 0))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    time.sleep(0.5) # Warm up
    state.metrics["camera_status"] = "Conectada"
    
    jpeg_params = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
    
    fps_calc_start = time.time()
    fps_frame_count = 0
    fps_updated = False
    
    while True:
        ret, raw_frame = cap.read()
        if not ret or raw_frame is None:
            time.sleep(0.01)
            continue
            
        if raw_frame.shape[1] > target_width:
            processed_frame = imutils.resize(raw_frame, width=target_width)
        else:
            processed_frame = raw_frame
            
        fps_frame_count += 1
        elapsed = time.time() - fps_calc_start
        if elapsed >= 1.0:
            current_fps = max(1, int(round(fps_frame_count / elapsed)))
            state.metrics["fps_real"] = current_fps
            fps_frame_count = 0
            fps_calc_start = time.time()
            if not fps_updated:
                try:
                    scale = current_fps / float(config.get('fps', current_fps))
                    analyzer.FPS = current_fps
                    analyzer.EYE_CLOSED_CONSEC_FRAMES = max(1, int(round(analyzer.EYE_CLOSED_CONSEC_FRAMES * scale)))
                    analyzer.HEAD_NOD_CONSEC_FRAMES = max(1, int(round(analyzer.HEAD_NOD_CONSEC_FRAMES * scale)))
                    analyzer.YAWN_CONSEC_FRAMES = max(1, int(round(analyzer.YAWN_CONSEC_FRAMES * scale)))
                except Exception:
                    pass
                fps_updated = True
        
        # Procesar métricas en tiempo real
        display_frame, raw_metrics = detector.process_frame(processed_frame)
        
        if raw_metrics:
            analysis_payload = analyzer.analyze(raw_metrics)
            
            # Update shared state
            state.metrics.update({
                "ear": round(raw_metrics.get("ear", 0.0), 3),
                "mar": round(raw_metrics.get("mar", 0.0), 3),
                "head_pitch": round(raw_metrics.get("head_pitch", 0.0), 1),
                "fatigueLevel": analysis_payload.get("fatigueLevel", "NINGUNO"),
                "fatigueType": analysis_payload.get("fatigueType", "NINGUNO"),
                "camera_status": "Rostro Detectado"
            })
            
            # Dibujar en el frame para el stream
            if raw_metrics['face_landmarks'] is not None:
                for (x, y) in raw_metrics['face_landmarks']:
                    cv2.circle(display_frame, (x, y), 2, (0, 255, 255), -1)
                    
            if state.metrics["fatigueLevel"] == "ALTO" or state.metrics["fatigueLevel"] == "HIGH":
                cv2.putText(display_frame, "ALERTA FATIGA", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        else:
            # NO hay rostro detectado: reiniciar contadores y apagar alarma inmediatamente
            analyzer.reset()
            state.metrics.update({
                "ear": 0.0,
                "mar": 0.0,
                "head_pitch": 0.0,
                "fatigueLevel": "NINGUNO",
                "fatigueType": "NINGUNO",
                "camera_status": "Buscando rostro..."
            })
            cv2.putText(display_frame, "BUSCANDO CONDUCTOR...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                
        # Encode to JPEG optimizado (calidad 75 = encode de 3ms)
        ret, buffer = cv2.imencode('.jpg', display_frame, jpeg_params)
        if ret:
            state.frame = buffer.tobytes()
            state.frame_id += 1

@app.on_event("startup")
async def startup_event():
    import threading
    t = threading.Thread(target=run_camera, daemon=True)
    t.start()

async def generate_frames():
    last_id = -1
    while True:
        if state.frame is not None and state.frame_id != last_id:
            last_id = state.frame_id
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + state.frame + b'\r\n')
        await asyncio.sleep(0.005) # Check rápido de 5ms sin encolar buffers ni crear lag

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.active_clients.append(websocket)
    try:
        while True:
            await websocket.send_json(state.metrics)
            await asyncio.sleep(0.1) # 10Hz telemetry
    except WebSocketDisconnect:
        state.active_clients.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
