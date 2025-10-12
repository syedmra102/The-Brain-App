import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import hashlib
from datetime import datetime

# Page config
st.set_page_config(page_title="Performance Predictor", layout="centered")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}

# Simple CSS for better appearance
st.markdown("""
<style>
    .main-header {
        background-color: #1E90FF;
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #1E90FF;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ML Prediction Function (Fast)
def predict_performance(hours, distractions, habits):
    score = (hours * 15) - (distractions * 7)
    
    for habit, value in habits.items():
        if value == "Yes":
            if 'sugar' in habit: score += 25
            elif 'junk' in habit: score += 20
            elif 'water' in habit: score += 15
            elif 'sleep' in habit: score += 30
            elif 'exercise' in habit: score += 15
            elif 'wakeup' in habit: score += 10
        else:
            if 'sugar' in habit: score -= 10
            elif 'junk' in habit: score -= 5
            elif 'water' in habit: score -= 5
            elif 'sleep' in habit: score -= 15
            elif 'exercise' in habit: score -= 5
    
    percentile = max(1, min(99, 100 - (score / 3)))
    return percentile

# Challenge Data
CHALLENGE_STAGES = {
    'Silver': {'duration': 15, 'rules': ['2 hours in field', 'Avoid distractions', 'Fill form daily']},
    'Platinum': {'duration': 30, 'rules': ['4 hours in field', 'Avoid distractions', '1 hour exercise', '5L water', 'Fill form']},
    'Gold': {'duration': 60, 'rules': ['6 hours in field', 'Avoid distractions', '1 hour exercise', '5L water', 'Wake up early', 'Sleep early', 'No junk food', 'No sugar']}
}

# Pages
def login_page():
    st.markdown('<div class="main-header"><h1>🚀 Performance Predictor</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in st.session_state.users and st.session_state.users[username] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.session_state.current_page = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    with col2:
        st.subheader("Register")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Register"):
            if new_user in st.session_state.users:
                st.error("Username exists")
            else:
                st.session_state.users[new_user] = hash_password(new_pass)
                st.session_state.user_data[new_user] = {
                    'profile': {},
                    'progress': {'stage': None, 'days_done': 0, 'streak': 0, 'savings': 0},
                    'records': []
                }
                st.success("Registered! Please login")

def dashboard():
    user = st.session_state.current_user
    st.markdown(f'<div class="main-header"><h1>Welcome, {user}!</h1></div>', unsafe_allow_html=True)
    
    # Performance Prediction
    st.subheader("Performance Prediction")
    col1, col2 = st.columns(2)
    
    with col1:
        hours = st.number_input("Study Hours", 0.5, 12.0, 5.5)
        distractions = st.number_input("Distractions", 0, 15, 5)
    
    with col2:
        habits = {
            'avoid_sugar': st.selectbox("Avoid Sugar", ["Yes", "No"]),
            'avoid_junk_food': st.selectbox("Avoid Junk Food", ["Yes", "No"]),
            'drink_5L_water': st.selectbox("Drink 5L Water", ["Yes", "No"]),
            'sleep_early': st.selectbox("Sleep Early", ["Yes", "No"]),
            'exercise_daily': st.selectbox("Exercise Daily", ["Yes", "No"]),
            'wakeup_early': st.selectbox("Wakeup Early", ["Yes", "No"])
        }
    
    if st.button("Predict Performance"):
        percentile = predict_performance(hours, distractions, habits)
        st.success(f"Your Performance: Top {percentile:.1f}%")
        
        # Simple chart
        fig, ax = plt.subplots(figsize=(10, 6))
        metrics = ['Study Hours', 'Focus', 'Discipline', 'Health']
        values = [min(100, (hours/12)*100), max(10, 100-(distractions/15)*100), 75, 65]
        bars = ax.bar(metrics, values, color='#1E90FF')
        ax.set_ylim(0, 100)
        ax.set_ylabel('Score')
        ax.set_title('Performance Breakdown')
        st.pyplot(fig)
    
    # Challenge invitation
    st.markdown("---")
    st.subheader("🎯 105-Day Challenge")
    st.write("Become the top 1% in your field!")
    
    if st.button("Start Challenge"):
        st.session_state.current_page = 'challenge_info'
        st.rerun()

def challenge_info():
    st.markdown('<div class="main-header"><h1>105-Day Challenge</h1></div>', unsafe_allow_html=True)
    
    st.write("""
    ### Transform Your Life:
    - **Healthy Diet** - No sugar, no junk food
    - **Early Rising** - Wake up at 4 AM
    - **Peak Fitness** - Daily exercise
    - **Expert Skills** - Deep knowledge
    - **Laser Focus** - No distractions
    """)
    
    if st.button("See Rules"):
        st.session_state.current_page = 'challenge_rules'
        st.rerun()
    
    if st.button("Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()

def challenge_rules():
    st.markdown('<div class="main-header"><h1>Challenge Rules</h1></div>', unsafe_allow_html=True)
    
    for stage, info in CHALLENGE_STAGES.items():
        with st.expander(f"{stage} Stage ({info['duration']} days)"):
            for rule in info['rules']:
                st.write(f"• {rule}")
    
    if st.button("Start My Journey"):
        st.session_state.current_page = 'setup_profile'
        st.rerun()

def setup_profile():
    st.markdown('<div class="main-header"><h1>Setup Profile</h1></div>', unsafe_allow_html=True)
    
    fields = ["Programming", "Engineering", "Medicine", "Business", "Sports"]
    distractions = ["Social Media", "Procrastination", "Games", "TV", "Phone"]
    
    col1, col2 = st.columns(2)
    with col1:
        field = st.selectbox("Your Field", fields)
        goal = st.text_input("Your Goal")
    with col2:
        stage = st.selectbox("Challenge Stage", list(CHALLENGE_STAGES.keys()))
        user_distractions = st.multiselect("Your Distractions", distractions)
    
    if st.button("Save Profile"):
        user = st.session_state.current_user
        st.session_state.user_data[user]['profile'] = {
            'field': field, 'goal': goal, 'stage': stage, 'distractions': user_distractions
        }
        st.session_state.user_data[user]['progress']['stage'] = stage
        st.success("Profile saved!")
        st.session_state.current_page = 'daily_tracking'
        st.rerun()

def daily_tracking():
    user = st.session_state.current_user
    profile = st.session_state.user_data[user]['profile']
    progress = st.session_state.user_data[user]['progress']
    records = st.session_state.user_data[user]['records']
    
    st.markdown('<div class="main-header"><h1>Daily Tracking</h1></div>', unsafe_allow_html=True)
    
    # Stats header
    stage = profile.get('stage', 'None')
    stage_info = CHALLENGE_STAGES.get(stage, {'duration': 0})
    days_left = stage_info['duration'] - progress['days_done']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-box"><h3>Stage</h3><h2>{stage}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-box"><h3>Days Left</h3><h2>{days_left}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-box"><h3>Streak</h3><h2>{progress["streak"]}</h2></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-box"><h3>Savings</h3><h2>${progress["savings"]}</h2></div>', unsafe_allow_html=True)
    
    # Show records
    if records:
        st.subheader("Your Records")
        for record in records[-3:]:
            st.write(f"{record['date']} - {record['completed']}/{record['total']} tasks")
    
    # Daily form
    st.subheader("Today's Checklist")
    
    tasks = []
    stage = profile.get('stage')
    
    if stage == 'Silver':
        tasks.append(st.checkbox("2 hours in field"))
        tasks.append(st.checkbox("Avoided distractions"))
        tasks.append(st.checkbox("Fill form"))
    elif stage == 'Platinum':
        tasks.append(st.checkbox("4 hours in field"))
        tasks.append(st.checkbox("Avoided distractions"))
        tasks.append(st.checkbox("1 hour exercise"))
        tasks.append(st.checkbox("5L water"))
        tasks.append(st.checkbox("Fill form"))
    elif stage == 'Gold':
        tasks.append(st.checkbox("6 hours in field"))
        tasks.append(st.checkbox("Avoided distractions"))
        tasks.append(st.checkbox("1 hour exercise"))
        tasks.append(st.checkbox("5L water"))
        tasks.append(st.checkbox("Wake up early"))
        tasks.append(st.checkbox("Sleep early"))
        tasks.append(st.checkbox("No junk food"))
        tasks.append(st.checkbox("No sugar"))
    
    penalty = st.number_input("Penalty $", 0.0, 100.0, 0.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Day"):
            completed = sum(tasks)
            total = len(tasks)
            
            record = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'completed': completed,
                'total': total,
                'penalty': penalty
            }
            records.append(record)
            
            if completed == total:
                progress['days_done'] += 1
                progress['streak'] += 1
                st.success("Perfect day! 🎉")
            elif completed >= total - 2 and penalty > 0:
                progress['days_done'] += 1
                progress['streak'] = 0
                progress['savings'] += penalty
                st.warning(f"Day saved with ${penalty} penalty")
            else:
                st.error("Day not counted")
            
            st.rerun()
    
    with col2:
        if st.button("Refill Form"):
            st.rerun()
    
    if st.button("Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()

# Main app
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        pages = {
            'login': login_page,
            'dashboard': dashboard,
            'challenge_info': challenge_info,
            'challenge_rules': challenge_rules,
            'setup_profile': setup_profile,
            'daily_tracking': daily_tracking
        }
        
        current_page = st.session_state.current_page
        if current_page in pages:
            pages[current_page]()
        else:
            st.session_state.current_page = 'dashboard'
            st.rerun()

if __name__ == "__main__":
    main()
