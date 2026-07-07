@echo off
cd /d "%~dp0"
echo Iniciando Streamlit...
python -m streamlit run app\main.py
pause
