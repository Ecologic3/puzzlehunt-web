import streamlit as st
import db_funcs as db


def render_main():
    st.sidebar.title("Přehled", anchor=False)
    
    button_type = "primary" if st.session_state.current_page == "puzzles" else "secondary"
    if st.sidebar.button("Seznam šifer", type=button_type, use_container_width=True):
        st.session_state.current_page = p
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

    page = st.session_state.current_page

    st.title("Seznam šifer", anchor=False)
    st.write("*Klikněte na odemčenou šifru pro zadání aktivačního kódu nebo hesla*")

    current_puzzle = db.get_current_puzzle(st.session_state.current_user)
    for p in puzzles:
        puzzle_order = int(p.replace("puzzle_", ""))
        puzzle_name = db.get_puzzle_name(puzzle_order)

        if puzzle_order < current_puzzle:
            if st.button(f"{puzzle_order}. Šifra ({puzzle_name}): Vyřešena ✅", use_container_width=True):  # TODO check if dead
                st.session_state.current_page = p
                st.rerun()
        elif puzzle_order == current_puzzle:
            if st.button(f"{puzzle_order}. Šifra ({puzzle_name}): Připravena na řešení 🔓", type="primary", use_container_width=True):
                st.session_state.current_page = p
                st.rerun()
        else:
            st.button(f"{puzzle_order}. Šifra ({puzzle_name}): Zamčena 🔒", disabled=True, use_container_width=True)


def render_puzzle(puzzle: str):
    task_num = 5
    st.title(f"Puzzle {task_num}", anchor=False)
    
    if st.session_state.progress >= task_num:
        if task_num == 5:
            st.success("Correct! You have completed the final puzzle! 🎉 All puzzles are done!")
            st.balloons()
        else:
            st.success("You have already solved this puzzle!")
            if st.button(f"Go to Puzzle {task_num + 1}", type="primary"):
                st.session_state.current_page = f"Puzzle {task_num + 1}"
                st.rerun()
                
    elif st.session_state.progress < task_num - 1:
        st.error(f"**Locked!** You must solve Puzzle {task_num - 1} before you can attempt this puzzle.")
        
    else:
        st.info("This puzzle is unlocked. Enter the secret code to solve it.")
        
        with st.form(f"task_form_{task_num}"):
            entered_code = st.text_input("Secret Code:")
            submitted = st.form_submit_button("Submit Code", type="primary")
            
            if submitted:
                if entered_code.lower() == secret_codes[task_num]:
                    st.session_state.progress = task_num 
                    st.rerun() 
                else:
                    st.error("Incorrect code. Try again!")
