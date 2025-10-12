# app.py (Authentication Focus with Dark Theme and Password Hashing)

# ===== IMPORTS AND INITIAL SETUP =====
import streamlit as st
import hashlib
import re # For regex validation
import time
from datetime import date # Keep date for log structure consistency

# --- STATE MANAGEMENT INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_db' not in st.session_state:
    st.session_state.user_db = {}
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# --- CONSTANTS FOR THE CHALLENGE (Used for structure when logged in) ---
CHALLENGE_STAGES = {
    'Silver': {'duration': 15, 'rules': {'Give 2 hours daily in your field': True, 'Avoid all distractions': True, 'Fill the form daily': True}},
    'Platinum': {'duration': 30, 'rules': {'Give 4 hours daily in your field': True, 'Avoid all distractions': True, 'Do 1 hour of exercise daily': True, 'Drink 5 liters of water': True, 'Fill the form daily': True}},
    'Gold': {'duration': 60, 'rules': {'Give 6 hours daily in your field': True, 'Do 1 hour of exercise': True, 'Avoid all distractions': True, 'Drink 5 liters of water': True, 'Wake up early (4 AM or 5 AM)': True, 'Sleep early (8 PM or 9 PM)': True, 'Avoid junk food': True, 'Avoid sugar': True, 'Fill the form daily': True}}
}

