import streamlit as st
import sqlite3


# --- CSS HACK TO HIDE THE "PRESS ENTER TO SUBMIT FORM" TEXT ---
st.markdown("""
    <style>
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

ADMIN_PASSWORD = "EpsteinFuckNiggers"

# ==========================================
# 1. DATABASE SETUP
# ==========================================
def init_user_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, points INTEGER, time INTEGER)')

def init_data_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS data (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        action TEXT,
                        time TEXT,
                        successful INTEGER,
                        data TEXT
                        )''')  # possible actions: login, begin, hint, dead, submit

def check_login(username, password):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        result = c.fetchone()
        return result is not None

def create_user(username, password):
    try:
        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users VALUES (?, ?, 0, 0)", (username, password))
            return True
    except sqlite3.IntegrityError:
        return False

def remove_user(username):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username=?", (username,))
        return c.rowcount > 0

def edit_user(username, password, points, time):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.rowcount == 0:
            return False
        user_data = c.fetchone()
        password = password if password else user_data[1]
        points = points if points else user_data[2]
        time = time if time else user_data[3]
        c.execute("UPDATE users SET password=?, points=?, time=? WHERE username=?", (password, points, time, username))
        return c.rowcount > 0


init_user_db()

# ==========================================
# 2. SESSION MEMORY 
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "progress" not in st.session_state:
    st.session_state.progress = 0
if "current_page" not in st.session_state:
    st.session_state.current_page = "Task Overview"

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_action" not in st.session_state:
    st.session_state.admin_action = None

# ==========================================
# 3. ADMIN DASHBOARD
# ==========================================
if st.session_state.admin_logged_in:
    st.title("Admin Dashboard", anchor=False)
    
    st.subheader("Leaderboard", anchor=False)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY points DESC, time ASC")
    users = c.fetchall()
    conn.close()
    
    for i, user in enumerate(users):
        st.write(f"{i+1}. {user[0]} - {user[2]} - {user[3]}")
    
    st.subheader("Admin functions", anchor=False)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Create user", type="primary"):
            st.session_state.admin_action = "create_user"
            st.rerun()

    with col2:
        if st.button("Remove user", type="primary"):
            st.session_state.admin_action = "remove_user"
            st.rerun()

    with col3:
        if st.button("Edit user", type="primary"):
            st.session_state.admin_action = "edit_user"
            st.rerun()
    
    match st.session_state.admin_action:
        case "create_user":
            with st.form("create_user_form"):
                username = st.text_input("Username")
                password = st.text_input("Password")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if create_user(username, password):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error creating user")

        case "remove_user":
            with st.form("remove_user_form"):
                username = st.text_input("Username")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if remove_user(username):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error removing user")

        case "edit_user":
            with st.form("edit_user_form"):
                username = st.text_input("Username")
                password = st.text_input("Password")
                points = st.text_input("Points")
                time = st.text_input("Time")
                submitted = st.form_submit_button("Submit", type="primary")
                if submitted:
                    if edit_user(username, password, points, time):
                        st.session_state.admin_action = None
                        st.rerun()
                    else:
                        st.error("Error editing user")

    st.divider()
    
    if st.button("Logout of Admin", type="primary"):
        st.session_state.admin_logged_in = False
        st.session_state.admin_mode = False
        st.rerun()

# ==========================================
# 4. ADMIN LOGIN PAGE
# ==========================================
elif st.session_state.admin_mode:
    st.title("Admin Access", anchor=False)
    st.write("Please enter the master password.")
    
    with st.form("admin_login_form"):
        admin_pass = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login as Admin", type="primary", use_container_width=True)
        
        if submitted:
            if admin_pass == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect admin password.")
    
    if st.button("Back to User Login", use_container_width=True):
        st.session_state.admin_mode = False
        st.rerun()

# ==========================================
# 5. USER LOGIN PAGE
# ==========================================
elif not st.session_state.logged_in:
    st.title("Welcome to the Event App", anchor=False)
    st.write("Please log in to continue.")
    
    with st.form("user_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submitted:
            if check_login(username, password):
                st.session_state.logged_in = True
                st.rerun() 
            else:
                st.error("Incorrect username or password.")
            
    st.divider()
    
    if st.button("Admin Login", use_container_width=True):
        st.session_state.admin_mode = True
        st.rerun()

# ==========================================
# 6. MAIN APP & TASKS
# ==========================================
else:
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
