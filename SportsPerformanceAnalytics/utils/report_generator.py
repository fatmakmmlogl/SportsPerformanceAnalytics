"""
ReportGenerator: CSV ve grafik formatında performans raporları üreten sınıf.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # GUI olmayan ortamlar için


class ReportGenerator:
    """
    Sporcu performans verilerini CSV ve görsel grafik raporlarına dönüştüren sınıf.
    
    Raporlar reports/ dizinine kaydedilir.
    """

    REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

    def __init__(self):
        os.makedirs(self.REPORTS_DIR, exist_ok=True)

    # ── CSV Raporu ─────────────────────────────────────────────────────────

    def export_sessions_csv(self, sessions: List[Dict],
                            athlete_name: str = "athlete") -> str:
        """
        Seans listesini CSV dosyasına aktarır.
        
        Args:
            sessions: DatabaseManager.get_sessions_by_athlete() çıktısı
            athlete_name: Dosya adında kullanılacak sporcu adı
            
        Returns:
            str: Oluşturulan CSV dosyasının yolu
        """
        if not sessions:
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"{athlete_name.replace(' ', '_')}_{timestamp}.csv"
        filepath  = os.path.join(self.REPORTS_DIR, filename)

        fieldnames = ["id", "date", "exercise_type", "score", "duration_sec", "notes"]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(sessions)

        return filepath

    # ── Performans Grafiği ──────────────────────────────────────────────────

    def plot_score_history(self, score_history: List[Dict],
                           athlete_name: str = "Sporcu") -> str:
        """
        Zaman içindeki skor gelişimini çizgi grafiği olarak kaydeder.
        
        Args:
            score_history: [{'date': str, 'score': float, 'exercise_type': str}, ...]
            athlete_name: Grafik başlığında kullanılacak isim
            
        Returns:
            str: Kaydedilen grafik dosyasının yolu
        """
        if not score_history:
            return ""

        df = pd.DataFrame(score_history)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_facecolor("#1a1a2e")
        fig.patch.set_facecolor("#16213e")

        # Her egzersiz tipi için ayrı çizgi
        exercises = df["exercise_type"].unique()
        colors = ["#00d4ff", "#ff6b6b", "#51cf66", "#ffd43b"]

        for i, ex in enumerate(exercises):
            sub = df[df["exercise_type"] == ex]
            ax.plot(sub["date"], sub["score"],
                    marker="o", linewidth=2.5, markersize=5,
                    color=colors[i % len(colors)], label=ex.capitalize())

        ax.set_title(f"{athlete_name} – Performans Gelişimi",
                     color="white", fontsize=14, pad=12)
        ax.set_xlabel("Tarih", color="#aaaaaa")
        ax.set_ylabel("Skor (0–100)", color="#aaaaaa")
        ax.tick_params(colors="#aaaaaa")
        ax.spines[:].set_color("#444444")
        ax.set_ylim(0, 105)
        ax.legend(facecolor="#1a1a2e", labelcolor="white")
        ax.grid(True, linestyle="--", alpha=0.3)

        plt.tight_layout()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.REPORTS_DIR,
                                f"score_history_{athlete_name.replace(' ', '_')}_{timestamp}.png")
        plt.savefig(filepath, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return filepath

    def plot_exercise_breakdown(self, breakdown: List[Dict],
                                athlete_name: str = "Sporcu") -> str:
        """
        Egzersiz başına seans sayısını pasta grafiği olarak kaydeder.
        
        Args:
            breakdown: [{'exercise_type': str, 'cnt': int, 'avg_score': float}, ...]
            athlete_name: Grafik başlığında kullanılacak isim
            
        Returns:
            str: Kaydedilen grafik dosyasının yolu
        """
        if not breakdown:
            return ""

        labels = [r["exercise_type"].capitalize() for r in breakdown]
        sizes  = [r["cnt"] for r in breakdown]
        colors = ["#00d4ff", "#ff6b6b", "#51cf66", "#ffd43b"]

        fig, ax = plt.subplots(figsize=(6, 6))
        fig.patch.set_facecolor("#16213e")
        ax.set_facecolor("#16213e")

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.1f%%",
            colors=colors[:len(labels)], startangle=140,
            textprops={"color": "white"}
        )
        for autotext in autotexts:
            autotext.set_color("#1a1a2e")
            autotext.set_fontweight("bold")

        ax.set_title(f"{athlete_name} – Egzersiz Dağılımı",
                     color="white", fontsize=13, pad=12)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.REPORTS_DIR,
                                f"breakdown_{athlete_name.replace(' ', '_')}_{timestamp}.png")
        plt.savefig(filepath, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return filepath
