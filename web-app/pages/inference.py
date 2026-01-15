# pages/inference.py
import os
import requests
import numpy as np
import streamlit as st
from PIL import Image, ImageOps

from utils.db import get_conn, put_conn
from utils.inference import log_inference

# ==================================================
# Config
# ==================================================
API_BASE = os.getenv(
    "INFERENCE_API_URL",
    "http://localhost:8000"
)

PREDICT_URL = f"{API_BASE}/mnist/predict"


def check_backend_health():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=2)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False


st.set_page_config(page_title="MNIST Inference", layout="centered")
st.title("🧠 MNIST Inference Platform")

# ==================================================
# Auth
# ==================================================
if not st.session_state.get("authenticated"):
    st.warning("Пожалуйста, войдите в систему")
    st.stop()

if not check_backend_health():
    st.error("❌ Inference backend недоступен (FastAPI не запущен)")
    st.stop()
else:
    st.success("✅ Inference backend доступен")

# ==================================================
# Session accuracy stats
# ==================================================
if "mnist_stats" not in st.session_state:
    st.session_state.mnist_stats = {
        "total": 0,
        "correct": 0,
    }


# ==================================================
# FastAPI client
# ==================================================
def predict_via_api(pil_img_28):
    pixels = np.array(pil_img_28, dtype=np.float32).reshape(-1).tolist()

    r = requests.post(
        PREDICT_URL,
        json={"pixels": pixels},
        timeout=5,
    )

    if r.status_code != 200:
        st.error("❌ Inference backend недоступен")
        st.stop()

    data = r.json()
    pred = int(data["predicted_label"])
    probs = {int(k): float(v) for k, v in data["probabilities"].items()}
    return pred, probs


# ==================================================
# MNIST DB helpers
# ==================================================
def fetch_one_per_digit():
    conn = get_conn()
    try:
        samples = []
        with conn.cursor() as cur:
            for d in range(10):
                cur.execute(
                    """
                    SELECT label, vec, rows, cols
                    FROM demo.mnist_samples
                    WHERE split = 'test' AND label = %s
                    ORDER BY random()
                    LIMIT 1
                    """,
                    (d,),
                )
                samples.append(cur.fetchone())
        return samples
    finally:
        put_conn(conn)


def vec_to_pil(vec_blob, rows, cols):
    arr = np.frombuffer(vec_blob, dtype=np.float32).reshape(rows, cols)
    return Image.fromarray((arr * 255).astype(np.uint8))


def preprocess_upload(pil_img, invert=False):
    img = pil_img.convert("L")
    if invert:
        img = ImageOps.invert(img)
    img = ImageOps.pad(img, (28, 28), color=255)
    return img


# ==================================================
# UI — Grid MNIST
# ==================================================
st.subheader("⚡ Быстрый тест MNIST (grid 0–9)")
st.caption("Известен истинный класс → считается accuracy")

if "mnist_grid" not in st.session_state or st.button("🔄 Обновить примеры"):
    st.session_state.mnist_grid = fetch_one_per_digit()

cols = st.columns(10, gap="small")
clicked = None

for i, col in enumerate(cols):
    row = st.session_state.mnist_grid[i]
    if row is None:
        col.write("—")
        continue

    true_label, vec, r, c = row
    img = vec_to_pil(vec, r, c)

    col.image(img, caption=str(true_label), width='stretch')
    if col.button(f"{true_label}", key=f"pick_mnist_{i}"):
        pred, probs = predict_via_api(img)
        clicked = (true_label, pred, probs)

# ==================================================
# Grid result + logging + accuracy
# ==================================================
if clicked:
    true_label, pred, probs = clicked
    is_correct = pred == true_label

    # update stats
    st.session_state.mnist_stats["total"] += 1
    if is_correct:
        st.session_state.mnist_stats["correct"] += 1

    # log
    log_inference(
        task="mnist",
        user_id=st.session_state.user_id,
        username=st.session_state.username,
        input_payload=None,
        input_meta={
            "source": "mnist_grid",
            "true_label": int(true_label),
            "correct": bool(is_correct),
        },
        predicted_label=str(pred),
        confidence=float(probs[pred]),
        probabilities={str(i): float(probs[i]) for i in range(10)},
        model_version="mnist_cnn_v1",
    )

    if is_correct:
        st.success(f"✅ Предсказание: {pred} — ВЕРНО")
    else:
        st.error(f"❌ Предсказание: {pred} | Истинная: {true_label}")

    st.bar_chart({str(i): probs[i] for i in range(10)})

    stats = st.session_state.mnist_stats
    acc = stats["correct"] / stats["total"]
    st.metric(
        "Accuracy по grid (сессия)",
        f"{acc:.2%}",
        f"{stats['correct']} / {stats['total']}",
    )

# ==================================================
# UI — Upload
# ==================================================
st.divider()
st.subheader("✍️ Загрузить собственную цифру")

st.info(
    "ℹ️ Белая цифра на тёмном фоне даёт лучший результат. "
    "Используйте инверсию при необходимости."
)

file = st.file_uploader(
    "PNG / JPG",
    type=["png", "jpg", "jpeg"],
)

invert = st.checkbox("Инвертировать цвета")

if file:
    pil = Image.open(file)
    pre = preprocess_upload(pil, invert=invert)

    c1, c2 = st.columns(2)
    c1.image(pil, caption="Исходное изображение")
    c2.image(pre, caption="28×28 для модели")

    if st.button("🔍 Распознать цифру"):
        pred, probs = predict_via_api(pre)

        log_inference(
            task="mnist",
            user_id=st.session_state.user_id,
            username=st.session_state.username,
            input_payload=None,
            input_meta={
                "source": "upload",
                "true_label": None,
            },
            predicted_label=str(pred),
            confidence=float(probs[pred]),
            probabilities={str(i): float(probs[i]) for i in range(10)},
            model_version="mnist_cnn_v1",
        )

        st.success(f"✅ Предсказание модели: **{pred}**")
        st.bar_chart({str(i): probs[i] for i in range(10)})
