import streamlit as st
import streamlit.config as st_config

import db_funcs as db
from auth import get_cookie_manager
from views import admin, login, puzzles


def main():
    # host = st.context.headers.get("host", "").split(":")[0].lower()
    IS_LOCAL = st_config.get_option("server.address") in ["localhost", "127.0.0.1"] or st_config.get_option("server.port") == 8501
    if IS_LOCAL:
        render_puzzlehunt()
    else:
        render_main()

    # PUZZLEHUNT_SUBDOMAIN = "sifrovacka.deadlocked.me"

    # if host == PUZZLEHUNT_SUBDOMAIN:
    #     render_puzzlehunt()
    # else:
    #     render_main()


def render_main():
    st.set_page_config(page_title="Deadlock", page_icon="static/favicon.png", layout="centered")

    st.image("static/deadlock.png")


def render_puzzlehunt():
    # db.init_puzzles_db()
    # db.init_teams_db()
    # db.init_actions_db()
    # db.init_submissions_db()
    # db.init_logging_db()
    # db.init_settings_db()

    st.set_page_config(page_title="Šifrovačka", page_icon="static/favicon.png", layout="centered")
    st.markdown("""
        <style>
        div[data-testid="InputInstructions"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    ACTIVE_PUZZLES = db.get_active_puzzles()

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

        saved_user_id = cookies.get("logged_in_user_id")
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