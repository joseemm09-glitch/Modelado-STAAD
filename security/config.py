# ==============================================================================
# CONFIGURACIÓN DE CONEXIÓN CON SUPABASE (FREE TIER)
# ==============================================================================
# IMPORTANTE: 
# En el cliente de escritorio SOLAMENTE se utiliza la clave pública / publishable (SUPABASE_ANON_KEY).
# NUNCA incluyas la clave secret en el código del cliente distribuible.
# Toda la seguridad y validaciones se ejecutan del lado del servidor en las funciones RPC.
# ==============================================================================

import os

SUPABASE_URL = os.environ.get("FRAMEONE_SUPABASE_URL", "https://btqnxkqmvjilwcnmqaki.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("FRAMEONE_SUPABASE_ANON_KEY", "sb_publishable__VzhxfRFtrn4quzaRMRRog_I8vB6ayF")

# Clave secreta (solo para uso en el panel de administración privado o backend maestro)
SUPABASE_SECRET_KEY = os.environ.get("FRAMEONE_SUPABASE_SECRET_KEY", "sb_secret_Ek-Nc5lzbzQeNgX0Ue9qjw_AHTW0r0l")

# Configuración de latido (Heartbeat)
HEARTBEAT_INTERVAL_SECONDS = 90      # Enviar latido cada 90 segundos (1.5 min)
SESSION_EXPIRATION_MINUTES = 4       # El servidor libera el asiento tras 4 minutos sin latido
