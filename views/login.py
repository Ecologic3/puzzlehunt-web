import datetime
import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

import db_funcs as db
from auth import get_cookie_manager

try:
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD")
except StreamlitSecretNotFoundError:
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    raise ValueError("Admin password is not set up!")


def render_user_login():
    st.title("K-SCUK Šifrovačka", anchor=False)
    st.write("*Přihlaste se pro zadávání aktivačních kódů a hesel k šifrám.*")

    with st.form("user_login_form"):
        st.text_input("Jméno/barva týmu", key="login_username")
        st.text_input("Heslo", type="password", key="login_password")
        st.form_submit_button("Přihlásit se", type="primary", use_container_width=True, on_click=process_login)

    if st.session_state.pop("login_error", False):
        st.error("Nesprávné jméno/barva týmu nebo heslo.")

    st.divider()

    cols = st.columns(3)

    with cols[1]:
        if st.button("Admin Login", use_container_width=True):
            st.session_state.current_page = "admin_login"
            st.rerun()


def render_admin_login():
    st.title("Adminský přístup", anchor=False)
    st.write("*Tady nic nenajdete...*")

    with st.form("admin_login_form"):
        password = st.text_input("Heslo", type="password")
        submitted = st.form_submit_button("Přihlásit jako Admin", type="primary", use_container_width=True)

        if submitted:
            ip_address = st.context.ip_address
            user_agent = st.context.headers.get("User-Agent")
            db.log_login_attempt(None, password, ip_address, user_agent)
            if password == ADMIN_PASSWORD:
                st.session_state.current_page = "admin_dashboard"
                st.rerun()
            elif "epstein" in password.lower():
                st.error("Skoro!")
            else:
                st.error("Nesprávné adminské heslo.")

    if st.button("Zpátky na týmové přihlášení", use_container_width=True):
        st.session_state.current_page = "login"
        st.rerun()


def render_logout():
    st.sidebar.button("Odhlásit se", use_container_width=True, on_click=process_logout)


def process_login():
    input_username = st.session_state.login_username
    input_password = st.session_state.login_password

    ip_address = st.context.ip_address
    user_agent = st.context.headers.get("User-Agent")
    db.log_login_attempt(input_username, input_password, ip_address, user_agent)
    team_id = db.check_login(input_username, input_password)

    if team_id:
        cookie_manager = get_cookie_manager()
        expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        cookie_manager.set(
            cookie="logged_in_team_id",
            val=team_id,
            expires_at=expiry,
            key="login_cookie_set",
            same_site="lax"
        )
        st.session_state.current_user = team_id
        st.session_state.current_page = "puzzles"
    else:
        st.session_state.login_error = True


def process_logout():
    get_cookie_manager().delete("logged_in_team_id", key="logout_cookie_del")
    st.session_state.clear()
    st.stop()
