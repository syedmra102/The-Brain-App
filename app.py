import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="The Brain App", 
    page_icon="🧠", 
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #7C3AED;
        background: #7C3AED;
        color: white;
        font-weight: 500;
        padding: 10px 20px;
    }
    
    .stButton>button:hover {
        background: #6D28D9;
        border-color: #6D28D9;
    }
    
    .popup-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    
    .popup-content {
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        max-width: 500px;
        width: 90%;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Firebase setup
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": "brain-app-12345",
            "private_key_id": "your_private_key_id_here",
            "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-xyz@brain-app-12345.iam.gserviceaccount.com",
            "client_id": "your_client_id_here",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xyz%40brain-app-12345.iam.gserviceaccount.com"
        })
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
except Exception as e:
    st.error("System temporarily unavailable")
    st.stop()

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
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

def set_persistent_login(username):
    st.query_params["username"] = username
    st.query_params["logged_in"] = "true"

def clear_persistent_login():
    st.query_params.clear()

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

# Load ML Model
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

# Initialize session state
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
if 'show_error' not in st.session_state:
    st.session_state.show_error = None
if 'show_success' not in st.session_state:
    st.session_state.show_success = None
if 'show_motivational_task' not in st.session_state:
    st.session_state.show_motivational_task = False

# Check for persistent login
if st.session_state.user is None:
    query_params = st.query_params
    if 'username' in query_params and 'logged_in' in query_params and query_params['logged_in'] == "true":
        username = query_params['username']
        try:
            user_doc = db.collection('users').document(username).get()
            if user_doc.exists:
                user_info = user_doc.to_dict()
                st.session_state.user = {
                    "username": username,
                    "email": user_info.get("email", ""),
                    "role": user_info.get("role", "student")
                }
                profile_doc = db.collection('user_profiles').document(username).get()
                if profile_doc.exists:
                    st.session_state.user_profile = profile_doc.to_dict()
                st.session_state.challenge_data = load_challenge_data(username)
                st.session_state.page = "ml_dashboard"
                set_persistent_login(username)
            else:
                st.session_state.page = "signin"
                clear_persistent_login()
        except Exception as e:
            st.session_state.page = "signin"
            clear_persistent_login()
else:
    set_persistent_login(st.session_state.user['username'])

# ML Prediction Function
def predict_performance(hours, distraction_count, habits):
    try:
        input_data = pd.DataFrame([{
            'hours': hours,
            'distraction_count': distraction_count,
            **habits
        }])
        
        input_data[model_data['numeric_columns']] = model_data['scaler'].transform(input_data[model_data['numeric_columns']])
        input_data = input_data[model_data['feature_columns']]
        
        prediction = model_data['model'].predict(input_data)[0]
        prediction = max(1, min(100, prediction))
        
        return prediction
        
    except Exception as e:
        st.error("Prediction error occurred")
        return 50.0

def calculate_feature_percentiles(hours, distractions, habit_inputs):
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
        habit_value = habit_inputs[col]
        if habit_value == 1:
            habit_percentile = (df[col] == 1).mean() * 100
            feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
        else:
            habit_percentile = (df[col] == 0).mean() * 100
            feature_percentiles[friendly_name] = max(1, habit_percentile)
    
    return feature_percentiles

# Clean Sidebar Navigation
def show_sidebar_content():
    if st.session_state.user:
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
            
            if st.button("Setup Profile", use_container_width=True):
                st.session_state.page = "setup_profile"
                st.rerun()
            
            if st.session_state.user_profile:
                if st.button("Daily Challenge", use_container_width=True):
                    st.session_state.page = "daily_challenge"
                    st.rerun()
            
            st.markdown("---")
            
            st.markdown("### My Profile")
            st.write(f"**Username:** {st.session_state.user['username']}")
            
            if st.session_state.user_profile:
                st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
                st.write(f"**Goal:** {st.session_state.user_profile.get('goal', 'Not set')}")
                st.write(f"**Stage:** {st.session_state.user_profile.get('stage', 'Not set')}")
                
                if st.session_state.challenge_data:
                    st.write(f"**Current Day:** {st.session_state.challenge_data.get('current_day', 1)}")
                    st.write(f"**Streak Days:** {st.session_state.challenge_data.get('streak_days', 0)}")
                    st.write(f"**Total Savings:** ${st.session_state.challenge_data.get('total_savings', 0)}")
            
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.user_profile = {}
                st.session_state.challenge_data = {}
                st.session_state.page = "signin"
                st.session_state.prediction_results = None
                st.session_state.show_stage_completion = False
                st.session_state.form_submitted = False
                st.session_state.show_error = None
                st.session_state.show_success = None
                st.session_state.show_motivational_task = False
                clear_persistent_login()
                st.rerun()

