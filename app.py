import pandas as pd
import numpy as np
import streamlit as st
import hashlib
from datetime import datetime

# ===== CONFIG =====
st.set_page_config(
    page_title="Performance Predictor",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== SIMPLE CSS =====
st.markdown("""
<style>
    .main-header {
        background: #1E90FF;
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #1E90FF;
        margin: 0.5rem;
    }
    .success-box { background: #4CAF50; color: white; padding: 1rem; border-radius: 10px; }
    .warning-box { background: #FF9800; color: white; padding: 1rem; border-radius: 10px; }
    .error-box { background: #f44336; color: white; padding: 1rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ===== SIMPLE AUTH =====
def init_session():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'users_db' not in st.session_state:
        st.session_state.users_db = {}
    if 'profiles_db' not in st.session_state:
        st.session_state.profiles_db = {}
    if 'progress_db' not in st.session_state:
        st.session_state.progress_db = {}

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ===== QUICK ML MODEL =====
@st.cache_data
def get_ml_model():
    # Simplified ML setup for speed
    np.random.seed(42)
    n_samples = 200
    
    data = {
        'hours': np.clip(np.random.normal(5.5, 2, n_samples), 0.5, 10),
        'distraction_count': np.random.randint(0, 15, n_samples),
        'avoid_sugar': np.random.choice(['Yes', 'No'], n_samples, p=[0.4, 0.6]),
        'avoid_junk_food': np.random.choice(['Yes', 'No'], n_samples, p=[0.45, 0.55]),
        'drink_5L_water': np.random.choice(['Yes', 'No'], n_samples, p=[0.35, 0.65]),
        'exercise_daily': np.random.choice(['Yes', 'No'], n_samples),
        'sleep_early': np.random.choice(['Yes', 'No'], n_samples, p=[0.4, 0.6]),
        'wakeup_early': np.random.choice(['Yes', 'No'], n_samples, p=[0.3, 0.7])
    }
    
    df = pd.DataFrame(data)
    
    # Simple percentile calculation (no heavy ML)
    def calculate_percentile(row):
        score = (row['hours'] * 15) - (row['distraction_count'] * 7)
        score += 25 if row['avoid_sugar'] == 'Yes' else -10
        score += 20 if row['avoid_junk_food'] == 'Yes' else -5
        score += 15 if row['drink_5L_water'] == 'Yes' else -5
        score += 30 if row['sleep_early'] == 'Yes' else -15
        score += 15 if row['exercise_daily'] == 'Yes' else -5
        score += 10 if row['wakeup_early'] == 'Yes' else 0
        percentile = max(1, min(99, 100 - (score / 3)))
        return percentile
    
    df['top_percentile'] = df.apply(calculate_percentile, axis=1)
    return df

# ===== APP DATA =====
CHALLENGE_STAGES = {
    'Silver': {'duration': 15, 'badge': '🥈', 'rules': ['2 hours in field', 'Avoid distractions', 'Fill form daily']},
    'Platinum': {'duration': 30, 'badge': '🥇', 'rules': ['4 hours in field', 'Avoid distractions', '1 hour exercise', '5L water', 'Fill form']},
    'Gold': {'duration': 60, 'badge': '🏆', 'rules': ['6 hours in field', 'Avoid distractions', '1 hour exercise', '5L water', 'Wake up 4-5am', 'Sleep 8-9pm', 'No junk food', 'No sugar']}
}

FIELDS = ["Programming", "Engineering", "Medicine", "Business", "Sports", "Arts", "Science"]
DISTRACTIONS = ["Social Media", "Procrastination", "Video Games", "TV", "Phone", "Laziness", "Late Sleep"]

# ===== PAGES =====
def login_page():
    st.markdown('<div class="main-header"><h1>🚀 Performance Predictor</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if user in st.session_state.users_db and st.session_state.users_db[user] == hash_password(pwd):
                    st.session_state.user = user
                    init_user_data(user)
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        with st.form("register"):
            new_user = st.text_input("New Username")
            new_pwd = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                if new_user in st.session_state.users_db:
                    st.error("User exists")
                elif len(new_pwd) < 4:
                    st.error("Password too short")
                else:
                    st.session_state.users_db[new_user] = hash_password(new_pwd)
                    init_user_data(new_user)
                    st.success("Registered! Please login")

def init_user_data(user):
    if user not in st.session_state.profiles_db:
        st.session_state.profiles_db[user] = {}
    if user not in st.session_state.progress_db:
        st.session_state.progress_db[user] = {
            'current_stage': None,
            'days_completed': 0,
            'streak_days': 0,
            'total_savings': 0,
            'start_date': None
        }

def dashboard():
    st.markdown(f'<div class="main-header"><h1>👋 Welcome, {st.session_state.user}</h1></div>', unsafe_allow_html=True)
    
    # Quick Performance Prediction
    st.subheader("📊 Quick Performance Check")
    col1, col2 = st.columns(2)
    with col1:
        hours = st.slider("Study Hours", 0.5, 12.0, 5.5)
        distractions = st.slider("Distractions", 0, 15, 5)
    with col2:
        avoid_sugar = st.selectbox("Avoid Sugar", ["Yes", "No"])
        exercise = st.selectbox("Exercise Daily", ["Yes", "No"])
    
    if st.button("Check Performance"):
        # Simple calculation instead of heavy ML
        base_score = (hours * 15) - (distractions * 7)
        base_score += 25 if avoid_sugar == "Yes" else -10
        base_score += 15 if exercise == "Yes" else -5
        percentile = max(1, min(99, 100 - (base_score / 3)))
        
        st.success(f"🎯 Your Performance: Top {percentile:.1f}%")
        
        # Simple progress bars
        st.subheader("Performance Breakdown")
        metrics = {
            "Study Hours": min(100, (hours / 10) * 100),
            "Focus": max(1, 100 - (distractions / 15) * 100),
            "Discipline": 80 if avoid_sugar == "Yes" else 30,
            "Fitness": 85 if exercise == "Yes" else 35
        }
        
        for metric, value in metrics.items():
            st.write(f"{metric}: {value:.0f}%")
            st.progress(int(value))
    
    # Challenge Invite
    st.markdown("---")
    st.markdown("### 🎯 Challenge of 105 Days")
    st.write("**Become the Top 1% in Your Field**")
    
    if st.button("🚀 Start Challenge", use_container_width=True):
        st.session_state.page = "challenge_preview"
        st.rerun()

def challenge_preview():
    st.markdown('<div class="main-header"><h1>🌟 Your Future Self</h1></div>', unsafe_allow_html=True)
    
    benefits = [
        "**Healthy Diet** - No sugar, no junk food, 5L water daily",
        "**Early Rising** - Natural wake up at 4 AM",
        "**Peak Fitness** - 1 hour daily exercise",
        "**Expert Skills** - Deep knowledge in your field",
        "**Laser Focus** - Distractions eliminated",
        "**Wealth Mindset** - Financial intelligence",
        "**Emotional Mastery** - High EQ & resilience"
    ]
    
    for benefit in benefits:
        st.write(f"✅ {benefit}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 See Rules", use_container_width=True):
            st.session_state.page = "challenge_rules"
            st.rerun()
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

def challenge_rules():
    st.markdown('<div class="main-header"><h1>📋 Challenge Stages</h1></div>', unsafe_allow_html=True)
    
    for stage, info in CHALLENGE_STAGES.items():
        with st.expander(f"{info['badge']} {stage} Stage ({info['duration']} days)", expanded=True):
            for rule in info['rules']:
                st.write(f"• {rule}")
            st.write(f"**Penalty:** Skip any rule → Pay daily savings")
    
    if st.button("🎯 Start My Journey", use_container_width=True):
        st.session_state.page = "profile_setup"
        st.rerun()

def profile_setup():
    st.markdown('<div class="main-header"><h1>👤 Setup Profile</h1></div>', unsafe_allow_html=True)
    
    with st.form("profile"):
        col1, col2 = st.columns(2)
        with col1:
            field = st.selectbox("Your Field", FIELDS)
            goal = st.text_input("Your Goal (e.g., Doctor)")
        with col2:
            stage = st.selectbox("Challenge Stage", list(CHALLENGE_STAGES.keys()))
            distractions = st.multiselect("Your Distractions", DISTRACTIONS)
        
        # Show selected stage info
        if stage:
            info = CHALLENGE_STAGES[stage]
            st.info(f"**{stage} Stage**: {info['duration']} days - {info['badge']}")
        
        if st.form_submit_button("💾 Save Profile"):
            st.session_state.profiles_db[st.session_state.user] = {
                'field': field, 'goal': goal, 'stage': stage, 'distractions': distractions
            }
            st.session_state.progress_db[st.session_state.user]['current_stage'] = stage
            st.session_state.progress_db[st.session_state.user]['start_date'] = datetime.now().strftime("%Y-%m-%d")
            st.success("Profile saved!")
            st.session_state.page = "daily_track"
            st.rerun()

def daily_tracking():
    user = st.session_state.user
    profile = st.session_state.profiles_db.get(user, {})
    progress = st.session_state.progress_db.get(user, {})
    
    st.markdown(f'<div class="main-header"><h1>📝 Daily Tracking</h1></div>', unsafe_allow_html=True)
    
    # 4 Stats Header
    stage = profile.get('stage', 'Not set')
    stage_info = CHALLENGE_STAGES.get(stage, {'duration': 0})
    days_left = stage_info['duration'] - progress.get('days_completed', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-box"><h3>Stage</h3><h2>{stage}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-box"><h3>Days Left</h3><h2>{days_left}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-box"><h3>Streak</h3><h2>{progress.get("streak_days", 0)}</h2></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-box"><h3>Savings</h3><h2>${progress.get("total_savings", 0)}</h2></div>', unsafe_allow_html=True)
    
    # Daily Checklist
    st.subheader("✅ Today's Tasks")
    
    with st.form("daily_check"):
        tasks = []
        stage = profile.get('stage')
        
        if stage == 'Silver':
            tasks.append(st.checkbox("2 hours in field"))
            tasks.append(st.checkbox("Avoided distractions"))
            tasks.append(st.checkbox("Filling this form"))
        elif stage == 'Platinum':
            tasks.append(st.checkbox("4 hours in field"))
            tasks.append(st.checkbox("Avoided distractions"))
            tasks.append(st.checkbox("1 hour exercise"))
            tasks.append(st.checkbox("Drank 5L water"))
            tasks.append(st.checkbox("Filling this form"))
        elif stage == 'Gold':
            tasks.append(st.checkbox("6 hours in field"))
            tasks.append(st.checkbox("Avoided distractions"))
            tasks.append(st.checkbox("1 hour exercise"))
            tasks.append(st.checkbox("Drank 5L water"))
            tasks.append(st.checkbox("Woke up early"))
            tasks.append(st.checkbox("Sleep early"))
            tasks.append(st.checkbox("No junk food"))
            tasks.append(st.checkbox("No sugar"))
        
        penalty = st.number_input("Penalty $ (if skipped tasks)", 0.0, 100.0, 0.0)
        
        if st.form_submit_button("📅 Submit Day"):
            completed = sum(tasks)
            total = len(tasks)
            
            if completed == total:
                progress['days_completed'] += 1
                progress['streak_days'] += 1
                st.markdown('<div class="success-box"><h3>🎉 Perfect Day!</h3></div>', unsafe_allow_html=True)
                st.balloons()
            elif completed >= total - 2 and penalty > 0:
                progress['days_completed'] += 1
                progress['streak_days'] = 0
                progress['total_savings'] += penalty
                st.markdown(f'<div class="warning-box"><h3>⚠️ Day Saved with ${penalty} Penalty</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box"><h3>❌ Day Not Counted</h3></div>', unsafe_allow_html=True)
            
            # Check stage completion
            if progress['days_completed'] >= stage_info['duration']:
                st.balloons()
                st.markdown('<div class="success-box"><h2>🏆 Stage Complete!</h2></div>', unsafe_allow_html=True)
                if st.button("🚀 Upgrade Stage"):
                    upgrade_stage(stage)
    
    if st.button("← Back to Profile"):
        st.session_state.page = "dashboard"
        st.rerun()

def upgrade_stage(current_stage):
    stages = list(CHALLENGE_STAGES.keys())
    current_idx = stages.index(current_stage)
    if current_idx < len(stages) - 1:
        new_stage = stages[current_idx + 1]
        st.session_state.profiles_db[st.session_state.user]['stage'] = new_stage
        st.session_state.progress_db[st.session_state.user]['days_completed'] = 0
        st.session_state.progress_db[st.session_state.user]['streak_days'] = 0
        st.success(f"Upgraded to {new_stage}!")
        st.rerun()

# ===== MAIN APP =====
def main():
    init_session()
    
    if 'page' not in st.session_state:
        st.session_state.page = "dashboard"
    
    if st.session_state.user is None:
        login_page()
    else:
        # Simple navigation
        if st.sidebar.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()
        
        pages = {
            "dashboard": dashboard,
            "challenge_preview": challenge_preview,
            "challenge_rules": challenge_rules,
            "profile_setup": profile_setup,
            "daily_track": daily_tracking
        }
        
        pages[st.session_state.page]()

if __name__ == "__main__":
    main()
