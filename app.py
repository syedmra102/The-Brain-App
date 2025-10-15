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

# FIXED Twilio SMS Reminders Function
def send_sms_reminder(phone_number, message):
    """
    Send SMS reminder using Twilio - FIXED VERSION
    """
    try:
        # Safely get Twilio credentials
        twilio_config = st.secrets.get("twilio", {})
        twilio_account_sid = twilio_config.get("ACCOUNT_SID", "")
        twilio_auth_token = twilio_config.get("AUTH_TOKEN", "")
        twilio_phone_number = twilio_config.get("PHONE_NUMBER", "")
        
        # Validate credentials format
        if not twilio_account_sid or not twilio_auth_token or not twilio_phone_number:
            return False, "SMS service configuration incomplete"
        
        # Check if credentials look valid
        if not twilio_account_sid.startswith("AC") or len(twilio_auth_token) < 20:
            return False, "SMS service credentials are invalid"
        
        # Try to import Twilio
        try:
            from twilio.rest import Client
        except ImportError:
            return False, "Twilio package not installed. Run: pip install twilio"
        
        # Validate phone number format
        if not phone_number.startswith('+'):
            return False, "Phone number must include country code (e.g., +1234567890)"
        
        client = Client(twilio_account_sid, twilio_auth_token)
        
        message = client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=phone_number
        )
        
        return True, "SMS reminder sent successfully"
    except Exception as e:
        error_msg = str(e)
        if "authenticate" in error_msg.lower():
            return False, "SMS service authentication failed. Check your credentials."
        elif "phone number" in error_msg.lower():
            return False, "Invalid phone number format"
        else:
            return False, f"SMS service error: {error_msg}"

# FIXED PDF Certificate Generation
def generate_certificate(username, user_profile, challenge_data):
    """
    Generate a PDF certificate for completed stages - FIXED VERSION
    """
    try:
        # Create PDF instance
        pdf = FPDF()
        pdf.add_page()
        
        # Add title
        pdf.set_font('Arial', 'B', 24)
        pdf.cell(0, 20, 'CERTIFICATE OF ACHIEVEMENT', 0, 1, 'C')
        pdf.ln(10)
        
        # Add user information
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, 'This certifies that', 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 22)
        pdf.cell(0, 10, username, 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'has successfully completed the', 0, 1, 'C')
        pdf.ln(5)
        
        # Add stage information
        current_stage = challenge_data.get('current_stage', 'Brain App Challenge')
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, current_stage, 0, 1, 'C')
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
        
        # Add generation date
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'C')
        
        # FIXED: Safe PDF output generation
        try:
            pdf_output = pdf.output(dest='S')
            if isinstance(pdf_output, bytes):
                return pdf_output
            else:
                return pdf_output.encode('utf-8')
        except:
            # Alternative method
            return pdf.output()
            
    except Exception as e:
        st.error(f"PDF Generation Error: {str(e)}")
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
            
            # SMS Reminders Section - IMPROVED
            st.markdown("---")
            st.markdown("### SMS Reminders")
            phone_number = st.text_input("Phone Number", 
                                       value=st.session_state.phone_number,
                                       placeholder="+1234567890",
                                       key="phone_input",
                                       help="Include country code (e.g., +923001234567)")
            
            if phone_number != st.session_state.phone_number:
                st.session_state.phone_number = phone_number
            
            if phone_number and st.button("Test SMS", use_container_width=True):
                success, message = send_sms_reminder(phone_number, "Test reminder from The Brain App! You're doing great!")
                if success:
                    st.success("Test SMS sent successfully!")
                else:
                    st.warning(f"SMS not sent: {message}")
            
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

