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

# [ALL OTHER PAGES REMAIN THE SAME AS BEFORE - ml_dashboard_page, life_vision_page, challenge_rules_page, setup_profile_page, edit_profile_page, stage_completion_popup, daily_challenge_page, analytics_page, sign_in_page, forgot_password_page, sign_up_page]

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
        
        # [REST OF THE ORIGINAL process_daily_submission FUNCTION REMAINS THE SAME]
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
   
