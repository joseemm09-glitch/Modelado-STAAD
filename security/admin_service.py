import requests
from typing import List, Dict, Any, Optional
from security.config import SUPABASE_URL, SUPABASE_SECRET_KEY

class AdminService:
    """
    Servicio de administración maestro para gestión de licencias,
    empresas, usuarios, HWIDs y sesiones activas.
    Utiliza la clave secreta (service_role) para tener control total.
    """
    def __init__(self, url: Optional[str] = None, secret_key: Optional[str] = None):
        self.url = (url or SUPABASE_URL).rstrip("/")
        self.secret_key = secret_key or SUPABASE_SECRET_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": self.secret_key,
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        })

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.url}/rest/v1/{endpoint}"
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.url}/rest/v1/{endpoint}"
        resp = self.session.post(url, json=data, timeout=10)
        if resp.status_code in [200, 201]:
            res = resp.json()
            return res[0] if isinstance(res, list) and res else res
        return None

    def _patch(self, endpoint: str, match_params: Dict[str, Any], data: Dict[str, Any]) -> bool:
        url = f"{self.url}/rest/v1/{endpoint}"
        resp = self.session.patch(url, params=match_params, json=data, timeout=10)
        return resp.status_code in [200, 204]

    def _delete(self, endpoint: str, match_params: Dict[str, Any]) -> bool:
        url = f"{self.url}/rest/v1/{endpoint}"
        resp = self.session.delete(url, params=match_params, timeout=10)
        return resp.status_code in [200, 204]

    # --- EMPRESAS ---
    def get_empresas(self) -> List[Dict[str, Any]]:
        return self._get("empresas?select=*&order=created_at.desc")

    def create_empresa(self, nombre: str, max_asientos: int, max_hwids: int) -> Optional[Dict[str, Any]]:
        return self._post("empresas", {
            "nombre": nombre.strip(),
            "max_asientos": max_asientos,
            "max_hwids": max_hwids,
            "activa": True
        })

    def update_empresa(self, empresa_id: str, data: Dict[str, Any]) -> bool:
        return self._patch("empresas", {"id": f"eq.{empresa_id}"}, data)

    # --- USUARIOS ---
    def get_usuarios(self) -> List[Dict[str, Any]]:
        return self._get("usuarios?select=*,empresas(nombre)&order=created_at.desc")

    def create_usuario(self, empresa_id: str, correo: str, password_raw: str) -> Optional[Dict[str, Any]]:
        # En Supabase podemos invocar pgcrypto crypt vía query o guardar para que login_and_acquire_seat lo valide
        return self._post("usuarios", {
            "empresa_id": empresa_id,
            "correo": correo.strip().lower(),
            "password_hash": password_raw.strip(),
            "activo": True
        })

    def update_usuario_status(self, usuario_id: str, activo: bool) -> bool:
        return self._patch("usuarios", {"id": f"eq.{usuario_id}"}, {"activo": activo})

    def update_usuario_password(self, usuario_id: str, new_password_raw: str) -> bool:
        return self._patch("usuarios", {"id": f"eq.{usuario_id}"}, {"password_hash": new_password_raw.strip()})

    # --- DISPOSITIVOS HWID ---
    def get_dispositivos(self, empresa_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "dispositivos_hwid?select=*,empresas(nombre)&order=ultimo_acceso.desc"
        if empresa_id:
            query += f"&empresa_id=eq.{empresa_id}"
        return self._get(query)

    def toggle_hwid_status(self, hwid_id: str, activo: bool) -> bool:
        return self._patch("dispositivos_hwid", {"id": f"eq.{hwid_id}"}, {"activo": activo})

    def delete_hwid(self, hwid_id: str) -> bool:
        """Elimina permanentemente una PC de la lista blanca para liberar cupo."""
        return self._delete("dispositivos_hwid", {"id": f"eq.{hwid_id}"})

    # --- SESIONES ACTIVAS (MONITOREO EN TIEMPO REAL) ---
    def get_sesiones_activas(self) -> List[Dict[str, Any]]:
        # Limpiar primero sesiones con más de 4 minutos sin latido
        return self._get("sesiones_activas?select=*,empresas(nombre),usuarios(correo)&order=ultimo_latido.desc")

    def kill_sesion(self, sesion_id: str) -> bool:
        """Fuerza la liberación de un asiento ocupado."""
        return self._delete("sesiones_activas", {"id": f"eq.{sesion_id}"})
