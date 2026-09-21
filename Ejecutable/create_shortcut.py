import os
import sys

try:
    import winshell
    import win32com.client
except ImportError:
    print("Faltan dependencias. Instala winshell y pypiwin32.")
    sys.exit(1)

def create_desktop_shortcut():
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, "FrameOne StandAlone.lnk")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    target = pythonw
    runner_script = os.path.join(base_dir, "Ejecutable", "desktop_runner.py")
    
    icon_path = os.path.join(base_dir, "FrameOne.ico")
    
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.Arguments = f'"{runner_script}"'
    shortcut.WorkingDirectory = os.path.join(base_dir, "Ejecutable")
    shortcut.IconLocation = icon_path
    shortcut.save()
    
    print(f"Acceso directo creado con éxito en: {shortcut_path}")

if __name__ == "__main__":
    create_desktop_shortcut()
