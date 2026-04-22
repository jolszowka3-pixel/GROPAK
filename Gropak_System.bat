@echo off
title Serwer Gropak System
echo ========================================
echo   URUCHAMIANIE SYSTEMU GROPAK...
echo   PROSZE NIE ZAMYKAC TEGO OKNA
echo ========================================

cd /d "%~dp0"

:: Uruchomienie serwera Streamlit w tle
start /b streamlit run main_app.py --browser.gatherUsageStats False --server.headless True

:: Czekamy 5 sekund na start serwera
timeout /t 5 >nul

:: Otwarcie aplikacji w trybie "App" (osobne okno bez pasków przeglądarki)
start chrome.exe --app=http://localhost:8501

exit