import streamlit as st
import db_funcs as db
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from views import admin, login, puzzles


st.markdown("""
    <style>
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)


db.init_teams_db()
db.init_actions_db()
db.init_logging_db()
db.init_puzzles_db()


PUBLIC_PAGES = ["login", "admin_login"]

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "admin_action" not in st.session_state:
    st.session_state.admin_action = None
if "progress" not in st.session_state:
    st.session_state.progress = 0

# Route guard
if st.session_state.current_page not in PUBLIC_PAGES and not st.session_state.current_user:
    st.session_state.current_page = "login"
    st.rerun()

# Page router
if st.session_state.current_page == "login":
    login.render_user_login()

elif st.session_state.current_page == "admin_login":
    login.render_admin_login()

elif st.session_state.current_page == "admin_dashboard":
    admin.render()

elif st.session_state.current_page == "puzzles":
    puzzles.render()
