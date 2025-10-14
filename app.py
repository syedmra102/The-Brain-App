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
import requests
import json

# Page config with modern theme
st.set_page_config(
    page_title="The Brain App", 
    page_icon="🧠", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Modern button styles */
    .stButton>button {
        border-radius: 12px;
        border: 2px solid #7C3AED;
        background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%);
        color: white;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(124, 58, 237, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(124, 58, 237, 0.3);
        background: linear-gradient(135deg, #6D28D9 0%, #4338CA 100%);
    }
    
    /* Modern containers */
    .modern-container {
        background: white;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Penalty container with strong visual impact */
    .penalty-container {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border: 2px solid #F59E0B;
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
    }
    
    .reward-container {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        border: 2px solid #10B981;
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .modern-container {
            padding: 16px;
            margin: 12px 0;
        }
        
        .stButton>button {
            padding: 14px 20px;
            font-size: 16px;
        }
    }
    
    /* Form styling */
    .stForm {
        background: white;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_password_reset_token(email):
    """Generate a secure password reset token"""
    try:
        # Using Firebase Auth for password reset
        link = auth.generate_password_reset_link(email)
        return True, link
    except Exception as e:
        return False, str(e)

def send_password_reset_email(to_email, reset_link):
    """Send secure password reset email"""
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Brain App - Password Reset Request'
        msg['From'] = st.secrets["email"]["address"]
        msg['To'] = to_email
        msg.set_content(f"""
        Hello,
        
        You requested a password reset for your Brain App account.
        
        Click this link to reset your password: {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        The Brain App Team
        """)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(st.secrets["email"]["address"], st.secrets["email"]["password"])
            smtp.send_message(msg)
        return True, "Password reset link sent to your email"
    except Exception as e:
        return False, "Email service temporarily unavailable"

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

# Mock savings service integration
class SavingsService:
    @staticmethod
    def process_savings_transaction(user_id, amount, description):
        """Mock savings transaction processing"""
        try:
            # In a real implementation, this would integrate with a payment service
            # For now, we'll simulate processing with enhanced UI feedback
            
            transaction_data = {
                'user_id': user_id,
                'amount': amount,
                'description': description,
                'timestamp': datetime.now(),
                'status': 'completed',
                'transaction_id': f"TX_{int(time.time())}_{user_id}"
            }
            
            # Simulate API call delay
            time.sleep(1)
            
            return True, transaction_data, "Savings transaction completed successfully!"
            
        except Exception as e:
            return False, None, f"Transaction failed: {str(e)}"

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
                'badges': [],
                'savings_transactions': []
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

# Firebase setup with proper authentication
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
if 'show_motivational_task' not in st.session_state:
    st.session_state.show_motivational_task = False
if 'savings_processed' not in st.session_state:
    st.session_state.savings_processed = False

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
                st.session_state.page = "daily_challenge" if st.session_state.user_profile else "ml_dashboard"
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

# Universal Sidebar Navigation and Profile Display
def show_sidebar_content():
    """Show navigation and full profile in sidebar for all pages when user is logged in"""
    if st.session_state.user:
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            
            if st.button("📊 Performance Predictor", use_container_width=True):
                st.session_state.page = "ml_dashboard"
                st.rerun()
                
            if st.button("🎯 Life Vision", use_container_width=True):
                st.session_state.page = "life_vision"
                st.rerun()
                
            if st.button("📋 Challenge Rules", use_container_width=True):
                st.session_state.page = "challenge_rules"
                st.rerun()
            
            if st.session_state.user_profile:
                if st.button("✅ Daily Challenge", use_container_width=True):
                    st.session_state.page = "daily_challenge"
                    st.rerun()
            
            if not st.session_state.user_profile:
                if st.button("⚙️ Setup Profile", use_container_width=True):
                    st.session_state.page = "setup_profile"
                    st.rerun()
            
            st.markdown("---")
            
            st.markdown("### 👤 My Profile")
            st.write(f"**Username:** {st.session_state.user['username']}")
            st.write(f"**Email:** {st.session_state.user['email']}")
            
            if st.session_state.user_profile:
                st.markdown("---")
                st.markdown("### 🎯 My Goals")
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
                    st.markdown("### 📈 My Progress")
                    st.write(f"**Current Day:** {st.session_state.challenge_data.get('current_day', 1)}")
                    st.write(f"**Streak Days:** {st.session_state.challenge_data.get('streak_days', 0)}")
                    st.write(f"**Total Savings:** ${st.session_state.challenge_data.get('total_savings', 0)}")
                    st.write(f"**Completed Days:** {st.session_state.challenge_data.get('completed_days', 0)}")
                
                if st.session_state.challenge_data.get('badges'):
                    st.markdown("---")
                    st.markdown("### 🏆 My Badges")
                    for badge in st.session_state.challenge_data['badges']:
                        st.success(f"{badge}")
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.user_profile = {}
                st.session_state.challenge_data = {}
                st.session_state.page = "signin"
                st.session_state.prediction_results = None
                st.session_state.show_stage_completion = False
                st.session_state.form_submitted = False
                st.session_state.show_motivational_task = False
                clear_persistent_login()
                st.rerun()

# Enhanced Authentication Pages
def sign_in_page():
    st.markdown("<h1 style='text-align: center;'>🧠 The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Secure Sign In</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            
            st.markdown("""
            <div style='background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 12px 0;'>
            <small>🔐 Password must contain:</small><br>
            <small>• 8+ characters with uppercase & lowercase</small><br>
            <small>• Numbers and special characters</small>
            </div>
            """, unsafe_allow_html=True)
            
            login_button = st.form_submit_button("🚀 Sign In")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if login_button:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("🔐 Signing in securely..."):
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
                                    else:
                                        st.session_state.user_profile = {}
                                    st.session_state.challenge_data = load_challenge_data(username_clean)
                                    set_persistent_login(username_clean)
                                    st.success("✅ Login successful!")
                                    st.session_state.page = "daily_challenge" if st.session_state.user_profile else "ml_dashboard"
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid username or password")
                            else:
                                st.error("❌ Invalid username or password")
                        except Exception as e:
                            st.error("🔒 Login failed. Please try again.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("🔑 Forgot Password", use_container_width=True, on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        with col2:
            st.button("📝 Create Account", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signup"}))

def forgot_password_page():
    st.markdown("<h2 style='text-align: center;'>🔑 Secure Password Reset</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("forgot_form"):
            st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
            email = st.text_input("📧 Enter your registered email")
            submit_btn = st.form_submit_button("🔄 Send Reset Link")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if submit_btn:
                if not email:
                    st.error("Please enter your email")
                else:
                    email_clean = sanitize_input(email)
                    with st.spinner("🔄 Sending secure reset link..."):
                        time.sleep(1)
                        
                        username, user_info = get_user_by_email(email_clean)
                        if user_info:
                            success, reset_link = generate_password_reset_token(email_clean)
                            if success:
                                email_success, message = send_password_reset_email(email_clean, reset_link)
                                if email_success:
                                    st.success("✅ Password reset link sent to your email!")
                                    st.info("📧 Check your inbox for the secure reset link (expires in 1 hour)")
                                else:
                                    st.error("❌ Failed to send email")
                            else:
                                st.error("❌ Failed to generate reset link")
                        else:
                            st.info("ℹ️ If this email exists, a reset link will be sent")
        
        st.button("← Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

def sign_up_page():
    st.markdown("<h1 style='text-align: center;'>🧠 The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create Secure Account</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("signup_form"):
            st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
            username = st.text_input("👤 Username")
            email = st.text_input("📧 Email")
            password = st.text_input("🔒 Password", type="password")
            password2 = st.text_input("✅ Confirm Password", type="password")
            
            # Password strength indicator
            if password:
                strength, message = validate_password(password)
                if strength:
                    st.success("✅ " + message)
                else:
                    st.error("❌ " + message)
            
            signup_btn = st.form_submit_button("🚀 Create Account")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if signup_btn:
                if not all([username, email, password, password2]):
                    st.error("Please fill in all fields")
                elif password != password2:
                    st.error("Passwords do not match")
                elif not validate_password(password)[0]:
                    st.error("Password does not meet security requirements")
                else:
                    with st.spinner("🔐 Creating secure account..."):
                        time.sleep(1)
                        
                        username_clean = sanitize_input(username)
                        email_clean = sanitize_input(email)
                        password_clean = sanitize_input(password)
                        
                        try:
                            if db.collection('users').document(username_clean).get().exists:
                                st.error("❌ Username already exists")
                            else:
                                existing_user, _ = get_user_by_email(email_clean)
                                if existing_user:
                                    st.error("❌ Email already registered")
                                else:
                                    hashed_password = hash_password(password_clean)
                                    user_data = {
                                        "email": email_clean,
                                        "password": hashed_password,
                                        "role": "student",
                                        "created_at": firestore.SERVER_TIMESTAMP
                                    }
                                    db.collection('users').document(username_clean).set(user_data)
                                    st.success("✅ Account created successfully!")
                                    st.session_state.page = "signin"
                                    st.rerun()
                        except Exception as e:
                            st.error("❌ Registration failed. Please try again.")
        
        st.button("← Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

# ... (Keep all your existing pages ML_DASHBOARD, LIFE_VISION, CHALLENGE_RULES, SETUP_PROFILE exactly as they were)

# Enhanced Daily Challenge Page with Better Savings UI
def daily_challenge_page():
    if "user" not in st.session_state or st.session_state.user is None:
        st.session_state.page = "signin"
        clear_persistent_login()
        st.rerun()
        return
    
    show_sidebar_content()
    
    if st.session_state.show_stage_completion:
        stage_completion_popup()
        return
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>✅ Daily Challenge Tracker</h1>", unsafe_allow_html=True)
    
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
    
    # Progress metrics in modern containers
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
        st.metric("🎯 Current Stage", current_stage)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
        st.metric("📅 Days Left", days_left)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
        st.metric("🔥 Streak Days", f"{streak_days} days")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
        st.metric("💰 Total Savings", f"${total_savings}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Stage completion check
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
    
    if st.session_state.form_submitted:
        st.success("✅ Today's progress saved successfully!")
        st.session_state.form_submitted = False
    
    # Enhanced Daily Tasks Form
    st.markdown(f"### 📝 Today's Tasks - Day {current_day}")
    st.markdown(f"**Stage:** {current_stage}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = get_stage_tasks(current_stage)
    
    with st.form("daily_tasks_form", clear_on_submit=True):
        st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
        completed_tasks = []
        
        st.markdown("#### ✅ Complete Your Daily Tasks:")
        for task in tasks:
            if st.checkbox(task, key=f"task_{task}"):
                completed_tasks.append(task)
        
        st.markdown("---")
        
        # Enhanced Savings Section with Visual Impact
        missed_tasks = len(tasks) - len(completed_tasks)
        
        if missed_tasks > 0:
            if missed_tasks == 1:
                st.markdown("<div class='penalty-container'>", unsafe_allow_html=True)
                st.warning("⚠️ You missed 1 task today!")
                st.info("According to rules: You need to pay your daily penalty to count this day toward your streak.")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='penalty-container'>", unsafe_allow_html=True)
                st.error("🚨 You missed multiple tasks!")
                st.warning("According to rules: Missing 2+ tasks means this day won't count, even with penalty.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='reward-container'>", unsafe_allow_html=True)
            st.success("🎉 Perfect day! All tasks completed!")
            st.info("You can still add to your savings for your future project!")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("#### 💰 Savings & Accountability")
        savings_amount = st.number_input(
            "Amount to add to savings today ($)",
            min_value=0.0,
            step=1.0,
            key="savings_amount",
            help="Add to your project fund. Required if you missed 1 task."
        )
        
        if savings_amount > 0:
            st.info(f"💳 You're adding **${savings_amount}** to your project fund")
        
        submit_btn = st.form_submit_button("🚀 Submit Today's Progress")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if submit_btn:
            process_enhanced_daily_submission(completed_tasks, savings_amount, today, tasks)
    
    # Motivational task
    if st.session_state.show_motivational_task:
        st.markdown("---")
        st.markdown("<div class='reward-container'>", unsafe_allow_html=True)
        st.success("🎯 Your final task for today:")
        st.markdown("**Go to Google, find a motivational image and set it as your wallpaper.**")
        st.markdown("*When you wake up tomorrow, you'll see your mission first thing!*")
        st.markdown("</div>", unsafe_allow_html=True)
        time.sleep(10)
        st.session_state.show_motivational_task = False
        st.rerun()
    
    # Enhanced Savings Display
    if challenge_data.get('total_savings', 0) > 0:
        st.markdown("---")
        st.markdown("<div class='modern-container'>", unsafe_allow_html=True)
        st.markdown("### 💰 Your Challenge Savings")
        
        # Visual savings progress
        savings_goal = 1000  # Example goal
        savings_progress = min(challenge_data['total_savings'] / savings_goal, 1.0)
        
        st.metric("Total Savings", f"${challenge_data['total_savings']}")
        st.progress(savings_progress)
        st.caption(f"Progress toward $1,000 project fund: {savings_progress*100:.1f}%")
        
        st.markdown("""
        💡 **Remember**: This money is for:
        - Launching your dream project
        - Investing in your field  
        - Building your future
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("← Back to Predictor", use_container_width=True, on_click=lambda: st.session_state.update({"page":"ml_dashboard"}))

def process_enhanced_daily_submission(completed_tasks, savings_amount, today, tasks):
    """Enhanced daily submission with savings service integration"""
    user = st.session_state.user
    challenge_data = st.session_state.challenge_data
    
    missed_tasks = len(tasks) - len(completed_tasks)
    
    # Always show motivational task
    st.session_state.show_motivational_task = True
    
    if missed_tasks == 0:
        # Perfect day - process savings if any
        if savings_amount > 0:
            success, transaction, message = SavingsService.process_savings_transaction(
                user['username'], savings_amount, "Voluntary savings - Perfect day"
            )
            if success:
                st.balloons()
                st.success(f"💰 {message}")
        
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
        
    elif missed_tasks == 1:
        if savings_amount > 0:
            # Process penalty payment
            success, transaction, message = SavingsService.process_savings_transaction(
                user['username'], savings_amount, f"Penalty payment - Missed 1 task: {set(tasks) - set(completed_tasks)}"
            )
            
            if success:
                st.success(f"✅ {message}")
                
                challenge_data['streak_days'] += 1
                challenge_data['completed_days'] += 1
                challenge_data['current_day'] += 1
                challenge_data['total_savings'] += savings_amount
                
                # Save transaction details
                if 'savings_transactions' not in challenge_data:
                    challenge_data['savings_transactions'] = []
                challenge_data['savings_transactions'].append(transaction)
                
                penalty_record = {
                    'date': today,
                    'amount': savings_amount,
                    'missed_tasks': 1,
                    'reason': f"Missed 1 task: {set(tasks) - set(completed_tasks)}",
                    'transaction_id': transaction.get('transaction_id')
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
                    'penalty_paid': True,
                    'transaction_id': transaction.get('transaction_id')
                }
                
                save_challenge_data(user['username'], challenge_data)
                st.session_state.challenge_data = challenge_data
                st.session_state.form_submitted = True
                
                st.warning(f"⚠️ You missed 1 task but paid ${savings_amount} penalty. Day counted! 🔥 Streak: {challenge_data['streak_days']} days")
            else:
                st.error(f"❌ {message}")
        else:
            st.error("💳 According to rules: You missed 1 task but didn't pay penalty. This day doesn't count toward your progress.")
            
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
            st.session_state.form_submitted = True
            
    else:
        st.error(f"🚨 According to rules: You missed {missed_tasks} tasks. This day doesn't count even if you pay penalty.")
        
        if 'daily_checkins' not in challenge_data:
            challenge_data['daily_checkins'] = {}
        challenge_data['daily_checkins'][today] = {
            'tasks_completed': completed_tasks,
            'missed_tasks': missed_tasks,
            'savings_added': savings_amount,
            'perfect_day': False,
            'day_not_counted': True
        }
        save_challenge_data(user['username'], challenge_data)
        st.session_state.challenge_data = challenge_data
        st.session_state.form_submitted = True
    
    st.rerun()

# Keep all your existing functions (stage_completion_popup, etc.) exactly as they were
# ... [Your existing stage_completion_popup and other functions remain unchanged]

# Main app routing (unchanged)
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
