# pages/logs.py
import streamlit as st
import pandas as pd
from utils.db import get_conn, put_conn

st.set_page_config(page_title="Логи инференса", layout="wide")
st.title("📜 История инференса")

if not st.session_state.get("authenticated"):
    st.warning("Пожалуйста, войдите")
    st.stop()

username = st.session_state.username

limit = st.slider("Количество записей", 10, 500, 100)

conn = get_conn()
try:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                created_at,
                task,
                predicted_label,
                confidence,
                model_version,
                input_meta
            FROM ml.inference_logs
            WHERE username = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (username, limit),
        )
        rows = cur.fetchall()

    df = pd.DataFrame(
        rows,
        columns=[
            "created_at",
            "task",
            "predicted_label",
            "confidence",
            "model_version",
            "input_meta",
        ],
    )

    st.dataframe(df, use_container_width=True)

finally:
    put_conn(conn)
