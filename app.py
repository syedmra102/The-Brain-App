import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore, auth
import smtplib
from email.message import EmailMessage
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from datetime import datetime, timedelta
import json
from fpdf import FPDF
import base64
from io import BytesIO
import traceback
import secrets
import hashlib

# Page config
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# Initialize session state with all required variables
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
if 'show_motivational_task' not in st.session_state:
    st.session_state.show_motivational_task = False
if 'phone_number' not in st.session_state:
    st.session_state.phone_number = ""
if 'ml_model_loaded' not in st.session_state:
    st.session_state.ml_model_loaded = False
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'reset_token' not in st.session_state:
    st.session_state.reset_token = None
if 'reset_username' not in st.session_state:
    st.session_state.reset_username = None

# Helper functions
def hash_password(password):
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        st.error("Password hashing failed")
        return None

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        return False

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)

def store_reset_token(username, token):
    """Store reset token in Firebase with expiration"""
    try:
        expires_at = datetime.now() + timedelta(hours=24)  # Token valid for 24 hours
        reset_data = {
            'token': token,
            'username': username,
            'expires_at': expires_at,
            'used': False
        }
        db.collection('password_resets').document(token).set(reset_data)
        return True
    except Exception as e:
        return False

def validate_reset_token(token):
    """Validate reset token and return username if valid"""
    try:
        doc_ref = db.collection('password_resets').document(token)
        doc = doc_ref.get()
        if doc.exists:
            reset_data = doc.to_dict()
            if (not reset_data.get('used', False) and 
                reset_data.get('expires_at') > datetime.now()):
                return reset_data.get('username')
        return None
    except Exception as e:
        return None

def mark_token_used(token):
    """Mark reset token as used"""
    try:
        db.collection('password_resets').document(token).update({'used': True})
        return True
    except Exception as e:
        return False

def send_password_reset_email(to_email, reset_link):
    try:
        email_config = st.secrets.get("email", {})
        email_address = email_config.get("EMAIL_ADDRESS", "")
        email_password = email_config.get("EMAIL_PASSWORD", "")
        
        if not email_address or not email_password:
            # DEVELOPMENT MODE - Show direct reset option
            st.session_state.page = "reset_password"
            return True, "Email service not configured. Please use the direct reset option below."
            
        msg = EmailMessage()
        msg['Subject'] = 'Your Brain App - Password Reset'
        msg['From'] = email_address
        msg['To'] = to_email
        msg.set_content(f"""
Hello,

You requested a password reset for your Brain App account.

Click the link below to reset your password:

{reset_link}

This link will expire in 24 hours.

If you did not request this, please ignore this email.

Best regards,
The Brain App Team
""")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        return True, "Password reset link sent to your email"
    except Exception as e:
        return False, f"Email service temporarily unavailable. Please try again later."

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
    except Exception as e:
        return None, None

def sanitize_input(text):
    return re.sub(r'[<>"\']', '', text.strip())

def set_persistent_login(username):
    try:
        st.query_params["username"] = username
        st.query_params["logged_in"] = "true"
    except Exception as e:
        pass

def clear_persistent_login():
    try:
        st.query_params.clear()
    except Exception as e:
        pass

# ... (KEEP ALL YOUR EXISTING FUNCTIONS THE SAME - challenge functions, analytics, etc.)
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
        return {}

def save_challenge_data(username, data):
    try:
        db.collection('challenge_progress').document(username).set(data)
        return True
    except Exception as e:
        return False

# ... (KEEP ALL YOUR EXISTING Firebase setup, ML model loading, etc.)

# Firebase setup
try:
    if 'firebase' in st.secrets:
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
    else:
        st.error("Firebase configuration not found.")
        st.stop()
except Exception as e:
    st.error("Database connection failed.")
    st.stop()

# ... (KEEP ALL YOUR EXISTING ML model functions, sidebar, etc.)

# ML Model loading
@st.cache_resource
def load_ml_model():
    try:
        with open('model.pkl', 'rb') as f:
            model_data = pickle.load(f)
        st.session_state.ml_model_loaded = True
        return model_data
    except FileNotFoundError:
        st.session_state.ml_model_loaded = False
        return None
    except Exception as e:
        st.session_state.ml_model_loaded = False
        return None

if not st.session_state.ml_model_loaded:
    model_data = load_ml_model()
else:
    model_data = None