# ML Dashboard Page
def ml_dashboard_page():
    """Machine Learning Performance Prediction Dashboard"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("### Predict your performance based on your daily habits")
    
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            hours = st.slider("Study Hours", 0, 12, 4, help="Hours spent on focused work")
            distraction_count = st.slider("Distractions Count", 0, 20, 5, help="Number of distractions encountered")
        
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
            
            prediction = predict_performance(hours, distraction_count, habit_inputs)
            percentiles = calculate_feature_percentiles(hours, distraction_count, habit_inputs)
            
            st.session_state.prediction_results = {
                'score': prediction,
                'percentiles': percentiles,
                'hours': hours,
                'distractions': distraction_count,
                'habits': habit_inputs
            }
    
    if st.session_state.prediction_results:
        results = st.session_state.prediction_results
        
        st.markdown("---")
        st.markdown("### Prediction Results")
        
        # Performance Score
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            score = results['score']
            if score >= 80:
                color = "green"
                emoji = "🎯"
            elif score >= 60:
                color = "orange"
                emoji = "📈"
            else:
                color = "red"
                emoji = "📉"
            
            st.markdown(f"<h1 style='text-align: center; color: {color};'>Performance Score: {score:.1f}% {emoji}</h1>", unsafe_allow_html=True)
        
        # Feature Analysis
        st.markdown("#### Feature Analysis")
        features_df = pd.DataFrame(list(results['percentiles'].items()), columns=['Feature', 'Percentile'])
        
        for _, row in features_df.iterrows():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"{row['Feature']}:")
            with col2:
                percentile = row['Percentile']
                st.progress(percentile/100, text=f"{percentile:.0f}%")
        
        # Recommendations
        st.markdown("#### Recommendations")
        low_percentile_features = [f for f, p in results['percentiles'].items() if p < 40]
        if low_percentile_features:
            st.warning("**Areas for Improvement:**")
            for feature in low_percentile_features:
                st.write(f"• Improve your {feature.lower()}")
        else:
            st.success("**Great job!** All your habits are in good standing.")
        
        # Reset button
        if st.button("Make Another Prediction", use_container_width=True):
            st.session_state.prediction_results = None
            st.rerun()

# Life Vision Page
def life_vision_page():
    """Life Vision and Goal Setting Page"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>My Life Vision</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.info("Please complete your profile setup to access the full Life Vision features.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    # Vision Board Section
    st.markdown("### 🎯 My Vision Board")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Current Status")
        st.write(f"**Field:** {st.session_state.user_profile.get('field', 'Not set')}")
        st.write(f"**Goal:** {st.session_state.user_profile.get('goal', 'Not set')}")
        st.write(f"**Stage:** {st.session_state.user_profile.get('stage', 'Not set')}")
        
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
            
            # Motivational quote based on progress
            if progress < 25:
                st.info("🚀 **Getting started!** Every great journey begins with a single step.")
            elif progress < 50:
                st.info("📈 **Making progress!** Keep building momentum.")
            elif progress < 75:
                st.info("🔥 **Halfway there!** You're doing amazing.")
            else:
                st.info("🎯 **Almost there!** Finish strong!")
    
    # Daily Motivation Section
    st.markdown("---")
    st.markdown("### 💪 Daily Motivation")
    
    motivational_quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "The future depends on what you do today. - Mahatma Gandhi",
        "Don't watch the clock; do what it does. Keep going. - Sam Levenson",
        "The harder you work for something, the greater you'll feel when you achieve it.",
        "Your limitation—it's only your imagination.",
        "Push yourself, because no one else is going to do it for you.",
        "Great things never come from comfort zones.",
        "Dream it. Wish it. Do it.",
        "Success doesn't just find you. You have to go out and get it."
    ]
    
    import random
    daily_quote = random.choice(motivational_quotes)
    st.success(f"**Today's Motivation:** {daily_quote}")
    
    # Quick Actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
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

