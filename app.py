import streamlit as st
import json, os
from datetime import datetime
import numpy as np
import pandas as pd

# Simple data storage
DATA_FILE = "data.json"
def load_store():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "logs": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)
def save_store(store):
    with open(DATA_FILE, "w") as f:
        json.dump(store, f, indent=2)

store = load_store()

# 🏔️ BEAUTIFUL MOUNTAIN AESTHETIC BACKGROUND
def add_mountain_aesthetic():
    st.markdown("""
    <style>
    .stApp {
        background: 
            linear-gradient(rgba(15, 32, 65, 0.85), rgba(25, 55, 109, 0.90)),
            url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&w=2000');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: white;
        font-family: 'Segoe UI', system-ui, sans-serif;
        min-height: 100vh;
    }
    
    /* Beautiful text */
    .stApp, .stApp * {
        color: white !important;
    }
    
    /* Premium cards */
    .main .block-container {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 30px;
        margin-top: 30px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }
    
    /* Beautiful buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4);
    }
    
    /* Beautiful inputs */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 12px 16px !important;
    }
    
    /* Checkboxes */
    .stCheckbox>div>label {
        color: white !important;
        font-size: 16px;
    }
    
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)

# Simple user functions
def create_user(username, password):
    if not username or not password:
        return False, "Username and password required!"
    if username in store["users"]:
        return False, "Username already exists!"
    
    store["users"][username] = {
        "password": password,
        "streak": 0,
        "savings": 0.0,
        "stage": "Silver",
        "joined_date": datetime.now().strftime("%Y-%m-%d"),
        "badges": []
    }
    save_store(store)
    return True, "Registration successful!"

def check_user(username, password):
    user = store["users"].get(username)
    if not user:
        return False
    return user["password"] == password

# 🏠 HOME PAGE - MOUNTAIN AESTHETIC
def home_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0;'>🏔️ THE BRAIN</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #a8edea; margin-top: 0;'>Conquer Your Goals Like Mountains</h3>", unsafe_allow_html=True)
        st.markdown("---")
    
    # Login/Register Form
    st.markdown("<h2 style='text-align: center; color: #fed6e3;'>🚀 Begin Your Journey</h2>", unsafe_allow_html=True)
    
    with st.form("auth"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("👤 Username", placeholder="Enter your username")
        with col2:
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("🎯 Login", use_container_width=True)
        with col2:
            register_btn = st.form_submit_button("✨ Register", use_container_width=True)
    
    if register_btn:
        if username and password:
            success, message = create_user(username, password)
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
        else:
            st.warning("⚠️ Please enter both username and password")
    
    if login_btn:
        if username and password:
            if check_user(username, password):
                st.session_state.user = username
                st.session_state.page = "dashboard"
                st.success("🎉 Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
        else:
            st.warning("⚠️ Please enter both username and password")
    
    # Features showcase
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #a8edea;'>🎯 Your Transformation Journey</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='text-align: center;'>
            <h3>🥈 Silver Stage</h3>
            <p>15 days • 2 hours/day</p>
            <p>Build foundation habits</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center;'>
            <h3>🥇 Platinum Stage</h3>
            <p>30 days • 4 hours/day</p>
            <p>Advanced discipline</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center;'>
            <h3>👑 Gold Stage</h3>
            <p>60 days • 6 hours/day</p>
            <p>Master level focus</p>
        </div>
        """, unsafe_allow_html=True)

