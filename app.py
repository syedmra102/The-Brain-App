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

# --- GLOBAL CONFIGURATION AND CONSTANTS ---
# Define Stage Rules for easier check-in logic and profile setup
STAGE_RULES = {
    "Silver (15 Days - Easy)": {
        "days": 15,
        "min_hours": 2.0,
        "max_distractions": 0,
        "min_pushups": 0,
        "water_required": False,
        "junk_food_avoided": False,
        "sugar_avoided": False,
        "wakeup_early": False,
        "sleep_early": False
    },
    "Platinum (30 Days - Medium)": {
        "days": 30,
        "min_hours": 4.0,
        "max_distractions": 0,
        "min_pushups": 30,
        "water_required": True,
        "junk_food_avoided": True,
        "sugar_avoided": False,
        "wakeup_early": False,
        "sleep_early": False
    },
    "Gold (60 Days - Hard)": {
        "days": 60,
        "min_hours": 6.0,
        "max_distractions": 0,
        "min_pushups": 50, # Using the highest number from the rule list
        "water_required": True,
        "junk_food_avoided": True,
        "sugar_avoided": True,
        "wakeup_early": True, # Before 7 AM
        "sleep_early": True # Before 11 PM
    }
}

# Page config
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# Initialize session state for persistence - CHECK COOKIES FIRST
if 'user' not in st.session_state:
    # Try to get user from query params (persistent login)
    query_params = st.experimental_get_query_params()
    if 'username' in query_params and 'logged_in' in query_params:
        username = query_params['username'][0]
        # Verify user still exists in database
        try:
            user_doc = db.collection('users').document(username).get()
            if user_doc.exists:
                user_info = user_doc.to_dict()
                st.session_state.user = {
                    "username": username,
                    "email": user_info.get("email", ""),
                    "role": user_info.get("role", "student")
                }
                # Load user profile
                profile_doc = db.collection('user_profiles').document(username).get()
                if profile_doc.exists:
                    st.session_state.user_profile = profile_doc.to_dict()
                
                # Load challenge data
                st.session_state.challenge_data = load_challenge_data(username)
                
                # Set appropriate page
                if st.session_state.user_profile:
                    st.session_state.page = "daily_challenge"
                else:
                    st.session_state.page = "ml_dashboard"
            else:
                st.session_state.user = None
                st.session_state.page = "signin"
        except:
            st.session_state.user = None
            st.session_state.page = "signin"
    else:
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

def set_persistent_login(username):
    """Set persistent login using query parameters"""
    st.experimental_set_query_params(
        username=username,
        logged_in="true"
    )

def clear_persistent_login():
    """Clear persistent login"""
    st.experimental_set_query_params()

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
        # st.error("Prediction error occurred")
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
            # If habit is 'Yes' (1), compare to others who also said 'Yes'
            habit_percentile = (df[col] == 1).mean() * 100
            feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
        else:
            # If habit is 'No' (0), use the average percentage who said 'No' as a low baseline
            habit_percentile = (df[col] == 0).mean() * 100
            feature_percentiles[friendly_name] = max(1, habit_percentile)
    
    return feature_percentiles

# Challenge Functions
# Note: get_stage_days and get_stage_tasks are now redundant, but kept for legacy/rule display.
def get_stage_days(stage):
    return STAGE_RULES.get(stage, {}).get("days", 15)

def get_stage_tasks(stage):
    # This function is now used only for displaying text in the challenge page
    tasks = []
    rules = STAGE_RULES.get(stage)
    if not rules: return []

    tasks.append(f"Do {rules['min_hours']:.1f} hours of work in your field")
    tasks.append("Achieve zero distractions today")
    if rules['min_pushups'] > 0:
        tasks.append(f"Do {rules['min_pushups']} pushups exercise")
    if rules['water_required']:
        tasks.append("Drink 5 liters of water")
    if rules['junk_food_avoided']:
        tasks.append("Avoid junk food")
    if rules['sugar_avoided']:
        tasks.append("Avoid sugar")
    if rules['wakeup_early']:
        tasks.append("Wake up before 7 AM")
    if rules['sleep_early']:
        tasks.append("Sleep before 11 PM")
    tasks.append("Fill daily routine form (Check-in)")
    
    return tasks