# Stage Completion Popup
def stage_completion_popup():
    if st.session_state.show_stage_completion:
        st.markdown("""
        <div class="popup-overlay">
            <div class="popup-content">
        """, unsafe_allow_html=True)
        
        st.success("🎉 CONGRATULATIONS! 🎉")
        st.markdown(f"### You've successfully completed the {st.session_state.challenge_data['current_stage']}!")
        st.markdown(f"### You've earned the {st.session_state.challenge_data['current_stage'].split(' ')[0]} Badge! 🏅")
        
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
                if st.button("Yes, Upgrade Stage", use_container_width=True):
                    challenge_data = st.session_state.challenge_data
                    challenge_data['current_stage'] = next_stage
                    challenge_data['current_day'] = 1
                    challenge_data['completed_days'] = 0
                    
                    save_challenge_data(st.session_state.user['username'], challenge_data)
                    st.session_state.challenge_data = challenge_data
                    st.session_state.show_stage_completion = False
                    st.rerun()
            
            with col2:
                if st.button("No, Stay Current", use_container_width=True):
                    st.session_state.show_stage_completion = False
                    st.rerun()
        else:
            st.success("🏆 YOU ARE A CHAMPION! You've completed all stages! 🏆")
            if st.button("Continue", use_container_width=True):
                st.session_state.show_stage_completion = False
                st.rerun()
        
        st.markdown("</div></div>", unsafe_allow_html=True)

# DAILY CHALLENGE PAGE - FIXED: Errors at TOP, Motivational task at BOTTOM
def daily_challenge_page():
    if "user" not in st.session_state or st.session_state.user is None:
        st.session_state.page = "signin"
        clear_persistent_login()
        st.rerun()
        return
    
    show_sidebar_content()
    
    # Show stage completion popup if needed
    if st.session_state.show_stage_completion:
        stage_completion_popup()
        return
    
    # FIXED: Show errors at the TOP of the page
    if st.session_state.show_error:
        st.error(st.session_state.show_error)
        # Clear error after 20 seconds
        if st.session_state.get('error_timer', 0) == 0:
            st.session_state.error_timer = time.time()
        elif time.time() - st.session_state.error_timer > 20:
            st.session_state.show_error = None
            st.session_state.error_timer = 0
            st.rerun()
    
    if st.session_state.show_success:
        st.success(st.session_state.show_success)
        # Clear success after 20 seconds
        if st.session_state.get('success_timer', 0) == 0:
            st.session_state.success_timer = time.time()
        elif time.time() - st.session_state.success_timer > 20:
            st.session_state.show_success = None
            st.session_state.success_timer = 0
            st.rerun()
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Daily Challenge Tracker</h1>", unsafe_allow_html=True)
    
    challenge_data = st.session_state.challenge_data
    user_profile = st.session_state.user_profile
    
    if not challenge_data or not user_profile:
        st.error("Please complete your profile setup first")
        st.session_state.page = "setup_profile"
        clear_persistent_login()
        st.rerun()
        return
    
    current_stage = challenge_data.get('current_stage', 'Silver (15 Days - Easy)')
    current_day = challenge_data.get('current_day', 1)
    streak_days = challenge_data.get('streak_days', 0)
    total_savings = challenge_data.get('total_savings', 0)
    completed_days = challenge_data.get('completed_days', 0)
    
    stage_days = get_stage_days(current_stage)
    days_left = stage_days - completed_days
    
    # Progress metrics
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
    
    # Check if stage is completed
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
            if st.checkbox(task, key=f"task_{task}"):
                completed_tasks.append(task)
        
        st.markdown("---")
        st.markdown("#### Savings Section")
        
        savings_amount = st.number_input("Amount to add to savings today ($)",
                                       min_value=0.0,
                                       step=1.0,
                                       key="savings_amount")
        
        submit_btn = st.form_submit_button("Submit Today's Progress")
        
        if submit_btn:
            process_daily_submission(completed_tasks, savings_amount, today, tasks)
    
    # FIXED: Show savings at the BOTTOM
    if challenge_data.get('total_savings', 0) > 0:
        st.markdown("---")
        st.markdown("### Your Challenge Savings")
        st.info(f"Total savings: **${challenge_data['total_savings']}**")
        st.markdown("Remember: When you complete this challenge, use this money for making a project in your field or invest it in your field.")
    
    # FIXED: Motivational task at the VERY BOTTOM
    if st.session_state.show_motivational_task:
        st.markdown("---")
        st.success("🎯 Your final task for today:")
        st.markdown("**Go to Google, find a motivational image and set it as your wallpaper.**")
        st.markdown("*When you wake up tomorrow, you'll see your mission first thing!*")
        
        # Clear after 20 seconds
        if st.session_state.get('motivational_timer', 0) == 0:
            st.session_state.motivational_timer = time.time()
        elif time.time() - st.session_state.motivational_timer > 20:
            st.session_state.show_motivational_task = False
            st.session_state.motivational_timer = 0
            st.rerun()

