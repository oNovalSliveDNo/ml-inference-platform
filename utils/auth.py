# utils/auth.py
import hashlib
from contextlib import contextmanager
from utils.db import get_conn, put_conn


# --------------------------------------------------
# DB cursor context manager
# --------------------------------------------------
@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


# --------------------------------------------------
# Security helpers
# --------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# --------------------------------------------------
# Users
# --------------------------------------------------
def get_user(username: str):
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                username,
                password_hash,
                role,
                registered_at,
                last_login,
                login_count
            FROM auth.users
            WHERE username = %s
            """,
            (username,),
        )
        row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "role": row[3],
        "registered_at": row[4],
        "last_login": row[5],
        "login_count": row[6],
    }


def user_exists(username: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM auth.users WHERE username = %s",
            (username,),
        )
        return cur.fetchone() is not None


def create_user(username: str, password: str):
    """
    Создать нового пользователя.
    """
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO auth.users (username, password_hash)
            VALUES (%s, %s)
            RETURNING id, registered_at, login_count
            """,
            (username, hash_password(password)),
        )
        row = cur.fetchone()

    return {
        "id": row[0],
        "registered_at": row[1],
        "login_count": row[2],
    }


def verify_user(username: str, password: str) -> bool:
    u = get_user(username)
    if not u:
        return False
    return u["password_hash"] == hash_password(password)


def bump_login_stats(username: str):
    """
    Обновить статистику входов.
    """
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE auth.users
            SET last_login = NOW(),
                login_count = COALESCE(login_count, 0) + 1
            WHERE username = %s
            """,
            (username,),
        )
