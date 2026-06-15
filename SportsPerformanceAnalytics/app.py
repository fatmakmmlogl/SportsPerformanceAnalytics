"""
app.py – AI Destekli Spor Performans Analiz Sistemi
Kullanıcı girişli + Admin paneli. `streamlit run app.py` ile başlatılır.
"""

import cv2, time, hashlib, numpy as np
import streamlit as st
from datetime import datetime

from services.analytics_service  import AnalyticsService
from database.database_manager   import DatabaseManager
from utils.report_generator      import ReportGenerator

# ── Admin şifresi (değiştirmek için buraya yaz) ──────────────────────────────
ADMIN_PASSWORD = "admin123"

st.set_page_config(
    page_title="AthleteIQ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #080c14; }
.block-container { padding: 1.5rem 2rem; }
[data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #1e2736; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #161b22 !important; border: 1px solid #30363d !important;
    border-radius: 8px !important; color: #e6edf3 !important;
}
.stButton > button {
    background: linear-gradient(135deg,#0072ff,#00c6ff) !important;
    color:#fff !important; border:none !important; border-radius:8px !important;
    font-weight:600 !important;
}
.stButton > button:hover { opacity:.85 !important; }
.metric-card {
    background:#0d1117; border:1px solid #1e2736; border-radius:12px;
    padding:1.1rem 1.3rem; margin-bottom:.75rem;
}
.metric-label { font-size:.72rem; color:#8b949e; text-transform:uppercase; letter-spacing:.06em; }
.metric-value { font-family:'Space Grotesk',sans-serif; font-size:1.9rem; font-weight:700; color:#fff; }
.score-high { color:#3fb950; } .score-mid { color:#d29922; } .score-low { color:#f85149; }
.fb-pill { display:inline-block; padding:.3rem .8rem; border-radius:20px; font-size:.82rem; font-weight:500; margin:.2rem 0; }
.fb-green  { background:rgba(63,185,80,.15);  color:#3fb950; border:1px solid rgba(63,185,80,.3); }
.fb-yellow { background:rgba(210,153,34,.15); color:#d29922; border:1px solid rgba(210,153,34,.3); }
.fb-red    { background:rgba(248,81,73,.15);  color:#f85149; border:1px solid rgba(248,81,73,.3); }
.stTabs [data-baseweb="tab-list"] { background:#0d1117; border-bottom:1px solid #1e2736; }
.stTabs [data-baseweb="tab"] { color:#8b949e !important; font-weight:500 !important; }
.stTabs [aria-selected="true"] { color:#fff !important; border-bottom:2px solid #0072ff !important; background:transparent !important; }
#MainMenu, footer, header { visibility:hidden; }
.stDeployButton { display:none; }
div[data-testid="stMetric"] {
    background:#0d1117 !important; border:1px solid #1e2736 !important;
    border-radius:10px !important; padding:.8rem 1rem !important;
}
div[data-testid="stMetric"] label { color:#8b949e !important; font-size:.75rem !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#fff !important; }
</style>
""", unsafe_allow_html=True)

db     = DatabaseManager()
report = ReportGenerator()

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ── Oturum durumu ─────────────────────────────────────────────────────────────
defaults = {
    "logged_in": False, "is_admin": False,
    "athlete_id": None, "athlete_name": "",
    "service": None, "session_active": False,
    "last_data": {}, "session_summary": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════════════
# GİRİŞ / KAYIT SAYFASI
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:

    st.markdown("""
    <div style="text-align:center;padding:3vh 0 1vh">
        <div style="display:inline-flex;align-items:center;gap:10px">
            <div style="width:44px;height:44px;background:linear-gradient(135deg,#0072ff,#00c6ff);
                border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;">⚡</div>
            <span style="font-family:'Space Grotesk',sans-serif;font-size:1.7rem;font-weight:700;color:#fff;">AthleteIQ</span>
        </div>
        <p style="color:#8b949e;margin-top:.5rem;font-size:.9rem;">AI Destekli Spor Performans Analizi</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.4, 1])[1]

    with col:
        tab_l, tab_r, tab_a = st.tabs(["  Giriş Yap  ", "  Kayıt Ol  ", "  🔐 Admin  "])

        # ── KULLANICI GİRİŞİ ──────────────────────────────────────────────────
        with tab_l:
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
            uname = st.text_input("Kullanıcı Adı", key="li_user", placeholder="kullanici_adi")
            upw   = st.text_input("Şifre", type="password", key="li_pw", placeholder="••••••••")
            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

            if st.button("Giriş Yap", use_container_width=True, key="btn_login"):
                athletes = db.get_all_athletes()
                match = next((a for a in athletes
                              if a.get("username") == uname
                              and a.get("password_hash") == hash_pw(upw)), None)
                if match:
                    st.session_state.logged_in    = True
                    st.session_state.is_admin     = False
                    st.session_state.athlete_id   = match["id"]
                    st.session_state.athlete_name = match["name"]
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı.")

        # ── KULLANICI KAYDI ───────────────────────────────────────────────────
        with tab_r:
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
            r_name  = st.text_input("Ad Soyad",      key="reg_name",  placeholder="Ali Yılmaz")
            r_user  = st.text_input("Kullanıcı Adı", key="reg_user",  placeholder="ali_yilmaz")
            r_pw    = st.text_input("Şifre",  type="password", key="reg_pw",  placeholder="En az 6 karakter")
            r_pw2   = st.text_input("Şifre Tekrar", type="password", key="reg_pw2", placeholder="••••••••")
            r_age   = st.number_input("Yaş", 10, 80, 22, key="reg_age")
            r_sport = st.selectbox("Spor Dalı",
                ["Fitness","Basketbol","Futbol","Yüzme","Atletizm","Diğer"], key="reg_sport")
            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

            if st.button("Hesap Oluştur", use_container_width=True, key="btn_reg"):
                if not r_name or not r_user or not r_pw:
                    st.error("Tüm alanları doldurun.")
                elif r_pw != r_pw2:
                    st.error("Şifreler eşleşmiyor.")
                elif len(r_pw) < 6:
                    st.error("Şifre en az 6 karakter olmalı.")
                else:
                    existing = db.get_all_athletes()
                    if any(a.get("username") == r_user for a in existing):
                        st.error("Bu kullanıcı adı zaten alınmış.")
                    else:
                        aid = db.create_athlete(r_name, r_age, r_sport,
                                                username=r_user,
                                                password_hash=hash_pw(r_pw))
                        st.session_state.logged_in    = True
                        st.session_state.is_admin     = False
                        st.session_state.athlete_id   = aid
                        st.session_state.athlete_name = r_name
                        st.rerun()

        # ── ADMİN GİRİŞİ ─────────────────────────────────────────────────────
        with tab_a:
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
            st.markdown("<div style='color:#8b949e;font-size:.85rem;margin-bottom:.8rem'>Admin şifresi ile giriş yapın.</div>", unsafe_allow_html=True)
            admin_pw = st.text_input("Admin Şifresi", type="password", key="admin_pw", placeholder="••••••••")

            if st.button("Admin Girişi", use_container_width=True, key="btn_admin"):
                if admin_pw == ADMIN_PASSWORD:
                    st.session_state.logged_in    = True
                    st.session_state.is_admin     = True
                    st.session_state.athlete_name = "Admin"
                    st.rerun()
                else:
                    st.error("Yanlış şifre.")

    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# ADMİN PANELİ
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.is_admin:
    import pandas as pd

    with st.sidebar:
        st.markdown("""
        <div style="background:#161b22;border:1px solid #f85149;border-radius:10px;
             padding:.9rem 1rem;margin-bottom:1.2rem;">
            <div style="font-weight:700;color:#f85149;font-size:1rem;">🔐 Admin Paneli</div>
            <div style="font-size:.75rem;color:#8b949e;margin-top:2px;">Tam yetki</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            for k in defaults: st.session_state[k] = defaults[k]
            st.rerun()

    st.markdown("## 🔐 Admin Paneli")
    st.markdown("---")

    athletes = db.get_all_athletes()
    sessions = db.get_recent_sessions(100)

    # Özet kartlar
    c1, c2, c3 = st.columns(3)
    c1.metric("👤 Toplam Kullanıcı",  len(athletes))
    c2.metric("🎯 Toplam Seans",      len(sessions))
    avg = sum(s.get("score",0) for s in sessions)/len(sessions) if sessions else 0
    c3.metric("📊 Genel Ortalama Skor", f"{avg:.1f}")

    st.markdown("---")

    # Kullanıcı listesi
    st.markdown("### 👥 Kayıtlı Kullanıcılar")
    if athletes:
        df_users = pd.DataFrame(athletes)[["id","name","username","age","sport","created_at"]].copy()
        df_users.columns = ["ID","Ad Soyad","Kullanıcı Adı","Yaş","Spor","Kayıt Tarihi"]
        st.dataframe(df_users, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz kayıtlı kullanıcı yok.")

    st.markdown("---")

    # Kullanıcı detayı
    st.markdown("### 📊 Kullanıcı Detayı")
    if athletes:
        selected = st.selectbox(
            "Kullanıcı seç",
            options=[a["id"] for a in athletes],
            format_func=lambda x: next((a["name"] for a in athletes if a["id"]==x), "")
        )
        if selected:
            stats    = db.get_athlete_stats(selected)
            history  = db.get_score_history(selected)
            sessions_u = db.get_sessions_by_athlete(selected)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ortalama Skor",  f"{stats.get('average_score',0):.1f}")
            c2.metric("En İyi Skor",    f"{stats.get('best_score',0):.1f}")
            c3.metric("Toplam Seans",   stats.get("total_sessions",0))
            c4.metric("Toplam Tekrar",  stats.get("total_reps",0))

            if sessions_u:
                df_s = pd.DataFrame(sessions_u)[["date","exercise_type","score","duration_sec"]].copy()
                df_s.columns = ["Tarih","Egzersiz","Skor","Süre (sn)"]
                df_s["Skor"] = df_s["Skor"].round(1)
                st.dataframe(df_s.head(20), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Kullanıcı sil
    st.markdown("### 🗑️ Kullanıcı Sil")
    if athletes:
        del_id = st.selectbox(
            "Silinecek kullanıcı",
            options=[a["id"] for a in athletes],
            format_func=lambda x: next((f"{a['name']} (@{a.get('username','?')})" for a in athletes if a["id"]==x), ""),
            key="del_select"
        )
        if st.button("🗑️ Kullanıcıyı Sil", type="primary"):
            db.delete_athlete(del_id)
            st.success("Kullanıcı silindi.")
            st.rerun()

    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# NORMAL KULLANICI SAYFASI
# ═══════════════════════════════════════════════════════════════════════════════
athlete_id   = st.session_state.athlete_id
athlete_name = st.session_state.athlete_name
athlete      = db.get_athlete(athlete_id) or {}

with st.sidebar:
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #1e2736;border-radius:10px;
         padding:.9rem 1rem;margin-bottom:1.2rem;">
        <div style="font-weight:600;color:#e6edf3;font-size:.95rem;">⚡ AthleteIQ</div>
        <div style="font-weight:500;color:#c9d1d9;margin-top:4px;">👤 {athlete_name}</div>
        <div style="font-size:.75rem;color:#8b949e;margin-top:2px;">
            {athlete.get('sport','—')} · {athlete.get('age','?')} yaş
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🏋️ Egzersiz")
    exercise_mode = st.selectbox("Egzersiz", ["auto","squat","pushup","lunge","plank"],
        format_func=lambda x: {"auto":"🤖 Otomatik","squat":"🦵 Squat",
                               "pushup":"💪 Push-Up","lunge":"🚶 Lunge","plank":"🏄 Plank"}.get(x,x))
    language = st.radio("Dil", ["tr","en"],
                        format_func=lambda x: "🇹🇷 Türkçe" if x=="tr" else "🇬🇧 English",
                        horizontal=True)
    st.divider()
    source_type = st.radio("📹 Kaynak", ["Webcam","Video Dosyası"])
    video_file  = None
    if source_type == "Video Dosyası":
        video_file = st.file_uploader("Video Yükle", type=["mp4","avi","mov"])

    if st.session_state.last_data:
        st.divider()
        ang = st.session_state.last_data.get("angles",{})
        st.markdown("**📐 Eklem Açıları**")
        for k,lbl in [("left_knee","Sol Diz"),("right_knee","Sağ Diz"),
                      ("left_elbow","Sol Dirsek"),("right_elbow","Sağ Dirsek")]:
            if k in ang: st.metric(lbl, f"{ang[k]:.0f}°")

    st.divider()
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        for k in defaults: st.session_state[k] = defaults[k]
        st.rerun()

tab_live, tab_dash, tab_rep = st.tabs(["⚡ Canlı Analiz","📊 Dashboard","📄 Raporlar"])

# ── CANLI ANALİZ ──────────────────────────────────────────────────────────────
with tab_live:
    st.markdown(f"### Hoş geldin, **{athlete_name}** 👋")
    col_vid, col_panel = st.columns([3,1])

    with col_vid:
        b1, b2 = st.columns(2)
        with b1:
            start_btn = st.button("▶ Analizi Başlat",
                disabled=st.session_state.session_active,
                use_container_width=True, type="primary")
        with b2:
            stop_btn = st.button("⏹ Durdur & Kaydet",
                disabled=not st.session_state.session_active,
                use_container_width=True)

        if start_btn:
            svc = AnalyticsService(language=language)
            svc.start_session(athlete_name, exercise_mode,
                              age=athlete.get("age"), sport=athlete.get("sport"))
            st.session_state.service        = svc
            st.session_state.session_active = True
            st.session_state.session_summary = None
            st.rerun()

        if stop_btn and st.session_state.service:
            summary = st.session_state.service.end_session()
            st.session_state.service.close()
            st.session_state.service        = None
            st.session_state.session_active = False
            st.session_state.session_summary = summary
            st.rerun()

        if st.session_state.session_summary:
            s = st.session_state.session_summary
            st.success(f"✅ Seans bitti! Skor: **{s['average_score']}** · Tekrar: **{s['total_reps']}** · Süre: **{s['duration_sec']:.0f} sn**")

        frame_ph = st.empty()

        if st.session_state.session_active and st.session_state.service:
            import tempfile, os
            if source_type == "Video Dosyası" and video_file:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tfile.write(video_file.read())
                cap = cv2.VideoCapture(tfile.name)
            else:
                cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            st.session_state.service.rep_counter.set_fps(fps)

            while st.session_state.session_active:
                ret, frame = cap.read()
                if not ret: break
                annotated, data = st.session_state.service.process_frame(frame)
                st.session_state.last_data = data
                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_ph.image(rgb, channels="RGB")
                time.sleep(0.033)
            cap.release()
        else:
            frame_ph.markdown("""
            <div style="background:#0d1117;border:1px solid #1e2736;border-radius:12px;
                 min-height:320px;display:flex;align-items:center;justify-content:center;">
                <div style="text-align:center;color:#30363d;padding:3rem;">
                    <div style="font-size:3rem;margin-bottom:.75rem">📷</div>
                    <p style="font-size:.9rem">Başlatmak için ▶ butonuna tıkla</p>
                </div>
            </div>""", unsafe_allow_html=True)

    with col_panel:
        st.markdown("#### 📈 Anlık Durum")
        if st.session_state.last_data:
            d  = st.session_state.last_data
            sc = d.get("score",{})
            total = sc.get("total",0)
            cls = "score-high" if total>=70 else "score-mid" if total>=45 else "score-low"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Egzersiz</div>
                <div class="metric-value" style="font-size:1.3rem">{d.get('exercise','—').upper()}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Tekrar</div>
                <div class="metric-value">{d.get('reps',0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Performans Skoru</div>
                <div class="metric-value {cls}">{total:.0f}<span style="font-size:.8rem;color:#8b949e">/100</span></div>
            </div>""", unsafe_allow_html=True)

            for k,lbl in [("posture","Duruş"),("range","Hareket"),("stability","Denge"),("symmetry","Simetri")]:
                v = sc.get(k,0)
                c = "#3fb950" if v>=70 else "#d29922" if v>=45 else "#f85149"
                st.markdown(f"""
                <div style="margin-bottom:.5rem">
                    <div style="display:flex;justify-content:space-between;font-size:.75rem;color:#8b949e;margin-bottom:3px">
                        <span>{lbl}</span><span>{v:.0f}</span>
                    </div>
                    <div style="background:#1e2736;border-radius:4px;height:5px">
                        <div style="width:{v}%;background:{c};height:5px;border-radius:4px"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown("#### 💬 Geri Bildirim")
            for fb in d.get("feedback",[])[:3]:
                p = fb["priority"]
                css = "fb-green" if p==3 else "fb-yellow" if p==2 else "fb-red"
                st.markdown(f'<div class="fb-pill {css}">{fb["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#586069;font-size:.85rem'>Seans başladığında burada görünecek.</div>", unsafe_allow_html=True)

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
with tab_dash:
    import plotly.express as px
    import pandas as pd

    stats   = db.get_athlete_stats(athlete_id)
    history = db.get_score_history(athlete_id)
    sessions= db.get_sessions_by_athlete(athlete_id)

    st.markdown(f"### {athlete_name} – Performans Panosu")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Ortalama Skor", f"{stats.get('average_score',0):.1f}")
    c2.metric("En İyi Skor",   f"{stats.get('best_score',0):.1f}")
    c3.metric("Toplam Seans",  stats.get("total_sessions",0))
    c4.metric("Toplam Tekrar", stats.get("total_reps",0))

    if history:
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])
        fig = px.line(df, x="date", y="score", color="exercise_type",
                      template="plotly_dark", markers=True,
                      labels={"date":"Tarih","score":"Skor","exercise_type":"Egzersiz"})
        fig.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                          font_color="#c9d1d9", yaxis_range=[0,105],
                          margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Henüz seans verisi yok.")

    if sessions:
        st.markdown("#### Son Seanslar")
        df2 = pd.DataFrame(sessions)[["date","exercise_type","score","duration_sec"]].copy()
        df2.columns = ["Tarih","Egzersiz","Skor","Süre (sn)"]
        df2["Skor"] = df2["Skor"].round(1)
        st.dataframe(df2.head(10), use_container_width=True, hide_index=True)

# ── RAPORLAR ──────────────────────────────────────────────────────────────────
with tab_rep:
    st.markdown("### Rapor Oluştur")
    sessions = db.get_sessions_by_athlete(athlete_id)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### 📁 CSV İndir")
        if st.button("CSV Oluştur", use_container_width=True):
            path = report.export_sessions_csv(sessions, athlete_name)
            if path:
                with open(path,"rb") as f:
                    st.download_button("⬇️ İndir", f.read(),
                        file_name=path.split("\\")[-1].split("/")[-1],
                        mime="text/csv", use_container_width=True)
            else:
                st.warning("Önce bir seans tamamla.")
    with c2:
        st.markdown("#### 📈 Grafik")
        if st.button("Grafik Oluştur", use_container_width=True):
            h = db.get_score_history(athlete_id)
            p = report.plot_score_history(h, athlete_name)
            if p:
                st.image(p)
            else:
                st.warning("Önce bir seans tamamla.")
