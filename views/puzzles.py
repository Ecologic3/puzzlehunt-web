import os
from time import sleep

import streamlit as st

import db_funcs as db
from views.login import render_logout


def render_navigation():
    current_page = st.session_state.current_page
    current_user = st.session_state.current_user
    puzzles = db.get_active_puzzles()

    st.sidebar.title("Přehled", anchor=False)

    # Navigation buttons
    button_type = "primary" if current_page == "puzzles" else "secondary"
    if st.sidebar.button("Seznam šifer", type=button_type, use_container_width=True):
        st.session_state.current_page = "puzzles"
        st.rerun()

    for puzzle_order in puzzles:  # Puzzles
        puzzle_page = f"puzzle_{puzzle_order}"
        button_type = "primary" if current_page == puzzle_page else "secondary"
        page_name = f"{puzzle_order}. {db.get_puzzle_data(puzzle_order)['name']}"
        if st.sidebar.button(page_name, type=button_type, use_container_width=True):
            st.session_state.current_page = puzzle_page
            st.rerun()

    with open("static/sifrovaci-pomucka.pdf", "rb") as file:  # Puzzle solving help
        st.sidebar.download_button(
            label="Šifrovací pomůcka",
            data=file,
            file_name="sifrovaci-pomucka.pdf",
            mime="application/pdf",
            type="secondary",
            use_container_width=True
        )

    is_end = db.get_setting("is_end")
    is_end = False if is_end is None else is_end == "true"
    if st.sidebar.button("Výsledky", type="primary", disabled=not is_end,
                         help="Budou dostupné po konci hry." if not is_end else None, use_container_width=True):
        st.session_state.current_page = "leaderboard"
        st.rerun()

    st.sidebar.divider()

    # Logout and set password
    render_logout()

    with st.sidebar.expander("Nastavit heslo"), st.form("set_password"):
        new_password = st.text_input("Nové heslo:")
        submitted = st.form_submit_button("Nastavit", type="primary")

        if submitted:
            if len(new_password) < 5:
                st.error("Heslo musí mít alespoň 5 znaků.")
            else:
                db.set_password(current_user, new_password)
                st.success("Heslo úspěšně nastaveno. Stále však můžete používat i počáteční heslo.")

    st.sidebar.caption("V případě jakýchkoliv problémů volejte Adamovi: +421 949 327 686")


def render_leaderboard():
    st.title("Výsledky", anchor=False)
    leaderboard_data = db.get_leaderboard()
    st.dataframe(leaderboard_data, hide_index=True)


def render_main():
    current_user = st.session_state.current_user
    current_puzzle = db.get_current_puzzle(current_user)
    puzzles = db.get_active_puzzles()

    st.title("Seznam šifer", anchor=False)

    # Show current puzzle location
    if current_puzzle > len(puzzles):
        st.subheader("**Úspěšně jste vyřešili všechny šifry!** 🎉")
        st.balloons()
    else:
        current_puzzle_data = db.get_puzzle_data(current_puzzle)
        team_path = db.get_team_path(current_user)
        current_puzzle_location, specification = current_puzzle_data[f"location_{team_path}"].split("|")
        st.write("Klikněte na odemčenou šifru pro zadání aktivačního kódu nebo hesla")
        st.write("*Nezapomeňte zadat aktivační kód ihned po nalezení šifry!*")
        st.write(f"Lokace poslední odemčené šifry je [zde]({current_puzzle_location}), upřesnítko: {specification}.")

    st.divider()

    # Puzzle and status list
    for puzzle_order in puzzles:
        puzzle_data = db.get_puzzle_data(puzzle_order)
        puzzle_status = db.get_puzzle_status(current_user, puzzle_order)
        puzzle_name = puzzle_data["name"]
        puzzle_page = f"puzzle_{puzzle_order}"

        if puzzle_order < current_puzzle:  # Solved puzzle
            is_deaded = puzzle_status["is_deaded"]
            solved_status = "Deadnuta ❎" if is_deaded else "Vyřešena ✅"
            if st.button(f"{puzzle_order}. {puzzle_name}: {solved_status}", use_container_width=True):
                st.session_state.current_page = puzzle_page
                st.rerun()

        elif puzzle_order == current_puzzle:  # Current puzzle
            is_activated = puzzle_status["is_activated"]
            activated_status = "V řešení 💭" if is_activated else "Připravena na řešení 🔓"
            if st.button(f"{puzzle_order}. {puzzle_name}: {activated_status}", type="primary", use_container_width=True):
                st.session_state.current_page = puzzle_page
                st.rerun()

        else:  # Locked puzzle
            st.button(f"{puzzle_order}. {puzzle_name}: Zamčena 🔒", disabled=True, use_container_width=True)


