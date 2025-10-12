# ===== IMPORTS AND INITIAL SETUP =====
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random
import streamlit as st
import time

# --- STATE MANAGEMENT INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_db' not in st.session_state:
    st.session_state.user_db = {} # Stores user profiles: {'username': {'password': '...', 'profile': {...}, 'challenge': {...}}}
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# --- CONSTANTS FOR THE CHALLENGE ---
CHALLENGE_STAGES = {
    'Silver': {
        'duration': 15,
        'rules': {
            'Give 2 hours daily in your field': True,
            'Avoid all distractions': True,
            'Fill the form daily': True,
        }
    },
    'Platinum': {
        'duration': 30,
        'rules': {
            'Give 4 hours daily in your field': True,
            'Avoid all distractions': True,
            'Do 1 hour of exercise daily': True,
            'Drink 5 liters of water': True,
            'Fill the form daily': True,
        }
    },
    'Gold': {
        'duration': 60,
        'rules': {
            'Give 6 hours daily in your field': True,
            'Do 1 hour of exercise': True,
            'Avoid all distractions': True,
            'Drink 5 liters of water': True,
            'Wake up early (4 AM or 5 AM)': True,
            'Sleep early (8 PM or 9 PM)': True,
            'Avoid junk food': True,
            'Avoid sugar': True,
            'Fill the form daily': True,
        }
    }
}

# --- PAGE CONFIGURATION & CUSTOM CSS (Sidebar Text Fix Applied) ---
st.set_page_config(
    page_title="Elite Performance Engine",
    page_icon="👑",
    layout="wide",
)

