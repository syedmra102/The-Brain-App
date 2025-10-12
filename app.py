import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random
import streamlit as st
import json
import os
import hashlib
from datetime import datetime, timedelta

# ===== STREAMLIT PAGE CONFIG =====
st.set_page_config(
    page_title="Performance Predictor",
    page_icon="📊",
    layout="centered",
)

# ===== CUSTOM CSS =====
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://source.unsplash.com/random/1920x1080/?mountain,snow,ice,white');
        background-size: cover;
        color: black;
    }
    .stButton>button {
        background-color: #00FF00; /* Green buttons */
        color: white;
        font-weight: bold;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ===== DATA FILES =====
USERS_FILE = 'users.json'
USER_DATA_FILE = 'user_data.json'

# Load or initialize users
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# Load or initialize user data
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'r') as f:
        user_data = json.load(f)
else:
    user_data = {}
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f)

# ===== HELPER FUNCTIONS =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def save_user_data():
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f)

def get_today():
    return datetime.now().date().isoformat()

def check_last_submission(username):
    if 'last_submission' in user_data[username]:
        last_date = datetime.fromisoformat(user_data[username]['last_submission']).date()
        return last_date == datetime.now().date()
    return False

# ===== REAL WORLD DATA COLLECTION =====
def create_real_world_dataset():
    N = 500
    data = []
    for _ in range(N):
        hours = np.clip(np.random.normal(loc=5.5, scale=2.5), 0.5, 10.0)
        distraction_count = int(np.clip(np.random.normal(loc=6, scale=3.5), 0, 15))
        avoid_sugar = random.choices(['Yes', 'No'], weights=[0.4, 0.6])[0]
        avoid_junk_food = random.choices(['Yes', 'No'], weights=[0.45, 0.55])[0]
        drink_5L_water = random.choices(['Yes', 'No'], weights=[0.35, 0.65])[0]
        exercise_daily = random.choices(['Yes', 'No'], weights=[0.5, 0.5])[0]
        sleep_early = random.choices(['Yes', 'No'], weights=[0.4, 0.6])[0]
        wakeup_early = 'Yes' if sleep_early == 'Yes' and random.random() < 0.7 else 'No'
        score = (hours * 15) - (distraction_count * 7)
        score += 25 if avoid_sugar == 'Yes' else -10
        score += 20 if avoid_junk_food == 'Yes' else -5
        score += 15 if drink_5L_water == 'Yes' else -5
        score += 30 if sleep_early == 'Yes' else -15
        score += 15 if exercise_daily == 'Yes' else -5
        score += 10 if wakeup_early == 'Yes' else 0
        if score > 150:
            score_noise = np.random.normal(0, 0.5)
        else:
            score_noise = np.random.normal(0, 8)
        final_score = score + score_noise
        percentile = np.clip(100 - (final_score / 2.5), 1.0, 99.9)
        data.append({
            "hours": round(hours, 1),
            "avoid_sugar": avoid_sugar,
            "avoid_junk_food": avoid_junk_food,
            "drink_5L_water": drink_5L_water,
            "sleep_early": sleep_early,
            "exercise_daily": exercise_daily,
            "wakeup_early": wakeup_early,
            "distraction_count": distraction_count,
            "top_percentile": round(percentile, 1)
        })
  
    return pd.DataFrame(data)

# ===== DATASET =====
df = create_real_world_dataset()

# ===== LABEL ENCODING =====
encoders = {}
categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water",
                       "sleep_early", "exercise_daily", "wakeup_early"]
for col in categorical_columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

# ===== FEATURE SCALING =====
numeric_columns = ['hours', 'distraction_count']
scaler = StandardScaler()
df_scaled = df.copy()
df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])
X = df_scaled.drop(columns=['top_percentile'])
y = df_scaled['top_percentile']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ===== MODEL TRAINING =====
model = XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=5,
    reg_lambda=1.0,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model.fit(X_train, y_train)

# ===== SESSION STATE INITIALIZATION =====
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# ===== LOGIN/REGISTER PAGE =====
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if login_username in users and users[login_username] == hash_password(login_password):
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.session_state.page = 'dashboard'
                if login_username not in user_data:
                    user_data[login_username] = {
                        'profile': None,
                        'current_stage': None,
                        'days_left': 0,
                        'streak_days': 0,
                        'savings': 0.0,
                        'last_submission': None,
                        'badges': []
                    }
                    save_user_data()
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        if st.button("Register"):
            if reg_password != reg_confirm:
                st.error("Passwords do not match")
            elif reg_username in users:
                st.error("Username already exists")
            else:
                users[reg_username] = hash_password(reg_password)
                save_users()
                st.success("Registered successfully! Please login.")

