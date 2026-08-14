import streamlit as st
import db_funcs as db
from time import sleep


def render_navigation():
    st.sidebar.title("Přehled", anchor=False)
    
    button_type = "primary" if st.session_state.current_page == "puzzles" else "secondary"
    if st.sidebar.button("Seznam šifer", type=button_type, use_container_width=True):
        st.session_state.current_page = "puzzles"
        st.rerun()

    puzzles = db.get_active_puzzles()
    for p in puzzles:
        button_type = "primary" if st.session_state.current_page == p else "secondary"
        puzzle_order = p.replace("puzzle_", "")
        page_name = puzzle_order + ". " + db.get_puzzle_name(int(puzzle_order))
        if st.sidebar.button(page_name, type=button_type, use_container_width=True):
            st.session_state.current_page = p
            st.rerun()

    st.sidebar.divider() 
    
    if st.sidebar.button("Odhlásit se", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.current_page = "login" 
        st.rerun()
    
    with st.sidebar.expander("Nastavit heslo"):
        with st.form("set_password"):
            new_password = st.text_input("Nové heslo:")
            submitted = st.form_submit_button("Nastavit", type="primary")

            if submitted:
                if len(new_password) < 5:
                    st.error("Heslo musí mít alespoň 5 znaků.")
                else:
                    db.set_password(st.session_state.current_user, new_password)
                    st.success("Heslo úspěšně nastaveno. Stále však můžete používat i počáteční heslo.")

    
    st.sidebar.caption("V případě jakýchkoliv problémů volejte Adamovi: +421 949 327 686")


def render_main():
    st.title("Seznam šifer", anchor=False)
    st.write("Klikněte na odemčenou šifru pro zadání aktivačního kódu nebo hesla")
    st.write("*Nezapomeňte zadat aktivační kód ihned po nalezení šifry!*")

    puzzles = db.get_active_puzzles()
    current_puzzle = db.get_current_puzzle(st.session_state.current_user)
    next_puzzle_location, specification = db.get_puzzle_location(current_puzzle).split("|")
    st.write(f"Lokace poslední odemčené šifry je [zde]({next_puzzle_location}), upřesnítko: {specification}.")
    for p in puzzles:
        puzzle_order = int(p.replace("puzzle_", ""))
        puzzle_name = db.get_puzzle_name(puzzle_order)

        if puzzle_order < current_puzzle:
            is_deaded = db.is_deaded(st.session_state.current_user, puzzle_order)
            solved_status = "Deadnuta ❎" if is_deaded else "Vyřešena ✅"
            if st.button(f"{puzzle_order}. {puzzle_name}: {solved_status}", use_container_width=True):
                st.session_state.current_page = p
                st.rerun()
        elif puzzle_order == current_puzzle:
            is_activated = db.is_activated(st.session_state.current_user, puzzle_order)
            activated_status = "V řešení 💭" if is_activated else "Připravena na řešení 🔓"
            if st.button(f"{puzzle_order}. {puzzle_name}: {activated_status}", type="primary", use_container_width=True):
                st.session_state.current_page = p
                st.rerun()
        else:
            st.button(f"{puzzle_order}. {puzzle_name}: Zamčena 🔒", disabled=True, use_container_width=True)


def render_puzzle(puzzle_order: str):
    puzzles = db.get_active_puzzles()
    puzzle_order_number = int(puzzle_order.replace("puzzle_", ""))
    puzzle_name = db.get_puzzle_name(puzzle_order_number)

    st.title(f"{puzzle_order_number}. {puzzle_name}", anchor=False)

    current_puzzle = db.get_current_puzzle(st.session_state.current_user)
    if puzzle_order_number < current_puzzle:
        if puzzle_order_number == len(puzzles):
            st.success("Všechny šifry byly vyřešeny! 🎉")
            st.balloons()
        else:
            st.success("Tuto šifru jste už **vyřešili**.")
            next_puzzle_name = db.get_puzzle_name(current_puzzle)
            next_puzzle_location, specification = db.get_puzzle_location(current_puzzle).split("|")
            st.write(f"Lokace poslední odemčené šifry je [zde]({next_puzzle_location}), upřesnítko: {specification}.")
            if st.button(f"Poslední odemčená šifra: **{current_puzzle}. {next_puzzle_name}**", type="primary"):
                st.session_state.current_page = "puzzle_" + str(current_puzzle)
                st.rerun()

    elif puzzle_order_number > current_puzzle:
        st.error(f"Tato šifra je **zamčená**. Vyřešte všechny předchozí šifry pro odemčení.")
        
    else:
        is_activated = db.is_activated(st.session_state.current_user, puzzle_order_number)
        if is_activated:
            st.info("Tuto šifru už řešíte a čas vám běží.")

            with st.form(f"puzzle_form_{puzzle_order_number}"):
                input_solution = st.text_input("Heslo:")
                submitted = st.form_submit_button("Odevzdat", type="primary")

                if submitted:
                    db.log_action(st.session_state.current_user, current_puzzle, "submit")
                    solution = db.get_puzzle_solution(puzzle_order_number)  # TODO logging action, logging submit, process action
                    if entered_code.upper() == solution:
                        pass
                        st.success("Správné heslo!")
                        sleep(2)
                        st.rerun()
                    else:
                        st.error("Nesprávné heslo!")

            hint_eligible = db.check_hint_eligiblity(st.session_state.current_user, current_puzzle)
            with st.popover("Získat nápovědu", type="primary", disabled=False):
                st.write("Opravdu chcete získat nápovědu? Po nápovědě můžete za šifru získat nejvýše 1 bod.")
                if st.button("Potvrdit", key="conf_1"):
                    db.log_action(st.session_state.current_user, current_puzzle, "hint")
                    pass

            dead_eligible = db.check_dead_eligiblity(st.session_state.current_user, current_puzzle)
            with st.popover("Vzdát šifru", type="primary", disabled=not dead_eligible):
                st.write("Opravdu chcete vzdát šifru? Po deadnutí nezískáte za šifru **žádné** body!")
                if st.button("Potvrdit", key="conf_2"):
                    db.log_action(st.session_state.current_user, current_puzzle, "dead")
                    pass

        else:
            st.info("Pro zahájení řešení šifry zadejte aktivační kód.")

            with st.form(f"puzzle_activation_form_{puzzle_order_number}"):
                input_code = st.text_input("Aktivační kód:")
                submitted = st.form_submit_button("Odevzdat", type="primary")

                if submitted:
                    activation_code = db.get_puzzle_activation_code(puzzle_order_number)
                    if input_code.lower() == activation_code:
                        st.success("Šifra aktivována, můžete řešit.")
                        db.log_action(st.session_state.current_user, current_puzzle, "begin")
                        sleep(3)
                        st.rerun() 
                    else:
                        st.error("Nesprávný kód!")
