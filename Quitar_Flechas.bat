@echo off
title Quitar Flechas de Accesos Directos
echo Solicitando permisos de Administrador...
NET SESSION >nul 2>&1
if %errorLevel% NEQ 0 (
    echo =======================================================
    echo ERROR: Este archivo necesita permisos de Administrador.
    echo Por favor, cierralo, haz clic derecho sobre el archivo 
    echo y selecciona "Ejecutar como Administrador".
    echo =======================================================
    pause
    exit
)

echo.
echo Aplicando cambios en el Registro de Windows...
REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 29 /t REG_SZ /d "%LOCALAPPDATA%\blank_shortcut.ico,0" /f

echo.
echo Reiniciando el Explorador de Windows para aplicar los cambios...
taskkill /f /im explorer.exe
start explorer.exe

echo.
echo ¡Listo! Las flechas han sido eliminadas de tus accesos directos.
pause
