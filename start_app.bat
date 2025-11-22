@echo off
:: Pindah ke directory di mana file .bat ini berada (biar aman)
cd /d "%~dp0"

:: Cek dulu, venv-nya udah ada belum?
if exist "quick_health\Scripts\activate.bat" (
    echo [INFO] Venv udah ada, langsung gass run...
    goto RUN_APP
)

:: Kalo belum ada, bikin dulu bos
echo [INFO] Venv belum ada. Otw bikin venv & install requirements...
python -m venv quick_health

:: Aktifin venv (pake CALL biar script gak mati)
call "quick_health\Scripts\activate.bat"

:: Install library
echo [INFO] Install dependencies...
pip install -r requirements.txt

:: Langsung loncat ke run
goto RUN_APP

:RUN_APP
:: Pastikan venv aktif sebelum run streamlit
call "quick_health\Scripts\activate.bat"

echo [INFO] Menjalankan Streamlit...
streamlit run QuickHealth-9.py

:: Pause biar kalo error window-nya gak langsung nutup, jadi lo bisa baca errornya
pause