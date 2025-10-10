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

# 🏔️ BEAUTIFUL WHITE/BLUE MOUNTAIN AESTHETIC
def add_white_blue_mountain_bg():
    st.markdown("""
    <style>
    .stApp {
        background: 
            linear-gradient(rgba(240, 248, 255, 0.92), rgba(224, 247, 250, 0.95)),
            url('https://images.unsplash.com/photo-1519681393784-d120267933ba?ixlib=rb-4.0.3&w=2000');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #2c3e50;
        font-family: 'Segoe UI', system-ui, sans-serif;
        min-height: 100vh;
    }
    
    /* Beautiful dark text for contrast */
    .stApp, .stApp * {
        color: #2c3e50 !important;
    }
    
    /* Premium glass cards */
    .main .block-container {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 35px;
        margin-top: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 20px 40px rgba(135, 206, 250, 0.15);
        transition: all 0.3s ease;
    }
    
    .main .block-container:hover {
        box-shadow: 0 25px 50px rgba(135, 206, 250, 0.25);
        transform: translateY(-5px);
    }
    
    /* Beautiful blue buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 16px;
        padding: 14px 28px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Beautiful inputs */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #2c3e50 !important;
        border-radius: 14px !important;
        border: 2px solid #e3f2fd !important;
        padding: 14px 18px !important;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus, 
    .stNumberInput>div>div>input:focus {
        border: 2px solid #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Checkboxes */
    .stCheckbox>div>label {
        color: #2c3e50 !important;
        font-size: 16px;
        font-weight: 500;
    }
    
    /* Metrics styling */
    .stMetric {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(135, 206, 250, 0.3);
        box-shadow: 0 10px 30px rgba(135, 206, 250, 0.1);
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Custom headers */
    .blue-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 800;
    }
    
    .blue-subheader {
        color: #5d7da8 !important;
        text-align: center;
        font-weight: 600;
    }
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

# 🏠 HOME PAGE - WHITE/BLUE AESTHETIC
def home_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='blue-header' style='font-size: 4rem; margin-bottom: 0;'>🏔️ THE BRAIN</h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='blue-subheader' style='margin-top: 0;'>Climb Your Personal Everest</h3>", unsafe_allow_html=True)
        st.markdown("---")
    
    # Login/Register Form
    st.markdown("<h2 style='text-align: center; color: #667eea;'>🚀 Begin Your Ascent</h2>", unsafe_allow_html=True)
    
    with st.form("auth"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("👤 Username", placeholder="Enter your username")
        with col2:
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("🎯 Begin Climb", use_container_width=True)
        with col2:
            register_btn = st.form_submit_button("✨ Start Journey", use_container_width=True)
    
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
                st.success("🎉 Welcome to the mountains!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
        else:
            st.warning("⚠️ Please enter both username and password")
    
    # Features showcase
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #667eea;'>🎯 Your Climbing Journey</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.7); border-radius: 20px; border: 1px solid #e3f2fd;'>
            <h3 style='color: #667eea;'>🥈 Base Camp</h3>
            <p style='color: #5d7da8;'>15 days • 2 hours/day</p>
            <p style='color: #5d7da8;'>Build foundation habits</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.7); border-radius: 20px; border: 1px solid #e3f2fd;'>
            <h3 style='color: #667eea;'>🥇 High Camp</h3>
            <p style='color: #5d7da8;'>30 days • 4 hours/day</p>
            <p style='color: #5d7da8;'>Advanced discipline</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.7); border-radius: 20px; border: 1px solid #e3f2fd;'>
            <h3 style='color: #667eea;'>👑 Summit</h3>
            <p style='color: #5d7da8;'>60 days • 6 hours/day</p>
            <p style='color: #5d7da8;'>Master level focus</p>
        </div>
        """, unsafe_allow_html=True)

