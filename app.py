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

# Page config
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def send_password_reset_email(to_email, reset_link):
    """
    Send a password reset email containing a secure reset link.
    Uses EMAIL_ADDRESS and EMAIL_PASSWORD from st.secrets.
    """
    try:
        # SECURITY FIX: Move email credentials to st.secrets
        email_address = st.secrets.get("email", {}).get("EMAIL_ADDRESS", "")
        email_password = st.secrets.get("email", {}).get("EMAIL_PASSWORD", "")
        
        if not email_address or not email_password:
            return False, "Email service not configured"
            
        msg = EmailMessage()
        msg['Subject'] = 'Your Brain App - Password Reset'
        msg['From'] = email_address
        msg['To'] = to_email
        msg.set_content(f"""
Hello,

You requested a password reset for your Brain App account.

Click the link below to reset your password (this link will expire as configured by Firebase):

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
        return False, f"Email service temporarily unavailable: {e}"

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
    st.query_params["username"] = username
    st.query_params["logged_in"] = "true"

def clear_persistent_login():
    """Clear persistent login"""
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
            # PUSHUPS FIX: Changed from two separate pushup tasks to one clear task
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

# Twilio SMS Reminders Function
def send_sms_reminder(phone_number, message):
    """
    Send SMS reminder using Twilio
    """
    try:
        # Get Twilio credentials from secrets
        twilio_account_sid = st.secrets.get("twilio", {}).get("ACCOUNT_SID", "")
        twilio_auth_token = st.secrets.get("twilio", {}).get("AUTH_TOKEN", "")
        twilio_phone_number = st.secrets.get("twilio", {}).get("PHONE_NUMBER", "")
        
        if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
            return False, "SMS service not configured"
        
        # Import Twilio here to avoid dependency issues if not configured
        from twilio.rest import Client
        
        client = Client(twilio_account_sid, twilio_auth_token)
        
        message = client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=phone_number
        )
        
        return True, "SMS reminder sent successfully"
    except ImportError:
        return False, "Twilio not installed. Run: pip install twilio"
    except Exception as e:
        return False, f"SMS sending failed: {str(e)}"

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
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        
        # Save to bytes buffer
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        return pdf_bytes
    except Exception as e:
        st.error(f"Certificate generation failed: {str(e)}")
        return None

# Advanced Analytics Visualizations
def create_advanced_analytics(challenge_data, user_profile):
    """
    Create advanced analytics visualizations with different graph types
    """
    try:
        daily_checkins = challenge_data.get('daily_checkins', {})
        if not daily_checkins:
            st.info("📊 Complete more days to see advanced analytics!")
            return
            
        # Prepare data for analytics
        dates = sorted(daily_checkins.keys())
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
        st.markdown("### 📈 Advanced Performance Analytics")
        
        # Row 1: Performance Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_days = len(dates)
            perfect_count = sum(perfect_days)
            st.metric("Perfect Days", f"{perfect_count}/{total_days}")
        
        with col2:
            completion_avg = np.mean(task_completion_rates)
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
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        explode = (0.1, 0, 0)  # explode perfect days
        
        ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')
        ax1.set_title('Day Performance Distribution', fontweight='bold')
        
        st.pyplot(fig1)
        
        # Row 3: Savings Over Time - Area Chart
        st.markdown("#### Savings Growth Over Time")
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        
        cumulative_savings = np.cumsum(daily_savings)
        ax2.fill_between(range(len(dates)), cumulative_savings, alpha=0.4, color='#3498db')
        ax2.plot(range(len(dates)), cumulative_savings, color='#2980b9', linewidth=2, marker='o')
        ax2.set_xlabel('Days')
        ax2.set_ylabel('Total Savings ($)')
        ax2.set_title('Cumulative Savings Progress', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis to show every 5th day
        if len(dates) > 10:
            ax2.set_xticks(range(0, len(dates), max(1, len(dates)//10)))
            ax2.set_xticklabels([dates[i] for i in range(0, len(dates), max(1, len(dates)//10))], rotation=45)
        
        st.pyplot(fig2)
        
        # Row 4: Task Completion Heatmap (Weekly View)
        st.markdown("#### Weekly Performance Heatmap")
        
        # Create a weekly heatmap
        weekly_data = []
        current_week = []
        
        for i, (date, completion) in enumerate(zip(dates, task_completion_rates)):
            current_week.append(completion)
            if len(current_week) == 7 or i == len(dates) - 1:
                weekly_data.append(current_week)
                current_week = []
        
        if weekly_data:
            fig3, ax3 = plt.subplots(figsize=(12, 4))
            im = ax3.imshow(weekly_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
            
            # Set labels
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ax3.set_xticks(range(7))
            ax3.set_xticklabels(days[:len(weekly_data[0])])
            ax3.set_yticks(range(len(weekly_data)))
            ax3.set_yticklabels([f'Week {i+1}' for i in range(len(weekly_data))])
            
            # Add text annotations
            for i in range(len(weekly_data)):
                for j in range(len(weekly_data[i])):
                    text = ax3.text(j, i, f'{weekly_data[i][j]:.0f}%',
                                   ha="center", va="center", color="black", fontweight='bold')
            
            ax3.set_title('Weekly Task Completion Rate (%)', fontweight='bold')
            plt.colorbar(im, ax=ax3, label='Completion Rate %')
            
            st.pyplot(fig3)
        
        # Row 5: Performance Trend - Bar Chart
        st.markdown("#### Daily Performance Trends")
        fig4, ax4 = plt.subplots(figsize=(12, 4))
        
        x_pos = range(len(dates))
        bar_width = 0.6
        
        bars = ax4.bar(x_pos, task_completion_rates, bar_width, 
                      color=['#2ecc71' if rate == 100 else '#f39c12' if rate >= 80 else '#e74c3c' 
                            for rate in task_completion_rates],
                      alpha=0.7)
        
        ax4.set_xlabel('Days')
        ax4.set_ylabel('Completion Rate (%)')
        ax4.set_title('Daily Task Completion Performance', fontweight='bold')
        ax4.set_ylim(0, 110)
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Format x-axis
        if len(dates) > 10:
            ax4.set_xticks(range(0, len(dates), max(1, len(dates)//10)))
            ax4.set_xticklabels([dates[i] for i in range(0, len(dates), max(1, len(dates)//10))], rotation=45)
        
        st.pyplot(fig4)
        
    except Exception as e:
        st.error(f"Analytics creation failed: {str(e)}")

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

# SECURITY FIX: Remove hardcoded email credentials - now using st.secrets

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
if 'phone_number' not in st.session_state:
    st.session_state.phone_number = ""

# Check for persistent login only if user is not already in session state
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
                st.session_state.page = "daily_challenge" if st.session_state.user_profile else "life_vision"
                set_persistent_login(username)
            else:
                st.session_state.page = "signin"
                clear_persistent_login()
        except Exception as e:
            st.session_state.page = "signin"
            clear_persistent_login()
else:
    set_persistent_login(st.session_state.user['username'])

# ML Prediction Function - FIXED VERSION
def predict_performance(hours, distraction_count, habits):
    try:
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
        for col in model_data['feature_columns']:
            if col not in input_df.columns:
                input_df[col] = 0
        
        # Reorder columns to match training data
        input_df = input_df[model_data['feature_columns']]
        
        # Scale numeric features
        numeric_cols = model_data.get('numeric_columns', ['hours', 'distraction_count'])
        input_df[numeric_cols] = model_data['scaler'].transform(input_df[numeric_cols])
        
        # Make prediction
        prediction = model_data['model'].predict(input_df)[0]
        prediction = max(1, min(100, prediction))
        
        return prediction
        
    except Exception as e:
        st.error(f"Prediction error occurred: {str(e)}")
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

# Enhanced Sidebar with Analytics Button
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
                
                # NEW: Analytics Page Button
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
            phone_number = st.text_input("Phone Number (for reminders)", 
                                       value=st.session_state.phone_number,
                                       placeholder="+1234567890")
            
            if phone_number != st.session_state.phone_number:
                st.session_state.phone_number = phone_number
            
            if phone_number and st.button("Test SMS", use_container_width=True):
                success, message = send_sms_reminder(phone_number, "Test reminder from The Brain App! You're doing great!")
                if success:
                    st.success("Test SMS sent!")
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
                clear_persistent_login()
                st.rerun()

# FIXED ML Dashboard Page
def ml_dashboard_page():
    if "user" not in st.session_state or st.session_state.user is None:
        st.session_state.page = "signin"
        clear_persistent_login()
        st.rerun()
        return
    
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Discover Your Top Percentile</h3>", unsafe_allow_html=True)
    
    # ADDED: Back button
    if st.button("← Back to Life Vision", use_container_width=False):
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
                
                # FIXED: Properly encode categorical variables
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
                    if col in model_data['encoders']:
                        try:
                            # Handle encoding safely
                            habits[col] = model_data['encoders'][col].transform([value])[0]
                        except ValueError:
                            # If value not in encoder, use default
                            habits[col] = 0
                    else:
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
        st.markdown(f"<h2 style='text-align: center; color: #7C3AED;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
        
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
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Join 105-Day Transformation Challenge", use_container_width=True, type="primary"):
            if st.session_state.user_profile:
                st.session_state.page = "daily_challenge"
            else:
                st.session_state.page = "setup_profile"
            st.rerun()

# NEW Analytics Page
def analytics_page():
    if "user" not in st.session_state or st.session_state.user is None:
        st.session_state.page = "signin"
        clear_persistent_login()
        st.rerun()
        return
    
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Advanced Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    if st.button("← Back to Daily Challenge", use_container_width=False):
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
    st.markdown("### 📋 Performance Insights")
    
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

# Certificate Page
def certificate_page():
    if "user" not in st.session_state or st.session_state.user is None:
        st.session_state.page = "signin"
        clear_persistent_login()
        st.rerun()
        return
    
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Your Achievement Certificate</h1>", unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard", use_container_width=False):
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
        st.success("🎉 Your certificate is ready!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Download PDF Certificate",
                data=pdf_bytes,
                file_name=f"brain_app_certificate_{st.session_state.user['username']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        with col2:
            if st.button("🔄 Generate New Certificate", use_container_width=True):
                st.rerun()
    else:
        st.error("Could not generate certificate. Please try again.")

# SIMPLIFIED Daily Challenge Page (No Graphs)
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
    
    st.markdown("<h1 style='text-align: center; color: #7C3AED;'>Daily Challenge Tracker</h1>", unsafe_allow_html=True)
    
    if st.button("← Back to Setup Profile", use_container_width=False):
        st.session_state.page = "setup_profile"
        st.rerun()
    
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
    
    # Progress Dashboard - SIMPLIFIED (No Graphs)
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
        send_reminder = st.checkbox("Send me an SMS reminder tomorrow", value=True)
        
        submit_btn = st.form_submit_button("Submit Today's Progress")
        
        if submit_btn:
            process_daily_submission(completed_tasks, savings_amount, today, tasks, send_reminder)
    
    if st.session_state.show_motivational_task:
        st.markdown("---")
        motivational_container = st.container()
        with motivational_container:
            st.success("Your final task for today: Go to Google, find a motivational image and set it as your wallpaper. When you wake up tomorrow, you will remember your mission!")
            time.sleep(20)
            st.session_state.show_motivational_task = False
            st.rerun()
    
    if challenge_data.get('total_savings', 0) > 0:
        st.markdown("---")
        st.markdown("### Your Challenge Savings")
        st.info(f"Total savings: **${challenge_data['total_savings']}**")
        st.markdown("Remember: When you complete this challenge, use this money for making a project in your field or invest it in your field.")

# [Keep all other existing functions the same...]
# (process_daily_submission, challenge_rules_page, life_vision_page, setup_profile_page, 
# edit_profile_page, stage_completion_popup, sign_in_page, forgot_password_page, sign_up_page)

# Main app routing - Add analytics page
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