def process_daily_submission(completed_tasks, savings_amount, today, tasks):
    """FIXED: Proper rule enforcement with TOP errors and BOTTOM motivational task"""
    user = st.session_state.user
    challenge_data = st.session_state.challenge_data
    
    missed_tasks = len(tasks) - len(completed_tasks)
    
    # Always show motivational task at the bottom
    st.session_state.show_motivational_task = True
    st.session_state.motivational_timer = 0
    
    if missed_tasks == 0:
        # Perfect day - all tasks completed
        challenge_data['completed_days'] += 1
        challenge_data['current_day'] += 1
        challenge_data['total_savings'] += savings_amount
        challenge_data['streak_days'] += 1
        
        if 'daily_checkins' not in challenge_data:
            challenge_data['daily_checkins'] = {}
        challenge_data['daily_checkins'][today] = {
            'tasks_completed': completed_tasks,
            'missed_tasks': 0,
            'savings_added': savings_amount,
            'perfect_day': True
        }
        
        save_challenge_data(user['username'], challenge_data)
        st.session_state.challenge_data = challenge_data
        
        # FIXED: Show success at TOP
        st.session_state.show_success = "✅ Perfect day! All tasks completed! Your day is saved."
        st.session_state.success_timer = 0
        
    elif missed_tasks == 1:
        if savings_amount > 0:
            # Missed 1 task but paid penalty - day counts, streak increases
            challenge_data['streak_days'] += 1
            challenge_data['completed_days'] += 1
            challenge_data['current_day'] += 1
            challenge_data['total_savings'] += savings_amount
            
            penalty_record = {
                'date': today,
                'amount': savings_amount,
                'missed_tasks': 1,
                'reason': f"Missed 1 task: {set(tasks) - set(completed_tasks)}"
            }
            if 'penalty_history' not in challenge_data:
                challenge_data['penalty_history'] = []
            challenge_data['penalty_history'].append(penalty_record)
            
            if 'daily_checkins' not in challenge_data:
                challenge_data['daily_checkins'] = {}
            challenge_data['daily_checkins'][today] = {
                'tasks_completed': completed_tasks,
                'missed_tasks': 1,
                'savings_added': savings_amount,
                'perfect_day': False,
                'penalty_paid': True
            }
            
            save_challenge_data(user['username'], challenge_data)
            st.session_state.challenge_data = challenge_data
            
            # FIXED: Show success at TOP
            st.session_state.show_success = f"✅ Day counted! ${savings_amount} penalty paid. Streak: {challenge_data['streak_days']} days. Your day is saved."
            st.session_state.success_timer = 0
            
        else:
            # Missed 1 task but didn't pay penalty - show clear error at TOP
            st.session_state.show_error = "❌ According to rules: You missed 1 task but didn't pay penalty. This day doesn't count toward your progress."
            st.session_state.error_timer = 0
            
            if 'daily_checkins' not in challenge_data:
                challenge_data['daily_checkins'] = {}
            challenge_data['daily_checkins'][today] = {
                'tasks_completed': completed_tasks,
                'missed_tasks': 1,
                'savings_added': 0,
                'perfect_day': False,
                'day_not_counted': True
            }
            save_challenge_data(user['username'], challenge_data)
            st.session_state.challenge_data = challenge_data
            
    else:
        # Missed 2+ tasks - day doesn't count even with payment
        if savings_amount > 0:
            st.session_state.show_error = f"❌ According to rules: You missed {missed_tasks} tasks. This day doesn't count even if you pay penalty. Your ${savings_amount} was not accepted."
        else:
            st.session_state.show_error = f"❌ According to rules: You missed {missed_tasks} tasks. This day doesn't count."
        
        st.session_state.error_timer = 0
        
        if 'daily_checkins' not in challenge_data:
            challenge_data['daily_checkins'] = {}
        challenge_data['daily_checkins'][today] = {
            'tasks_completed': completed_tasks,
            'missed_tasks': missed_tasks,
            'savings_added': 0,  # Don't accept money for 2+ missed tasks
            'perfect_day': False,
            'day_not_counted': True
        }
        save_challenge_data(user['username'], challenge_data)
        st.session_state.challenge_data = challenge_data
    
    st.rerun()

