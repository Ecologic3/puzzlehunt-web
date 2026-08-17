from datetime import timedelta
from time import sleep

import streamlit as st

import db_funcs as db


def render():
    st.title("Admin Dashboard", anchor=False)
    
    st.subheader("Leaderboard", anchor=False)
    leaderboard_data = db.get_leaderboard()
    st.dataframe(leaderboard_data, hide_index=True)
    if st.button("Refresh"):
        st.rerun()
    st.divider()

    st.subheader("Admin functions", anchor=False)
    team_cols = st.columns(3)
    puzzle_cols = st.columns(3)
    log_cols = st.columns(4)

    with team_cols[0]:
        if st.button("Create team", type="primary"):
            st.session_state.admin_action = "create_team"
            st.rerun()

    with team_cols[1]:
        if st.button("Remove team", type="primary"):
            st.session_state.admin_action = "remove_team"
            st.rerun()

    with team_cols[2]:
        if st.button("Edit team", type="primary"):
            st.session_state.admin_action = "edit_team"
            st.rerun()
    
    with puzzle_cols[0]:
        if st.button("Create puzzle", type="primary"):
            st.session_state.admin_action = "create_puzzle"
            st.rerun()

    with puzzle_cols[1]:
        if st.button("Remove puzzle", type="primary"):
            st.session_state.admin_action = "remove_puzzle"
            st.rerun()

    with puzzle_cols[2]:
        if st.button("Edit puzzle", type="primary"):
            st.session_state.admin_action = "edit_puzzle"
            st.rerun()

    with log_cols[0]:
        if st.button("Show action log", type="primary"):
            st.session_state.admin_action = "action_log"
            st.rerun()

    with log_cols[1]:
        if st.button("Show submissions", type="primary"):
            st.session_state.admin_action = "submission_log"
            st.rerun()

    with log_cols[2]:
        if st.button("Show login attempts", type="primary"):
            st.session_state.admin_action = "login_attempts"
            st.rerun()
    
    with log_cols[3]:
        if st.button("Show puzzle list", type="primary"):
            st.session_state.admin_action = "puzzle_list"
            st.rerun()

    if st.button("Manual SQL query", type="primary"):
        st.session_state.admin_action = "sql_query"
        st.rerun()

    match st.session_state.admin_action:
        case "create_team":
            with st.form("create_team_form"):
                team_color = st.text_input("Team color")
                initial_password = st.text_input("Initial password")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if db.create_team(team_color, initial_password):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error creating team")

        case "remove_team":
            with st.form("remove_team_form"):
                team_color = st.text_input("Team color")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if db.remove_team(team_color):
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
                    if total_time:
                        if not total_time.isdigit():
                            total_time = None
                        else:
                            total_time = timedelta(seconds=int(total_time))
                    else:
                        total_time = None
                    if db.edit_team(team_color, team_name, password, points, total_time):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error editing team")

        case "create_puzzle":
            with st.form("create_puzzle_form"):
                name = st.text_input("Puzzle name")
                solution = st.text_input("Solution")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    db.create_puzzle(name, solution)
                    st.session_state.admin_action = None
                    st.rerun()

        case "remove_puzzle":
            with st.form("remove_puzzle_form"):
                name = st.text_input("Puzzle name")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if db.remove_puzzle(name):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error removing puzzle")

        case "edit_puzzle":
            with st.form("edit_puzzle_form"):
                name = st.text_input("Puzzle name")
                order = st.text_input("Puzzle order")
                activation_code = st.text_input("Activation code")
                solution = st.text_input("Solution")
                hint = st.text_input("Hint")
                filename = st.text_input("Filename")
                location = st.text_input("Location")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if order:
                        if not order.isdigit():
                            order = None
                        else:
                            order = int(order)
                    else:
                        order = None
                    if db.edit_puzzle(name, order, activation_code, solution, hint, filename, location):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error editing puzzle")

        case "action_log":
            action_log = db.get_action_log()
            st.dataframe(action_log, hide_index=True)
            if st.button("Close", type="primary"):
                st.session_state.admin_action = None
                st.rerun()
    
        case "submission_log":
            submission_log = db.get_submissions()
            st.dataframe(submission_log, hide_index=True)
            if st.button("Close", type="primary"):
                st.session_state.admin_action = None
                st.rerun()

        case "login_attempts":
            login_attempts = db.get_login_attempts()
            st.dataframe(login_attempts, hide_index=True)
            if st.button("Close", type="primary"):
                st.session_state.admin_action = None
                st.rerun()
        
        case "puzzle_list":
            puzzle_list = db.get_puzzles()
            st.dataframe(puzzle_list, hide_index=True)
            if st.button("Close", type="primary"):
                st.session_state.admin_action = None
                st.rerun()

        case "sql_query":
            with st.form("sql_query_form"):
                    query = st.text_input("SQL Query")
                    submitted = st.form_submit_button("Submit", type="primary")
                    if submitted:
                        success, result = db.execute_query(query)
                        if success:
                            st.success(f"Success! Output: {result}")
                            sleep(2)
                            st.session_state.admin_action = None
                            st.rerun()
                        else:
                            st.error(f"Error while executing query: {result}")


    st.divider()
    
    if st.button("Logout of Admin"):
        st.session_state.current_page = "login"
        st.session_state.current_user = None
        st.rerun()
