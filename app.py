import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import random
import os
import hashlib
from textblob import TextBlob
import re

# Firebase setup
@st.cache_resource
def init_firebase():
    file_path = "/content/the-brain-app-a0824-firebase-adminsdk-fbsvc-5d3ad34668.json"  # Colab path
    try:
        # Check if Firebase app already exists
        firebase_admin.get_app()
    except ValueError:
        # Initialize Firebase only if not already initialized
        if os.path.exists(file_path):
            cred = credentials.Certificate(file_path)
            firebase_admin.initialize_app(cred)
        elif "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])  # Convert AttrDict to dict
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            raise Exception("Firebase credentials not found! Upload JSON or set secrets.")
    db = firestore.client()
    # Add sample roadmaps
    sample_roadmaps = [
        {"field": "Cricket", "starting_steps": "Join a local club; focus on fitness.", "month1_plan": "Practice batting/bowling 3x/week; watch tutorials.", "uniqueness_tips": "Develop agility for spin bowling if tall."},
        {"field": "Programming", "starting_steps": "Learn Python basics on Codecademy.", "month1_plan": "Build 1 CLI app; contribute to GitHub.", "uniqueness_tips": "Specialize in ML for healthcare apps."},
        {"field": "Music", "starting_steps": "Practice scales daily; use free apps like Yousician.", "month1_plan": "Compose 1 simple song; join online jam sessions.", "uniqueness_tips": "Blend genres like fusion for uniqueness."}
    ]
    for roadmap in sample_roadmaps:
        db.collection('roadmaps').document(roadmap['field']).set(roadmap)
    return db

# Hash password for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Check user
def check_user(user_id, password, db):
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        stored_password = doc.to_dict().get('password', '')
        return stored_password == hash_password(password)
    return False

# Save user (register)
def save_user(user_id, password, db):
    hashed_pw = hash_password(password)
    db.collection('users').document(user_id).set({
        'user_id': user_id,
        'password': hashed_pw,
        'interests': '',
        'hours_per_day': 0.0,
        'distractions': '',
        'streak_days': 0,
        'badges': '',
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'total_hours': 0.0,
        'savings': 0.0,
        'stage': 'Silver'
    })
    return True

# Save profile
def save_profile(user_id, interests, hours_per_day, distractions, db):
    db.collection('users').document(user_id).update({
        'interests': ','.join(interests),
        'hours_per_day': hours_per_day,
        'distractions': distractions,
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    })
    return True

# ML: Progress prediction
def predict_progress(hours_per_day, total_hours=0):
    X = np.array([[1], [2], [3], [4], [5], [6], [8]]).reshape(-1, 1)
    y = np.array([10000/1, 10000/2, 10000/3, 10000/4, 10000/5, 10000/6, 10000/8])
    model = LinearRegression().fit(X, y)
    days_remaining = model.predict(np.array([[hours_per_day]]))[0] - (total_hours / hours_per_day)
    months = max(0, round(days_remaining / 30, 1))
    years = round(months / 12, 1)
    return months, years, total_hours + (hours_per_day * 30)

# NLP: Distraction detection
def detect_distractions(review):
    if review.lower() == 'none':
        return False
    blob = TextBlob(review)
    sentiment = blob.sentiment.polarity
    keywords = ['social media', 'gaming', 'scrolling', 'tv', 'procrastinating']
    has_keywords = any(re.search(keyword, review.lower()) for keyword in keywords)
    return sentiment < 0 or has_keywords

# Update badges
def update_badges(db, user_id, streak_days, stage):
    badges = []
    if streak_days >= 15 and stage == "Silver":
        badges.append('Silver (15 Days Strong!)')
        stage = "Platinum"
    elif streak_days >= 30 and stage == "Platinum":
        badges.append('Platinum (30 Days Unstoppable!)')
        stage = "Gold"
    elif streak_days >= 60 and stage == "Gold":
        badges.append('Gold (60 Days Mastered!)')
    db.collection('users').document(user_id).update({
        'badges': ', '.join(badges),
        'stage': stage
    })
    return badges, stage

# Get roadmap
def get_roadmap(db, field):
    doc = db.collection('roadmaps').document(field).get()
    if doc.exists:
        data = doc.to_dict()
        return data['starting_steps'], data['month1_plan'], data['uniqueness_tips']
    return "Start with basics and build daily habits!", "Focus on 1 month goals.", "Find your unique strength to stand out."

