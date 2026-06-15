"""
DashboardManager: Streamlit dashboard bileşenlerini yöneten sınıf.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Optional


class DashboardManager:
    """
    Streamlit tabanlı sporcu performans panosunu yöneten sınıf.
    
    Bu sınıf doğrudan app.py tarafından çağrılır ve dashboard'un
    her bölümünü ayrı metodlarla render eder.
    """

    @staticmethod
    def render_stats_cards(stats: Dict):
        """Üst kısımdaki istatistik kartlarını render eder."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📊 Ortalama Skor",
                value=f"{stats.get('average_score', 0):.1f}",
                delta=None
            )
        with col2:
            st.metric(
                label="🏆 En İyi Skor",
                value=f"{stats.get('best_score', 0):.1f}"
            )
        with col3:
            st.metric(
                label="🎯 Toplam Seans",
                value=stats.get("total_sessions", 0)
            )
        with col4:
            st.metric(
                label="🔁 Toplam Tekrar",
                value=stats.get("total_reps", 0)
            )

    @staticmethod
    def render_score_chart(score_history: List[Dict]) -> Optional[go.Figure]:
        """
        Skor gelişim grafiğini Plotly ile render eder.
        
        Args:
            score_history: [{'date': str, 'score': float, 'exercise_type': str}]
            
        Returns:
            go.Figure veya None (veri yoksa)
        """
        if not score_history:
            st.info("Henüz seans verisi yok. İlk antrenmanını tamamla!")
            return None

        df = pd.DataFrame(score_history)
        df["date"] = pd.to_datetime(df["date"])

        fig = px.line(
            df, x="date", y="score", color="exercise_type",
            title="Performans Gelişimi",
            labels={"date": "Tarih", "score": "Skor", "exercise_type": "Egzersiz"},
            template="plotly_dark",
            markers=True,
        )
        fig.update_layout(
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="#16213e",
            font_color="white",
            legend_title="Egzersiz",
            yaxis_range=[0, 105],
        )
        return fig

    @staticmethod
    def render_exercise_pie(breakdown: List[Dict]) -> Optional[go.Figure]:
        """
        Egzersiz dağılım pasta grafiğini render eder.
        
        Args:
            breakdown: [{'exercise_type': str, 'cnt': int, 'avg_score': float}]
            
        Returns:
            go.Figure veya None
        """
        if not breakdown:
            return None

        labels = [r["exercise_type"].capitalize() for r in breakdown]
        values = [r["cnt"] for r in breakdown]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            marker_colors=["#00d4ff", "#ff6b6b", "#51cf66", "#ffd43b"],
        )])
        fig.update_layout(
            title="Egzersiz Dağılımı",
            template="plotly_dark",
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="#16213e",
            font_color="white",
            showlegend=True,
        )
        return fig

    @staticmethod
    def render_sessions_table(sessions: List[Dict]):
        """Son seans geçmişini tablo olarak render eder."""
        if not sessions:
            st.info("Henüz seans kaydı yok.")
            return

        df = pd.DataFrame(sessions)[
            ["date", "exercise_type", "score", "duration_sec"]
        ].copy()
        df.columns = ["Tarih", "Egzersiz", "Skor", "Süre (sn)"]
        df["Skor"] = df["Skor"].round(1)
        df["Süre (sn)"] = df["Süre (sn)"].round(1)
        df = df.head(15)

        st.dataframe(df, use_container_width=True, hide_index=True)

    @staticmethod
    def render_realtime_metrics(data: Dict):
        """
        Analiz pipeline'ından gelen anlık metrikleri sidebar'da gösterir.
        
        Args:
            data: AnalyticsService.process_frame() çıktısı
        """
        score = data.get("score", {})
        angles = data.get("angles", {})

        st.sidebar.markdown("### 📐 Eklem Açıları")
        angle_labels = {
            "left_knee":   "Sol Diz",
            "right_knee":  "Sağ Diz",
            "left_elbow":  "Sol Dirsek",
            "right_elbow": "Sağ Dirsek",
            "hip":         "Kalça",
            "shoulder":    "Omuz",
        }
        for key, label in angle_labels.items():
            val = angles.get(key)
            if val is not None:
                st.sidebar.metric(label, f"{val:.1f}°")

        st.sidebar.markdown("### 🎯 Performans Detayı")
        criteria = {
            "posture":   "Duruş",
            "range":     "Hareket Genişliği",
            "stability": "Denge",
            "symmetry":  "Simetri",
        }
        for key, label in criteria.items():
            val = score.get(key, 0)
            color = "green" if val >= 70 else "orange" if val >= 45 else "red"
            st.sidebar.markdown(
                f"**{label}:** :{color}[{val:.1f}]"
            )
