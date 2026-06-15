"""
PerformanceScorer: 0-100 arasında anlık performans skoru hesaplayan sınıf.
Doğru duruş, hareket genişliği, denge ve simetri kriterleri kullanılır.
"""

from typing import Dict, Optional
from models.angle_calculator import AngleCalculator


class PerformanceScorer:
    """
    Dört kritere göre 0-100 arasında performans skoru hesaplar:
    
    1. Posture Score   (Doğru Duruş)   – %30
    2. Range of Motion (Hareket Genişliği) – %30
    3. Stability Score (Denge)          – %20
    4. Symmetry Score  (Simetri)        – %20
    """

    # Kriter ağırlıkları (toplamı 1.0 olmalı)
    WEIGHTS = {
        "posture":    0.30,
        "range":      0.30,
        "stability":  0.20,
        "symmetry":   0.20,
    }

    # Her egzersiz için ideal açı aralıkları
    IDEAL_ANGLES = {
        "squat": {
            "knee_down": (80, 100),   # Alt pozisyon ideal diz açısı
            "knee_up":   (160, 180),  # Üst pozisyon ideal diz açısı
            "hip_range": (60, 160),
        },
        "pushup": {
            "elbow_down": (70, 100),  # Alt pozisyon ideal dirsek açısı
            "elbow_up":   (155, 180), # Üst pozisyon
            "hip_range":  (160, 180), # Gövde düzlüğü
        },
        "lunge": {
            "knee_down": (80, 100),
            "knee_up":   (155, 180),
        },
        "plank": {
            "hip_range":     (160, 180),
            "shoulder_range":(70, 110),
        },
    }

    def __init__(self):
        self._score_history = []  # Son N frame puanları (denge hesabı için)
        self._history_size = 30   # ~1 saniye (30 FPS varsayımıyla)

    def calculate(self, exercise: str, angles: Dict[str, float],
                  stage: Optional[str] = None) -> Dict[str, float]:
        """
        Anlık performans skorunu hesaplar.
        
        Args:
            exercise: Aktif egzersiz adı
            angles: Eklem açıları sözlüğü
            stage: Egzersizin mevcut fazı ('up' / 'down' / None)
            
        Returns:
            Dict[str, float]: {
                'total': Toplam skor (0-100),
                'posture': Duruş skoru,
                'range': Hareket genişliği skoru,
                'stability': Denge skoru,
                'symmetry': Simetri skoru,
            }
        """
        if not angles or exercise not in self.IDEAL_ANGLES:
            return self._empty_score()

        posture_s   = self._posture_score(exercise, angles, stage)
        range_s     = self._range_of_motion_score(exercise, angles, stage)
        stability_s = self._stability_score(posture_s)
        symmetry_s  = self._symmetry_score(angles)

        total = (
            posture_s   * self.WEIGHTS["posture"]   +
            range_s     * self.WEIGHTS["range"]     +
            stability_s * self.WEIGHTS["stability"] +
            symmetry_s  * self.WEIGHTS["symmetry"]
        )

        result = {
            "total":     round(min(100.0, max(0.0, total)), 1),
            "posture":   round(posture_s, 1),
            "range":     round(range_s, 1),
            "stability": round(stability_s, 1),
            "symmetry":  round(symmetry_s, 1),
        }

        # Geçmişe ekle (denge hesabı için)
        self._score_history.append(result["total"])
        if len(self._score_history) > self._history_size:
            self._score_history.pop(0)

        return result

    # ── Kriter hesaplama yöntemleri ─────────────────────────────────────────

    def _posture_score(self, exercise: str, angles: Dict[str, float],
                       stage: Optional[str]) -> float:
        """Doğru duruş skorunu hesaplar."""
        score = 100.0

        if exercise == "squat":
            hip = angles.get("hip", 90)
            # Squat sırasında kalça öne eğilmemeli
            if hip < 55:
                score -= 30  # Aşırı öne eğilme cezası
            elif hip < 70:
                score -= 15

        elif exercise == "pushup":
            hip = angles.get("hip", 170)
            # Gövde düz olmalı
            if hip < 150:
                score -= 40  # Kalça sarkıyor
            elif hip < 160:
                score -= 20

        elif exercise == "plank":
            hip    = angles.get("hip", 170)
            trunk  = angles.get("trunk", 170)
            if hip < 150 or trunk < 150:
                score -= 50

        elif exercise == "lunge":
            trunk = angles.get("trunk", 170)
            if trunk < 140:
                score -= 25  # Gövde fazla öne eğilmiş

        return max(0.0, score)

    def _range_of_motion_score(self, exercise: str, angles: Dict[str, float],
                                stage: Optional[str]) -> float:
        """Hareket genişliği skorunu hesaplar."""
        ideal = self.IDEAL_ANGLES.get(exercise, {})

        if exercise in ("squat", "lunge"):
            knee = min(angles.get("left_knee", 180), angles.get("right_knee", 180))
            if stage == "down":
                lo, hi = ideal.get("knee_down", (80, 100))
                return self._range_penalty(knee, lo, hi)
            else:
                lo, hi = ideal.get("knee_up", (160, 180))
                return self._range_penalty(knee, lo, hi)

        elif exercise == "pushup":
            elbow = (angles.get("left_elbow", 90) + angles.get("right_elbow", 90)) / 2
            if stage == "down":
                lo, hi = ideal.get("elbow_down", (70, 100))
                return self._range_penalty(elbow, lo, hi)
            else:
                lo, hi = ideal.get("elbow_up", (155, 180))
                return self._range_penalty(elbow, lo, hi)

        elif exercise == "plank":
            hip = angles.get("hip", 170)
            lo, hi = ideal.get("hip_range", (160, 180))
            return self._range_penalty(hip, lo, hi)

        return 80.0  # Varsayılan

    def _stability_score(self, current_posture: float) -> float:
        """
        Denge skorunu anlık duruş puanı ve geçmiş ortalama üzerinden hesaplar.
        Düşük varyans = yüksek denge.
        """
        if len(self._score_history) < 5:
            return current_posture

        import statistics
        try:
            stdev = statistics.stdev(self._score_history[-10:])
            # Standart sapma 0 ise mükemmel denge
            stability = max(0.0, 100.0 - stdev * 2)
        except statistics.StatisticsError:
            stability = current_posture

        return stability

    def _symmetry_score(self, angles: Dict[str, float]) -> float:
        """Sol/sağ simetri skorunu hesaplar."""
        scores = []

        lk = angles.get("left_knee")
        rk = angles.get("right_knee")
        if lk is not None and rk is not None:
            scores.append(AngleCalculator.symmetry_score(lk, rk))

        le = angles.get("left_elbow")
        re = angles.get("right_elbow")
        if le is not None and re is not None:
            scores.append(AngleCalculator.symmetry_score(le, re))

        return sum(scores) / len(scores) if scores else 80.0

    @staticmethod
    def _range_penalty(value: float, lo: float, hi: float) -> float:
        """
        Değerin ideal aralığa yakınlığına göre puan verir.
        Aralık içindeyse 100, dışındaysa uzaklığa göre ceza uygular.
        """
        if lo <= value <= hi:
            return 100.0
        elif value < lo:
            diff = lo - value
        else:
            diff = value - hi
        # Her 10 derece sapma için 15 puan düş
        return max(0.0, 100.0 - (diff / 10.0) * 15.0)

    @staticmethod
    def _empty_score() -> Dict[str, float]:
        return {"total": 0.0, "posture": 0.0, "range": 0.0,
                "stability": 0.0, "symmetry": 0.0}

    def get_average_score(self) -> float:
        """Geçmiş frame'lerin ortalama toplam skorunu döndürür."""
        if not self._score_history:
            return 0.0
        return round(sum(self._score_history) / len(self._score_history), 1)

    def reset(self):
        """Skor geçmişini temizler."""
        self._score_history.clear()
