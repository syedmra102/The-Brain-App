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

# 🎨 AMAZING BACKGROUND - JUST COPY THIS
def add_amazing_background():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: white;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Make text readable */
    .stApp, .stApp * {
        color: white !important;
    }
    
    /* Beautiful buttons */
    .stButton>button {
        background: rgba(255,255,255,0.2);
        color: white;
        border: 2px solid white;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 16px;
    }
    
    .stButton>button:hover {
        background: rgba(255,255,255,0.3);
    }
    
    /* Hide Streamlit default stuff */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Simple user functions
def create_user(username, password):
    if username in store["users"]:
        return False
    store["users"][username] = {
        "password": password,
        "streak": 0,
        "savings": 0,
        "stage": "Silver"
    }
    save_store(store)
    return True

def check_user(username, password):
    user = store["users"].get(username)
    return user and user["password"] == password

# 🏠 HOME PAGE - SIMPLE & BEAUTIFUL
def home_page():
    st.markdown("<h1 style='text-align: center;'>🧠 THE BRAIN</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Transform Your Life in 105 Days</h3>", unsafe_allow_html=True)
    
    # Login/Register Form
    with st.form("auth"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("🚀 Login")
        with col2:
            register_btn = st.form_submit_button("✨ Register")
    
    if register_btn and username and password:
        if create_user(username, password):
            st.success("Registered! Now login.")
        else:
            st.error("Username exists!")
    
    if login_btn and username and password:
        if check_user(username, password):
            st.session_state.user = username
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Wrong credentials!")

# 📊 DASHBOARD - SIMPLE & BEAUTIFUL
def dashboard_page():
    user_data = store["users"][st.session_state.user]
    
    st.markdown("<h1 style='text-align: center;'>🎯 Your Progress</h1>", unsafe_allow_html=True)
    
    # Stats in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Streak", f"{user_data['streak']} days")
    with col2:
        st.metric("💰 Savings", f"{user_data['savings']} PKR")
    with col3:
        st.metric("🎚️ Stage", user_data['stage'])
    
    # Daily Check-in
    st.markdown("---")
    st.subheader("✅ Today's Check-in")
    
    with st.form("daily_check"):
        st.write("Did you complete today's tasks?")
        
        completed = st.checkbox("✅ I worked on my goals today")
        exercised = st.checkbox("💪 I exercised today")
        saved_money = st.number_input("💰 Money saved today (PKR)", 0, 1000, 0)
        
        if st.form_submit_button("🎯 Submit Day"):
            if completed and exercised:
                user_data['streak'] += 1
                user_data['savings'] += saved_money
                save_store(store)
                st.balloons()
                st.success("🎉 Amazing! Day completed!")
            else:
                st.warning("Complete all tasks to continue streak!")
    
    # Logout
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.page = "home"
        st.rerun()

# 🎯 MAIN APP
def main():
    st.set_page_config(page_title="The Brain", layout="centered")
    
    # Add the amazing background
    add_amazing_background()
    
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