# Challenge Rules Page
def challenge_rules_page():
    """Challenge Rules and Guidelines Page"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Challenge Rules & Guidelines</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ## 🎯 The Brain App Challenge System
    
    ### Challenge Stages
    """)
    
    # Stage Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🥈 Silver Stage
        **Duration:** 15 Days (Easy)
        
        **Daily Tasks:**
        - 2 hours of focused work
        - No distractions
        - Fill daily routine form
        
        **Perfect for beginners!**
        """)
    
    with col2:
        st.markdown("""
        ### 🥉 Platinum Stage  
        **Duration:** 30 Days (Medium)
        
        **Daily Tasks:**
        - 4 hours of focused work
        - No distractions
        - 30 pushups exercise
        - Drink 5L water
        - Avoid junk food
        - Fill daily form
        
        **Intermediate level challenge!**
        """)
    
    with col3:
        st.markdown("""
        ### 🥇 Gold Stage
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
        
        **Advanced discipline training!**
        """)
    
    st.markdown("---")
    
    # Rules Section
    st.markdown("""
    ## 📜 Challenge Rules
    
    ### Task Completion Rules:
    1. **Perfect Day (All tasks completed):**
       - Day counts toward progress
       - Streak increases by 1
       - Savings added to total
    
    2. **Miss 1 Task:**
       - **With Penalty Payment:** Day counts but streak doesn't increase
       - **Without Penalty:** Day doesn't count toward progress
    
    3. **Miss 2+ Tasks:**
       - Day doesn't count (even with penalty)
       - No progress made
    
    ### Penalty System:
    - Pay a self-determined penalty amount when you miss 1 task
    - Penalty money goes into your savings
    - Helps maintain accountability
    
    ### Streak System:
    - Perfect days increase your streak
    - Breaking streak doesn't reset overall progress
    - Long streaks earn special badges!
    """)
    
    # Badges Section
    st.markdown("---")
    st.markdown("""
    ## 🏆 Achievement Badges
    
    Earn badges for your accomplishments:
    
    - **Consistency Badge:** 7-day perfect streak
    - **Discipline Master:** 30-day perfect streak  
    - **Elite Performer:** 60-day perfect streak
    - **Savings Champion:** $100+ total savings
    - **Stage Completer:** Finish any challenge stage
    - **Distraction-Free:** Perfect distraction control for a week
    """)
    
    if st.button("Back to Dashboard", use_container_width=True):
        st.session_state.page = "life_vision"
        st.rerun()

# Setup Profile Page
def setup_profile_page():
    """User Profile Setup Page"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Setup Your Profile</h1>", unsafe_allow_html=True)
    
    with st.form("profile_setup"):
        st.markdown("### Tell Us About Yourself")
        
        # Basic Information
        col1, col2 = st.columns(2)
        
        with col1:
            field = st.selectbox(
                "Your Field/Profession",
                ["Student", "Software Developer", "Entrepreneur", "Researcher", 
                 "Creative Arts", "Business", "Healthcare", "Engineering", "Other"]
            )
            
            if field == "Other":
                field = st.text_input("Specify your field")
        
        with col2:
            goal = st.text_input("I want to become...", 
                               placeholder="e.g., a successful entrepreneur, expert developer, etc.")
        
        # Challenge Stage Selection
        st.markdown("### Choose Your Challenge Stage")
        stage = st.selectbox(
            "Challenge Difficulty",
            ["Silver (15 Days - Easy)", "Platinum (30 Days - Medium)", "Gold (60 Days - Hard)"],
            help="Start with Silver if you're new to productivity challenges"
        )
        
        # Distractions
        st.markdown("### Your Biggest Distractions")
        distractions = st.multiselect(
            "Select your main distractions",
            ["Social Media", "Video Games", "TV/Netflix", "Phone Notifications", 
             "Procrastination", "Unorganized Environment", "Lack of Motivation", "Other"]
        )
        
        # Additional Information
        st.markdown("### Additional Preferences")
        enable_sms = st.checkbox("Enable SMS reminders (recommended)", value=True)
        daily_reminder_time = st.time_input("Preferred reminder time", value=datetime.now().time())
        
        submitted = st.form_submit_button("Save Profile & Start Challenge", use_container_width=True)
        
        if submitted:
            if not goal:
                st.error("Please tell us what you want to become!")
                return
            
            # Save profile data
            profile_data = {
                'field': field,
                'goal': goal,
                'stage': stage,
                'distractions': distractions,
                'enable_sms': enable_sms,
                'daily_reminder_time': str(daily_reminder_time),
                'created_at': datetime.now()
            }
            
            try:
                db.collection('user_profiles').document(st.session_state.user['username']).set(profile_data)
                st.session_state.user_profile = profile_data
                
                # Initialize challenge data
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
                
                st.success("Profile setup complete! Welcome to The Brain App Challenge! 🎉")
                st.balloons()
                
                # Redirect to life vision page
                time.sleep(2)
                st.session_state.page = "life_vision"
                st.rerun()
                
            except Exception as e:
                st.error("Error saving profile. Please try again.")