def load_challenge_data(username):
    try:
        doc_ref = db.collection('challenge_progress').document(username)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            # Convert Firestore Timestamps/dates back to datetime objects if necessary for internal logic
            data['start_date'] = data['start_date'] if isinstance(data['start_date'], datetime) else data['start_date'].to_pydatetime()
            data['daily_checkins'] = {k: {key: val.to_pydatetime() if hasattr(val, 'to_pydatetime') else val for key, val in v.items()} for k, v in data.get('daily_checkins', {}).items()}
            return data
        else:
            # Initialize challenge data
            initial_data = {
                'current_stage': '', # Will be set during setup_profile
                'start_date': datetime.now(),
                'current_day': 1,
                'streak_days': 0,
                'total_savings': 0.0, # Use float for money
                'completed_days': 0,
                'penalty_history': [],
                'daily_checkins': {},
                'badges': []
            }
            return initial_data
    except Exception as e:
        st.error(f"Error loading challenge data: {e}")
        return {}

def save_challenge_data(username, data):
    try:
        # Convert datetime objects to Firestore-compatible format before saving
        data_to_save = data.copy()
        # Keep datetimes, Firestore handles them correctly.
        db.collection('challenge_progress').document(username).set(data_to_save)
        return True
    except Exception as e:
        st.error(f"Error saving challenge data: {e}")
        return False

