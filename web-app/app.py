# app.py
import streamlit as st

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="ML Inference Platform",
    page_icon="🧠",
    layout="centered",
)

# --------------------------------------------------
# Session state initialization
# --------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("🧠 ML Inference Platform")
st.caption(
    "Unified platform for secure machine-learning inference, "
    "user management and inference logging."
)

st.divider()

# --------------------------------------------------
# NOT AUTHENTICATED
# --------------------------------------------------
if not st.session_state.authenticated:
    st.info(
        "Для использования платформы необходимо войти или зарегистрироваться."
    )

    st.page_link(
        "pages/auth.py",
        label="🔐 Авторизация / Регистрация",
        icon="🔑",
    )

    st.divider()

    st.markdown(
        """
        ### 🧩 Возможности платформы
        - 🔐 Пользовательская аутентификация
        - 🧠 ML-инференс (несколько моделей / задач)
        - 📜 Логирование всех предсказаний
        - 📊 Анализ и аудит использования моделей
        """
    )

    st.stop()

# --------------------------------------------------
# AUTHENTICATED
# --------------------------------------------------
st.success(
    f"Вы вошли как **{st.session_state.username}** ✅"
)

# Navigation
st.subheader("Навигация")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link(
        "pages/inference.py",
        label="🧩 Инференс модели",
        icon="🧠",
    )

with col2:
    st.page_link(
        "pages/logs.py",
        label="📜 История инференса",
        icon="📊",
    )

with col3:
    st.page_link(
        "pages/auth.py",
        label="👤 Профиль / Выход",
        icon="🔐",
    )

if st.session_state.role == "admin":
    st.page_link(
        "pages/admin_dashboard.py",
        label="🛠 Admin Dashboard",
        icon="🧑‍💼",
    )

st.divider()

# --------------------------------------------------
# Platform status / info
# --------------------------------------------------
st.markdown(
    """
    ### ✅ Статус платформы

    - 🔒 Система аутентификации активна  
    - 🗄️ База данных подключена  
    - 📜 Логирование инференса включено  
    - 🧠 Поддержка нескольких ML-задач  

    ---
    """
)

st.caption(
    "ML Inference Platform — архитектурный шаблон для ML-сервисов "
    "с полной трассируемостью решений моделей."
)

# --------------------------------------------------
# Logout shortcut
# --------------------------------------------------
with st.expander("🚪 Выход из системы"):
    if st.button("Выйти из аккаунта"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.rerun()
