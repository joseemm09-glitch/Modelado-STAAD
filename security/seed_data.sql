-- ==============================================================================
-- FRAMEONE: DATOS INICIALES DE PRUEBA (SEED DATA)
-- Ejecutar en el SQL Editor de Supabase después de ejecutar schema.sql
-- ==============================================================================

SET search_path = public, extensions;

DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    -- 1. Insertar o actualizar Empresa "IMPER de Chihuahua"
    INSERT INTO public.empresas (nombre, max_asientos, max_hwids, activa)
    VALUES ('IMPER de Chihuahua', 2, 5, true)
    ON CONFLICT (nombre) DO UPDATE
    SET max_asientos = 2, max_hwids = 5, activa = true
    RETURNING id INTO v_empresa_id;

    -- 2. Insertar Usuario inicial: joseemm09@gmail.com / 9918 (cifrado con crypt bf)
    INSERT INTO public.usuarios (empresa_id, correo, password_hash, activo)
    VALUES (
        v_empresa_id,
        'joseemm09@gmail.com',
        crypt('9918', gen_salt('bf')),
        true
    )
    ON CONFLICT (correo) DO UPDATE
    SET empresa_id = v_empresa_id,
        password_hash = crypt('9918', gen_salt('bf')),
        activo = true;

    RAISE NOTICE 'Seed data insertado correctamente para IMPER de Chihuahua';
END;
$$;
