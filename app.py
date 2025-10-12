import streamlit as st
import hashlib

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize user storage
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

def login_page():
    st.markdown("""
    <div style='background:#1E90FF; padding:2rem; border-radius:10px; text-align:center; color:white; margin-bottom:2rem;'>
        <h1>🚀 Performance Predictor</h1>
        <p>Login to track your performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Two columns layout
    col1, col2 = st.columns(2)
    
    # Login Section
    with col1:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                if username in st.session_state.users:
                    if st.session_state.users[username] == hash_password(password):
                        st.session_state.current_user = username
                        st.success(f"Welcome {username}!")
                        st.rerun()
                    else:
                        st.error("Wrong password!")
                else:
                    st.error("User not found!")
    
    # Register Section
    with col2:
        st.subheader("📝 Register")
        with st.form("register_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            register_btn = st.form_submit_button("Create Account")
            
            if register_btn:
                if new_user in st.session_state.users:
                    st.error("Username already exists!")
                elif new_pass != confirm_pass:
                    st.error("Passwords don't match!")
                elif len(new_pass) < 4:
                    st.error("Password must be 4+ characters")
                else:
                    st.session_state.users[new_user] = hash_password(new_pass)
                    st.success("Account created! Please login.")
                    st.rerun()

# Main Dashboard (after login)
def dashboard():
    st.title(f"Welcome, {st.session_state.current_user}!")
    st.write("This is your dashboard")
    
    if st.button("Logout"):
        st.session_state.current_user = None
        st.rerun()

# Run the app
if st.session_state.current_user:
    dashboard()
else:
    login_page()