# Custom CSS for a professional, clean look (White Mountain Snow Ice concept)
st.markdown(
    """
    <style>
    /* White Mountain Snow Ice theme: Light background, cool accents */
    .stApp {
        background-color: #F8F8FF; /* Ghost White (Snow/Ice) */
        color: #333333; /* Default text color set to dark for visibility */
    }
    .stButton>button {
        background-color: #1E90FF; /* Dodger Blue (Mountain Sky) */
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stSelectbox label, .stNumberInput label, .stTextInput label, .stCheckbox label, .stRadio label {
        color: #000080; /* Navy Blue labels */
        font-weight: 600;
    }
    h1, h2, h3, h4 {
        color: #000080; /* Navy Blue headings */
    }
    .main-header {
        color: #1E90FF;
        font-size: 36px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 20px;
    }
    /* FIX: Ensure sidebar text is dark and visible */
    [data-testid="stSidebar"] * {
        color: #333333 !important;
    }
    /* Override for sidebar headings to be Navy Blue */
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #000080 !important;
    }
    .stSuccess {
        background-color: #E6FFE6; /* Light green for success */
        color: #006600;
        border-radius: 5px;
        padding: 10px;
    }
    .stError {
        background-color: #FFE6E6; /* Light red for error */
        color: #CC0000;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- UTILITY FUNCTIONS ---

# --- PERSISTENT DATA GENERATION AND MODEL TRAINING (UNCHANGED ML CODE) ---
@st.cache_resource
def load_ml_model():
    """Loads and trains the ML model and preprocessing tools once."""
    
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

    df = create_real_world_dataset()
    encoders = {}
    categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water",
                           "sleep_early", "exercise_daily", "wakeup_early"]
    for col in categorical_columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
    numeric_columns = ['hours', 'distraction_count']
    scaler = StandardScaler()
    df_scaled = df.copy()
    df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])
    X = df_scaled.drop(columns=['top_percentile'])
    y = df_scaled['top_percentile']
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = XGBRegressor(
        n_estimators=1000, learning_rate=0.05, max_depth=5, reg_lambda=1.0, 
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    model.fit(X_train, y_train)
    
    return model, df, encoders, scaler, X.columns, categorical_columns, numeric_columns

# Load model and data components
model, df, encoders, scaler, X_cols, cat_cols, num_cols = load_ml_model()


# --- AUTHENTICATION FUNCTIONS ---

def register_user():
    st.subheader("New User Registration")
    new_user = st.text_input("Choose Username", key="reg_user")
    new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
    
    if st.button("Register"):
        if new_user in st.session_state.user_db:
            st.error("Username already exists.")
        elif not new_user or not new_pass:
            st.error("Username and Password cannot be empty.")
        else:
            st.session_state.user_db[new_user] = {
                'password': new_pass,
                'profile': {},
                'challenge': {'status': 'Pending', 'stage': None, 'day_start': None, 'daily_log': {}, 'penalty_amount': 0.0, 'badges': [], 'stage_days_completed': 0, 'streak_days_penalty': 0}
            }
            st.success("Registration successful! Please log in.")
            st.session_state.page = 'login'
            st.rerun()

def login_user():
    st.markdown('<p class="main-header">Elite Performance Engine</p>', unsafe_allow_html=True)
    st.subheader("User Login")
    user = st.text_input("Username", key="log_user")
    password = st.text_input("Password", type="password", key="log_pass")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            if user in st.session_state.user_db and st.session_state.user_db[user]['password'] == password:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success(f"Welcome back, {user}!")
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid Username or Password.")
    with col2:
        if st.button("Go to Register"):
            st.session_state.page = 'register'
            st.rerun()

# --- ML PREDICTION APP LOGIC ---

def predict_performance_ui():
    st.title("🎯 ML Performance Predictor")
    st.subheader(f"Hello, {st.session_state.username}!")
    st.markdown("""
        <div style="background-color: #000080; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
        <h4 style="color: white; margin: 0;">
        We are doing a challenge of 105 days! This can make you the Top 1% in your field with simple stages. Do you want to become the Top 1%?
        </h4>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Become Top 1%"):
        st.session_state.page = 'challenge_intro'
        st.rerun()

    st.markdown("---")
    st.header("Current Performance Assessment")
    
    col1, col2 = st.columns(2)
    with col1:
        hours = st.number_input("Daily Study Hours (0.5 - 12)", min_value=0.5, max_value=12.0, value=5.5, key="pred_hours")
        distractions = st.number_input("Number of Distractions (0 - 15)", min_value=0, max_value=15, value=5, key="pred_distractions")
    
    habit_inputs = {}
    with col2:
        # Group habit inputs
        for col in cat_cols:
            friendly_name = col.replace('_', ' ').title()
            habit_inputs[col] = st.selectbox(f"{friendly_name}", ["Yes", "No"], key=f"pred_{col}")

    if st.button("Predict Performance", key="run_predict"):
        
        # 1. Prepare input data
        encoded_habits = {col: encoders[col].transform([val])[0] for col, val in habit_inputs.items()}
        input_data = pd.DataFrame([{
            'hours': hours,
            'distraction_count': distractions,
            **encoded_habits
        }])
        
        # 2. Scale and Predict
        input_data[num_cols] = scaler.transform(input_data[num_cols])
        input_data = input_data[X_cols]
        prediction = model.predict(input_data)[0]
        prediction = max(1, min(100, prediction))
        
        st.success(f"🎯 Your Predicted Overall Performance: Top {prediction:.1f}%")

        # 3. Feature Breakdown
        feature_percentiles = {}
        
        # Hours
        hours_percentile = (df['hours'] <= hours).mean() * 100
        feature_percentiles['Study Hours'] = max(1, 100 - hours_percentile)
        # Distractions
        dist_percentile = (df['distraction_count'] >= distractions).mean() * 100
        feature_percentiles['Distraction Control'] = max(1, 100 - dist_percentile)
        
        # Habits
        habit_mapping = {
            'avoid_sugar': 'Sugar Avoidance', 'avoid_junk_food': 'Junk Food Avoidance', 
            'drink_5L_water': 'Water Intake', 'sleep_early': 'Sleep Schedule', 
            'exercise_daily': 'Exercise Routine', 'wakeup_early': 'Wake-up Time'
        }
        for col, friendly_name in habit_mapping.items():
            val = encoded_habits[col]
            if val == 1:
                habit_percentile = (df[col] == 1).mean() * 100
                feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
            else:
                habit_percentile = (df[col] == 0).mean() * 100
                feature_percentiles[friendly_name] = max(1, habit_percentile)
        
        # 4. Plot Chart
        plt.style.use('default') # Use a clean default style
        fig, ax = plt.subplots(figsize=(10, 6))
        
        features = list(feature_percentiles.keys())
        percentiles = list(feature_percentiles.values())
        
        # Create a light color palette for the Snow Ice theme
        colors = ['#ADD8E6' if p > 50 else '#1E90FF' for p in percentiles] # Light Blue for Average/Dark Blue for Elite
        
        bars = ax.bar(features, percentiles, color=colors, edgecolor='#000080')
        
        # Set text color for labels to BLACK 
        ax.bar_label(bars, labels=[f'Top {p:.1f}%' for p in percentiles], 
                     label_type='edge', padding=2, fontweight='bold', fontsize=8, color='black') 
        
        # Ensure axis and title text is dark
        ax.set_xlabel('Performance Features', fontweight='bold', fontsize=10, color='black')
        ax.set_title(f'PERFORMANCE BREAKDOWN (Predicted: Top {prediction:.1f}%)', fontweight='bold', fontsize=12, color='#000080')
        ax.set_ylabel('Performance Percentile', fontweight='bold', fontsize=10, color='black')
        ax.tick_params(axis='x', colors='black') 
        ax.tick_params(axis='y', colors='black') 

        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.ylim(0, 100)
        
        st.pyplot(fig)

# --- CHALLENGE PAGES LOGIC ---

def challenge_intro_ui():
    st.title('👑 The 105-Day Challenge: Your Path to the Top 1%')
    
    st.header("How Your Life Will Look After This Challenge:")
    
    goals = [
        "**Healthy Diet:** No sugar, no alcohol, no junk food; 5L water daily & deep sleep.",
        "**Early Rising:** Wake up naturally at 4 AM full of energy.",
        "**Peak Fitness:** 1 hour daily exercise, perfect physique.",
        "**Quality Sleep:** Deep, restorative sleep by 9 PM.",
        "**Expert Skills:** Deep hands-on knowledge in your chosen field.",
        "**Unstoppable Character:** Laziness completely removed.",
        "**Laser Focus:** All major distractions controlled/removed.",
        "**Wealth Mindset:** Financial intelligence & investment habits.",
        "**Emotional Mastery:** High EQ, positive thinking, resilience.",
    ]
    
    for goal in goals:
        st.markdown(f"✅ {goal}")
        
    st.markdown("---")
    
    if st.button("Show Rules"):
        st.session_state.page = 'challenge_rules'
        st.rerun()

def challenge_rules_ui():
    st.title("⚖️ Challenge Rules and Stages")
    st.markdown("To achieve the Top 1% performance, you must successfully complete all three stages over **105 days**.")
    
    for stage, data in CHALLENGE_STAGES.items():
        st.subheader(f"{stage} Stage ({data['duration']} days)")
        st.markdown("---")
        for rule in data['rules']:
            st.markdown(f"➡️ **{rule}**")
    
    st.markdown("---")
    st.header("The Penalty System: The Ultimate Commitment")
    st.markdown(
        """
        Listen: If you skip **any** rule at **any** stage of your day, you must pay the **whole day's pocket money or earnings** into your dedicated **Challenge Saving**.
        You can only open this saving after **completing all 105 days**. This money must then be used to fund your **first project or idea** in your chosen field, helping you utilize your new skills!
        """
    )
    
    if st.button("Start Challenge Setup"):
        st.session_state.page = 'challenge_setup'
        st.rerun()

def challenge_setup_ui():
    user_data = st.session_state.user_db[st.session_state.username]
    st.title("⚙️ Challenge Profile Setup")
    
    st.header("1. Define Your Focus")
    field = st.selectbox("What is your field?", ['Programming', 'Engineering', 'Sports', 'Medicine (Doctor)', 'Art/Design', 'Other'], key='setup_field')
    goal = st.text_input("What do you want to become? (e.g., AI Engineer, Neurosurgeon, Pro-Athlete)", key='setup_goal')
    
    st.header("2. Select Your Distractions")
    all_distractions = ['Masterbation/Pornography', 'Friends Calls/Socializing', 'Late Sleep', 'Laziness/Procrastination', 'Unhealthy Gaming', 'Endless Social Media Scroll']
    selected_distractions = st.multiselect("Select ALL your major daily distractions:", all_distractions, key='setup_distractions')

    st.header("3. Choose Your Starting Stage")
    stage_selection = st.radio("Which stage do you want to select?", list(CHALLENGE_STAGES.keys()), key='setup_stage')
    
    # Show goals for the selected stage
    st.subheader(f"Rules for the **{stage_selection}** Stage:")
    st.info("\n".join([f"• {rule}" for rule in CHALLENGE_STAGES[stage_selection]['rules']]))
    
    if st.button("Save Profile and Start Challenge"):
        if not goal or not selected_distractions:
            st.error("Please fill out your goal and select your distractions.")
        else:
            # Update user profile
            user_data['profile'] = {
                'field': field,
                'goal': goal,
                'distractions': selected_distractions,
            }
            # Initialize challenge state
            user_data['challenge']['status'] = 'Active'
            user_data['challenge']['stage'] = stage_selection
            user_data['challenge']['stage_days_completed'] = 0
            user_data['challenge']['stage_start_date'] = pd.Timestamp.today().date().strftime('%Y-%m-%d')
            user_data['challenge']['current_rules'] = CHALLENGE_STAGES[stage_selection]['rules']
            
            st.success("Profile saved! Your challenge starts now.")
            st.session_state.page = 'daily_tracking'
            st.rerun()

def display_user_profile(user_data):
    st.sidebar.markdown(f"## 👤 **{st.session_state.username}**")
    profile = user_data['profile']
    challenge = user_data['challenge']
    
    st.sidebar.markdown(f"**Goal:** {profile.get('goal', 'N/A')}")
    st.sidebar.markdown(f"**Field:** {profile.get('field', 'N/A')}")
    st.sidebar.markdown("---")

    if challenge['stage']:
        st.sidebar.markdown(f"### Current Stage: **{challenge['stage']}**")
        
        st.sidebar.markdown("**Your Daily Distractions:**")
        # Ensure list items are visible
        for d in profile.get('distractions', []):
            st.sidebar.markdown(f"• *{d}*")
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Daily Rules:**")
        for rule in challenge.get('current_rules', {}):
             st.sidebar.markdown(f"• *{rule}*")
    else:
        st.sidebar.info("Challenge not yet started.")

def daily_tracking_ui():
    user_data = st.session_state.user_db[st.session_state.username]
    profile = user_data['profile']
    challenge = user_data['challenge']

    if challenge['status'] != 'Active':
        st.error("Please start the challenge first in the Setup page.")
        if st.button("Go to Setup"):
            st.session_state.page = 'challenge_setup'
            st.rerun()
        return

    # --- TOP METRICS ---
    current_stage_data = CHALLENGE_STAGES[challenge['stage']]
    days_in_stage = current_stage_data['duration']
    days_left = days_in_stage - challenge['stage_days_completed']
    
    st.title("📅 Daily Challenge Tracker")
    st.markdown(f"Hello, **{st.session_state.username}**! You are becoming a **{profile['goal']}**.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stage", challenge['stage'])
    col2.metric("Days Left in Stage", days_left)
    col3.metric("Penalty Streak (Days)", challenge.get('streak_days_penalty', 0))
    col4.metric("Total Saving", f"PKR {challenge['penalty_amount']:,.2f}")
    
    st.markdown("---")
    st.header(f"Today's **{challenge['stage']}** Rules Checklist")
    
    # --- DAILY CHECKLIST ---
    rules = challenge['current_rules']
    checklist = {}
    
    # Create checkboxes for all rules EXCEPT "Fill the form daily"
    for rule in rules:
        if rule != 'Fill the form daily': 
            checklist[rule] = st.checkbox(f"✅ {rule}", key=f"check_{rule}")
    
    st.subheader("Penalty and Pocket Money")
    penalty_input = st.number_input("If you failed any task, enter your daily pocket money/earning for the penalty (PKR):", min_value=0.0, value=0.0, key='penalty_input')

    if st.button("Save Daily Routine"):
        
        # 1. Check Compliance
        completed_tasks = sum(checklist.values())
        total_tasks = len(rules) - 1 # Exclude 'Fill the form daily'
        tasks_skipped = total_tasks - completed_tasks
        
        # 2. Enforcement Logic
        if tasks_skipped == 0:
            # PERFECT DAY (Tasks Skipped = 0)
            st.success("🎉 Day Saved! 100% Compliant! No Penalty!")
            
            # Update challenge stats
            user_data['challenge']['stage_days_completed'] += 1
            # Reset streak if day was perfect
            user_data['challenge']['streak_days_penalty'] = 0 
            
        elif tasks_skipped > 0 and penalty_input > 0.0:
            # DAY SAVED WITH PENALTY 
            
            # Day is not accepted if more than 2 tasks are skipped *even if money is paid*.
            if tasks_skipped > 2:
                st.error(
                    "❌ Day NOT Accepted! You skipped more than 2 tasks (only 2 skips allowed with penalty). "
                    "Focus on improving compliance tomorrow."
                )
                return
            
            st.warning(f"⚠️ Day Saved with Penalty. You skipped {tasks_skipped} task(s).")
            
            # Update challenge stats
            user_data['challenge']['stage_days_completed'] += 1
            user_data['challenge']['streak_days_penalty'] = user_data['challenge'].get('streak_days_penalty', 0) + 1
            user_data['challenge']['penalty_amount'] += penalty_input
            
        else:
            # DAY FAILED - Skipped tasks OR penalty not paid
            if tasks_skipped > 0 and penalty_input == 0.0:
                 st.error(
                    "❌ ERROR: Day NOT Accepted! You failed one or more tasks and did not pay the penalty. "
                    "You must pay the full pocket money amount to save the day count."
                )
            else:
                 st.error(
                    "❌ ERROR: Day NOT Accepted. You must meet the daily challenges or pay the penalty."
                )
            return
            
        # 3. Last Task & Day Progression
        st.markdown("---")
        st.subheader("Your Last Task for the Day:")
        st.info("Go to Google, find a good motivational image/quote, and **set it as your phone wallpaper**. When you wake up, you will be reminded of your mission!")
        
        # Check if stage is completed
        check_stage_completion(user_data)
        
        # Rerun to update metrics
        time.sleep(1) # Pause for success message to be read
        st.rerun()

def check_stage_completion(user_data):
    challenge = user_data['challenge']
    current_stage = challenge['stage']
    current_stage_data = CHALLENGE_STAGES[current_stage]
    
    if challenge['stage_days_completed'] >= current_stage_data['duration']:
        
        # Add badge
        user_data['challenge']['badges'].append(current_stage)
        st.balloons()
        st.success(f"🌟 CONGRATULATIONS! You have completed the **{current_stage}** stage! You earned the {current_stage} Badge!")
        
        # Determine next stage
        stages_order = list(CHALLENGE_STAGES.keys())
        current_index = stages_order.index(current_stage)
        
        if current_index < len(stages_order) - 1:
            # Upgrade to next stage
            next_stage = stages_order[current_index + 1]
            st.info(f"Do you want to upgrade to the **{next_stage}** stage?")
            
            # Note: This button handles the upgrade logic
            if st.button(f"Yes, Upgrade to {next_stage}"):
                # Reset and upgrade
                challenge['stage'] = next_stage
                challenge['stage_days_completed'] = 0
                challenge['stage_start_date'] = pd.Timestamp.today().date().strftime('%Y-%m-%d')
                challenge['current_rules'] = CHALLENGE_STAGES[next_stage]['rules']
                st.session_state.page = 'daily_tracking'
                st.rerun()
        else:
            # Challenge complete
            challenge['status'] = 'Completed'
            st.header("🏆 105-DAY CHALLENGE COMPLETE! 🏆")
            st.balloons()
            st.success(f"You have finished all stages! Open your saving of **PKR {challenge['penalty_amount']:,.2f}** to fund your project!")
            st.session_state.page = 'dashboard'
            st.rerun()

# --- MAIN PAGE ROUTER ---

def main_app():
    if st.session_state.logged_in:
        display_user_profile(st.session_state.user_db[st.session_state.username])
        
        if st.session_state.page == 'dashboard':
            predict_performance_ui()
        elif st.session_state.page == 'challenge_intro':
            challenge_intro_ui()
        elif st.session_state.page == 'challenge_rules':
            challenge_rules_ui()
        elif st.session_state.page == 'challenge_setup':
            challenge_setup_ui()
        elif st.session_state.page == 'daily_tracking':
            daily_tracking_ui()
        
        # Sidebar Navigation
        st.sidebar.markdown("---")
        if st.sidebar.button("Go to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
        st.sidebar.markdown(f"**Badges Earned:** {', '.join(st.session_state.user_db[st.session_state.username]['challenge']['badges']) or 'None'}")
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.page = 'login'
            st.rerun()
    else:
        if st.session_state.page == 'register':
            register_user()
        else:
            login_user()

if __name__ == "__main__":
    main_app()