# --- PAGE CONFIGURATION & CUSTOM CSS (UPDATED FOR DARK THEME) ---
st.set_page_config(
    page_title="Elite Performance Engine",
    page_icon="👑",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Dark Theme Setup */
    .stApp { 
        background-color: #0A1931; /* Deep Navy Blue Background */
        color: white; /* Default text color is white */
    } 
    /* Set text color to white globally */
    .stApp, .stApp * { 
        color: white;
    }
    
    /* Input field label and text color */
    .stSelectbox label, .stNumberInput label, .stTextInput label, .stCheckbox label, .stRadio label { 
        color: #ADD8E6 !important; /* Light blue for labels */
        font-weight: 600; 
    }
    
    /* Headings */
    h1, h2, h3, h4, .main-header { 
        color: #90CAF9; /* Light, bright blue for headers */
        font-weight: 800; 
    }
    
    /* Main Content Area (Dashboard) */
    [data-testid="stSidebar"] { 
        background-color: #123456; /* Sidebar slightly different dark blue */
        color: white; 
    }
    [data-testid="stVerticalBlock"] {
        background-color: #182B49; /* Darker blue for main content containers */
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    
    /* Login/Sign Up buttons */
    .stButton>button { 
        background-color: #5C6BC0; /* Medium Blue for login/signup */
        color: white; 
        font-weight: bold; 
        border-radius: 8px; 
        padding: 10px 20px; 
        border: none;
    }
    
    /* Green Logout Button (Specific Request) */
    .green-button button {
        background-color: #4CAF50 !important; /* Green */
    }

    /* Success/Error/Info boxes */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 8px;
        padding: 10px;
    }
    .stSuccess { background-color: #1B5E20; color: #E8F5E9; }
    .stError { background-color: #D32F2F; color: #FFEBEE; }
    .stInfo { background-color: #0277BD; color: #E1F5FE; }
    
    /* Input text color fix */
    div[data-testid="stForm"] input[type="text"], div[data-testid="stForm"] input[type="password"] {
        color: #FFFFFF !important;
        background-color: #182B49; 
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- SECURITY FUNCTIONS ---

def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def validate_password(password):
    """
    Validates the password based on strict rules:
    - At least 1 Capital character
    - At least 3 Small characters
    - At least 1 Digit
    """
    errors = []
    
    # Check for 1 Capital
    if not re.search(r'[A-Z]', password):
        errors.append("1 Capital character (A-Z)")
    
    # Check for 3 Small characters
    if len(re.findall(r'[a-z]', password)) < 3:
        errors.append("3 Small characters (a-z)")
        
    # Check for 1 Digit
    if not re.search(r'\d', password):
        errors.append("1 Digit (0-9)")
        
    return errors

# --- AUTHENTICATION UI ---

def register_user():
    st.subheader("New Account Registration")
    
    with st.form("register_form"):
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        
        submitted = st.form_submit_button("Sign Up Now")

        if submitted:
            if new_user in st.session_state.user_db:
                st.error("Username already exists. Please log in or choose another name.")
                return
            
            # --- Password Validation ---
            validation_errors = validate_password(new_pass)
            if validation_errors:
                st.error("❌ Password failed validation.")
                st.markdown(
                    f"**Password must contain:**"
                    f"<ul>"
                    f"<li>{validation_errors[0]}</li>"
                    f"<li>{validation_errors[1]}</li>"
                    f"<li>{validation_errors[2]}</li>"
                    f"</ul>", unsafe_allow_html=True
                )
                return

            if not new_user or not new_pass:
                st.error("Username and Password cannot be empty.")
            else:
                # Store hashed password and initialize user profile
                st.session_state.user_db[new_user] = {
                    'password_hash': hash_password(new_pass),
                    'profile': {},
                    'challenge': {
                        'status': 'Pending', 
                        'stage': None, 
                        'daily_log': {}, 
                        'penalty_amount': 0.0, 
                        'badges': [], 
                        'stage_days_completed': 0, 
                        'streak_days_penalty': 0,
                        'last_task_message': False 
                    }
                }
                st.success("Registration successful! Redirecting to Login...")
                time.sleep(1)
                st.session_state.page = 'login'
                st.rerun()

    if st.button("Go back to Login"):
        st.session_state.page = 'login'
        st.rerun()

def login_user():
    st.markdown('<h1 class="main-header">Elite Performance Engine</h1>', unsafe_allow_html=True)
    st.subheader("User Login")
    
    with st.form("login_form"):
        user = st.text_input("Username", key="log_user")
        password = st.text_input("Password", type="password", key="log_pass")
        
        submitted = st.form_submit_button("Login")

        if submitted:
            if user not in st.session_state.user_db:
                st.error("User does not exist. Please sign up for a new account.")
            elif st.session_state.user_db[user]['password_hash'] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success(f"Welcome back, {user}!")
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid Password.")
    
    st.markdown("---")
    st.info("If you don't have an account, please make an account below.")
    if st.button("Sign Up"):
        st.session_state.page = 'register'
        st.rerun()

# --- DASHBOARD UI (SIMPLIFIED FOR TESTING) ---

def dashboard_ui():
    st.title(f"Welcome to Your Dashboard, {st.session_state.username}!")
    st.markdown("---")
    
    # Green Logout Button
    st.markdown('<div class="green-button">', unsafe_allow_html=True)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = 'login'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Your Next Steps")
    
    if st.session_state.user_db[st.session_state.username]['challenge']['status'] == 'Pending':
        st.info("You haven't started the challenge yet! Start with the setup.")
        if st.button("Start Challenge Setup"):
            st.session_state.page = 'challenge_setup'
            st.rerun()
    else:
        st.success(f"Challenge Status: {st.session_state.user_db[st.session_state.username]['challenge']['status']}")
        if st.button("Go to Daily Tracking"):
            st.session_state.page = 'daily_tracking'
            st.rerun()

# --- MAIN APP ROUTER ---

def main_app():
    if st.session_state.logged_in:
        # Placeholder for display_user_profile, which you can re-implement later
        
        if st.session_state.page == 'dashboard' or st.session_state.page == 'challenge_intro' or st.session_state.page == 'challenge_rules':
             dashboard_ui() # Currently simplified to dashboard
        elif st.session_state.page == 'challenge_setup':
            st.title("Challenge Setup Page (To be built)") # Placeholder
        elif st.session_state.page == 'daily_tracking':
            st.title("Daily Tracking Page (To be built)") # Placeholder
        
        # Simple sidebar structure for logged-in users
        st.sidebar.title("Navigation")
        if st.sidebar.button("Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
        if st.sidebar.button("Daily Tracking"):
            st.session_state.page = 'daily_tracking'
            st.rerun()
        
    else:
        if st.session_state.page == 'register':
            register_user()
        else:
            login_user()

if __name__ == "__main__":
    main_app()
