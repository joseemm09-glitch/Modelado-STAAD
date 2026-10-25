-- ==============================================================================
-- FRAMEONE: SISTEMA DE GESTIÓN DE LICENCIAS FLOTANTES Y SEGURIDAD HWID
-- BASE DE DATOS: Supabase (PostgreSQL)
-- Costo: $0 Mensual Permanente (Supabase Free Tier)
-- ==============================================================================

-- 1. EXTENSIÓN PARA CRIPTOGRAFÍA Y UUIDs
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. TABLA: EMPRESAS
CREATE TABLE IF NOT EXISTS public.empresas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL UNIQUE,
    max_asientos INTEGER NOT NULL DEFAULT 1 CHECK (max_asientos > 0),
    max_hwids INTEGER NOT NULL DEFAULT 5 CHECK (max_hwids > 0),
    activa BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. TABLA: USUARIOS (Credenciales de acceso para ingenieros)
CREATE TABLE IF NOT EXISTS public.usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    correo TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. TABLA: DISPOSITIVOS HWID (Lista blanca de PCs autorizadas)
CREATE TABLE IF NOT EXISTS public.dispositivos_hwid (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    hwid_hash TEXT NOT NULL,
    nombre_equipo TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    registrado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultimo_acceso TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_empresa_hwid UNIQUE (empresa_id, hwid_hash)
);

-- 5. TABLA: SESIONES ACTIVAS (Control de concurrencia y Heartbeat)
CREATE TABLE IF NOT EXISTS public.sesiones_activas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
    hwid_hash TEXT NOT NULL,
    nombre_equipo TEXT NOT NULL,
    token_sesion TEXT NOT NULL UNIQUE,
    ultimo_latido TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    iniciada_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices de alto rendimiento para búsquedas y latidos
CREATE INDEX IF NOT EXISTS idx_sesiones_empresa_latido ON public.sesiones_activas (empresa_id, ultimo_latido);
CREATE INDEX IF NOT EXISTS idx_sesiones_token ON public.sesiones_activas (token_sesion);
CREATE INDEX IF NOT EXISTS idx_dispositivos_hwid ON public.dispositivos_hwid (hwid_hash);
CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON public.usuarios (correo);

-- ==============================================================================
-- 6. PROCEDIMIENTOS ALMACENADOS (RPC FUNCTIONS - SECURITY DEFINER)
-- Toda la lógica de negocio y seguridad corre en el servidor PostgreSQL
-- ==============================================================================