def render_puzzle(puzzle_page: str):
    current_user = st.session_state.current_user
    current_puzzle = db.get_current_puzzle(current_user)
    puzzles = db.get_active_puzzles()
    rendered_puzzle = int(puzzle_page.replace("puzzle_", ""))
    rendered_puzzle_data = db.get_puzzle_data(rendered_puzzle)
    rendered_puzzle_name = rendered_puzzle_data["name"]

    st.title(f"{rendered_puzzle}. {rendered_puzzle_name}", anchor=False)

    if rendered_puzzle < current_puzzle:  # Already solved puzzle
        st.success("Tuto šifru jste už **vyřešili**.")
        if rendered_puzzle == len(puzzles):  # All puzzles solved
            st.success("Všechny šifry byly vyřešeny! 🎉")
            st.balloons()
        elif current_puzzle <= len(puzzles):  # Show current puzzle details
            current_puzzle_data = db.get_puzzle_data(current_puzzle)
            current_puzzle_name = current_puzzle_data["name"]
            team_path = db.get_team_path(current_user)
            current_puzzle_location, specification = current_puzzle_data[f"location_{team_path}"].split("|")  # type: ignore[literal-required]
            st.write(f"Lokace poslední odemčené šifry je [zde]({current_puzzle_location}), upřesnítko: {specification}.")
            if st.button(f"Poslední odemčená šifra: **{current_puzzle}. {current_puzzle_name}**", type="primary"):
                st.session_state.current_page = f"puzzle_{current_puzzle}"
                st.rerun()

    elif rendered_puzzle > current_puzzle:   # Locked puzzle
        st.error("Tato šifra je **zamčená**. Vyřešte všechny předchozí šifry pro odemčení.")

    else:  # Current puzzle
        current_puzzle_data = db.get_puzzle_data(current_puzzle)
        current_puzzle_status = db.get_puzzle_status(current_user, current_puzzle)
        current_puzzle_name = current_puzzle_data["name"]
        team_path = db.get_team_path(current_user)
        current_puzzle_location, specification = current_puzzle_data[f"location_{team_path}"].split("|")  # type: ignore[literal-required]

        is_activated = current_puzzle_status["is_activated"]
        if is_activated:  # Solveable
            st.info("Tuto šifru už řešíte a čas vám běží.")
            is_hinted = current_puzzle_status["is_hinted"]
            if is_hinted:  # Show hint
                hint = current_puzzle_data["hint"]
                st.warning(f"**Nápověda:** {hint}")

            with st.form(f"solution_form_{current_puzzle}"):
                input_solution = st.text_input("Heslo:")
                submitted = st.form_submit_button("Odevzdat", type="primary")

                if submitted:  # Solution check
                    db.log_action(current_user, current_puzzle, "submit")
                    if db.submit_solution(current_user, current_puzzle, input_solution.upper()):
                        st.success("Správné heslo!")
                        sleep(2)
                        st.rerun()
                    else:
                        st.error("Nesprávné heslo!")

            cols1 = st.columns([1, 2, 1])
            cols2 = st.columns([1, 2, 1])

            # Download puzzle PDF button
            with cols1[2]:
                puzzle_filename = current_puzzle_data["filename"]
                if puzzle_filename and os.path.exists(f"puzzles/{puzzle_filename}.pdf"):
                    with open(f"puzzles/{puzzle_filename}.pdf", "rb") as file:
                        st.download_button(
                            label="Stáhnout šifru",
                            data=file,
                            file_name=f"{current_puzzle_name}.pdf",
                            mime="application/pdf",
                            type="secondary",
                            use_container_width=True
                        )
            
            # Download puzzle solution PDF button
            with cols2[2]:
                is_end = db.get_setting("is_end")
                is_end = False if is_end is None else is_end == "true"
                puzzle_filename = current_puzzle_data["filename"]
                if puzzle_filename and os.path.exists(f"solutions/{puzzle_filename}_reseni.pdf"):
                    with open(f"solutions/{puzzle_filename}_reseni.pdf", "rb") as file:
                        st.download_button(
                            label="Vzorové řešení",
                            data=file,
                            file_name=f"{current_puzzle_name} Řešení.pdf",
                            mime="application/pdf",
                            type="primary",
                            help="Bude dostupné po konci hry." if not is_end else None,
                            disabled=not is_end,
                            use_container_width=True
                        )

            # Hint and dead options
            hint_eligible = db.check_hint_eligiblity(current_user, current_puzzle)
            with cols1[0], st.popover("Získat nápovědu", type="primary", disabled=not hint_eligible,
                                      help="Nápovědu můžete získat až po 15 minutách od začátku řešení." 
                                      if not hint_eligible else None, use_container_width=True):
                if is_hinted:
                    st.write("Nápovědu jste už získali.")
                else:
                    st.write("Opravdu chcete získat nápovědu? Po nápovědě můžete za šifru získat nejvýše 1 bod.")
                    if st.button("Potvrdit", key="conf_1"):
                        st.success("Nápověda odemčena.")
                        db.log_action(current_user, current_puzzle, "hint")
                        sleep(2)
                        st.rerun()

            dead_eligible = db.check_dead_eligiblity(current_user, current_puzzle)
            with cols2[0], st.popover("Vzdát šifru", type="primary", disabled=not dead_eligible,
                                      help="Vzdát šifru můžete po získání nápovědy a až po 30 minutách od začátku řešení."
                                      if not dead_eligible else None, use_container_width=True):
                st.write("Opravdu chcete vzdát šifru? Po deadnutí nezískáte za šifru **žádné** body!")
                if st.button("Potvrdit", key="conf_2"):
                    st.success("Šifra deadnuta.")
                    db.log_action(current_user, current_puzzle, "dead")
                    db.dead_puzzle(current_user, current_puzzle)
                    sleep(2)
                    st.rerun()

        else:  # Not activated
            st.info("Pro zahájení řešení šifry zadejte aktivační kód.")
            st.warning(f"Lokace této šifry je [zde]({current_puzzle_location}), upřesnítko: {specification}.")

            with st.form(f"activation_form_{current_puzzle}"):
                input_code = st.text_input("Aktivační kód:")
                submitted = st.form_submit_button("Odevzdat", type="primary")

                if submitted:  # Activation code check
                    activation_code = current_puzzle_data["activation_code"]
                    if input_code.lower() == activation_code:
                        st.success("Šifra aktivována, můžete řešit.")
                        db.log_action(current_user, current_puzzle, "begin")
                        sleep(2)
                        st.rerun()
                    else:
                        st.error("Nesprávný kód!")
