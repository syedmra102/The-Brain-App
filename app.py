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
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random

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

# Email setup
EMAIL_ADDRESS = "zada44919@gmail.com"
EMAIL_PASSWORD = "mrgklwomlcwwfxrd"

# ML Model Setup
@st.cache_resource
def load_ml_model():
    def create_real_world_dataset():
        N = 500
        data = []
        
        for _ in range(N):
            hours = np.clip(np.random.normal(loc=5.5, scale=2.5), 0.5, 10.0)
            distraction_count = int(np.clip(np.random.normal(loc=6, scale=3.5), 0, 15))
            
            avoid_sugar = random.choices(['Yes', 'No'], weights=[0.4, 0.6])[0]
            avoid_junk_food = random.choices(['Yes', 'No'], weights=[0.45, 0.55])[0]
            drink_5L_water = random.choices(['Yes', 'No'], weights=[0.35, 0.65])[0]
            exercise_daily = random.choices(['Yes', 'No'], weights=[0.5, 0.5])[0]
            sleep_early = random.choices(['Yes', 'No'], weights=[0.4, 0.6])[0]
            wakeup_early = 'Yes' if sleep_early == 'Yes' and random.random() < 0.7 else 'No'
            
            score = (hours * 15) - (distraction_count * 7)
            score += 25 if avoid_sugar == 'Yes' else -10
            score += 20 if avoid_junk_food == 'Yes' else -5
            score += 15 if drink_5L_water == 'Yes' else -5
            score += 30 if sleep_early == 'Yes' else -15
            score += 15 if exercise_daily == 'Yes' else -5
            score += 10 if wakeup_early == 'Yes' else 0

            if score > 150:
                score_noise = np.random.normal(loc=0, scale=0.5)
            else:
                score_noise = np.random.normal(loc=0, scale=8)

            final_score = score + score_noise
            percentile = np.clip(100 - (final_score / 2.5), 1.0, 99.9)

            data.append({
                "hours": round(hours, 1),
                "avoid_sugar": avoid_sugar,
                "avoid_junk_food": avoid_junk_food,
                "drink_5L_water": drink_5L_water,
                "sleep_early": sleep_early,
                "exercise_daily": exercise_daily,
                "wakeup_early": wakeup_early,
                "distraction_count": distraction_count,
                "top_percentile": round(percentile, 1)
            })
        
        return pd.DataFrame(data)

    df = create_real_world_dataset()
    
    encoders = {}
    categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water", "sleep_early", "exercise_daily", "wakeup_early"]

    for col in categorical_columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le

    numeric_columns = ['hours', 'distraction_count']
    scaler = StandardScaler()
    df_scaled = df.copy()
    df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])

    X = df_scaled.drop(columns=['top_percentile'])
    y = df_scaled['top_percentile']

    model = XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=5,
        reg_lambda=1.0,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X, y)
    
    return model, encoders, scaler, df, categorical_columns, numeric_columns, X.columns

model, encoders, scaler, df, categorical_columns, numeric_columns, feature_columns = load_ml_model()

# ML Prediction Function
def predict_performance(hours, distraction_count, habits):
    try:
        input_data = pd.DataFrame([{
            'hours': hours,
            'distraction_count': distraction_count,
            **habits
        }])
        
        input_data[numeric_columns] = scaler.transform(input_data[numeric_columns])
        input_data = input_data[feature_columns]
        
        prediction = model.predict(input_data)[0]
        prediction = max(1, min(100, prediction))
        
        return prediction
        
    except Exception as e:
        st.error("Prediction error occurred")
        return 50.0

def calculate_feature_percentiles(hours, distractions, habit_inputs):
    feature_percentiles = {}
    
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

# Helper functions (YOUR EXISTING CODE - NO CHANGES)
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

# Pages (YOUR EXISTING CODE - NO CHANGES)
def sign_in_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
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
                                    st.success("Login successful")
                                    st.session_state.page = "dashboard"
                                    st.rerun()
                                else:
                                    st.error("Invalid username or password")
                            else:
                                st.error("Invalid username or password")
                        except:
                            st.error("System error. Please try again.")

        col1, col2 = st.columns(2)
        with col1:
            st.button("Forgot Password", use_container_width=True, on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        with col2:
            st.button("Create Account", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signup"}))

def forgot_password_page():
    st.markdown("<h2 style='text-align: center;'>Forgot Password</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
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

        st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

def sign_up_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create Account</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
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
                        except:
                            st.error("System error. Please try again.")

        st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

# NEW PAGES ADDED FOR ML MODEL
def dashboard_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
        
    user = st.session_state.user
    
    st.markdown(f"<h1 style='text-align: center;'>Welcome, {user['username']}!</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Performance Dashboard</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("Take Performance Test", use_container_width=True, on_click=lambda: st.session_state.update({"page":"performance_test"}))
        st.button("Logout", use_container_width=True, on_click=lambda: st.session_state.pop("user", None) or st.session_state.update({"page":"signin"}))

def performance_test_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    st.markdown("<h1 style='text-align: center;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Discover Your Top Percentile</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
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
                    time.sleep(2)
                    
                    habits = {}
                    for col in categorical_columns:
                        value = locals()[col]
                        habits[col] = encoders[col].transform([value])[0]
                    
                    percentile = predict_performance(hours, distraction_count, habits)
                    feature_percentiles = calculate_feature_percentiles(hours, distraction_count, habits)
                    
                    st.markdown("---")
                    st.markdown(f"<h2 style='text-align: center; color: #7C3AED;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    features = list(feature_percentiles.keys())
                    percentiles = list(feature_percentiles.values())
                    
                    bars = ax.bar(features, percentiles, color='#7C3AED', alpha=0.7)
                    ax.set_ylabel('Performance Percentile')
                    ax.set_title('Performance Breakdown')
                    ax.set_ylim(0, 100)
                    plt.xticks(rotation=45, ha='right')
                    
                    for bar, percentile_val in zip(bars, percentiles):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                               f'Top {percentile_val:.1f}%', ha='center', va='bottom', fontweight='bold')
                    
                    st.pyplot(fig)
                    
                    st.markdown("---")
                    st.markdown("<h2 style='text-align: center;'>105 Days to Top 1% Challenge</h2>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
                        <h3>Currently at Top {percentile:.1f}% to Goal: Top 1%</h3>
                        <p>Join our 105-day transformation program to become among the top performers worldwide!</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("I Want to Become Top 1%!", use_container_width=True):
                        st.session_state.challenge_accepted = True
                        st.success("Welcome to the 105-Day Challenge! Your transformation journey starts now!")

        st.button("Back to Dashboard", use_container_width=True, on_click=lambda: st.session_state.update({"page":"dashboard"}))

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
