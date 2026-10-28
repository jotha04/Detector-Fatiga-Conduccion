import os
import sys
import cv2
import numpy as np

# Ensure we can import from the parent edge directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mediapipe as mp
from scipy.spatial import distance as dist

class MediaPipeDetector:
    """
    Detector de fatiga basado en MediaPipe Face Mesh (solutions API 0.10.x).
    Usa 478 puntos faciales (vs 68 de dlib). Funciona perfectamente con gafas,
    distintas condiciones de luz, y es extremadamente estable.
    
    Devuelve métricas en el mismo formato que DrowsinessDetector para
    ser 100% compatible con FatigueAnalyzer.
    """

    # Índices de MediaPipe Face Mesh para EAR
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]

    # Puntos para MAR
    MOUTH_TOP_INNER = [82, 13, 312]
    MOUTH_BOTTOM_INNER = [87, 14, 317]
    MOUTH_LEFT = 78
    MOUTH_RIGHT = 308

    # Puntos para estimación de pose de cabeza
    NOSE_TIP = 1
    CHIN = 152
    LEFT_EYE_CORNER = 263
    RIGHT_EYE_CORNER = 33
    LEFT_MOUTH_CORNER = 78
    RIGHT_MOUTH_CORNER = 308

    def __init__(self, config):
        print("[INFO] Inicializando MediaPipe Face Mesh (478 puntos, compatible con gafas)...")
        self.config = config

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,  # Incluye iris para mejor detección de ojos
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Modelo 3D para estimación de pose
        self.face_model_3d = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -330.0, -65.0),
            (-225.0, 170.0, -135.0),
            (225.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0),
            (150.0, -150.0, -125.0)
        ], dtype=np.float64)

    def _lm_to_px(self, landmark, w, h):
        """Convierte un landmark normalizado a coordenadas de píxel."""
        return int(landmark.x * w), int(landmark.y * h)

    def _calculate_ear(self, eye_points):
        """Calcula EAR usando 6 puntos del ojo."""
        A = dist.euclidean(eye_points[1], eye_points[5])
        B = dist.euclidean(eye_points[2], eye_points[4])
        C = dist.euclidean(eye_points[0], eye_points[3])
        if C == 0:
            return 0.0
        return (A + B) / (2.0 * C)

    def _calculate_mar(self, landmarks, w, h):
        """Calcula MAR usando puntos de la boca."""
        top_pts = [self._lm_to_px(landmarks[i], w, h) for i in self.MOUTH_TOP_INNER]
        bot_pts = [self._lm_to_px(landmarks[i], w, h) for i in self.MOUTH_BOTTOM_INNER]
        left = self._lm_to_px(landmarks[self.MOUTH_LEFT], w, h)
        right = self._lm_to_px(landmarks[self.MOUTH_RIGHT], w, h)

        vertical_dists = [dist.euclidean(t, b) for t, b in zip(top_pts, bot_pts)]
        D = dist.euclidean(left, right)
        if D == 0:
            return 0.0
        return sum(vertical_dists) / (3.0 * D)

    def _estimate_head_pose(self, landmarks, w, h):
        """Estima la pose de la cabeza (pitch, yaw, roll)."""
        pose_indices = [
            self.NOSE_TIP, self.CHIN,
            self.LEFT_EYE_CORNER, self.RIGHT_EYE_CORNER,
            self.LEFT_MOUTH_CORNER, self.RIGHT_MOUTH_CORNER
        ]
        image_points = np.array([
            self._lm_to_px(landmarks[idx], w, h) for idx in pose_indices
        ], dtype=np.float64)

        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array(
            [[focal_length, 0, center[0]],
             [0, focal_length, center[1]],
             [0, 0, 1]], dtype=np.float64
        )
        dist_coeffs = np.zeros((4, 1))

        try:
            success, rotation_vector, _ = cv2.solvePnP(
                self.face_model_3d, image_points, camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            if not success:
                return (0.0, 0.0, 0.0), None

            rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_matrix)
            pitch, yaw, roll = angles[0], angles[1], angles[2]
            return (pitch, yaw, roll), rotation_vector
        except Exception:
            return (0.0, 0.0, 0.0), None

    def process_frame(self, frame):
        """
        Procesa un frame y devuelve las métricas faciales.
        Compatible con FatigueAnalyzer.
        """
        h, w = frame.shape[:2]

        # MediaPipe requiere RGB - pasar por referencia sin copiar
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.face_mesh.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if not results.multi_face_landmarks:
            return frame, None

        landmarks = results.multi_face_landmarks[0].landmark

        # Calcular EAR
        left_eye_pts = [self._lm_to_px(landmarks[idx], w, h) for idx in self.LEFT_EYE]
        right_eye_pts = [self._lm_to_px(landmarks[idx], w, h) for idx in self.RIGHT_EYE]
        
        left_ear = self._calculate_ear(left_eye_pts)
        right_ear = self._calculate_ear(right_eye_pts)
        ear = (left_ear + right_ear) / 2.0

        # Calcular MAR
        mar = self._calculate_mar(landmarks, w, h)

        # Estimar pose de cabeza
        head_pose_angles, rotation_vector = self._estimate_head_pose(landmarks, w, h)
        pitch, yaw, roll = head_pose_angles

        # Construir landmarks para visualización (puntos clave)
        vis_indices = (
            self.LEFT_EYE + self.RIGHT_EYE +  # ojos
            [168, 6, 197, 195, 5, 4, 1, 2, 98, 327] +  # nariz
            [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308,
             415, 310, 311, 312, 13, 82, 81, 80, 191] +  # boca
            [336, 296, 334, 293, 300] +  # ceja izquierda
            [70, 63, 105, 66, 107]  # ceja derecha
        )
        face_landmarks = np.array(
            [self._lm_to_px(landmarks[idx], w, h) for idx in vis_indices],
            dtype=np.int32
        )

        metrics = {
            "ear": ear,
            "mar": mar,
            "head_pitch": pitch,
            "head_yaw": yaw,
            "head_roll": roll,
            "face_landmarks": face_landmarks,
            "rotation_vector": rotation_vector
        }

        return frame, metrics