# [Keep all other pages exactly the same as before - ML, Life Vision, Challenge Rules, Setup Profile, Sign In, Sign Up]
# ... (Include all the other page functions from previous code)

# Main app routing
if st.session_state.page == "signin":
    # Sign in page code
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            st.markdown("**Password: 8+ chars, uppercase, lowercase, number, special character**")
            
            login_button = st.form_submit_button("Sign In")
            
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
                                    profile_doc = db.collection('user_profiles').document(username_clean).get()
                                    if profile_doc.exists:
                                        st.session_state.user_profile = profile_doc.to_dict()
                                    st.session_state.challenge_data = load_challenge_data(username_clean)
                                    set_persistent_login(username_clean)
                                    st.success("Login successful!")
                                    st.session_state.page = "ml_dashboard"
                                    st.rerun()
                                else:
                                    st.error("Invalid username or password")
                            else:
                                st.error("Invalid username or password")
                        except Exception as e:
                            st.error("Login failed. Please try again.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("Forgot Password", use_container_width=True, on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        with col2:
            st.button("Create Account", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signup"}))

elif st.session_state.page == "signup":
    # Sign up page code
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create Account</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("signup_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm Password", type="password")
            
            st.markdown("**Password: 8+ chars, uppercase, lowercase, number, special character**")
            
            if password:
                strength, message = validate_password(password)
                if strength:
                    st.success("Strong password")
                else:
                    st.error("Weak password")
            
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                if not all([username, email, password, password2]):
                    st.error("Please fill in all fields")
                elif password != password2:
                    st.error("Passwords do not match")
                elif not validate_password(password)[0]:
                    st.error("Password does not meet security requirements")
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
                                        "role": "student",
                                        "created_at": firestore.SERVER_TIMESTAMP
                                    }
                                    db.collection('users').document(username_clean).set(user_data)
                                    st.success("Account created successfully!")
                                    st.session_state.page = "signin"
                                    st.rerun()
                        except Exception as e:
                            st.error("Registration failed. Please try again.")
        
        st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

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
elif st.session_state.page == "forgot_password":
    st.info("Password reset feature coming soon")
    st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"}))
