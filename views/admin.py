import streamlit as st
import db_funcs

def render():
    st.title("Admin Dashboard", anchor=False)
    
    st.subheader("Leaderboard", anchor=False)
    query = text("""
        SELECT
            team_color AS "Barva týmu",
            team_name AS "Jméno týmu",
            points AS "Body",
            TO_CHAR(total_time, 'FMHH24 "h" FMMI "m" FMSS "s"') AS "Čas"
        FROM teams ORDER BY points DESC, total_time ASC
    """)
    with engine.connect() as conn:
        result = conn.execute(query).mappings().all()
    st.dataframe(result, hide_index=True)
    st.divider()

    st.subheader("Admin functions", anchor=False)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("Create team", type="primary", use_container_width=True):
            st.session_state.admin_action = "create_team"
            st.rerun()

    with col2:
        if st.button("Remove team", type="primary", use_container_width=True):
            st.session_state.admin_action = "remove_team"
            st.rerun()

    with col3:
        if st.button("Edit team", type="primary", use_container_width=True):
            st.session_state.admin_action = "edit_team"
            st.rerun()

    with col4:
        if st.button("Show action log", type="primary", use_container_width=True):
            st.session_state.admin_action = "action_log"
            st.rerun()
    
    with col5:
        if st.button("Show login attempts", type="primary", use_container_width=True):
            st.session_state.admin_action = "login_attempts"
            st.rerun()

    match st.session_state.admin_action:
        case "create_team":
            with st.form("create_user_form"):
                team_color = st.text_input("Team color")
                initial_password = st.text_input("Initial password")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if create_team(team_color, initial_password):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error creating team")

        case "remove_team":
            with st.form("remove_team_form"):
                team_color = st.text_input("Team color")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if remove_team(team_color):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error removing team")

        case "edit_team":
            with st.form("edit_team_form"):
                team_color = st.text_input("Team color")
                team_name = st.text_input("Team name")
                password = st.text_input("Password")
                points = st.text_input("Points")
                total_time = st.text_input("Total time")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if edit_team(team_color, team_name, password, points, total_time):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error editing team")
        
        case "action_log":
            query = text("""
                SELECT
                    id,
                    team_color AS "Barva týmu",
                    action AS "Akce",
                    input AS "Input",
                    correct AS "Správně",
                    TO_CHAR(time AT TIME ZONE 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS') AS "Datum a čas"
                FROM actions
            """)
            with engine.connect() as conn:
                result = conn.execute(query).mappings().all()
            st.dataframe(result, hide_index=True)
            if st.button("Close", type="primary"):
                st.session_state.admin_action = None
                st.rerun()

        case "login_attempts":
            query = text("""
                SELECT
                    id,
                    input_username AS "Input",
                    password AS "Heslo",
                    ip_address AS "IP adresa",
                    user_agent AS "Agent",
                    TO_CHAR(time AT TIME ZONE 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS') AS "Datum a čas"
                FROM login_attempts
            """)
            with engine.connect() as conn:
                result = conn.execute(query).mappings().all()
            st.dataframe(result, hide_index=True)
            if st.button("Close", type="primary"):
                st.session_state.admin_action = None
                st.rerun()

    st.divider()
    
    if st.button("Logout of Admin", type="primary"):
        st.session_state.current_page = "login"
        st.rerun()
