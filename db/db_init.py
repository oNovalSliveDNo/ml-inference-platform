# db/db_init.py
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# --------------------------------------------------
# Environment
# --------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not found in environment")

# --------------------------------------------------
# SQL bootstrap statements
# --------------------------------------------------
DDL_STATEMENTS = [

    # =========================
    # Core infrastructure
    # =========================
    """
    CREATE SCHEMA IF NOT EXISTS public;
    """,

    """
    CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
    """,

    # =========================
    # AUTH SCHEMA
    # =========================
    """
    CREATE SCHEMA IF NOT EXISTS auth;
    """,

    """
    CREATE TABLE IF NOT EXISTS auth.users (
        id UUID PRIMARY KEY DEFAULT public.gen_random_uuid(),
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',

        registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_login    TIMESTAMPTZ,
        login_count   INTEGER NOT NULL DEFAULT 0
    );
    """,

    # -- safety for old databases (if table existed before 'role')
    """
    ALTER TABLE auth.users
    ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';
    """,

    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_users_username
    ON auth.users (username);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_auth_users_role
    ON auth.users (role);
    """,

    # =========================
    # ML SCHEMA
    # =========================
    """
    CREATE SCHEMA IF NOT EXISTS ml;
    """,

    """
    CREATE TABLE IF NOT EXISTS ml.inference_logs (
        id UUID PRIMARY KEY DEFAULT public.gen_random_uuid(),

        -- user context
        user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
        username TEXT,

        -- task / model
        task TEXT NOT NULL,
        model_version TEXT NOT NULL,

        -- input
        input_text TEXT,
        input_meta JSONB,

        -- output
        predicted_label TEXT NOT NULL,
        confidence DOUBLE PRECISION NOT NULL,
        probabilities JSONB,

        -- meta
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_ml_logs_user_id
    ON ml.inference_logs (user_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_ml_logs_username
    ON ml.inference_logs (username);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_ml_logs_task
    ON ml.inference_logs (task);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_ml_logs_created_at
    ON ml.inference_logs (created_at DESC);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_ml_logs_predicted_label
    ON ml.inference_logs (predicted_label);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_ml_logs_input_meta
    ON ml.inference_logs USING GIN (input_meta);
    """,

    # =========================
    # DEMO SCHEMA (MNIST)
    # =========================
    """
    CREATE SCHEMA IF NOT EXISTS demo;
    """,

    """
    CREATE TABLE IF NOT EXISTS demo.mnist_samples (
        id BIGSERIAL PRIMARY KEY,
        split TEXT NOT NULL,
        label INTEGER NOT NULL,
        vec BYTEA NOT NULL,
        rows INTEGER NOT NULL,
        cols INTEGER NOT NULL
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_mnist_split_label
    ON demo.mnist_samples (split, label);
    """,
]


# --------------------------------------------------
# Bootstrap runner
# --------------------------------------------------
def main():
    print("🚀 Initializing database schema (auth / ml / demo)...")

    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            for stmt in DDL_STATEMENTS:
                cur.execute(stmt)

        print("✅ Database initialization completed successfully")

    finally:
        conn.close()


# --------------------------------------------------
# Entry point
# --------------------------------------------------
if __name__ == "__main__":
    main()
