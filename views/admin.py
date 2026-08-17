import os
from datetime import timedelta
from time import sleep

import streamlit as st

import db_funcs as db

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or st.secrets.get("ADMIN_PASSWORD")

def render():
    st.title("Admin Dashboard", anchor=False)
    
    # Leaderboard rendering
    st.subheader("Leaderboard", anchor=False)
    leaderboard_data = db.get_leaderboard(True)
    st.dataframe(leaderboard_data, hide_index=True)
    if st.button("Refresh"):
        st.rerun()
    st.divider()

    # Admin function buttons
    st.subheader("Admin functions", anchor=False)
    team_cols = st.columns(3)
    puzzle_cols = st.columns(3)
    log_cols = st.columns(4)
    other_cols = st.columns(3)

    with team_cols[0]:   # Create team
        if st.button("Create team", type="primary", use_container_width=True):
            st.session_state.admin_action = "create_team"
            st.rerun()

    with team_cols[1]:  # Remove team
        if st.button("Remove team", type="primary", use_container_width=True):
            st.session_state.admin_action = "remove_team"
            st.rerun()

    with team_cols[2]:  # Edit team
        if st.button("Edit team", type="primary", use_container_width=True):
            st.session_state.admin_action = "edit_team"
            st.rerun()
    
    with puzzle_cols[0]:  # Create puzzle
        if st.button("Create puzzle", type="primary", use_container_width=True):
            st.session_state.admin_action = "create_puzzle"
            st.rerun()

    with puzzle_cols[1]:  # Remove puzzle
        if st.button("Remove puzzle", type="primary", use_container_width=True):
            st.session_state.admin_action = "remove_puzzle"
            st.rerun()

    with puzzle_cols[2]:  # Edit puzzle
        if st.button("Edit puzzle", type="primary", use_container_width=True):
            st.session_state.admin_action = "edit_puzzle"
            st.rerun()

    with log_cols[0]:  # Show action log
        if st.button("Show action log", type="primary", use_container_width=True):
            st.session_state.admin_action = "action_log"
            st.rerun()

    with log_cols[1]:  # Show submissions
        if st.button("Show submissions", type="primary", use_container_width=True):
            st.session_state.admin_action = "submission_log"
            st.rerun()

    with log_cols[2]:  # Show login attempts
        if st.button("Show login attempts", type="primary", use_container_width=True):
            st.session_state.admin_action = "login_attempts"
            st.rerun()
    
    with log_cols[3]:  # Show puzzle list
        if st.button("Show puzzle list", type="primary", use_container_width=True):
            st.session_state.admin_action = "puzzle_list"
            st.rerun()

    with other_cols[0]:  # Manual SQL query
        if st.button("Manual SQL query", type="primary", use_container_width=True):
            st.session_state.admin_action = "sql_query"
            st.rerun()
    
    with other_cols[1]:  # Clear cache
        if st.button("Clear cache", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared.")
            sleep(0.5)
            st.rerun()

    with other_cols[2]:  # Reset database
        if st.button("Reset database", type="primary", use_container_width=True):
            st.session_state.admin_action = "reset_database"
            st.rerun()


    # Admin functions
    match st.session_state.admin_action:
        case "create_team":
            with st.form("create_team_form"):
                team_color = st.text_input("Team color")
                initial_password = st.text_input("Initial password")
                path = st.text_input("Path (a or b)")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if db.create_team(team_color, initial_password, path):
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
                path = st.text_input("Path")
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
                    if db.edit_team(team_color, team_name, path, password, points, total_time):
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
                location_a = st.text_input("Location for path a")
                location_b = st.text_input("Location for path b")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if order:
                        if not order.isdigit():
                            order = None
                        else:
                            order = int(order)
                    else:
                        order = None
                    if db.edit_puzzle(name, order, activation_code, solution,
                                      hint, filename, location_a, location_b):
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
                    else:
                        st.error(f"Error while executing query: {result}")
            if st.button("Close", type="primary"):
                st.session_state.admin_action = None
                st.rerun()

        case "reset_database":
            with st.form("admin_password"):
                input_password = st.text_input("Are you sure? Enter admin password to confirm:", type="password")
                submitted = st.form_submit_button("Reset", type="primary")
                if submitted:
                    if input_password == ADMIN_PASSWORD:
                        st.success("Resetting database.")
                        db.reset_database()
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Incorrect admin password.")

    st.divider()
    
    # Admin logout
    if st.button("Logout of Admin"):
        st.session_state.current_page = "login"
        st.session_state.current_user = None
        st.rerun()