# Universal Sidebar Navigation and Profile Display
def show_sidebar_content():
    """Show navigation and full profile in sidebar for all pages when user is logged in"""
    if st.session_state.user:
        with st.sidebar:
            st.markdown("### Navigation")
            
            # Always show these main pages
            if st.button("Performance Predictor", use_container_width=True):
                st.session_state.page = "ml_dashboard"
                st.rerun()
                
            if st.button("Life Vision", use_container_width=True):
                st.session_state.page = "life_vision"
                st.rerun()
                
            if st.button("Challenge Rules", use_container_width=True):
                st.session_state.page = "challenge_rules"
                st.rerun()
                
            # Only show Daily Challenge if profile exists AND a stage is selected
            if st.session_state.user_profile and st.session_state.user_profile.get('stage'):
                if st.button("Daily Challenge", use_container_width=True):
                    st.session_state.page = "daily_challenge"
                    st.rerun()
            
            # Only show Setup Profile if no profile exists OR stage is missing
            if not st.session_state.user_profile or not st.session_state.user_profile.get('stage'):
                if st.button("Setup Profile", use_container_width=True):
                    st.session_state.page = "setup_profile"
                    st.rerun()
            
            st.markdown("---")
            
            # Show complete user profile
            st.markdown("### My Profile")
            st.write(f"**Username:** {st.session_state.user['username']}")
            st.write(f"**Email:** {st.session_state.user['email']}")
            
            if st.session_state.user_profile:
                st.markdown("---")
                st.markdown("### My Goals")
                st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
                st.write(f"**I want to become:** {st.session_state.user_profile.get('goal', 'Not set')}")
                
                current_stage = st.session_state.user_profile.get('stage', 'Not set')
                st.write(f"**Current Stage:** **{current_stage}**")
                
                distractions = st.session_state.user_profile.get('distractions', [])
                if distractions:
                    st.write(f"**My Distractions:** {', '.join(distractions)}")
                else:
                    st.write("**My Distractions:** None selected")
                
                # Show challenge progress
                if st.session_state.challenge_data:
                    st.markdown("---")
                    st.markdown("### My Progress")
                    st.write(f"**Challenge Start:** {st.session_state.challenge_data.get('start_date', datetime.now()).strftime('%Y-%m-%d')}")
                    st.write(f"**Current Day:** {st.session_state.challenge_data.get('current_day', 1)}")
                    st.write(f"**Streak Days:** {st.session_state.challenge_data.get('streak_days', 0)}")
                    st.write(f"**Completed Days:** {st.session_state.challenge_data.get('completed_days', 0)} / {STAGE_RULES.get(current_stage, {}).get('days', '?')}")
                    st.markdown(f"**Total Savings (Penalty Fund):** <span style='color:#10B981; font-weight:bold;'>${st.session_state.challenge_data.get('total_savings', 0.0):.2f}</span>", unsafe_allow_html=True)
                
                # Show badges if any
                if st.session_state.challenge_data.get('badges'):
                    st.markdown("---")
                    st.markdown("### My Badges")
                    for badge in st.session_state.challenge_data['badges']:
                        st.success(f"🏅 {badge}")
            
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.user_profile = {}
                st.session_state.challenge_data = {}
                st.session_state.page = "signin"
                clear_persistent_login()
                st.rerun()

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
                                    
                                    # Set persistent login
                                    set_persistent_login(username_clean)
                                    
                                    st.success("Login successful")
                                    
                                    # Redirect to appropriate page based on profile completion
                                    if st.session_state.user_profile and st.session_state.user_profile.get('stage'):
                                        st.session_state.page = "daily_challenge"
                                    else:
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
    
    # Show sidebar navigation and profile
    show_sidebar_content()
    
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
                
                habits = {}
                # The model requires encoded categorical columns
                # The ML model expects 'avoid_sugar', 'avoid_junk_food', 'drink_5L_water', 'sleep_early', 'exercise_daily', 'wakeup_early'
                
                # Map selectbox values to model column names and ensure encoding is 1 or 0
                habit_inputs = {
                    'avoid_sugar': 1 if avoid_sugar == "Yes" else 0,
                    'avoid_junk_food': 1 if avoid_junk_food == "Yes" else 0,
                    'drink_5L_water': 1 if drink_5L_water == "Yes" else 0,
                    'sleep_early': 1 if sleep_early == "Yes" else 0,
                    'exercise_daily': 1 if exercise_daily == "Yes" else 0,
                    'wakeup_early': 1 if wakeup_early == "Yes" else 0
                }
                
                # Use the original model encoder which maps 'Yes' to 1 and 'No' to 0 for consistency
                for col in model_data['categorical_columns']:
                    value = "Yes" if habit_inputs[col] == 1 else "No"
                    habits[col] = model_data['encoders'][col].transform([value])[0]
                
                percentile = predict_performance(hours, distraction_count, habits)
                feature_percentiles = calculate_feature_percentiles(hours, distraction_count, habit_inputs)
                
                st.session_state.prediction_results = {
                    'percentile': percentile,
                    'feature_percentiles': feature_percentiles
                }
                st.rerun()
    
    # SHOW RESULTS OUTSIDE FORM
    if st.session_state.prediction_results is not None:
        results = st.session_state.prediction_results
        percentile = results['percentile']
        feature_percentiles = results['feature_percentiles']
        
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; color: #7C3AED;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
        
        # DARK BLUE CHART
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
    
    # 105 Days Challenge Section - More Prominent
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>105 Days to Top 1% Challenge</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 2px solid #7C3AED;'>
    <h3 style='text-align: center; color: #7C3AED;'>Transform Your Life Completely!</h3>
    <p style='text-align: center; font-weight: bold; font-size: 18px;'>
    This is your only opportunity to become top 1% in the world and in your field. 
    Join the challenge that will change everything!
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Attractive Join Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Join 105-Day Transformation Challenge", use_container_width=True, type="primary"):
            if st.session_state.user_profile:
                st.session_state.page = "daily_challenge"
            else:
                st.session_state.page = "setup_profile"
            st.rerun()

# LIFE VISION PAGE
def life_vision_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    # Show sidebar navigation and profile
    show_sidebar_content()
    
    # MAIN CONTENT
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>After This Challenge How Your Life Is Looking</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detailed Vision Content
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
    
    # Back button at bottom
    st.markdown("---")
    if st.button("Back to Predictor", use_container_width=True):
        st.session_state.page = "ml_dashboard"
        st.rerun()

