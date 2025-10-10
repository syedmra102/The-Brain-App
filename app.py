import streamlit as st
from PIL import Image

# Page Config
st.set_page_config(page_title="Brain App", layout="wide")

# Custom Background CSS
def set_background(image_file):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{image_file}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Convert image to base64
import base64
def get_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_image = get_base64("assets/background.jpg")
set_background(bg_image)

# Sidebar Navigation
st.sidebar.title("🧠 Brain App Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📊 Dashboard", "💎 Challenge Stages", "📅 Progress Tracker", "💬 Motivation"])

# Home
if page == "🏠 Home":
    st.markdown("<h1 style='text-align:center; color:#00e5ff; text-shadow:0 0 20px #00e5ff;'>Welcome to Brain App</h1>", unsafe_allow_html=True)
    st.write("### Change your life in 105 days! 🚀")
    st.markdown("""
    This AI-inspired challenge builds your mind, health, and habits.
    Choose your path — **Easy**, **Medium**, or **Hard** — and transform your future.
    """)
    st.image("assets/logo.png", width=150)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Start your journey → go to the Dashboard tab!</p>", unsafe_allow_html=True)

# Dashboard
elif page == "📊 Dashboard":
    st.title("📊 Your Dashboard")
    st.write("Track your habits and progress daily.")
    name = st.text_input("Enter your name:")
    day = st.number_input("Enter current day of your challenge:", 1, 105)
    completed = st.checkbox("Completed today's challenge?")
    if completed:
        st.success("Great job! Keep the streak alive 🔥")
    else:
        st.warning("Stay consistent. Tomorrow is a new chance!")

# Challenge Stages
elif page == "💎 Challenge Stages":
    st.title("💎 Challenge Levels")
    st.write("3 Stages to build your new life.")
    st.markdown("""
    **Easy (15 days)** → 2 hrs of study, control distractions  
    **Medium (30 days)** → + Exercise, hydration, 4 hrs of study  
    **Hard (60 days)** → Wake 4AM, strict routine, 6 hrs focused work  
    """)

# Progress Tracker
elif page == "📅 Progress Tracker":
    st.title("📅 Progress Tracker")
    progress = st.slider("Select your progress (%)", 0, 100, 25)
    st.progress(progress / 100)
    if progress == 100:
        st.balloons()
        st.success("Congratulations! You completed your 105-day challenge 🎉")

# Motivation
elif page == "💬 Motivation":
    st.title("💬 Daily Motivation")
    import random
    quotes = [
        "Discipline beats motivation.",
        "Small steps every day = Big success.",
        "You’re closer than you think!",
        "The future belongs to those who act today."
    ]
    st.info(random.choice(quotes))
    st.image("assets/background.jpg", use_column_width=True)
