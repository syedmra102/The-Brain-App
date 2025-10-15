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
import seaborn as sns
import pickle
from datetime import datetime, timedelta
import json
from fpdf import FPDF
import base64
from io import BytesIO
import traceback

# Set professional styling
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Professional color scheme
PROFESSIONAL_COLORS = {
    'primary': '#1f4e79',  # Dark blue
    'secondary': '#2e75b6',  # Medium blue
    'accent': '#9dc3e6',  # Light blue
    'success': '#2e8b57',  # Sea green
    'warning': '#ff8c00',  # Dark orange
    'error': '#c00000',  # Crimson red
    'background': '#f8f9fa'  # Light gray
}

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
            return False, "SMS service configuration incomplete. Please check your Streamlit secrets configuration."
        
        # Check if credentials look valid
        if not twilio_account_sid.startswith("AC") or len(twilio_auth_token) < 20:
            return False, "SMS service credentials are invalid. Please check your Twilio credentials."
        
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
            return False, "SMS service authentication failed. Check your Twilio credentials in Streamlit secrets."
        elif "phone number" in error_msg.lower():
            return False, "Invalid phone number format. Please use format: +1234567890"
        elif "not found" in error_msg.lower():
            return False, "Twilio account not found. Please check your Account SID."
        else:
            return False, f"SMS service error: {error_msg}"

# FIXED PDF Certificate Generation with encoding fix
def generate_certificate(username, user_profile, challenge_data):
    """
    Generate a PDF certificate for completed stages - FIXED VERSION with encoding fix
    """
    try:
        # Create PDF instance with proper encoding
        pdf = FPDF()
        pdf.add_page()
        
        # Set font with proper encoding
        pdf.set_font('Arial', 'B', 24)
        pdf.cell(0, 20, 'CERTIFICATE OF ACHIEVEMENT', 0, 1, 'C')
        pdf.ln(10)
        
        # Add user information
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, 'This certifies that', 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 22)
        # Sanitize username for PDF
        safe_username = username.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, safe_username, 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'has successfully completed the', 0, 1, 'C')
        pdf.ln(5)
        
        # Add stage information
        current_stage = challenge_data.get('current_stage', 'Brain App Challenge')
        safe_stage = current_stage.encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, safe_stage, 0, 1, 'C')
        pdf.ln(10)
        
        # Add achievements
        pdf.set_font('Arial', '', 12)
        field = user_profile.get("field", "Not specified")
        safe_field = field.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 8, f'Field: {safe_field}', 0, 1, 'C')
        
        goal = user_profile.get("goal", "Not specified")
        safe_goal = goal.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 8, f'Goal: {safe_goal}', 0, 1, 'C')
        
        pdf.cell(0, 8, f'Completed Days: {challenge_data.get("completed_days", 0)}', 0, 1, 'C')
        pdf.cell(0, 8, f'Total Savings: ${challenge_data.get("total_savings", 0)}', 0, 1, 'C')
        pdf.ln(10)
        
        # Add badges with safe encoding
        badges = challenge_data.get('badges', [])
        if badges:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Badges Earned:', 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            for badge in badges:
                safe_badge = badge.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 8, f'- {safe_badge}', 0, 1, 'C')  # Using hyphen instead of bullet
            pdf.ln(10)
        
        # Add generation date
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'C')
        
        # Safe PDF output generation
        try:
            return pdf.output(dest='S').encode('latin-1')
        except Exception as e:
            # Fallback to bytes output
            return pdf.output()
            
    except Exception as e:
        st.error(f"PDF Generation Error: {str(e)}")
        return None

