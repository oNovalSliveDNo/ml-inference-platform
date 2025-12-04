# utils/inference.py
import json
from contextlib import contextmanager
from utils.db import get_conn, put_conn


# --------------------------------------------------
# DB cursor
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
# Inference logging
# --------------------------------------------------
def log_inference(
        *,
        task: str,
        user_id: str | None,
        username: str | None,
        input_payload: str | None,
        input_meta: dict | None,
        predicted_label: str,
        confidence: float,
        probabilities: dict | list | None,
        model_version: str,
):
    """
    Универсальное логирование инференса для любых ML-задач.
    """

    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO ml.inference_logs (
                user_id,
                username,
                task,
                input_text,
                input_meta,
                predicted_label,
                confidence,
                probabilities,
                model_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                username,
                task,
                input_payload,
                json.dumps(input_meta) if input_meta else None,
                predicted_label,
                float(confidence),
                json.dumps(probabilities) if probabilities else None,
                model_version,
            ),
        )
