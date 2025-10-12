import streamlit as st
import hashlib
import re

# Password hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Strong password validation
def is_strong_password(password):
    """
    Password must have:
    - At least 1 capital letter
    - At least 3 small letters  
    - At least 1 digit
    - Minimum 6 characters total
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    capital_count = len(re.findall(r'[A-Z]', password))
    small_count = len(re.findall(r'[a-z]', password))
    digit_count = len(re.findall(r'[0-9]', password))
    
    errors = []
    if capital_count < 1:
        errors.append("1 capital letter (A-Z)")
    if small_count < 3:
        errors.append("3 small letters (a-z)")
    if digit_count < 1:
        errors.append("1 digit (0-9)")
    
    if errors:
        error_message = "Password must contain: " + ", ".join(errors)
        return False, error_message
    
    return True, "Strong password!"

# Complete login page with password validation
def login_page():
    st.markdown("""
    <div style='background:#1E90FF; padding:2rem; border-radius:10px; text-align:center; color:white; margin-bottom:2rem;'>
        <h1>🚀 Performance Predictor</h1>
        <p>Secure Login System</p>
    </div>
    """, unsafe_allow_html=True)
    
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
                    hashed_input_password = hash_password(password)
                    if st.session_state.users[username]['password'] == hashed_input_password:
                        st.session_state.current_user = username
                        st.success(f"Welcome {username}!") 
                        st.rerun()
                    else:
                        st.error("❌ Wrong password!")
                else:
                    st.error("❌ User not found!")
    
    # Register Section
    with col2:
        st.subheader("📝 Register")
        with st.form("register_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password", 
                                   help="Must contain: 1 CAPITAL, 3 small, 1 digit")
            confirm_pass = st.text_input("Confirm Password", type="password")
            register_btn = st.form_submit_button("Create Account")
            
            if register_btn:
                # Check if username exists
                if new_user in st.session_state.users:
                    st.error("❌ Username already exists!")
                
                # Check if passwords match
                elif new_pass != confirm_pass:
                    st.error("❌ Passwords don't match!")
                
                # Check password strength
                else:
                    is_strong, message = is_strong_password(new_pass)
                    
                    if is_strong:
                        # Save user with hashed password
                        st.session_state.users[new_user] = {
                            'password': hash_password(new_pass),
                            'created_at': st.datetime.now()
                        }
                        st.success("✅ Account created successfully! Please login.")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

# Initialize user storage
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Run the app
if st.session_state.current_user:
    st.title(f"Welcome, {st.session_state.current_user}!")
    if st.button("Logout"):
        st.session_state.current_user = None
        st.rerun()
else:
    login_page()
