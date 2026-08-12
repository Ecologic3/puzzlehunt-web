import streamlit as st
import db_funcs

def render():
    st.sidebar.title("Navigation", anchor=False)
    
    pages = ["Task Overview", "Task 1", "Task 2", "Task 3", "Task 4", "Task 5"]
    
    for p in pages:
        button_type = "primary" if st.session_state.current_page == p else "secondary"
        if st.sidebar.button(p, type=button_type, use_container_width=True):
            st.session_state.current_page = p
            st.rerun()

    st.sidebar.divider() 
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.progress = 0 
        st.session_state.current_page = "Task Overview" 
        st.rerun()

    secret_codes = {
        1: "apple", 2: "banana", 3: "cherry", 4: "date", 5: "elderberry"
    }

    page = st.session_state.current_page

    if page == "Task Overview":
        st.title("Your Tasks", anchor=False)
        st.write("Click on an unlocked task to enter its secret code!")
        
        for i in range(1, 6):
            if st.session_state.progress >= i:
                if st.button(f"Task {i}: Solved! ✅", use_container_width=True):
                    st.session_state.current_page = f"Task {i}"
                    st.rerun()
            elif st.session_state.progress == i - 1:
                if st.button(f"Task {i}: Unlocked - Waiting for code 🔓", type="primary", use_container_width=True):
                    st.session_state.current_page = f"Task {i}"
                    st.rerun()
            else:
                st.button(f"Task {i}: Locked 🔒", disabled=True, use_container_width=True)

    else:
        task_num = int(page.split(" ")[1])
        st.title(f"Task {task_num}", anchor=False)
        
        if st.session_state.progress >= task_num:
            if task_num == 5:
                st.success("Correct! You have completed the final task! 🎉 All tasks are done!")
                st.balloons()
            else:
                st.success("You have already solved this task!")
                if st.button(f"Go to Task {task_num + 1}", type="primary"):
                    st.session_state.current_page = f"Task {task_num + 1}"
                    st.rerun()
                    
        elif st.session_state.progress < task_num - 1:
            st.error(f"**Locked!** You must solve Task {task_num - 1} before you can attempt this task.")
            
        else:
            st.info("This task is unlocked. Enter the secret code to solve it.")
            
            with st.form(f"task_form_{task_num}"):
                entered_code = st.text_input("Secret Code:")
                submitted = st.form_submit_button("Submit Code", type="primary")
                
                if submitted:
                    if entered_code.lower() == secret_codes[task_num]:
                        st.session_state.progress = task_num 
                        st.rerun() 
                    else:
                        st.error("Incorrect code. Try again!")