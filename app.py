# app.py
# Streamlit app integrating user's exact ML model (unchanged) + auth + 105-challenge flow
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random
import json
import hashlib
import os
from datetime import datetime, timedelta

# ---------------------------
# Helpers: user persistence
# ---------------------------
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2, default=str)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def ensure_user_structure(user):
    # default fields for every user profile
    defaults = {
        "full_name": "",
        "field": "",
        "goal": "",
        "stage": None,
        "stage_start": None,
        "days_left": 0,
        "streak_days": 0,
        "savings": 0.0,
        "penalty_history": [],
        "completed_days": [],
        "selected_distractions": [],
        "badges": [],
    }
    for k,v in defaults.items():
        if k not in user:
            user[k] = v
    return user

# ---------------------------
# Styling & page config
# ---------------------------
st.set_page_config(page_title="Brain · Performance Predictor", page_icon="🧠", layout="centered")

# Snowy mountain background (public image)
bg_url = "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1600&q=80"

st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(30,144,255,0.9), rgba(30,144,255,0.9)), url("{bg_url}");
        background-size: cover;
        color: white;
    }}
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
    }}
    .dashboard-card {{
        background-color: #0b2a52; /* dark blue dashboard panel */
        padding: 18px;
        border-radius: 12px;
    }}
    .green-button > button {{
        background-color: #00b33c !important;
        color: white !important;
        font-weight: 700;
    }}
    .small-muted {{ color: #cfe8ff; font-size:12px; }}
    </style>
    """, unsafe_allow_html=True)

# ---------------------------
# ====== ML MODEL (UNCHANGED) ======
# I copied your provided ML training block verbatim (kept logic unchanged)
# ---------------------------

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
# ===== END ML MODEL (unchanged) =====

# ---------------------------
# App logic: auth / pages
# ---------------------------

users = load_users()
st.sidebar.title("Navigation")
menu = st.sidebar.radio("", ["Home", "Register HR", "Login", "About"])

def register_hr():
    st.header("HR Registration")
    st.info("Register an HR / manager account. You will use this to login and view the dashboard.")
    with st.form("register_form"):
        username = st.text_input("Username (unique)")
        password = st.text_input("Password", type="password")
        full_name = st.text_input("Full name")
        submit = st.form_submit_button("Register", type="primary")
    if submit:
        if not username or not password:
            st.error("Username & password required")
            return
        if username in users:
            st.error("Username already exists")
            return
        users[username] = {
            "password_hash": hash_password(password),
            "full_name": full_name or username,
        }
        ensure_user_structure(users[username])
        save_users(users)
        st.success("Registered! Now go to Login.")

def login():
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        if username not in users:
            st.error("User does not exist. Please Register first.")
            return
        if users[username]["password_hash"] != hash_password(password):
            st.error("Incorrect password.")
            return
        st.success(f"Welcome back, {users[username].get('full_name', username)}!")
        st.session_state["user"] = username

def home():
    st.title("Welcome to Brain — Performance & 105 Challenge")
    st.markdown("This app includes your ML Performance Predictor (unchanged) plus the 105 Challenge program.")
    st.markdown("Use the sidebar to Register as HR, Login, or read About.")

def about():
    st.header("About this app")
    st.markdown("""
    - Blue background + dark blue dashboard panels + green buttons + white text.
    - HR-register -> login -> view dashboard -> run ML model -> enroll in 105 Challenge.
    - The ML model code is kept exactly as provided (no changes to prediction logic).
    """)

# Render selected menu
if menu == "Home":
    home()
elif menu == "Register HR":
    register_hr()
elif menu == "Login":
    login()
elif menu == "About":
    about()

# If logged in, show dashboard and challenge pages
if "user" in st.session_state:
    username = st.session_state["user"]
    user = users.get(username, {})
    user = ensure_user_structure(user)  # ensure fields exist
    users[username] = user
    save_users(users)

    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.subheader(f"Dashboard — {user.get('full_name', username)}")
    st.markdown("<div class='small-muted'>You are logged in as HR/Manager</div>", unsafe_allow_html=True)

    # Show ML model area (exact inputs / prediction logic used from original code)
    st.markdown("---")
    st.subheader("🔎 Performance Predictor (Your ML Model)")
    st.markdown("Enter the details below and press **Predict Performance**. (Model logic unchanged.)")

    with st.form("ml_form"):
        col1, col2 = st.columns(2)
        with col1:
            hours = st.number_input("Daily Study Hours (0.5 - 12)", min_value=0.5, max_value=12.0, value=5.5, step=0.5)
            distractions = st.number_input("Number of Distractions (0 - 15)", min_value=0, max_value=15, value=5, step=1)
        with col2:
            habit_inputs = {}
            for col in categorical_columns:
                friendly_name = col.replace('_', ' ').title()
                habit_inputs[col] = st.selectbox(f"{friendly_name}", ["Yes", "No"])
        ml_submit = st.form_submit_button("Predict Performance", help="Run the XGBoost model")

    if ml_submit:
        # Create input and predict (uses same encoders/scaler/model)
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

        # Feature breakdown (same approach)
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

        # Plot chart (similar style)
        plt.figure(figsize=(10, 6))
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

    st.markdown("---")

    # ------------- 105 Challenge Invitation ----------------
    st.header("🔥 We are running the 105 Challenge — Become Top 1%")
    st.write("This challenge is designed as 3 stages. Complete all stages to get badges, build habit streaks, and save money for your first project.")
    st.info("“We are doing a challenge of 105!! which can make you the top 1% in your field with simple three stages. Do you want to become the top 1%?”")
    if st.button("Become Top 1%", key="become_top"):
        st.session_state["open_challenge"] = True

    # If challenge opened or on click, show challenge intro
    if st.session_state.get("open_challenge", False):
        st.markdown("### How your life will look after this challenge:")
        outcomes = [
            "**Healthy Diet** - No sugar, no alcohol, no junk food; 5L water daily & deep sleep",
            "**Early Rising** - Wake up naturally at 4 AM full of energy",
            "**Peak Fitness** - 1 hour daily exercise, perfect physique",
            "**Quality Sleep** - Deep, restorative sleep by 9 PM",
            "**Expert Skills** - Deep hands-on knowledge in your chosen field",
            "**Unstoppable Character** - Laziness completely removed",
            "**Laser Focus** - All major distractions controlled/removed",
            "**Wealth Mindset** - Financial intelligence & investment habits",
            "**Emotional Mastery** - High EQ, positive thinking, resilience"
        ]
        for o in outcomes:
            st.write("-", o)

        st.markdown("---")
        st.header("Show rules")
        if st.button("Show Rules", key="show_rules"):
            st.session_state["show_rules"] = True

        if st.session_state.get("show_rules", False):
            st.subheader("Stages")
            st.markdown("**1. Silver (Easy) — 15 days**")
            st.markdown("""
            - Give **2 hours daily** in your field  
            - Avoid all distractions for 15 days  
            - Fill the form daily at night on this website
            """)

            st.markdown("**2. Platinum (Medium) — 30 days**")
            st.markdown("""
            - Give **4 hours daily** in your field  
            - Avoid daily distractions  
            - Do **1 hour exercise** daily  
            - Drink **5 liters** of water  
            - Fill the form daily at night on this website
            """)

            st.markdown("**3. Gold (Hard) — 60 days**")
            st.markdown("""
            - Give **6 hours daily** to your field  
            - Do **1 hour exercise** daily  
            - Avoid distractions  
            - Drink **5 liters** of water  
            - Wake up early at 4am or 5am  
            - Sleep early (8pm or 9pm)  
            - Avoid junk food & sugar
            """)

        st.markdown("---")
        # ---------- Profile selection / setup ----------
        st.subheader("Set up your challenge profile")
        st.write("Tell us about the user's field and goals. This will be saved to the user's profile.")

        with st.form("profile_form"):
            field = st.selectbox("What's your field?", ["Programming", "Engineering", "Sports", "AI/ML", "Cybersecurity", "Data Analysis", "Network Engineering", "Cloud Computing", "Other"])
            goal = st.text_input("What do you want to become? (e.g., Doctor, Data Scientist, Entrepreneur)")
            distractions_options = ["Late sleep", "Friends calls", "Social media", "Porn/Masturbation", "Snacking/Junk food", "Laziness", "TV/YouTube", "Gaming"]
            selected_distractions = st.multiselect("Choose distractions to avoid (user-selected)", distractions_options)
            stage_choice = st.radio("Select stage to start with", ["Silver (15 days)", "Platinum (30 days)", "Gold (60 days)"])
            profile_submit = st.form_submit_button("Save Profile")

        if profile_submit:
            # Save profile details into users
            users[username]["field"] = field
            users[username]["goal"] = goal
            users[username]["selected_distractions"] = selected_distractions
            # map stage to days
            if "Silver" in stage_choice:
                stage_days = 15
                stage_key = "Silver"
            elif "Platinum" in stage_choice:
                stage_days = 30
                stage_key = "Platinum"
            else:
                stage_days = 60
                stage_key = "Gold"
            users[username]["stage"] = stage_key
            users[username]["stage_start"] = datetime.utcnow().isoformat()
            users[username]["days_left"] = stage_days
            users[username]["streak_days"] = 0
            users[username]["savings"] = users[username].get("savings", 0.0)
            save_users(users)
            st.success("Profile saved! Your stage and rules will be used in daily forms.")
            st.experimental_rerun()

        st.markdown("---")

        # ---------- Daily routine / checklist ----------
        st.subheader("Daily Routine & Progress")
        u = users[username]
        st.markdown(f"**Stage:** {u.get('stage') or 'Not set'}")
        st.markdown(f"**Days left in stage:** {u.get('days_left', 0)}")
        st.markdown(f"**Streak penalty days:** {u.get('streak_days', 0)}")
        st.markdown(f"**Savings amount:** ${u.get('savings', 0):.2f}")

        st.markdown("### Complete today's checklist")
        # Determine tasks for the stage
        stage = u.get("stage")
        tasks = []
        hours_req = 0
        require_exercise = False
        require_water = False
        require_wakeup = False
        require_sleep_early = False
        require_no_sugar = False
        require_no_junk = False

        if stage == "Silver":
            hours_req = 2
            require_exercise = False
            require_water = False
        elif stage == "Platinum":
            hours_req = 4
            require_exercise = True
            require_water = True
        elif stage == "Gold":
            hours_req = 6
            require_exercise = True
            require_water = True
            require_wakeup = True
            require_sleep_early = True
            require_no_sugar = True
            require_no_junk = True

        # present checkboxes
        with st.form("daily_form"):
            st.write(f"Hours spent on field today (required: {hours_req}):")
            hours_done = st.number_input("Hours spent", min_value=0.0, max_value=24.0, value=0.0, step=0.5)
            check_exercise = st.checkbox("Did 1 hour of exercise today?") if require_exercise else st.checkbox("Exercise (optional)")
            check_water = st.checkbox("Drank 5L water today?") if require_water else st.checkbox("Water (optional)")
            check_wakeup = st.checkbox("Woke up at 4am/5am?") if require_wakeup else st.checkbox("Wake up early (optional)")
            check_sleep_early = st.checkbox("Slept by 8pm/9pm?") if require_sleep_early else st.checkbox("Sleep early (optional)")
            check_no_sugar = st.checkbox("Avoided sugar today?") if require_no_sugar else st.checkbox("No sugar (optional)")
            check_no_junk = st.checkbox("Avoided junk food today?") if require_no_junk else st.checkbox("No junk (optional)")
            # distractions check: ensure all selected distractions avoided
            st.write("Mark that you avoided your chosen distractions today:")
            distractions_avoid_flags = {}
            for d in u.get("selected_distractions", []):
                distractions_avoid_flags[d] = st.checkbox(f"Avoided: {d}")
            notes = st.text_area("Optional notes about today")
            submit_daily = st.form_submit_button("Submit Today's Checklist")
        if submit_daily:
            # Validate
            missing = 0
            missing_reasons = []
            if hours_done < hours_req:
                missing += 1
                missing_reasons.append(f"Hours less than required ({hours_done} < {hours_req})")
            if require_exercise and not check_exercise:
                missing += 1
                missing_reasons.append("Exercise not completed")
            if require_water and not check_water:
                missing += 1
                missing_reasons.append("Water requirement not met")
            if require_wakeup and not check_wakeup:
                missing += 1
                missing_reasons.append("Wake up early not met")
            if require_sleep_early and not check_sleep_early:
                missing += 1
                missing_reasons.append("Sleep early not met")
            if require_no_sugar and not check_no_sugar:
                missing += 1
                missing_reasons.append("Sugar avoided not met")
            if require_no_junk and not check_no_junk:
                missing += 1
                missing_reasons.append("Junk food avoided not met")
            # distractions
            for d, flag in distractions_avoid_flags.items():
                if not flag:
                    missing += 1
                    missing_reasons.append(f"Did not avoid distraction: {d}")

            # decision rules
            if missing == 0:
                # accept the day
                users[username]["completed_days"].append({
                    "date": datetime.utcnow().isoformat(),
                    "notes": notes,
                    "accepted": True,
                    "penalty": 0.0
                })
                users[username]["days_left"] = max(0, users[username].get("days_left", 0) - 1)
                # reset streak penalty days (no penalty for accepted day)
                save_users(users)
                st.success("Day saved ✅ — great job! Day counted as completed.")
            elif missing <= 2:
                # allow penalty payment to accept the day
                st.warning("You missed a few tasks. You may pay a penalty for the day to accept it.")
                penalty = st.number_input("Enter penalty amount to pay (USD)", min_value=0.0, value=1.0, step=0.5)
                pay = st.button("Pay penalty & accept day")
                if pay:
                    users[username]["savings"] += float(penalty)  # pay into the savings (as requirement)
                    users[username]["completed_days"].append({
                        "date": datetime.utcnow().isoformat(),
                        "notes": notes,
                        "accepted": True,
                        "penalty": float(penalty),
                        "reasons": missing_reasons
                    })
                    users[username]["penalty_history"].append({"date": datetime.utcnow().isoformat(), "amount": float(penalty), "reasons": missing_reasons})
                    users[username]["days_left"] = max(0, users[username].get("days_left", 0) - 1)
                    users[username]["streak_days"] = users[username].get("streak_days", 0) + 1
                    save_users(users)
                    st.success("Day accepted after penalty payment. It has been saved.")
                else:
                    st.info("Pay penalty to accept the day, or revise your checklist.")
            else:
                # missing > 2 -> day rejected even if paying
                users[username]["completed_days"].append({
                    "date": datetime.utcnow().isoformat(),
                    "notes": notes,
                    "accepted": False,
                    "penalty": 0.0,
                    "reasons": missing_reasons
                })
                users[username]["streak_days"] = users[username].get("streak_days", 0) + 1
                save_users(users)
                st.error("Day NOT accepted. You missed too many tasks (more than 2). This day does not count even if you try to pay a penalty.")

            # If stage days finished:
            if users[username]["days_left"] == 0:
                st.balloons()
                st.success(f"🎉 Stage {users[username]['stage']} completed! You earned a badge.")
                badge_name = f"{users[username]['stage']}_badge"
                if badge_name not in users[username]["badges"]:
                    users[username]["badges"].append(badge_name)
                    save_users(users)
                # ask to upgrade
                next_stage = None
                if users[username]["stage"] == "Silver":
                    next_stage = "Platinum"
                elif users[username]["stage"] == "Platinum":
                    next_stage = "Gold"
                else:
                    next_stage = None
                if next_stage:
                    if st.button(f"Upgrade to {next_stage}"):
                        if next_stage == "Platinum":
                            users[username]["stage"] = "Platinum"
                            users[username]["days_left"] = 30
                        elif next_stage == "Gold":
                            users[username]["stage"] = "Gold"
                            users[username]["days_left"] = 60
                        users[username]["stage_start"] = datetime.utcnow().isoformat()
                        save_users(users)
                        st.success(f"Upgraded to {next_stage} — good luck!")
                else:
                    st.info("All stages completed. Well done — you've finished the 105 Challenge!")
    # end challenge block

    st.markdown("---")
    # show some profile summary and badges
    st.subheader("Profile summary")
    st.write(f"**Name:** {users[username].get('full_name') or username}")
    st.write(f"**Field:** {users[username].get('field') or 'Not set'}")
    st.write(f"**Goal / Profession:** {users[username].get('goal') or 'Not set'}")
    st.write(f"**Stage:** {users[username].get('stage') or 'Not set'}")
    st.write(f"**Days left:** {users[username].get('days_left',0)}")
    st.write(f"**Savings:** ${users[username].get('savings',0):.2f}")
    st.write("**Badges earned:**", users[username].get("badges", []))
    st.markdown("---")

    # logout
    if st.button("Logout"):
        st.session_state.pop("user", None)
        st.success("Logged out")
        st.experimental_rerun()
