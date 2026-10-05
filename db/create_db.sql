-- Provisión de la base del laboratorio OrderFlow (PostgreSQL).
-- Ejecutar como superusuario de Postgres, p.ej.:
--     sudo -u postgres psql -f db/create_db.sql
-- Es idempotente: no falla si el rol o la base ya existen.

-- Rol de aplicación (credenciales de laboratorio; coinciden con app/config.py).
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'orderflow') THEN
      CREATE ROLE orderflow LOGIN PASSWORD 'orderflow';
   END IF;
END
$$;

-- Base de datos (CREATE DATABASE no puede ir dentro de un bloque DO/transacción;
-- \gexec ejecuta la sentencia sólo si la base no existe).
SELECT 'CREATE DATABASE orderflow_lab OWNER orderflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'orderflow_lab')\gexec

-- Asegurar permisos sobre el esquema public (necesario en PostgreSQL 15+).
\connect orderflow_lab
GRANT ALL ON SCHEMA public TO orderflow;
