"""
PoseDetector: MediaPipe Pose kullanarak gerçek zamanlı insan vücudu landmark tespiti.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple, List


class PoseDetector:
    """
    MediaPipe Pose ile insan vücudu landmark'larını tespit eden sınıf.
    
    Attributes:
        detection_confidence (float): Minimum tespit güven eşiği
        tracking_confidence (float): Minimum takip güven eşiği
        pose: MediaPipe Pose nesnesi
        mp_draw: MediaPipe çizim yardımcıları
        mp_pose: MediaPipe Pose modülü
    """

    # MediaPipe Pose landmark indeksleri
    LANDMARK_INDICES = {
        "nose": 0,
        "left_shoulder": 11, "right_shoulder": 12,
        "left_elbow": 13,    "right_elbow": 14,
        "left_wrist": 15,    "right_wrist": 16,
        "left_hip": 23,      "right_hip": 24,
        "left_knee": 25,     "right_knee": 26,
        "left_ankle": 27,    "right_ankle": 28,
    }

    def __init__(self, detection_confidence: float = 0.7, tracking_confidence: float = 0.7):
        """
        PoseDetector başlatıcı.
        
        Args:
            detection_confidence: MediaPipe tespit güven eşiği (0.0 - 1.0)
            tracking_confidence: MediaPipe takip güven eşiği (0.0 - 1.0)
        """
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence,
            model_complexity=1,
            smooth_landmarks=True
        )

        self.results = None

    def detect(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[object]]:
        """
        Verilen frame üzerinde pose tespiti yapar.
        
        Args:
            frame: BGR formatında video karesi (numpy array)
            
        Returns:
            Tuple[np.ndarray, Optional[object]]: 
                - Üzerine çizim yapılmış frame
                - MediaPipe pose sonuçları (yoksa None)
        """
        if frame is None:
            return frame, None

        # BGR -> RGB dönüşümü (MediaPipe RGB kullanır)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False  # Performans iyileştirmesi

        # Pose tespiti
        self.results = self.pose.process(rgb_frame)

        rgb_frame.flags.writeable = True
        return frame, self.results

    def draw_landmarks(self, frame: np.ndarray, results: Optional[object] = None) -> np.ndarray:
        """
        Tespit edilen landmark'ları ve iskelet bağlantılarını frame üzerine çizer.
        
        Args:
            frame: Çizim yapılacak video karesi
            results: MediaPipe pose sonuçları (None ise self.results kullanılır)
            
        Returns:
            np.ndarray: Landmark'ların çizildiği frame
        """
        if results is None:
            results = self.results

        if results and results.pose_landmarks:
            # İskelet bağlantılarını çiz
            self.mp_draw.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                    color=(0, 255, 0), thickness=2, circle_radius=3
                ),
                connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                    color=(0, 200, 255), thickness=2
                )
            )
        return frame

    def get_landmarks(self, results: Optional[object] = None) -> Optional[List]:
        """
        Tespit edilen landmark'ları liste olarak döndürür.
        
        Args:
            results: MediaPipe pose sonuçları
            
        Returns:
            Optional[List]: Landmark listesi veya None
        """
        if results is None:
            results = self.results

        if results and results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None

    def get_landmark_coords(self, landmark_name: str, frame_shape: Tuple[int, int],
                            results: Optional[object] = None) -> Optional[Tuple[int, int]]:
        """
        Belirtilen landmark'ın pixel koordinatlarını döndürür.
        
        Args:
            landmark_name: Landmark adı (LANDMARK_INDICES sözlüğündeki anahtar)
            frame_shape: Frame boyutları (height, width)
            results: MediaPipe pose sonuçları
            
        Returns:
            Optional[Tuple[int, int]]: (x, y) pixel koordinatları veya None
        """
        landmarks = self.get_landmarks(results)
        if landmarks is None:
            return None

        idx = self.LANDMARK_INDICES.get(landmark_name)
        if idx is None:
            return None

        h, w = frame_shape[:2]
        lm = landmarks[idx]
        return (int(lm.x * w), int(lm.y * h))

    def get_visibility(self, landmark_name: str, results: Optional[object] = None) -> float:
        """
        Belirtilen landmark'ın görünürlük skorunu döndürür.
        
        Args:
            landmark_name: Landmark adı
            results: MediaPipe pose sonuçları
            
        Returns:
            float: Görünürlük skoru (0.0 - 1.0), landmark yoksa 0.0
        """
        landmarks = self.get_landmarks(results)
        if landmarks is None:
            return 0.0

        idx = self.LANDMARK_INDICES.get(landmark_name)
        if idx is None:
            return 0.0

        return landmarks[idx].visibility

    def is_pose_detected(self, results: Optional[object] = None) -> bool:
        """
        Pose tespitinin başarılı olup olmadığını kontrol eder.
        
        Args:
            results: MediaPipe pose sonuçları
            
        Returns:
            bool: Pose tespit edildi ise True
        """
        if results is None:
            results = self.results
        return results is not None and results.pose_landmarks is not None

    def close(self):
        """MediaPipe kaynaklarını serbest bırakır."""
        self.pose.close()