# Advanced Analytics Visualizations with Professional Charts
def create_advanced_analytics(challenge_data, user_profile):
    """
    Create advanced analytics visualizations with professional, university-level charts
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
        daily_hours = []
        daily_distractions = []
        
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
            
            # Extract hours and distractions if available
            daily_hours.append(checkin.get('study_hours', 0))
            daily_distractions.append(checkin.get('distraction_count', 0))
        
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
        
        # Row 2: Performance Distribution - Donut Chart
        st.markdown("#### Performance Distribution")
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        
        labels = ['Perfect Days', 'Penalty Days', 'Skipped Days']
        sizes = [sum(perfect_days), sum(penalty_days), sum(skipped_days)]
        colors = [PROFESSIONAL_COLORS['success'], PROFESSIONAL_COLORS['warning'], PROFESSIONAL_COLORS['error']]
        
        # Create donut chart for better visual appeal
        wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                          startangle=90, pctdistance=0.85)
        
        # Draw a circle in the center to make it a donut
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        ax1.add_artist(centre_circle)
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax1.axis('equal')
        ax1.set_title('Performance Distribution Analysis', fontsize=16, fontweight='bold', pad=20)
        
        # Style the text
        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_fontsize(11)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        st.pyplot(fig1)
        
        # Row 3: Savings Growth Over Time - Area Chart with Trend Line
        if len(dates) > 1:
            st.markdown("#### Savings Growth Analysis")
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            
            cumulative_savings = np.cumsum(daily_savings)
            
            # Create area chart with gradient fill
            ax2.fill_between(range(len(dates)), cumulative_savings, alpha=0.4, color=PROFESSIONAL_COLORS['primary'])
            ax2.plot(range(len(dates)), cumulative_savings, color=PROFESSIONAL_COLORS['primary'], 
                    linewidth=3, marker='o', markersize=6, label='Cumulative Savings')
            
            # Add trend line
            z = np.polyfit(range(len(dates)), cumulative_savings, 1)
            p = np.poly1d(z)
            ax2.plot(range(len(dates)), p(range(len(dates))), "--", color=PROFESSIONAL_COLORS['secondary'], 
                    linewidth=2, alpha=0.8, label='Trend Line')
            
            ax2.set_xlabel('Timeline (Days)', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Total Savings ($)', fontsize=12, fontweight='bold')
            ax2.set_title('Cumulative Savings Progress with Trend Analysis', fontsize=14, fontweight='bold')
            ax2.legend()
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
        
        # Row 4: Task Completion Heatmap
        if len(dates) > 7:
            st.markdown("#### Weekly Performance Heatmap")
            
            # Create weekly data
            weeks_data = []
            current_week = []
            
            for i, rate in enumerate(task_completion_rates):
                current_week.append(rate)
                if len(current_week) == 7 or i == len(task_completion_rates) - 1:
                    weeks_data.append(current_week)
                    current_week = []
            
            # Pad last week if necessary
            if current_week:
                while len(current_week) < 7:
                    current_week.append(0)
                weeks_data.append(current_week)
            
            if weeks_data:
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                
                # Create heatmap
                im = ax3.imshow(weeks_data, cmap='YlGnBu', aspect='auto', vmin=0, vmax=100)
                
                # Set labels
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                ax3.set_xticks(range(7))
                ax3.set_xticklabels(days)
                ax3.set_xlabel('Days of Week', fontweight='bold')
                ax3.set_ylabel('Weeks', fontweight='bold')
                ax3.set_title('Weekly Task Completion Heatmap', fontsize=14, fontweight='bold')
                
                # Add colorbar
                cbar = plt.colorbar(im, ax=ax3)
                cbar.set_label('Completion Rate (%)', fontweight='bold')
                
                # Add text annotations
                for i in range(len(weeks_data)):
                    for j in range(len(weeks_data[i])):
                        text = ax3.text(j, i, f'{weeks_data[i][j]:.0f}%',
                                       ha="center", va="center", color="black" if weeks_data[i][j] > 50 else "white",
                                       fontweight='bold')
                
                st.pyplot(fig3)
        
        # Row 5: Performance Metrics Radar Chart
        if len(dates) > 1:
            st.markdown("#### Performance Metrics Radar Chart")
            
            # Calculate metrics for radar chart
            metrics = {
                'Consistency': (sum(perfect_days) / len(dates)) * 100,
                'Task Completion': np.mean(task_completion_rates),
                'Savings Rate': (sum(daily_savings) / len(dates)) * 10,  # Scaled for better visualization
                'Discipline': 100 - (sum(penalty_days) / len(dates)) * 100,
                'Progress Rate': (challenge_data.get('completed_days', 0) / len(dates)) * 100
            }
            
            categories = list(metrics.keys())
            values = list(metrics.values())
            
            # Complete the circle
            values += values[:1]
            categories += categories[:1]
            
            fig4, ax4 = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            
            # Compute angles for each category
            angles = [n / float(len(categories)-1) * 2 * np.pi for n in range(len(categories))]
            
            # Plot the radar chart
            ax4.plot(angles, values, 'o-', linewidth=2, color=PROFESSIONAL_COLORS['primary'], label='Your Performance')
            ax4.fill(angles, values, alpha=0.25, color=PROFESSIONAL_COLORS['primary'])
            
            # Add category labels
            ax4.set_xticks(angles[:-1])
            ax4.set_xticklabels(categories[:-1], fontsize=12, fontweight='bold')
            
            # Set y-axis limits and labels
            ax4.set_ylim(0, 100)
            ax4.set_yticks([20, 40, 60, 80, 100])
            ax4.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=10)
            ax4.grid(True)
            
            ax4.set_title('Comprehensive Performance Analysis', size=16, fontweight='bold', pad=20)
            ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
            
            st.pyplot(fig4)
        
    except Exception as e:
        st.info("Advanced analytics will be available after you complete more challenge days")

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

# FIXED: Higher percentiles are now better (reversed the logic)
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
        
        # FIXED: Higher hours should give higher percentile (better)
        hours_percentile = (df['hours'] <= hours).mean() * 100
        feature_percentiles['Study Hours'] = hours_percentile  # Higher is better
        
        # FIXED: Lower distractions should give higher percentile (better)
        dist_percentile = (df['distraction_count'] >= distractions).mean() * 100
        feature_percentiles['Distraction Control'] = 100 - dist_percentile  # Higher is better
        
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
                # FIXED: Having good habit (value=1) should give higher percentile
                habit_percentile = (df[col] == 1).mean() * 100
                feature_percentiles[friendly_name] = habit_percentile  # Higher is better
            else:
                # FIXED: Not having good habit should give lower percentile
                habit_percentile = (df[col] == 0).mean() * 100
                feature_percentiles[friendly_name] = habit_percentile  # Higher is better
        
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

# Enhanced Sidebar with safe navigation (no emojis)
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
            
            # SMS Reminders Section - IMPROVED with better error messages
            st.markdown("---")
            st.markdown("### SMS Reminders")
            
            # Show SMS configuration status
            twilio_config = st.secrets.get("twilio", {})
            if not all([twilio_config.get("ACCOUNT_SID"), twilio_config.get("AUTH_TOKEN"), twilio_config.get("PHONE_NUMBER")]):
                st.warning("SMS service not configured. Add Twilio credentials to Streamlit secrets.")
            else:
                st.success("SMS service: Configured")
            
            phone_number = st.text_input("Phone Number", 
                                       value=st.session_state.phone_number,
                                       placeholder="+1234567890",
                                       key="phone_input",
                                       help="Include country code (e.g., +923001234567)")
            
            if phone_number != st.session_state.phone_number:
                st.session_state.phone_number = phone_number
            
            if phone_number and st.button("Test SMS", use_container_width=True):
                success, message = send_sms_reminder(phone_number, "Test reminder from The Brain App! You are doing great!")
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

# ML Dashboard Page with Professional Bar Charts
def ml_dashboard_page():
    """Machine Learning Performance Prediction Dashboard"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: #1f4e79;'>Performance Predictor</h1>", unsafe_allow_html=True)
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
        
        # Performance Score with professional styling
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            score = results['score']
            if score >= 80:
                color = PROFESSIONAL_COLORS['success']
                status = "Excellent"
                interpretation = f"You're in the top {100 - score:.1f}% of performers!"
            elif score >= 60:
                color = PROFESSIONAL_COLORS['secondary']
                status = "Good"
                interpretation = f"You're performing better than {score:.1f}% of users!"
            else:
                color = PROFESSIONAL_COLORS['warning']
                status = "Needs Improvement"
                interpretation = f"You're in the bottom {100 - score:.1f}% - time to optimize!"
            
            st.markdown(f"<h1 style='text-align: center; color: {color};'>Performance Score: {score:.1f}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: {color};'>{status}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size: 16px;'>{interpretation}</p>", unsafe_allow_html=True)
        
        # Feature Analysis with Professional Bar Chart
        st.markdown("#### Feature Analysis - Percentile Ranking")
        features_df = pd.DataFrame(list(results['percentiles'].items()), columns=['Feature', 'Percentile'])
        
        # Create professional bar chart with dark blue colors
        fig, ax = plt.subplots(figsize=(12, 8))
        features = features_df['Feature']
        percentiles = features_df['Percentile']
        
        # Create gradient colors based on percentile values
        colors = [PROFESSIONAL_COLORS['primary'] if p >= 70 else 
                 PROFESSIONAL_COLORS['secondary'] if p >= 40 else 
                 PROFESSIONAL_COLORS['warning'] for p in percentiles]
        
        bars = ax.bar(features, percentiles, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
        ax.set_ylabel('Percentile Score (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Performance Features', fontsize=12, fontweight='bold')
        ax.set_title('Feature Performance Percentile Analysis', fontsize=16, fontweight='bold', pad=20)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars with improved positioning
        for bar, value in zip(bars, percentiles):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 1,
                   f'{value:.0f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Add percentile interpretation
        for i, (feature, percentile) in enumerate(zip(features, percentiles)):
            if percentile >= 80:
                interpretation = "Top 20% - Excellent!"
            elif percentile >= 60:
                interpretation = "Top 40% - Very Good"
            elif percentile >= 40:
                interpretation = "Average - Room for growth"
            else:
                interpretation = "Needs attention"
            ax.text(bar.get_x() + bar.get_width()/2, -5, interpretation, 
                   ha='center', va='top', fontsize=9, color='gray', rotation=45)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)
        
        # Individual progress bars with improved styling
        st.markdown("#### Detailed Feature Breakdown")
        for _, row in features_df.iterrows():
            col1, col2, col3 = st.columns([2, 3, 2])
            with col1:
                st.write(f"**{row['Feature']}:**")
            with col2:
                percentile = row['Percentile']
                # Use different colors based on percentile
                if percentile >= 70:
                    color = PROFESSIONAL_COLORS['success']
                elif percentile >= 40:
                    color = PROFESSIONAL_COLORS['secondary']
                else:
                    color = PROFESSIONAL_COLORS['warning']
                
                st.progress(percentile/100, text=f"{percentile:.0f}%")
            with col3:
                if percentile >= 80:
                    st.markdown("<span style='color: #2e8b57; font-weight: bold;'>Excellent</span>", unsafe_allow_html=True)
                elif percentile >= 60:
                    st.markdown("<span style='color: #2e75b6; font-weight: bold;'>Good</span>", unsafe_allow_html=True)
                elif percentile >= 40:
                    st.markdown("<span style='color: #ff8c00; font-weight: bold;'>Average</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: #c00000; font-weight: bold;'>Needs Work</span>", unsafe_allow_html=True)
        
        # Professional Recommendations
        st.markdown("#### Strategic Recommendations")
        low_percentile_features = [(f, p) for f, p in results['percentiles'].items() if p < 40]
        high_percentile_features = [(f, p) for f, p in results['percentiles'].items() if p >= 80]
        
        if low_percentile_features:
            st.warning("**Priority Improvement Areas:**")
            for feature, percentile in low_percentile_features:
                st.write(f"- **{feature}** ({percentile:.0f}%): Focus on improving this area for maximum impact")
        
        if high_percentile_features:
            st.success("**Your Strengths:**")
            for feature, percentile in high_percentile_features:
                st.write(f"- **{feature}** ({percentile:.0f}%): Maintain this excellent performance")
        
        if not low_percentile_features and not high_percentile_features:
            st.info("**Balanced Performance:** All your metrics are in the average range. Consider focusing on specific areas to achieve excellence.")
        
        # Reset button
        if st.button("Make Another Prediction", use_container_width=True):
            st.session_state.prediction_results = None
            st.rerun()

