import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

import db_funcs as db
from auth import get_cookie_manager
from views import admin, login, puzzles


def main():
    host = st.context.headers.get("host", "").split(":")[0].lower()

    PUZZLEHUNT_SUBDOMAIN = "sifrovacka.deadlocked.me"
    try:
        ACCESS_TOKEN = st.secrets.get("ACCESS_TOKEN")
    except StreamlitSecretNotFoundError:
        ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

    if host == PUZZLEHUNT_SUBDOMAIN:
        if ACCESS_TOKEN:  # Not public access
            token = st.query_params.get("secret")
            if token == ACCESS_TOKEN:
                render_puzzlehunt()
            else:
                render_main()
        else:
            render_puzzlehunt()
    else:
        render_main()


def render_main():
    st.set_page_config(page_title="Deadlock", page_icon="static/favicon.png", layout="centered")

    st.image("static/deadlock.png")


def render_puzzlehunt():
    st.set_page_config(page_title="Šifrovačka", page_icon="static/favicon.png", layout="centered")
    st.markdown("""
        <style>
        div[data-testid="InputInstructions"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    ACTIVE_PUZZLES = [f"puzzle_{p}" for p in db.get_active_puzzles()]

    if "is_hydrated" not in st.session_state:
        st.session_state.is_hydrated = False
        st.session_state.current_page = "login"
        st.session_state.current_user = None
        st.session_state.admin_action = None

    cookie_manager = get_cookie_manager()
    if not st.session_state.is_hydrated:
        cookies = cookie_manager.get_all()
        if not cookies:
            st.stop()

        saved_user_id = cookies.get("logged_in_team_id")
        if saved_user_id:
            st.session_state.current_user = saved_user_id
            st.session_state.current_page = "puzzles"

        st.session_state.is_hydrated = True

    # Page router
    if st.session_state.current_page == "admin_login":
        login.render_admin_login()

    elif st.session_state.current_page == "admin_dashboard":
        admin.render()

    elif st.session_state.current_user:
        if st.session_state.current_page == "puzzles":
            puzzles.render_navigation()
            puzzles.render_main()

        elif st.session_state.current_page in ACTIVE_PUZZLES:
            puzzles.render_navigation()
            puzzles.render_puzzle(st.session_state.current_page)

        elif st.session_state.current_page == "leaderboard":
            puzzles.render_navigation()
            puzzles.render_leaderboard()

    else:
        login.render_user_login()


if __name__ == "__main__":
    main()