-- A. FUNCIÓN ATÓMICA: LOGIN, VALIDACIÓN HWID Y ASIGNACIÓN DE ASIENTO
CREATE OR REPLACE FUNCTION public.login_and_acquire_seat(
    p_correo TEXT,
    p_password TEXT,
    p_hwid TEXT,
    p_pc_name TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
    v_user RECORD;
    v_empresa RECORD;
    v_hwid_row RECORD;
    v_hwids_count INTEGER;
    v_active_seats INTEGER;
    v_current_session RECORD;
    v_token TEXT;
    v_ocupantes JSONB;
    v_pass_valid BOOLEAN := false;
BEGIN
    -- 1. Limpieza de sesiones huérfanas/inactivas (más de 4 minutos sin latido)
    DELETE FROM public.sesiones_activas
    WHERE ultimo_latido < NOW() - INTERVAL '4 minutes';

    -- 2. Validar existencia del usuario
    SELECT * INTO v_user
    FROM public.usuarios
    WHERE LOWER(TRIM(correo)) = LOWER(TRIM(p_correo));

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'error_code', 'INVALID_CREDENTIALS',
            'error_message', 'Correo o contraseña incorrectos.'
        );
    END IF;

    IF NOT v_user.activo THEN
        RETURN jsonb_build_object(
            'success', false,
            'error_code', 'USER_INACTIVE',
            'error_message', 'Esta cuenta de usuario ha sido desactivada.'
        );
    END IF;

    -- 3. Validar contraseña (soporta hash extensions.crypt o coincidencia directa)
    BEGIN
        IF v_user.password_hash = extensions.crypt(p_password, v_user.password_hash) OR v_user.password_hash = p_password THEN
            v_pass_valid := true;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        IF v_user.password_hash = p_password THEN
            v_pass_valid := true;
        END IF;
    END;

    IF NOT v_pass_valid THEN
        RETURN jsonb_build_object(
            'success', false,
            'error_code', 'INVALID_CREDENTIALS',
            'error_message', 'Correo o contraseña incorrectos.'
        );
    END IF;

    -- 4. Validar estado de la empresa
    SELECT * INTO v_empresa
    FROM public.empresas
    WHERE id = v_user.empresa_id;

    IF NOT FOUND OR NOT v_empresa.activa THEN
        RETURN jsonb_build_object(
            'success', false,
            'error_code', 'COMPANY_INACTIVE',
            'error_message', 'La suscripción de la empresa no se encuentra activa.'
        );
    END IF;

    -- 5. Validar Lista Blanca de Hardware (HWID Whitelist)
    SELECT * INTO v_hwid_row
    FROM public.dispositivos_hwid
    WHERE empresa_id = v_empresa.id AND hwid_hash = p_hwid;

    IF FOUND THEN
        -- El equipo ya está registrado previamente
        IF NOT v_hwid_row.activo THEN
            RETURN jsonb_build_object(
                'success', false,
                'error_code', 'HWID_REVOKED',
                'error_message', 'Este equipo ha sido revocado. Contacte a su administrador.'
            );
        END IF;
        -- Actualizar marca de último acceso y nombre
        UPDATE public.dispositivos_hwid
        SET ultimo_acceso = NOW(), nombre_equipo = p_pc_name
        WHERE id = v_hwid_row.id;
    ELSE
        -- Equipo nuevo: verificar si la empresa aún tiene cupo de PCs
        SELECT COUNT(*) INTO v_hwids_count
        FROM public.dispositivos_hwid
        WHERE empresa_id = v_empresa.id AND activo = true;

        IF v_hwids_count >= v_empresa.max_hwids THEN
            RETURN jsonb_build_object(
                'success', false,
                'error_code', 'HWID_LIMIT_REACHED',
                'error_message', format('Límite de PCs físicas alcanzado (%s/%s). Este equipo no está autorizado para %s.', v_hwids_count, v_empresa.max_hwids, v_empresa.nombre)
            );
        END IF;

        -- Registrar automáticamente el nuevo equipo autorizado
        INSERT INTO public.dispositivos_hwid (empresa_id, hwid_hash, nombre_equipo, activo, registrado_en, ultimo_acceso)
        VALUES (v_empresa.id, p_hwid, p_pc_name, true, NOW(), NOW());
    END IF;

    -- 6. Validar Licencias Flotantes (Asientos Concurrentes)
    -- Verificar si este mismo usuario en este mismo HWID ya tenía una sesión activa (ej. reconexión rápida)
    SELECT * INTO v_current_session
    FROM public.sesiones_activas
    WHERE empresa_id = v_empresa.id AND hwid_hash = p_hwid AND usuario_id = v_user.id;

    IF FOUND THEN
        -- Reutilizar y renovar sesión existente
        v_token := gen_random_uuid()::text;
        UPDATE public.sesiones_activas
        SET token_sesion = v_token, ultimo_latido = NOW(), nombre_equipo = p_pc_name
        WHERE id = v_current_session.id;

        -- Conteo de asientos en uso actuales
        SELECT COUNT(*) INTO v_active_seats
        FROM public.sesiones_activas
        WHERE empresa_id = v_empresa.id;

        RETURN jsonb_build_object(
            'success', true,
            'token', v_token,
            'empresa', v_empresa.nombre,
            'cuentas_en_uso', v_active_seats,
            'max_cuentas', v_empresa.max_asientos
        );
    END IF;

    -- Si es una sesión nueva, contar cuántas hay activas
    SELECT COUNT(*) INTO v_active_seats
    FROM public.sesiones_activas
    WHERE empresa_id = v_empresa.id;

    IF v_active_seats >= v_empresa.max_asientos THEN
        -- Recopilar los nombres de los equipos que tienen ocupadas las licencias
        SELECT jsonb_agg(nombre_equipo) INTO v_ocupantes
        FROM (
            SELECT DISTINCT nombre_equipo
            FROM public.sesiones_activas
            WHERE empresa_id = v_empresa.id
            ORDER BY nombre_equipo
        ) sub;

        RETURN jsonb_build_object(
            'success', false,
            'error_code', 'SEATS_FULL',
            'error_message', format('Límite de licencias alcanzado (%s/%s).', v_active_seats, v_empresa.max_asientos),
            'cuentas_en_uso', v_active_seats,
            'max_cuentas', v_empresa.max_asientos,
            'ocupantes', COALESCE(v_ocupantes, '[]'::jsonb)
        );
    END IF;

    -- Generar nuevo token y registrar sesión
    v_token := gen_random_uuid()::text;
    INSERT INTO public.sesiones_activas (empresa_id, usuario_id, hwid_hash, nombre_equipo, token_sesion, ultimo_latido, iniciada_en)
    VALUES (v_empresa.id, v_user.id, p_hwid, p_pc_name, v_token, NOW(), NOW());

    RETURN jsonb_build_object(
        'success', true,
        'token', v_token,
        'empresa', v_empresa.nombre,
        'cuentas_en_uso', v_active_seats + 1,
        'max_cuentas', v_empresa.max_asientos
    );
END;
$$;

-- B. FUNCIÓN DE HEARTBEAT (LATIDO CADA 90-120 SEGUNDOS)
CREATE OR REPLACE FUNCTION public.heartbeat(
    p_token TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_updated INTEGER;
BEGIN
    UPDATE public.sesiones_activas
    SET ultimo_latido = NOW()
    WHERE token_sesion = p_token;

    GET DIAGNOSTICS v_updated = ROW_COUNT;

    IF v_updated > 0 THEN
        RETURN jsonb_build_object('success', true, 'active', true);
    ELSE
        RETURN jsonb_build_object('success', false, 'active', false, 'error_message', 'Sesión expirada o revocada por el administrador.');
    END IF;
END;
$$;

-- C. FUNCIÓN DE LIBERACIÓN DE ASIENTO (EVENTO ON_CLOSE)
CREATE OR REPLACE FUNCTION public.release_seat(
    p_token TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    DELETE FROM public.sesiones_activas
    WHERE token_sesion = p_token;

    RETURN jsonb_build_object('success', true);
END;
$$;

-- ==============================================================================
-- 7. PERMISOS Y SEGURIDAD RLS (Row Level Security)
-- ==============================================================================
-- Habilitar RLS en todas las tablas para que nadie pueda consultarlas directamente vía REST
ALTER TABLE public.empresas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dispositivos_hwid ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sesiones_activas ENABLE ROW LEVEL SECURITY;

-- Permitir ejecución de las funciones RPC al rol anon y authenticated
GRANT EXECUTE ON FUNCTION public.login_and_acquire_seat(TEXT, TEXT, TEXT, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.heartbeat(TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.release_seat(TEXT) TO anon, authenticated;
