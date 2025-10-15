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

def send_password_reset_email(to_email, reset_link):
    """
    Send a password reset email containing a secure reset link.
    """
    try:
        # Safely get email credentials from secrets
        email_config = st.secrets.get("email", {})
        email_address = email_config.get("EMAIL_ADDRESS", "")
        email_password = email_config.get("EMAIL_PASSWORD", "")
        
        if not email_address or not email_password:
            return False, "Email service not configured. Please contact support."
            
        msg = EmailMessage()
        msg['Subject'] = 'Your Brain App - Password Reset'
        msg['From'] = email_address
        msg['To'] = to_email
        msg.set_content(f"""
Hello,

You requested a password reset for your Brain App account.

Click the link below to reset your password:

{reset_link}

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
    """Set persistent login using query parameters"""
    try:
        st.query_params["username"] = username
        st.query_params["logged_in"] = "true"
    except Exception as e:
        pass  # Silently fail if query params not available

def clear_persistent_login():
    """Clear persistent login"""
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

# Twilio SMS Reminders Function
def send_sms_reminder(phone_number, message):
    """
    Send SMS reminder using Twilio
    """
    try:
        # Safely get Twilio credentials
        twilio_config = st.secrets.get("twilio", {})
        twilio_account_sid = twilio_config.get("ACCOUNT_SID", "")
        twilio_auth_token = twilio_config.get("AUTH_TOKEN", "")
        twilio_phone_number = twilio_config.get("PHONE_NUMBER", "")
        
        if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
            return False, "SMS service not configured"
        
        # Try to import Twilio
        try:
            from twilio.rest import Client
        except ImportError:
            return False, "Twilio package not available"
        
        client = Client(twilio_account_sid, twilio_auth_token)
        
        message = client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=phone_number
        )
        
        return True, "SMS reminder sent successfully"
    except Exception as e:
        return False, "SMS service not available"

# PDF Certificate Generation
def generate_certificate(username, user_profile, challenge_data):
    """
    Generate a PDF certificate for completed stages
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Add title
        pdf.set_font('Arial', 'B', 24)
        pdf.cell(0, 20, 'CERTIFICATE OF ACHIEVEMENT', 0, 1, 'C')
        pdf.ln(10)
        
        # Add user information
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, f'This certifies that', 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 22)
        pdf.cell(0, 10, f'{username}', 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'has successfully completed the', 0, 1, 'C')
        pdf.ln(5)
        
        # Add stage information
        current_stage = challenge_data.get('current_stage', 'Brain App Challenge')
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, f'{current_stage}', 0, 1, 'C')
        pdf.ln(10)
        
        # Add achievements
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f'Field: {user_profile.get("field", "Not specified")}', 0, 1, 'C')
        pdf.cell(0, 8, f'Goal: {user_profile.get("goal", "Not specified")}', 0, 1, 'C')
        pdf.cell(0, 8, f'Completed Days: {challenge_data.get("completed_days", 0)}', 0, 1, 'C')
        pdf.cell(0, 8, f'Total Savings: ${challenge_data.get("total_savings", 0)}', 0, 1, 'C')
        pdf.ln(10)
        
        # Add badges
        badges = challenge_data.get('badges', [])
        if badges:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Badges Earned:', 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            for badge in badges:
                pdf.cell(0, 8, f'• {badge}', 0, 1, 'C')
        
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'C')
        
        # Save to bytes buffer
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        return None

