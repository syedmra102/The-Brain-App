import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

# ===== PROFESSIONAL CSS WITH PROPER CONTRAST =====
st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: white;
    }
    
    /* HEADERS - WHITE TEXT ON BLUE BACKGROUND */
    .main-header {
        background: linear-gradient(135deg, #1E90FF 0%, #0066CC 100%);
        color: white !important;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1, .main-header p {
        color: white !important;
    }
    
    /* STAT BOXES - DARK TEXT ON WHITE BACKGROUND */
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
    
    /* STATUS BOXES - WHITE TEXT ON COLORED BACKGROUNDS */
    .success-box { 
        background: #4CAF50; 
        color: white !important; 
        padding: 1rem; 
        border-radius: 10px; 
        margin: 1rem 0; 
    }
    .warning-box { 
        background: #FF9800; 
        color: white !important; 
        padding: 1rem; 
        border-radius: 10px; 
        margin: 1rem 0; 
    }
    .error-box { 
        background: #f44336; 
        color: white !important; 
        padding: 1rem; 
        border-radius: 10px; 
        margin: 1rem 0; 
    }
    
    /* DATA RECORDS - DARK TEXT ON LIGHT BACKGROUND */
    .data-record {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #1E90FF;
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: black !important;
    }
    
    /* CHECKBOXES - BLACK TEXT ON WHITE BACKGROUND */
    .stCheckbox > label {
        color: black !important;
        font-weight: 500;
    }
    
    /* ALL REGULAR TEXT - BLACK ON WHITE */
    .stApp {
        color: black !important;
    }
    
    /* FORM LABELS AND TEXT */
    .stTextInput > label, .stSelectbox > label, .stNumberInput > label, .stMultiselect > label {
        color: black !important;
        font-weight: 500;
    }
    
    /* SIDEBAR TEXT */
    .css-1d391kg {
        color: black !important;
    }
    
    /* TABS AND BUTTONS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1E90FF;
        color: white !important;
    }
    
    /* INPUT FIELDS */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: white;
        color: black !important;
        border: 1px solid #ccc;
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

# ===== FAST ML PREDICTION WITH BLUE CHART =====
def quick_performance_predict(hours, distractions, habits):
    """Ultra-fast performance prediction"""
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
    """Performance breakdown for blue chart"""
    breakdown = {}
    
    # Study hours percentile
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

def create_blue_chart(breakdown, overall_percentile):
    """Create your exact blue bar chart"""
    fig, ax = plt.subplots(figsize=(12, 8))
    features = list(breakdown.keys())
    percentiles = list(breakdown.values())
    
    # Your exact blue color
    bars = ax.bar(features, percentiles, color='#1E90FF', edgecolor='darkblue', alpha=0.8)
    
    # Add labels on bars
    for bar, percentile in zip(bars, percentiles):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'Top {percentile:.1f}%', ha='center', va='bottom', 
                fontweight='bold', fontsize=9, color='#1a237e')
    
    ax.set_xlabel('Performance Features', fontweight='bold', fontsize=12, color='black')
    ax.set_ylabel('Performance Percentile', fontweight='bold', fontsize=12, color='black')
    ax.set_title(f'PERFORMANCE BREAKDOWN ANALYSIS (Top {overall_percentile:.1f}%)', 
                 fontweight='bold', fontsize=14, color='black')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    return fig

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
    st.markdown('<div class="main-header"><h1>🚀 Performance Predictor</h1><p>Become the Top 1% in Your Field</p></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        if st.button("🚀 Login", use_container_width=True):
            if username in st.session_state.users_db and st.session_state.users_db[username] == hash_password(password):
                st.session_state.user = username
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
        st.subheader("Create New Account")
        new_user = st.text_input("👤 Choose Username")
        new_pwd = st.text_input("🔒 Choose Password", type="password")
        confirm_pwd = st.text_input("🔒 Confirm Password", type="password")
        if st.button("📝 Register", use_container_width=True):
            if new_user in st.session_state.users_db:
                st.error("❌ User exists")
            elif len(new_pwd) < 4:
                st.error("❌ Password too short")
            elif new_pwd != confirm_pwd:
                st.error("❌ Passwords don't match")
            else:
                st.session_state.users_db[new_user] = hash_password(new_pwd)
                st.success("✅ Registered! Please login")

def dashboard():
    st.markdown(f'<div class="main-header"><h1>👋 Welcome, {st.session_state.user}!</h1><p>Track your performance and achieve excellence</p></div>', unsafe_allow_html=True)
    
    # Performance Prediction
    st.subheader("📊 Performance Prediction Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        hours = st.slider("🕒 Study Hours", 0.5, 12.0, 5.5)
        distractions = st.slider("📵 Distractions", 0, 15, 5)
    
    with col2:
        habits = {
            'avoid_sugar': st.selectbox("🍭 Avoid Sugar", ["Yes", "No"]),
            'avoid_junk_food': st.selectbox("🍔 Avoid Junk Food", ["Yes", "No"]),
            'drink_5L_water': st.selectbox("💧 Drink 5L Water", ["Yes", "No"]),
            'sleep_early': st.selectbox("😴 Sleep Early", ["Yes", "No"]),
            'exercise_daily': st.selectbox("💪 Exercise Daily", ["Yes", "No"]),
            'wakeup_early': st.selectbox("🌅 Wakeup Early", ["Yes", "No"])
        }

    if st.button("🎯 Predict My Performance", use_container_width=True):
        # Fast prediction
        percentile = quick_performance_predict(hours, distractions, habits)
        breakdown = quick_performance_breakdown(hours, distractions, habits)
        
        st.success(f"🎯 Your Overall Performance: Top **{percentile:.1f}%**")
        
        # Show your blue bar chart
        fig = create_blue_chart(breakdown, percentile)
        st.pyplot(fig)

    # Challenge Section
    st.markdown("---")
    st.markdown("### 🎯 Challenge of 105 Days")
    st.write("**Become the Top 1% in Your Field**")
    
    if st.button("🚀 Start Challenge", use_container_width=True):
        st.session_state.page = "challenge_preview"
        st.rerun()

def challenge_preview():
    st.markdown('<div class="main-header"><h1>🌟 Your Future Self</h1><p>After completing the 105-day challenge</p></div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="main-header"><h1>📋 Challenge Stages</h1><p>Three stages to excellence</p></div>', unsafe_allow_html=True)
    
    for stage, info in CHALLENGE_STAGES.items():
        with st.expander(f"{info['badge']} {stage} Stage ({info['duration']} days)"):
            st.write("**Daily Requirements:**")
            for rule in info['rules']:
                st.write(f"• {rule}")
            st.write("**Penalty:** Skip any rule → Pay daily savings")
    
    if st.button("🎯 Start My Journey", use_container_width=True):
        st.session_state.page = "profile_setup"
        st.rerun()

def profile_setup():
    st.markdown('<div class="main-header"><h1>👤 Setup Profile</h1><p>Personalize your challenge journey</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        field = st.selectbox("🎯 Your Field", FIELDS)
        goal = st.text_input("🎓 Your Goal", placeholder="e.g., Software Engineer, Doctor")
    with col2:
        stage = st.selectbox("📊 Challenge Stage", list(CHALLENGE_STAGES.keys()))
        distractions = st.multiselect("📵 Your Distractions", DISTRACTIONS)
    
    # Show stage info
    if stage:
        info = CHALLENGE_STAGES[stage]
        st.info(f"**{stage} Stage Selected** - {info['duration']} days - {info['badge']}")
    
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
    
    st.markdown('<div class="main-header"><h1>📝 Daily Progress Tracking</h1><p>Stay consistent, achieve greatness</p></div>', unsafe_allow_html=True)
    
    # 4 Stats Header
    stage = profile.get('stage', 'Not set')
    stage_info = CHALLENGE_STAGES.get(stage, {'duration': 0})
    days_left = stage_info['duration'] - progress.get('days_completed', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-box"><h3>Current Stage</h3><h2>{stage}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-box"><h3>Days Left</h3><h2>{days_left}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-box"><h3>Streak Days</h3><h2>{progress.get("streak_days", 0)}</h2></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-box"><h3>Total Savings</h3><h2>${progress.get("total_savings", 0)}</h2></div>', unsafe_allow_html=True)
    
    # Show previous records
    if st.session_state.daily_records.get(user):
        st.subheader("📋 Your Previous Records")
        for record in reversed(st.session_state.daily_records[user][-5:]):
            status = "✅ Perfect Day" if record['perfect'] else f"⚠️ Penalty: ${record['penalty']}"
            st.markdown(f"""
            <div class="data-record">
                <strong>{record['date']}</strong> | {status}<br>
                Completed: {record['completed']}/{record['total']} tasks
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("✅ Today's Challenge Checklist")
    
    # Daily Checklist with proper black text
    with st.form("daily_checklist"):
        st.markdown("**Check all tasks you completed today:**")
        
        tasks = []
        stage = profile.get('stage')
        
        if stage == 'Silver':
            tasks.append(st.checkbox("✅ Gave 2 hours in my field today", value=False))
            tasks.append(st.checkbox("✅ Avoided all distractions today", value=False))
            tasks.append(st.checkbox("✅ Filling this form at night", value=False))
        elif stage == 'Platinum':
            tasks.append(st.checkbox("✅ Gave 4 hours in my field today", value=False))
            tasks.append(st.checkbox("✅ Avoided all distractions today", value=False))
            tasks.append(st.checkbox("✅ Completed 1 hour exercise", value=False))
            tasks.append(st.checkbox("✅ Drank 5L water today", value=False))
            tasks.append(st.checkbox("✅ Filling this form at night", value=False))
        elif stage == 'Gold':
            tasks.append(st.checkbox("✅ Gave 6 hours in my field today", value=False))
            tasks.append(st.checkbox("✅ Avoided all distractions today", value=False))
            tasks.append(st.checkbox("✅ Completed 1 hour exercise", value=False))
            tasks.append(st.checkbox("✅ Drank 5L water today", value=False))
            tasks.append(st.checkbox("✅ Woke up early (4am/5am)", value=False))
            tasks.append(st.checkbox("✅ Will sleep early (8pm/9pm)", value=False))
            tasks.append(st.checkbox("✅ Avoided junk food today", value=False))
            tasks.append(st.checkbox("✅ Avoided sugar today", value=False))
        
        penalty_amount = st.number_input("💰 Penalty Amount (if you skipped any task)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
        
        submitted = st.form_submit_button("📅 Submit Today's Progress", use_container_width=True)
        
        if submitted:
            completed = sum(tasks)
            total = len(tasks)
            perfect = completed == total
            
            # Record data
            record = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'completed': completed,
                'total': total,
                'penalty': penalty_amount,
                'perfect': perfect
            }
            
            if user not in st.session_state.daily_records:
                st.session_state.daily_records[user] = []
            st.session_state.daily_records[user].append(record)
            
            if perfect:
                progress['days_completed'] += 1
                progress['streak_days'] += 1
                st.markdown('<div class="success-box"><h3>🎉 Perfect Day Completed!</h3></div>', unsafe_allow_html=True)
                st.balloons()
            elif completed >= total - 2 and penalty_amount > 0:
                progress['days_completed'] += 1
                progress['streak_days'] = 0
                progress['total_savings'] += penalty_amount
                st.markdown(f'<div class="warning-box"><h3>⚠️ Day Accepted with ${penalty_amount} Penalty</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box"><h3>❌ Day Not Accepted</h3></div>', unsafe_allow_html=True)
            
            st.rerun()
    
    # Refill form button
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Fill Form Again", use_container_width=True):
            st.info("Form reset! You can submit again.")
            st.rerun()
    with col2:
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
            st.write(f"**User:** {st.session_state.user}")
            if st.button("🚪 Logout"):
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