# 📊 DASHBOARD - BEAUTIFUL DESIGN
def dashboard_page():
    user_data = store["users"][st.session_state.user]
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center;'>🎯 Welcome, {st.session_state.user}!</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #fed6e3;'>Your mountain-climbing journey to success</p>", unsafe_allow_html=True)
    
    # Stats Dashboard
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔥 Current Streak", f"{user_data['streak']} days")
    with col2:
        st.metric("💰 Total Savings", f"{user_data['savings']:.0f} PKR")
    with col3:
        st.metric("🏔️ Current Stage", user_data['stage'])
    with col4:
        st.metric("⭐ Badges Earned", len(user_data['badges']))
    
    # Daily Check-in Section
    st.markdown("---")
    st.markdown("<h2 style='color: #a8edea;'>📝 Daily Progress Tracker</h2>", unsafe_allow_html=True)
    
    with st.form("daily_check"):
        st.markdown("### ✅ Today's Achievements")
        
        # Stage-based tasks
        if user_data['stage'] == "Silver":
            task1 = st.checkbox("⏰ Work 2 hours on my goals")
            task2 = st.checkbox("🚫 Avoid distractions")
            task3 = st.checkbox("📚 Learn something new")
        elif user_data['stage'] == "Platinum":
            task1 = st.checkbox("⏰ Work 4 hours on my goals")
            task2 = st.checkbox("💪 30 minutes exercise")
            task3 = st.checkbox("💧 Drink 3L water")
            task4 = st.checkbox("🚫 No junk food")
        else:  # Gold
            task1 = st.checkbox("⏰ Work 6 hours on my goals")
            task2 = st.checkbox("💪 1 hour exercise")
            task3 = st.checkbox("💧 Drink 5L water")
            task4 = st.checkbox("🌅 Wake up early")
            task5 = st.checkbox("🎯 Positive mindset practice")
        
        savings = st.number_input("💰 Money saved today (PKR)", 0, 5000, 0, 50)
        
        submitted = st.form_submit_button("🏔️ Submit Today's Progress", use_container_width=True)
        
        if submitted:
            tasks_completed = True
            if user_data['stage'] == "Silver":
                tasks_completed = task1 and task2 and task3
            elif user_data['stage'] == "Platinum":
                tasks_completed = task1 and task2 and task3 and task4
            else:
                tasks_completed = task1 and task2 and task3 and task4 and task5
            
            if tasks_completed:
                user_data['streak'] += 1
                user_data['savings'] += savings
                
                # Check for stage promotion
                if user_data['streak'] >= 15 and user_data['stage'] == "Silver":
                    user_data['stage'] = "Platinum"
                    st.balloons()
                    st.success("🌟 CONGRATULATIONS! You advanced to PLATINUM stage!")
                elif user_data['streak'] >= 30 and user_data['stage'] == "Platinum":
                    user_data['stage'] = "Gold"
                    st.balloons()
                    st.success("👑 PHENOMENAL! You reached GOLD stage!")
                
                save_store(store)
                st.success("🎉 Amazing! Today's progress recorded successfully!")
            else:
                st.warning("⚠️ Complete all tasks to continue your streak!")
    
    # Progress Visualization
    st.markdown("---")
    st.markdown("<h2 style='color: #a8edea;'>📈 Your Journey Progress</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        # Streak progress
        target_streak = 15 if user_data['stage'] == "Silver" else 30 if user_data['stage'] == "Platinum" else 60
        progress = min(user_data['streak'] / target_streak, 1.0)
        st.metric("🏔️ Mountain Progress", f"{progress*100:.1f}%")
        st.progress(progress)
    
    with col2:
        # Savings goal
        savings_goal = 5000
        savings_progress = min(user_data['savings'] / savings_goal, 1.0)
        st.metric("💰 Savings Goal", f"{savings_progress*100:.1f}%")
        st.progress(savings_progress)
    
    # Logout button
    st.markdown("---")
    if st.button("🚪 Logout from Mountain Peak", use_container_width=True):
        st.session_state.user = None
        st.session_state.page = "home"
        st.rerun()

# 🎯 MAIN APP
def main():
    st.set_page_config(
        page_title="The Brain - Mountain Journey", 
        page_icon="🏔️", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Add the beautiful mountain aesthetic background
    add_mountain_aesthetic()
    
    # Initialize session state
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Show the right page
    if st.session_state.user:
        dashboard_page()
    else:
        home_page()

if __name__ == "__main__":
    main()
