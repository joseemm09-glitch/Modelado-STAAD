@echo off
echo Compilando FrameOne StandAlone...
pyinstaller --noconfirm --windowed --name "FrameOne StandAlone" --icon="..\FrameOne.ico" desktop_runner.py
echo.
echo Compilacion terminada. El ejecutable esta en la carpeta dist\FrameOne StandAlone\
echo.
echo Creando acceso directo en el escritorio...
python create_shortcut.py
echo Todo listo!
pause
