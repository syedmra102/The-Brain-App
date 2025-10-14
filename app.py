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
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# FIX: COMPLETE SESSION STATE SOLUTION
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

# Initialize session state
initialize_session_state()

# FIX: PERSISTENCE CHECK - This runs on every load
if st.session_state.logged_in and st.session_state.user is not None:
    # User is logged in, ensure they're not on auth pages
    if st.session_state.page in ["signin", "signup", "forgot_password"]:
        st.session_state.page = "ml_dashboard"
        st.rerun()
else:
    # User is not logged in, ensure they're on auth pages
    if st.session_state.page not in ["signin", "signup", "forgot_password"]:
        st.session_state.page = "signin"
        st.rerun()

# Firebase setup
try:
    firebase_secrets = st.secrets["firebase"]
    
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": firebase_secrets["type"],
            "project_id": firebase_secrets["project_id"],
            "private_key_id": firebase_secrets["private_key_id"],
            "private_key": firebase_secrets["private_key"].replace("\\n", "\n"),
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
    return re.sub(r'[<>"\']', '', text.strip())

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
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            st.write("Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")
            
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Signing in..."):
                        time.sleep(1)
                        
                        username_clean = sanitize_input(username)
                        password_clean = sanitize_input(password)
                        
                        try:
                            user_doc = db.collection('users').document(username_clean).get()
                            if user_doc.exists:
                                user_info = user_doc.to_dict()
                                if check_password(password_clean, user_info.get("password", "")):
                                    # FIX: COMPLETE LOGIN PROCESS
                                    st.session_state.user = {
                                        "username": username_clean,
                                        "email": user_info.get("email", ""),
                                        "role": user_info.get("role", "student")
                                    }
                                    # Load user profile if exists
                                    profile_doc = db.collection('user_profiles').document(username_clean).get()
                                    if profile_doc.exists:
                                        st.session_state.user_profile = profile_doc.to_dict()
                                    
                                    # Load challenge data
                                    st.session_state.challenge_data = load_challenge_data(username_clean)
                                    
                                    # FIX: SET LOGIN STATE AND PAGE
                                    st.session_state.logged_in = True
                                    st.session_state.page = "ml_dashboard"
                                    
                                    st.success("Login successful!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Invalid username or password")
                            else:
                                st.error("Invalid username or password")
                        except Exception as e:
                            st.error("Login failed. Please try again.")

        col1, col2 = st.columns(2)
        with col1:
            st.button("Forgot Password", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'forgot_password'))
        with col2:
            st.button("Create Account", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'signup'))

def forgot_password_page():
    st.markdown("<h2 style='text-align: center;'>Forgot Password</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("forgot_form"):
            email = st.text_input("Enter your email")
            submit_btn = st.form_submit_button("Send Password")
            
            if submit_btn:
                if not email:
                    st.error("Please enter your email")
                else:
                    email_clean = sanitize_input(email)
                    with st.spinner("Sending password..."):
                        time.sleep(1)
                        
                        username, user_info = get_user_by_email(email_clean)
                        if user_info:
                            original_password = user_info.get("plain_password", "")
                            if original_password:
                                success, message = send_password_email(email_clean, username, original_password)
                                if success:
                                    st.success("Password sent to your email")
                                else:
                                    st.error("Failed to send email")
                            else:
                                st.error("Account not found")
                        else:
                            st.info("If this email exists, password will be sent")

        st.button("Back to Sign In", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'signin'))

def sign_up_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create Account</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("signup_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                if not all([username, email, password, password2]):
                    st.error("Please fill in all fields")
                elif password != password2:
                    st.error("Passwords do not match")
                elif not validate_password(password)[0]:
                    st.error("Password must be 7+ characters with uppercase, lowercase, and number")
                else:
                    with st.spinner("Creating account..."):
                        time.sleep(1)
                        
                        username_clean = sanitize_input(username)
                        email_clean = sanitize_input(email)
                        password_clean = sanitize_input(password)
                        
                        try:
                            if db.collection('users').document(username_clean).get().exists:
                                st.error("Username already exists")
                            else:
                                existing_user, _ = get_user_by_email(email_clean)
                                if existing_user:
                                    st.error("Email already registered")
                                else:
                                    hashed_password = hash_password(password_clean)
                                    user_data = {
                                        "email": email_clean,
                                        "password": hashed_password,
                                        "plain_password": password_clean,
                                        "role": "student"
                                    }
                                    db.collection('users').document(username_clean).set(user_data)
                                    st.success("Account created successfully")
                                    st.session_state.page = "signin"
                                    st.rerun()
                        except Exception as e:
                            st.error("Registration failed. Please try again.")

        st.button("Back to Sign In", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'signin'))

