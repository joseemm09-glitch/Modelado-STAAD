import json
import requests
from typing import Dict, Any, Optional

from security.config import SUPABASE_URL, SUPABASE_ANON_KEY
from security.hwid import get_hardware_id, get_computer_name

class LicenseClient:
    """
    Cliente seguro de comunicación con el backend de Supabase.
    Invoca los procedimientos almacenados (RPC) con la clave pública anon.
    """
    def __init__(self, url: Optional[str] = None, anon_key: Optional[str] = None):
        self.url = (url or SUPABASE_URL).rstrip("/")
        self.anon_key = anon_key or SUPABASE_ANON_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
            "Content-Type": "application/json"
        })

    def _call_rpc(self, function_name: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        """Realiza una petición POST segura al endpoint RPC de Supabase."""
        endpoint = f"{self.url}/rest/v1/rpc/{function_name}"
        try:
            response = self.session.post(endpoint, json=payload, timeout=timeout)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                try:
                    err_data = response.json()
                    msg = err_data.get("message") or err_data.get("error") or response.text
                except Exception:
                    msg = response.text
                return {
                    "success": False,
                    "error_code": f"HTTP_{response.status_code}",
                    "error_message": f"Error del servidor ({response.status_code}): {msg}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error_code": "NETWORK_ERROR",
                "error_message": "No se pudo conectar con el servidor de licencias. Verifique su conexión a Internet."
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error_code": "TIMEOUT_ERROR",
                "error_message": "El servidor de licencias tardó demasiado en responder."
            }
        except Exception as e:
            return {
                "success": False,
                "error_code": "UNKNOWN_ERROR",
                "error_message": f"Error inesperado de comunicación: {str(e)}"
            }

    def login_and_acquire_seat(self, correo: str, password: str) -> Dict[str, Any]:
        """
        Valida las credenciales, verifica el HWID y solicita un asiento flotante.
        """
        hwid = get_hardware_id()
        pc_name = get_computer_name()

        payload = {
            "p_correo": correo.strip(),
            "p_password": password.strip(),
            "p_hwid": hwid,
            "p_pc_name": pc_name
        }
        return self._call_rpc("login_and_acquire_seat", payload, timeout=12)

    def heartbeat(self, token: str) -> Dict[str, Any]:
        """
        Envía un pulso de latido cada 90-120 segundos para mantener el asiento activo.
        """
        payload = {"p_token": token}
        return self._call_rpc("heartbeat", payload, timeout=8)

    def release_seat(self, token: str) -> Dict[str, Any]:
        """
        Libera inmediatamente el asiento flotante al cerrar el programa.
        """
        payload = {"p_token": token}
        return self._call_rpc("release_seat", payload, timeout=6)
