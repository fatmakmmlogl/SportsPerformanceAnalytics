"""
ExerciseRecognizer: Eklem açıları ve landmark pozisyonlarına göre egzersiz tipini tespit eder.
"""

from typing import Dict, Optional, List
from models.angle_calculator import AngleCalculator


class ExerciseRecognizer:
    """
    Squat, Push-Up, Lunge ve Plank egzersizlerini otomatik olarak tanıyan sınıf.
    
    Her egzersiz için belirli açı eşikleri ve gövde pozisyon kuralları kullanılır.
    """

    EXERCISES = ["squat", "pushup", "lunge", "plank", "unknown"]

    # ── Egzersiz açı eşikleri ───────────────────────────────────────────────
    THRESHOLDS = {
        "squat": {
            "knee_angle_min": 60,    # Squat sırasında diz açısı aralığı
            "knee_angle_max": 170,
            "hip_angle_min": 60,
            "hip_angle_max": 170,
        },
        "pushup": {
            "elbow_angle_min": 40,   # Şınav sırasında dirsek açısı aralığı
            "elbow_angle_max": 170,
            "hip_angle_min": 160,    # Gövde düz olmalı
            "hip_angle_max": 180,
        },
        "lunge": {
            "front_knee_min": 80,    # Öndeki diz açısı
            "front_knee_max": 110,
            "back_knee_min": 60,
            "back_knee_max": 120,
        },
        "plank": {
            "hip_angle_min": 160,    # Kalça düz olmalı
            "hip_angle_max": 180,
            "elbow_angle_min": 155,  # Kollar uzanmış (veya bükülmüş)
            "shoulder_angle_min": 70,
            "shoulder_angle_max": 110,
        }
    }

    def __init__(self):
        self._last_exercise = "unknown"
        self._confidence_buffer: List[str] = []
        self._buffer_size = 5  # Kararlılık için son N frame'in oylaması

    def recognize(self, angles: Dict[str, float], landmarks: Optional[List] = None) -> str:
        """
        Verilen açılara göre egzersiz tipini belirler.
        
        Args:
            angles: Eklem açıları sözlüğü (AngleCalculator çıktısı)
            landmarks: MediaPipe landmark listesi (ek pozisyon analizi için)
            
        Returns:
            str: Tanınan egzersiz adı ('squat', 'pushup', 'lunge', 'plank', 'unknown')
        """
        if not angles:
            return "unknown"

        detected = self._detect_exercise(angles, landmarks)

        # Kararlılık filtresi: son N tespiti oy çokluğuyla belirle
        self._confidence_buffer.append(detected)
        if len(self._confidence_buffer) > self._buffer_size:
            self._confidence_buffer.pop(0)

        # En sık tekrar eden egzersiz
        if self._confidence_buffer:
            self._last_exercise = max(
                set(self._confidence_buffer),
                key=self._confidence_buffer.count
            )

        return self._last_exercise

    def _detect_exercise(self, angles: Dict[str, float],
                         landmarks: Optional[List]) -> str:
        """Açı değerlerine göre ham egzersiz tespiti yapar."""

        left_knee  = angles.get("left_knee", 180)
        right_knee = angles.get("right_knee", 180)
        left_elbow  = angles.get("left_elbow", 180)
        right_elbow = angles.get("right_elbow", 180)
        hip         = angles.get("hip", 180)
        shoulder    = angles.get("shoulder", 90)
        trunk       = angles.get("trunk", 180)

        avg_knee   = (left_knee + right_knee) / 2
        avg_elbow  = (left_elbow + right_elbow) / 2

        # ── Plank tespiti ──────────────────────────────────────────────────
        # Gövde düz, kalça düz, dirsekler uzanmış veya bükülmüş
        if (AngleCalculator.angle_in_range(hip, 155, 180) and
                AngleCalculator.angle_in_range(trunk, 155, 180) and
                avg_elbow > 140):
            # Dirsek bükülmüşse forearm plank, uzanmışsa straight-arm plank
            return "plank"

        # ── Push-up tespiti ────────────────────────────────────────────────
        # Gövde düz, dirsekler değişen açıda, omuzlar diz seviyesinde
        if (AngleCalculator.angle_in_range(hip, 155, 180) and
                AngleCalculator.angle_in_range(avg_elbow, 40, 165)):
            if landmarks is not None:
                # Omuzun kalçadan yüksek olup olmadığını kontrol et
                if self._shoulders_above_hips(landmarks):
                    return "pushup"

        # ── Squat tespiti ──────────────────────────────────────────────────
        # Dizler bükülmüş, kalça aşağıda, gövde görece dik
        if (AngleCalculator.angle_in_range(avg_knee, 60, 165) and
                AngleCalculator.angle_in_range(hip, 55, 160)):
            # Lunge'dan ayırt etmek için iki diz açısının farkını kontrol et
            knee_diff = abs(left_knee - right_knee)
            if knee_diff < 30:  # Squat'ta iki diz neredeyse eşit
                return "squat"

        # ── Lunge tespiti ─────────────────────────────────────────────────
        # Bir diz bükülmüş, diğeri daha düz, asimetri yüksek
        if (AngleCalculator.angle_in_range(avg_knee, 60, 160)):
            knee_diff = abs(left_knee - right_knee)
            if knee_diff >= 30:  # Lunge'da iki diz asimetrik
                return "lunge"

        return "unknown"

    @staticmethod
    def _shoulders_above_hips(landmarks: List) -> bool:
        """
        Omuzların kalçalardan y-ekseninde yukarıda olup olmadığını kontrol eder.
        (Görüntüde y ekseni aşağı doğrudur, dolayısıyla küçük y = yukarı)
        
        Args:
            landmarks: MediaPipe landmark listesi
            
        Returns:
            bool: Omuzlar kalçanın üzerindeyse True
        """
        try:
            shoulder_y = (landmarks[11].y + landmarks[12].y) / 2
            hip_y      = (landmarks[23].y + landmarks[24].y) / 2
            # Görüntüde küçük y = ekranın üstü
            return shoulder_y < hip_y
        except (IndexError, AttributeError):
            return False

    def get_exercise_display_name(self, exercise: str) -> str:
        """
        Egzersiz adının görüntülenecek Türkçe/İngilizce halini döndürür.
        
        Args:
            exercise: Egzersiz kodu
            
        Returns:
            str: Görüntülenecek ad
        """
        names = {
            "squat":   "Squat",
            "pushup":  "Push-Up",
            "lunge":   "Lunge",
            "plank":   "Plank",
            "unknown": "Egzersiz Algılanmadı",
        }
        return names.get(exercise, "Bilinmeyen")

    def reset(self):
        """Tespit geçmişini sıfırlar."""
        self._confidence_buffer.clear()
        self._last_exercise = "unknown"
