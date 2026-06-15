# 🏋️ AI Destekli Gerçek Zamanlı Spor Performans Analiz Sistemi

> Bilgisayar Mühendisliği Bitirme Projesi  
> MediaPipe · OpenCV · Streamlit · SQLite

---

## 📌 Proje Özeti

Bu sistem, bir webcam veya yüklenen video aracılığıyla sporcuların vücut hareketlerini
gerçek zamanlı olarak analiz eden, yapay zeka destekli bir performans takip platformudur.

**Temel Özellikler:**
- 🤖 MediaPipe ile gerçek zamanlı poz (pose) tespiti
- 📐 6 eklem açısı hesaplama (diz, dirsek, kalça, omuz)
- 🏋️ 4 egzersiz tanıma: Squat, Push-Up, Lunge, Plank
- 🔁 Otomatik tekrar (repetition) sayacı
- 🎯 0-100 aralığında performans skoru
- 💬 Türkçe/İngilizce anlık form geri bildirimi
- 📊 Streamlit tabanlı performans panosu
- 🗄️ SQLite ile sporcu ve seans geçmişi

---

## 📁 Klasör Yapısı

```
SportsPerformanceAnalytics/
│
├── app.py                      # Ana Streamlit uygulaması
├── requirements.txt            # Python bağımlılıkları
├── database.db                 # SQLite veritabanı (otomatik oluşturulur)
│
├── models/                     # Çekirdek AI modelleri
│   ├── pose_detector.py        # MediaPipe Pose entegrasyonu
│   ├── angle_calculator.py     # Eklem açısı hesaplayıcı
│   ├── exercise_recognizer.py  # Egzersiz tanıma motoru
│   ├── rep_counter.py          # Tekrar sayacı
│   ├── performance_scorer.py   # Performans skoru (0-100)
│   └── feedback_generator.py  # Gerçek zamanlı form geri bildirimi
│
├── services/
│   └── analytics_service.py   # Tüm pipeline'ı koordine eden ana servis
│
├── database/
│   └── database_manager.py    # SQLite CRUD işlemleri
│
├── dashboard/
│   └── dashboard_manager.py   # Streamlit bileşenleri
│
├── utils/
│   ├── video_processor.py     # Webcam/video akış yönetimi
│   └── report_generator.py    # CSV ve grafik raporu
│
├── reports/                   # Üretilen raporlar (CSV, PNG)
├── results/                   # Ek çıktılar
├── assets/                    # Görseller ve statik dosyalar
└── tests/                     # Unit testler
    ├── test_angle_calculator.py
    ├── test_rep_counter.py
    └── test_database.py
```

---

## ⚙️ Kurulum

### 1. Python Ortamı Oluştur

```bash
# Python 3.12 ile sanal ortam oluştur
python -m venv venv

# Aktifleştir (Windows)
venv\Scripts\activate

# Aktifleştir (macOS / Linux)
source venv/bin/activate
```

### 2. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 3. Uygulamayı Başlat

```bash
streamlit run app.py
```

Tarayıcı otomatik olarak `http://localhost:8501` adresini açar.

---

## 🚀 Kullanım

1. **Sol panelden (Sidebar)** sporcu adı, yaş ve spor dalını girin
2. Egzersiz tipini seçin veya **"Otomatik Tespit"** bırakın
3. **"▶️ Analizi Başlat"** butonuna tıklayın
4. Kameraya karşı egzersizinizi yapın
5. Sistem şunları gerçek zamanlı gösterir:
   - İskelet bağlantıları (yeşil)
   - Eklem açıları (derece)
   - Tekrar sayısı
   - Performans skoru (0-100)
   - Form geri bildirimi
6. **"⏹️ Durdur & Kaydet"** ile seansı bitirin
7. **"📊 Dashboard"** sekmesinden gelişiminizi takip edin
8. **"📄 Raporlar"** sekmesinden CSV veya grafik raporu indirin

---

## 🧪 Testleri Çalıştırma

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Belirli bir test dosyası
python -m pytest tests/test_angle_calculator.py -v
```

---

## 🏗️ Mimari

```
Webcam/Video
     │
     ▼
PoseDetector (MediaPipe)
     │  landmarks
     ▼
AngleCalculator
     │  açılar
     ├──► ExerciseRecognizer  ──► egzersiz tipi
     ├──► RepCounter          ──► tekrar sayısı
     ├──► PerformanceScorer   ──► 0-100 skor
     └──► FeedbackGenerator   ──► form mesajları
                │
                ▼
         DatabaseManager (SQLite)
                │
                ▼
        DashboardManager (Streamlit)
```

---

## 🏆 Performans Skoru Kriterleri

| Kriter | Ağırlık | Açıklama |
|---|---|---|
| Duruş (Posture) | %30 | Doğru vücut hizası |
| Hareket Genişliği (Range) | %30 | Tam ROM tamamlama |
| Denge (Stability) | %20 | Hareketler arası tutarlılık |
| Simetri (Symmetry) | %20 | Sol/sağ denge |

---

## 📚 Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Poz Tespiti | MediaPipe 0.10.9 |
| Görüntü İşleme | OpenCV 4.9 |
| Sayısal Hesaplama | NumPy 1.26 |
| Veri Analizi | Pandas 2.2 |
| Web Arayüzü | Streamlit 1.32 |
| Görselleştirme | Plotly 5.20, Matplotlib 3.8 |
| Veritabanı | SQLite (yerleşik) |
| Dil | Python 3.12 |

---

## 👨‍💻 Geliştirici Notları

- Tüm sınıflar SOLID prensiplerine göre tasarlanmıştır
- Her modül bağımsız olarak test edilebilir
- `AnalyticsService`, bağımlılıkları enjekte ederek koordine eder
- Veritabanı yabancı anahtar kısıtlamaları aktif edilmiştir
- `ReportGenerator` GUI gerektirmeden (headless) PNG üretir

---

## 📝 Lisans

Bu proje akademik kullanım amacıyla geliştirilmiştir.