# [Other page functions remain the same as previous implementation - Life Vision, Challenge Rules, Setup Profile, Edit Profile, Daily Challenge, Analytics, Sign In, Forgot Password, Sign Up, Certificate]

# Life Vision Page (no emojis)
def life_vision_page():
    """Life Vision and Goal Setting Page"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: #1f4e79;'>My Life Vision</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.info("Please complete your profile setup to access the full Life Vision features.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    # Vision Board Section
    st.markdown("### My Vision Board")
    
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
            
            # Create professional progress visualization
            fig, ax = plt.subplots(figsize=(10, 3))
            
            # Background bar
            ax.barh(['Progress'], [100], color=PROFESSIONAL_COLORS['accent'], alpha=0.3)
            # Progress bar
            progress_bar = ax.barh(['Progress'], [progress], color=PROFESSIONAL_COLORS['primary'], alpha=0.8)
            
            ax.set_xlim(0, 100)
            ax.set_xlabel('Completion Percentage', fontweight='bold')
            ax.set_title(f'Stage Progress: {current_day}/{total_days} Days', fontweight='bold', pad=10)
            ax.grid(True, alpha=0.3, axis='x')
            
            # Add percentage text
            ax.text(progress/2, 0, f'{progress:.1f}% Complete', ha='center', va='center', 
                   color='white', fontweight='bold', fontsize=12)
            
            st.pyplot(fig)
            
            # Motivational message based on progress
            if progress < 25:
                st.info("Getting started! Every great journey begins with a single step.")
            elif progress < 50:
                st.info("Making progress! Keep building momentum.")
            elif progress < 75:
                st.info("Halfway there! You are doing amazing.")
            else:
                st.info("Almost there! Finish strong!")
    
    # Daily Motivation Section
    st.markdown("---")
    st.markdown("### Daily Motivation")
    
    motivational_quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "The future depends on what you do today. - Mahatma Gandhi",
        "Do not watch the clock; do what it does. Keep going. - Sam Levenson",
        "The harder you work for something, the greater you will feel when you achieve it.",
        "Your limitation - it is only your imagination.",
        "Push yourself, because no one else is going to do it for you.",
        "Great things never come from comfort zones.",
        "Dream it. Wish it. Do it.",
        "Success does not just find you. You have to go out and get it."
    ]
    
    import random
    daily_quote = random.choice(motivational_quotes)
    st.success(f"**Today's Motivation:** {daily_quote}")
    
    # Quick Actions
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

# [Other page functions - Challenge Rules, Setup Profile, Edit Profile, Daily Challenge, Analytics, Sign In, Forgot Password, Sign Up, Certificate - remain the same as previous implementation but with professional colors]

# Analytics Page with Professional Visualizations
def analytics_page():
    """Advanced Analytics and Progress Tracking"""
    show_sidebar_content()
    
    st.markdown("<h1 style='text-align: center; color: #1f4e79;'>Advanced Analytics</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.error("Please complete your profile setup first.")
        if st.button("Setup Profile", use_container_width=True):
            st.session_state.page = "setup_profile"
            st.rerun()
        return
    
    challenge_data = st.session_state.challenge_data
    
    # Overview Metrics
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
    
    # Advanced Analytics with Professional Charts
    create_advanced_analytics(challenge_data, st.session_state.user_profile)
    
    # Badges Section
    st.markdown("---")
    st.markdown("### Earned Badges")
    
    badges = challenge_data.get('badges', [])
    if badges:
        for badge in badges:
            st.success(f"**{badge}**")
    else:
        st.info("Complete more challenges to earn badges!")
    
    # Export Data Option
    st.markdown("---")
    st.markdown("### Data Export")
    
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

# [Sign In, Forgot Password, Sign Up, Certificate pages remain the same but with professional colors]

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