# CHALLENGE RULES PAGE
def challenge_rules_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    # Show sidebar navigation and profile
    show_sidebar_content()
    
    # MAIN CONTENT
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>105 Days Transformation Challenge Rules</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Challenge Rules Content
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Silver Stage (15 Days - Easy)</h2>", unsafe_allow_html=True)
    st.markdown("""
    1. Do **2 hours** of work in your field daily
    2. **Zero distractions** today (no unnecessary phone/social media usage)
    3. Fill your daily routine form at this website at night
    """)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Platinum Stage (30 Days - Medium)</h2>", unsafe_allow_html=True)
    st.markdown("""
    1. Do **4 hours** of work in your field daily
    2. **Zero distractions** today
    3. Do **30 pushups** exercise daily
    4. Drink **5 liters** of water daily
    5. **Avoid junk food**
    6. Fill your daily routine form at this website at night
    """)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Gold Stage (60 Days - Hard but Last)</h2>", unsafe_allow_html=True)
    st.markdown("""
    1. Do **6 hours** of work in your field daily
    2. **Zero distractions** today
    3. Do **50 pushups** exercise daily (combines and supersedes the 30 pushups rule)
    4. Drink **5 liters** of water daily
    5. **Avoid junk food**
    6. **Avoid sugar**
    7. **Wake up before 7 AM**
    8. **Sleep before 11 PM**
    9. Fill your daily routine form at this website at night
    """)
    
    st.markdown("---")
    
    st.markdown("<h2 style='text-align: center; color: #7C3AED;'>Penalty Rules</h2>", unsafe_allow_html=True)
    st.markdown("""
    If you miss **one rule** any day at any stage you have to pay that day whole pocket money or any money that you earn that day and put on savings. This penalty **redeems** the day, and your streak continues.

    But if you miss **2 or more habits** at any stage, the day **does not count** (current day stalled), you still pay the penalty, and your **streak is reset to 0**. You must do all the things tomorrow.
    """)
    
    st.markdown("---")
    
    st.markdown("<p style='text-align: center; font-weight: bold; font-size: 20px;'>This is your only opportunity to transform your life and become top 1%</p>", unsafe_allow_html=True)
    
    # Back button at bottom
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start My Transformation Now!", use_container_width=True, type="primary"):
            if st.session_state.user_profile and st.session_state.user_profile.get('stage'):
                st.session_state.page = "daily_challenge"
            else:
                st.session_state.page = "setup_profile"
            st.rerun()

# --- NEW PAGE LOGIC ---

# SETUP PROFILE PAGE
def setup_profile_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return

    show_sidebar_content()

    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Start Your 105-Day Transformation</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Complete your profile to begin the challenge.</h3>", unsafe_allow_html=True)

    username = st.session_state.user['username']

    # Use the form to collect profile and starting challenge data
    with st.form("profile_setup_form"):
        st.subheader("Your Vision")
        field = st.text_input("Your Field of Study/Work (e.g., Software Engineering, Finance)", value=st.session_state.user_profile.get('field', ''))
        goal = st.text_area("Your 105-Day Transformation Goal (e.g., Become a Top 1% Developer)", value=st.session_state.user_profile.get('goal', ''))

        st.subheader("Your Challenge Settings")
        
        # Collect distractions
        DISTRACTION_OPTIONS = ["Social Media", "Video Games", "TV/Movies", "Mindless Browsing", "Junk Food/Snacking", "Excessive Sleep"]
        distractions = st.multiselect(
            "What are your biggest time-wasting distractions? (Select all that apply)",
            options=DISTRACTION_OPTIONS,
            default=st.session_state.user_profile.get('distractions', [])
        )

        # Select starting stage
        stages = list(STAGE_RULES.keys())
        initial_stage = st.selectbox(
            "Select Your Starting Challenge Stage",
            options=stages,
            index=stages.index(st.session_state.user_profile.get('stage')) if st.session_state.user_profile.get('stage') in stages else 0,
            help="Silver is the easiest start, Gold is the full 105-day commitment."
        )

        submit_btn = st.form_submit_button("Start Challenge!")

        if submit_btn:
            if not field or not goal or not initial_stage:
                st.error("Please fill in your field, goal, and select a stage.")
            else:
                with st.spinner("Saving profile and initializing challenge..."):
                    
                    # 1. Save/Update User Profile
                    new_profile = {
                        'field': sanitize_input(field),
                        'goal': sanitize_input(goal),
                        'distractions': distractions,
                        'stage': initial_stage
                    }
                    db.collection('user_profiles').document(username).set(new_profile)
                    st.session_state.user_profile = new_profile

                    # 2. Initialize/Update Challenge Data
                    challenge_data = st.session_state.challenge_data.copy()
                    
                    # Only reset challenge data if the stage is being changed or it's brand new
                    if challenge_data.get('current_stage') != initial_stage or not challenge_data.get('current_stage'):
                        challenge_data = {
                            'current_stage': initial_stage,
                            'start_date': datetime.now(),
                            'current_day': 1,
                            'streak_days': 0,
                            'total_savings': 0.0,
                            'completed_days': 0,
                            'penalty_history': [],
                            'daily_checkins': {},
                            'badges': []
                        }
                    
                    save_challenge_data(username, challenge_data)
                    st.session_state.challenge_data = challenge_data
                    
                    st.success(f"Profile saved! Starting {initial_stage} challenge on Day 1.")
                    st.session_state.page = "daily_challenge"
                    st.rerun()

