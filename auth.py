import extra_streamlit_components as stx  # type: ignore[import-untyped]
import streamlit as st


def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="auth_cookie_manager")
    return st.session_state.cookie_manager
