@echo off
title Sports Performance Analytics - Kurulum ve Baslat
color 0A

echo ============================================
echo  AI Spor Performans Analiz Sistemi
echo  Otomatik Kurulum ve Baslatma
echo ============================================
echo.

:: Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Lutfen python.org adresinden Python 3.12 indirin.
    echo https://www.python.org/downloads/
    pause
    exit
)

echo [1/4] Python bulundu.

:: Sanal ortam olustur (yoksa)
if not exist "venv" (
    echo [2/4] Sanal ortam olusturuluyor...
    python -m venv venv
) else (
    echo [2/4] Sanal ortam zaten mevcut.
)

:: Kutuphaneleri yukle
echo [3/4] Kutuphaneler yukleniyor (ilk kurulumda 3-5 dk surebilir)...
call venv\Scripts\activate
pip install -r requirements.txt --quiet

echo [4/4] Uygulama baslatiliyor...
echo.
echo Tarayici otomatik acilacak: http://localhost:8501
echo Kapatmak icin bu pencereyi kapatin.
echo.

streamlit run app.py

pause
