import os
import sys
import win32com.client

def create_desktop_shortcuts():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = shell.SpecialFolders("Desktop")
    
    python_exe = sys.executable
    pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = python_exe

    # 1. Acceso Directo: FrameOne StandAlone
    runner_script = os.path.join(base_dir, "Ejecutable", "desktop_runner.py")
    frameone_icon = os.path.join(base_dir, "FrameOne.ico")
    shortcut_client = os.path.join(desktop, "FrameOne StandAlone.lnk")
    
    sc1 = shell.CreateShortCut(shortcut_client)
    sc1.TargetPath = pythonw_exe
    sc1.Arguments = f'"{runner_script}"'
    sc1.WorkingDirectory = os.path.join(base_dir, "Ejecutable")
    sc1.IconLocation = frameone_icon
    sc1.Description = "FrameOne - Modelado de Naves Industriales para STAAD.Pro"
    sc1.save()
    print(f"[OK] Creado: {shortcut_client} (Icono: FrameOne.ico)")

    # 2. Acceso Directo: FrameOne Admin Panel (Ejecutable Nativo)
    admin_script = os.path.join(base_dir, "admin_runner.py")
    degradado_icon = os.path.join(base_dir, "Degradado_1.ico")
    shortcut_admin = os.path.join(desktop, "FrameOne Admin Panel.lnk")
    
    sc2 = shell.CreateShortCut(shortcut_admin)
    sc2.TargetPath = pythonw_exe
    sc2.Arguments = f'"{admin_script}"'
    sc2.WorkingDirectory = base_dir
    sc2.IconLocation = degradado_icon
    sc2.Description = "FrameOne - Panel de Control de Licencias"
    sc2.save()
    print(f"[OK] Creado: {shortcut_admin} (Icono: Degradado_1.ico)")

if __name__ == "__main__":
    create_desktop_shortcuts()
