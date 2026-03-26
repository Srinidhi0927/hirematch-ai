import sqlite3
import hashlib
import streamlit as st

DB_FILE = "users.db"


# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, email, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)",
                  (username, email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == hash_password(password)


# ---------------- SESSION ---------------- #

def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"


def switch_auth_mode(mode):
    st.session_state.auth_mode = mode


# ---------------- LOGIN ---------------- #

def login_form():
    st.markdown("<div class='main-header'>AI Resume Analyzer</div>", unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):

        st.markdown("""
            <div class='custom-label label-anim1'>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2BE25F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                Username
            </div>
        """, unsafe_allow_html=True)
        username = st.text_input(
            "Username",
            label_visibility="collapsed",
            placeholder="Enter your username"
        )

        st.markdown("""
            <div class='custom-label label-anim2'>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2BE25F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                Password
            </div>
        """, unsafe_allow_html=True)
        password = st.text_input(
            "Password",
            type="password",
            label_visibility="collapsed",
            placeholder="Enter your password"
        )

        submit = st.form_submit_button("Log In", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Please enter both username and password.")
            elif verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")

    st.markdown("<div class='toggle-text text-anim'>• Don't have an account? •</div>", unsafe_allow_html=True)

    if st.button("Create account", use_container_width=True):
        switch_auth_mode("signup")
        st.rerun()


# ---------------- SIGNUP ---------------- #

def signup_form():
    st.markdown("<div class='main-header'>AI Resume Analyzer</div>", unsafe_allow_html=True)

    with st.form("signup_form", clear_on_submit=False):

        st.markdown("""
            <div class='custom-label label-anim1'>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2BE25F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                Username
            </div>
        """, unsafe_allow_html=True)
        username = st.text_input("Username", label_visibility="collapsed", placeholder="Enter your username")

        st.markdown("""
            <div class='custom-label label-anim2'>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2BE25F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                Email
            </div>
        """, unsafe_allow_html=True)
        email = st.text_input("Email", label_visibility="collapsed", placeholder="Enter your email")

        st.markdown("""
            <div class='custom-label label-anim3'>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2BE25F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                Password
            </div>
        """, unsafe_allow_html=True)
        password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Create a password")

        st.markdown("""
            <div class='custom-label label-anim4'>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2BE25F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                Confirm Password
            </div>
        """, unsafe_allow_html=True)
        confirm_password = st.text_input("Confirm Password", type="password", label_visibility="collapsed", placeholder="Confirm your password")

        submit = st.form_submit_button("Sign Up", use_container_width=True)

        if submit:
            if not username or not email or not password:
                st.error("Fill all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                if create_user(username, email, password):
                    st.success("Account created successfully!")
                else:
                    st.error("Username already exists")

    st.markdown("<div class='toggle-text text-anim'>• Already have an account? •</div>", unsafe_allow_html=True)

    if st.button("Return to Log In", use_container_width=True):
        switch_auth_mode("login")
        st.rerun()


# ---------------- AUTH PAGE ---------------- #

def show_auth_page():
    init_db()
    init_session_state()

    st.markdown("""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap');

    /* ----------- KEYFRAMES ----------- */

    @keyframes gradientShift {
        0% { background-position: 0% 50%; opacity: 0.8;}
        50% { background-position: 100% 50%; opacity: 1;}
        100% { background-position: 0% 50%; opacity: 0.8;}
    }

    @keyframes cardEnter {
        0% { opacity: 0; transform: translateY(30px) scale(0.95); }
        100% { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes neonPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(43,226,95,0.4), 0 0 20px rgba(43,226,95,0.2); }
        50% { text-shadow: 0 0 20px rgba(43,226,95,0.8), 0 0 40px rgba(43,226,95,0.5); }
    }

    @keyframes formFadeIn {
        from { opacity: 0; transform: translateX(-15px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes glowBorderPulse {
        0%, 100% { box-shadow: 0 0 15px rgba(43,226,95,0.1), inset 0 0 5px rgba(43,226,95,0.05); }
        50% { box-shadow: 0 0 30px rgba(43,226,95,0.3), inset 0 0 15px rgba(43,226,95,0.1); }
    }
    
    @keyframes slowFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }

    /* ----------- GLOBAL ----------- */

    .stApp {
        background-color: #030406 !important;
        background-image: 
            radial-gradient(ellipse at bottom center, rgba(43,226,95,0.25) 0%, rgba(5,5,5,1) 60%),
            url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%232be25f' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        background-attachment: fixed !important;
        font-family: 'Sora', sans-serif;
        color: white;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 0.8rem;
    }

    /* ----------- HEADER ----------- */
    .main-header {
        text-align: center;
        font-size: 2.3rem;
        font-weight: 600;
        margin-bottom: 2rem;
        color: #A3E4AE;
        animation: neonPulse 3s infinite ease-in-out;
        letter-spacing: 0.5px;
    }

    /* ----------- LABELS & TEXT DECORATION ----------- */
    .custom-label {
        display: flex;
        align-items: center;
        font-size: 0.95rem;
        color: #CFCFCF;
        margin-bottom: 0.3rem;
        margin-top: 0.6rem;
        font-weight: 400;
        transition: color 0.3s, transform 0.3s;
        opacity: 0; /* for animation */
        animation: formFadeIn 0.5s forwards;
    }

    .custom-label:hover {
        color: #2BE25F;
        transform: translateX(3px);
    }

    .label-anim1 { animation-delay: 0.2s; }
    .label-anim2 { animation-delay: 0.3s; }
    .label-anim3 { animation-delay: 0.4s; }
    .label-anim4 { animation-delay: 0.5s; }

    /* ----------- MAIN CARD ----------- */
    .auth-card {
        background: rgba(10, 10, 15, 0.45) !important;
        border-radius: 20px !important;
        backdrop-filter: blur(25px);
        padding: 2.2rem !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 40px rgba(43,226,95,0.06), 0 0 100px rgba(43,226,95,0.03) !important;
        animation: cardEnter 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards, slowFloat 7s infinite ease-in-out 0.9s;
        transition: transform 0.4s ease, border-color 0.4s ease;
    }

    .auth-card:hover {  
        border-color: rgba(43,226,95,0.3) !important;
    }

    /* CURSOR GLOW (JavaScript tracking overlay) */
    .auth-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at var(--x,50%) var(--y,50%), rgba(43,226,95,0.18), transparent 45%);
        opacity: 0;
        transition: opacity 0.5s, background 0.1s ease;
        pointer-events: none;
        z-index: 0;
    }
    .auth-card:hover::before {
        opacity: 1;
    }

    /* ----------- FORM BACKGROUND CONTAINER ----------- */
    div[data-testid="stForm"] {
        background: rgba(15, 15, 20, 0.5) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        animation: formFadeIn 0.8s backwards;
        animation-delay: 0.1s;
        transition: border 0.3s ease, background 0.3s ease;
        position: relative;
        z-index: 1;
        margin-bottom: 1.5rem !important;
    }
    div[data-testid="stForm"]:hover {
        border-color: rgba(43,226,95,0.2) !important;
        background: rgba(15,15,18,0.3) !important;
    }

    /* ----------- INPUTS ----------- */
    input {
        background: #111113 !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.65rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        opacity: 0;
        animation: formFadeIn 0.5s forwards;
        animation-delay: 0.3s;
    }

    input:focus {
        border-color: rgba(43,226,95,0.8) !important;
        background: #08080A !important;
        transform: scale(1.01);
        animation: glowBorderPulse 3s infinite alternate;
        outline: none !important;
    }
    
    input:hover:not(:focus) {
        border-color: rgba(43,226,95,0.3) !important;
    }

    /* ----------- BUTTONS ----------- */
    div[data-testid="stForm"] div.stButton > button {
        border-radius: 8px !important;
        border: 1px solid rgba(43,226,95,0.3) !important;
        background: linear-gradient(90deg, transparent, rgba(43,226,95,0.05)) !important;
        color: #A3E4AE !important;
        font-weight: 500 !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        opacity: 0;
        animation: formFadeIn 0.5s forwards;
        animation-delay: 0.4s;
        margin-top: 1.2rem !important;
        width: 100% !important;
        position: relative;
        overflow: hidden;
    }

    div[data-testid="stForm"] div.stButton > button:hover {
        background: rgba(43,226,95,0.15) !important;
        border-color: #2BE25F !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(43,226,95,0.4), inset 0 0 10px rgba(43,226,95,0.2) !important;
        transform: translateY(-2px);
    }
    
    div[data-testid="stForm"] div.stButton > button:active {
        transform: translateY(1px) scale(0.98);
        box-shadow: 0 0 10px rgba(43,226,95,0.2) !important;
    }

    div[data-testid="stVerticalBlock"] > div.stButton > button {
        background: rgba(10,10,10,0.6) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        color: #A3E4AE !important; 
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        opacity: 0;
        animation: formFadeIn 0.5s forwards;
        animation-delay: 0.5s;
    }
    div[data-testid="stVerticalBlock"] > div.stButton > button:hover {
        border-color: rgba(43,226,95,0.3) !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 15px rgba(43,226,95,0.2) !important;
        transform: translateY(-2px);
    }
    div[data-testid="stVerticalBlock"] > div.stButton > button:active {
        transform: translateY(1px) scale(0.98);
    }

    .toggle-text {
        text-align: center;
        font-size: 0.9rem;
        color: #777;
        margin-top: 0.8rem;
        margin-bottom: 0.4rem;
        opacity: 0;
        animation: formFadeIn 0.5s forwards;
        animation-delay: 0.6s;
        transition: color 0.3s, text-shadow 0.3s;
    }
    
    .toggle-text:hover {
        color: #A3E4AE !important;
        text-shadow: 0 0 8px rgba(43,226,95,0.4);
    }

    </style>

    <script>
    document.addEventListener("mousemove", function(e) {
        const card = window.parent.document.querySelector('.auth-card');
        if(card){
            const rect = card.getBoundingClientRect();
            card.style.setProperty('--x', (e.clientX - rect.left) + 'px');
            card.style.setProperty('--y', (e.clientY - rect.top) + 'px');
        }
    });
    </script>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)

        if st.session_state.auth_mode == "login":
            login_form()
        else:
            signup_form()

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------- LOGOUT ---------------- #

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.auth_mode = "login"
    st.rerun()
