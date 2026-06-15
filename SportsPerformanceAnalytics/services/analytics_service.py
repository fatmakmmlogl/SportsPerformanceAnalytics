"""
AnalyticsService: Kamera/video frame akışını alıp tüm analiz pipeline'ını çalıştıran ana servis.
PoseDetector, AngleCalculator, ExerciseRecognizer, RepCounter, PerformanceScorer ve
FeedbackGenerator'ı koordine eder.
"""

import cv2
import numpy as np
import time
from typing import Dict, Any, Optional, Tuple

from models.pose_detector      import PoseDetector
from models.angle_calculator   import AngleCalculator
from models.exercise_recognizer import ExerciseRecognizer
from models.rep_counter        import RepCounter
from models.performance_scorer import PerformanceScorer
from models.feedback_generator import FeedbackGenerator
from database.database_manager import DatabaseManager


class AnalyticsService:
    """
    Tek bir frame akışı üzerinde tüm spor analiz pipeline'ını çalıştıran servis.
    
    Kullanım:
        service = AnalyticsService()
        service.start_session("Ali", exercise_type="squat")
        annotated, data = service.process_frame(frame)
        service.end_session()
    """

    def __init__(self, language: str = "tr"):
        self.pose_detector    = PoseDetector()
        self.angle_calc       = AngleCalculator()
        self.ex_recognizer    = ExerciseRecognizer()
        self.rep_counter      = RepCounter()
        self.scorer           = PerformanceScorer()
        self.feedback_gen     = FeedbackGenerator(language=language)
        self.db               = DatabaseManager()

        self._session_id:    Optional[int] = None
        self._athlete_id:    Optional[int] = None
        self._session_start: Optional[float] = None
        self._current_exercise: str = "unknown"
        self._frame_count: int = 0
        self._score_accumulator: float = 0.0

    # ── Seans yönetimi ───────────────────────────────────────────────────────

    def start_session(self, athlete_name: str, exercise_type: str = "auto",
                      age: Optional[int] = None, sport: Optional[str] = None):
        """
        Yeni bir antrenman seansı başlatır.
        
        Args:
            athlete_name: Sporcu adı
            exercise_type: Egzersiz tipi veya 'auto' (otomatik tespit)
            age: Sporcu yaşı
            sport: Spor dalı
        """
        self._athlete_id = self.db.get_or_create_athlete(athlete_name, age, sport)
        self._current_exercise = exercise_type if exercise_type != "auto" else "unknown"
        self._session_id = self.db.create_session(
            self._athlete_id, self._current_exercise
        )
        self._session_start = time.time()
        self._frame_count = 0
        self._score_accumulator = 0.0

        # Alt modülleri sıfırla
        self.rep_counter.reset()
        self.scorer.reset()
        self.ex_recognizer.reset()

    def end_session(self) -> Optional[Dict]:
        """
        Mevcut seansı bitirir; ortalama skoru DB'ye kaydeder.
        
        Returns:
            Dict: Seans özeti veya None
        """
        if self._session_id is None:
            return None

        duration = time.time() - (self._session_start or time.time())
        avg_score = self.scorer.get_average_score()

        self.db.update_session_score(self._session_id, avg_score, duration)

        total_reps = self.rep_counter.get_total_reps()
        self.db.save_metric(
            session_id    = self._session_id,
            rep_count     = total_reps,
            avg_angle     = 0.0,
            stability     = 0.0,
            symmetry      = 0.0,
            posture       = 0.0,
            range_score   = 0.0,
        )

        summary = {
            "session_id":    self._session_id,
            "duration_sec":  round(duration, 1),
            "average_score": avg_score,
            "total_reps":    total_reps,
            "exercise":      self._current_exercise,
        }
        self._session_id = None
        return summary

    # ── Frame işleme ─────────────────────────────────────────────────────────

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Tek bir video karesi üzerinde tüm analiz pipeline'ını çalıştırır.
        
        Args:
            frame: BGR formatında video karesi
            
        Returns:
            Tuple[np.ndarray, Dict]:
                - Üzerine açıklama eklenmiş frame
                - Analiz sonuçları sözlüğü
        """
        self._frame_count += 1

        # 1) Pose tespiti
        frame, results = self.pose_detector.detect(frame)

        if not self.pose_detector.is_pose_detected(results):
            frame = self._draw_overlay(frame, {}, [], "unknown", {}, 0)
            return frame, self._empty_data()

        # 2) Landmark'ları çiz
        frame = self.pose_detector.draw_landmarks(frame, results)
        landmarks = self.pose_detector.get_landmarks(results)

        # 3) Eklem açıları
        angles = self.angle_calc.get_joint_angles(landmarks, frame.shape)

        # 4) Egzersiz tespiti
        exercise = self.ex_recognizer.recognize(angles, landmarks)
        if self._current_exercise == "unknown":
            self._current_exercise = exercise

        # 5) Tekrar sayımı
        reps = self.rep_counter.update(exercise, angles)
        stage = self.rep_counter.get_stage(exercise)

        # 6) Performans skoru
        score = self.scorer.calculate(exercise, angles, stage)

        # 7) Geri bildirimler
        feedback = self.feedback_gen.generate(exercise, angles, score, stage)

        # 8) Frame üzerine overlay çiz
        frame = self._draw_overlay(frame, angles, feedback, exercise, score, reps)

        data = {
            "exercise": exercise,
            "angles":   angles,
            "reps":     reps,
            "score":    score,
            "feedback": feedback,
            "stage":    stage,
        }
        return frame, data

    # ── Ekran Çizimi ─────────────────────────────────────────────────────────

    def _draw_overlay(self, frame: np.ndarray, angles: Dict,
                      feedback: list, exercise: str,
                      score: Dict, reps: int) -> np.ndarray:
        """Frame üzerine bilgi paneli çizer."""
        h, w = frame.shape[:2]

        # Yarı saydam arka plan paneli
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 110), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Egzersiz adı
        ex_name = self.ex_recognizer.get_exercise_display_name(exercise)
        cv2.putText(frame, f"Egzersiz: {ex_name}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        # Tekrar sayısı
        cv2.putText(frame, f"Tekrar: {reps}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Performans skoru
        total_score = score.get("total", 0)
        score_color = (0, 230, 0) if total_score >= 70 else \
                      (0, 200, 255) if total_score >= 45 else (0, 0, 255)
        cv2.putText(frame, f"Skor: {total_score:.0f}/100", (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, score_color, 2)

        # Eklem açıları (sağ taraf)
        if angles:
            y_offset = 30
            for name, angle in list(angles.items())[:4]:
                label = {
                    "left_knee": "Sol Diz",
                    "right_knee": "Sağ Diz",
                    "left_elbow": "Sol Dirsek",
                    "right_elbow": "Sağ Dirsek",
                    "hip": "Kalça",
                    "shoulder": "Omuz",
                }.get(name, name)
                cv2.putText(frame, f"{label}: {angle:.0f}°",
                            (w - 200, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
                y_offset += 25

        # Geri bildirim mesajları (alt kısım)
        if feedback:
            msg = feedback[0]  # En kritik mesajı göster
            cv2.putText(frame, msg["text"], (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, msg["color"], 2)

        return frame

    @staticmethod
    def _empty_data() -> Dict:
        return {
            "exercise": "unknown",
            "angles":   {},
            "reps":     0,
            "score":    {"total": 0.0, "posture": 0.0, "range": 0.0,
                         "stability": 0.0, "symmetry": 0.0},
            "feedback": [],
            "stage":    None,
        }

    def get_session_id(self) -> Optional[int]:
        return self._session_id

    def get_current_exercise(self) -> str:
        return self._current_exercise

    def close(self):
        """Kaynakları serbest bırakır."""
        self.pose_detector.close()
