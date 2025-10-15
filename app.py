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
        
        # Convert to Firestore timestamp
        from google.cloud import firestore as google_firestore
        firestore_expires = google_firestore.SERVER_TIMESTAMP
        
        reset_data = {
            'token': token,
            'username': username,
            'expires_at': expires_at,
            'created_at': datetime.now(),
            'used': False
        }
        db.collection('password_resets').document(token).set(reset_data)
        return True
    except Exception as e:
        st.error(f"Error storing token: {str(e)}")
        return False

def validate_reset_token(token):
    """Validate reset token and return username if valid"""
    try:
        doc_ref = db.collection('password_resets').document(token)
        doc = doc_ref.get()
        
        if not doc.exists:
            st.error("Token not found in database")
            return None
            
        reset_data = doc.to_dict()
        
        # Check if token is used
        if reset_data.get('used', False):
            st.error("Token has already been used")
            return None
            
        # Check expiration
        expires_at = reset_data.get('expires_at')
        if not expires_at:
            st.error("Token has no expiration date")
            return None
            
        # Convert Firestore timestamp to datetime if needed
        if hasattr(expires_at, 'timestamp'):
            expires_at = expires_at.replace(tzinfo=None)
        
        if expires_at < datetime.now():
            st.error("Token has expired")
            return None
            
        return reset_data.get('username')
        
    except Exception as e:
        st.error(f"Error validating token: {str(e)}")
        return None

def mark_token_used(token):
    """Mark reset token as used"""
    try:
        db.collection('password_resets').document(token).update({
            'used': True,
            'used_at': datetime.now()
        })
        return True
    except Exception as e:
        st.error(f"Error marking token as used: {str(e)}")
        return False

def send_password_reset_email(to_email, reset_token):
    try:
        email_config = st.secrets.get("email", {})
        email_address = email_config.get("EMAIL_ADDRESS", "")
        email_password = email_config.get("EMAIL_PASSWORD", "")
        
        if not email_address or not email_password:
            # DEVELOPMENT MODE - Show token directly
            return True, "development", reset_token
            
        msg = EmailMessage()
        msg['Subject'] = 'Your Brain App - Password Reset'
        msg['From'] = email_address
        msg['To'] = to_email
        msg.set_content(f"""
Hello,

You requested a password reset for your Brain App account.

Use this reset token to reset your password:

{reset_token}

You can enter this token on the password reset page.

This token will expire in 24 hours.

If you did not request this, please ignore this email.

Best regards,
The Brain App Team
""")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        return True, "sent", reset_token
    except Exception as e:
        return False, f"Email service temporarily unavailable. Please try again later.", None

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

# ... (KEEP ALL YOUR EXISTING FUNCTIONS - sanitize_input, set_persistent_login, clear_persistent_login, challenge functions, etc.)

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

# ... (KEEP ALL YOUR EXISTING ML model functions, sidebar, page functions)

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

# ... (KEEP ALL YOUR EXISTING predict_performance, calculate_feature_percentiles, get_distraction_trend functions)

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

# ... (KEEP ALL YOUR EXISTING PAGE FUNCTIONS - ml_dashboard_page, life_vision_page, challenge_rules_page, setup_profile_page, edit_profile_page, daily_challenge_page, analytics_page)

# NEW: SIMPLE RESET PASSWORD PAGE THAT ACTUALLY WORKS
def reset_password_page():
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Reset Your Password</h1>", unsafe_allow_html=True)
    
    # If we have username from token, show password reset form
    if st.session_state.reset_username:
        st.success(f"Reset authorized for user: {st.session_state.reset_username}")
        
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
                    
                    # Mark token as used if we have one
                    if st.session_state.reset_token:
                        mark_token_used(st.session_state.reset_token)
                    
                    st.success("✅ Password reset successfully! You can now sign in with your new password.")
                    time.sleep(3)
                    
                    # Clear reset state and go to sign in
                    st.session_state.reset_token = None
                    st.session_state.reset_username = None
                    st.session_state.page = "signin"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error resetting password: {str(e)}")
    
    else:
        # Show token input form
        st.info("Please enter the reset token you received")
        
        with st.form("enter_token_form"):
            reset_token = st.text_input("Reset Token", placeholder="Paste your reset token here")
            
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
                    st.error("❌ Invalid or expired reset token. Please request a new one.")
    
    st.markdown("---")
    if st.button("Back to Sign In", use_container_width=True):
        st.session_state.page = "signin"
        st.rerun()

# UPDATED: Forgot Password Page - SIMPLIFIED AND WORKS
def forgot_password_page():
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Reset Your Password</h1>", unsafe_allow_html=True)
    
    st.info("Enter your email address to receive a password reset token")
    
    with st.form("forgot_password_form"):
        email = st.text_input("Email Address", placeholder="Enter your registered email")
        submitted = st.form_submit_button("Generate Reset Token", use_container_width=True)
        
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
                    
                    # Try to send email
                    success, message, token = send_password_reset_email(email, reset_token)
                    
                    if success:
                        if message == "development":
                            # DEVELOPMENT MODE - Show token directly
                            st.success("🔧 Development Mode - Email service not configured")
                            st.info("**Your Reset Token (copy this):**")
                            st.code(reset_token, language="text")
                            st.info("👉 Use this token on the reset password page")
                            
                            # Auto-redirect to reset page
                            st.session_state.reset_token = reset_token
                            st.session_state.reset_username = user_id
                            st.success("Auto-redirecting to reset page...")
                            time.sleep(2)
                            st.session_state.page = "reset_password"
                            st.rerun()
                        else:
                            st.success("✅ Reset token sent to your email!")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Error generating reset token. Please try again.")
            else:
                st.error("❌ No account found with this email address")
    
    # Direct manual token entry
    st.markdown("---")
    st.markdown("### Already have a reset token?")
    if st.button("Enter Reset Token Manually", use_container_width=True):
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

# ... (KEEP ALL YOUR EXISTING Certificate Page and other pages)

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
    elif st.session_state.page == "reset_password":
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
    st.error(f"An unexpected error occurred: {str(e)}")
