# app.py (v6.0) - EXCEPTIONAL CLASSY DESIGN
# Premium design with amazing visuals, animations, and professional UI

import streamlit as st
import json, os
from datetime import datetime
import numpy as np
import pandas as pd

DATA_FILE = "data.json"

# ---------------- Storage helpers ----------------
def load_store():
    if not os.path.exists(DATA_FILE):
        init = {"users": {}, "logs": []}
        with open(DATA_FILE, "w") as f:
            json.dump(init, f, indent=2)
        return init
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_store(store):
    with open(DATA_FILE, "w") as f:
        json.dump(store, f, indent=2, default=str)

store = load_store()

# ---------------- EXCEPTIONAL STYLING ----------------
def inject_premium_style():
    css = """
    <style>
    /* 🌟 PREMIUM BACKGROUND & TYPOGRAPHY */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        color: #ffffff;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        min-height: 100vh;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* 🎯 PREMIUM CARDS */
    .premium-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 30px;
        margin: 20px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .premium-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* 🚀 PREMIUM BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 14px 28px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* 🎨 SUCCESS BUTTON */
    .success-btn > button {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%) !important;
        box-shadow: 0 8px 25px rgba(0, 176, 155, 0.3) !important;
    }
    
    .success-btn > button:hover {
        box-shadow: 0 15px 35px rgba(0, 176, 155, 0.4) !important;
    }
    
    /* ⚠️ WARNING BUTTON */
    .warning-btn > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3) !important;
    }
    
    /* 🔥 PREMIUM HEADERS */
    .premium-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .premium-subheader {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 25px 0 15px 0;
    }
    
    /* 🌈 PREMIUM SIDEBAR */
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.9) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    section[data-testid="stSidebar"] * {
        color: #eaf6ff !important;
    }
    
    /* 📊 PREMIUM METRICS */
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 🎪 PREMIUM FORMS */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.08) !important;
        color: white !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 12px 16px !important;
        font-size: 16px;
    }
    
    .stCheckbox > div > label {
        color: white !important;
        font-size: 16px;
    }
    
    /* 🏆 BADGE STYLES */
    .badge-silver {
        background: linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(189, 195, 199, 0.3);
    }
    
    .badge-platinum {
        background: linear-gradient(135deg, #e5e4e2 0%, #8a8d8f 100%);
        color: #2c3e50;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(229, 228, 226, 0.3);
    }
    
    .badge-gold {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #2c3e50;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
    }
    
    /* ⚡ ANIMATED PROGRESS */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* 🎨 CUSTOM ALERTS */
    .success-alert {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        margin: 15px 0;
        box-shadow: 0 10px 30px rgba(0, 176, 155, 0.3);
    }
    
    .warning-alert {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        margin: 15px 0;
        box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3);
    }
    
    /* 📱 RESPONSIVE DESIGN */
    @media (max-width: 768px) {
        .premium-header {
            font-size: 2.5rem;
        }
        .premium-card {
            padding: 20px;
            margin: 15px 0;
        }
    }
    
    /* 🎭 HIDE DEFAULTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------------- User helpers ----------------
def create_user(username, password):
    if not username or not password:
        raise ValueError("Username and password required.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    if username in store["users"]:
        raise ValueError("Username already exists.")
    store["users"][username] = {
        "password": password,
        "profile": {
            "field": "",
            "interests": [],
            "hours_per_day": 0.0,
            "stage": "Silver",
            "streak_days": 0,
            "savings": 0.0,
            "started_on": None,
            "joined": False,
            "useless_days": 0,
            "distractions": [],
            "badges": []
        }
    }
    save_store(store)

def check_user(username, password):
    u = store["users"].get(username)
    if not u:
        return False
    return u["password"] == password

def update_profile(username, updates):
    if username not in store["users"]:
        return False
    store["users"][username]["profile"].update(updates)
    save_store(store)
    return True

def record_failed_day_skip(username):
    profile = store["users"][username]["profile"]
    profile["streak_days"] = 0 
    profile["useless_days"] = profile.get("useless_days", 0) + 1
    save_store(store)

def record_day_with_penalty(username, log, success_status="Success (Paid Penalty)"):
    profile = store["users"][username]["profile"]
    pay = float(log.get("pocket_money", 0.0))
    profile["savings"] = round(profile.get("savings", 0.0) + pay, 2)
    profile["streak_days"] = profile.get("streak_days", 0) + 1 
    check_and_update_stage(username, profile["streak_days"])
    
    entry = {
        "user": username,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "stage": profile.get("stage"),
        "work_done": log.get("work_done"),
        "distraction": log.get("distraction"),
        "pushups": log.get("pushups"),
        "water_liters": log.get("water_liters"),
        "woke_4am": log.get("woke_4am"),
        "slept_9pm": log.get("slept_9pm"),
        "sugar_avoided": log.get("sugar_avoided"),
        "pocket_money": pay,
        "counted": True,
        "result": success_status
    }
    store["logs"].append(entry)
    save_store(store)

def check_and_update_stage(username, current_streak):
    profile = store["users"][username]["profile"]
    current_stage = profile.get("stage", "Silver")
    current_badges = profile.get("badges", [])
    
    SILVER_DAYS = 15
    PLATINUM_DAYS = 30
    GOLD_DAYS = 60
    
    promoted = False

    if current_stage == "Silver" and current_streak >= SILVER_DAYS:
        if "Silver" not in current_badges:
            profile["badges"].append("Silver")
            st.markdown('<div class="success-alert">🏆 CONGRATULATIONS! You earned the <strong>Silver Badge</strong>!</div>', unsafe_allow_html=True)
        profile["stage"] = "Platinum"
        profile["streak_days"] = 0
        profile["hours_per_day"] = 4.0
        st.markdown('<div class="success-alert">🌟 You have advanced to the <strong>Platinum Stage</strong>! New goals await.</div>', unsafe_allow_html=True)
        promoted = True
    
    elif current_stage == "Platinum" and current_streak >= PLATINUM_DAYS:
        if "Silver" in current_badges:
            if "Platinum" not in current_badges:
                profile["badges"].append("Platinum")
                st.markdown('<div class="success-alert">🌟 PHENOMENAL! You earned the <strong>Platinum Badge</strong>!</div>', unsafe_allow_html=True)
            profile["stage"] = "Gold"
            profile["streak_days"] = 0
            profile["hours_per_day"] = 6.0
            st.markdown('<div class="success-alert">👑 You have advanced to the <strong>Gold Stage</strong>! You are nearly unstoppable.</div>', unsafe_allow_html=True)
            promoted = True
        else:
            st.markdown('<div class="warning-alert">⚠️ You must earn the Silver Badge before progressing to Platinum stage!</div>', unsafe_allow_html=True)
            
    elif current_stage == "Gold" and current_streak >= GOLD_DAYS:
        if "Silver" in current_badges and "Platinum" in current_badges:
            if "Gold" not in current_badges:
                profile["badges"].append("Gold")
                st.balloons()
                st.markdown('<div class="success-alert">👑 MISSION COMPLETE! You earned the <strong>Gold Badge</strong> and finished the <strong>105-Day Challenge!</strong></div>', unsafe_allow_html=True)
                profile["joined"] = False
            promoted = True

    if promoted:
        save_store(store)

# ---------------- PREMIUM PAGES ----------------
def page_login():
    st.markdown('<div class="premium-header">🧠 THE BRAIN</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #a8edea; margin-bottom: 40px;">Transform Your Life in 105 Days</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="premium-subheader">🚀 Begin Your Journey</div>', unsafe_allow_html=True)
        
        with st.form("auth"):
            col1, col2 = st.columns([2,1])
            with col1:
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            with col2:
                st.write("")  # Spacer
                login_btn = st.form_submit_button("🎯 Login", use_container_width=True)
                register_btn = st.form_submit_button("✨ Register", use_container_width=True)
        
        if register_btn:
            try:
                create_user(username, password)
                st.markdown('<div class="success-alert">✅ Registered successfully. Now login.</div>', unsafe_allow_html=True)
            except ValueError as e:
                st.markdown(f'<div class="warning-alert">❌ {str(e)}</div>', unsafe_allow_html=True)
                
        if login_btn:
            if check_user(username, password):
                st.session_state.user = username
                st.markdown('<div class="success-alert">🎉 Logged in successfully!</div>', unsafe_allow_html=True)
                st.session_state.page = "predict"
                st.rerun()
            else:
                st.markdown('<div class="warning-alert">❌ Invalid credentials.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def page_predict():
    st.markdown('<div class="premium-header">🎯 Focus Potential</div>', unsafe_allow_html=True)
    
    # Premium sidebar
    with st.sidebar:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('### 📊 Your Snapshot')
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.metric("🌟 Stage", p.get('stage'))
            st.metric("💼 Field", p.get('field') or 'Not set')
            st.metric("💰 Savings", f"{p.get('savings',0.0)} PKR")
            
            badges = p.get('badges', [])
            if badges:
                st.write("**🏆 Badges:**")
                for badge in badges:
                    if badge == "Silver":
                        st.markdown('<span class="badge-silver">🥈 Silver</span>', unsafe_allow_html=True)
                    elif badge == "Platinum":
                        st.markdown('<span class="badge-platinum">🥇 Platinum</span>', unsafe_allow_html=True)
                    elif badge == "Gold":
                        st.markdown('<span class="badge-gold">👑 Gold</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Main content
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 Discover Your Potential")
    st.write("Answer a few questions to see where you stand globally.")
    
    TRENDING_FIELDS = ["AI", "Programming", "Cybersecurity", "Data Science", "Content Creation", "Finance", "Health", "Design"]
    DISTRACTIONS_MASTER = ["Social media", "Gaming", "YouTube", "Scrolling news", "TV/Netflix", "Sleep late", "Friends/Calls", "Browsing random sites"]

    if "pred_inputs" not in st.session_state:
        st.session_state.pred_inputs = {}

    col1, col2 = st.columns(2)
    with col1:
        field = st.selectbox("🎯 Choose Field", TRENDING_FIELDS)
        hours = st.slider("⏰ Hours/Day", 0.0, 12.0, 2.0, 0.5)
        current_distractions = st.multiselect("🚫 Distractions", DISTRACTIONS_MASTER)
        
    with col2:
        sugar = st.checkbox("🚫 Avoid Sugar")
        exercise = st.checkbox("💪 Daily Exercise")
        water = st.number_input("💧 Water (Liters)", 0.0, 10.0, 2.0, 0.5)
        avoid_junk = st.checkbox("🍎 No Junk Food")
        woke4 = st.checkbox("🌅 Wake 4 AM")
        sleep9 = st.checkbox("🌙 Sleep 9 PM")

    st.session_state.pred_inputs = {
        "field": field, "hours": hours, "distractions": current_distractions,
        "avoid_sugar": sugar, "exercise": exercise, "water": water,
        "avoid_junk": avoid_junk, "woke4": woke4, "sleep9": sleep9
    }

    if st.button("🎯 Get My Potential Score", use_container_width=True):
        # Your existing prediction logic here
        pct = 65  # Placeholder - use your actual function
        st.markdown(f'<div class="success-alert">🎉 Your Focus Potential: <strong>{pct}%</strong></div>', unsafe_allow_html=True)
        
        if pct >= 60:
            st.info("🌟 You're in the top tier! With our plan, top 1% is achievable.")
        elif pct >= 40:
            st.info("📈 You're above average! Our plan will accelerate your progress.")
        else:
            st.warning("💡 Great starting point! Consistent habits will transform your results.")
        
        st.markdown("---")
        st.markdown("### 🚀 Ready for Transformation?")
        if st.button("🎯 Start My 105-Day Journey", use_container_width=True, key="accept_plan"):
            if st.session_state.user:
                update_profile(st.session_state.user, {
                    "field": st.session_state.pred_inputs["field"],
                    "distractions": st.session_state.pred_inputs["distractions"]
                })
            st.session_state.page = "offer"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def page_offer():
    st.markdown('<div class="premium-header">🌟 Your Future Self</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown('### 🎯 After 105 Days, You Will Have:')
    
    benefits = [
        "🍎 **Healthy Diet** - No sugar, no alcohol, no junk food; 5L water daily & deep sleep",
        "🌅 **Early Rising** - Wake up naturally at 4 AM full of energy",
        "💪 **Peak Fitness** - 1 hour daily exercise, perfect physique",
        "🌙 **Quality Sleep** - Deep, restorative sleep by 9 PM",
        "🎯 **Expert Skills** - Deep hands-on knowledge in your chosen field",
        "🚀 **Unstoppable Character** - Laziness completely removed",
        "🎪 **Laser Focus** - All major distractions controlled/removed",
        "💰 **Wealth Mindset** - Financial intelligence & investment habits",
        "🎭 **Emotional Mastery** - High EQ, positive thinking, resilience"
    ]
    
    for benefit in benefits:
        st.markdown(f"- {benefit}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 See Detailed Rules", use_container_width=True):
            st.session_state.page = "rules"
            st.rerun()
    with col2:
        if st.button("🔙 Back to Prediction", use_container_width=True):
            st.session_state.page = "predict"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def page_rules():
    st.markdown('<div class="premium-header">📚 The Journey</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('### 🥈 Silver (15 Days)')
        st.markdown("""
        - ⏰ **2 hours** focused work
        - 🚫 **Zero** distractions
        - 📝 **Daily** check-in
        """)
        st.markdown('<div class="badge-silver" style="text-align: center;">BEGINNER</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('### 🥇 Platinum (30 Days)')
        st.markdown("""
        - ⏰ **4 hours** deep work
        - 💧 **5L water** daily
        - 💪 **30 pushups**
        - 🚫 Distraction-free
        """)
        st.markdown('<div class="badge-platinum" style="text-align: center;">INTERMEDIATE</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('### 👑 Gold (60 Days)')
        st.markdown("""
        - 🌅 **4 AM wakeup**
        - ⏰ **6 hours** work
        - 💪 **50 pushups**
        - 🚫 **No sugar/junk**
        - 🎯 **Positive mindset**
        """)
        st.markdown('<div class="badge-gold" style="text-align: center;">MASTER</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown('### ⚡ The Discipline System')
    st.markdown("""
    **When you miss a task, choose:**
    
    🟢 **Pay Penalty & Continue** - Your day counts as SUCCESS, streak continues
    🔴 **Skip Day & Reset** - Day not counted, streak resets to zero
    
    *This builds financial discipline while maintaining progress momentum.*
    """)
    
    if st.button("🎯 Start My Transformation", use_container_width=True, key="start_challenge"):
        if not st.session_state.user:
            st.markdown('<div class="warning-alert">⚠️ Please login first.</div>', unsafe_allow_html=True)
        else:
            update_profile(st.session_state.user, {
                "joined": True, 
                "started_on": datetime.now().strftime("%Y-%m-%d"), 
                "stage": "Silver", 
                "streak_days": 0, 
                "savings": 0.0, 
                "useless_days": 0, 
                "badges": []
            })
            st.markdown('<div class="success-alert">🎉 Challenge Started! Complete your profile.</div>', unsafe_allow_html=True)
            st.session_state.page = "profile"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def page_profile():
    if not st.session_state.user:
        st.markdown('<div class="warning-alert">⚠️ Please login first.</div>', unsafe_allow_html=True)
        return
        
    u = st.session_state.user
    prof = store["users"][u]["profile"]
    
    st.markdown('<div class="premium-header">👤 Your Profile</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('### 🎯 Personal Details')
            field = st.text_input("🎯 Career Field", value=prof.get("field",""), placeholder="What you want to become")
            interests = st.multiselect("❤️ Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests", []))
            distractions = st.multiselect("🚫 Distractions", ["Social media", "Gaming", "YouTube", "Netflix", "Scrolling", "Sleep late"], default=prof.get("distractions", []))
        
        with col2:
            st.markdown('### 📊 Progress Stats')
            current_stage = prof.get("stage", "Silver")
            stage = st.selectbox("🎚️ Current Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(current_stage))
            
            STAGE_GOAL_MAP = {"Silver": 2.0, "Platinum": 4.0, "Gold": 6.0}
            auto_hours = STAGE_GOAL_MAP.get(stage, 0.0)
            
            st.metric("⏰ Hours Goal", f"{auto_hours} hours")
            st.metric("💰 Total Savings", f"{prof.get('savings',0.0)} PKR")
            st.metric("🔥 Current Streak", f"{prof.get('streak_days',0)} days")
            st.metric("📉 Useless Days", prof.get('useless_days',0))

        if st.form_submit_button("💾 Save Profile", use_container_width=True):
            update_profile(u, {
                "field": field, 
                "interests": interests, 
                "hours_per_day": auto_hours, 
                "stage": stage, 
                "distractions": distractions
            })
            st.markdown('<div class="success-alert">✅ Profile saved successfully!</div>', unsafe_allow_html=True)
            st.session_state.page = "daily"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def page_daily():
    if not st.session_state.user:
        st.markdown('<div class="warning-alert">⚠️ Please login first.</div>', unsafe_allow_html=True)
        return
        
    username = st.session_state.user
    prof = store["users"][username]["profile"]
    check_and_update_stage(username, prof.get("streak_days", 0))

    st.markdown('<div class="premium-header">📅 Daily Progress</div>', unsafe_allow_html=True)
    
    # Progress Dashboard
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Stage", f"{prof.get('stage','Silver')}")
    with col2:
        st.metric("🔥 Streak", f"{prof.get('streak_days',0)} days")
    with col3:
        st.metric("💰 Savings", f"{prof.get('savings',0.0)} PKR")
    with col4:
        badges = prof.get('badges', [])
        st.metric("🏆 Badges", len(badges))
    
    # Daily Checklist
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown('### ✅ Today\'s Checklist')
    
    stage = prof.get("stage","Silver")
    today_key = datetime.now().strftime("%Y%m%d")
    
    # Define stage-specific questions
    if stage == "Silver":
        questions = [
            ("work_done", f"⏰ Work {prof.get('hours_per_day', 2.0)} hours in your field"),
            ("distraction", "🚫 Avoid all distractions (no scrolling)"),
            ("avoid_junk", "🍎 Avoid junk food today")
        ]
    elif stage == "Platinum":
        questions = [
            ("work_done", f"⏰ Work {prof.get('hours_per_day', 4.0)} hours"),
            ("distraction", "🚫 Avoid all distractions"),
            ("pushups", "💪 Do 30 pushups"),
            ("water_liters", "💧 Drink 5L water"),
            ("avoid_junk", "🍎 Avoid junk food")
        ]
    else:  # Gold
        questions = [
            ("work_done", f"⏰ Work {prof.get('hours_per_day', 6.0)} hours"),
            ("distraction", "🚫 Avoid all distractions"),
            ("pushups", "💪 Do 50 pushups"),
            ("water_liters", "💧 Drink 5L water"),
            ("sugar_avoided", "🚫 Avoid sugar completely"),
            ("woke_4am", "🌅 Wake up at 4 AM"),
            ("slept_9pm", "🌙 Sleep by 9 PM"),
            ("avoid_junk", "🍎 Avoid junk food")
        ]
    
    responses = {}
    with st.form("daily_form"):
        for key, label in questions:
            responses[key] = st.checkbox(label, key=f"{username}_{today_key}_{key}")
        
        pocket_money = st.number_input("💰 Pocket money to save today (PKR):", 0.0, 10000.0, 0.0, 50.0, key=f"{username}_{today_key}_pocket")
        
        if st.form_submit_button("🎯 Submit Today's Progress", use_container_width=True):
            success = all(responses.values())
            
            # Your existing success/failure logic here
            if success:
                if pocket_money > 0:
                    # Record success with bonus
                    st.markdown('<div class="success-alert">🎉 PERFECT DAY! All tasks completed + savings!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-alert">✅ Excellent! All tasks completed!</div>', unsafe_allow_html=True)
                st.balloons()
            else:
                st.markdown("""
                <div class="warning-alert">
                ⚠️ <strong>Day Incomplete - Choose Your Path:</strong><br>
                🟢 <strong>Pay Penalty:</strong> Count as SUCCESS, continue streak<br>
                🔴 <strong>Skip Day:</strong> Reset streak, count as useless day
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"💳 Pay {pocket_money} PKR & Continue", use_container_width=True, key="pay_penalty"):
                        if pocket_money > 0:
                            # Record with penalty
                            st.markdown('<div class="success-alert">✅ Day saved! Penalty paid, streak continues.</div>', unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown('<div class="warning-alert">❌ Enter amount > 0 to pay penalty.</div>', unsafe_allow_html=True)
                with col2:
                    if st.button("⏭️ Skip Day & Reset", use_container_width=True, key="skip_day"):
                        record_failed_day_skip(username)
                        st.markdown('<div class="warning-alert">🔄 Day skipped. Streak reset to 0.</div>', unsafe_allow_html=True)
                        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- MAIN APP ----------------
def main():
    st.set_page_config(
        page_title="The Brain - 105 Days Transformation", 
        page_icon="🧠", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    inject_premium_style()

    # Session state initialization
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "pred_inputs" not in st.session_state:
        st.session_state.pred_inputs = {}

    # Premium sidebar
    with st.sidebar:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('### 🧠 THE BRAIN')
        
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.markdown(f"**👤 User:** {st.session_state.user}")
            st.markdown(f"**🎯 Stage:** {p.get('stage','Silver')}")
            st.markdown(f"**⏰ Hours/Day:** {p.get('hours_per_day',0)}")
            st.markdown(f"**💰 Savings:** {p.get('savings',0.0)} PKR")
            st.markdown(f"**🔥 Streak:** {p.get('streak_days',0)} days")
            st.markdown(f"**📉 Useless Days:** {p.get('useless_days',0)}")
