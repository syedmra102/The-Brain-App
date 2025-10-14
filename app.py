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

# Initialize session state for persistence
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = "signin"
if 'prediction_results' not in st.session_state:
    st.session_state.prediction_results = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'challenge_data' not in st.session_state:
    st.session_state.challenge_data = {}
if 'show_stage_completion' not in st.session_state:
    st.session_state.show_stage_completion = False
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'submission_message' not in st.session_state:
    st.session_state.submission_message = None
if 'submission_type' not in st.session_state:  # 'success', 'error', 'warning'
    st.session_state.submission_type = None

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
        # Check if model_data has necessary components
        if not all(key in model_data for key in ['numeric_columns', 'scaler', 'feature_columns', 'model', 'categorical_columns', 'encoders']):
            st.error("ML model configuration incomplete")
            return 50.0
            
        input_data = pd.DataFrame([{
            'hours': hours,
            'distraction_count': distraction_count,
            **habits
        }])
        
        # Ensure all numeric columns exist
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
            # Initialize challenge data
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

# Pages - LOGIN/REGISTER/FORGOT PASSWORD CENTERED
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
                                    
                                    st.success("Login successful")
                                    st.session_state.page = "ml_dashboard"
                                    st.rerun()
                                else:
                                    st.error("Invalid username or password")
                            else:
                                st.error("Invalid username or password")
                        except Exception as e:
                            st.error("Login failed. Please try again.")

        # Buttons below the form
        col1, col2 = st.columns(2)
        with col1:
            st.button("Forgot Password", use_container_width=True, on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        with col2:
            st.button("Create Account", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signup"}))

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

        # Button below the form
        st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

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

        # Button below the form
        st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

# ML PAGE
def ml_dashboard_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    user = st.session_state.user
    
    # SIDEBAR WITH USER PROFILE - Show all details
    with st.sidebar:
        st.markdown("### User Profile")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        
        # Show complete user profile if exists
        if st.session_state.user_profile:
            st.markdown("---")
            st.markdown("### Challenge Profile")
            st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
            st.write(f"**Goal:** {st.session_state.user_profile.get('goal', 'Not set')}")
            st.write(f"**Stage:** {st.session_state.user_profile.get('stage', 'Not set')}")
            distractions = st.session_state.user_profile.get('distractions', [])
            if distractions:
                st.write(f"**Distractions:** {', '.join(distractions)}")
            else:
                st.write("**Distractions:** None selected")
            
            # Show challenge progress
            if st.session_state.challenge_data:
                st.markdown("---")
                st.markdown("### Challenge Progress")
                st.write(f"**Current Day:** {st.session_state.challenge_data.get('current_day', 1)}")
                st.write(f"**Streak Days:** {st.session_state.challenge_data.get('streak_days', 0)}")
                st.write(f"**Total Savings:** ${st.session_state.challenge_data.get('total_savings', 0)}")
                st.write(f"**Completed Days:** {st.session_state.challenge_data.get('completed_days', 0)}")
            
            # Show badges if any
            if st.session_state.challenge_data.get('badges'):
                st.markdown("---")
                st.markdown("### Your Badges")
                for badge in st.session_state.challenge_data['badges']:
                    st.success(f"🏅 {badge}")
    
    # MAIN CONTENT - NO COLUMNS, OPENLY DISPLAYED
    st.markdown("<h1 style='text-align: center;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Discover Your Top Percentile</h3>", unsafe_allow_html=True)
    
    # FORM FOR PREDICTION INPUTS
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
                
                # Create habits dictionary safely
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
                            # Default encoding if encoder not found
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
    
    # SHOW RESULTS OUTSIDE FORM
    if st.session_state.prediction_results is not None:
        results = st.session_state.prediction_results
        percentile = results['percentile']
        feature_percentiles = results['feature_percentiles']
        
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; color: #7C3AED;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
        
        # DARK BLUE CHART
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
        
        # 105 Days Challenge
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>105 Days to Top 1% Challenge</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold;'>This is a completely life changing challenge and the only opportunity to become top 1% in the world and also in your field</p>", unsafe_allow_html=True)
    
    # Buttons below the content
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("See How My Life Will Look After This Challenge", use_container_width=True):
            st.session_state.page = "life_vision"
            st.rerun()

# STAGE COMPLETION POPUP
def stage_completion_popup():
    """Show stage completion popup that freezes the entire website"""
    # Create an overlay that blocks interaction with the rest of the app
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
    
    # Popup content
    st.markdown('<div class="main-blocker">', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="popup-content">', unsafe_allow_html=True)
        
        st.balloons()
        st.success("🎉 CONGRATULATIONS! 🎉")
        st.markdown(f"### You've successfully completed the {st.session_state.challenge_data['current_stage']}!")
        
        badge_name = f"{st.session_state.challenge_data['current_stage'].split(' ')[0]} Badge"
        st.markdown(f"### You've earned the {badge_name}! 🏅")
        
        st.markdown("---")
        
        next_stages = {
            "Silver (15 Days - Easy)": "Platinum (30 Days - Medium)",
            "Platinum (30 Days - Medium)": "Gold (60 Days - Hard)",
            "Gold (60 Days - Hard)": "All Stages Completed! 🏆"
        }
        
        next_stage = next_stages.get(st.session_state.challenge_data['current_stage'])
        
        if next_stage and next_stage != "All Stages Completed! 🏆":
            st.markdown(f"### Ready to upgrade to {next_stage}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Upgrade Now", use_container_width=True):
                    # Upgrade to next stage
                    challenge_data = st.session_state.challenge_data
                    challenge_data['current_stage'] = next_stage
                    challenge_data['current_day'] = 1
                    challenge_data['completed_days'] = 0
                    # Keep streak days and savings
                    
                    save_challenge_data(st.session_state.user['username'], challenge_data)
                    st.session_state.challenge_data = challenge_data
                    st.session_state.show_stage_completion = False
                    st.rerun()
            
            with col2:
                if st.button("🔄 Stay Here", use_container_width=True):
                    st.session_state.show_stage_completion = False
                    st.rerun()
        else:
            st.success("🏆 YOU ARE A CHAMPION! You've completed all stages! 🏆")
            if st.button("🎯 Continue Journey", use_container_width=True):
                st.session_state.show_stage_completion = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# DAILY CHALLENGE PAGE
def daily_challenge_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    user = st.session_state.user
    
    # Show stage completion popup if needed (this freezes everything else)
    if st.session_state.show_stage_completion:
        stage_completion_popup()
        return
    
    # SIDEBAR WITH FULL PROFILE
    with st.sidebar:
        st.markdown("### User Profile")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        
        if st.session_state.user_profile:
            st.markdown("---")
            st.markdown("### Challenge Profile")
            st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
            st.write(f"**Goal:** {st.session_state.user_profile.get('goal', 'Not set')}")
            st.write(f"**Stage:** {st.session_state.user_profile.get('stage', 'Not set')}")
            
        if st.session_state.challenge_data:
            st.markdown("---")
            st.markdown("### Challenge Progress")
            st.write(f"**Current Day:** {st.session_state.challenge_data.get('current_day', 1)}")
            st.write(f"**Streak Days:** {st.session_state.challenge_data.get('streak_days', 0)}")
            st.write(f"**Total Savings:** ${st.session_state.challenge_data.get('total_savings', 0)}")
            st.write(f"**Completed Days:** {st.session_state.challenge_data.get('completed_days', 0)}")
            
            # Show badges if any
            if st.session_state.challenge_data.get('badges'):
                st.markdown("---")
                st.markdown("### Your Badges")
                for badge in st.session_state.challenge_data['badges']:
                    st.success(f"🏅 {badge}")
    
    # MAIN CONTENT - NO COLUMNS, FREELY DISPLAYED
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Daily Challenge Tracker</h1>", unsafe_allow_html=True)
    
    # Challenge Progress Overview
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
    
    # Display progress metrics
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
    
    # Check if stage is completed (but don't show popup yet)
    if completed_days >= stage_days and not st.session_state.show_stage_completion:
        badge_name = f"{current_stage.split(' ')[0]} Badge"
        
        if badge_name not in challenge_data.get('badges', []):
            # Add badge if not already earned
            if 'badges' not in challenge_data:
                challenge_data['badges'] = []
            challenge_data['badges'].append(badge_name)
            save_challenge_data(user['username'], challenge_data)
            st.session_state.challenge_data = challenge_data
        
        # Set flag to show popup on next render
        st.session_state.show_stage_completion = True
        st.rerun()
    
    # Daily Tasks Checkbox Form
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
        st.info("💡 You can add to your savings anytime, even if you complete all tasks!")
        
        # Always show penalty/savings input
        penalty_amount = st.number_input("Amount to add to savings today ($)", 
                                       min_value=0.0, 
                                       step=1.0, 
                                       key="penalty_amount",
                                       help="Add any amount to your challenge savings")
        
        missed_tasks = len(tasks) - len(completed_tasks)
        
        if missed_tasks > 0:
            if missed_tasks == 1:
                st.warning(f"⚠️ You missed 1 task today. According to rules, you need to pay your whole day money to count this day.")
                penalty_confirmation = st.checkbox("I confirm I've paid the penalty for missed task")
            else:
                st.error(f"❌ You missed {missed_tasks} tasks. According to rules, this day won't count even if you pay penalty.")
                penalty_confirmation = False
        else:
            penalty_confirmation = True  # No missed tasks, so automatically confirmed
        
        submit_btn = st.form_submit_button("✅ Submit Today's Progress")
        
        if submit_btn:
            # Process the form submission
            process_daily_submission(completed_tasks, missed_tasks, penalty_amount, penalty_confirmation, today, tasks)
    
    # Show submission message at the BOTTOM of the page
    if st.session_state.submission_message:
        st.markdown("---")
        if st.session_state.submission_type == "success":
            st.success(st.session_state.submission_message)
        elif st.session_state.submission_type == "error":
            st.error(st.session_state.submission_message)
        elif st.session_state.submission_type == "warning":
            st.warning(st.session_state.submission_message)
        
        # Show the final motivational task for successful days
        if st.session_state.submission_type == "success" and "successfully" in st.session_state.submission_message.lower():
            st.markdown("---")
            st.markdown("### 🎯 Your Final Task For Today:")
            st.success("**🌅 Go to Google, find a powerful motivational image and set it as your wallpaper. When you wake up tomorrow and see that wallpaper, you'll remember that you're on a mission and won't get distracted!**")
            
        # Clear the message after showing
        st.session_state.submission_message = None
        st.session_state.submission_type = None
    
    # Show savings progress
    if challenge_data.get('total_savings', 0) > 0:
        st.markdown("---")
        st.markdown("### 💰 Your Challenge Savings")
        st.info(f"**Total savings: ${challenge_data['total_savings']}**")
        st.markdown("💡 *Remember: When you complete this challenge, use this money for making a project in your field or invest it in your field.*")
    
    # Back button at bottom
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Predictor", use_container_width=True):
            st.session_state.page = "ml_dashboard"
            st.rerun()

def process_daily_submission(completed_tasks, missed_tasks, penalty_amount, penalty_confirmation, today, tasks):
    """Process the daily form submission"""
    user = st.session_state.user
    challenge_data = st.session_state.challenge_data
    
    if missed_tasks == 0:
        # Perfect day - all tasks completed
        challenge_data['streak_days'] += 1
        challenge_data['completed_days'] += 1
        challenge_data['current_day'] += 1
        challenge_data['total_savings'] += penalty_amount  # Add any voluntary savings
        
        # Save daily checkin
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
        
        st.session_state.submission_message = f"🎉 Perfect day! All tasks completed! Day {challenge_data['current_day']-1} successfully saved. Streak: {challenge_data['streak_days']} days!"
        st.session_state.submission_type = "success"
        
    elif missed_tasks == 1 and penalty_confirmation and penalty_amount > 0:
        # Missed 1 task but paid penalty
        challenge_data['streak_days'] += 1
        challenge_data['completed_days'] += 1
        challenge_data['current_day'] += 1
        challenge_data['total_savings'] += penalty_amount
        
        # Add to penalty history
        penalty_record = {
            'date': today,
            'amount': penalty_amount,
            'missed_tasks': 1,
            'reason': f"Missed 1 task"
        }
        if 'penalty_history' not in challenge_data:
            challenge_data['penalty_history'] = []
        challenge_data['penalty_history'].append(penalty_record)
        
        # Save daily checkin
        if 'daily_checkins' not in challenge_data:
            challenge_data['daily_checkins'] = {}
        challenge_data['daily_checkins'][today] = {
            'tasks_completed': completed_tasks,
            'missed_tasks': 1,
            'savings_added': penalty_amount,
            'perfect_day': False
        }
        
        save_challenge_data(user['username'], challenge_data)
        st.session_state.challenge_data = challenge_data
        
        st.session_state.submission_message = f"✅ Day counted! ${penalty_amount} added to savings. Day {challenge_data['current_day']-1} successfully saved. Streak continues: {challenge_data['streak_days']} days!"
        st.session_state.submission_type = "success"
        
    elif missed_tasks == 1 and (not penalty_confirmation or penalty_amount == 0):
        st.session_state.submission_message = "❌ According to rules: You missed 1 task but didn't pay penalty. Please pay your whole day money to count this day."
        st.session_state.submission_type = "error"
        
    else:  # missed_tasks >= 2
        st.session_state.submission_message = f"❌ According to rules: You missed {missed_tasks} tasks. This day doesn't count even if you pay penalty. You have to do all tasks tomorrow."
        st.session_state.submission_type = "error"
        
        # Still save the checkin but don't count the day
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

# Other page functions remain the same (life_vision_page, challenge_rules_page, setup_profile_page)
def life_vision_page():
    # ... (keep existing life_vision_page code)
    pass

def challenge_rules_page():
    # ... (keep existing challenge_rules_page code)
    pass

def setup_profile_page():
    # ... (keep existing setup_profile_page code)
    pass

# Session persistence - Check if user should stay logged in
if st.session_state.user is not None and st.session_state.page == "signin":
    st.session_state.page = "ml_dashboard"

# Main app routing
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