# Protected Pages with Enhanced Authentication
def ml_dashboard_page():
    # FIX: STRICT AUTH CHECK
    if not st.session_state.logged_in or not st.session_state.user:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Discover Your Top Percentile</h3>", unsafe_allow_html=True)
    
    with st.form("performance_form"):
        st.subheader("Your Daily Habits")
        
        hours = st.slider("Daily Study Hours", 0.5, 12.0, 5.0, 0.5)
        distraction_count = st.slider("Daily Distractions", 0, 15, 5)
        
        st.subheader("Lifestyle Habits")
        avoid_sugar = st.selectbox("Avoid Sugar", ["Yes", "No"])
        avoid_junk_food = st.selectbox("Avoid Junk Food", ["Yes", "No"])
        drink_5L_water = st.selectbox("Drink 5L Water Daily", ["Yes", "No"])
        sleep_early = st.selectbox("Sleep Before 11 PM", ["Yes", "No"])
        exercise_daily = st.selectbox("Exercise Daily", ["Yes", "No"])
        wakeup_early = st.selectbox("Wake Up Before 7 AM", ["Yes", "No"])
        
        predict_btn = st.form_submit_button("Predict My Performance")
        
        if predict_btn:
            with st.spinner("Analyzing your performance..."):
                time.sleep(1)
                
                habits = {}
                categorical_mapping = {
                    'avoid_sugar': avoid_sugar,
                    'avoid_junk_food': avoid_junk_food,
                    'drink_5L_water': drink_5L_water,
                    'sleep_early': sleep_early,
                    'exercise_daily': exercise_daily,
                    'wakeup_early': wakeup_early
                }
                
                try:
                    for col, value in categorical_mapping.items():
                        if col in model_data.get('encoders', {}):
                            habits[col] = model_data['encoders'][col].transform([value])[0]
                        else:
                            habits[col] = 1 if value == "Yes" else 0
                    
                    percentile = predict_performance(hours, distraction_count, habits)
                    feature_percentiles = calculate_feature_percentiles(hours, distraction_count, habits)
                    
                    st.session_state.prediction_results = {
                        'percentile': percentile,
                        'feature_percentiles': feature_percentiles
                    }
                    st.rerun()
                except Exception as e:
                    st.error("Error processing your inputs. Please try again.")
    
    if st.session_state.prediction_results is not None:
        results = st.session_state.prediction_results
        percentile = results['percentile']
        feature_percentiles = results['feature_percentiles']
        
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; color: #7C3AED;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
        
        if feature_percentiles:
            fig, ax = plt.subplots(figsize=(12, 6))
            features = list(feature_percentiles.keys())
            percentiles = list(feature_percentiles.values())
            
            bars = ax.bar(features, percentiles, color='#1E3A8A', edgecolor='#1E40AF', linewidth=1.5)
            ax.set_ylabel('Performance Percentile', fontweight='bold')
            ax.set_title('Performance Breakdown Analysis', fontweight='bold', fontsize=14)
            ax.set_ylim(0, 100)
            plt.xticks(rotation=45, ha='right', fontweight='bold')
            
            for bar, percentile_val in zip(bars, percentiles):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'Top {percentile_val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=9)
            
            ax.grid(True, alpha=0.3, color='#1E40AF')
            ax.set_facecolor('#F8FAFC')
            
            st.pyplot(fig)
        
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>105 Days to Top 1% Challenge</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold;'>This is a completely life changing challenge and the only opportunity to become top 1% in the world and also in your field</p>", unsafe_allow_html=True)
    
    show_navigation_buttons()

