import os
from PIL import Image

ico_path = os.path.expandvars(r"%LOCALAPPDATA%\blank_shortcut.ico")
img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
img.save(ico_path, format='ICO')

bat_quitar = r"""@echo off
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
"""

with open(r"c:\Users\josee\OneDrive\Escritorio\AG - Modelado STAAD\Quitar_Flechas.bat", "w", encoding="utf-8") as f:
    f.write(bat_quitar)


bat_restaurar = r"""@echo off
title Restaurar Flechas de Accesos Directos
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
echo Restaurando el Registro de Windows...
REG DELETE "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 29 /f

echo.
echo Reiniciando el Explorador de Windows para aplicar los cambios...
taskkill /f /im explorer.exe
start explorer.exe

echo.
echo ¡Listo! Las flechas han vuelto a la normalidad.
pause
"""

with open(r"c:\Users\josee\OneDrive\Escritorio\AG - Modelado STAAD\Restaurar_Flechas.bat", "w", encoding="utf-8") as f:
    f.write(bat_restaurar)

print("Archivos generados con exito.")
