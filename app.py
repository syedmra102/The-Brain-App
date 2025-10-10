import streamlit as st
from datetime import datetime

# Page config
st.set_page_config(page_title="Brain App", page_icon="🧠", layout="wide")

# Custom CSS for professional design
st.markdown("""
    <style>
        body {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: #e6f7ff;
            font-family: 'Poppins', sans-serif;
        }
        [data-testid="stSidebar"] {
            background: rgba(25, 25, 40, 0.9);
            backdrop-filter: blur(10px);
        }
        .main-title {
            font-size: 3rem;
            text-align: center;
            color: #00bfff;
            text-shadow: 0 0 20px #00bfff;
        }
        .subtitle {
            text-align: center;
            color: #cce7ff;
            font-size: 1.2rem;
        }
        .feature-card {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 0 15px rgba(0,191,255,0.3);
            transition: 0.3s ease-in-out;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 0 25px rgba(0,191,255,0.6);
        }
        .footer {
            text-align: center;
            font-size: 0.9rem;
            margin-top: 50px;
            color: #a9c9ff;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to:", ["Home", "Dashboard", "About", "Contact"])

# Home Page
if page == "Home":
    st.markdown("<h1 class='main-title'>Welcome to The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Unlock your potential. Build focus, health, and unstoppable growth.</p>", unsafe_allow_html=True)

    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-card'><h3>🧠 AI Tracking</h3><p>Monitor your progress using smart learning analytics.</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-card'><h3>💪 Self-Improvement</h3><p>Transform your habits with our 105-day guided challenge.</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-card'><h3>🌍 Global Mentors</h3><p>Connect with teachers and learners worldwide.</p></div>", unsafe_allow_html=True)

    st.markdown("<div class='footer'>© 2025 The Brain App | Made with 💙 by Syed Imran Shah</div>", unsafe_allow_html=True)

# Dashboard Page
elif page == "Dashboard":
    st.markdown("<h1 class='main-title'>Your Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Track your learning journey and challenges in real-time.</p>", unsafe_allow_html=True)

    progress = st.slider("Today's Progress", 0, 100, 65)
    st.progress(progress / 100)
    st.metric("Current Streak 🔥", "15 days", "+3 days")
    st.metric("Focus Hours", "6 hrs", "+2 hrs")
    st.metric("Consistency", "87%", "+5%")

# About Page
elif page == "About":
    st.markdown("<h1 class='main-title'>About The Brain App</h1>", unsafe_allow_html=True)
    st.write("""
        The Brain App is an AI-based self-growth platform designed to help individuals
        build focus, health, and skill mastery. It’s more than a productivity tool—
        it’s a full lifestyle transformation program.
        
        🔹 105-Day Life Challenge  
        🔹 Personalized habit tracking  
        🔹 Motivation & learning analytics  
        🔹 AI guidance for your goals
    """)

# Contact Page
elif page == "Contact":
    st.markdown("<h1 class='main-title'>Contact Us</h1>", unsafe_allow_html=True)
    with st.form("contact_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        message = st.text_area("Your Message")
        submitted = st.form_submit_button("Send Message 💌")

        if submitted:
            st.success(f"Thanks, {name}! We’ll get back to you soon.")
