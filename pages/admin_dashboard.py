# pages/admin_dashboard.py
import streamlit as st
import pandas as pd
from utils.db import get_conn, put_conn

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# --------------------------------------------------
# Access control
# --------------------------------------------------
if not st.session_state.get("authenticated"):
    st.warning("Войдите в систему")
    st.stop()

if st.session_state.get("role") != "admin":
    st.error("🚫 Доступ запрещён")
    st.stop()

st.title("🛠 Admin Dashboard")

# --------------------------------------------------
# Global MNIST metrics
# --------------------------------------------------
conn = get_conn()
try:
    with conn.cursor() as cur:
        # Accuracy по grid
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE (input_meta->>'correct')::boolean = true) AS correct,
                COUNT(*) FILTER (WHERE input_meta ? 'correct') AS total
            FROM ml.inference_logs
            WHERE task = 'mnist'
              AND input_meta->>'source' = 'mnist_grid'
        """)
        correct, total = cur.fetchone()

        acc = (correct / total) if total else 0

        st.metric(
            "MNIST Accuracy (grid, глобально)",
            f"{acc:.2%}",
            f"{correct} / {total}"
        )

        st.divider()

        # Ошибки модели
        cur.execute("""
            SELECT
                input_meta->>'true_label' AS true_label,
                predicted_label,
                COUNT(*) AS cnt
            FROM ml.inference_logs
            WHERE input_meta->>'correct' = 'false'
            GROUP BY true_label, predicted_label
            ORDER BY cnt DESC
            LIMIT 20
        """)
        rows = cur.fetchall()

        df = pd.DataFrame(
            rows,
            columns=["true_label", "predicted_label", "count"]
        )

        st.subheader("❌ Частые ошибки модели")
        st.dataframe(df, use_container_width=True)

finally:
    put_conn(conn)
