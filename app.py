import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random
import streamlit as st
import hashlib
from datetime import datetime

# ===== STREAMLIT PAGE CONFIG =====
st.set_page_config(
    page_title="Performance Predictor",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== PROFESSIONAL CSS =====
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1E90FF 0%, #0066CC 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stat-box {
        background: white;
        padding: 1.5rem 1rem;
        border-radius: 12px;
        text-align: center;
        border: 3px solid #1E90FF;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.3rem;
    }
    .stat-box h3 {
        color: #1E90FF !important;
        margin: 0;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .stat-box h2 {
        color: #1a237e !important;
        margin: 0.5rem 0 0 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .success-box {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
    }
    .warning-box {
        background: linear-gradient(135deg, #FF9800 0%, #EF6C00 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
    }
    .error-box {
        background: linear-gradient(135deg, #f44336 0%, #C62828 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
    }
    .stage-info-box {
        background: linear-gradient(135deg, #1E90FF 0%, #0066CC 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1E90FF 0%, #0066CC 100%);
        color: white;
        border: none;
        padding: 0.7rem 2rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0066CC 0%, #004499 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ===== USER AUTHENTICATION =====
def init_session():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'users_db' not in st.session_state:
        st.session_state.users_db = {}
    if 'profiles_db' not in st.session_state:
        st.session_state.profiles_db = {}
    if 'progress_db' not in st.session_state:
        st.session_state.progress_db = {}
    if 'page' not in st.session_state:
        st.session_state.page = "login"

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ===== YOUR EXACT ML MODEL =====
@st.cache_resource
def initialize_ml_model():
    # Your exact dataset creation function
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

    # Create dataset
    df = create_real_world_dataset()
    
    # Your exact preprocessing
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

    # Your exact model
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
    
    return model, encoders, scaler, categorical_columns, numeric_columns, X.columns

# Initialize ML model once
model, encoders, scaler, categorical_columns, numeric_columns, feature_columns = initialize_ml_model()

# ===== APP DATA =====
CHALLENGE_STAGES = {
    'Silver': {
        'duration': 15,
        'badge': '🥈',
        'rules': [
            "Give 2 hours daily in your field",
            "Avoid all distractions for 15 days", 
            "Fill the form daily at night"
        ]
    },
    'Platinum': {
        'duration': 30,
        'badge': '🥇',
        'rules': [
            "Give 4 hours daily in your field",
            "Avoid all distractions",
            "1 hour exercise daily",
            "Drink 5 liters of water",
            "Fill the form daily at night"
        ]
    },
    'Gold': {
        'duration': 60,
        'badge': '🏆',
        'rules': [
            "Give 6 hours daily in your field",
            "Avoid all distractions",
            "1 hour exercise daily", 
            "Drink 5 liters of water",
            "Wake up early (4am or 5am)",
            "Sleep early (8pm or 9pm)",
            "Avoid junk food",
            "Avoid sugar"
        ]
    }
}

FIELDS = ["Programming", "Engineering", "Medicine", "Business", "Sports", "Arts", "Science", "Education", "Finance"]
DISTRACTIONS = ["Social Media", "Procrastination", "Video Games", "TV/Netflix", "Phone Addiction", "Laziness", "Late Sleeping"]

# ===== PAGES =====
def login_page():
    st.markdown('<div class="main-header"><h1>🚀 Performance Predictor</h1><p>Become the Top 1% in Your Field</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("👤 Username")
                password = st.text_input("🔒 Password", type="password")
                if st.form_submit_button("🚀 Login", use_container_width=True):
                    if username in st.session_state.users_db and st.session_state.users_db[username] == hash_password(password):
                        st.session_state.user = username
                        if username not in st.session_state.profiles_db:
                            st.session_state.profiles_db[username] = {}
                        if username not in st.session_state.progress_db:
                            st.session_state.progress_db[username] = {
                                'current_stage': None,
                                'days_completed': 0,
                                'streak_days': 0,
                                'total_savings': 0,
                                'start_date': None
                            }
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
        
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("👤 Choose Username")
                new_pwd = st.text_input("🔒 Choose Password", type="password")
                confirm_pwd = st.text_input("🔒 Confirm Password", type="password")
                if st.form_submit_button("📝 Register", use_container_width=True):
                    if new_user in st.session_state.users_db:
                        st.error("❌ Username already exists")
                    elif new_pwd != confirm_pwd:
                        st.error("❌ Passwords don't match")
                    elif len(new_pwd) < 4:
                        st.error("❌ Password must be at least 4 characters")
                    else:
                        st.session_state.users_db[new_user] = hash_password(new_pwd)
                        st.success("✅ Account created! Please login")
                        st.rerun()

def dashboard():
    st.markdown(f'<div class="main-header"><h1>👋 Welcome, {st.session_state.user}!</h1><p>Track your performance and achieve excellence</p></div>', unsafe_allow_html=True)
    
    # Your exact ML prediction interface
    st.subheader("📊 Performance Prediction Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        hours = st.slider("🕒 Daily Study Hours", 0.5, 12.0, 5.5, 0.5)
        distractions = st.slider("📵 Number of Distractions", 0, 15, 5)
    
    with col2:
        habit_inputs = {}
        for col in categorical_columns:
            friendly_name = col.replace('_', ' ').title()
            habit_inputs[col] = st.selectbox(f"{friendly_name}", ["Yes", "No"])

    if st.button("🎯 Predict My Performance", use_container_width=True):
        # Your exact prediction code
        input_data = pd.DataFrame([{
            'hours': hours,
            'distraction_count': distractions,
            **{col: encoders[col].transform([val])[0] for col, val in habit_inputs.items()}
        }])
        
        input_data[numeric_columns] = scaler.transform(input_data[numeric_columns])
        input_data = input_data[feature_columns]
        
        prediction = model.predict(input_data)[0]
        prediction = max(1, min(100, prediction))
        
        st.success(f"🎯 Your Overall Performance: Top **{prediction:.1f}%**")
        
        # Your exact feature breakdown chart
        feature_percentiles = {}
        df_temp = create_real_world_dataset()  # Create temp dataset for percentiles
        
        hours_percentile = (df_temp['hours'] <= hours).mean() * 100
        feature_percentiles['Study Hours'] = max(1, 100 - hours_percentile)
        
        dist_percentile = (df_temp['distraction_count'] >= distractions).mean() * 100
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
            df_temp[col] = encoders[col].transform(df_temp[col])
            if val == 1:
                habit_percentile = (df_temp[col] == 1).mean() * 100
                feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
            else:
                habit_percentile = (df_temp[col] == 0).mean() * 100
                feature_percentiles[friendly_name] = max(1, habit_percentile)

        # Your exact blue chart
        plt.figure(figsize=(12, 8))
        features = list(feature_percentiles.keys())
        percentiles = list(feature_percentiles.values())
        bars = plt.bar(features, percentiles, color='#1E90FF', edgecolor='darkblue', alpha=0.8)
        plt.bar_label(bars, labels=[f'Top {p:.1f}%' for p in percentiles], label_type='edge', padding=2, fontweight='bold', fontsize=9, color='#1a237e')
        plt.xlabel('Performance Features', fontweight='bold', fontsize=12, color='#1a237e')
        plt.ylabel('Performance Percentile', fontweight='bold', fontsize=12, color='#1a237e')
        plt.title(f'PERFORMANCE BREAKDOWN ANALYSIS (Top {prediction:.1f}%)', fontweight='bold', fontsize=14, color='#1a237e')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        st.pyplot(plt)

    # Challenge Section
    st.markdown("---")
    st.markdown('<div class="stage-info-box"><h2>🎯 Challenge of 105 Days!</h2><h3>Become the Top 1% in Your Field</h3></div>', unsafe_allow_html=True)
    
    if st.button("🚀 Start 105-Day Challenge", use_container_width=True):
        st.session_state.page = "challenge_preview"
        st.rerun()

def challenge_preview():
    st.markdown('<div class="main-header"><h1>🌟 Transform Your Life</h1><p>Your future after completing the challenge</p></div>', unsafe_allow_html=True)
    
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
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Show Rules & Stages", use_container_width=True):
            st.session_state.page = "challenge_rules"
            st.rerun()
    with col2:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

def challenge_rules():
    st.markdown('<div class="main-header"><h1>📋 Challenge Structure</h1><p>Three stages to excellence</p></div>', unsafe_allow_html=True)
    
    for stage, info in CHALLENGE_STAGES.items():
        with st.expander(f"{info['badge']} {stage} Stage ({info['duration']} days)", expanded=True):
            st.write(f"**Duration:** {info['duration']} days")
            st.write("**Daily Requirements:**")
            for rule in info['rules']:
                st.write(f"• {rule}")
            st.write("**Penalty:** Skip any rule → Pay daily savings to your future project fund")
    
    st.info("💡 **Rule:** If you skip any requirement, pay your daily pocket money to savings. Access only after 105 days for your first project!")
    
    if st.button("🎯 Start My Journey", use_container_width=True):
        st.session_state.page = "profile_setup"
        st.rerun()

def profile_setup():
    st.markdown('<div class="main-header"><h1>👤 Setup Your Profile</h1><p>Personalize your challenge journey</p></div>', unsafe_allow_html=True)
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            field = st.selectbox("🎯 Your Field", FIELDS)
            goal = st.text_input("🎯 Your Career Goal", placeholder="e.g., Software Engineer, Doctor, etc.")
        
        with col2:
            selected_stage = st.selectbox("📊 Challenge Stage", list(CHALLENGE_STAGES.keys()))
            distractions = st.multiselect("📵 Your Distractions", DISTRACTIONS)
        
        # Show selected stage info with proper colors
        if selected_stage:
            stage_info = CHALLENGE_STAGES[selected_stage]
            st.markdown(f'<div class="stage-info-box">'
                       f'<h3>🎯 {selected_stage} Stage Selected</h3>'
                       f'<p><strong>Duration:</strong> {stage_info["duration"]} days | <strong>Badge:</strong> {stage_info["badge"]}</p>'
                       f'</div>', unsafe_allow_html=True)
        
        if st.form_submit_button("💾 Save Profile & Start Challenge", use_container_width=True):
            st.session_state.profiles_db[st.session_state.user] = {
                'field': field,
                'goal': goal, 
                'stage': selected_stage,
                'distractions': distractions,
                'join_date': datetime.now().strftime("%Y-%m-%d")
            }
            
            progress = st.session_state.progress_db[st.session_state.user]
            progress['current_stage'] = selected_stage
            progress['start_date'] = datetime.now().strftime("%Y-%m-%d")
            progress['days_completed'] = 0
            
            st.success("✅ Profile saved successfully!")
            st.session_state.page = "daily_tracking"
            st.rerun()

def daily_tracking():
    user = st.session_state.user
    profile = st.session_state.profiles_db.get(user, {})
    progress = st.session_state.progress_db.get(user, {})
    
    st.markdown(f'<div class="main-header"><h1>📝 Daily Progress Tracking</h1><p>Stay consistent, achieve greatness</p></div>', unsafe_allow_html=True)
    
    # 4 Stats Header with proper colors
    current_stage = profile.get('stage', 'Not Set')
    stage_info = CHALLENGE_STAGES.get(current_stage, {'duration': 0})
    days_completed = progress.get('days_completed', 0)
    days_left = max(0, stage_info['duration'] - days_completed)
    streak_days = progress.get('streak_days', 0)
    total_savings = progress.get('total_savings', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="stat-box">'
                   f'<h3>Current Stage</h3>'
                   f'<h2>{current_stage}</h2>'
                   f'</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="stat-box">'
                   f'<h3>Days Left</h3>'
                   f'<h2>{days_left}</h2>'
                   f'</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="stat-box">'
                   f'<h3>Streak Days</h3>'
                   f'<h2>{streak_days}</h2>'
                   f'</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'<div class="stat-box">'
                   f'<h3>Total Savings</h3>'
                   f'<h2>${total_savings}</h2>'
                   f'</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("✅ Today's Challenge Checklist")
    
    with st.form("daily_checklist"):
        tasks_completed = []
        current_stage = profile.get('stage')
        
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
        
        penalty_amount = st.number_input("💰 Penalty Amount (if you skipped any task)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
        
        if st.form_submit_button("📅 Submit Today's Progress", use_container_width=True):
            completed_count = sum(tasks_completed)
            total_tasks = len(tasks_completed)
            
            if completed_count == total_tasks:
                # Perfect day
                progress['days_completed'] += 1
                progress['streak_days'] += 1
                st.markdown('<div class="success-box"><h3>🎉 Perfect Day Completed!</h3><p>All tasks completed successfully</p></div>', unsafe_allow_html=True)
                st.balloons()
                
                # Check stage completion
                if progress['days_completed'] >= stage_info['duration']:
                    st.markdown('<div class="success-box"><h2>🏆 Stage Completed!</h2><p>You have successfully completed this stage!</p></div>', unsafe_allow_html=True)
                    if st.button("🚀 Upgrade to Next Stage"):
                        upgrade_stage(current_stage)
                
                st.info("🌙 **Final task for today:** Set a motivational wallpaper to see when you wake up tomorrow!")
                
            elif completed_count >= total_tasks - 2 and penalty_amount > 0:
                # Day accepted with penalty
                progress['days_completed'] += 1
                progress['streak_days'] = 0
                progress['total_savings'] += penalty_amount
                st.markdown(f'<div class="warning-box"><h3>⚠️ Day Accepted with Penalty</h3><p>${penalty_amount:.2f} added to your savings. Total: ${progress["total_savings"]:.2f}</p></div>', unsafe_allow_html=True)
                
            else:
                # Day not accepted
                st.markdown('<div class="error-box"><h3>❌ Day Not Accepted</h3><p>You missed too many tasks. Please try again tomorrow!</p></div>', unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

def upgrade_stage(current_stage):
    stages = list(CHALLENGE_STAGES.keys())
    current_index = stages.index(current_stage)
    
    if current_index < len(stages) - 1:
        next_stage = stages[current_index + 1]
        st.session_state.profiles_db[st.session_state.user]['stage'] = next_stage
        st.session_state.progress_db[st.session_state.user]['days_completed'] = 0
        st.session_state.progress_db[st.session_state.user]['streak_days'] = 0
        st.success(f"🎉 Upgraded to {next_stage} Stage!")
        st.rerun()
    else:
        st.success("🎊 Congratulations! You've completed all stages!")

# ===== MAIN APP =====
def main():
    init_session()
    
    if st.session_state.user is None:
        login_page()
    else:
        # Sidebar navigation
        with st.sidebar:
            st.write(f"**User:** {st.session_state.user}")
            if st.button("🚪 Logout"):
                st.session_state.user = None
                st.session_state.page = "login"
                st.rerun()
            
            st.markdown("---")
            pages = {
                "Dashboard": "dashboard",
                "Challenge Preview": "challenge_preview", 
                "Challenge Rules": "challenge_rules",
                "Profile Setup": "profile_setup",
                "Daily Tracking": "daily_tracking"
            }
            
            for page_name, page_id in pages.items():
                if st.button(page_name, use_container_width=True):
                    st.session_state.page = page_id
                    st.rerun()
        
        # Display current page
        pages = {
            "dashboard": dashboard,
            "challenge_preview": challenge_preview,
            "challenge_rules": challenge_rules,
            "profile_setup": profile_setup,
            "daily_tracking": daily_tracking,
            "login": login_page
        }
        
        current_page = st.session_state.page
        if current_page in pages:
            pages[current_page]()
        else:
            st.session_state.page = "dashboard"
            st.rerun()

if __name__ == "__main__":
    main()
