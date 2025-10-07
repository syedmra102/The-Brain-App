import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LinearRegression
import sqlite3
from datetime import datetime
import random
import os
import hashlib
from textblob import TextBlob
import re

# Database setup (using SQLite for simplicity, error-free)
def init_db():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id TEXT PRIMARY KEY, password TEXT, interests TEXT, hours_per_day REAL, distractions TEXT, 
                  stage TEXT, streak_days INTEGER, badges TEXT, savings REAL, total_hours REAL, last_updated TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_logs 
                 (user_id TEXT, date TEXT, distractions_avoided INTEGER, work_done INTEGER, 
                  sleep_early INTEGER, pushups INTEGER, water_liters REAL, sugar_avoided INTEGER, 
                  pocket_money REAL, review TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS roadmaps 
                 (field TEXT PRIMARY KEY, starting_steps TEXT, month1_plan TEXT, uniqueness_tips TEXT)''')
    sample_roadmaps = [
        ("Cricket", "Join a local club; focus on fitness.", "Practice batting/bowling 3x/week; watch tutorials.", "Develop agility for spin bowling if tall."),
        ("Programming", "Learn Python basics on Codecademy.", "Build 1 CLI app; contribute to GitHub.", "Specialize in ML for healthcare apps."),
        ("Music", "Practice scales daily; use free apps like Yousician.", "Compose 1 simple song; join online jam sessions.", "Blend genres like fusion for uniqueness.")
    ]
    for field, steps, month1, tips in sample_roadmaps:
        c.execute("INSERT OR REPLACE INTO roadmaps (field, starting_steps, month1_plan, uniqueness_tips) VALUES (?, ?, ?, ?)",
                  (field, steps, month1, tips))
    conn.commit()
    return conn

# Hash password for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Check user
def check_user(user_id, password, conn):
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        stored_password = result[0]
        return stored_password == hash_password(password)
    return False

# Save user profile
def save_profile(user_id, interests, hours_per_day, distractions, conn):
    c = conn.cursor()
    c.execute("UPDATE users SET interests = ?, hours_per_day = ?, distractions = ? WHERE user_id = ?", (','.join(interests), hours_per_day, distractions, user_id))
    conn.commit()
    return True

# Load synthetic data for ML (if needed, but not in this version)
@st.cache_data
def load_data():
    data = {
        'field': ['Cricket', 'Programming', 'Music', 'Art', 'Data Science', 'Business', 'Fitness'],
        'Sports': [1, 0, 0, 0, 0, 0, 1],
        'Programming': [0, 1, 0, 0, 1, 0, 0],
        'Music': [0, 0, 1, 1, 0, 0, 0],
        'Art': [0, 0, 1, 1, 0, 0, 0],
        'Science': [0, 1, 0, 0, 1, 0, 0],
        'Business': [0, 0, 0, 0, 0, 1, 0],
        'Health': [0, 0, 0, 0, 0, 0, 1]
    }
    return pd.DataFrame(data)

# ML: Recommend goal (example, if needed)
def recommend_goal(interests, df):
    interest_vector = np.zeros(len(df.columns[1:]))
    for interest in interests:
        if interest in df.columns[1:]:
            interest_vector[df.columns[1:].index(interest)] = 1
    similarities = cosine_similarity([interest_vector], df.iloc[:, 1:])[0]
    top_idx = np.argmax(similarities)
    return df['field'][top_idx]

# ML: Progress prediction (example, if needed)
def predict_progress(hours_per_day, field, total_hours=0):
    X = np.array([[1], [2], [3], [4], [5], [6], [8]]).reshape(-1, 1)
    y = np.array([10000/1, 10000/2, 10000/3, 10000/4, 10000/5, 10000/6, 10000/8])
    model = LinearRegression().fit(X, y)
    days_remaining = model.predict(np.array([[hours_per_day]]))[0] - (total_hours / hours_per_day)
    months = max(0, round(days_remaining / 30, 1))
    years = round(months / 12, 1)
    return months, years, total_hours + (hours_per_day * 30)

# NLP: Distraction detection (example, if needed)
def detect_distractions(text):
    if text.lower() == 'none':
        return False
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    keywords = ['social media', 'gaming', 'scrolling', 'tv', 'procrastinating']
    has_keywords = any(re.search(keyword, text.lower()) for keyword in keywords)
    return sentiment < 0 or has_keywords

# Get roadmap
def get_roadmap(conn, field):
    c = conn.cursor()
    c.execute("SELECT starting_steps, month1_plan, uniqueness_tips FROM roadmaps WHERE field = ?", (field,))
    result = c.fetchone()
    if result:
        return result
    return "Start with basics and build daily habits!", "Focus on 1 month goals.", "Find your unique strength to stand out."

# Update badges
def update_badges(conn, user_id, streak_days, stage):
    badges = []
    if streak_days >= 15 and stage == "Silver":
        badges.append('Silver (15 Days Strong!)')
        stage = "Platinum"
    if streak_days >= 30 and stage == "Platinum":
        badges.append('Platinum (30 Days Unstoppable!)')
        stage = "Gold"
    if streak_days >= 60 and stage == "Gold":
        badges.append('Gold (60 Days Mastered!)')
    c = conn.cursor()
    c.execute("UPDATE users SET badges = ?, stage = ? WHERE user_id = ?", (','.join(badges), stage, user_id))
    conn.commit()
    return badges, stage

# Daily check-in form
def daily_check_in(conn, user_id, stage, distractions_avoided, work_done, sleep_early, pushups, water_liters, sugar_avoided, pocket_money, review):
    c = conn.cursor()
    c.execute("SELECT streak_days, savings, stage FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    streak_days = result[0] if result else 0
    savings = result[1] if result else 0.0
    current_stage = result[2] if result else "Silver"

    all_conditions_met = False
    if stage == "Silver":
        all_conditions_met = (distractions_avoided and work_done)
    elif stage == "Platinum":
        all_conditions_met = (distractions_avoided and work_done and pushups >= 30 and water_liters >= 5)
    elif stage == "Gold":
        all_conditions_met = (distractions_avoided and work_done and sleep_early and pushups >= 50 and water_liters >= 5 and sugar_avoided)

    motivational_images = [
        ("images/motiv1.png", "Tum unstoppable ho! Keep pushing forward!"),
        ("images/motiv2.png", "Every small step counts! Stay focused!"),
        ("images/motiv3.png", "Your dreams are closer than you think!"),
        ("images/motiv4.png", "Discipline is your superpower!"),
    ]

    if all_conditions_met:
        streak_days += 1
        days_required = 15 if stage == "Silver" else 30 if stage == "Platinum" else 60
        days_left = days_required - streak_days
        image_path, quote = random.choice(motivational_images)
        message = f"Great start! Just {days_left} days more, start now! 🎉 Quote: {quote}"
        badges, stage = update_badges(conn, user_id, streak_days, stage)
    else:
        savings += pocket_money
        streak_days = 0
        image_path, quote = motivational_images[0]
        message = f"Conditions nahi poori hui! {pocket_money} PKR added to savings. Total: {savings} PKR. Try again tomorrow!"

    c.execute("INSERT INTO daily_logs (user_id, date, distractions_avoided, work_done, sleep_early, pushups, water_liters, sugar_avoided, pocket_money, review) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, datetime.now().strftime('%Y-%m-%d'), distractions_avoided, work_done, sleep_early, pushups, water_liters, sugar_avoided, pocket_money, review))
    c.execute("UPDATE users SET streak_days = ?, savings = ?, stage = ? WHERE user_id = ?", (streak_days, savings, stage, user_id))
    conn.commit()
    return message, streak_days, savings, image_path, quote

# Motivational quotes
motivational_quotes = [
    "The journey of a thousand miles begins with one step. - Lao Tzu",
    "Success is the sum of small efforts repeated day in and day out. - Robert Collier",
    "You are never too old to set another goal or to dream a new dream. - C.S. Lewis"
]

# Main app
def main():
    st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="wide")
    st.title("🧠 The Brain That Helps You to Use Your Brain!!")
    st.markdown("**Change your life in 105 days with this free challenge!**")

    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.stage = None

    # Login/Registration Form
    if not st.session_state.logged_in:
        st.header("Login or Register")
        with st.form("login_form"):
            user_id = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            register_button = st.form_submit_button("Register (New User)")

            conn = init_db()
            if login_button:
                if user_id and password:
                    if check_user(user_id, password, conn):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        c = conn.cursor()
                        c.execute("SELECT stage FROM users WHERE user_id = ?", (user_id,))
                        result = c.fetchone()
                        st.session_state.stage = result[0] if result else 'Silver'
                        st.success(f"Welcome back, {user_id}!")
                        st.experimental_rerun()  # Refresh to show main app
                    else:
                        st.error("Username or password incorrect. Try again or register.")
                else:
                    st.error("Please enter username and password.")
            
            if register_button:
                if user_id and password:
                    c = conn.cursor()
                    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                    if c.fetchone():
                        st.error("Username already exists! Choose another.")
                    else:
                        c.execute("INSERT INTO users (user_id, password, field, hours_per_day, distractions, streak_days, badges, last_updated, total_hours, savings, stage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                  (user_id, hash_password(password), "", 0.0, "", 0, "", "", 0.0, 0.0, "Silver"))
                        conn.commit()
                        st.success(f"Registered successfully, {user_id}! Now login.")
                        st.experimental_rerun()  # Refresh to update UI
                else:
                    st.error("Please enter username and password.")
            conn.close()
    else:
        # Main app content
        user_id = st.session_state.user_id
        st.header(f"Welcome, {user_id}!")

        # Profile form
        st.header("Complete Your Profile")
        with st.form("profile_form"):
            field = st.text_input("Chosen Field (e.g., Cricket)")
            interests = st.multiselect("Interests", ['Sports', 'Programming', 'Music', 'Art', 'Science', 'Business', 'Health'])
            hours_per_day = st.slider("Daily Hours", 0.0, 12.0, 2.0)
            distractions = st.text_area("Distractions (e.g., 'social media')", value="None")
            submit_profile = st.form_submit_button("Save Profile")
            if submit_profile:
                conn = init_db()
                c = conn.cursor()
                c.execute("UPDATE users SET field = ?, interests = ?, hours_per_day = ?, distractions = ? WHERE user_id = ?", (field, ','.join(interests), hours_per_day, distractions, user_id))
                conn.commit()
                st.success("Profile saved!")
                conn.close()

        # Challenge Overview
        st.header("105 Days Challenge")
        st.markdown("""
        **Change your life in 105 days!** Join our free challenge:
        1. Healthy diet (no sugar, 5L water, 8 hours sleep).
        2. Wake up at 4 AM.
        3. 1 hour exercise (pushups, yoga).
        4. Sleep early (9 PM).
        5. Deep knowledge in your field.
        6. No laziness.
        7. No distractions.
        8. Wealthy investment mindset.
        9. Unstoppable focus like Elon Musk.
        10. Positive thinking and high EQ.
        """)
        if st.button("See Rules & Stages"):
            st.markdown("""
            **Stages**:
            - **Silver (15 days)**: 2 hours/day, no distractions.
            - **Platinum (30 days)**: 4 hours/day, 30 pushups, 5L water.
            - **Gold (60 days)**: 6 hours/day, wake at 4 AM, sleep at 9 PM, 50 pushups, no sugar.
            
            **Rules**:
            - Fill daily tick mark form before sleeping (30 seconds).
            - Fail tasks? Put your day's pocket money in savings for your field (e.g., cricket gear, courses).
            - Complete tasks? Get a colorful wallpaper with motivational quote – screenshot and set as phone wallpaper!
            - After 105 days, earn 3 badges and use savings to boost your field!
            """)
            if st.button("Agree & Start Rewinding Your Life!"):
                try:
                    conn = init_db()
                    c = conn.cursor()
                    c.execute("UPDATE users SET stage = 'Silver' WHERE user_id = ?", (user_id,))
                    conn.commit()
                    st.session_state.stage = 'Silver'
                    st.success("Challenge started! You're now in Silver stage. 🎉")
                    st.experimental_rerun()  # Refresh to show dashboard
                    conn.close()
                except Exception as e:
                    st.error(f"Challenge start failed: {str(e)}")

        # Dashboard
        if st.session_state.stage:
            st.header("Your Dashboard")
            conn = init_db()
            c = conn.cursor()
            c.execute("SELECT field, streak_days, savings, stage FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            if result:
                field, streak_days, savings, stage = result
                st.metric("Stage", stage)
                st.metric("Streak", f"{streak_days}/{15 if stage == 'Silver' else 30 if stage == 'Platinum' else 60}")
                st.metric("Savings for Field", f"{savings} PKR")
                steps, month1, tips = get_roadmap(conn, field)
                st.subheader(f"Roadmap for {field}")
                st.write(f"**Starting Steps:** {steps}")
                st.write(f"**1-Month Plan:** {month1}")
                st.write(f"**Uniqueness Tips:** {tips}")

            # Progress Calendar
            st.subheader("Progress Calendar")
            c.execute("SELECT date, distractions_avoided, work_done FROM daily_logs WHERE user_id = ?", (user_id,))
            logs = c.fetchall()
            if logs:
                df_logs = pd.DataFrame(logs, columns=['Date', 'Distractions Avoided', 'Work Done'])
                df_logs['Date'] = pd.to_datetime(df_logs['Date'])
                df_logs['Completed'] = df_logs['Distractions Avoided'] & df_logs['Work Done']
                st.write(df_logs[['Date', 'Completed']].set_index('Date'))
            else:
                st.info("Log your first day to see your calendar!")

            # Daily Check-In Form
            st.header("Daily Check-In")
            with st.form("daily_check_in"):
                st.write("Fill this before sleeping! Tick the boxes:")
                distractions_avoided = st.checkbox("I avoided distractions today")
                work_done = st.checkbox("I worked at least 2 hours on my field")
                sleep_early = st.checkbox("I slept early (before 9 PM, for Gold)") if stage == "Gold" else False
                pushups = st.number_input("Pushups done today (30 for Platinum, 50 for Gold)", 0, 100, 0) if stage in ["Platinum", "Gold"] else 0
                water_liters = st.number_input("Water drunk today (liters, 5 for Platinum/Gold)", 0.0, 10.0, 0.0) if stage in ["Platinum", "Gold"] else 0.0
                sugar_avoided = st.checkbox("I avoided sugar/junk/alcohol (for Gold)") if stage == "Gold" else True
                pocket_money = st.number_input("Today's pocket money (PKR)", 0.0, 10000.0, 0.0)
                review = st.text_area("Daily Review (e.g., what went well?)")
                submit_check_in = st.form_submit_button("Submit Check-In")

                if submit_check_in:
                    try:
                        conn = init_db()
                        message, streak_days, savings, image_path, quote = daily_check_in(
                            conn, user_id, stage, distractions_avoided, work_done, sleep_early, 
                            pushups, water_liters, sugar_avoided, pocket_money, review)
                        st.write(message)
                        try:
                            if os.path.exists(image_path):
                                st.image(image_path, caption=f"{quote} Screenshot this and set as your wallpaper to stay motivated!")
                            else:
                                st.warning(f"Image not found: {image_path}. Please add images to 'images/' folder in your repo.")
                        except Exception as e:
                            st.warning(f"Image loading failed: {str(e)}. Continue without images.")
                        st.metric("Current Streak", f"{streak_days} days")
                        st.metric("Savings for Field", f"{savings} PKR")
                        badges, stage = update_badges(conn, user_id, streak_days, stage)
                        if badges:
                            st.balloons()
                            st.success(f"🎉 Earned Badges: {', '.join(badges)}")
                        if stage == "Gold" and streak_days >= 60:
                            st.success(f"🎉 Gold Badge Achieved! Use your {savings} PKR to develop your field!")
                        conn.close()
                    except Exception as e:
                        st.error(f"Daily check-in failed: {str(e)}")

            # Logout button
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.stage = None
                st.experimental_rerun()

if __name__ == "__main__":
    main()
