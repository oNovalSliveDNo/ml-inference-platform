# utils/db.py
import os
from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool

# --------------------------------------------------
# Load environment
# --------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not set in environment")

# --------------------------------------------------
# Connection pool
# --------------------------------------------------
_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=DATABASE_URL,
)


def get_conn():
    """
    Получить соединение из пула.
    """
    return _pool.getconn()


def put_conn(conn):
    """
    Вернуть соединение обратно в пул.
    """
    if conn:
        _pool.putconn(conn)