def stage_completion_popup():
    st.markdown("""
        <style>
        .main-blocker {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .popup-content {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            border: 3px solid #7C3AED;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 500px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-blocker">', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="popup-content">', unsafe_allow_html=True)
        
        st.balloons()
        st.success("CONGRATULATIONS!")
        st.markdown(f"### You've successfully completed the {st.session_state.challenge_data['current_stage']}!")
        
        badge_name = f"{st.session_state.challenge_data['current_stage'].split(' ')[0]} Badge"
        st.markdown(f"### You've earned the {badge_name}!")
        
        st.markdown("---")
        
        next_stages = {
            "Silver (15 Days - Easy)": "Platinum (30 Days - Medium)",
            "Platinum (30 Days - Medium)": "Gold (60 Days - Hard)",
            "Gold (60 Days - Hard)": "All Stages Completed!"
        }
        
        next_stage = next_stages.get(st.session_state.challenge_data['current_stage'])
        
        if next_stage and next_stage != "All Stages Completed!":
            st.markdown(f"### Ready to upgrade to {next_stage}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Upgrade Now", use_container_width=True):
                    challenge_data = st.session_state.challenge_data
                    challenge_data['current_stage'] = next_stage
                    challenge_data['current_day'] = 1
                    challenge_data['completed_days'] = 0
                    
                    save_challenge_data(st.session_state.user['username'], challenge_data)
                    st.session_state.challenge_data = challenge_data
                    st.session_state.show_stage_completion = False
                    st.rerun()
            
            with col2:
                if st.button("Stay Here", use_container_width=True):
                    st.session_state.show_stage_completion = False
                    st.rerun()
        else:
            st.success("YOU ARE A CHAMPION! You've completed all stages!")
            if st.button("Continue Journey", use_container_width=True):
                st.session_state.show_stage_completion = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_persistent_message():
    if st.session_state.submission_message:
        st.markdown("---")
        if st.session_state.submission_type == "success":
            st.success(st.session_state.submission_message)
        elif st.session_state.submission_type == "error":
            st.error(st.session_state.submission_message)
        elif st.session_state.submission_type == "warning":
            st.warning(st.session_state.submission_message)
        
        if st.session_state.submission_type == "success" and "successfully" in st.session_state.submission_message.lower():
            st.markdown("---")
            st.markdown("### Your Final Task For Today:")
            st.success("**Go to Google, find a powerful motivational image and set it as your wallpaper. When you wake up tomorrow and see that wallpaper, you'll remember that you're on a mission and won't get distracted!**")

def daily_challenge_page():
    # FIX: STRICT AUTH CHECK
    if not st.session_state.logged_in or not st.session_state.user:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    show_sidebar_content()
    
    if st.session_state.show_stage_completion:
        stage_completion_popup()
        return
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Daily Challenge Tracker</h1>", unsafe_allow_html=True)
    
    challenge_data = st.session_state.challenge_data
    user_profile = st.session_state.user_profile
    
    if not challenge_data or not user_profile:
        st.error("Please complete your profile setup first")
        st.session_state.page = "setup_profile"
        st.rerun()
        return
    
    current_stage = challenge_data.get('current_stage', 'Silver (15 Days - Easy)')
    current_day = challenge_data.get('current_day', 1)
    streak_days = challenge_data.get('streak_days', 0)
    total_savings = challenge_data.get('total_savings', 0)
    completed_days = challenge_data.get('completed_days', 0)
    
    stage_days = get_stage_days(current_stage)
    days_left = stage_days - completed_days
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Stage", current_stage)
    with col2:
        st.metric("Days Left", days_left)
    with col3:
        st.metric("Streak Days", f"{streak_days} days")
    with col4:
        st.metric("Total Savings", f"${total_savings}")
    
    st.markdown("---")
    
    if completed_days >= stage_days and not st.session_state.show_stage_completion:
        badge_name = f"{current_stage.split(' ')[0]} Badge"
        
        if badge_name not in challenge_data.get('badges', []):
            if 'badges' not in challenge_data:
                challenge_data['badges'] = []
            challenge_data['badges'].append(badge_name)
            save_challenge_data(st.session_state.user['username'], challenge_data)
            st.session_state.challenge_data = challenge_data
        
        st.session_state.show_stage_completion = True
        st.rerun()
    
    st.markdown(f"### Today's Tasks - Day {current_day}")
    st.markdown(f"**Stage:** {current_stage}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = get_stage_tasks(current_stage)
    
    with st.form("daily_tasks_form", clear_on_submit=True):
        completed_tasks = []
        
        st.markdown("#### Complete Your Daily Tasks:")
        for task in tasks:
            if st.checkbox(task, key=f"task_{hash(task)}"):
                completed_tasks.append(task)
        
        st.markdown("---")
        st.markdown("#### Savings & Penalty Section")
        st.info("You can add to your savings anytime, even if you complete all tasks!")
        
        penalty_amount = st.number_input("Amount to add to savings today ($)", 
                                       min_value=0.0, 
                                       step=1.0, 
                                       key="penalty_amount",
                                       help="Add any amount to your challenge savings")
        
        missed_tasks = len(tasks) - len(completed_tasks)
        
        if missed_tasks > 0:
            if missed_tasks == 1:
                st.warning(f"You missed 1 task today. According to rules, you need to pay penalty to count this day toward your streak.")
                penalty_confirmation = st.checkbox("I confirm I've paid the penalty for missed task")
                st.info("Note: If you pay penalty for 1 missed task, the day WILL count toward your streak and progress.")
            else:
                st.error(f"You missed {missed_tasks} tasks. According to rules, this day WON'T count even if you pay penalty.")
                penalty_confirmation = False
        else:
            penalty_confirmation = True
        
        submit_btn = st.form_submit_button("Submit Today's Progress")
        
        if submit_btn:
            process_daily_submission(completed_tasks, missed_tasks, penalty_amount, penalty_confirmation, today, tasks)
    
    show_persistent_message()
    
    if challenge_data.get('total_savings', 0) > 0:
        st.markdown("---")
        st.markdown("### Your Challenge Savings")
        st.info(f"**Total savings: ${challenge_data['total_savings']}**")
        st.markdown("*Remember: When you complete this challenge, use this money for making a project in your field or invest it in your field.*")
    
    show_navigation_buttons()

def process_daily_submission(completed_tasks, missed_tasks, penalty_amount, penalty_confirmation, today, tasks):
    user = st.session_state.user
    challenge_data = st.session_state.challenge_data
    
    if missed_tasks == 0:
        challenge_data['streak_days'] += 1
        challenge_data['completed_days'] += 1
        challenge_data['current_day'] += 1
        challenge_data['total_savings'] += penalty_amount
        
        if 'daily_checkins' not in challenge_data:
            challenge_data['daily_checkins'] = {}
        challenge_data['daily_checkins'][today] = {
            'tasks_completed': completed_tasks,
            'missed_tasks': 0,
            'savings_added': penalty_amount,
            'perfect_day': True
        }
        
        save_challenge_data(user['username'], challenge_data)
        st.session_state.challenge_data = challenge_data
        
        st.session_state.submission_message = f"Perfect day! All tasks completed! Day {challenge_data['current_day']-1} successfully saved. Streak: {challenge_data['streak_days']} days!"
        st.session_state.submission_type = "success"
        
    elif missed_tasks == 1:
        challenge_data['completed_days'] += 1
        challenge_data['current_day'] += 1
        
        if penalty_confirmation and penalty_amount > 0:
            challenge_data['streak_days'] += 1
            challenge_data['total_savings'] += penalty_amount
            
            penalty_record = {
                'date': today,
                'amount': penalty_amount,
                'missed_tasks': 1,
                'reason': f"Missed 1 task but paid penalty"
            }
            if 'penalty_history' not in challenge_data:
                challenge_data['penalty_history'] = []
            challenge_data['penalty_history'].append(penalty_record)
            
            st.session_state.submission_message = f"Day counted with penalty! ${penalty_amount} added to savings. Day {challenge_data['current_day']-1} successfully saved. Streak continues: {challenge_data['streak_days']} days!"
            st.session_state.submission_type = "success"
        else:
            st.session_state.submission_message = f"Day {challenge_data['current_day']-1} counted but no penalty paid for missed task, so streak not incremented. Streak remains: {challenge_data['streak_days']} days."
            st.session_state.submission_type = "warning"
        
        if 'daily_checkins' not in challenge_data:
            challenge_data['daily_checkins'] = {}
        challenge_data['daily_checkins'][today] = {
            'tasks_completed': completed_tasks,
            'missed_tasks': 1,
            'savings_added': penalty_amount,
            'perfect_day': False,
            'penalty_paid': penalty_confirmation and penalty_amount > 0
        }
        
        save_challenge_data(user['username'], challenge_data)
        st.session_state.challenge_data = challenge_data
        
    else:
        st.session_state.submission_message = f"According to rules: You missed {missed_tasks} tasks. This day doesn't count even if you pay penalty. You have to do all tasks tomorrow."
        st.session_state.submission_type = "error"
        
        if 'daily_checkins' not in challenge_data:
            challenge_data['daily_checkins'] = {}
        challenge_data['daily_checkins'][today] = {
            'tasks_completed': completed_tasks,
            'missed_tasks': missed_tasks,
            'savings_added': penalty_amount,
            'perfect_day': False,
            'day_not_counted': True
        }
        save_challenge_data(user['username'], challenge_data)
        st.session_state.challenge_data = challenge_data
    
    st.rerun()

def life_vision_page():
    # FIX: STRICT AUTH CHECK
    if not st.session_state.logged_in or not st.session_state.user:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>After This Challenge How Your Life Is Looking</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Your Life After Completing 105-Day Challenge</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    ### **Grade: ELITE PERFORMER - Top 1% Worldwide**
    
    **1. Perfect Health & Fitness**
    - Complete sugar-free lifestyle with optimal nutrition
    - Daily exercise routine with peak physical fitness
    - 5 liters water daily consumption
    - Perfect sleep cycle with consistent energy levels
    
    **2. Unbreakable Discipline**
    - Wake up at 4-5 AM automatically without alarms
    - Sleep by 9 PM for optimal recovery
    - Complete control over cravings and impulses
    - Military-level daily routine execution
    
    **3. Peak Productivity**
    - 6+ hours of deep focused work daily in your field
    - Zero procrastination or time wasting
    - Maximum output with minimum effort
    - Consistent skill development and mastery
    
    **4. Wealth Mindset**
    - Financial discipline with substantial savings
    - Multiple income streams developed
    - Investment portfolio for your field
    - Money to launch your dream project
    
    **5. Distraction-Free Life**
    - Complete elimination of time-wasting activities
    - No social media addiction
    - Focused attention span of 3+ hours
    - Mental clarity and sharp thinking
    
    **6. Elite Social Circle**
    - Surrounded by top 1% performers
    - Mentors and experts in your network
    - Respect from peers and competitors
    - Leadership position in your field
    """)
    
    st.markdown("---")
    
    st.markdown("<p style='text-align: center; font-weight: bold; font-size: 20px;'>This transformation will make you unrecognizable to your current self</p>", unsafe_allow_html=True)
    
    show_navigation_buttons()

