import os
import sys
import win32com.client

def create_desktop_shortcuts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = shell.SpecialFolders("Desktop")
    
    python_exe = sys.executable
    pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = python_exe

    # --- 1. Acceso Directo: FrameOne StandAlone (Cliente con Login) ---
    runner_script = os.path.join(base_dir, "Ejecutable", "desktop_runner.py")
    frameone_icon = os.path.join(base_dir, "FrameOne.ico")
    shortcut_client_path = os.path.join(desktop, "FrameOne StandAlone.lnk")
    
    sc_client = shell.CreateShortCut(shortcut_client_path)
    sc_client.TargetPath = pythonw_exe
    sc_client.Arguments = f'"{runner_script}"'
    sc_client.WorkingDirectory = os.path.join(base_dir, "Ejecutable")
    sc_client.IconLocation = frameone_icon
    sc_client.Description = "FrameOne - Modelado de Naves Industriales para STAAD.Pro"
    sc_client.save()
    print(f"[OK] Creado: {shortcut_client_path} (Icono: FrameOne.ico)")

    # --- 2. Acceso Directo: FrameOne Admin Panel (Ejecutable Nativo de Escritorio) ---
    admin_runner_script = os.path.join(base_dir, "admin_runner.py")
    degradado_icon = os.path.join(base_dir, "Degradado_1.ico")
    shortcut_admin_path = os.path.join(desktop, "FrameOne Admin Panel.lnk")
    
    sc_admin = shell.CreateShortCut(shortcut_admin_path)
    sc_admin.TargetPath = pythonw_exe
    sc_admin.Arguments = f'"{admin_runner_script}"'
    sc_admin.WorkingDirectory = base_dir
    sc_admin.IconLocation = degradado_icon
    sc_admin.Description = "FrameOne - Panel de Control de Licencias"
    sc_admin.save()
    print(f"[OK] Creado: {shortcut_admin_path} (Icono: Degradado_1.ico)")

if __name__ == "__main__":
    create_desktop_shortcuts()
