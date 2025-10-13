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

# Page config
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

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

# Load ML Model from pickle file
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

# Helper functions (your existing code)
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

# Your existing pages (sign_in_page, forgot_password_page, sign_up_page) remain EXACTLY THE SAME

def dashboard_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
        
    user = st.session_state.user
    
    st.markdown(f"<h1 style='text-align: center;'>Welcome, {user['username']}!</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Performance Dashboard</h3>", unsafe_allow_html=True)
    
    st.button("Take Performance Test", on_click=lambda: st.session_state.update({"page":"performance_test"}))
    st.button("Logout", on_click=lambda: st.session_state.pop("user", None) or st.session_state.update({"page":"signin"}))

def performance_test_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    st.markdown("<h1 style='text-align: center;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Discover Your Top Percentile</h3>", unsafe_allow_html=True)
    
    # User progress slider
    user = st.session_state.user
    st.write(f"User: {user['username']}")
    st.progress(0)
    
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
                for col in model_data['categorical_columns']:
                    value = locals()[col]
                    habits[col] = model_data['encoders'][col].transform([value])[0]
                
                percentile = predict_performance(hours, distraction_count, habits)
                feature_percentiles = calculate_feature_percentiles(hours, distraction_count, habits)
                
                st.markdown("---")
                st.markdown(f"<h2 style='text-align: center; color: #7C3AED;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
                
                # DARK BLUE CHART
                fig, ax = plt.subplots(figsize=(12, 6))
                features = list(feature_percentiles.keys())
                percentiles = list(feature_percentiles.values())
                
                # Dark blue color
                bars = ax.bar(features, percentiles, color='#1E3A8A', edgecolor='#1E40AF', linewidth=1.5)
                ax.set_ylabel('Performance Percentile', fontweight='bold')
                ax.set_title('Performance Breakdown Analysis', fontweight='bold', fontsize=14)
                ax.set_ylim(0, 100)
                plt.xticks(rotation=45, ha='right', fontweight='bold')
                
                # Add value labels
                for bar, percentile_val in zip(bars, percentiles):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'Top {percentile_val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=9)
                
                # Dark blue grid
                ax.grid(True, alpha=0.3, color='#1E40AF')
                ax.set_facecolor('#F8FAFC')
                
                st.pyplot(fig)
                
                # 105 Days Challenge
                st.markdown("---")
                st.markdown("<h2 style='text-align: center;'>105 Days to Top 1% Challenge</h2>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
                    <h3 style='text-align: center;'>Currently at Top {percentile:.1f}% → Goal: Top 1%</h3>
                    <p style='text-align: center;'>Join our 105-day transformation program to become among the top performers worldwide!</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("I Want to Become Top 1%!", use_container_width=True):
                    st.session_state.challenge_accepted = True
                    st.success("Welcome to the 105-Day Challenge! Your transformation journey starts now!")

# Main app routing
if "page" not in st.session_state:
    st.session_state.page = "signin"

if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
elif st.session_state.page == "forgot_password":
    forgot_password_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
elif st.session_state.page == "performance_test":
    performance_test_page()