def challenge_rules_page():
    # FIX: STRICT AUTH CHECK
    if not st.session_state.logged_in or not st.session_state.user:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>105 Days Transformation Challenge Rules</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Silver Stage (15 Days - Easy)</h2>", unsafe_allow_html=True)
    st.markdown("""
    1. Do 2 hours of work in your field daily
    2. Dont do any distraction for just 15 days
    3. Fill your daily routine form at this website at night
    """)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Platinum Stage (30 Days - Medium)</h2>", unsafe_allow_html=True)
    st.markdown("""
    1. Do 4 hours of work in your field daily
    2. Dont do any distraction for just 30 days
    3. Do 30 pushups exercise daily
    4. Drink 5 liters of water daily
    5. Avoid junk food
    6. Fill your daily routine form at this website at night
    """)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Gold Stage (60 Days - Hard but Last)</h2>", unsafe_allow_html=True)
    st.markdown("""
    1. Do 6 hours of work in your field daily
    2. Dont do any distraction for just 60 days
    3. Do 30 pushups exercise daily
    4. Do 50 pushups exercise daily
    5. Drink 5 liters of water daily
    6. Avoid junk food
    7. Avoid sugar
    8. Wake up before 7 AM
    9. Sleep before 11 PM
    10. Fill your daily routine form at this website at night
    """)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Penalty Rules</h2>", unsafe_allow_html=True)
    st.markdown("""
    If you miss one rule any day at any stage you have to pay that day whole pocket money or any money that you earn that day and put on savings.
    When you complete this challenge you use this money for making project on your field or invest that money in your field.
    But if you miss 2 or more habits at any stage we dont count that day even also you paying money and you have to do all of the things tomorrow.
    """)
    
    st.markdown("---")
    
    st.markdown("<p style='text-align: center; font-weight: bold; font-size: 20px;'>This is your only opportunity to transform your life and become top 1%</p>", unsafe_allow_html=True)
    
    show_navigation_buttons()

