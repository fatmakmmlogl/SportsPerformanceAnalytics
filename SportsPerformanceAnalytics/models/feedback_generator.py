"""
FeedbackGenerator: Eklem açıları ve performans skoruna göre anlık sesli/yazılı geri bildirim üretir.
"""

from typing import Dict, List, Optional


class FeedbackGenerator:
    """
    Sporcuya gerçek zamanlı formu düzeltmesine yardımcı olacak
    Türkçe/İngilizce geri bildirim mesajları üreten sınıf.
    
    Geri bildirimler:
    - Kırmızı  (kritik): Hemen düzeltilmesi gereken form hataları
    - Sarı (uyarı): İyileştirme önerileri
    - Yeşil  (başarı): Doğru yapılan hareketler
    """

    # Renk kodları (BGR)
    COLOR_GREEN  = (0, 230, 0)
    COLOR_YELLOW = (0, 200, 255)
    COLOR_RED    = (0, 0, 255)

    def __init__(self, language: str = "tr"):
        """
        Args:
            language: Geri bildirim dili ('tr' = Türkçe, 'en' = İngilizce)
        """
        self._lang = language
        self._last_feedback: List[Dict] = []

    def generate(self, exercise: str, angles: Dict[str, float],
                 score: Dict[str, float], stage: Optional[str] = None) -> List[Dict]:
        """
        Mevcut durum için geri bildirim mesajları üretir.
        
        Args:
            exercise: Aktif egzersiz
            angles: Eklem açıları sözlüğü
            score: Performans skoru sözlüğü (PerformanceScorer çıktısı)
            stage: Mevcut faz ('up' / 'down' / None)
            
        Returns:
            List[Dict]: Her biri {'text': str, 'color': tuple, 'priority': int}
                        olan mesaj listesi (priority: 1=kritik, 2=uyarı, 3=başarı)
        """
        messages: List[Dict] = []

        if not angles or exercise == "unknown":
            messages.append(self._msg(
                "Egzersiz pozisyonu algılanıyor...",
                "Detecting exercise position...",
                self.COLOR_YELLOW, 2
            ))
            self._last_feedback = messages
            return messages

        # ── Genel performans skoru geri bildirimi ───────────────────────────
        total = score.get("total", 0)
        if total >= 85:
            messages.append(self._msg(
                "🏆 Mükemmel form!",
                "🏆 Excellent form!",
                self.COLOR_GREEN, 3
            ))
        elif total >= 65:
            messages.append(self._msg(
                "👍 İyi gidiyorsunuz, devam edin!",
                "👍 Good job, keep going!",
                self.COLOR_GREEN, 3
            ))
        elif total >= 45:
            messages.append(self._msg(
                "⚠️ Formu düzeltin",
                "⚠️ Correct your form",
                self.COLOR_YELLOW, 2
            ))
        else:
            messages.append(self._msg(
                "❌ Duruşa dikkat edin!",
                "❌ Watch your posture!",
                self.COLOR_RED, 1
            ))

        # ── Egzersiz özel geri bildirimler ─────────────────────────────────
        exercise_feedbacks = {
            "squat":  self._squat_feedback,
            "pushup": self._pushup_feedback,
            "lunge":  self._lunge_feedback,
            "plank":  self._plank_feedback,
        }

        specific = exercise_feedbacks.get(exercise)
        if specific:
            messages.extend(specific(angles, stage))

        # ── Simetri geri bildirimi ──────────────────────────────────────────
        sym = score.get("symmetry", 100)
        if sym < 70:
            messages.append(self._msg(
                "↔️ Sol/sağ dengesini koruyun",
                "↔️ Keep left/right balance",
                self.COLOR_YELLOW, 2
            ))

        # Önceliğe göre sırala (kritikler önce)
        messages.sort(key=lambda x: x["priority"])

        self._last_feedback = messages
        return messages

    # ── Egzersiz özel geri bildirimler ──────────────────────────────────────

    def _squat_feedback(self, angles: Dict[str, float],
                        stage: Optional[str]) -> List[Dict]:
        msgs = []
        left_knee  = angles.get("left_knee",  180)
        right_knee = angles.get("right_knee", 180)
        avg_knee   = (left_knee + right_knee) / 2
        hip        = angles.get("hip", 90)

        if stage == "down":
            if avg_knee > 110:
                msgs.append(self._msg(
                    "⬇️ Daha fazla çömelin",
                    "⬇️ Squat deeper",
                    self.COLOR_YELLOW, 2
                ))
            elif avg_knee < 70:
                msgs.append(self._msg(
                    "⬆️ Fazla çökmeyiniz",
                    "⬆️ Don't over-squat",
                    self.COLOR_YELLOW, 2
                ))
            else:
                msgs.append(self._msg(
                    "✅ Diz açısı iyi!",
                    "✅ Good knee angle!",
                    self.COLOR_GREEN, 3
                ))

        if hip < 60:
            msgs.append(self._msg(
                "🔼 Sırtınızı dik tutun",
                "🔼 Keep your back straight",
                self.COLOR_RED, 1
            ))

        return msgs

    def _pushup_feedback(self, angles: Dict[str, float],
                         stage: Optional[str]) -> List[Dict]:
        msgs = []
        avg_elbow = (angles.get("left_elbow", 90) + angles.get("right_elbow", 90)) / 2
        hip       = angles.get("hip", 170)

        if hip < 155:
            msgs.append(self._msg(
                "📏 Kalçanızı düzeltin",
                "📏 Align your hips",
                self.COLOR_RED, 1
            ))

        if stage == "down":
            if avg_elbow > 100:
                msgs.append(self._msg(
                    "⬇️ Daha fazla inin",
                    "⬇️ Lower yourself more",
                    self.COLOR_YELLOW, 2
                ))
            elif avg_elbow < 60:
                msgs.append(self._msg(
                    "⚠️ Çok fazla indiriyorsunuz",
                    "⚠️ You're going too low",
                    self.COLOR_YELLOW, 2
                ))
            else:
                msgs.append(self._msg(
                    "✅ Dirsek açısı mükemmel!",
                    "✅ Perfect elbow angle!",
                    self.COLOR_GREEN, 3
                ))

        return msgs

    def _lunge_feedback(self, angles: Dict[str, float],
                        stage: Optional[str]) -> List[Dict]:
        msgs = []
        front_knee = min(angles.get("left_knee", 180), angles.get("right_knee", 180))
        trunk      = angles.get("trunk", 170)

        if stage == "down":
            if front_knee > 110:
                msgs.append(self._msg(
                    "⬇️ Ön dizinizi bükin",
                    "⬇️ Bend your front knee",
                    self.COLOR_YELLOW, 2
                ))
            else:
                msgs.append(self._msg(
                    "✅ Lunge derinliği iyi!",
                    "✅ Good lunge depth!",
                    self.COLOR_GREEN, 3
                ))

        if trunk < 145:
            msgs.append(self._msg(
                "🔼 Gövdenizi dik tutun",
                "🔼 Keep your torso upright",
                self.COLOR_YELLOW, 2
            ))

        return msgs

    def _plank_feedback(self, angles: Dict[str, float],
                        stage: Optional[str]) -> List[Dict]:
        msgs = []
        hip   = angles.get("hip", 170)
        trunk = angles.get("trunk", 170)

        if hip < 155 or trunk < 155:
            msgs.append(self._msg(
                "📏 Kalçanızı kaldırın",
                "📏 Raise your hips",
                self.COLOR_RED, 1
            ))
        elif hip > 180:
            msgs.append(self._msg(
                "⬇️ Kalçanızı biraz indirin",
                "⬇️ Lower your hips slightly",
                self.COLOR_YELLOW, 2
            ))
        else:
            msgs.append(self._msg(
                "💪 Harika plank pozisyonu!",
                "💪 Great plank position!",
                self.COLOR_GREEN, 3
            ))

        return msgs

    # ── Yardımcı yöntemler ───────────────────────────────────────────────────

    def _msg(self, tr_text: str, en_text: str,
             color: tuple, priority: int) -> Dict:
        """Dile göre mesaj objesi oluşturur."""
        text = tr_text if self._lang == "tr" else en_text
        return {"text": text, "color": color, "priority": priority}

    def get_last_feedback(self) -> List[Dict]:
        """Son üretilen geri bildirimi döndürür."""
        return self._last_feedback

    def set_language(self, lang: str):
        """Geri bildirim dilini değiştirir ('tr' veya 'en')."""
        self._lang = lang if lang in ("tr", "en") else "tr"