def predict_performance(hours, distraction_count, habits):
    try:
        if model_data is None:
            return 75.0
            
        input_data = {}
        input_data['hours'] = hours
        input_data['distraction_count'] = distraction_count
        
        for col, value in habits.items():
            input_data[col] = value
        
        input_df = pd.DataFrame([input_data])
        
        required_columns = model_data.get('feature_columns', [])
        for col in required_columns:
            if col not in input_df.columns:
                input_df[col] = 0
        
        input_df = input_df[required_columns]
        
        if 'scaler' in model_data:
            numeric_cols = model_data.get('numeric_columns', ['hours', 'distraction_count'])
            input_df[numeric_cols] = model_data['scaler'].transform(input_df[numeric_cols])
        
        prediction = model_data['model'].predict(input_df)[0]
        prediction = max(1, min(100, prediction))
        
        return prediction
        
    except Exception as e:
        return 75.0

# ... (KEEP ALL YOUR EXISTING calculate_feature_percentiles, get_distraction_trend, show_sidebar_content functions)

def calculate_feature_percentiles(hours, distractions, habit_inputs):
    try:
        if model_data is None:
            return {
                'Study Hours': 50,
                'Distraction Control': 50,
                'Sugar Avoidance': 50,
                'Junk Food Avoidance': 50,
                'Water Intake': 50,
                'Sleep Schedule': 50,
                'Exercise Routine': 50,
                'Wake-up Time': 50
            }
            
        feature_percentiles = {}
        df = model_data['df']
        
        hours_percentile = (df['hours'] > hours).mean() * 100
        feature_percentiles['Study Hours'] = max(1, hours_percentile)
        
        dist_percentile = (df['distraction_count'] < distractions).mean() * 100
        feature_percentiles['Distraction Control'] = max(1, dist_percentile)
        
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
    except Exception as e:
        return {
            'Study Hours': 50,
            'Distraction Control': 50,
            'Sugar Avoidance': 50,
            'Junk Food Avoidance': 50,
            'Water Intake': 50,
            'Sleep Schedule': 50,
            'Exercise Routine': 50,
            'Wake-up Time': 50
        }

def get_distraction_trend(challenge_data):
    """Calculate distraction trend from challenge data"""
    try:
        daily_checkins = challenge_data.get('daily_checkins', {})
        if not daily_checkins:
            return "No data yet"
        
        distraction_days = 0
        total_days = len(daily_checkins)
        
        for date, checkin in daily_checkins.items():
            tasks_completed = checkin.get('tasks_completed', [])
            if "No distractions today" not in tasks_completed:
                distraction_days += 1
        
        if total_days == 0:
            return "No data"
        
        distraction_rate = (distraction_days / total_days) * 100
        if distraction_rate <= 20:
            return f"Excellent ({distraction_rate:.1f}% distraction days)"
        elif distraction_rate <= 40:
            return f"Good ({distraction_rate:.1f}% distraction days)"
        elif distraction_rate <= 60:
            return f"Average ({distraction_rate:.1f}% distraction days)"
        else:
            return f"Needs Improvement ({distraction_rate:.1f}% distraction days)"
            
    except Exception as e:
        return "Calculating..."

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
            
            if st.session_state.user_profile:
                if st.button("Daily Challenge", use_container_width=True):
                    st.session_state.page = "daily_challenge"
                    st.rerun()
                
                if st.button("Advanced Analytics", use_container_width=True):
                    st.session_state.page = "analytics"
                    st.rerun()
            
            if not st.session_state.user_profile:
                if st.button("Setup Profile", use_container_width=True):
                    st.session_state.page = "setup_profile"
                    st.rerun()
            
            if st.session_state.user_profile:
                if st.button("Edit Profile", use_container_width=True):
                    st.session_state.page = "edit_profile"
                    st.rerun()
            
            st.markdown("---")
            st.markdown("### My Profile")
            st.write(f"**Username:** {st.session_state.user['username']}")
            st.write(f"**Email:** {st.session_state.user['email']}")
            
            if st.session_state.user_profile:
                st.markdown("---")
                st.markdown("### My Goals")
                st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
                st.write(f"**Goal:** {st.session_state.user_profile.get('goal', 'Not set')}")
                st.write(f"**Stage:** {st.session_state.user_profile.get('stage', 'Not set')}")
                
                if st.session_state.challenge_data:
                    distraction_trend = get_distraction_trend(st.session_state.challenge_data)
                    st.write(f"**Distraction Trend:** {distraction_trend}")
                
            if st.session_state.challenge_data:
                st.markdown("---")
                st.markdown("### My Progress")
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
                clear_persistent_login()
                st.rerun()

# FIXED: Improved persistent login check
def check_persistent_login():
    if st.session_state.user is None and not st.session_state.initialized:
        try:
            query_params = st.query_params
            if 'username' in query_params and 'logged_in' in query_params and query_params['logged_in'] == "true":
                username = query_params['username']
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
                    st.session_state.initialized = True
        except Exception as e:
            pass

# Check for persistent login at the start
check_persistent_login()

