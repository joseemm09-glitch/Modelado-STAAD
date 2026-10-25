@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo   FRAMEONE STANDALONE - COMPILACION Y PROTECCION NATIVA (NUITKA)
echo =====================================================================
echo.

:: 1. Verificar si Nuitka esta instalado
python -c "import nuitka" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [1/3] Nuitka no esta instalado en el entorno de Python.
    echo Instalando Nuitka y dependencias de compilacion...
    pip install nuitka zstandard
) else (
    echo [1/3] Nuitka detectado correctamente.
)

:: 2. Compilar los modulos matematicos confidenciales a binarios C nativos (.pyd)
echo.
echo [2/3] Compilando modulos confidenciales (model, staad_writer, security) a C nativo...
python -m nuitka --module --remove-output --no-pyi-file "..\app\model.py"
python -m nuitka --module --remove-output --no-pyi-file "..\app\staad_writer.py"
python -m nuitka --module --remove-output --no-pyi-file "..\app\prediseno.py"
python -m nuitka --module --remove-output --no-pyi-file "..\security\client.py"
python -m nuitka --module --remove-output --no-pyi-file "..\security\hwid.py"

:: 3. Compilar el ejecutable principal desktop_runner.py
echo.
echo [3/3] Compilando ejecutable nativo FrameOne StandAlone.exe...
python -m nuitka --standalone --windows-disable-console --windows-icon-from-ico="..\FrameOne.ico" --output-filename="FrameOne StandAlone.exe" --output-dir="dist" desktop_runner.py

echo.
echo =====================================================================
echo   COMPILACION NATIVA EXITOSA!
echo   El ejecutable protegido esta en: dist\FrameOne StandAlone.dist\
echo =====================================================================
pause
