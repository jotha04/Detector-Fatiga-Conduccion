import time
from datetime import datetime, timezone
import collections

class FatigueAnalyzer:
    """
    Analiza las métricas faciales a lo largo del tiempo para determinar el nivel y tipo de fatiga.
    Mantiene un estado interno para evitar falsas alarmas y proporcionar un análisis robusto.
    """

    def __init__(self, config, driver_id="DEFAULT_DRIVER", vehicle_id="DEFAULT_VEHICLE"):
        self.config = config
        self.driver_id = driver_id
        self.vehicle_id = vehicle_id

        # --- Umbrales de Configuración ---
        self.EAR_THRESHOLD = config['FATIGUE_EAR_THRESHOLD']
        self.MAR_THRESHOLD = config['FATIGUE_MAR_THRESHOLD']
        self.EYE_CLOSED_CONSEC_FRAMES = config['FATIGUE_EYE_CLOSED_CONSEC_FRAMES']
        self.HEAD_NOD_CONSEC_FRAMES = config['FATIGUE_HEAD_NOD_CONSEC_FRAMES']
        self.YAWN_CONSEC_FRAMES = config['FATIGUE_YAWN_CONSEC_FRAMES']
        self.HEAD_PITCH_DOWN_THRESHOLD = config['FATIGUE_HEAD_PITCH_DOWN_THRESHOLD']
        self.HEAD_YAW_THRESHOLD = config['FATIGUE_HEAD_YAW_THRESHOLD']
        self.HEAD_YAW_CONSEC_FRAMES = config['FATIGUE_HEAD_YAW_CONSEC_FRAMES']
        self.FPS = config['fps'] # Frames per second from config
        self.HEAD_NOD_REQUIRE_EYES_CLOSED = config.get('head_nod_require_eyes_closed', True)
        self.HEAD_NOD_IGNORE_IF_YAWN = config.get('head_nod_ignore_if_yawn', True)
        self.IGNORE_YAWN_IF_HEAD_DOWN = config.get('IGNORE_YAWN_IF_HEAD_DOWN', True) # Nuevo

        # --- Contadores de Estado Interno ---
        self._eye_closed_frames = 0
        self._yawn_frames = 0
        self._head_nod_frames = 0
        self._head_down_with_eyes_closed_frames = 0
        self._head_yaw_frames = 0

        # --- Métricas de Parpadeo ---
        self._is_blinking = False
        self._blink_start_time = 0
        self._blink_timestamps = collections.deque(maxlen=self.FPS * 60 * 2) # Almacenar hasta 2 minutos de parpadeos
        self.blink_rate = 0.0
        self.avg_blink_duration = 0.0

        # --- Métricas de Bostezo ---
        self._yawn_timestamps = collections.deque(maxlen=self.FPS * 60 * 2) # Almacenar hasta 2 minutos de bostezos
        self.yawn_count = 0

        # --- Historial para suavizado (media móvil) ---
        self._ear_history = collections.deque(maxlen=5)
        self._mar_history = collections.deque(maxlen=5)
        self._pitch_history = collections.deque(maxlen=5)
        self._yaw_history = collections.deque(maxlen=5)

        # --- Métricas de Fatiga Derivadas ---
        self.eye_closure_duration = 0.0 # Duración del cierre de ojos actual
        self.fatigue_level = "NONE"
        self.fatigue_type = "NONE"

    def reset(self):
        """Reinicia contadores inmediatos cuando no hay conductor o rostro visible."""
        self._eye_closed_frames = 0
        self._yawn_frames = 0
        self._head_nod_frames = 0
        self._head_down_with_eyes_closed_frames = 0
        self._head_yaw_frames = 0
        self._is_blinking = False
        self.eye_closure_duration = 0.0
        self.fatigue_level = "NONE"
        self.fatigue_type = "NONE"
        self._ear_history.clear()
        self._mar_history.clear()
        self._pitch_history.clear()
        self._yaw_history.clear()

    def _avg(self, seq):
        return (sum(seq) / len(seq)) if seq else 0.0

    def _update_blink_metrics(self, ear):
        current_time = time.time()
        
        # Detección de parpadeo completo (cierre y apertura)
        if ear < self.EAR_THRESHOLD:
            if not self._is_blinking:
                self._is_blinking = True
                self._blink_start_time = current_time
        elif self._is_blinking:
            self._is_blinking = False
            blink_duration = current_time - self._blink_start_time
            self._blink_timestamps.append((current_time, blink_duration))

        # Calcular tasa de parpadeo (parpadeos por minuto)
        one_minute_ago = current_time - 60
        while self._blink_timestamps and self._blink_timestamps[0][0] < one_minute_ago:
            self._blink_timestamps.popleft()
        self.blink_rate = len(self._blink_timestamps)

        # Calcular duración promedio de parpadeo
        if self._blink_timestamps:
            self.avg_blink_duration = sum([d for _, d in self._blink_timestamps]) / len(self._blink_timestamps) * 1000 # en ms
        else:
            self.avg_blink_duration = 0.0

    def _update_yawn_metrics(self, mar, head_pitch_eff):
        current_time = time.time()

        # Nuevo: Ignorar bostezo si la cabeza está agachada y la configuración lo permite
        if self.IGNORE_YAWN_IF_HEAD_DOWN and head_pitch_eff < -self.HEAD_PITCH_DOWN_THRESHOLD:
            self._yawn_frames = 0 # Resetear el contador de bostezo
            return # Salir sin procesar el bostezo

        if mar > self.MAR_THRESHOLD:
            self._yawn_frames += 1
        else:
            if self._yawn_frames >= self.YAWN_CONSEC_FRAMES:
                # Se detectó un bostezo sostenido
                self._yawn_timestamps.append(current_time)
            self._yawn_frames = 0
        
        # Contar bostezos en el último minuto
        one_minute_ago = current_time - 60
        while self._yawn_timestamps and self._yawn_timestamps[0] < one_minute_ago:
            self._yawn_timestamps.popleft()
        self.yawn_count = len(self._yawn_timestamps)

    def analyze(self, metrics):
        """
        Analiza las métricas crudas y actualiza el estado de fatiga.
        
        Args:
            metrics (dict): Diccionario de métricas crudas de DrowsinessDetector.
        
        Returns:
            dict: Diccionario con el análisis de fatiga simplificado para el backend.
        """
        ear = metrics.get("ear", 0.0)
        mar = metrics.get("mar", 0.0)
        head_pitch = metrics.get("head_pitch", 0.0)
        head_yaw = metrics.get("head_yaw", 0.0) # Nuevo: Recuperar head_yaw

        # Actualizar históricos para suavizado
        if ear > 0:
            self._ear_history.append(ear)
        if mar > 0:
            self._mar_history.append(mar)
        self._pitch_history.append(head_pitch)
        self._yaw_history.append(head_yaw) # Nuevo: Actualizar historial de yaw

        ear_eff = self._avg(self._ear_history) if self._ear_history else ear
        mar_eff = self._avg(self._mar_history) if self._mar_history else mar
        head_pitch_eff = self._avg(self._pitch_history) if self._pitch_history else head_pitch
        head_yaw_eff = self._avg(self._yaw_history) if self._yaw_history else head_yaw # Nuevo: yaw efectivo

        self._update_blink_metrics(ear_eff)
        self._update_yawn_metrics(mar_eff, head_pitch_eff)

        # --- Lógica de Detección de Microsueño (Ojos Cerrados) ---
        if ear_eff < self.EAR_THRESHOLD:
            self._eye_closed_frames += 1
            self.eye_closure_duration = self._eye_closed_frames / self.FPS
        else:
            self._eye_closed_frames = 0
            self.eye_closure_duration = 0.0

        # --- Lógica de Detección de Cabeceo por Somnolencia ---
        # Cabeza hacia abajo suele ser pitch negativo; usar valor absoluto configurable si tu sensor invierte ejes.
        if head_pitch_eff < -self.HEAD_PITCH_DOWN_THRESHOLD:
            self._head_nod_frames += 1
            if ear_eff < self.EAR_THRESHOLD:
                # Evitar contar cabeceo si hay un bostezo (boca ampliamente abierta)
                if self.HEAD_NOD_IGNORE_IF_YAWN and mar_eff > self.MAR_THRESHOLD:
                    self._head_down_with_eyes_closed_frames = 0
                else:
                    self._head_down_with_eyes_closed_frames += 1
            else:
                self._head_down_with_eyes_closed_frames = 0
        else:
            self._head_nod_frames = 0
            self._head_down_with_eyes_closed_frames = 0

        # --- Lógica de Detección de Distracción (Giro de Cabeza Lateral) ---
        if abs(head_yaw_eff) > self.HEAD_YAW_THRESHOLD:
            self._head_yaw_frames += 1
        else:
            self._head_yaw_frames = 0

        # --- Determinación del Nivel y Tipo de Fatiga ---
        self.fatigue_level = "NONE"
        self.fatigue_type = "NONE"

        if self.eye_closure_duration >= (self.EYE_CLOSED_CONSEC_FRAMES / self.FPS):
            self.fatigue_level = "HIGH"
            self.fatigue_type = "MICRO_SLEEP"
        elif (self._head_down_with_eyes_closed_frames >= self.HEAD_NOD_CONSEC_FRAMES) if self.HEAD_NOD_REQUIRE_EYES_CLOSED else (self._head_nod_frames >= self.HEAD_NOD_CONSEC_FRAMES):
            self.fatigue_level = "HIGH"
            self.fatigue_type = "HEAD_NOD"
        elif self._head_yaw_frames >= self.HEAD_YAW_CONSEC_FRAMES: # Nuevo: Detección de distracción por giro de cabeza
            # Cambiado: ahora se considera como cansancio visual en lugar de distracción
            self.fatigue_level = "LOW"
            self.fatigue_type = "EYE_STRAIN"
        elif self.yawn_count >= 3: # Más de 3 bostezos en el último minuto
            self.fatigue_level = "MEDIUM"
            self.fatigue_type = "YAWNING"
        elif self.blink_rate >= 30 or self.blink_rate <= 5: # Tasa de parpadeo anormal
            self.fatigue_level = "LOW"
            self.fatigue_type = "EYE_STRAIN"

        # --- Construcción del Payload Simplificado ---
        level_map = {
            "NONE": "NINGUNO",
            "LOW": "BAJO",
            "MEDIUM": "MEDIO",
            "HIGH": "ALTO"
        }
        type_map = {
            "NONE": "NINGUNO",
            "MICRO_SLEEP": "MICROSUEÑO",
            "HEAD_NOD": "CABECEO",
            "YAWNING": "BOSTEZO",
            "EYE_STRAIN": "CANSANCIO_VISUAL"
        }
        level_es = level_map.get(self.fatigue_level, self.fatigue_level)
        type_es = type_map.get(self.fatigue_type, self.fatigue_type)

        final_payload = {
            "driverId": self.driver_id,
            "vehicleId": self.vehicle_id,
            "timestamp": datetime.now( timezone.utc).isoformat(),
            "fatigueLevel": level_es,        # ahora en español
            "fatigueType": type_es,          # ahora en español
            "eyeClosureDuration": round(self.eye_closure_duration, 2),
            "yawnCount": self.yawn_count, # el número de bostezos
            "blinkRate": round(self.blink_rate, 1)
        }

        return final_payload
