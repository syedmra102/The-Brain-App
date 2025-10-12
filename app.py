# app.py (Final Authentication Focus with Clean Design, New Dark Theme, and Visible Password Rules)

# ===== IMPORTS AND INITIAL SETUP =====
import streamlit as st
import hashlib
import re # For regex validation
import time
from datetime import date 

# --- STATE MANAGEMENT INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_db' not in st.session_state:
    st.session_state.user_db = {}
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# --- CONSTANTS FOR THE CHALLENGE (Placeholder for structure) ---
CHALLENGE_STAGES = {
    'Silver': {'duration': 15, 'rules': {'Give 2 hours daily in your field': True, 'Avoid all distractions': True, 'Fill the form daily': True}},
    'Platinum': {'duration': 30, 'rules': {'Give 4 hours daily in your field': True, 'Avoid all distractions': True, 'Do 1 hour of exercise daily': True, 'Drink 5 liters of water': True, 'Fill the form daily': True}},
    'Gold': {'duration': 60, 'rules': {'Give 6 hours daily in your field': True, 'Do 1 hour of exercise': True, 'Avoid all distractions': True, 'Drink 5 liters of water': True, 'Wake up early (4 AM or 5 AM)': True, 'Sleep early (8 PM or 9 PM)': True, 'Avoid junk food': True, 'Avoid sugar': True, 'Fill the form daily': True}}
}