else:
    username = st.session_state.username
    data = user_data[username]

    # ===== DASHBOARD PAGE =====
    if st.session_state.page == 'dashboard':
        st.title(f"📊 Performance Predictor Dashboard - {username}")
        st.subheader("Enter your details:")
        hours = st.number_input("Daily Study Hours (0.5 - 12)", min_value=0.5, max_value=12.0, value=5.5)
        distractions = st.number_input("Number of Distractions (0 - 15)", min_value=0, max_value=15, value=5)
        habit_inputs = {}
        for col in categorical_columns:
            friendly_name = col.replace('_', ' ').title()
            habit_inputs[col] = st.selectbox(f"{friendly_name}", ["Yes", "No"])
        
        if st.button("Predict Performance"):
            input_data = pd.DataFrame([{
                'hours': hours,
                'distraction_count': distractions,
                **{col: encoders[col].transform([val])[0] for col, val in habit_inputs.items()}
            }])
            input_data[numeric_columns] = scaler.transform(input_data[numeric_columns])
            input_data = input_data[X.columns]
            prediction = model.predict(input_data)[0]
            prediction = max(1, min(100, prediction))
            st.success(f"🎯 Your Overall Performance: Top {prediction:.1f}%")
            
            # ===== FEATURE BREAKDOWN CHART =====
            feature_percentiles = {}
            hours_percentile = (df['hours'] <= hours).mean() * 100
            feature_percentiles['Study Hours'] = max(1, 100 - hours_percentile)
            dist_percentile = (df['distraction_count'] >= distractions).mean() * 100
            feature_percentiles['Distraction Control'] = max(1, 100 - dist_percentile)
          
            habit_mapping = {
                'avoid_sugar': 'Sugar Avoidance',
                'avoid_junk_food': 'Junk Food Avoidance',
                'drink_5L_water': 'Water Intake',
                'sleep_early': 'Sleep Schedule',
                'exercise_daily': 'Exercise Routine',
                'wakeup_early': 'Wake-up Time'
            }
            for col, friendly_name in habit_mapping.items():
                val = encoders[col].transform([habit_inputs[col]])[0]
                if val == 1:
                    habit_percentile = (df[col] == 1).mean() * 100
                    feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
                else:
                    habit_percentile = (df[col] == 0).mean() * 100
                    feature_percentiles[friendly_name] = max(1, habit_percentile)
            
            plt.figure(figsize=(12, 8))
            features = list(feature_percentiles.keys())
            percentiles = list(feature_percentiles.values())
            bars = plt.bar(features, percentiles, color='blue', edgecolor='darkblue')
            plt.bar_label(bars, labels=[f'Top {p:.1f}%' for p in percentiles], label_type='edge', padding=2, fontweight='bold', fontsize=8, color='white')
            plt.xlabel('Performance Features', fontweight='bold', fontsize=12)
            plt.title(f'PERFORMANCE BREAKDOWN ANALYSIS (Top {prediction:.1f}%)', fontweight='bold', fontsize=14)
            plt.ylabel('Performance Percentile', fontweight='bold', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.ylim(0, 100)
            st.pyplot(plt)
        
        st.markdown("We are doing a challenge of 105!! which become u the top 1% in your field with simple three stages did u want to become the top 1% ?")
        if st.button("become top 1%"):
            st.session_state.page = 'challenge_intro'
            st.rerun()

    # ===== CHALLENGE INTRO PAGE =====
    elif st.session_state.page == 'challenge_intro':
        st.title("How your life is looking after this challenge")
        st.markdown("""
        - **Healthy Diet** - No sugar, no alcohol, no junk food; 5L water daily & deep sleep
        - **Early Rising** - Wake up naturally at 4 AM full of energy
        - **Peak Fitness** - 1 hour daily exercise, perfect physique
        - **Quality Sleep** - Deep, restorative sleep by 9 PM
        - **Expert Skills** - Deep hands-on knowledge in your chosen field
        - **Unstoppable Character** - Laziness completely removed
        - **Laser Focus** - All major distractions controlled/removed
        - **Wealth Mindset** - Financial intelligence & investment habits
        - **Emotional Mastery** - High EQ, positive thinking, resilience
        """)
        if st.button("show rules"):
            st.session_state.page = 'rules'
            st.rerun()

    # ===== RULES PAGE =====
    elif st.session_state.page == 'rules':
        st.title("Challenge Rules")
        st.markdown("""
        there r here stages
        1.Silver (Easy)(15 days):
        1. You have to give just 2 hours daily in ur field !!
        2. Avoiding your all distractions for just 15 days !!
        3. filling the form daily at night of your day at this website !!
           2.Platinium (Medium)(30 days):
           1. frstly u have to put 4 hours every day on your field !!
           2. after that u have to avoid your daily distraction !!
           3. doing 1 hour excersice daily !!
           4. Drinking 5 liters of water !!
           5. filling the form daily at night at this website !!
              3.Gold(hard)(60 days ):
              1. in this frsly you have to give 6 hours daily at your field !!
              2. doing 1 hours of excersice
              3. avoiding distraction
              4. drinking 5 liters of water
              5. Wake up early like 4am or 5am!!
              6. sleeping early like 8pm or 9pm
              7. avoid junk food !!
              8. avoid sugar
                 Listen if you skip any rule at any stage of your day so you have to pay your whole day pocket money or anything you get or earn to your saving and you will just open this saving after 105 days after completing all the stages and u will use that money for making your first prject and idea in your field and help u to utilize that money on your field !!
        """)
        st.subheader("Create Your Profile")
        field = st.text_input("What's your field? (e.g., programming, engineering, Sports)")
        goal = st.text_input("What do you want to become? (e.g., doctor)")
        distractions_options = ["masturbation", "friends calls", "late sleep", "laziness", "social media", "gaming", "tv", "others"]
        selected_distractions = st.multiselect("Select your distractions", distractions_options)
        stage_options = ["Silver", "Platinum", "Gold"]
        selected_stage = st.selectbox("Which stage do you want to select?", stage_options)
        
        if st.button("save profile"):
            data['profile'] = {
                'field': field,
                'goal': goal,
                'distractions': selected_distractions
            }
            data['current_stage'] = selected_stage
            if selected_stage == "Silver":
                data['days_left'] = 15
            elif selected_stage == "Platinum":
                data['days_left'] = 30
            elif selected_stage == "Gold":
                data['days_left'] = 60
            data['streak_days'] = 0
            data['savings'] = 0.0
            save_user_data()
            st.session_state.page = 'daily_form'
            st.rerun()

    # ===== DAILY FORM PAGE =====
    elif st.session_state.page == 'daily_form':
        if data['profile'] is None:
            st.error("Please create profile first.")
            st.session_state.page = 'rules'
            st.rerun()
        else:
            st.title("Daily Routine Form")
            st.subheader(f"Stage: {data['current_stage']}")
            st.subheader(f"Days Left: {data['days_left']}")
            st.subheader(f"Streak Days: {data['streak_days']}")
            st.subheader(f"Savings: ${data['savings']:.2f}")
            st.subheader(f"Username: {username}")
            st.subheader(f"Field: {data['profile']['field']}")
            st.subheader(f"Goal: {data['profile']['goal']}")
            st.subheader(f"Distractions: {', '.join(data['profile']['distractions'])}")
            
            if check_last_submission(username):
                st.info("You have already submitted for today.")
            else:
                stage_rules = {
                    "Silver": [
                        "Gave 2 hours in field",
                        "Avoided all distractions",
                    ],
                    "Platinum": [
                        "Gave 4 hours in field",
                        "Avoided distractions",
                        "Did 1 hour exercise",
                        "Drank 5L water",
                    ],
                    "Gold": [
                        "Gave 6 hours in field",
                        "Did 1 hour exercise",
                        "Avoided distractions",
                        "Drank 5L water",
                        "Woke up early (4am or 5am)",
                        "Slept early (8pm or 9pm)",
                        "Avoided junk food",
                        "Avoided sugar",
                    ]
                }
                rules = stage_rules[data['current_stage']]
                checks = {}
                for rule in rules:
                    checks[rule] = st.checkbox(rule)
                
                if st.button("Submit Day"):
                    unchecked = sum(1 for v in checks.values() if not v)
                    if unchecked == 0:
                        data['days_left'] -= 1
                        data['last_submission'] = get_today()
                        save_user_data()
                        st.success("Your day is saved!")
                        if data['days_left'] == 0:
                            data['badges'].append(data['current_stage'])
                            if data['current_stage'] == "Silver":
                                data['current_stage'] = "Platinum"
                                data['days_left'] = 30
                            elif data['current_stage'] == "Platinum":
                                data['current_stage'] = "Gold"
                                data['days_left'] = 60
                            elif data['current_stage'] == "Gold":
                                st.success("Congratulations! You completed the 105-day challenge!")
                            save_user_data()
                            st.success(f"You completed {data['badges'][-1]} stage! Badge awarded.")
                        st.info("Your last task is to go to Google find a good motivational page and set as a wallpaper because when I wake up tomorrow so u see ur mobile and remember that u r on a admission and don't distracted")
                    elif unchecked <= 2:
                        penalty = st.number_input("Pay penalty amount to save day", min_value=0.0)
                        if st.button("Pay Penalty"):
                            if penalty > 0:
                                data['savings'] += penalty
                                data['streak_days'] += 1
                                data['days_left'] -= 1
                                data['last_submission'] = get_today()
                                save_user_data()
                                st.success("Day saved with penalty.")
                                if data['days_left'] == 0:
                                    data['badges'].append(data['current_stage'])
                                    if data['current_stage'] == "Silver":
                                        data['current_stage'] = "Platinum"
                                        data['days_left'] = 30
                                    elif data['current_stage'] == "Platinum":
                                        data['current_stage'] = "Gold"
                                        data['days_left'] = 60
                                    elif data['current_stage'] == "Gold":
                                        st.success("Congratulations! You completed the 105-day challenge!")
                                    save_user_data()
                                    st.success(f"You completed {data['badges'][-1]} stage! Badge awarded.")
                                st.info("Your last task is to go to Google find a good motivational page and set as a wallpaper because when I wake up tomorrow so u see ur mobile and remember that u r on a admission and don't distracted")
                            else:
                                st.error("Penalty must be greater than 0.")
                    else:
                        st.error("Too many tasks missed. Day not accepted, even with penalty.")