# Edit Profile Page
def edit_profile_page():
    """Edit User Profile Page"""
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
        
        # Basic Information
        col1, col2 = st.columns(2)
        
        with col1:
            field = st.selectbox(
                "Your Field/Profession",
                ["Student", "Software Developer", "Entrepreneur", "Researcher", 
                 "Creative Arts", "Business", "Healthcare", "Engineering", "Other"],
                index=["Student", "Software Developer", "Entrepreneur", "Researcher", 
                      "Creative Arts", "Business", "Healthcare", "Engineering", "Other"].index(
                          st.session_state.user_profile.get('field', 'Student')
                      )
            )
            
            if field == "Other":
                field = st.text_input("Specify your field", value=st.session_state.user_profile.get('field_custom', ''))
        
        with col2:
            goal = st.text_input("I want to become...", 
                               value=st.session_state.user_profile.get('goal', ''),
                               placeholder="e.g., a successful entrepreneur, expert developer, etc.")
        
        # Challenge Stage Selection
        st.markdown("### Update Challenge Stage")
        current_stage = st.session_state.user_profile.get('stage', 'Silver (15 Days - Easy)')
        stage_options = ["Silver (15 Days - Easy)", "Platinum (30 Days - Medium)", "Gold (60 Days - Hard)"]
        stage_index = stage_options.index(current_stage) if current_stage in stage_options else 0
        
        stage = st.selectbox(
            "Challenge Difficulty",
            stage_options,
            index=stage_index,
            help="Changing stage will reset your current progress for the new stage"
        )
        
        # Distractions
        st.markdown("### Update Your Distractions")
        current_distractions = st.session_state.user_profile.get('distractions', [])
        distractions = st.multiselect(
            "Select your main distractions",
            ["Social Media", "Video Games", "TV/Netflix", "Phone Notifications", 
             "Procrastination", "Unorganized Environment", "Lack of Motivation", "Other"],
            default=current_distractions
        )
        
        # Additional Information
        st.markdown("### Update Preferences")
        enable_sms = st.checkbox("Enable SMS reminders", 
                               value=st.session_state.user_profile.get('enable_sms', True))
        
        submitted = st.form_submit_button("Update Profile", use_container_width=True)
        
        if submitted:
            if not goal:
                st.error("Please tell us what you want to become!")
                return
            
            # Check if stage changed
            stage_changed = stage != st.session_state.user_profile.get('stage')
            
            # Update profile data
            profile_data = {
                'field': field,
                'goal': goal,
                'stage': stage,
                'distractions': distractions,
                'enable_sms': enable_sms,
                'updated_at': datetime.now()
            }
            
            try:
                db.collection('user_profiles').document(st.session_state.user['username']).update(profile_data)
                st.session_state.user_profile.update(profile_data)
                
                # Reset challenge data if stage changed
                if stage_changed:
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
                    st.info("Challenge stage changed. Progress has been reset for the new stage.")
                
                st.success("Profile updated successfully! ✅")
                
                # Redirect to life vision page
                time.sleep(2)
                st.session_state.page = "life_vision"
                st.rerun()
                
            except Exception as e:
                st.error("Error updating profile. Please try again.")

