import streamlit as st
import db_funcs as db
import os

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or st.secrets.get("ADMIN_PASSWORD")

def render_user_login():
    st.title("K-SCUK Šifrovačka", anchor=False)
    st.write("*Přihlaste se pro zadávání kódů a hesel k šifrám.*")
    
    with st.form("user_login_form"):
        input_username = st.text_input("Jméno/barva týmu")
        password = st.text_input("Heslo", type="password")
        submitted = st.form_submit_button("Přihlásit se", type="primary", use_container_width=True)

        if submitted:
            ip_address = st.context.ip_address
            user_agent = st.context.headers.get("User-Agent")
            db.log_login_attempt(input_username, password, ip_address, user_agent)
            if db.check_login(input_username, password):
                st.session_state.current_user = input_username
                st.session_state.current_page = "tasks"
                st.rerun() 
            else:
                st.error("Nesprávné jméno/barva týmu nebo heslo.")
            
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
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
                st.session_state.current_user = "admin"
                st.rerun()
            elif "epstein" in password.lower():
                st.error("Skoro!")
            else:
                st.error("Nesprávné adminské heslo.")
    
    if st.button("Zpátky na týmové přihlášení", use_container_width=True):
        st.session_state.current_page = "login"
        st.rerun()
