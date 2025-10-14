Here's the complete Streamlit code with the session persistence issue fixed. You can just copy and paste this code into your Streamlit application:

```python
import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from datetime import datetime

# Page config
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables with proper defaults"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user = None
        st.session_state.page = "signin"
        st.session_state.logged_in = False
        st.session_state.prediction_results = None
        st.session_state.user_profile = {}
        st.session_state.challenge_data = {}
        st.session_state.show_stage_completion = False
        st.session_state.form_submitted = False
        st.session_state.submission_message = None
        st.session_state.submission_type = None
        st.session_state.session_persisted = False

# Initialize session state
initialize_session_state()

# Firebase setup
try:
    firebase_secrets = st.secrets["firebase"]

    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": firebase_secrets["type"],
            "project_id": firebase_secrets["project_id"],
            "private_key_id": firebase_secrets["private_key_id"],
            "private_key": firebase_secrets["private_key"].replace("\\\\n", "\\n"),
            "client_email": firebase_secrets["client_email"],
            "client_id": firebase_secrets["client_id"],
            "auth_uri": firebase_secrets["auth_uri"],
            "token_uri": firebase_secrets["token_uri"],
            "auth_provider_x509_cert_url": firebase_secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": firebase_secrets["client_x509_cert_url"]
        })
        firebase_admin.initialize_app(cred)

    db = firestore.client()

except Exception as e:
    st.error("System temporarily unavailable")
    st.stop()

# Ensure session_persisted exists
if 'session_persisted' not in st.session_state:
    st.session_state.session_persisted = False

# Get query params
query_params = st.experimental_get_query_params()

# Improved persistence check to prevent logout on refresh
if not st.session_state.session_persisted:
    try:
        # Check if user is already logged in or can be restored
        if st.session_state.logged_in and st.session_state.user and 'username' in st.session_state.user:
            # Ensure user is not on auth pages
            if st.session_state.page in ["signin", "signup", "forgot_password"]:
                st.session_state.page = "ml_dashboard"
            st.session_state.session_persisted = True
            st.rerun()
        else:
            # Attempt to restore session from query params or user data
            username = None
            if 'username' in query_params:
                username = query_params['username'][0]
            elif st.session_state.user and 'username' in st.session_state.user:
                username = st.session_state.user['username']

            if username:
                user_doc = db.collection('users').document(username).get()
                if user_doc.exists:
                    user_info = user_doc.to_dict()
                    st.session_state.user = {
                        "username": username,
                        "email": user_info.get("email", ""),
                        "role": user_info.get("role", "student")
                    }
                    # Restore user profile
                    profile_doc = db.collection('user_profiles').document(username).get()
                    if profile_doc.exists:
                        st.session_state.user_profile = profile_doc.to_dict()
                    else:
                        st.session_state.user_profile = {}
                    # Restore challenge data
                    st.session_state.challenge_data = load_challenge_data(username)
                    st.session_state.logged_in = True
                    st.session_state.page = "ml_dashboard"
                    st.session_state.session_persisted = True
                    # Ensure query params are set
                    st.experimental_set_query_params(username=username)
                    st.rerun()
                else:
                    # User not found in Firebase, reset to signin
                    st.session_state.user = None
                    st.session_state.logged_in = False
                    st.session_state.user_profile = {}
                    st.session_state.challenge_data = {}
                    st.session_state.page = "signin"
                    st.experimental_set_query_params()
                    st.session_state.session_persisted = True
                    st.rerun()
            else:
                # No user data, ensure on signin page
                st.session_state.user = None
                st.session_state.logged_in = False
                st.session_state.user_profile = {}
                st.session_state.challenge_data = {}
                st.session_state.page = "signin"
                st.experimental_set_query_params()
                st.session_state.session_persisted = True
                st.rerun()
    except Exception as e:
        # Handle any errors by resetting to signin
        st.session_state.user = None
        st.session_state.logged_in = False
        st.session_state.user_profile = {}
        st.session_state.challenge_data = {}
        st.session_state.page = "signin"
        st.experimental_set_query_params()
        st.session_state.session_persisted = True
        st.rerun()
else:
    # Session already persisted, verify user state
    if st.session_state.logged_in and st.session_state.user and 'username' in st.session_state.user:
        if st.session_state.page in ["signin", "signup", "forgot_password"]:
            st.session_state.page = "ml_dashboard"
            st.rerun()
    else:
        if st.session_state.page not in ["signin", "signup", "forgot_password"]:
            st.session_state.page = "signin"
            st.experimental_set_query_params()
            st.rerun()

# Load ML Model from model.pkl
@st.cache_resource
def load_ml_model():
    try:
        with open('model.pkl', 'rb') as f:
            model_data = pickle.load(f)
        return model_data
    except FileNotFoundError:
        st.error("ML model not found. Please upload model.pkl to your GitHub repository.")
        return None

model_data = load_ml_model()
if model_data is None:
    st.stop()

# Email setup
EMAIL_ADDRESS = "zada44919@gmail.com"
EMAIL_PASSWORD = "mrgklwomlcwwfxrd"

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def send_password_email(to_email, username, password):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Your Brain App Password'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg.set_content(f"""
        Hello {username}
        Your Brain App Account Details:
        Username: {username}
        Password: {password}
        Please keep this information secure.
        Best regards,
        The Brain App Team
        """)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True, "Password sent to your email"
    except Exception as e:
        return False, "Email service temporarily unavailable"

def validate_password(password):
    if len(password) < 7:
        return False, "Password must be at least 7 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def get_user_by_email(email):
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).get()
        if query:
            for doc in query:
                return doc.id, doc.to_dict()
        return None, None
    except:
        return None, None

def sanitize_input(text):
    return re.sub(r'[<>\"\\\'\\]', '', text.strip())

# ML Prediction Function
def predict_performance(hours, distraction_count, habits):
    try:
        if not all(key in model_data for key in ['numeric_columns', 'scaler', 'feature_columns', 'model', 'categorical_columns', 'encoders']):
            st.error("ML model configuration incomplete")
            return 50.0

        input_data = pd.DataFrame([{
            'hours': hours,
            'distraction_count': distraction_count,
            **habits
        }])

        for col in model_data['numeric_columns']:
            if col not in input_data.columns:
                input_data[col] = 0

        input_data[model_data['numeric_columns']] = model_data['scaler'].transform(input_data[model_data['numeric_columns']])
        input_data = input_data[model_data['feature_columns']]

        prediction = model_data['model'].predict(input_data)[0]
        prediction = max(1, min(100, prediction))

        return prediction

    except Exception as e:
        st.error("Prediction error occurred")
        return 50.0

def calculate_feature_percentiles(hours, distractions, habit_inputs):
    try:
        feature_percentiles = {}
        df = model_data['df']

        hours_percentile = (df['hours'] <= hours).mean() * 100
        feature_percentiles['Study Hours'] = max(1, 100 - hours_percentile)

        dist_percentile = (df['distraction_count'] >= distractions).mean() * 100
        feature_percentiles['Distraction Control'] = max(1, 100 - dist_percentile)

        habit_mapping = {
            'avoid_sugar': 'Sugar Avoidance',
            'avoid_junk_food': 'Junk Food Avoidance',
            'drink_5L_water': 'Water Intake',
            'sleep_early': 'Sleep Schedule',
            'exercise_daily': 'Exercise Routine',
            'wakeup_early': 'Wake-up Time'
        }

        for col, friendly_name in habit_mapping.items():
            habit_value = habit_inputs.get(col, 0)
            if habit_value == 1:
                habit_percentile = (df[col] == 1).mean() * 100
                feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
            else:
                habit_percentile = (df[col] == 0).mean() * 100
                feature_percentiles[friendly_name] = max(1, habit_percentile)

        return feature_percentiles
    except Exception as e:
        st.error("Error calculating feature percentiles")
        return {}

# Challenge Functions
def get_stage_days(stage):
    stage_days = {
        "Silver (15 Days - Easy)": 15,
        "Platinum (30 Days - Medium)": 30,
        "Gold (60 Days - Hard)": 60
    }
    return stage_days.get(stage, 15)

def get_stage_tasks(stage):
    tasks = {
        "Silver (15 Days - Easy)": [
            "Do 2 hours of work in your field",
            "No distractions today",
            "Fill daily routine form"
        ],
        "Platinum (30 Days - Medium)": [
            "Do 4 hours of work in your field",
            "No distractions today",
            "Do 30 pushups exercise",
            "Drink 5 liters of water",
            "Avoid junk food",
            "Fill daily routine form"
        ],
        "Gold (60 Days - Hard)": [
            "Do 6 hours of work in your field",
            "No distractions today",
            "Do 30 pushups exercise",
            "Do 50 pushups exercise",
            "Drink 5 liters of water",
            "Avoid junk food",
            "Avoid sugar",
            "Wake up before 7 AM",
            "Sleep before 11 PM",
            "Fill daily routine form"
        ]
    }
    return tasks.get(stage, [])

def load_challenge_data(username):
    try:
        doc_ref = db.collection('challenge_progress').document(username)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            initial_data = {
                'current_stage': '',
                'start_date': datetime.now(),
                'current_day': 1,
                'streak_days': 0,
                'total_savings': 0,
                'completed_days': 0,
                'penalty_history': [],
                'daily_checkins': {},
                'badges': []
            }
            return initial_data
    except Exception as e:
        st.error("Error loading challenge data")
        return {}

def save_challenge_data(username, data):
    try:
        db.collection('challenge_progress').document(username).set(data)
        return True
    except Exception as e:
        st.error("Error saving challenge data")
        return False

# Universal Sidebar Navigation and Profile Display
def show_sidebar_content():
    """Show navigation and full profile in sidebar for all pages when user is logged in"""
    if st.session_state.user and st.session_state.logged_in:
        with st.sidebar:
            st.markdown("### Navigation")

            if st.button("Performance Predictor", use_container_width=True):
                st.session_state.page = "ml_dashboard"
                st.rerun()

            if st.button("Life Vision", use_container_width=True):
                st.session_state.page = "life_vision"
                st.rerun()

            if st.button("Challenge Rules", use_container_width=True):
                st.session_state.page = "challenge_rules"
                st.rerun()

            if st.session_state.user_profile:
                if st.button("Daily Challenge", use_container_width=True):
                    st.session_state.page = "daily_challenge"
                    st.rerun()

            if st.session_state.user_profile:
                if st.button("Edit Profile", use_container_width=True):
                    st.session_state.page = "setup_profile"
                    st.rerun()

            if not st.session_state.user_profile:
                if st.button("Setup Profile", use_container_width=True):
                    st.session_state.page = "setup_profile"
                    st.rerun()

            st.markdown("---")

            st.markdown("### My Profile")
            st.write(f"**Username:** {st.session_state.user['username']}")
            st.write(f"**Email:** {st.session_state.user['email']}")

            if st.session_state.user_profile:
                st.markdown("---")
                st.markdown("### My Goals")
                st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
                st.write(f"**I want to become:** {st.session_state.user_profile.get('goal', 'Not set')}")
                st.write(f"**Current Stage:** {st.session_state.user_profile.get('stage', 'Not set')}")

                distractions = st.session_state.user_profile.get('distractions', [])
                if distractions:
                    st.write(f"**My Distractions:** {', '.join(distractions)}")
                else:
                    st.write("**My Distractions:** None selected")

                if st.session_state.challenge_data:
                    st.markdown("---")
                    st.markdown("### My Progress")
                    st.write(f"**Current Day:** {st.session_state.challenge_data.get('current_day', 1)}")
                    st.write(f"**Streak Days:** {st.session_state.challenge_data.get('streak_days', 0)}")
                    st.write(f"**Total Savings:** ${st.session_state.challenge_data.get('total_savings', 0)}")
                    st.write(f"**Completed Days:** {st.session_state.challenge_data.get('completed_days', 0)}")

                if st.session_state.challenge_data.get('badges'):
                    st.markdown("---")
                    st.markdown("### My Badges")
                    for badge in st.session_state.challenge_data['badges']:
                        st.success(f"{badge}")

            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                initialize_session_state()  # Reinitialize session state
                st.experimental_set_query_params()
                st.session_state.page = "signin"
                st.rerun()

def show_navigation_buttons():
    """Show navigation buttons at the bottom of every page"""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    current_page = st.session_state.page

    if current_page == "ml_dashboard":
        with col2:
            if st.button("See Life Vision →", use_container_width=True):
                st.session_state.page = "life_vision"
                st.rerun()

    elif current_page == "life_vision":
        with col2:
            col_left, col_right = st.columns(2)
            with col_left:
                if st.button("← Back to Predictor", use_container_width=True):
                    st.session_state.page = "ml_dashboard"
                    st.rerun()
            with col_right:
                if st.button("Challenge Rules →", use_container_width=True):
                    st.session_state.page = "challenge_rules"
                    st.rerun()

    elif current_page == "challenge_rules":
        with col2:
            col_left, col_right = st.columns(2)
            with col_left:
                if st.button("← Back to Life Vision", use_container_width=True):
                    st.session_state.page = "life_vision"
                    st.rerun()
            with col_right:
                if st.session_state.user_profile:
                    if st.button("Daily Challenge →", use_container_width=True):
                        st.session_state.page = "daily_challenge"
                        st.rerun()
                else:
                    if st.button("Setup Profile →", use_container_width=True):
                        st.session_state.page = "setup_profile"
                        st.rerun()

    elif current_page == "setup_profile":
        with col2:
            col_left, col_right = st.columns(2)
            with col_left:
                if st.button("← Back to Rules", use_container_width=True):
                    st.session_state.page = "challenge_rules"
                    st.rerun()
            with col_right:
                if st.session_state.user_profile:
                    if st.button("Daily Challenge →", use_container_width=True):
                        st.session_state.page = "daily_challenge"
                        st.rerun()

    elif current_page == "daily_challenge":
        with col2:
            if st.button("← Back to Predictor", use_container_width=True):
                st.session_state.page = "ml_dashboard"
                st.rerun()

# Authentication Pages
def sign_in_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("login_form"):
           
