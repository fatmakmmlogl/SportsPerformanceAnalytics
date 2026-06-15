"""
AngleCalculator: Vücut landmark'larından eklem açılarını hesaplayan sınıf.
"""

import numpy as np
from typing import Optional, Tuple, Dict, List


class AngleCalculator:
    """
    Üç nokta arasındaki açıyı hesaplayan ve eklem açılarını döndüren sınıf.
    
    Tüm açılar 0-180 derece arasında hesaplanır.
    """

    @staticmethod
    def calculate_angle(a: Tuple[float, float], b: Tuple[float, float],
                        c: Tuple[float, float]) -> float:
        """
        Üç nokta arasındaki açıyı hesaplar. b noktası köşe (eklem) noktasıdır.
        
        Args:
            a: Birinci nokta koordinatları (x, y)
            b: Köşe nokta koordinatları (eklem) (x, y)
            c: Üçüncü nokta koordinatları (x, y)
            
        Returns:
            float: Derece cinsinden açı (0-180)
        """
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)
        c = np.array(c, dtype=float)

        # Vektörleri hesapla
        ba = a - b  # b'den a'ya vektör
        bc = c - b  # b'den c'ye vektör

        # Vektörlerin normlarını al
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)

        # Sıfıra bölme kontrolü
        if norm_ba == 0 or norm_bc == 0:
            return 0.0

        # Kosinüs değerini hesapla (-1 ile 1 arasına kırp)
        cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)

        # Açıyı dereceye çevir
        angle = np.degrees(np.arccos(cos_angle))
        return round(float(angle), 2)

    def get_joint_angles(self, landmarks: List, frame_shape: Tuple[int, int]) -> Dict[str, float]:
        """
        Tüm önemli eklem açılarını hesaplayarak sözlük olarak döndürür.
        
        Args:
            landmarks: MediaPipe landmark listesi
            frame_shape: Frame boyutları (height, width)
            
        Returns:
            Dict[str, float]: Eklem adı -> açı (derece) eşleşmeleri
        """
        if not landmarks:
            return {}

        h, w = frame_shape[:2]

        def lm(idx: int) -> Tuple[float, float]:
            """Landmark'ı pixel koordinatlarına dönüştürür."""
            return (landmarks[idx].x * w, landmarks[idx].y * h)

        angles = {}

        try:
            # ── Sol diz açısı ──────────────────────────────────────────────
            angles["left_knee"] = self.calculate_angle(
                lm(23),  # sol kalça
                lm(25),  # sol diz  (köşe)
                lm(27)   # sol ayak bileği
            )

            # ── Sağ diz açısı ──────────────────────────────────────────────
            angles["right_knee"] = self.calculate_angle(
                lm(24),  # sağ kalça
                lm(26),  # sağ diz  (köşe)
                lm(28)   # sağ ayak bileği
            )

            # ── Sol dirsek açısı ───────────────────────────────────────────
            angles["left_elbow"] = self.calculate_angle(
                lm(11),  # sol omuz
                lm(13),  # sol dirsek (köşe)
                lm(15)   # sol bilek
            )

            # ── Sağ dirsek açısı ───────────────────────────────────────────
            angles["right_elbow"] = self.calculate_angle(
                lm(12),  # sağ omuz
                lm(14),  # sağ dirsek (köşe)
                lm(16)   # sağ bilek
            )

            # ── Kalça açısı (sol taraf) ────────────────────────────────────
            angles["hip"] = self.calculate_angle(
                lm(11),  # sol omuz
                lm(23),  # sol kalça (köşe)
                lm(25)   # sol diz
            )

            # ── Omuz açısı (sol taraf) ────────────────────────────────────
            angles["shoulder"] = self.calculate_angle(
                lm(13),  # sol dirsek
                lm(11),  # sol omuz (köşe)
                lm(23)   # sol kalça
            )

            # ── Gövde dikliği (sırt açısı) ────────────────────────────────
            # Omuz - kalça - diz açısı
            angles["trunk"] = self.calculate_angle(
                lm(11),  # sol omuz
                lm(23),  # sol kalça
                lm(25)   # sol diz
            )

        except (IndexError, AttributeError):
            # Landmark listesi beklenen indeksleri içermiyorsa boş döndür
            pass

        return angles

    @staticmethod
    def angle_in_range(angle: float, min_val: float, max_val: float) -> bool:
        """
        Açının belirtilen aralıkta olup olmadığını kontrol eder.
        
        Args:
            angle: Kontrol edilecek açı
            min_val: Minimum değer
            max_val: Maksimum değer
            
        Returns:
            bool: Açı aralıkta ise True
        """
        return min_val <= angle <= max_val

    @staticmethod
    def symmetry_score(left_angle: float, right_angle: float) -> float:
        """
        Sol ve sağ eklem arasındaki simetri skorunu hesaplar.
        
        Args:
            left_angle: Sol eklem açısı
            right_angle: Sağ eklem açısı
            
        Returns:
            float: 0-100 arası simetri skoru (100 = mükemmel simetri)
        """
        diff = abs(left_angle - right_angle)
        # Maksimum 30 derece fark kabul edilebilir
        score = max(0.0, 100.0 - (diff / 30.0) * 100.0)
        return round(score, 2)
