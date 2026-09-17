"""
Módulo de conexión y sincronización con STAAD.Pro vía OpenSTAAD para el Catálogo de Conceptos.
Permite consultar en tiempo real las propiedades y perfiles asignados por el calculista.
"""

import os
import math

def get_staad_connection():
    """
    Intenta conectarse a la sesión activa de STAAD.Pro usando openstaad.
    Retorna (session, filename, status_dict).
    """
    try:
        from openstaad import ops
        s = ops.connect()
        filename = s.GetSTAADFile()
        if not filename:
            return None, None, {"status": "disconnected", "error": "No hay ningún archivo abierto en STAAD.Pro"}
        return s, os.path.basename(filename), {"status": "connected", "filename": os.path.basename(filename), "error": None}
    except Exception as e:
        return None, None, {"status": "disconnected", "error": str(e)}

def get_member_profile_from_staad(session, member_id: int):
    """
    Obtiene el nombre del perfil de un miembro dado en STAAD.Pro.
    """
    if not session:
        return None
    try:
        prop = session.property
        name = prop.GetBeamSectionName(member_id)
        if name:
            return str(name).strip()
    except Exception:
        pass
    return None

def sync_profiles_from_staad(model, session=None):
    """
    Sincroniza los perfiles del modelo STAAD.Pro activo hacia un diccionario de grupos y miembros.
    Retorna un diccionario con los perfiles detectados por grupo y por miembro.
    """
    if session is None:
        session, _, status = get_staad_connection()
        if status["status"] != "connected":
            return {"status": "error", "message": status["error"], "profiles_by_group": {}, "profiles_by_member": {}}

    profiles_by_member = {}
    profiles_by_group = {}

    try:
        prop = session.property
        # Sincronizar miembros del modelo
        for m_id in model.members.keys():
            try:
                sec_name = prop.GetBeamSectionName(int(m_id))
                if sec_name:
                    profiles_by_member[m_id] = str(sec_name).strip()
            except Exception:
                continue

        # Agrupar perfiles dominantes por grupos del modelo
        for g_name, m_ids in model.groups.items():
            found_profiles = {}
            for mid in m_ids:
                p_name = profiles_by_member.get(mid)
                if p_name:
                    found_profiles[p_name] = found_profiles.get(p_name, 0) + 1
            if found_profiles:
                top_p = max(found_profiles, key=found_profiles.get)
                profiles_by_group[g_name] = top_p

        return {
            "status": "success",
            "message": f"Sincronizados {len(profiles_by_member)} miembros desde STAAD.Pro",
            "profiles_by_group": profiles_by_group,
            "profiles_by_member": profiles_by_member
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error leyendo perfiles de STAAD: {e}",
            "profiles_by_group": {},
            "profiles_by_member": {}
        }

def get_member_length(model, member_id):
    """Calcula la longitud en metros de un miembro del modelo."""
    if member_id not in model.members:
        return 0.0
    n1, n2 = model.members[member_id]
    x1, y1, z1 = model.nodes[n1]
    x2, y2, z2 = model.nodes[n2]
    # Coordenadas están en cm en StaadModel
    dx = (x2 - x1) / 100.0
    dy = (y2 - y1) / 100.0
    dz = (z2 - z1) / 100.0
    return math.sqrt(dx * dx + dy * dy + dz * dz)