def setup_profile_page():
    # FIX: STRICT AUTH CHECK
    if not st.session_state.logged_in or not st.session_state.user:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    show_sidebar_content()
    
    is_editing = bool(st.session_state.user_profile)
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Setup Your Challenge Profile</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.form("profile_form"):
        st.subheader("Your Field & Goals")
        
        field = st.selectbox("Select Your Field", [
            "Programming & Technology",
            "Engineering",
            "Medical & Healthcare",
            "Business & Entrepreneurship",
            "Science & Research",
            "Arts & Creative",
            "Sports & Fitness",
            "Education & Teaching",
            "Finance & Investment",
            "Other"
        ])
        
        goal = st.text_input("What do you want to become? (e.g., Neurosurgeon, AI Engineer, Entrepreneur)")
        
        st.subheader("Your Current Distractions")
        distractions = st.multiselect("Select distractions you currently face", [
            "Social Media Scrolling",
            "YouTube/Netflix Binging",
            "Video Games",
            "Masturbation/Porn",
            "Procrastination",
            "Phone Addiction",
            "Unproductive Socializing",
            "Overthinking",
            "Substance Use",
            "Other"
        ])
        
        st.subheader("Challenge Stage Selection")
        stage = st.selectbox("Choose your starting stage", [
            "Silver (15 Days - Easy)",
            "Platinum (30 Days - Medium)",
            "Gold (60 Days - Hard)"
        ])
        
        save_btn = st.form_submit_button("Update Profile" if is_editing else "Save Profile & Start Challenge")
        
        if save_btn:
            if not field or not goal or not stage:
                st.error("Please fill all fields")
            else:
                with st.spinner("Saving your profile..."):
                    profile_data = {
                        'field': field,
                        'goal': goal,
                        'distractions': distractions,
                        'stage': stage,
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'updated_at': firestore.SERVER_TIMESTAMP
                    }
                    
                    st.session_state.user_profile = profile_data
                    
                    if not is_editing:
                        challenge_data = {
                            'current_stage': stage,
                            'start_date': datetime.now(),
                            'current_day': 1,
                            'streak_days': 0,
                            'total_savings': 0,
                            'completed_days': 0,
                            'penalty_history': [],
                            'daily_checkins': {},
                            'badges': []
                        }
                        st.session_state.challenge_data = challenge_data
                    
                    try:
                        db.collection('user_profiles').document(st.session_state.user['username']).set(profile_data)
                        if not is_editing:
                            save_challenge_data(st.session_state.user['username'], challenge_data)
                        st.success("Profile saved successfully!")
                        
                        if not is_editing:
                            st.info("Your profile is now visible in the sidebar. Your challenge begins now!")
                            time.sleep(2)
                            st.session_state.page = "daily_challenge"
                            st.rerun()
                    except Exception as e:
                        st.error("Failed to save profile. Please try again.")
    
    show_navigation_buttons()

# FIX: MAIN APP ROUTING - SIMPLE AND EFFECTIVE
if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
elif st.session_state.page == "forgot_password":
    forgot_password_page()
elif st.session_state.page == "ml_dashboard":
    ml_dashboard_page()
elif st.session_state.page == "life_vision":
    life_vision_page()
elif st.session_state.page == "challenge_rules":
    challenge_rules_page()
elif st.session_state.page == "setup_profile":
    setup_profile_page()
elif st.session_state.page == "daily_challenge":
    daily_challenge_page()
else:
    # Fallback to signin
    st.session_state.page = "signin"
    st.rerun()
