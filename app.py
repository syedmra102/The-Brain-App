import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
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
            {"field": "Cricket", "starting_steps": "Join a local club; focus on fitness.", "month1_plan": "Practice batting/bowling 3x/week; watch tutorials.", "uniqueness_tips": "Develop agility for spin bowling."},
            {"field": "Programming", "starting_steps": "Learn Python basics on Codecademy.", "month1_plan": "Build 1 CLI app; contribute to GitHub.", "uniqueness_tips": "Specialize in ML for healthcare apps."},
            {"field": "Music", "starting_steps": "Practice scales daily; use Yousician.", "month1_plan": "Compose 1 song; join online jams.", "uniqueness_tips": "Blend genres like fusion."}
        ]
        for roadmap in sample_roadmaps:
            db.collection('roadmaps').document(roadmap['field']).set(roadmap)
        return db

    # Hash password
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
    def save_user(user_id, password, field, hours_per_day, distractions, db):
        hashed_pw = hash_password(password)
        db.collection('users').document(user_id).set({
            'user_id': user_id,
            'password': hashed_pw,
            'field': field,
            'hours_per_day': hours_per_day,
            'distractions': distractions,
            'streak_days': 0,
            'badges': '',
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'total_hours': 0.0,
            'savings': 0.0,
            'stage': 'Silver'
        })
        return True

    # Load synthetic data for ML
    @st.cache_data
    def load_data():
        try:
            data = pd.read_csv("data.csv")
            return data
        except FileNotFoundError:
            st.error("data.csv not found in repo!")
            raise

    # ML: Progress prediction
    def predict_progress(hours_per_day, total_hours=0):
        try:
            data = pd.read_csv("progress_data.csv")
        except FileNotFoundError:
            st.error("progress_data.csv not found in repo!")
            raise
        X = data[['hours']].values
        y = data['days_to_mastery'].values
        model = LinearRegression().fit(X, y)
        days_remaining = model.predict([[hours_per_day]])[0] - (total_hours / hours_per_day)
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

    # Badges
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

    # Roadmap
    def get_roadmap(db, field):
        doc = db.collection('roadmaps').document(field).get()
        if doc.exists:
            data = doc.to_dict()
            return data['starting_steps'], data['month1_plan'], data['uniqueness_tips']
        return "Start with basics.", "Focus on 1-month goals.", "Find your unique strength."

    # Daily check-in
    def daily_check_in(db, user_id, stage, distractions_avoided, work_done, sleep_early, pushups, water_liters, sugar_avoided, pocket_money, review):
        doc = db.collection('users').document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            streak_days = data.get('streak_days', 0)
            savings = data.get('savings', 0.0)
        else:
            streak_days = 0
            savings = 0.0

        all_conditions_met = False
        if stage == "Silver":
            all_conditions_met = (distractions_avoided and work_done)
        elif stage == "Platinum":
            all_conditions_met = (distractions_avoided and work_done and pushups >= 30 and water_liters >= 5)
        elif stage == "Gold":
            all_conditions_met = (distractions_avoided and work_done and sleep_early and pushups >= 50 and water_liters >= 5 and sugar_avoided)

        motivational_images = [
            ("images/motiv1.png", "Tum unstoppable ho!"),
            ("images/motiv2.png", "Every step counts!"),
            ("images/motiv3.png", "Dreams are closer!"),
            ("images/motiv4.png", "Discipline is power!")
        ]

        if all_conditions_met:
            streak_days += 1
            days_required = 15 if stage == "Silver" else 30 if stage == "Platinum" else 60
            days_left = days_required - streak_days
            image_path, quote = random.choice(motivational_images)
            message = f"Great start! {days_left} days left! 🎉 Quote: {quote}"
            badges, stage = update_badges(db, user_id, streak_days, stage)
        else:
            savings += pocket_money
            streak_days = 0
            image_path, quote = motivational_images[0]
            message = f"Failed! {pocket_money} PKR added to savings: {savings} PKR. Try tomorrow!"

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
            'stage': stage
        })
        return message, streak_days, savings, image_path, quote

    # Main app
    def main():
        st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="wide")
        st.title("🧠 The Brain That Helps You to Use Your Brain!!")
        st.markdown("**Change your life in 105 days!**")

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
                            st.experimental_rerun()  # Refresh to show main app
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
                            save_user(user_id, password, "", 0.0, "", db)
                            st.success(f"Registered successfully, {user_id}! Now login.")
                            st.experimental_rerun()  # Refresh to update UI
                    else:
                        st.error("Please enter username and password.")
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
                    try:
                        db = init_firebase()
                        db.collection('users').document(user_id).update({
                            'field': field,
                            'hours_per_day': hours_per_day,
                            'distractions': distractions,
                            'last_updated': datetime.now().strftime('%Y-%m-%d')
                        })
                        st.success("Profile saved!")
                        st.experimental_rerun()  # Refresh to update UI
                    except Exception as e:
                        st.error(f"Profile save failed: {str(e)}")

            # Challenge Overview
            st.header("105 Days Challenge")
            st.markdown("""
            **Change your life in 105 days!** Join our free challenge:
            1. Healthy diet (no sugar, 5L water, 8 hours sleep).
            2. Wake up at 4 AM.
            3. 1 hour exercise.
            4. Sleep early (9 PM).
            5. Deep knowledge in your field.
            6. No laziness.
            7. No distractions.
            8. Wealthy mindset.
            9. Unstoppable focus.
            10. Positive thinking.
            """)
            if st.button("See Rules & Stages"):
                st.markdown("""
                **Stages**:
                - **Silver (15 days)**: 2 hours/day, no distractions.
                - **Platinum (30 days)**: 4 hours/day, 30 pushups, 5L water.
                - **Gold (60 days)**: 6 hours/day, wake at 4 AM, sleep at 9 PM, 50 pushups, no sugar.
                
                **Rules**:
                - Fill daily form (30 seconds).
                - Fail tasks? Add pocket money to savings.
                - Complete tasks? Get motivational wallpaper!
                """)
                with st.form("agree_form"):  # Wrap Agree in a form
                    agree_button = st.form_submit_button("Agree")
                    if agree_button:
                        try:
                            db = init_firebase()
                            st.session_state.stage = "Silver"
                            db.collection('users').document(user_id).update({'stage': 'Silver'})
                            st.success("Challenge started! You're now in Silver stage! 🎉")
                            st.experimental_rerun()  # Refresh to show dashboard
                        except Exception as e:
                            st.error(f"Challenge start failed: {str(e)}")

            # Dashboard
            if st.session_state.stage:
                st.header("Dashboard")
                try:
                    db = init_firebase()
                    doc = db.collection('users').document(user_id).get()
                    if doc.exists:
                        data = doc.to_dict()
                        field = data.get('field', 'Cricket')
                        streak_days = data.get('streak_days', 0)
                        savings = data.get('savings', 0.0)
                        stage = data.get('stage', 'Silver')
                        st.metric("Stage", stage)
                        st.metric("Streak", f"{streak_days}/{15 if stage == 'Silver' else 30 if stage == 'Platinum' else 60}")
                        st.metric("Savings", f"{savings} PKR")
                        steps, month1, tips = get_roadmap(db, field)
                        st.subheader(f"Roadmap for {field}")
                        st.write(f"**Steps:** {steps}")
                        st.write(f"**1-Month Plan:** {month1}")
                        st.write(f"**Tips:** {tips}")
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
                        st.write(df_logs[['date', 'work_done', 'distractions_avoided']].set_index('date'))
                    else:
                        st.info("Log your first day!")
                except Exception as e:
                    st.error(f"Progress calendar failed: {str(e)}")

                # Daily Check-In
                st.header("Daily Check-In")
                with st.form("daily_check_in"):
                    distractions_avoided = st.checkbox("Avoided distractions")
                    work_done = st.checkbox(f"Worked {2 if stage == 'Silver' else 4 if stage == 'Platinum' else 6} hours")
                    sleep_early = st.checkbox("Slept early (9 PM, Gold)") if stage == "Gold" else False
                    pushups = st.number_input("Pushups (30 for Platinum, 50 for Gold)", 0, 100, 0) if stage in ["Platinum", "Gold"] else 0
                    water_liters = st.number_input("Water (liters, 5 for Platinum/Gold)", 0.0, 10.0, 0.0) if stage in ["Platinum", "Gold"] else 0.0
                    sugar_avoided = st.checkbox("Avoided sugar (Gold)") if stage == "Gold" else True
                    pocket_money = st.number_input("Pocket Money (PKR)", 0.0, 10000.0, 0.0)
                    review = st.text_area("Review")
                    submit_check_in = st.form_submit_button("Submit")

                    if submit_check_in:
                        try:
                            db = init_firebase()
                            message, streak_days, savings, image_path, quote = daily_check_in(
                                db, user_id, stage, distractions_avoided, work_done, sleep_early, 
                                pushups, water_liters, sugar_avoided, pocket_money, review)
                            st.write(message)
                            try:
                                if os.path.exists(image_path):
                                    st.image(image_path, caption=f"{quote} Screenshot this!")
                                else:
                                    st.warning(f"Image not found: {image_path}. Please add images to 'images/' folder.")
                            except Exception as e:
                                st.warning(f"Image loading failed: {str(e)}. Continue without images.")
                            st.metric("Streak", f"{streak_days} days")
                            st.metric("Savings", f"{savings} PKR")
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