# Advanced Analytics Visualizations
def create_advanced_analytics(challenge_data, user_profile):
    """
    Create advanced analytics visualizations with different graph types
    """
    try:
        daily_checkins = challenge_data.get('daily_checkins', {})
        if not daily_checkins:
            st.info("Complete more days to see advanced analytics!")
            return
            
        # Prepare data for analytics
        dates = sorted(daily_checkins.keys())
        if not dates:
            st.info("No data available for analytics")
            return
            
        perfect_days = []
        penalty_days = []
        skipped_days = []
        daily_savings = []
        task_completion_rates = []
        
        for date in dates:
            checkin = daily_checkins[date]
            perfect_days.append(1 if checkin.get('perfect_day', False) else 0)
            penalty_days.append(1 if checkin.get('penalty_paid', False) else 0)
            skipped_days.append(1 if checkin.get('day_not_counted', False) else 0)
            daily_savings.append(checkin.get('savings_added', 0))
            
            # Calculate task completion rate
            completed = len(checkin.get('tasks_completed', []))
            total_tasks = completed + checkin.get('missed_tasks', 0)
            rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
            task_completion_rates.append(rate)
        
        # Create advanced analytics dashboard
        st.markdown("### Advanced Performance Analytics")
        
        # Row 1: Performance Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_days = len(dates)
            perfect_count = sum(perfect_days)
            st.metric("Perfect Days", f"{perfect_count}/{total_days}")
        
        with col2:
            completion_avg = np.mean(task_completion_rates) if task_completion_rates else 0
            st.metric("Avg Completion", f"{completion_avg:.1f}%")
        
        with col3:
            penalty_count = sum(penalty_days)
            st.metric("Penalty Days", penalty_count)
        
        with col4:
            total_savings = sum(daily_savings)
            st.metric("Total Savings", f"${total_savings}")
        
        # Row 2: Performance Distribution Pie Chart
        st.markdown("#### Performance Distribution")
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        
        labels = ['Perfect Days', 'Penalty Days', 'Skipped Days']
        sizes = [sum(perfect_days), sum(penalty_days), sum(skipped_days)]
        colors = ['seagreen', 'goldenrod', 'indianred']
        
        # Only show pie chart if we have data
        if sum(sizes) > 0:
            explode = (0.1, 0, 0)
            ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax1.axis('equal')
            ax1.set_title('Day Performance Distribution', fontweight='bold')
            st.pyplot(fig1)
        else:
            st.info("No performance data available for chart")
        
        # Row 3: Savings Over Time - Area Chart
        if len(dates) > 1:
            st.markdown("#### Savings Growth Over Time")
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            
            cumulative_savings = np.cumsum(daily_savings)
            ax2.fill_between(range(len(dates)), cumulative_savings, alpha=0.4, color='steelblue')
            ax2.plot(range(len(dates)), cumulative_savings, color='navy', linewidth=2, marker='o')
            ax2.set_xlabel('Days')
            ax2.set_ylabel('Total Savings ($)')
            ax2.set_title('Cumulative Savings Progress', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis
            if len(dates) > 10:
                step = max(1, len(dates)//10)
                ax2.set_xticks(range(0, len(dates), step))
                ax2.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45)
            else:
                ax2.set_xticks(range(len(dates)))
                ax2.set_xticklabels(dates, rotation=45)
            
            st.pyplot(fig2)
        
    except Exception as e:
        st.info("Analytics will be available after you complete more challenge days")

# Firebase setup with error handling
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
        st.error("Firebase configuration not found. Please check your secrets configuration.")
        st.stop()
except Exception as e:
    st.error("Database connection failed. Please try again later.")
    st.stop()

# Load ML Model from model.pkl with safe handling
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

# Initialize ML model
if not st.session_state.ml_model_loaded:
    model_data = load_ml_model()
else:
    model_data = None

# ML Prediction Function - SAFE VERSION
def predict_performance(hours, distraction_count, habits):
    try:
        if model_data is None:
            return 75.0  # Default value if model not available
            
        # Create input data with proper structure
        input_data = {}
        
        # Add numeric features
        input_data['hours'] = hours
        input_data['distraction_count'] = distraction_count
        
        # Add encoded categorical features
        for col, value in habits.items():
            input_data[col] = value
        
        # Convert to DataFrame
        input_df = pd.DataFrame([input_data])
        
        # Ensure all required columns are present
        required_columns = model_data.get('feature_columns', [])
        for col in required_columns:
            if col not in input_df.columns:
                input_df[col] = 0
        
        # Reorder columns to match training data
        input_df = input_df[required_columns]
        
        # Scale numeric features if scaler exists
        if 'scaler' in model_data:
            numeric_cols = model_data.get('numeric_columns', ['hours', 'distraction_count'])
            input_df[numeric_cols] = model_data['scaler'].transform(input_df[numeric_cols])
        
        # Make prediction
        prediction = model_data['model'].predict(input_df)[0]
        prediction = max(1, min(100, prediction))
        
        return prediction
        
    except Exception as e:
        return 75.0  # Safe default

def calculate_feature_percentiles(hours, distractions, habit_inputs):
    try:
        if model_data is None:
            # Return default percentiles if model not available
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
    except Exception as e:
        # Return default values if calculation fails
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

# Enhanced Sidebar with safe navigation
def show_sidebar_content():
    """Show navigation and full profile in sidebar for all pages when user is logged in"""
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
                
                # Analytics Page Button
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
            
            # SMS Reminders Section
            st.markdown("---")
            st.markdown("### SMS Reminders")
            phone_number = st.text_input("Phone Number", 
                                       value=st.session_state.phone_number,
                                       placeholder="+1234567890",
                                       key="phone_input")
            
            if phone_number != st.session_state.phone_number:
                st.session_state.phone_number = phone_number
            
            if phone_number and st.button("Test SMS", use_container_width=True):
                success, message = send_sms_reminder(phone_number, "Test reminder from The Brain App! You're doing great!")
                if success:
                    st.success("Test SMS sent!")
                else:
                    st.info("SMS service is not configured")
            
            # Certificate Download
            if st.session_state.challenge_data.get('badges'):
                st.markdown("---")
                st.markdown("### Certificates")
                if st.button("Download Progress Certificate", use_container_width=True):
                    st.session_state.page = "certificate"
                    st.rerun()
            
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.user_profile = {}
                st.session_state.challenge_data = {}
                st.session_state.page = "signin"
                st.session_state.prediction_results = None
                st.session_state.show_stage_completion = False
                st.session_state.form_submitted = False
                st.session_state.show_motivational_task = False
                st.session_state.phone_number = ""
                clear_persistent_login()
                st.rerun()

# Check for persistent login - FIXED VERSION
if st.session_state.user is None:
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
                if st.session_state.user_profile:
                    st.session_state.page = "life_vision"
                else:
                    st.session_state.page = "life_vision"
                set_persistent_login(username)
    except Exception as e:
        pass  # Silently handle any errors during persistent login

# SAFE ML Dashboard Page
def ml_dashboard_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>Performance Predictor</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: darkblue;'>Discover Your Top Percentile</h3>", unsafe_allow_html=True)
        
        if st.button("Back to Life Vision", use_container_width=False):
            st.session_state.page = "life_vision"
            st.rerun()
        
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
                    
                    # Safe encoding
                    habits = {}
                    categorical_mapping = {
                        'avoid_sugar': avoid_sugar,
                        'avoid_junk_food': avoid_junk_food,
                        'drink_5L_water': drink_5L_water,
                        'sleep_early': sleep_early,
                        'exercise_daily': exercise_daily,
                        'wakeup_early': wakeup_early
                    }
                    
                    for col, value in categorical_mapping.items():
                        habits[col] = 1 if value == "Yes" else 0
                    
                    percentile = predict_performance(hours, distraction_count, habits)
                    feature_percentiles = calculate_feature_percentiles(hours, distraction_count, habits)
                    
                    st.session_state.prediction_results = {
                        'percentile': percentile,
                        'feature_percentiles': feature_percentiles
                    }
                    st.rerun()
        
        if st.session_state.prediction_results is not None:
            results = st.session_state.prediction_results
            percentile = results['percentile']
            feature_percentiles = results['feature_percentiles']
            
            st.markdown("---")
            st.markdown(f"<h2 style='text-align: center; color: darkgreen;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            features = list(feature_percentiles.keys())
            percentiles = list(feature_percentiles.values())
            
            bars = ax.bar(features, percentiles, color='steelblue', edgecolor='navy', linewidth=1.5)
            ax.set_ylabel('Performance Percentile', fontweight='bold')
            ax.set_title('Performance Breakdown Analysis', fontweight='bold', fontsize=14)
            ax.set_ylim(0, 100)
            plt.xticks(rotation=45, ha='right', fontweight='bold')
            
            for bar, percentile_val in zip(bars, percentiles):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'Top {percentile_val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=9)
            
            ax.grid(True, alpha=0.3, color='gray')
            ax.set_facecolor('white')
            
            st.pyplot(fig)
        
        st.markdown("---")
        st.markdown("<h2 style='text-align: center; color: darkblue;'>105 Days to Top 1% Challenge</h2>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background-color: aliceblue; padding: 20px; border-radius: 10px; border: 2px solid darkblue;'>
        <h3 style='text-align: center; color: darkblue;'>Transform Your Life Completely!</h3>
        <p style='text-align: center; font-weight: bold; font-size: 18px;'>
        This is your only opportunity to become top 1% in the world and in your field.
        Join the challenge that will change everything!
        </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Join 105-Day Transformation Challenge", use_container_width=True, type="primary"):
                if st.session_state.user_profile:
                    st.session_state.page = "daily_challenge"
                else:
                    st.session_state.page = "setup_profile"
                st.rerun()
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

# SAFE Life Vision Page
def life_vision_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>After This Challenge How Your Life Is Looking</h1>", unsafe_allow_html=True)
        
        if st.button("Back to Predictor", use_container_width=False):
            st.session_state.page = "ml_dashboard"
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("<h2 style='text-align: center; color: darkblue;'>Your Life After Completing 105-Day Challenge</h2>", unsafe_allow_html=True)
        
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
        
        st.markdown("<p style='text-align: center; font-weight: bold; font-size: 20px; color: darkgreen;'>This transformation will make you unrecognizable to your current self</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Next: Challenge Rules", use_container_width=True):
                st.session_state.page = "challenge_rules"
                st.rerun()
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

# SAFE Challenge Rules Page
def challenge_rules_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>105 Days Transformation Challenge Rules</h1>", unsafe_allow_html=True)
        
        if st.button("Back to Life Vision", use_container_width=False):
            st.session_state.page = "life_vision"
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("<h2 style='text-align: center; color: darkblue;'>Silver Stage (15 Days - Easy)</h2>", unsafe_allow_html=True)
        st.markdown("""
        1. Do 2 hours of work in your field daily
        2. Don't do any distraction for just 15 days
        3. Fill your daily routine form at this website at night
        """)
        
        st.markdown("---")
        
        st.markdown("<h2 style='text-align: center; color: darkblue;'>Platinum Stage (30 Days - Medium)</h2>", unsafe_allow_html=True)
        st.markdown("""
        1. Do 4 hours of work in your field daily
        2. Don't do any distraction for just 30 days
        3. Do 30 pushups exercise daily
        4. Drink 5 liters of water daily
        5. Avoid junk food
        6. Fill your daily routine form at this website at night
        """)
        
        st.markdown("---")
        
        st.markdown("<h2 style='text-align: center; color: darkblue;'>Gold Stage (60 Days - Hard but Last)</h2>", unsafe_allow_html=True)
        st.markdown("""
        1. Do 6 hours of work in your field daily
        2. Don't do any distraction for just 60 days
        3. Do 50 pushups exercise daily
        4. Drink 5 liters of water daily
        5. Avoid junk food
        6. Avoid sugar
        7. Wake up before 7 AM
        8. Sleep before 11 PM
        9. Fill your daily routine form at this website at night
        """)
        
        st.markdown("---")
        
        st.markdown("<h2 style='text-align: center; color: darkblue;'>Penalty Rules</h2>", unsafe_allow_html=True)
        st.markdown("""
        If you miss one rule any day at any stage you have to pay that day whole pocket money or any money that you earn that day and put on savings.
        When you complete this challenge you use this money for making project on your field or invest that money in your field.
        But if you miss 2 or more habits at any stage we don't count that day even also you paying money and you have to do all of the things tomorrow.
        """)
        
        st.markdown("---")
        
        st.markdown("<p style='text-align: center; font-weight: bold; font-size: 20px; color: darkgreen;'>This is your only opportunity to transform your life and become top 1%</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.session_state.user_profile:
                if st.button("Next: Daily Challenge", use_container_width=True):
                    st.session_state.page = "daily_challenge"
                    st.rerun()
            else:
                if st.button("Next: Setup Profile", use_container_width=True):
                    st.session_state.page = "setup_profile"
                    st.rerun()
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

# SAFE Setup Profile Page
def setup_profile_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>Setup Your Challenge Profile</h1>", unsafe_allow_html=True)
        
        if st.button("Back to Challenge Rules", use_container_width=False):
            st.session_state.page = "challenge_rules"
            st.rerun()
        
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
            
            save_btn = st.form_submit_button("Save Profile & Start Challenge")
            
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
                            'created_at': firestore.SERVER_TIMESTAMP
                        }
                        
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
                        st.session_state.challenge_data = challenge_data
                        
                        try:
                            db.collection('user_profiles').document(st.session_state.user['username']).set(profile_data)
                            save_challenge_data(st.session_state.user['username'], challenge_data)
                            set_persistent_login(st.session_state.user['username'])
                            st.success("Profile saved successfully!")
                            st.info("Your profile is now visible in the sidebar. Your challenge begins now!")
                            time.sleep(2)
                            st.session_state.page = "daily_challenge"
                            st.rerun()
                        except Exception as e:
                            st.error("Failed to save profile. Please try again.")
        
        st.markdown("---")
        if st.button("Back to Challenge Rules", use_container_width=True):
            st.session_state.page = "challenge_rules"
            st.rerun()
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

# SAFE Edit Profile Page
def edit_profile_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>Edit Your Profile</h1>", unsafe_allow_html=True)
        
        if st.button("Back to Previous Page", use_container_width=False):
            st.session_state.page = "daily_challenge"
            st.rerun()
        
        st.markdown("---")
        
        with st.form("edit_profile_form"):
            st.subheader("Your Field & Goals")
            
            current_field = st.session_state.user_profile.get('field', 'Programming & Technology')
            field_options = [
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
            ]
            
            field_index = field_options.index(current_field) if current_field in field_options else 0
            field = st.selectbox("Select Your Field", field_options, index=field_index)
            
            goal = st.text_input("What do you want to become?", value=st.session_state.user_profile.get('goal', ''))
            
            st.subheader("Your Current Distractions")
            default_distractions = st.session_state.user_profile.get('distractions', [])
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
            ], default=default_distractions)
            
            st.subheader("Challenge Stage Selection")
            current_stage = st.session_state.user_profile.get('stage', 'Silver (15 Days - Easy)')
            stage_options = [
                "Silver (15 Days - Easy)",
                "Platinum (30 Days - Medium)", 
                "Gold (60 Days - Hard)"
            ]
            stage_index = stage_options.index(current_stage) if current_stage in stage_options else 0
            stage = st.selectbox("Choose your stage", stage_options, index=stage_index)
            
            save_btn = st.form_submit_button("Update Profile")
            
            if save_btn:
                if not field or not goal or not stage:
                    st.error("Please fill all fields")
                else:
                    with st.spinner("Updating your profile..."):
                        profile_data = {
                            'field': field,
                            'goal': goal,
                            'distractions': distractions,
                            'stage': stage,
                            'updated_at': firestore.SERVER_TIMESTAMP
                        }
                        
                        # Update challenge data if stage changed
                        if stage != st.session_state.user_profile.get('stage'):
                            challenge_data = st.session_state.challenge_data
                            challenge_data['current_stage'] = stage
                            save_challenge_data(st.session_state.user['username'], challenge_data)
                            st.session_state.challenge_data = challenge_data
                        
                        st.session_state.user_profile.update(profile_data)
                        
                        try:
                            db.collection('user_profiles').document(st.session_state.user['username']).set(
                                st.session_state.user_profile, merge=True
                            )
                            st.success("Profile updated successfully!")
                            time.sleep(1)
                            st.session_state.page = "daily_challenge"
                            st.rerun()
                        except Exception as e:
                            st.error("Failed to update profile. Please try again.")
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

# STAGE COMPLETION POPUP
def stage_completion_popup():
    if st.session_state.show_stage_completion:
        with st.container():
            st.markdown("<div style='background-color: aliceblue; padding: 20px; border-radius: 10px; border: 2px solid darkblue;'>", unsafe_allow_html=True)
            
            st.success("CONGRATULATIONS!")
            st.markdown(f"### You've successfully completed the {st.session_state.challenge_data['current_stage']}!")
            st.markdown(f"### You've earned the {st.session_state.challenge_data['current_stage'].split(' ')[0]} Badge!")
            
            st.markdown("---")
            
            next_stages = {
                "Silver (15 Days - Easy)": "Platinum (30 Days - Medium)",
                "Platinum (30 Days - Medium)": "Gold (60 Days - Hard)",
                "Gold (60 Days - Hard)": "All Stages Completed!"
            }
            
            next_stage = next_stages.get(st.session_state.challenge_data['current_stage'])
            
            if next_stage and next_stage != "All Stages Completed!":
                st.markdown(f"### Ready to upgrade to {next_stage}?")
                
                upgrade = st.checkbox("Yes, I want to upgrade to the next stage!")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Upgrade Stage", disabled=not upgrade):
                        challenge_data = st.session_state.challenge_data
                        challenge_data['current_stage'] = next_stage
                        challenge_data['current_day'] = 1
                        challenge_data['completed_days'] = 0
                        challenge_data['streak_days'] = 0
                        
                        save_challenge_data(st.session_state.user['username'], challenge_data)
                        st.session_state.challenge_data = challenge_data
                        st.session_state.show_stage_completion = False
                        st.rerun()
                
                with col2:
                    if st.button("Stay Current Stage"):
                        st.session_state.show_stage_completion = False
                        st.rerun()
            else:
                st.success("YOU ARE A CHAMPION! You've completed all stages!")
                if st.button("Continue"):
                    st.session_state.show_stage_completion = False
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# SAFE Daily Challenge Page
def daily_challenge_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        if st.session_state.show_stage_completion:
            stage_completion_popup()
            return
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>Daily Challenge Tracker</h1>", unsafe_allow_html=True)
        
        if st.button("Back to Setup Profile", use_container_width=False):
            st.session_state.page = "setup_profile"
            st.rerun()
        
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
        
        # Progress Dashboard
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
        
        if st.session_state.form_submitted:
            st.success("Today's progress saved successfully!")
            st.session_state.form_submitted = False
        
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
            st.info("Add to your savings - this helps build your project fund!")
            
            savings_amount = st.number_input("Amount to add to savings today ($)",
                                           min_value=0.0,
                                           step=1.0,
                                           key="savings_amount",
                                           help="Add any amount to your challenge savings")
            
            # SMS Reminder Option
            st.markdown("---")
            st.markdown("#### Reminders")
            send_reminder = st.checkbox("Send me an SMS reminder tomorrow", value=False)
            
            submit_btn = st.form_submit_button("Submit Today's Progress")
            
            if submit_btn:
                process_daily_submission(completed_tasks, savings_amount, today, tasks, send_reminder)
        
        if st.session_state.show_motivational_task:
            st.markdown("---")
            with st.container():
                st.success("Your final task for today: Go to Google, find a motivational image and set it as your wallpaper. When you wake up tomorrow, you will remember your mission!")
                time.sleep(5)
                st.session_state.show_motivational_task = False
                st.rerun()
        
        if challenge_data.get('total_savings', 0) > 0:
            st.markdown("---")
            st.markdown("### Your Challenge Savings")
            st.info(f"Total savings: **${challenge_data['total_savings']}**")
            st.markdown("Remember: When you complete this challenge, use this money for making a project in your field or invest it in your field.")
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

def process_daily_submission(completed_tasks, savings_amount, today, tasks, send_reminder=False):
    """Process the daily form submission"""
    try:
        user = st.session_state.user
        challenge_data = st.session_state.challenge_data
        
        missed_tasks = len(tasks) - len(completed_tasks)
        
        st.session_state.show_motivational_task = True
        
        # Send SMS reminder if requested and phone number is available
        if send_reminder and st.session_state.phone_number:
            reminder_message = f"Hello {user['username']}! Don't forget your Brain App challenge today. Stay focused!"
            success, msg = send_sms_reminder(st.session_state.phone_number, reminder_message)
            if success:
                st.info("SMS reminder scheduled for tomorrow!")
            else:
                st.info("SMS service is not configured")
        
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
                
                penalty_record = {
                    'date': today,
                    'amount': savings_amount,
                    'missed_tasks': 1,
                    'reason': f"Missed 1 task"
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
                st.session_state.form_submitted = True
                
                st.warning(f"You missed 1 task but paid ${savings_amount} penalty. Day counted but streak remains: {challenge_data['streak_days']} days")
                st.info("According to rules: When you miss 1 task and pay penalty, the day counts but doesn't increase your streak.")
                
            else:
                st.error("According to rules: You missed 1 task but didn't pay penalty. This day doesn't count toward your progress.")
                
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
            st.error(f"According to rules: You missed {missed_tasks} tasks. This day doesn't count even if you pay penalty.")
            
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
    except Exception as e:
        st.error("Error processing submission. Please try again.")

# SAFE Analytics Page
def analytics_page():
    try:
        if "user" not in st.session_state or st.session_state.user is None:
            st.session_state.page = "signin"
            st.rerun()
            return
        
        show_sidebar_content()
        
        st.markdown("<h1 style='text-align: center; color: darkblue;'>Advanced Analytics Dashboard</h1>", unsafe_allow_html=True)
        
        if st.button("Back to Daily Challenge", use_container_width=False):
            st.session_state.page = "daily_challenge"
            st.rerun()
        
        challenge_data = st.session_state.challenge_data
        user_profile = st.session_state.user_profile
        
        if not challenge_data or not user_profile:
            st.error("Please complete your profile setup first")
            st.session_state.page = "setup_profile"
            st.rerun()
            return
        
        # Show advanced analytics
        create_advanced_analytics(challenge_data, user_profile)
        
        # Additional insights
        st.markdown("---")
        st.markdown("### Performance Insights")
        
        daily_checkins = challenge_data.get('daily_checkins', {})
        if daily_checkins:
            total_days = len(daily_checkins)
            perfect_days = sum(1 for checkin in daily_checkins.values() if checkin.get('perfect_day', False))
            penalty_days = sum(1 for checkin in daily_checkins.values() if checkin.get('penalty_paid', False))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**Total Tracked Days:** {total_days}")
            
            with col2:
                st.success(f"**Perfect Days:** {perfect_days}")
            
            with col3:
                st.warning(f"**Penalty Days:** {penalty_days}")
            
            if total_days > 0:
                success_rate = (perfect_days / total_days) * 100
                st.metric("Overall Success Rate", f"{success_rate:.1f}%")
        else:
            st.info("Complete your first challenge day to see analytics!")
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

# SAFE Certificate Page
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
        
        # Generate certificate
        pdf_bytes = generate_certificate(
            st.session_state.user['username'],
            st.session_state.user_profile,
            st.session_state.challenge_data
        )
        
        if pdf_bytes:
            # Display certificate info
            st.success("Your certificate is ready!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download PDF Certificate",
                    data=pdf_bytes,
                    file_name=f"brain_app_certificate_{st.session_state.user['username']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col2:
                if st.button("Generate New Certificate", use_container_width=True):
                    st.rerun()
        else:
            st.info("Certificate generation is currently unavailable. Please try again later.")
    except Exception as e:
        st.error("Something went wrong. Please try refreshing the page.")
        st.session_state.page = "signin"
        st.rerun()

# SAFE Sign In Page
def sign_in_page():
    try:
        st.markdown("<h1 style='text-align: center; color: darkblue;'>The Brain App</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: darkblue;'>Sign In</h3>", unsafe_allow_html=True)
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
                                        profile_doc = db.collection('user_profiles').document(username_clean).get()
                                        if profile_doc.exists:
                                            st.session_state.user_profile = profile_doc.to_dict()
                                        else:
                                            st.session_state.user_profile = {}
                                        st.session_state.challenge_data = load_challenge_data(username_clean)
                                        set_persistent_login(username_clean)
                                        st.success("Login successful")
                                        if st.session_state.user_profile:
                                            st.session_state.page = "life_vision"
                                        else:
                                            st.session_state.page = "life_vision"
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
    except Exception as e:
        st.error("Something went wrong. Please refresh the page.")

# SAFE Forgot Password Page
def forgot_password_page():
    try:
        st.markdown("<h2 style='text-align: center; color: darkblue;'>Forgot Password</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            with st.form("forgot_form"):
                email = st.text_input("Enter your email")
                submit_btn = st.form_submit_button("Send Reset Link")
                
                if submit_btn:
                    if not email:
                        st.error("Please enter your email")
                    else:
                        email_clean = sanitize_input(email)
                        with st.spinner("Sending password reset link..."):
                            time.sleep(1)
                            username, user_info = get_user_by_email(email_clean)
                            if user_info:
                                try:
                                    reset_link = auth.generate_password_reset_link(email_clean)
                                    email_success, msg = send_password_reset_email(email_clean, reset_link)
                                    if email_success:
                                        st.success("Password reset link sent to your email")
                                    else:
                                        st.info("Email service is not configured")
                                except Exception as e:
                                    st.error("Failed to generate reset link. Please try again later.")
                            else:
                                st.info("If this email is registered, a password reset link will be sent")
            st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))
    except Exception as e:
        st.error("Something went wrong. Please refresh the page.")

# SAFE Sign Up Page
def sign_up_page():
    try:
        st.markdown("<h1 style='text-align: center; color: darkblue;'>The Brain App</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: darkblue;'>Create Account</h3>", unsafe_allow_html=True)
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
                                        if hashed_password:
                                            user_data = {
                                                "email": email_clean,
                                                "password": hashed_password,
                                                "role": "student"
                                            }
                                            db.collection('users').document(username_clean).set(user_data)
                                            st.success("Account created successfully")
                                            st.session_state.page = "signin"
                                            st.rerun()
                                        else:
                                            st.error("Password processing failed")
                            except Exception as e:
                                st.error("Registration failed. Please try again.")
            st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))
    except Exception as e:
        st.error("Something went wrong. Please refresh the page.")

# Main app routing with error handling
try:
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
    elif st.session_state.page == "edit_profile":
        edit_profile_page()
    elif st.session_state.page == "daily_challenge":
        daily_challenge_page()
    elif st.session_state.page == "certificate":
        certificate_page()
    elif st.session_state.page == "analytics":
        analytics_page()
    else:
        st.session_state.page = "signin"
        st.rerun()
except Exception as e:
    st.error("Application error. Please refresh the page.")
    st.session_state.page = "signin"
    st.rerun()