# --- PAGE CONFIGURATION & CUSTOM CSS (NEW CLEAN DARK THEME) ---
st.set_page_config(
    page_title="Elite Performance Engine",
    page_icon="👑",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* New, Softer Dark Theme */
    
    /* General Background - Dark Gray */
    .stApp { 
        background-color: #1D2B3F; /* Soft Dark Gray/Blue */
        color: white; 
    } 
    /* Global Text Color - White */
    .stApp, .stApp * { 
        color: white !important;
    }
    
    /* Headings - Light Blue for contrast */
    h1, h2, h3, h4, .main-header { 
        color: #74b9ff !important; /* Soft Light Blue */
        font-weight: 700; 
    }
    
    /* Input field label color */
    .stSelectbox label, .stNumberInput label, .stTextInput label, .stCheckbox label, .stRadio label { 
        color: white !important; 
        font-weight: 600; 
    }
    
    /* Dashboard Block Background - Dark Slate Blue */
    [data-testid="stVerticalBlock"] {
        background-color: #2E475E; /* Darker background for dashboard/main content */
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    
    /* Button Color - Green */
    .stButton>button { 
        background-color: #4CAF50 !important; /* Vibrant Green */
        color: white !important; 
        font-weight: bold; 
        border-radius: 8px; 
        padding: 10px 20px; 
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45A049 !important; /* Slightly darker green on hover */
    }
    
    /* Input field styling for contrast and border */
    div[data-testid="stForm"] input[type="text"], 
    div[data-testid="stForm"] input[type="password"] {
        color: #FFFFFF !important;
        background-color: #1D2B3F; /* Match App BG */
        border: 1px solid #74b9ff; /* Light blue border */
        border-radius: 5px;
    }

    /* Error and Success boxes must have good contrast */
    .stSuccess { background-color: #1B5E20; color: #E8F5E9; }
    .stError { background-color: #D32F2F; color: #FFEBEE; }

    /* Custom class to center and limit the size of the auth forms */
    .centered-form-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
        background-color: #2E475E; /* Match dashboard background for the form container */
        border-radius: 12px;
        border: 2px solid #74b9ff;
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
    st.markdown('<h1 class="main-header" style="text-align: center;">Elite Performance Engine</h1>', unsafe_allow_html=True)
    st.subheader("New Account Registration")
    
    # --- Centering and shortening the form ---
    st.markdown('<div class="centered-form-container">', unsafe_allow_html=True)
    
    # --- Display Password Requirements ---
    st.markdown(
        """
        <div style='background-color: #1D2B3F; padding: 10px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #74b9ff;'>
            <p style='color: white; font-weight: bold; margin-bottom: 5px;'>Password Requirements:</p>
            <ul style='list-style-type: none; padding-left: 0; margin: 0;'>
                <li>- Must have 1 Capital character (A-Z)</li>
                <li>- Must have 3 Small characters (a-z)</li>
                <li>- Must have 1 Digit (0-9)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True
    )
    
    with st.form("register_form", clear_on_submit=False):
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        
        submitted = st.form_submit_button("Sign Up Now")

        if submitted:
            if new_user in st.session_state.user_db:
                st.error("Username already exists. Please log in or choose another name.")
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            validation_errors = validate_password(new_pass)
            if validation_errors:
                st.error("❌ Password failed validation. Please meet all requirements listed above.")
                st.markdown('</div>', unsafe_allow_html=True)
                return

            if not new_user or not new_pass:
                st.error("Username and Password cannot be empty.")
            else:
                st.session_state.user_db[new_user] = {
                    'password_hash': hash_password(new_pass),
                    'profile': {},
                    'challenge': {'status': 'Pending', 'stage': None, 'daily_log': {}, 'penalty_amount': 0.0, 'badges': [], 'stage_days_completed': 0, 'streak_days_penalty': 0, 'last_task_message': False }
                }
                st.success("Registration successful! Redirecting to Login...")
                time.sleep(1)
                st.session_state.page = 'login'
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True) # End centered form container
    
    # Button to go back to login
    st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
    if st.button("Go back to Login"):
        st.session_state.page = 'login'
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def login_user():
    st.markdown('<h1 class="main-header" style="text-align: center;">Elite Performance Engine</h1>', unsafe_allow_html=True)
    st.subheader("User Login")
    
    # --- Centering and shortening the form ---
    st.markdown('<div class="centered-form-container">', unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        user = st.text_input("Username", key="log_user")
        password = st.text_input("Password", type="password", key="log_pass")
        
        # The Login button is the only element initially visible for existing users
        submitted = st.form_submit_button("Login")

        if submitted:
            if user not in st.session_state.user_db:
                # User does not exist flow (Exactly as requested)
                st.error("User does not exist. Please sign up for a new account.")
            elif st.session_state.user_db[user]['password_hash'] == hash_password(password):
                # Successful login flow
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success(f"Welcome back, {user}!")
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                # Incorrect password flow
                st.error("Invalid Password.")
    
    st.markdown('</div>', unsafe_allow_html=True) # End centered form container
    
    # Sign Up section below the form
    st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
    st.write("If you don't have an account, please make an account.")
    if st.button("Sign Up"):
        st.session_state.page = 'register'
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- DASHBOARD UI (SIMPLIFIED FOR TESTING) ---

def dashboard_ui():
    st.title(f"Welcome to Your Dashboard, {st.session_state.username}!")
    st.markdown("---")
    
    # Green Logout Button (prominent at the top)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = 'login'
        st.rerun()
    
    st.markdown("---")
    st.subheader("Your Progress Tracker")
    
    st.info("You are successfully logged in! The background color is the dark blue you requested.")
    
    if st.button("Start 105-Day Challenge"):
        st.session_state.page = 'challenge_setup'
        st.rerun()

# --- MAIN APP ROUTER ---

def main_app():
    if st.session_state.logged_in:
        # The background for the dashboard is controlled by the CSS for [data-testid="stVerticalBlock"]
        if st.session_state.page == 'dashboard':
             dashboard_ui()
        elif st.session_state.page == 'challenge_setup':
            st.title("Challenge Setup Page (To be built)") # Placeholder
        elif st.session_state.page == 'daily_tracking':
            st.title("Daily Tracking Page (To be built)") # Placeholder
        
    else:
        if st.session_state.page == 'register':
            register_user()
        else:
            login_user()

if __name__ == "__main__":
    main_app()
