import streamlit as st
import db_funcs

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or st.secrets.get("ADMIN_PASSWORD")

def render_user_login():
    st.title("K-SCUK Šifrovačka", anchor=False)
    st.write("*Přihlaste se pro zadávání kódů a hesel k šifrám.*")
    
    with st.form("user_login_form"):
        input_username = st.text_input("Jméno/barva týmu")
        password = st.text_input("Heslo", type="password")
        submitted = st.form_submit_button("Přihlásit se", type="primary", use_container_width=True)

        if submitted:
            query = text("""
                INSERT INTO login_attempts 
                    (input_username, password, ip_address, user_agent)
                VALUES
                    (:input_username, :password, :ip_address, :user_agent)
            """)
            ip_address = st.context.ip_address
            user_agent = st.context.headers.get("User-Agent")
            with engine.begin() as conn:
                conn.execute(query, {"input_username": input_username, "password": password, "ip_address": ip_address, "user_agent": user_agent})
            if check_login(input_username, password):
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
        admin_pass = st.text_input("Heslo", type="password")
        submitted = st.form_submit_button("Přihlásit jako Admin", type="primary", use_container_width=True)
        
        if submitted:
            query = text("""
                INSERT INTO login_attempts 
                    (password, ip_address, user_agent)
                VALUES
                    (:admin_pass, :ip_address, :user_agent)
            """)
            ip_address = st.context.ip_address
            user_agent = st.context.headers.get("User-Agent")
            with engine.begin() as conn:
                conn.execute(query, {"admin_pass": admin_pass, "ip_address": ip_address, "user_agent": user_agent})
            if admin_pass == ADMIN_PASSWORD:
                st.session_state.current_page = "admin"
                st.rerun()
            elif "epstein" in admin_pass.lower():
                st.error("Skoro!")
            else:
                st.error("Nesprávné adminské heslo.")
    
    if st.button("Zpátky na týmové přihlášení", use_container_width=True):
        st.session_state.current_page = "login"
        st.rerun()
