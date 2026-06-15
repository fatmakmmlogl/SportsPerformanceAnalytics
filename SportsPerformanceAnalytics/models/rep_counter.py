"""
RepCounter: Egzersiz tekrar (repetition) sayacı.
Her egzersiz tipi için aşağı/yukarı fazlarını izleyerek rep sayar.
"""

from typing import Dict, Optional
from models.angle_calculator import AngleCalculator


class RepCounter:
    """
    Squat, Push-Up, Lunge ve Plank için otomatik tekrar sayacı.
    
    Durum makinesi (state machine) yaklaşımıyla her egzersizin
    "aşağı" ve "yukarı" fazlarını izler.
    
    Attributes:
        counts (Dict[str, int]): Egzersiz başına toplam tekrar sayısı
        _stage (Dict[str, str]): Her egzersiz için mevcut faz ('up'/'down'/None)
    """

    # ── Faz eşikleri ────────────────────────────────────────────────────────
    PHASE_THRESHOLDS = {
        "squat": {
            "down_angle": 90,   # Diz açısı bu değerin altına inerse "aşağı" fazı
            "up_angle":   160,  # Diz açısı bu değerin üstüne çıkarsa "yukarı" fazı
        },
        "pushup": {
            "down_angle": 90,   # Dirsek açısı bu değerin altına inerse "aşağı"
            "up_angle":   155,  # Dirsek açısı bu değerin üstüne çıkarsa "yukarı"
        },
        "lunge": {
            "down_angle": 100,  # Ön diz açısı bu değerin altında = "aşağı"
            "up_angle":   155,  # Ön diz açısı bu değerin üstünde = "yukarı"
        },
        "plank": {
            # Plank zamana dayalı sayılır (her 30 saniye = 1 rep)
            "hold_seconds": 30,
        }
    }

    def __init__(self):
        self.counts: Dict[str, int] = {
            "squat":  0,
            "pushup": 0,
            "lunge":  0,
            "plank":  0,
        }
        self._stage: Dict[str, Optional[str]] = {
            "squat":  None,
            "pushup": None,
            "lunge":  None,
            "plank":  None,
        }
        self._plank_frames = 0  # Plank için tutulan kare sayısı
        self._fps = 30          # Varsayılan FPS (plank hesabında kullanılır)

    def update(self, exercise: str, angles: Dict[str, float]) -> int:
        """
        Mevcut eklem açılarına göre tekrar sayacını günceller.
        
        Args:
            exercise: Aktif egzersiz ('squat', 'pushup', 'lunge', 'plank')
            angles: Eklem açıları sözlüğü
            
        Returns:
            int: Güncellenen egzersiz için toplam tekrar sayısı
        """
        if exercise not in self.counts:
            return 0

        if exercise == "squat":
            self._update_squat(angles)
        elif exercise == "pushup":
            self._update_pushup(angles)
        elif exercise == "lunge":
            self._update_lunge(angles)
        elif exercise == "plank":
            self._update_plank()

        return self.counts[exercise]

    # ── Egzersiz özel güncelleme yöntemleri ─────────────────────────────────

    def _update_squat(self, angles: Dict[str, float]):
        """Squat faz tespiti ve sayım."""
        left_knee  = angles.get("left_knee",  180)
        right_knee = angles.get("right_knee", 180)
        avg_knee   = (left_knee + right_knee) / 2

        thresh = self.PHASE_THRESHOLDS["squat"]

        if avg_knee < thresh["down_angle"]:
            self._stage["squat"] = "down"
        elif avg_knee > thresh["up_angle"] and self._stage["squat"] == "down":
            self._stage["squat"] = "up"
            self.counts["squat"] += 1

    def _update_pushup(self, angles: Dict[str, float]):
        """Push-up faz tespiti ve sayım."""
        left_elbow  = angles.get("left_elbow",  180)
        right_elbow = angles.get("right_elbow", 180)
        avg_elbow   = (left_elbow + right_elbow) / 2

        thresh = self.PHASE_THRESHOLDS["pushup"]

        if avg_elbow < thresh["down_angle"]:
            self._stage["pushup"] = "down"
        elif avg_elbow > thresh["up_angle"] and self._stage["pushup"] == "down":
            self._stage["pushup"] = "up"
            self.counts["pushup"] += 1

    def _update_lunge(self, angles: Dict[str, float]):
        """Lunge faz tespiti ve sayım (öndeki diz kullanılır)."""
        left_knee  = angles.get("left_knee",  180)
        right_knee = angles.get("right_knee", 180)
        # Öndeki dizi bulmak için küçük açıyı al
        front_knee = min(left_knee, right_knee)

        thresh = self.PHASE_THRESHOLDS["lunge"]

        if front_knee < thresh["down_angle"]:
            self._stage["lunge"] = "down"
        elif front_knee > thresh["up_angle"] and self._stage["lunge"] == "down":
            self._stage["lunge"] = "up"
            self.counts["lunge"] += 1

    def _update_plank(self):
        """Plank süre sayacı: her 30 saniye tutuşta 1 rep."""
        self._plank_frames += 1
        frames_per_rep = self.PHASE_THRESHOLDS["plank"]["hold_seconds"] * self._fps
        self.counts["plank"] = self._plank_frames // int(frames_per_rep)

    # ── Yardımcı yöntemler ───────────────────────────────────────────────────

    def get_stage(self, exercise: str) -> Optional[str]:
        """
        Belirtilen egzersiz için mevcut fazı döndürür.
        
        Args:
            exercise: Egzersiz adı
            
        Returns:
            Optional[str]: 'up', 'down' veya None
        """
        return self._stage.get(exercise)

    def get_count(self, exercise: str) -> int:
        """
        Belirtilen egzersiz için toplam tekrar sayısını döndürür.
        
        Args:
            exercise: Egzersiz adı
            
        Returns:
            int: Toplam tekrar sayısı
        """
        return self.counts.get(exercise, 0)

    def get_total_reps(self) -> int:
        """Tüm egzersizlerdeki toplam tekrar sayısını döndürür."""
        return sum(self.counts.values())

    def set_fps(self, fps: float):
        """
        Plank hesabı için FPS değerini günceller.
        
        Args:
            fps: Saniyedeki kare sayısı
        """
        self._fps = max(1, fps)

    def reset(self, exercise: Optional[str] = None):
        """
        Sayacı sıfırlar.
        
        Args:
            exercise: Sadece bu egzersizi sıfırla. None ise tümünü sıfırla.
        """
        if exercise:
            self.counts[exercise] = 0
            self._stage[exercise] = None
            if exercise == "plank":
                self._plank_frames = 0
        else:
            for key in self.counts:
                self.counts[key] = 0
                self._stage[key] = None
            self._plank_frames = 0