# ... (KEEP ALL YOUR EXISTING PAGE FUNCTIONS - ml_dashboard_page, life_vision_page, etc.)
# ML Dashboard Page
def ml_dashboard_page():
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("### Predict your performance based on your daily habits")
    
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            hours = st.slider("Study Hours", 0, 12, 4)
            distraction_count = st.slider("Distractions Count", 0, 20, 5)
            
            st.markdown("#### Distraction Types")
            social_media = st.checkbox("Social Media", value=False)
            phone_calls = st.checkbox("Phone Calls", value=False)
            entertainment = st.checkbox("Entertainment", value=False)
            people_interruptions = st.checkbox("People Interruptions", value=False)
            other_distractions = st.checkbox("Other Distractions", value=False)
        
        with col2:
            st.markdown("#### Daily Habits")
            avoid_sugar = st.checkbox("Avoided Sugar", value=True)
            avoid_junk_food = st.checkbox("Avoided Junk Food", value=True)
            drink_5L_water = st.checkbox("Drank 5L Water", value=False)
            sleep_early = st.checkbox("Slept Before 11 PM", value=False)
            exercise_daily = st.checkbox("Daily Exercise", value=False)
            wakeup_early = st.checkbox("Woke Up Before 7 AM", value=False)
        
        submitted = st.form_submit_button("Predict My Performance", use_container_width=True)
        
        if submitted:
            habit_inputs = {
                'avoid_sugar': 1 if avoid_sugar else 0,
                'avoid_junk_food': 1 if avoid_junk_food else 0,
                'drink_5L_water': 1 if drink_5L_water else 0,
                'sleep_early': 1 if sleep_early else 0,
                'exercise_daily': 1 if exercise_daily else 0,
                'wakeup_early': 1 if wakeup_early else 0
            }
            
            distraction_types = []
            if social_media:
                distraction_types.append("Social Media")
            if phone_calls:
                distraction_types.append("Phone Calls")
            if entertainment:
                distraction_types.append("Entertainment")
            if people_interruptions:
                distraction_types.append("People Interruptions")
            if other_distractions:
                distraction_types.append("Other")
            
            prediction = predict_performance(hours, distraction_count, habit_inputs)
            percentiles = calculate_feature_percentiles(hours, distraction_count, habit_inputs)
            
            st.session_state.prediction_results = {
                'score': prediction,
                'percentiles': percentiles,
                'hours': hours,
                'distractions': distraction_count,
                'distraction_types': distraction_types,
                'habits': habit_inputs
            }
    
    if st.session_state.prediction_results:
        results = st.session_state.prediction_results
        
        st.markdown("---")
        st.markdown("### Prediction Results")
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            score = results['score']
            if score <= 20:
                color = "green"
                status = "Elite Performer"
                interpretation = f"You're in the top {score}% of users! Excellent!"
            elif score <= 40:
                color = "blue"
                status = "Great Performer"
                interpretation = f"You're in the top {score}% - Great job!"
            elif score <= 60:
                color = "orange"
                status = "Good Performer"
                interpretation = f"You're in the top {score}% - Good work!"
            else:
                color = "red"
                status = "Needs Improvement"
                interpretation = f"You're in the top {score}% - Room to grow"
            
            st.markdown(f"<h1 style='text-align: center; color: {color};'>Performance Score: {score:.1f}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: {color};'>{status}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>{interpretation}</p>", unsafe_allow_html=True)
        
        if results['distraction_types']:
            st.markdown("#### Your Distractions Today")
            for distraction in results['distraction_types']:
                st.write(f"- {distraction}")
        
        st.markdown("#### Feature Analysis - Percentile Ranking")
        features_df = pd.DataFrame(list(results['percentiles'].items()), columns=['Feature', 'Percentile'])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        features = features_df['Feature']
        percentiles = features_df['Percentile']
        
        bars = ax.bar(features, percentiles, color='navy', alpha=0.7)
        ax.set_ylabel('Percentile Score (%)')
        ax.set_title('Feature Performance (Lower % = Better Ranking)')
        ax.set_ylim(0, 100)
        
        for bar, value in zip(bars, percentiles):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{value:.0f}%', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        
        st.markdown("#### Detailed Feature Breakdown")
        for _, row in features_df.iterrows():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"{row['Feature']}:")
            with col2:
                percentile = row['Percentile']
                progress_value = max(0, 100 - percentile) / 100
                st.progress(progress_value, text=f"Top {percentile:.0f}%")
        
        st.markdown("#### Recommendations")
        excellent_features = [f for f, p in results['percentiles'].items() if p <= 20]
        good_features = [f for f, p in results['percentiles'].items() if p <= 40]
        needs_work_features = [f for f, p in results['percentiles'].items() if p > 60]
        
        if excellent_features:
            st.success("**Your Strengths (Elite Level):**")
            for feature in excellent_features:
                percentile = results['percentiles'][feature]
                st.write(f"- {feature} (Top {percentile:.0f}%)")
        
        if good_features:
            st.info("**Good Performance:**")
            for feature in good_features:
                if feature not in excellent_features:
                    percentile = results['percentiles'][feature]
                    st.write(f"- {feature} (Top {percentile:.0f}%)")
        
        if needs_work_features:
            st.warning("**Areas for Improvement:**")
            for feature in needs_work_features:
                percentile = results['percentiles'][feature]
                st.write(f"- {feature} (Top {percentile:.0f}%)")
        
        if st.button("Make Another Prediction", use_container_width=True):
            st.session_state.prediction_results = None
            st.rerun()

