import os
import socket
import hashlib
import subprocess

def _run_ps_command(cmd: str) -> str:
    """Ejecuta un comando de PowerShell silenciosamente sin ventana de consola."""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=5,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return result.stdout.strip()
    except Exception:
        return ""

def get_system_uuid() -> str:
    """Obtiene el UUID único de la placa madre del equipo."""
    uuid = _run_ps_command("(Get-CimInstance Win32_ComputerSystemProduct).UUID")
    if not uuid or uuid.lower() in ["ffffffff-ffff-ffff-ffff-ffffffffffff", "00000000-0000-0000-0000-000000000000"]:
        # Fallback a wmic si existe
        uuid = _run_ps_command("wmic csproduct get uuid")
        lines = [line.strip() for line in uuid.splitlines() if line.strip() and "UUID" not in line.upper()]
        uuid = lines[0] if lines else ""
    return uuid

def get_cpu_id() -> str:
    """Obtiene el identificador del procesador."""
    return _run_ps_command("(Get-CimInstance Win32_Processor | Select-Object -First 1).ProcessorId")

def get_disk_serial() -> str:
    """Obtiene el número de serie del disco duro principal."""
    return _run_ps_command("(Get-CimInstance Win32_DiskDrive | Select-Object -First 1).SerialNumber")

def get_computer_name() -> str:
    """Obtiene el nombre de la computadora en la red."""
    name = os.environ.get("COMPUTERNAME")
    if not name:
        try:
            name = socket.gethostname()
        except Exception:
            name = "PC-DESCONOCIDA"
    return name.strip()

def get_hardware_id() -> str:
    """
    Genera un hash SHA-256 único e inmutable basado en el hardware físico de la PC.
    Combina: UUID de placa madre + ID de procesador + Serie de disco duro.
    """
    uuid = get_system_uuid()
    cpu = get_cpu_id()
    disk = get_disk_serial()
    
    # Combinar los componentes físicos
    raw_fingerprint = f"{uuid}_{cpu}_{disk}"
    
    # Si por alguna razón de permisos WMI fallaron todos, usar nombre de máquina y arquitectura como salvavidas
    if raw_fingerprint.strip("_") == "":
        raw_fingerprint = f"{get_computer_name()}_{os.environ.get('PROCESSOR_IDENTIFIER', 'ARCH')}"
        
    hwid_hash = hashlib.sha256(raw_fingerprint.encode("utf-8")).hexdigest()
    return hwid_hash

if __name__ == "__main__":
    print("Nombre del equipo:", get_computer_name())
    print("UUID Placa:", get_system_uuid())
    print("CPU ID:", get_cpu_id())
    print("Disco Serial:", get_disk_serial())
    print("HWID Hash (SHA-256):", get_hardware_id())
