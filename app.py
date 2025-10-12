import pandas as pd
import numpy as np
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
    }
    .stat-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #1E90FF;
        margin: 0.2rem;
    }
    .stat-box h3 {
        color: #1E90FF !important;
        margin: 0;
        font-size: 0.8rem;
    }
    .stat-box h2 {
        color: #1a237e !important;
        margin: 0.3rem 0 0 0;
        font-size: 1.4rem;
    }
    .success-box { background: #4CAF50; color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; }
    .warning-box { background: #FF9800; color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; }
    .error-box { background: #f44336; color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; }
    .data-record {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #1E90FF;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ===== QUICK INITIALIZATION =====
if 'users_db' not in st.session_state:
    st.session_state.users_db = {}
if 'profiles_db' not in st.session_state:
    st.session_state.profiles_db = {}
if 'progress_db' not in st.session_state:
    st.session_state.progress_db = {}
if 'daily_records' not in st.session_state:
    st.session_state.daily_records = {}
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = "login"

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ===== FAST ML PREDICTION =====
def quick_performance_predict(hours, distractions, habits):
    """Ultra-fast performance prediction without heavy ML"""
    base_score = (hours * 15) - (distractions * 7)
    
    # Add habit contributions
    habit_bonus = 0
    for habit, value in habits.items():
        if value == "Yes":
            if 'sugar' in habit: habit_bonus += 25
            elif 'junk' in habit: habit_bonus += 20
            elif 'water' in habit: habit_bonus += 15
            elif 'sleep' in habit: habit_bonus += 30
            elif 'exercise' in habit: habit_bonus += 15
            elif 'wakeup' in habit: habit_bonus += 10
        else:
            if 'sugar' in habit: habit_bonus -= 10
            elif 'junk' in habit: habit_bonus -= 5
            elif 'water' in habit: habit_bonus -= 5
            elif 'sleep' in habit: habit_bonus -= 15
            elif 'exercise' in habit: habit_bonus -= 5
    
    total_score = base_score + habit_bonus
    percentile = max(1, min(99, 100 - (total_score / 3)))
    return percentile

def quick_performance_breakdown(hours, distractions, habits):
    """Fast performance breakdown without heavy calculations"""
    breakdown = {}
    
    # Study hours percentile (simplified)
    breakdown['Study Hours'] = max(10, min(95, (hours / 12) * 100))
    
    # Distraction control
    breakdown['Distraction Control'] = max(10, 100 - (distractions / 15) * 100)
    
    # Habit percentiles
    habit_map = {
        'avoid_sugar': 'Sugar Avoidance',
        'avoid_junk_food': 'Junk Food Avoidance',
        'drink_5L_water': 'Water Intake', 
        'sleep_early': 'Sleep Schedule',
        'exercise_daily': 'Exercise Routine',
        'wakeup_early': 'Wake-up Time'
    }
    
    for habit_key, habit_name in habit_map.items():
        if habits.get(habit_key) == "Yes":
            breakdown[habit_name] = 85  # Good habit
        else:
            breakdown[habit_name] = 35  # Poor habit
    
    return breakdown

# ===== APP DATA =====
CHALLENGE_STAGES = {
    'Silver': {'duration': 15, 'badge': '🥈', 'rules': ['2 hours in field', 'Avoid distractions', 'Fill form daily']},
    'Platinum': {'duration': 30, 'badge': '🥇', 'rules': ['4 hours in field', 'Avoid distractions', '1 hour exercise', '5L water', 'Fill form']},
    'Gold': {'duration': 60, 'badge': '🏆', 'rules': ['6 hours in field', 'Avoid distractions', '1 hour exercise', '5L water', 'Wake up 4-5am', 'Sleep 8-9pm', 'No junk food', 'No sugar']}
}

FIELDS = ["Programming", "Engineering", "Medicine", "Business", "Sports", "Arts", "Science"]
DISTRACTIONS = ["Social Media", "Procrastination", "Video Games", "TV/Netflix", "Phone", "Laziness"]

# ===== PAGES =====
def login_page():
    st.markdown('<div class="main-header"><h1>🚀 Performance Predictor</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        if st.button("🚀 Login", use_container_width=True):
            if username in st.session_state.users_db and st.session_state.users_db[username] == hash_password(password):
                st.session_state.user = username
                # Initialize user data if not exists
                if username not in st.session_state.profiles_db:
                    st.session_state.profiles_db[username] = {}
                if username not in st.session_state.progress_db:
                    st.session_state.progress_db[username] = {'current_stage': None, 'days_completed': 0, 'streak_days': 0, 'total_savings': 0}
                if username not in st.session_state.daily_records:
                    st.session_state.daily_records[username] = []
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    
    with tab2:
        new_user = st.text_input("👤 New Username")
        new_pwd = st.text_input("🔒 New Password", type="password")
        if st.button("📝 Register", use_container_width=True):
            if new_user in st.session_state.users_db:
                st.error("❌ User exists")
            elif len(new_pwd) < 4:
                st.error("❌ Password too short")
            else:
                st.session_state.users_db[new_user] = hash_password(new_pwd)
                st.success("✅ Registered! Please login")

def dashboard():
    st.markdown(f'<div class="main-header"><h1>👋 Welcome, {st.session_state.user}!</h1></div>', unsafe_allow_html=True)
    
    # Fast Performance Prediction
    st.subheader("📊 Quick Performance Check")
    
    col1, col2 = st.columns(2)
    with col1:
        hours = st.slider("Study Hours", 0.5, 12.0, 5.5)
        distractions = st.slider("Distractions", 0, 15, 5)
    
    with col2:
        habits = {
            'avoid_sugar': st.selectbox("Avoid Sugar", ["Yes", "No"]),
            'avoid_junk_food': st.selectbox("Avoid Junk Food", ["Yes", "No"]),
            'drink_5L_water': st.selectbox("Drink 5L Water", ["Yes", "No"]),
            'sleep_early': st.selectbox("Sleep Early", ["Yes", "No"]),
            'exercise_daily': st.selectbox("Exercise Daily", ["Yes", "No"]),
            'wakeup_early': st.selectbox("Wakeup Early", ["Yes", "No"])
        }

    if st.button("🎯 Check Performance", use_container_width=True):
        # Ultra-fast prediction
        percentile = quick_performance_predict(hours, distractions, habits)
        breakdown = quick_performance_breakdown(hours, distractions, habits)
        
        st.success(f"🎯 Your Performance: Top **{percentile:.1f}%**")
        
        # Simple progress bars instead of chart
        st.subheader("Performance Breakdown")
        for metric, value in breakdown.items():
            st.write(f"**{metric}:** {value:.0f}%")
            st.progress(int(value) / 100)

    # Challenge Section
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
        with st.expander(f"{info['badge']} {stage} Stage ({info['duration']} days)"):
            for rule in info['rules']:
                st.write(f"• {rule}")
            st.write(f"**Penalty:** Skip any rule → Pay daily savings")
    
    if st.button("🎯 Start My Journey", use_container_width=True):
        st.session_state.page = "profile_setup"
        st.rerun()

def profile_setup():
    st.markdown('<div class="main-header"><h1>👤 Setup Profile</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        field = st.selectbox("Your Field", FIELDS)
        goal = st.text_input("Your Goal")
    with col2:
        stage = st.selectbox("Challenge Stage", list(CHALLENGE_STAGES.keys()))
        distractions = st.multiselect("Your Distractions", DISTRACTIONS)
    
    # Show stage info
    if stage:
        info = CHALLENGE_STAGES[stage]
        st.info(f"**{stage} Stage**: {info['duration']} days - {info['badge']}")
    
    if st.button("💾 Save Profile", use_container_width=True):
        st.session_state.profiles_db[st.session_state.user] = {
            'field': field, 'goal': goal, 'stage': stage, 'distractions': distractions
        }
        st.session_state.progress_db[st.session_state.user]['current_stage'] = stage
        st.success("✅ Profile saved!")
        st.session_state.page = "daily_tracking"
        st.rerun()

def daily_tracking():
    user = st.session_state.user
    profile = st.session_state.profiles_db.get(user, {})
    progress = st.session_state.progress_db.get(user, {})
    
    st.markdown('<div class="main-header"><h1>📝 Daily Tracking</h1></div>', unsafe_allow_html=True)
    
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
    
    # Show previous records
    if st.session_state.daily_records.get(user):
        st.subheader("📋 Your Records")
        for record in reversed(st.session_state.daily_records[user][-3:]):
            status = "✅ Perfect" if record['perfect'] else f"⚠️ Penalty: ${record['penalty']}"
            st.markdown(f"""
            <div class="data-record">
                <strong>{record['date']}</strong> | {status}<br>
                Completed: {record['completed']}/{record['total']} tasks
            </div>
            """, unsafe_allow_html=True)
    
    # Daily Checklist
    st.subheader("✅ Today's Tasks")
    
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
        tasks.append(st.checkbox("5L water"))
        tasks.append(st.checkbox("Filling this form"))
    elif stage == 'Gold':
        tasks.append(st.checkbox("6 hours in field"))
        tasks.append(st.checkbox("Avoided distractions"))
        tasks.append(st.checkbox("1 hour exercise"))
        tasks.append(st.checkbox("5L water"))
        tasks.append(st.checkbox("Wake up early"))
        tasks.append(st.checkbox("Sleep early"))
        tasks.append(st.checkbox("No junk food"))
        tasks.append(st.checkbox("No sugar"))
    
    penalty = st.number_input("Penalty $ (if skipped)", 0.0, 100.0, 0.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Submit Day", use_container_width=True):
            completed = sum(tasks)
            total = len(tasks)
            perfect = completed == total
            
            # Record data
            record = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'completed': completed,
                'total': total,
                'penalty': penalty,
                'perfect': perfect
            }
            
            if user not in st.session_state.daily_records:
                st.session_state.daily_records[user] = []
            st.session_state.daily_records[user].append(record)
            
            if perfect:
                progress['days_completed'] += 1
                progress['streak_days'] += 1
                st.markdown('<div class="success-box"><h3>🎉 Perfect Day!</h3></div>', unsafe_allow_html=True)
            elif completed >= total - 2 and penalty > 0:
                progress['days_completed'] += 1
                progress['streak_days'] = 0
                progress['total_savings'] += penalty
                st.markdown(f'<div class="warning-box"><h3>⚠️ Day Saved with ${penalty} Penalty</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box"><h3>❌ Day Not Counted</h3></div>', unsafe_allow_html=True)
            
            st.rerun()
    
    with col2:
        if st.button("🔄 Refill Form", use_container_width=True):
            st.info("Form reset! Fill again.")
            st.rerun()
    
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

# ===== MAIN APP =====
def main():
    if st.session_state.user is None:
        login_page()
    else:
        # Simple sidebar
        with st.sidebar:
            st.write(f"User: {st.session_state.user}")
            if st.button("Logout"):
                st.session_state.user = None
                st.session_state.page = "login"
                st.rerun()
        
        # Page routing
        pages = {
            "dashboard": dashboard,
            "challenge_preview": challenge_preview,
            "challenge_rules": challenge_rules,
            "profile_setup": profile_setup,
            "daily_tracking": daily_tracking
        }
        
        page = st.session_state.page
        if page in pages:
            pages[page]()
        else:
            st.session_state.page = "dashboard"
            st.rerun()

if __name__ == "__main__":
    main()
