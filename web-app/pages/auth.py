# pages/auth.py
import streamlit as st
from utils.auth import (
    get_user,
    create_user,
    verify_user,
    bump_login_stats,
    user_exists,
)

st.set_page_config(page_title="Авторизация", layout="centered")

# -------------------------------
# Session state init
# -------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "role" not in st.session_state:
    st.session_state.role = None

# ==================================================
# AUTHENTICATED USER
# ==================================================
if st.session_state.authenticated:
    user = get_user(st.session_state.username)

    st.title("👤 Профиль пользователя")
    st.success(f"Вы вошли как **{user['username']}**")

    st.divider()
    st.write("### 📊 Информация")
    st.write(f"🆔 User ID: `{user['id']}`")
    st.write(f"📅 Регистрация: {user['registered_at']}")
    st.write(f"🕒 Последний вход: {user['last_login']}")
    st.write(f"🔢 Количество входов: {user['login_count']}")

    st.divider()
    st.page_link("pages/inference.py", label="🧠 Инференс моделей", icon="🧩")
    st.page_link("pages/logs.py", label="📜 Логи инференса", icon="📊")

    st.divider()
    if st.button("🚪 Выйти из системы"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.rerun()

    st.stop()

# ==================================================
# NOT AUTHENTICATED
# ==================================================
st.title("🔐 Авторизация")

tab_login, tab_register = st.tabs(["Вход", "Регистрация"])

# -------------------------------
# LOGIN
# -------------------------------
with tab_login:
    username_login = st.text_input(
        "Имя пользователя",
        key="login_username",
    )
    password_login = st.text_input(
        "Пароль",
        type="password",
        key="login_password",
    )

    if st.button("Войти"):
        if verify_user(username_login, password_login):
            user = get_user(username_login)

            st.session_state.authenticated = True
            st.session_state.username = username_login
            st.session_state.user_id = user["id"]
            st.session_state.role = user["role"]

            bump_login_stats(username_login)

            st.success("✅ Успешный вход")
            st.rerun()
        else:
            st.error("❌ Неверное имя пользователя или пароль")

# -------------------------------
# REGISTER
# -------------------------------
with tab_register:
    username_reg = st.text_input(
        "Новое имя пользователя",
        key="reg_username",
    )
    password_reg_1 = st.text_input(
        "Пароль",
        type="password",
        key="reg_password_1",
    )
    password_reg_2 = st.text_input(
        "Повторите пароль",
        type="password",
        key="reg_password_2",
    )

    if st.button("Зарегистрироваться"):
        if not username_reg or not password_reg_1:
            st.warning("Введите все поля")
        elif password_reg_1 != password_reg_2:
            st.warning("Пароли не совпадают")
        elif user_exists(username_reg):
            st.warning("Такой пользователь уже существует")
        else:
            create_user(username_reg, password_reg_1)
            st.success("✅ Регистрация успешна. Теперь войдите.")