# ... (KEEP ALL YOUR EXISTING life_vision_page, challenge_rules_page, setup_profile_page)

# Life Vision Page
def life_vision_page():
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>My Life Vision</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.info("Please complete your profile setup to access the full Life Vision features.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    st.markdown("### My Vision Board")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Current Status")
        st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
        st.write(f"**Goal:** {st.session_state.user_profile.get('goal', 'Not set')}")
        st.write(f"**Stage:** {st.session_state.user_profile.get('stage', 'Not set')}")
        
        if st.session_state.challenge_data:
            distraction_trend = get_distraction_trend(st.session_state.challenge_data)
            st.write(f"**Distraction Trend:** {distraction_trend}")
            
        if st.session_state.challenge_data:
            st.write(f"**Current Day:** {st.session_state.challenge_data.get('current_day', 1)}")
            st.write(f"**Streak:** {st.session_state.challenge_data.get('streak_days', 0)} days")
            st.write(f"**Total Savings:** ${st.session_state.challenge_data.get('total_savings', 0)}")
    
    with col2:
        st.markdown("#### Progress Visualization")
        if st.session_state.challenge_data:
            current_day = st.session_state.challenge_data.get('current_day', 1)
            stage = st.session_state.user_profile.get('stage', 'Silver (15 Days - Easy)')
            total_days = get_stage_days(stage)
            
            progress = (current_day / total_days) * 100
            st.progress(progress/100, text=f"Stage Progress: {current_day}/{total_days} days ({progress:.1f}%)")
            
            if progress < 25:
                st.info("Getting started! Every great journey begins with a single step.")
            elif progress < 50:
                st.info("Making progress! Keep building momentum.")
            elif progress < 75:
                st.info("Halfway there! You are doing amazing.")
            else:
                st.info("Almost there! Finish strong!")
    
    st.markdown("---")
    st.markdown("### Daily Motivation")
    
    motivational_quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "The future depends on what you do today. - Mahatma Gandhi",
        "Do not watch the clock; do what it does. Keep going. - Sam Levenson",
        "The harder you work for something, the greater you will feel when you achieve it.",
    ]
    
    import random
    daily_quote = random.choice(motivational_quotes)
    st.success(f"**Today's Motivation:** {daily_quote}")
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Start Today's Challenge", use_container_width=True):
            st.session_state.page = "daily_challenge"
            st.rerun()
    
    with col2:
        if st.button("View Analytics", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()
    
    with col3:
        if st.button("Edit Profile", use_container_width=True):
            st.session_state.page = "edit_profile"
            st.rerun()

# ... (KEEP ALL YOUR EXISTING challenge_rules_page, setup_profile_page, edit_profile_page, etc.)

# Challenge Rules Page
def challenge_rules_page():
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Challenge Rules & Guidelines</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ## The Brain App Challenge System
    
    ### Challenge Stages
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### Silver Stage
        **Duration:** 15 Days (Easy)
        
        **Daily Tasks:**
        - 2 hours of focused work
        - No distractions
        - Fill daily routine form
        """)
    
    with col2:
        st.markdown("""
        ### Platinum Stage  
        **Duration:** 30 Days (Medium)
        
        **Daily Tasks:**
        - 4 hours of focused work
        - No distractions
        - 30 pushups exercise
        - Drink 5L water
        - Avoid junk food
        - Fill daily form
        """)
    
    with col3:
        st.markdown("""
        ### Gold Stage
        **Duration:** 60 Days (Hard)
        
        **Daily Tasks:**
        - 6 hours of focused work
        - No distractions
        - 50 pushups exercise
        - Drink 5L water
        - Avoid junk food & sugar
        - Wake up before 7 AM
        - Sleep before 11 PM
        - Fill daily form
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ## Challenge Rules
    
    ### Task Completion Rules:
    1. **Perfect Day (All tasks completed):**
       - Day counts toward progress
       - Streak increases by 1
       - Savings added to total
    
    2. **Miss 1 Task:**
       - **With Penalty Payment:** Day counts but streak does not increase
       - **Without Penalty:** Day does not count toward progress
    
    3. **Miss 2+ Tasks:**
       - Day does not count (even with penalty)
       - No progress made
    """)
    
    if st.button("Back to Dashboard", use_container_width=True):
        st.session_state.page = "life_vision"
        st.rerun()

# Setup Profile Page
def setup_profile_page():
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Setup Your Profile</h1>", unsafe_allow_html=True)
    
    with st.form("profile_setup"):
        st.markdown("### Tell Us About Yourself")
        
        col1, col2 = st.columns(2)
        
        with col1:
            field = st.selectbox(
                "Your Field/Interest",
                [
                    "Student - Computer Science", 
                    "Student - Engineering",
                    "Student - Medicine", 
                    "Student - Business",
                    "Student - Arts & Humanities",
                    "Software Developer",
                    "Data Scientist",
                    "Web Developer",
                    "Mobile App Developer",
                    "AI/ML Engineer",
                    "Entrepreneur",
                    "Researcher",
                    "Teacher/Educator",
                    "Digital Marketer",
                    "Content Creator",
                    "Other"
                ]
            )
        with col2:
            goal = st.text_input("I want to become...", placeholder="e.g., a successful entrepreneur")
        
        st.markdown("### Choose Your Challenge Stage")
        stage = st.selectbox(
            "Challenge Difficulty",
            ["Silver (15 Days - Easy)", "Platinum (30 Days - Medium)", "Gold (60 Days - Hard)"]
        )
        
        submitted = st.form_submit_button("Save Profile & Start Challenge", use_container_width=True)
        
        if submitted:
            if not goal:
                st.error("Please tell us what you want to become!")
                return
            
            profile_data = {
                'field': field,
                'goal': goal,
                'stage': stage,
                'created_at': datetime.now()
            }
            
            try:
                db.collection('user_profiles').document(st.session_state.user['username']).set(profile_data)
                st.session_state.user_profile = profile_data
                
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
                save_challenge_data(st.session_state.user['username'], challenge_data)
                st.session_state.challenge_data = challenge_data
                
                st.success("Profile setup complete! Welcome to The Brain App Challenge!")
                time.sleep(2)
                st.session_state.page = "life_vision"
                st.rerun()
                
            except Exception as e:
                st.error("Error saving profile. Please try again.")

# Edit Profile Page
def edit_profile_page():
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Edit Your Profile</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.error("No profile found. Please setup your profile first.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    with st.form("edit_profile"):
        st.markdown("### Update Your Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_field = st.session_state.user_profile.get('field', 'Student - Computer Science')
            field_options = [
                "Student - Computer Science", 
                "Student - Engineering",
                "Student - Medicine", 
                "Student - Business",
                "Student - Arts & Humanities",
                "Software Developer",
                "Data Scientist",
                "Web Developer",
                "Mobile App Developer",
                "AI/ML Engineer",
                "Entrepreneur",
                "Researcher",
                "Teacher/Educator",
                "Digital Marketer",
                "Content Creator",
                "Other"
            ]
            
            field_index = field_options.index(current_field) if current_field in field_options else 0
            field = st.selectbox("Your Field/Interest", field_options, index=field_index)
            
        with col2:
            goal = st.text_input("I want to become...", value=st.session_state.user_profile.get('goal', ''))
        
        current_stage = st.session_state.user_profile.get('stage', 'Silver (15 Days - Easy)')
        stage_options = ["Silver (15 Days - Easy)", "Platinum (30 Days - Medium)", "Gold (60 Days - Hard)"]
        stage_index = stage_options.index(current_stage) if current_stage in stage_options else 0
        
        stage = st.selectbox("Challenge Difficulty", stage_options, index=stage_index)
        
        st.markdown("### Common Distractions")
        st.markdown("Select the types of distractions you commonly face:")
        
        col1, col2 = st.columns(2)
        with col1:
            distraction_social_media = st.checkbox("Social Media", value=False)
            distraction_phone = st.checkbox("Phone/Notifications", value=False)
            distraction_entertainment = st.checkbox("Entertainment (TV/Games)", value=False)
            distraction_people = st.checkbox("People Interruptions", value=False)
            distraction_noise = st.checkbox("Environmental Noise", value=False)
        
        with col2:
            distraction_procrastination = st.checkbox("Procrastination", value=False)
            distraction_multitasking = st.checkbox("Multitasking", value=False)
            distraction_mental = st.checkbox("Mental Fatigue", value=False)
            distraction_physical = st.checkbox("Physical Discomfort", value=False)
            distraction_other = st.checkbox("Other Distractions", value=False)
        
        submitted = st.form_submit_button("Update Profile", use_container_width=True)
        
        if submitted:
            if not goal:
                st.error("Please tell us what you want to become!")
                return
            
            user_distractions = []
            if distraction_social_media:
                user_distractions.append("Social Media")
            if distraction_phone:
                user_distractions.append("Phone/Notifications")
            if distraction_entertainment:
                user_distractions.append("Entertainment")
            if distraction_people:
                user_distractions.append("People Interruptions")
            if distraction_noise:
                user_distractions.append("Environmental Noise")
            if distraction_procrastination:
                user_distractions.append("Procrastination")
            if distraction_multitasking:
                user_distractions.append("Multitasking")
            if distraction_mental:
                user_distractions.append("Mental Fatigue")
            if distraction_physical:
                user_distractions.append("Physical Discomfort")
            if distraction_other:
                user_distractions.append("Other")
            
            profile_data = {
                'field': field,
                'goal': goal,
                'stage': stage,
                'common_distractions': user_distractions,
                'updated_at': datetime.now()
            }
            
            try:
                db.collection('user_profiles').document(st.session_state.user['username']).update(profile_data)
                st.session_state.user_profile.update(profile_data)
                st.success("Profile updated successfully!")
                
                if user_distractions:
                    st.info(f"**Your common distractions:** {', '.join(user_distractions)}")
                    if len(user_distractions) >= 3:
                        st.warning("You have multiple distraction sources. Consider focusing on one at a time for improvement.")
                    else:
                        st.success("Good job identifying your distraction sources! Awareness is the first step to improvement.")
                
                time.sleep(2)
                st.session_state.page = "life_vision"
                st.rerun()
                
            except Exception as e:
                st.error("Error updating profile. Please try again.")

# ... (KEEP ALL YOUR EXISTING daily_challenge_page, analytics_page)

# Daily Challenge Page
def daily_challenge_page():
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Daily Challenge</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.error("Please complete your profile setup first.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    challenge_data = st.session_state.challenge_data
    current_stage = st.session_state.user_profile.get('stage', 'Silver (15 Days - Easy)')
    current_day = challenge_data.get('current_day', 1)
    total_days = get_stage_days(current_stage)
    
    st.markdown(f"### {current_stage} - Day {current_day}/{total_days}")
    
    progress = (current_day / total_days) * 100
    st.progress(progress/100, text=f"Stage Progress: {progress:.1f}%")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Streak", f"{challenge_data.get('streak_days', 0)} days")
    with col2:
        st.metric("Completed Days", challenge_data.get('completed_days', 0))
    with col3:
        st.metric("Total Savings", f"${challenge_data.get('total_savings', 0)}")
    
    st.markdown("---")
    
    today = datetime.now().strftime("%Y-%m-%d")
    if challenge_data.get('daily_checkins', {}).get(today):
        st.success("You have already completed today's check-in! Great job!")
        st.info("Come back tomorrow for your next challenge.")
        return
    
    st.markdown("### Today's Tasks")
    tasks = get_stage_tasks(current_stage)
    
    completed_tasks = []
    for task in tasks:
        if st.checkbox(task, key=f"task_{task}"):
            completed_tasks.append(task)
    
    st.markdown("---")
    st.markdown("### Penalty & Savings")
    
    missed_tasks = len(tasks) - len(completed_tasks)
    if missed_tasks == 1:
        savings_amount = st.number_input("Penalty Amount", min_value=0.0, value=5.0, step=1.0)
    else:
        savings_amount = st.number_input("Savings to Add", min_value=0.0, value=10.0, step=1.0)
    
    if st.button("Submit Daily Check-in", use_container_width=True, type="primary"):
        process_daily_submission(completed_tasks, savings_amount, today, tasks)

def process_daily_submission(completed_tasks, savings_amount, today, tasks):
    try:
        user = st.session_state.user
        challenge_data = st.session_state.challenge_data
        
        missed_tasks = len(tasks) - len(completed_tasks)
        
        if missed_tasks == 0:
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
            st.session_state.form_submitted = True
            
            st.success("Perfect day! All tasks completed!")
            
        elif missed_tasks == 1:
            if savings_amount > 0:
                challenge_data['completed_days'] += 1
                challenge_data['current_day'] += 1
                challenge_data['total_savings'] += savings_amount
                
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
                st.session_state.form_submitted = True
                
                st.warning(f"You missed 1 task but paid ${savings_amount} penalty. Day counted.")
                
            else:
                st.error("You missed 1 task but did not pay penalty. This day does not count.")
        else:
            st.error(f"You missed {missed_tasks} tasks. This day does not count.")
        
        st.rerun()
    except Exception as e:
        st.error("Error processing submission. Please try again.")

# Analytics Page
def analytics_page():
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Advanced Analytics</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.error("Please complete your profile setup first.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    challenge_data = st.session_state.challenge_data
    
    st.markdown("### Progress Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Stage", st.session_state.user_profile.get('stage', 'Not set'))
    with col2:
        st.metric("Current Day", challenge_data.get('current_day', 1))
    with col3:
        st.metric("Streak Days", challenge_data.get('streak_days', 0))
    with col4:
        st.metric("Total Savings", f"${challenge_data.get('total_savings', 0)}")
    
    create_advanced_analytics(challenge_data, st.session_state.user_profile)
    
    badges = challenge_data.get('badges', [])
    if badges:
        st.markdown("---")
        st.markdown("### Earned Badges")
        for badge in badges:
            st.success(f"**{badge}**")

# NEW: Reset Password Page - ACTUALLY WORKS!
def reset_password_page():
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Reset Your Password</h1>", unsafe_allow_html=True)
    
    # If we have a token, show password reset form
    if st.session_state.reset_token and st.session_state.reset_username:
        st.success("Token verified! Please enter your new password.")
        
        with st.form("reset_password_form"):
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
            
            submitted = st.form_submit_button("Reset Password", use_container_width=True)
            
            if submitted:
                if not new_password or not confirm_password:
                    st.error("Please fill in all fields")
                    return
                
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                is_valid, message = validate_password(new_password)
                if not is_valid:
                    st.error(f"Password requirements: {message}")
                    return
                
                try:
                    # Hash new password
                    hashed_password = hash_password(new_password)
                    if not hashed_password:
                        st.error("Error resetting password. Please try again.")
                        return
                    
                    # Update password in database
                    db.collection('users').document(st.session_state.reset_username).update({
                        'password': hashed_password,
                        'updated_at': datetime.now()
                    })
                    
                    # Mark token as used
                    mark_token_used(st.session_state.reset_token)
                    
                    st.success("Password reset successfully! You can now sign in with your new password.")
                    time.sleep(2)
                    
                    # Clear reset state and go to sign in
                    st.session_state.reset_token = None
                    st.session_state.reset_username = None
                    st.session_state.page = "signin"
                    st.rerun()
                    
                except Exception as e:
                    st.error("Error resetting password. Please try again.")
    
    else:
        # Show token input form
        st.info("Please enter the reset token you received.")
        
        with st.form("enter_token_form"):
            reset_token = st.text_input("Reset Token", placeholder="Enter your reset token")
            
            submitted = st.form_submit_button("Verify Token", use_container_width=True)
            
            if submitted:
                if not reset_token:
                    st.error("Please enter a reset token")
                    return
                
                username = validate_reset_token(reset_token)
                if username:
                    st.session_state.reset_token = reset_token
                    st.session_state.reset_username = username
                    st.rerun()
                else:
                    st.error("Invalid or expired reset token. Please request a new one.")
    
    st.markdown("---")
    if st.button("Back to Sign In", use_container_width=True):
        st.session_state.page = "signin"
        st.rerun()

# UPDATED: Forgot Password Page - NOW WORKS!
def forgot_password_page():
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Reset Your Password</h1>", unsafe_allow_html=True)
    
    with st.form("forgot_password_form"):
        email = st.text_input("Email Address", placeholder="Enter your registered email")
        submitted = st.form_submit_button("Send Reset Link", use_container_width=True)
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
                return
            
            user_id, user_data = get_user_by_email(email)
            if user_data:
                # Generate secure reset token
                reset_token = generate_reset_token()
                
                # Store token in database
                if store_reset_token(user_id, reset_token):
                    
                    # Create reset link (in production, this would be your app URL)
                    reset_link = f"Reset Token: {reset_token}\n\nPlease copy this token and use it on the reset page."
                    
                    # Try to send email
                    success, message = send_password_reset_email(email, reset_link)
                    
                    if success:
                        if "Development mode" in message:
                            # Show token directly in development mode
                            st.success("Email service not configured - Development Mode")
                            st.info(f"**Your Reset Token:** {reset_token}")
                            st.info("Please copy this token and go to the reset password page to continue.")
                        else:
                            st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Error generating reset token. Please try again.")
            else:
                st.error("No account found with this email address")
    
    # Direct token entry option
    st.markdown("---")
    st.markdown("### Already have a reset token?")
    if st.button("Enter Reset Token", use_container_width=True):
        st.session_state.page = "reset_password"
        st.rerun()
    
    st.markdown("---")
    if st.button("Back to Sign In", use_container_width=True):
        st.session_state.page = "signin"
        st.rerun()

# Sign In Page
def sign_in_page():
    st.markdown("<h1 style='text-align: center; color: darkblue;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign In to Your Account</h3>", unsafe_allow_html=True)
    
    with st.form("signin_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Sign In", use_container_width=True)
        with col2:
            if st.form_submit_button("Forgot Password?", use_container_width=True):
                st.session_state.page = "forgot_password"
                st.rerun()
        
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return
            
            try:
                user_doc = db.collection('users').document(username).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    if check_password(password, user_data['password']):
                        st.session_state.user = {
                            "username": username,
                            "email": user_data.get("email", ""),
                            "role": user_data.get("role", "student")
                        }
                        
                        profile_doc = db.collection('user_profiles').document(username).get()
                        if profile_doc.exists:
                            st.session_state.user_profile = profile_doc.to_dict()
                        
                        st.session_state.challenge_data = load_challenge_data(username)
                        set_persistent_login(username)
                        st.session_state.initialized = True
                        
                        st.success(f"Welcome back, {username}!")
                        st.session_state.page = "life_vision"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid password")
                else:
                    st.error("Username not found")
            except Exception as e:
                st.error("Login failed. Please try again.")
    
    st.markdown("---")
    st.markdown("Don't have an account?")
    if st.button("Sign Up", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()

# Sign Up Page
def sign_up_page():
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Create Your Account</h1>", unsafe_allow_html=True)
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email Address", placeholder="Enter your email")
        
        with col2:
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        if password:
            is_valid, message = validate_password(password)
            if not is_valid:
                st.warning(f"Password requirements: {message}")
        
        agreed = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            if not all([username, email, password, confirm_password]):
                st.error("Please fill in all fields")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            if not agreed:
                st.error("Please agree to the Terms of Service")
                return
            
            user_doc = db.collection('users').document(username).get()
            if user_doc.exists:
                st.error("Username already taken. Please choose another.")
                return
            
            _, existing_user = get_user_by_email(email)
            if existing_user:
                st.error("Email already registered. Please use a different email or sign in.")
                return
            
            try:
                hashed_password = hash_password(password)
                if not hashed_password:
                    st.error("Error creating account. Please try again.")
                    return
                
                user_data = {
                    'username': username,
                    'email': email,
                    'password': hashed_password,
                    'created_at': datetime.now()
                }
                
                db.collection('users').document(username).set(user_data)
                st.success("Account created successfully!")
                st.info("You can now sign in with your credentials.")
                time.sleep(2)
                st.session_state.page = "signin"
                st.rerun()
                
            except Exception as e:
                st.error("Error creating account. Please try again.")
    
    st.markdown("---")
    st.markdown("Already have an account?")
    if st.button("Sign In", use_container_width=True):
        st.session_state.page = "signin"
        st.rerun()

# Certificate Page
def certificate_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>Your Achievement Certificate</h1>", unsafe_allow_html=True)
        
        if st.button("Back to Dashboard", use_container_width=False):
            st.session_state.page = "daily_challenge"
            st.rerun()
        
        with st.spinner("Generating your certificate..."):
            pdf_bytes = generate_certificate(
                st.session_state.user['username'],
                st.session_state.user_profile,
                st.session_state.challenge_data
            )
        
        if pdf_bytes:
            st.success("Your certificate is ready!")
            
            st.download_button(
                label="Download PDF Certificate",
                data=pdf_bytes,
                file_name=f"brain_app_certificate_{st.session_state.user['username']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("Failed to generate certificate. Please try again.")
            
    except Exception as e:
        st.error("Something went wrong with certificate generation.")

# Main app routing - UPDATED with new reset_password_page
try:
    if st.session_state.page == "signin":
        sign_in_page()
    elif st.session_state.page == "signup":
        sign_up_page()
    elif st.session_state.page == "forgot_password":
        forgot_password_page()
    elif st.session_state.page == "reset_password":  # NEW PAGE
        reset_password_page()
    elif st.session_state.page == "ml_dashboard":
        ml_dashboard_page()
    elif st.session_state.page == "life_vision":
        life_vision_page()
    elif st.session_state.page == "challenge_rules":
        challenge_rules_page()
    elif st.session_state.page == "setup_profile":
        setup_profile_page()
    elif st.session_state.page == "edit_profile":
        edit_profile_page()
    elif st.session_state.page == "daily_challenge":
        daily_challenge_page()
    elif st.session_state.page == "analytics":
        analytics_page()
    elif st.session_state.page == "certificate":
        certificate_page()
    else:
        st.session_state.page = "signin"
        st.rerun()

except Exception as e:
    st.error("An unexpected error occurred. Please refresh the page.")
