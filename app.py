# ===== IMPORTS =====
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random
import streamlit as st
import json
import time
from datetime import datetime, timedelta
import hashlib

# ===== STREAMLIT PAGE CONFIG =====
st.set_page_config(
    page_title="Performance Predictor",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== CUSTOM CSS =====
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #e0f7fa 0%, #bbdefb 100%);
        color: #2c3e50;
    }
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stage-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1a237e;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .error-box {
        background: linear-gradient(135deg, #f44336 0%, #ef5350 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-box {
        background: linear-gradient(135deg, #ff9800 0%, #ffb74d 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stats-container {
        display: flex;
        justify-content: space-between;
        margin: 1rem 0;
    }
    .stat-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        flex: 1;
        margin: 0 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ===== USER AUTHENTICATION =====
def make_hashed_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashed_password(password, hashed_text):
    return make_hashed_password(password) == hashed_text

def initialize_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    if 'users' not in st.session_state:
        st.session_state.users = {}
    if 'user_profiles' not in st.session_state:
        st.session_state.user_profiles = {}
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = {}

def login_user():
    st.markdown('<div class="main-header"><h1>🚀 Performance Predictor Login</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            st.subheader("Login to Your Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                if username in st.session_state.users and check_hashed_password(password, st.session_state.users[username]):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.current_page = 'dashboard'
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.write("Don't have an account?")
        if st.button("Register Now"):
            st.session_state.current_page = 'register'
            st.rerun()

def register_user():
    st.markdown('<div class="main-header"><h1>🚀 Create Your Account</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("register_form"):
            st.subheader("Create New Account")
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_btn = st.form_submit_button("Register")
            
            if register_btn:
                if new_username in st.session_state.users:
                    st.error("Username already exists!")
                elif new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 4:
                    st.error("Password must be at least 4 characters!")
                else:
                    st.session_state.users[new_username] = make_hashed_password(new_password)
                    st.session_state.user_profiles[new_username] = {}
                    st.session_state.user_progress[new_username] = {
                        'current_stage': None,
                        'days_completed': 0,
                        'streak_days': 0,
                        'total_savings': 0,
                        'start_date': None,
                        'daily_checkins': []
                    }
                    st.success("Account created successfully! Please login.")
                    time.sleep(2)
                    st.session_state.current_page = 'login'
                    st.rerun()
        
        if st.button("← Back to Login"):
            st.session_state.current_page = 'login'
            st.rerun()

# ===== ML MODEL (UNCHANGED) =====
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
            score_noise = np.random.normal(0, 0.5)
        else:
            score_noise = np.random.normal(0, 8)
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

# Initialize ML model
df = create_real_world_dataset()
encoders = {}
categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water",
                       "sleep_early", "exercise_daily", "wakeup_early"]
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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=5,
    reg_lambda=1.0,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model.fit(X_train, y_train)

# ===== CHALLENGE DATA =====
CHALLENGE_STAGES = {
    'Silver': {
        'duration': 15,
        'rules': [
            "Give 2 hours daily in your field",
            "Avoid all distractions for 15 days",
            "Fill the form daily at night"
        ],
        'badge': '🥈'
    },
    'Platinum': {
        'duration': 30,
        'rules': [
            "Give 4 hours daily in your field",
            "Avoid all distractions",
            "1 hour exercise daily",
            "Drink 5 liters of water",
            "Fill the form daily at night"
        ],
        'badge': '🥇'
    },
    'Gold': {
        'duration': 60,
        'rules': [
            "Give 6 hours daily in your field",
            "Avoid all distractions",
            "1 hour exercise daily",
            "Drink 5 liters of water",
            "Wake up early (4am or 5am)",
            "Sleep early (8pm or 9pm)",
            "Avoid junk food",
            "Avoid sugar"
        ],
        'badge': '🏆'
    }
}

DISTRACTIONS = [
    "Procrastination", "Social Media", "Video Games", "TV/Netflix",
    "Unnecessary Phone Usage", "Laziness", "Late Sleeping", "Poor Diet",
    "Negative Friends", "Lack of Exercise", "Masturbation", "Alcohol",
    "Smoking", "Gossiping", "Time Wasting"
]

FIELDS = [
    "Programming", "Engineering", "Medicine", "Business", "Sports",
    "Arts", "Science", "Education", "Finance", "Technology",
    "Healthcare", "Law", "Design", "Marketing", "Other"
]

# ===== APP PAGES =====
def dashboard_page():
    st.markdown(f'<div class="main-header"><h1>🚀 Welcome, {st.session_state.username}!</h1></div>', unsafe_allow_html=True)
    
    # Performance Prediction Section
    st.subheader("📊 Performance Prediction")
    col1, col2 = st.columns(2)
    
    with col1:
        hours = st.number_input("Daily Study Hours (0.5 - 12)", min_value=0.5, max_value=12.0, value=5.5, key="pred_hours")
        distractions = st.number_input("Number of Distractions (0 - 15)", min_value=0, max_value=15, value=5, key="pred_distractions")
    
    with col2:
        habit_inputs = {}
        for col in categorical_columns:
            friendly_name = col.replace('_', ' ').title()
            habit_inputs[col] = st.selectbox(f"{friendly_name}", ["Yes", "No"], key=f"pred_{col}")

    if st.button("Predict My Performance"):
        input_data = pd.DataFrame([{
            'hours': hours,
            'distraction_count': distractions,
            **{col: encoders[col].transform([val])[0] for col, val in habit_inputs.items()}
        }])
        input_data[numeric_columns] = scaler.transform(input_data[numeric_columns])
        input_data = input_data[X.columns]
        prediction = model.predict(input_data)[0]
        prediction = max(1, min(100, prediction))
        
        st.success(f"🎯 Your Overall Performance: Top {prediction:.1f}%")
        
        # Feature breakdown chart
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
            val = encoders[col].transform([habit_inputs[col]])[0]
            if val == 1:
                habit_percentile = (df[col] == 1).mean() * 100
                feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
            else:
                habit_percentile = (df[col] == 0).mean() * 100
                feature_percentiles[friendly_name] = max(1, habit_percentile)

        plt.figure(figsize=(12, 8))
        features = list(feature_percentiles.keys())
        percentiles = list(feature_percentiles.values())
        bars = plt.bar(features, percentiles, color='blue', edgecolor='darkblue')
        plt.bar_label(bars, labels=[f'Top {p:.1f}%' for p in percentiles], label_type='edge', padding=2, fontweight='bold', fontsize=8, color='white')
        plt.xlabel('Performance Features', fontweight='bold', fontsize=12)
        plt.title(f'PERFORMANCE BREAKDOWN ANALYSIS (Top {prediction:.1f}%)', fontweight='bold', fontsize=14)
        plt.ylabel('Performance Percentile', fontweight='bold', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        st.pyplot(plt)

    # Challenge Invitation
    st.markdown("---")
    st.markdown('<div class="success-box"><h2>🎯 Challenge of 105 Days!</h2><h3>Become the Top 1% in Your Field</h3></div>', unsafe_allow_html=True)
    
    if st.button("🚀 Become Top 1%", use_container_width=True):
        st.session_state.current_page = 'challenge_preview'
        st.rerun()

def challenge_preview_page():
    st.markdown('<div class="main-header"><h1>🌟 How Your Life Looks After This Challenge</h1></div>', unsafe_allow_html=True)
    
    benefits = [
        "**Healthy Diet** - No sugar, no alcohol, no junk food; 5L water daily & deep sleep",
        "**Early Rising** - Wake up naturally at 4 AM full of energy",
        "**Peak Fitness** - 1 hour daily exercise, perfect physique",
        "**Quality Sleep** - Deep, restorative sleep by 9 PM",
        "**Expert Skills** - Deep hands-on knowledge in your chosen field",
        "**Unstoppable Character** - Laziness completely removed",
        "**Laser Focus** - All major distractions controlled/removed",
        "**Wealth Mindset** - Financial intelligence & investment habits",
        "**Emotional Mastery** - High EQ, positive thinking, resilience"
    ]
    
    for benefit in benefits:
        st.markdown(f"✅ {benefit}")
    
    if st.button("📋 Show Challenge Rules", use_container_width=True):
        st.session_state.current_page = 'challenge_rules'
        st.rerun()
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()

def challenge_rules_page():
    st.markdown('<div class="main-header"><h1>📋 Challenge Stages & Rules</h1></div>', unsafe_allow_html=True)
    
    # Silver Stage
    with st.expander("🥈 Silver Stage (Easy - 15 Days)", expanded=True):
        st.markdown("""
        **Duration:** 15 days
        
        **Daily Requirements:**
        - Give 2 hours daily in your field
        - Avoid all distractions for 15 days
        - Fill the form daily at night
        
        **Penalty:** If you skip any rule, pay your daily pocket money to savings
        """)
    
    # Platinum Stage
    with st.expander("🥇 Platinum Stage (Medium - 30 Days)"):
        st.markdown("""
        **Duration:** 30 days
        
        **Daily Requirements:**
        - Give 4 hours daily in your field
        - Avoid all distractions
        - 1 hour exercise daily
        - Drink 5 liters of water
        - Fill the form daily at night
        
        **Penalty:** If you skip any rule, pay your daily pocket money to savings
        """)
    
    # Gold Stage
    with st.expander("🏆 Gold Stage (Hard - 60 Days)"):
        st.markdown("""
        **Duration:** 60 days
        
        **Daily Requirements:**
        - Give 6 hours daily in your field
        - Avoid all distractions
        - 1 hour exercise daily
        - Drink 5 liters of water
        - Wake up early (4am or 5am)
        - Sleep early (8pm or 9pm)
        - Avoid junk food
        - Avoid sugar
        
        **Penalty:** If you skip any rule, pay your daily pocket money to savings
        """)
    
    st.markdown("""
    ### 💰 Penalty Rules:
    - If you skip ANY rule on any day, you must pay your entire day's pocket money/earnings to your savings
    - You can only access this savings after completing all 105 days
    - Use this money for your first project or investment in your field
    """)
    
    if st.button("🎯 Start My Challenge Journey", use_container_width=True):
        st.session_state.current_page = 'profile_setup'
        st.rerun()
    
    if st.button("← Back to Preview"):
        st.session_state.current_page = 'challenge_preview'
        st.rerun()

def profile_setup_page():
    st.markdown('<div class="main-header"><h1>👤 Setup Your Challenge Profile</h1></div>', unsafe_allow_html=True)
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            field = st.selectbox("What's Your Field?", FIELDS)
            goal = st.text_input("What Do You Want To Become? (e.g., Doctor, Engineer, etc.)")
        
        with col2:
            selected_stage = st.selectbox("Select Your Challenge Stage", list(CHALLENGE_STAGES.keys()))
            distractions = st.multiselect("Select Your Distractions", DISTRACTIONS)
        
        if st.form_submit_button("💾 Save Profile"):
            st.session_state.user_profiles[st.session_state.username] = {
                'field': field,
                'goal': goal,
                'stage': selected_stage,
                'distractions': distractions,
                'join_date': datetime.now().strftime("%Y-%m-%d")
            }
            
            progress = st.session_state.user_progress[st.session_state.username]
            progress['current_stage'] = selected_stage
            progress['start_date'] = datetime.now().strftime("%Y-%m-%d")
            progress['days_completed'] = 0
            
            st.success("Profile saved successfully!")
            time.sleep(1)
            st.session_state.current_page = 'profile_view'
            st.rerun()

def profile_view_page():
    username = st.session_state.username
    profile = st.session_state.user_profiles.get(username, {})
    progress = st.session_state.user_progress.get(username, {})
    
    st.markdown(f'<div class="main-header"><h1>👤 Profile: {username}</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        st.write(f"**Field:** {profile.get('field', 'Not set')}")
        st.write(f"**Goal:** {profile.get('goal', 'Not set')}")
        st.write(f"**Current Stage:** {profile.get('stage', 'Not started')}")
        st.write(f"**Join Date:** {profile.get('join_date', 'Not set')}")
    
    with col2:
        st.subheader("Your Distractions")
        distractions = profile.get('distractions', [])
        if distractions:
            for dist in distractions:
                st.write(f"• {dist}")
        else:
            st.write("No distractions selected")
    
    st.subheader("Stage Rules")
    current_stage = profile.get('stage')
    if current_stage in CHALLENGE_STAGES:
        stage_info = CHALLENGE_STAGES[current_stage]
        for i, rule in enumerate(stage_info['rules'], 1):
            st.write(f"{i}. {rule}")
    
    if st.button("📝 Start Daily Tracking", use_container_width=True):
        st.session_state.current_page = 'daily_tracking'
        st.rerun()
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()

def daily_tracking_page():
    username = st.session_state.username
    profile = st.session_state.user_profiles.get(username, {})
    progress = st.session_state.user_progress.get(username, {})
    
    current_stage = profile.get('stage')
    if current_stage not in CHALLENGE_STAGES:
        st.error("Please setup your profile first!")
        st.session_state.current_page = 'profile_setup'
        st.rerun()
        return
    
    stage_info = CHALLENGE_STAGES[current_stage]
    total_days = stage_info['duration']
    days_completed = progress.get('days_completed', 0)
    days_left = total_days - days_completed
    
    # Stats Header
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="stat-box"><h3>Stage</h3><h2>{current_stage}</h2></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="stat-box"><h3>Days Left</h3><h2>{days_left}</h2></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="stat-box"><h3>Streak Days</h3><h2>{progress.get("streak_days", 0)}</h2></div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'<div class="stat-box"><h3>Total Savings</h3><h2>${progress.get("total_savings", 0)}</h2></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📋 Daily Challenge Checklist")
    
    # Dynamic checklist based on stage
    with st.form("daily_checklist"):
        tasks_completed = []
        
        if current_stage == 'Silver':
            tasks_completed.append(st.checkbox("✅ Gave 2 hours in my field today"))
            tasks_completed.append(st.checkbox("✅ Avoided all distractions today"))
            tasks_completed.append(st.checkbox("✅ Filling this form at night"))
        
        elif current_stage == 'Platinum':
            tasks_completed.append(st.checkbox("✅ Gave 4 hours in my field today"))
            tasks_completed.append(st.checkbox("✅ Avoided all distractions today"))
            tasks_completed.append(st.checkbox("✅ Completed 1 hour exercise"))
            tasks_completed.append(st.checkbox("✅ Drank 5L water today"))
            tasks_completed.append(st.checkbox("✅ Filling this form at night"))
        
        elif current_stage == 'Gold':
            tasks_completed.append(st.checkbox("✅ Gave 6 hours in my field today"))
            tasks_completed.append(st.checkbox("✅ Avoided all distractions today"))
            tasks_completed.append(st.checkbox("✅ Completed 1 hour exercise"))
            tasks_completed.append(st.checkbox("✅ Drank 5L water today"))
            tasks_completed.append(st.checkbox("✅ Woke up early (4am/5am)"))
            tasks_completed.append(st.checkbox("✅ Will sleep early (8pm/9pm)"))
            tasks_completed.append(st.checkbox("✅ Avoided junk food today"))
            tasks_completed.append(st.checkbox("✅ Avoided sugar today"))
        
        penalty_amount = st.number_input("Penalty Amount (if any rule skipped)", min_value=0.0, value=0.0, step=1.0)
        
        if st.form_submit_button("📅 Submit Daily Progress"):
            completed_count = sum(tasks_completed)
            total_tasks = len(tasks_completed)
            
            if completed_count == total_tasks:
                # Perfect day
                progress['days_completed'] += 1
                progress['streak_days'] += 1
                
                st.markdown('<div class="success-box"><h3>🎉 Perfect Day Completed!</h3></div>', unsafe_allow_html=True)
                st.balloons()
                
                # Check if stage completed
                if progress['days_completed'] >= total_days:
                    st.markdown('<div class="success-box"><h2>🏆 Stage Completed!</h2></div>', unsafe_allow_html=True)
                    if st.button("🚀 Upgrade to Next Stage"):
                        upgrade_stage(current_stage)
                
                st.info("**Final Task:** Go to Google, find a motivational page and set it as your wallpaper for tomorrow!")
                
            elif completed_count >= total_tasks - 2 and penalty_amount > 0:
                # Day accepted with penalty
                progress['days_completed'] += 1
                progress['streak_days'] = 0
                progress['total_savings'] = progress.get('total_savings', 0) + penalty_amount
                
                st.markdown(f'<div class="warning-box"><h3>⚠️ Day Accepted with Penalty</h3><p>${penalty_amount} added to savings. Total: ${progress.get("total_savings", 0)}</p></div>', unsafe_allow_html=True)
                
            else:
                # Day not accepted
                st.markdown('<div class="error-box"><h3>❌ Day Not Accepted</h3><p>You missed more than 2 tasks. Please try again tomorrow!</p></div>', unsafe_allow_html=True)
            
            # Save progress
            progress['daily_checkins'].append({
                'date': datetime.now().strftime("%Y-%m-%d"),
                'completed_tasks': completed_count,
                'total_tasks': total_tasks,
                'penalty_paid': penalty_amount,
                'perfect_day': completed_count == total_tasks
            })
            
            st.session_state.user_progress[username] = progress
    
    if st.button("← Back to Profile"):
        st.session_state.current_page = 'profile_view'
        st.rerun()

def upgrade_stage(current_stage):
    stages = list(CHALLENGE_STAGES.keys())
    current_index = stages.index(current_stage)
    
    if current_index < len(stages) - 1:
        next_stage = stages[current_index + 1]
        st.session_state.user_profiles[st.session_state.username]['stage'] = next_stage
        st.session_state.user_progress[st.session_state.username]['days_completed'] = 0
        st.session_state.user_progress[st.session_state.username]['streak_days'] = 0
        st.success(f"🎉 Upgraded to {next_stage} Stage!")
        time.sleep(2)
        st.rerun()
    else:
        st.success("🎊 Congratulations! You've completed all stages!")

# ===== MAIN APP =====
def main():
    initialize_session_state()
    
    if not st.session_state.logged_in:
        if st.session_state.current_page == 'register':
            register_user()
        else:
            login_user()
    else:
        # Navigation
        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.current_page = 'login'
            st.rerun()
        
        pages = {
            'dashboard': dashboard_page,
            'challenge_preview': challenge_preview_page,
            'challenge_rules': challenge_rules_page,
            'profile_setup': profile_setup_page,
            'profile_view': profile_view_page,
            'daily_tracking': daily_tracking_page
        }
        
        current_page = st.session_state.current_page
        if current_page in pages:
            pages[current_page]()
        else:
            st.session_state.current_page = 'dashboard'
            st.rerun()

if __name__ == "__main__":
    main()