# 📊 DASHBOARD - WHITE/BLUE DESIGN
def dashboard_page():
    user_data = store["users"][st.session_state.user]
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"<h1 class='blue-header'>🎯 Welcome, {st.session_state.user}!</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #5d7da8;'>Climbing towards your personal summit</p>", unsafe_allow_html=True)
    
    # Stats Dashboard
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔥 Current Streak", f"{user_data['streak']} days", delta="+1 today" if user_data['streak'] > 0 else None)
    with col2:
        st.metric("💰 Total Savings", f"{user_data['savings']:.0f} PKR", delta=f"+{user_data['savings']/100:.0f}%")
    with col3:
        st.metric("🏔️ Current Stage", user_data['stage'])
    with col4:
        st.metric("⭐ Badges", len(user_data['badges']))
    
    # Daily Check-in Section
    st.markdown("---")
    st.markdown("<h2 style='color: #667eea;'>📝 Daily Climbing Log</h2>", unsafe_allow_html=True)
    
    with st.form("daily_check"):
        st.markdown("### ✅ Today's Ascent")
        
        # Stage-based tasks
        if user_data['stage'] == "Silver":
            task1 = st.checkbox("⏰ Work 2 hours on my goals")
            task2 = st.checkbox("🚫 Avoid digital distractions")
            task3 = st.checkbox("📚 Learn something new (30 min)")
        elif user_data['stage'] == "Platinum":
            task1 = st.checkbox("⏰ Work 4 hours on my goals")
            task2 = st.checkbox("💪 30 minutes exercise")
            task3 = st.checkbox("💧 Drink 3L water")
            task4 = st.checkbox("🍎 Healthy eating")
        else:  # Gold
            task1 = st.checkbox("⏰ Work 6 hours on my goals")
            task2 = st.checkbox("💪 1 hour exercise")
            task3 = st.checkbox("💧 Drink 5L water")
            task4 = st.checkbox("🌅 Wake up at 5 AM")
            task5 = st.checkbox("🎯 Mindfulness practice")
        
        savings = st.number_input("💰 Money saved today (PKR)", 0, 5000, 0, 50)
        
        submitted = st.form_submit_button("🏔️ Log Today's Climb", use_container_width=True)
        
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
                    user_data['badges'].append("Base Camp Complete")
                    st.balloons()
                    st.success("🌟 CONGRATULATIONS! You reached HIGH CAMP! (Platinum Stage)")
                elif user_data['streak'] >= 30 and user_data['stage'] == "Platinum":
                    user_data['stage'] = "Gold"
                    user_data['badges'].append("High Camp Complete")
                    st.balloons()
                    st.success("👑 PHENOMENAL! You're approaching the SUMMIT! (Gold Stage)")
                elif user_data['streak'] >= 60 and user_data['stage'] == "Gold":
                    user_data['badges'].append("Summit Reached")
                    st.balloons()
                    st.success("🏆 EVEREST CONQUERED! You completed the 105-Day Challenge!")
                
                save_store(store)
                st.success("🎉 Today's ascent recorded! You're climbing higher! 🏔️")
            else:
                st.warning("⚠️ Complete all climbing tasks to continue your ascent!")
    
    # Progress Visualization
    st.markdown("---")
    st.markdown("<h2 style='color: #667eea;'>📈 Your Climbing Progress</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        # Altitude progress
        target_streak = 15 if user_data['stage'] == "Silver" else 30 if user_data['stage'] == "Platinum" else 60
        progress = min(user_data['streak'] / target_streak, 1.0)
        altitude = user_data['streak'] * 100  # Each day = 100m climbed
        st.metric("🏔️ Current Altitude", f"{altitude}m")
        st.progress(progress)
        st.caption(f"Climbing to {target_streak * 100}m")
    
    with col2:
        # Summit goal
        total_journey = 105
        journey_progress = min(user_data['streak'] / total_journey, 1.0)
        st.metric("🎯 Journey Complete", f"{journey_progress*100:.1f}%")
        st.progress(journey_progress)
        st.caption(f"105-Day Summit Challenge")
    
    # Badges Section
    if user_data['badges']:
        st.markdown("---")
        st.markdown("<h2 style='color: #667eea;'>🏆 Climbing Achievements</h2>", unsafe_allow_html=True)
        
        for badge in user_data['badges']:
            st.success(f"✅ {badge}")
    
    # Logout button
    st.markdown("---")
    if st.button("🚪 Descend from Summit", use_container_width=True):
        st.session_state.user = None
        st.session_state.page = "home"
        st.rerun()

# 🎯 MAIN APP
def main():
    st.set_page_config(
        page_title="The Brain - Mountain Ascent", 
        page_icon="🏔️", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Add the beautiful white/blue mountain aesthetic background
    add_white_blue_mountain_bg()
    
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