# DAILY CHALLENGE PAGE
def daily_challenge_page():
    if not st.session_state.user or not st.session_state.user_profile.get('stage'):
        st.session_state.page = "setup_profile"
        st.rerun()
        return

    show_sidebar_content()

    username = st.session_state.user['username']
    profile = st.session_state.user_profile
    challenge = st.session_state.challenge_data
    
    current_stage = challenge.get('current_stage', 'Silver (15 Days - Easy)')
    stage_rules = STAGE_RULES[current_stage]
    current_day = challenge.get('current_day', 1)
    
    st.markdown(f"<h1 style='text-align: center; color: #7C3AED;'>🔥 Daily Transformation: {current_stage}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>Day **{current_day}** of **{stage_rules['days']}** | Streak: **{challenge.get('streak_days', 0)}**</h2>", unsafe_allow_html=True)
    
    # Check if user has already checked in today
    today_date_str = datetime.now().strftime('%Y-%m-%d')
    already_checked_in = today_date_str in challenge.get('daily_checkins', {})
    
    if already_checked_in:
        st.success("✅ You have already completed your check-in for today! Come back tomorrow.")
        st.markdown("---")
    
    # Display Daily Tasks
    with st.expander("🎯 Your Required Tasks for Today (Must achieve all)", expanded=True):
        for task in get_stage_tasks(current_stage):
            st.markdown(f"- **{task}**")

    st.markdown("---")

    # Daily Routine Check-in Form
    if not already_checked_in:
        st.markdown("<h3>Daily Check-in Form (To be filled at night)</h3>", unsafe_allow_html=True)
        
        with st.form("daily_checkin_form"):
            
            col_a, col_b = st.columns(2)
            with col_a:
                actual_hours = st.number_input(f"1. Actual Focused Work Hours (Minimum {stage_rules['min_hours']}h)", min_value=0.0, max_value=24.0, value=stage_rules['min_hours'])
                actual_distractions = st.number_input(f"2. Count of Distractions (Maximum {stage_rules['max_distractions']})", min_value=0, max_value=30, value=0)
                pocket_money = st.number_input("3. Daily Pocket Money / Earnings (For Penalty Fund)", min_value=0.0, value=10.0)
                
            with col_b:
                # Exercise
                min_pushups = stage_rules['min_pushups']
                if min_pushups > 0:
                    did_exercise = st.number_input(f"4. Pushups Completed (Minimum {min_pushups})", min_value=0, value=min_pushups)
                else:
                    did_exercise = min_pushups # Set to 0 if not required
                
                # Lifestyle Habits
                drank_water = st.checkbox("5. Drank 5L of Water Today?", value=stage_rules['water_required'])
                had_junk_food = st.checkbox("6. Had Junk Food Today?", value=not stage_rules['junk_food_avoided'])
                had_sugar = st.checkbox("7. Had Sugar Today?", value=not stage_rules['sugar_avoided'])
                woke_up_early = st.checkbox("8. Woke Up Before 7 AM?", value=stage_rules['wakeup_early'])
                slept_early = st.checkbox("9. Slept Before 11 PM?", value=stage_rules['sleep_early'])

            submit_checkin = st.form_submit_button("Submit Daily Check-in")

            if submit_checkin:
                # --- CORE LOGIC: CHECK RULES AND APPLY PENALTIES ---
                missed_rules = []

                # Rule 1: Focused Hours
                if actual_hours < stage_rules['min_hours']:
                    missed_rules.append(f"Work Hours (Goal: {stage_rules['min_hours']}h, Actual: {actual_hours}h)")

                # Rule 2: Distractions
                if actual_distractions > stage_rules['max_distractions']:
                    missed_rules.append(f"Distractions (Goal: {stage_rules['max_distractions']}, Actual: {actual_distractions})")
                
                # Rule 3: Exercise
                if stage_rules['min_pushups'] > 0 and did_exercise < stage_rules['min_pushups']:
                    missed_rules.append(f"Pushups (Goal: {stage_rules['min_pushups']}, Actual: {did_exercise})")

                # Rule 4: Water
                if stage_rules['water_required'] and not drank_water:
                    missed_rules.append("5L Water Intake")

                # Rule 5: Junk Food
                if stage_rules['junk_food_avoided'] and had_junk_food:
                    missed_rules.append("Avoid Junk Food")

                # Rule 6: Sugar
                if stage_rules['sugar_avoided'] and had_sugar:
                    missed_rules.append("Avoid Sugar")

                # Rule 7: Wake Up Early
                if stage_rules['wakeup_early'] and not woke_up_early:
                    missed_rules.append("Wake Up Before 7 AM")

                # Rule 8: Sleep Early
                if stage_rules['sleep_early'] and not slept_early:
                    missed_rules.append("Sleep Before 11 PM")


                num_missed = len(missed_rules)
                
                # Update Challenge Data (always update total savings)
                challenge_data = challenge.copy()
                penalty_amount = 0.0
                is_day_counted = False
                
                if num_missed == 0:
                    # PERFECT DAY
                    st.balloons()
                    st.success(f"PERFECT DAY! Day {current_day} completed with zero misses.")
                    challenge_data['completed_days'] += 1
                    challenge_data['current_day'] += 1
                    challenge_data['streak_days'] += 1
                    is_day_counted = True
                    
                elif num_missed == 1:
                    # 1 MISS - REDEEMED BY PENALTY (Day Counts, Streak continues)
                    penalty_amount = pocket_money
                    st.warning(f"⚠️ Day {current_day} completed with 1 miss: {missed_rules[0]}. You must pay **${penalty_amount:.2f}** into your savings fund.")
                    challenge_data['completed_days'] += 1
                    challenge_data['current_day'] += 1
                    challenge_data['streak_days'] += 1
                    challenge_data['total_savings'] += penalty_amount
                    is_day_counted = True

                else: # num_missed >= 2
                    # 2+ MISSES - DAY FAILED (Day DOES NOT Count, Streak Resets)
                    penalty_amount = pocket_money
                    st.error(f"❌ MAJOR FAILURE! Day {current_day} did NOT count. You missed {num_missed} rules: {', '.join(missed_rules)}. You must pay **${penalty_amount:.2f}** and your streak is **RESET to 0**.")
                    challenge_data['streak_days'] = 0 # Streak reset
                    challenge_data['total_savings'] += penalty_amount
                    # Current day and completed days are NOT incremented

                # Record check-in history
                checkin_record = {
                    'timestamp': datetime.now(),
                    'day': current_day,
                    'missed_count': num_missed,
                    'missed_rules': missed_rules,
                    'penalty_paid': penalty_amount,
                    'is_day_counted': is_day_counted,
                    'hours': actual_hours,
                    'distractions': actual_distractions,
                    'money': pocket_money
                }
                challenge_data['daily_checkins'][today_date_str] = checkin_record
                challenge_data['penalty_history'].append(checkin_record)

                # Check for Stage Completion (only if day was counted)
                if is_day_counted and challenge_data['completed_days'] >= stage_rules['days']:
                    
                    next_stage = ""
                    if current_stage.startswith("Silver"):
                        next_stage = "Platinum (30 Days - Medium)"
                        badge = "Silver Conqueror Badge"
                    elif current_stage.startswith("Platinum"):
                        next_stage = "Gold (60 Days - Hard)"
                        badge = "Platinum Warrior Badge"
                    elif current_stage.startswith("Gold"):
                        next_stage = "Challenge Master"
                        badge = "105-Day Master Badge"
                        st.session_state.show_stage_completion = "COMPLETE"
                    
                    if next_stage and next_stage != "Challenge Master":
                        # Advance to next stage
                        challenge_data['current_stage'] = next_stage
                        challenge_data['start_date'] = datetime.now()
                        challenge_data['current_day'] = 1
                        challenge_data['completed_days'] = 0
                        
                        st.session_state.show_stage_completion = f"Stage Completed! Advancing to **{next_stage}**."
                        
                    if badge not in challenge_data['badges']:
                        challenge_data['badges'].append(badge)

                # Save Data and Rerun
                if save_challenge_data(username, challenge_data):
                    st.session_state.challenge_data = challenge_data
                    # Update profile stage if needed (for sidebar display)
                    if current_stage != challenge_data['current_stage']:
                        st.session_state.user_profile['stage'] = challenge_data['current_stage']
                        db.collection('user_profiles').document(username).set(st.session_state.user_profile)
                    st.rerun() # Rerun to display success/failure messages and prevent form resubmission

    # Motivational Section (Appears after check-in or if already checked in)
    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #7C3AED;'>Your Transformation Dashboard</h3>", unsafe_allow_html=True)
    
    col_c, col_d = st.columns(2)
    with col_c:
        st.metric("Total Days Completed in Stage", f"{challenge.get('completed_days', 0)} / {stage_rules['days']}")
    with col_d:
        st.markdown(f"**Total Penalty Savings:** <span style='color:#10B981; font-weight:bold; font-size: 24px;'>${challenge.get('total_savings', 0.0):.2f}</span>", unsafe_allow_html=True)
    
    # Stage Completion Message
    if st.session_state.show_stage_completion:
        if st.session_state.show_stage_completion == "COMPLETE":
            st.success("🏆 CONGRATULATIONS! You have completed the entire 105-Day Transformation Challenge! You are now in the Top 1%.")
            st.markdown(f"Use your **${challenge.get('total_savings', 0.0):.2f}** savings to fund your dream project!")
        else:
            st.success(st.session_state.show_stage_completion)
        st.session_state.show_stage_completion = False # Reset flag

    # Performance Comparison Chart (if data exists)
    if challenge.get('penalty_history'):
        st.markdown("---")
        st.subheader("Last 7 Days Performance Overview")
        
        history = pd.DataFrame(challenge['penalty_history'])
        history['date'] = history['timestamp'].apply(lambda x: x.strftime('%m-%d'))
        
        last_7_days = history.tail(7).sort_values(by='timestamp')
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(last_7_days['date'], last_7_days['missed_count'], marker='o', linestyle='-', color='#F59E0B', label='Missed Rules')
        
        ax.axhline(y=0, color='green', linestyle='--', linewidth=1, label='Perfect Day')
        ax.axhline(y=1, color='orange', linestyle='--', linewidth=1, label='Penalty Day')
        ax.axhline(y=2, color='red', linestyle='--', linewidth=1, label='Failed Day')
        
        ax.set_title("Daily Compliance (Missed Rules Count)")
        ax.set_xlabel("Day")
        ax.set_ylabel("Rules Missed")
        ax.set_ylim(-0.5, last_7_days['missed_count'].max() + 1)
        ax.legend()
        st.pyplot(fig)


# --- MAIN APPLICATION ROUTER ---

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