# Daily check-in
def daily_check_in(db, user_id, stage, distractions_avoided, work_done, sleep_early, pushups, water_liters, sugar_avoided, pocket_money, review):
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        data = doc.to_dict()
        streak_days = data.get('streak_days', 0)
        savings = data.get('savings', 0.0)
        total_hours = data.get('total_hours', 0.0)
    else:
        streak_days = 0
        savings = 0.0
        total_hours = 0.0

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
        ("images/motiv4.png", "Discipline is your superpower!")
    ]

    if all_conditions_met:
        streak_days += 1
        total_hours += data.get('hours_per_day', 2.0)
        days_required = 15 if stage == "Silver" else 30 if stage == "Platinum" else 60
        days_left = days_required - streak_days
        image_path, quote = random.choice(motivational_images)
        message = f"Awesome job! {days_left} days left to level up! 🎉 Quote: {quote}"
        badges, stage = update_badges(db, user_id, streak_days, stage)
    else:
        savings += pocket_money
        streak_days = 0
        image_path, quote = motivational_images[0]
        message = f"Oops! {pocket_money} PKR added to savings. Total: {savings} PKR. Try again tomorrow!"

    db.collection('daily_logs').add({
        'user_id': user_id,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'distractions_avoided': distractions_avoided,
        'work_done': work_done,
        'sleep_early': sleep_early,
        'pushups': pushups,
        'water_liters': water_liters,
        'sugar_avoided': sugar_avoided,
        'pocket_money': pocket_money,
        'review': review
    })
    db.collection('users').document(user_id).update({
        'streak_days': streak_days,
        'savings': savings,
        'total_hours': total_hours,
        'stage': stage
    })
    return message, streak_days, savings, image_path, quote

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

            try:
                db = init_firebase()
            except Exception as e:
                st.error(f"Firebase initialization failed: {str(e)}")
                return

            if login_button:
                if user_id and password:
                    if check_user(user_id, password, db):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        doc = db.collection('users').document(user_id).get()
                        st.session_state.stage = doc.to_dict().get('stage', 'Silver') if doc.exists else 'Silver'
                        st.success(f"Welcome back, {user_id}!")
                        st.experimental_rerun()
                    else:
                        st.error("Username or password incorrect. Try again or register.")
                else:
                    st.error("Please enter username and password.")

            if register_button:
                if user_id and password:
                    doc = db.collection('users').document(user_id).get()
                    if doc.exists:
                        st.error("Username already exists! Choose another.")
                    else:
                        save_user(user_id, password, db)
                        st.success(f"Registered successfully, {user_id}! Now login.")
                        st.experimental_rerun()
                else:
                    st.error("Please enter username and password.")
    else:
        # Main app content
        user_id = st.session_state.user_id
        st.header(f"Welcome, {user_id}!")

        # Profile form
        st.header("Complete Your Profile")
        with st.form("profile_form"):
            interests = st.multiselect("Interests", ['Sports', 'Programming', 'Music', 'Art', 'Science', 'Business', 'Health'])
            hours_per_day = st.slider("Daily Hours", 0.0, 12.0, 2.0)
            distractions = st.text_area("Distractions (e.g., 'social media')", value="None")
            submit_profile = st.form_submit_button("Save Profile")
            if submit_profile:
                try:
                    db = init_firebase()
                    save_profile(user_id, interests, hours_per_day, distractions, db)
                    st.success("Profile saved! 🎉")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Profile save failed: {str(e)}")

        # Challenge Overview
        st.header("Do You Want to Change Your Life?")
        st.markdown("**Join the 105 Days Challenge!** Click 'Yes' to see how your life will transform!")
        if st.button("Yes"):
            st.subheader("Your Life After the 105 Days Challenge")
            st.markdown("""
                **Individual Benefits**:
                - **Health**: Feel energetic with 5L water daily, no sugar, and 8 hours sleep.
                - **Focus**: No distractions (social media, gaming) = laser-sharp focus like Elon Musk!
                - **Skills**: Master your field (e.g., Cricket, Programming) with daily practice.
                - **Savings**: Save pocket money for your goals (e.g., cricket gear, courses).
                - **Confidence**: Earn badges (Silver, Platinum, Gold) to boost your self-esteem.
                - **Mindset**: Build a wealthy, positive mindset for unstoppable success.

                **Detailed Rules**:
                - Fill a 30-second daily tick mark form before sleeping.
                - **Silver Stage (15 days)**: Work 2 hours/day, avoid distractions (e.g., no Instagram).
                - **Platinum Stage (30 days)**: Work 4 hours/day, 30 pushups, 5L water.
                - **Gold Stage (60 days)**: Work 6 hours/day, wake at 4 AM, sleep by 9 PM, 50 pushups, no sugar/junk/alcohol.
                - **Failure**: If you miss tasks, add pocket money to savings (e.g., 50 PKR/day).
                - **Success**: Complete tasks daily to earn a motivational wallpaper with a quote (screenshot it!).
                - After 105 days, use savings to invest in your field (e.g., buy equipment, enroll in courses).

                **Fine Details**:
                - **Daily Form**: Takes 30 seconds, tick boxes for tasks (e.g., worked, no distractions).
                - **Distractions**: Social media, gaming, TV, etc., count as failures unless marked 'None'.
                - **Savings**: Pocket money goes to savings if you fail tasks (e.g., 50 PKR/day adds up!).
                - **Badges**: Earn Silver (15 days), Platinum (30 days), Gold (60 days) badges.
                - **Calendar**: Tracks your progress daily, shows completed days with green ticks.
                - **Failure Rule**: If you fail tasks, streak resets to 0, but savings grow.
                - **Success Rule**: Complete tasks daily to maintain streak and earn badges.

                **Stages**:
                - **Silver (15 days)**: Build basic habits (2 hours work, no distractions).
                - **Platinum (30 days)**: Level up with fitness (4 hours work, 30 pushups, 5L water).
                - **Gold (60 days)**: Master discipline (6 hours work, 4 AM wake-up, 9 PM sleep, 50 pushups, no sugar).
            """)
            with st.form("agree_form"):
                agree_button = st.form_submit_button("I Agree & Start Challenge!")
                if agree_button:
                    try:
                        db = init_firebase()
                        st.session_state.stage = "Silver"
                        db.collection('users').document(user_id).update({'stage': 'Silver'})
                        st.success("Challenge started! You're now in Silver stage! 🎉")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Challenge start failed: {str(e)}")

        # Dashboard
        if st.session_state.stage:
            st.header("Your Dashboard")
            try:
                db = init_firebase()
                doc = db.collection('users').document(user_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    field = data.get('interests', 'Cricket').split(',')[0] if data.get('interests') else 'Cricket'
                    streak_days = data.get('streak_days', 0)
                    savings = data.get('savings', 0.0)
                    stage = data.get('stage', 'Silver')
                    st.metric("Stage", stage)
                    st.metric("Streak", f"{streak_days}/{15 if stage == 'Silver' else 30 if stage == 'Platinum' else 60}")
                    st.metric("Savings for Field", f"{savings} PKR")
                    steps, month1, tips = get_roadmap(db, field)
                    st.subheader(f"Roadmap for {field}")
                    st.write(f"**Starting Steps:** {steps}")
                    st.write(f"**1-Month Plan:** {month1}")
                    st.write(f"**Uniqueness Tips:** {tips}")
                else:
                    st.error("User data not found in Firestore!")
            except Exception as e:
                st.error(f"Dashboard load failed: {str(e)}")

            # Progress Calendar
            st.subheader("Progress Calendar")
            try:
                logs = db.collection('daily_logs').where('user_id', '==', user_id).stream()
                log_list = [log.to_dict() for log in logs]
                if log_list:
                    df_logs = pd.DataFrame(log_list)
                    df_logs['date'] = pd.to_datetime(df_logs['date'])
                    df_logs['Completed'] = df_logs.apply(
                        lambda row: (row['distractions_avoided'] and row['work_done']) if stage == "Silver" else
                                    (row['distractions_avoided'] and row['work_done'] and row['pushups'] >= 30 and row['water_liters'] >= 5) if stage == "Platinum" else
                                    (row['distractions_avoided'] and row['work_done'] and row['sleep_early'] and row['pushups'] >= 50 and row['water_liters'] >= 5 and row['sugar_avoided']), axis=1)
                    st.write(df_logs[['date', 'Completed']].set_index('date'))
                else:
                    st.info("Log your first day to see your calendar!")
            except Exception as e:
                st.error(f"Progress calendar failed: {str(e)}")

            # Daily Check-In
            st.header("Daily Check-In (Fill Before Sleeping)")
            with st.form("daily_check_in"):
                st.write("Tick the boxes for today's tasks:")
                distractions_avoided = st.checkbox("I avoided distractions (e.g., no social media, gaming)")
                work_done = st.checkbox(f"I worked {2 if stage == 'Silver' else 4 if stage == 'Platinum' else 6} hours on my field")
                sleep_early = st.checkbox("I slept early (before 9 PM)") if stage == "Gold" else False
                pushups = st.number_input("Pushups done today (30 for Platinum, 50 for Gold)", 0, 100, 0) if stage in ["Platinum", "Gold"] else 0
                water_liters = st.number_input("Water drunk today (liters, 5 for Platinum/Gold)", 0.0, 10.0, 0.0) if stage in ["Platinum", "Gold"] else 0.0
                sugar_avoided = st.checkbox("I avoided sugar/junk/alcohol") if stage == "Gold" else True
                pocket_money = st.number_input("Today's pocket money (PKR)", 0.0, 10000.0, 0.0)
                review = st.text_area("Daily Review (e.g., what went well?)", value="None")
                submit_check_in = st.form_submit_button("Submit Check-In")

                if submit_check_in:
                    try:
                        db = init_firebase()
                        message, streak_days, savings, image_path, quote = daily_check_in(
                            db, user_id, stage, distractions_avoided, work_done, sleep_early, 
                            pushups, water_liters, sugar_avoided, pocket_money, review)
                        st.write(message)
                        try:
                            if os.path.exists(image_path):
                                st.image(image_path, caption=f"{quote} Screenshot this and set as your wallpaper!")
                            else:
                                st.warning(f"Image not found: {image_path}. Please add images to 'images/' folder.")
                        except Exception as e:
                            st.warning(f"Image loading failed: {str(e)}. Continue without images.")
                        st.metric("Current Streak", f"{streak_days} days")
                        st.metric("Savings for Field", f"{savings} PKR")
                        badges, stage = update_badges(db, user_id, streak_days, stage)
                        if badges:
                            st.balloons()
                            st.success(f"🎉 Earned Badges: {', '.join(badges)}")
                        if stage == "Gold" and streak_days >= 60:
                            st.success(f"🎉 Gold Badge Achieved! Use your {savings} PKR to develop your field!")
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