# Stage Completion Popup
def stage_completion_popup():
    """Show stage completion celebration"""
    if st.session_state.show_stage_completion:
        with st.container():
            st.markdown("""
            <style>
            .celebration {
                background: linear-gradient(45deg, #FFD700, #FFA500);
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                margin: 2rem 0;
                border: 3px solid #FF6B00;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="celebration">', unsafe_allow_html=True)
            st.balloons()
            st.markdown("# 🎉 CONGRATULATIONS! 🎉")
            st.markdown(f"### You've completed the {st.session_state.user_profile.get('stage')} Stage!")
            st.markdown("### You are amazing! 🏆")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Continue to Next Stage", use_container_width=True):
                    st.session_state.show_stage_completion = False
                    # Logic to advance to next stage would go here
                    st.rerun()
            with col2:
                if st.button("Celebrate! 🎊", use_container_width=True):
                    st.session_state.show_stage_completion = False
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# Daily Challenge Page
def daily_challenge_page():
    """Daily Challenge Check-in Page"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Daily Challenge</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.error("Please complete your profile setup first.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    # Show stage completion popup if applicable
    stage_completion_popup()
    
    # Current progress
    challenge_data = st.session_state.challenge_data
    current_stage = st.session_state.user_profile.get('stage', 'Silver (15 Days - Easy)')
    current_day = challenge_data.get('current_day', 1)
    total_days = get_stage_days(current_stage)
    
    st.markdown(f"### {current_stage} - Day {current_day}/{total_days}")
    
    # Progress bar
    progress = (current_day / total_days) * 100
    st.progress(progress/100, text=f"Stage Progress: {progress:.1f}%")
    
    # Show current streak and savings
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Streak", f"{challenge_data.get('streak_days', 0)} days")
    with col2:
        st.metric("Completed Days", challenge_data.get('completed_days', 0))
    with col3:
        st.metric("Total Savings", f"${challenge_data.get('total_savings', 0)}")
    
    st.markdown("---")
    
    # Check if already submitted today
    today = datetime.now().strftime("%Y-%m-%d")
    if challenge_data.get('daily_checkins', {}).get(today):
        st.success("✅ You've already completed today's check-in! Great job!")
        st.info("Come back tomorrow for your next challenge.")
        
        if st.button("View My Progress", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()
        return
    
    # Daily Challenge Form
    st.markdown("### Today's Tasks")
    tasks = get_stage_tasks(current_stage)
    
    completed_tasks = []
    for task in tasks:
        if st.checkbox(task, key=f"task_{task}"):
            completed_tasks.append(task)
    
    st.markdown("---")
    st.markdown("### Penalty & Savings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        missed_tasks = len(tasks) - len(completed_tasks)
        if missed_tasks == 1:
            savings_amount = st.number_input(
                "Penalty Amount (if you missed 1 task)",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=1.0,
                help="Pay penalty to count this day despite missing 1 task"
            )
        else:
            savings_amount = st.number_input(
                "Savings to Add (for perfect day)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=1.0,
                help="Add to your savings for a perfect day"
            )
    
    with col2:
        st.markdown("#### Today's Summary")
        st.write(f"Tasks completed: **{len(completed_tasks)}/{len(tasks)}**")
        st.write(f"Tasks missed: **{missed_tasks}**")
        
        if missed_tasks == 0:
            st.success("Perfect day! All tasks completed! 🎉")
        elif missed_tasks == 1:
            st.warning("You missed 1 task. Pay penalty to count this day.")
        else:
            st.error(f"You missed {missed_tasks} tasks. This day won't count.")
    
    # SMS Reminder Option
    st.markdown("---")
    send_reminder = st.checkbox("Send me SMS reminders tomorrow", value=True)
    
    # Submit Button
    if st.button("Submit Daily Check-in", use_container_width=True, type="primary"):
        process_daily_submission(completed_tasks, savings_amount, today, tasks, send_reminder)

# Analytics Page
def analytics_page():
    """Advanced Analytics and Progress Tracking"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Advanced Analytics</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.error("Please complete your profile setup first.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    challenge_data = st.session_state.challenge_data
    
    # Overview Metrics
    st.markdown("### 📊 Progress Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Stage", st.session_state.user_profile.get('stage', 'Not set'))
    with col2:
        st.metric("Current Day", challenge_data.get('current_day', 1))
    with col3:
        st.metric("Streak Days", challenge_data.get('streak_days', 0))
    with col4:
        st.metric("Total Savings", f"${challenge_data.get('total_savings', 0)}")
    
    # Advanced Analytics
    create_advanced_analytics(challenge_data, st.session_state.user_profile)
    
    # Badges Section
    st.markdown("---")
    st.markdown("### 🏆 Earned Badges")
    
    badges = challenge_data.get('badges', [])
    if badges:
        for badge in badges:
            st.success(f"**{badge}**")
    else:
        st.info("Complete more challenges to earn badges!")
    
    # Export Data Option
    st.markdown("---")
    st.markdown("### 📈 Data Export")
    
    if st.button("Export My Progress Data", use_container_width=True):
        # Create downloadable data
        progress_data = {
            'username': st.session_state.user['username'],
            'profile': st.session_state.user_profile,
            'challenge_data': challenge_data,
            'export_date': datetime.now().isoformat()
        }
        
        # Convert to JSON
        json_data = json.dumps(progress_data, indent=2, default=str)
        
        st.download_button(
            label="Download Progress Data (JSON)",
            data=json_data,
            file_name=f"brain_app_progress_{st.session_state.user['username']}.json",
            mime="application/json",
            use_container_width=True
        )

# Sign In Page
def sign_in_page():
    """User Sign In Page"""
    st.markdown("<h1 style='text-align: center; color: darkblue;'>The Brain App 🧠</h1>", unsafe_allow_html=True)
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
                # Get user from database
                user_doc = db.collection('users').document(username).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    if check_password(password, user_data['password']):
                        st.session_state.user = {
                            "username": username,
                            "email": user_data.get("email", ""),
                            "role": user_data.get("role", "student")
                        }
                        
                        # Load user profile
                        profile_doc = db.collection('user_profiles').document(username).get()
                        if profile_doc.exists:
                            st.session_state.user_profile = profile_doc.to_dict()
                        
                        # Load challenge data
                        st.session_state.challenge_data = load_challenge_data(username)
                        
                        # Set persistent login
                        set_persistent_login(username)
                        
                        st.success(f"Welcome back, {username}! 🎉")
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

# Forgot Password Page
def forgot_password_page():
    """Password Recovery Page"""
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Reset Your Password</h1>", unsafe_allow_html=True)
    
    with st.form("forgot_password_form"):
        email = st.text_input("Email Address", placeholder="Enter your registered email")
        
        submitted = st.form_submit_button("Send Reset Link", use_container_width=True)
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
                return
            
            # Find user by email
            user_id, user_data = get_user_by_email(email)
            if user_data:
                # In a real app, generate a secure reset token and link
                reset_link = f"https://yourapp.com/reset-password?token=secure_token_here"
                success, message = send_password_reset_email(email, reset_link)
                
                if success:
                    st.success("Password reset link sent to your email!")
                    st.info("Check your inbox and follow the instructions to reset your password.")
                else:
                    st.error(message)
            else:
                st.error("No account found with this email address")
    
    st.markdown("---")
    if st.button("Back to Sign In", use_container_width=True):
        st.session_state.page = "signin"
        st.rerun()

# Sign Up Page
def sign_up_page():
    """User Registration Page"""
    st.markdown("<h1 style='text-align: center; color: darkblue;'>Create Your Account</h1>", unsafe_allow_html=True)
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email Address", placeholder="Enter your email")
        
        with col2:
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        # Password strength validation
        if password:
            is_valid, message = validate_password(password)
            if is_valid:
                st.success("✓ Password strength: Good")
            else:
                st.warning(f"Password requirements: {message}")
        
        role = st.selectbox("I am a...", ["Student", "Professional", "Entrepreneur", "Other"])
        
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
            
            # Check if username already exists
            user_doc = db.collection('users').document(username).get()
            if user_doc.exists:
                st.error("Username already taken. Please choose another.")
                return
            
            # Check if email already exists
            _, existing_user = get_user_by_email(email)
            if existing_user:
                st.error("Email already registered. Please use a different email or sign in.")
                return
            
            # Create new user
            try:
                hashed_password = hash_password(password)
                if not hashed_password:
                    st.error("Error creating account. Please try again.")
                    return
                
                user_data = {
                    'username': username,
                    'email': email,
                    'password': hashed_password,
                    'role': role,
                    'created_at': datetime.now(),
                    'last_login': datetime.now()
                }
                
                db.collection('users').document(username).set(user_data)
                
                st.success("Account created successfully! 🎉")
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

# IMPROVED Certificate Page
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
        
        # Generate certificate with better error handling
        with st.spinner("Generating your certificate..."):
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
            
            # Show certificate preview info
            st.markdown("---")
            st.markdown("### Certificate Details")
            st.write(f"**Username:** {st.session_state.user['username']}")
            st.write(f"**Current Stage:** {st.session_state.challenge_data.get('current_stage', 'Not set')}")
            st.write(f"**Completed Days:** {st.session_state.challenge_data.get('completed_days', 0)}")
            st.write(f"**Badges Earned:** {len(st.session_state.challenge_data.get('badges', []))}")
            
        else:
            st.error("Failed to generate certificate. This might be due to:")
            st.info("""
            1. **FPDF library issue** - Try installing: `pip install --upgrade fpdf`
            2. **Encoding problem** - Special characters in your username
            3. **Temporary system issue** - Please try again later
            """)
            
    except Exception as e:
        st.error("Something went wrong with certificate generation.")
        st.info("Please try again or contact support if the issue persists.")

# IMPROVED process_daily_submission function
def process_daily_submission(completed_tasks, savings_amount, today, tasks, send_reminder=False):
    """Process the daily form submission"""
    try:
        user = st.session_state.user
        challenge_data = st.session_state.challenge_data
        
        missed_tasks = len(tasks) - len(completed_tasks)
        
        st.session_state.show_motivational_task = True
        
        # Send SMS reminder if requested and phone number is available
        if send_reminder and st.session_state.phone_number:
            reminder_message = f"Hello {user['username']}! Don't forget your Brain App challenge today. Stay focused on your goals!"
            success, msg = send_sms_reminder(st.session_state.phone_number, reminder_message)
            if success:
                st.success("SMS reminder scheduled for tomorrow!")
            else:
                # Show specific error message for SMS
                if "authentication" in msg.lower() or "credentials" in msg.lower():
                    st.info("SMS service needs proper configuration")
                elif "phone number" in msg.lower():
                    st.warning("Please check your phone number format (include country code)")
                else:
                    st.info(f"SMS not available: {msg}")
        
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
    elif st.session_state.page == "analytics":
        analytics_page()
    elif st.session_state.page == "certificate":
        certificate_page()
    else:
        # Default to sign in page
        st.session_state.page = "signin"
        st.rerun()

except Exception as e:
    st.error("An unexpected error occurred. Please refresh the page and try again.")
    st.info("If the problem persists, please contact support.")
