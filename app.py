import streamlit as st
import json, os
from datetime import datetime
import numpy as np
import pandas as pd
from streamlit_lottie import st_lottie

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

# ---------------- Styling ----------------
def inject_style():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    .stApp {
        background-image: url('images/background.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background: linear-gradient(180deg, #0b57a4 0%, #0b69c3 100%);
        color: white;
        min-height: 100vh;
        padding-bottom: 40px;
    }
    .stApp::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        z-index: -1;
    }
    .stApp, .stApp * { color: #ffffff !important; }
    h1, h2, h3, p, div, .stButton>button, .stTextInput, .stSlider, .stSelectbox {
        font-family: 'Poppins', sans-serif !important;
    }
    h1 {
        font-weight: 700;
        color: #FFD700;
        text-align: center;
    }
    h2, h3 {
        font-weight: 600;
        color: #E0E0E0;
    }
    p, div {
        font-weight: 400;
        color: #FFFFFF;
    }
    .stButton>button {
        background: linear-gradient(45deg, #FF4B4B, #FF6B6B) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #FF6B6B, #FF8C8C) !important;
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4) !important;
    }
    input, textarea, .stTextInput, .stNumberInput, .stSelectbox {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid #4b6cb7 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(8, 61, 107, 0.9) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #eaf6ff !important;
    }
    .card {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(5px);
    }
    .center-box {
        max-width: 800px;
        margin: 30px auto;
        background: rgba(43, 0, 0, 0.8);
        border: 2px solid #FF4D4D;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }
    .center-box h3 {
        color: #ffdcdc;
        margin-top: 0;
    }
    .center-box p {
        color: #ffecec;
    }
    .center-box-success {
        max-width: 800px;
        margin: 30px auto;
        background: rgba(0, 43, 0, 0.8);
        border: 2px solid #4DFF4D;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }
    .center-box-success h3 {
        color: #dcfdc1;
        margin-top: 0;
    }
    .center-box-success p {
        color: #ecffe3;
    }
    @media (max-width: 600px) {
        .stApp {
            background-size: cover;
            padding: 10px;
        }
        h1 {
            font-size: 24px;
        }
        .stButton>button {
            width: 100%;
            padding: 10px !important;
        }
        .card {
            padding: 15px;
        }
        .center-box, .center-box-success {
            margin: 15px;
            padding: 15px;
        }
    }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    """
    st.markdown(css, unsafe_allow_html=True)

# Load Lottie animations
def load_lottiefile(filepath: str):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except:
        return None

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
    """Day failed AND penalty skipped. Day is NOT counted, but useless days increment."""
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
            lottie = load_lottiefile("animations/badge.json")
            if lottie:
                st_lottie(lottie, height=150)
            st.success("🏆 CONGRATULATIONS! You earned the **Silver Badge**!")
        profile["stage"] = "Platinum"
        profile["streak_days"] = 0
        profile["hours_per_day"] = 4.0
        st.success("🌟 You have advanced to the **Platinum Stage**! New goals await.")
        promoted = True
    
    elif current_stage == "Platinum" and current_streak >= PLATINUM_DAYS:
        if "Silver" in current_badges:
            if "Platinum" not in current_badges:
                profile["badges"].append("Platinum")
                lottie = load_lottiefile("animations/badge.json")
                if lottie:
                    st_lottie(lottie, height=150)
                st.success("🌟 PHENOMENAL! You earned the **Platinum Badge**!")
            profile["stage"] = "Gold"
            profile["streak_days"] = 0
            profile["hours_per_day"] = 6.0
            st.success("👑 You have advanced to the **Gold Stage**! You are nearly unstoppable.")
            promoted = True
        else:
            st.warning("You must earn the Silver Badge before progressing to Platinum stage!")
    
    elif current_stage == "Gold" and current_streak >= GOLD_DAYS:
        if "Silver" in current_badges and "Platinum" in current_badges:
            if "Gold" not in current_badges:
                profile["badges"].append("Gold")
                lottie = load_lottiefile("animations/badge.json")
                if lottie:
                    st_lottie(lottie, height=150)
                st.balloons()
                st.success("👑 MISSION COMPLETE! You earned the **Gold Badge** and finished the **105-Day Challenge!**")
                profile["joined"] = False
            promoted = True

    if promoted:
        save_store(store)

# ---------------- Predictor and Pages ----------------
TRENDING_FIELDS = ["AI", "Programming", "Cybersecurity", "Data Science", "Content Creation", "Finance", "Health", "Design"]
DISTRACTIONS_MASTER = ["Social media", "Gaming", "YouTube", "Scrolling news", "TV/Netflix", "Sleep late", "Friends/Calls", "Browsing random sites"]

def predict_percentile(field, hours_per_day, distractions_list, sugar_avoided, exercise_daily, water_liters, avoid_junkfood, woke_4am, slept_9pm):
    field_popularity = {"AI":60,"Programming":55,"Cybersecurity":50,"Data Science":55,"Content Creation":45,"Finance":50,"Health":50,"Design":48}
    base = field_popularity.get(field,50)
    hours_score = min(max(hours_per_day/12,0),1)*40
    distraction_penalty = min(len(distractions_list),8)*4
    sugar_bonus = 8 if sugar_avoided else -6
    exercise_bonus = 8 if exercise_daily else -8
    water_bonus = min(water_liters,5)/5*8
    junk_bonus = 4 if avoid_junkfood else -6
    sleep_bonus = 6 if (woke_4am and slept_9pm) else (-4 if not slept_9pm else 2)
    raw = base + hours_score - distraction_penalty + sugar_bonus + exercise_bonus + water_bonus + junk_bonus + sleep_bonus
    pct = int(np.clip((raw/120)*100, 1, 99))
    return pct

def page_login():
    st.markdown("<h2 style='color:#FFD700;'>Login / Register</h2>", unsafe_allow_html=True)
    with st.form("auth"):
        col1, col2 = st.columns([2,1])
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        with col2:
            login_btn = st.form_submit_button("Login")
            register_btn = st.form_submit_button("Register")
    if register_btn:
        try:
            create_user(username, password)
            st.success("Registered successfully. Now login.")
        except ValueError as e:
            st.error(str(e))
    if login_btn:
        if check_user(username, password):
            st.session_state.user = username
            st.success("Logged in.")
            st.session_state.page = "predict"
            st.rerun()
        else:
            st.error("Invalid credentials.")

def page_predict():
    st.header("Quick Prediction — Where do you stand?")
    st.markdown("<p style='color:#E0E0E0;'>Answer a few quick questions to estimate your current focus potential.</p>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("<h3 style='color:#FFD700;'>Snapshot</h3>", unsafe_allow_html=True)
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.markdown(f"<p><strong>User:</strong> {st.session_state.user}</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Stage:</strong> {p.get('stage')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Field:</strong> {p.get('field') or 'Not set'}</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Savings:</strong> {p.get('savings',0.0)} PKR</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Badges:</strong> {' '.join([f'✅ {b}' for b in p.get('badges',[])]) or 'None'}</p>", unsafe_allow_html=True)
        st.markdown("---")
        if st.session_state.user and st.button("Open Profile"):
            st.session_state.page = "profile"
            st.rerun()

    if "pred_inputs" not in st.session_state:
        st.session_state.pred_inputs = {}

    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        field = st.selectbox("Choose a trending field", TRENDING_FIELDS, index=TRENDING_FIELDS.index(st.session_state.pred_inputs.get("field", TRENDING_FIELDS[0])) if st.session_state.pred_inputs.get("field") in TRENDING_FIELDS else 0)
        hours = st.slider("Hours/day you spend on this field", 0.0, 12.0, float(st.session_state.pred_inputs.get("hours", 2.0)), 0.5)
        st.markdown("<h3 style='color:#E0E0E0;'>Which distractions do you face now?</h3>", unsafe_allow_html=True)
        current_distractions = st.multiselect("", DISTRACTIONS_MASTER, default=st.session_state.pred_inputs.get("distractions", []))
        sugar = st.checkbox("I avoid sugar", value=st.session_state.pred_inputs.get("avoid_sugar", False))
        exercise = st.checkbox("I exercise daily (30-60 min)", value=st.session_state.pred_inputs.get("exercise", False))
        water = st.number_input("Liters of water/day", 0.0, 10.0, float(st.session_state.pred_inputs.get("water", 2.0)), 0.5)
        avoid_junk = st.checkbox("I avoid junk food today", value=st.session_state.pred_inputs.get("avoid_junk", False))
        woke4 = st.checkbox("I wake ~4:00 AM", value=st.session_state.pred_inputs.get("woke4", False))
        sleep9 = st.checkbox("I sleep ~9:00 PM", value=st.session_state.pred_inputs.get("sleep9", False))
        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.pred_inputs = {
        "field": field, "hours": hours, "distractions": current_distractions,
        "avoid_sugar": sugar, "exercise": exercise, "water": water,
        "avoid_junk": avoid_junk, "woke4": woke4, "sleep9": sleep9
    }

    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, current_distractions, sugar, exercise, water, avoid_junk, woke4, sleep9)
        st.markdown("<div class='center-box-success'>", unsafe_allow_html=True)
        st.success(f"Estimated Focus Potential: {pct}%. You are ahead of {pct}% of people.")
        lottie = load_lottiefile("animations/success.json")
        if lottie:
            st_lottie(lottie, height=150)
        if pct >= 60:
            st.info(f"You're in top {pct}%. With a focused plan top 1% is reachable.")
        elif pct >= 40:
            st.info(f"You are around top {pct}%. A plan will accelerate progress.")
        else:
            st.warning(f"You are around {pct}%. Start consistent daily habits.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.write("Do you want our free stage-based plan to become top 1% (skills + health)?")
        if st.button("Yes — Make me top 1% (Free plan)", key="accept_plan"):
            st.session_state.page = "offer"
            st.rerun()
        if st.session_state.user:
            update_profile(st.session_state.user, {
                "field": st.session_state.pred_inputs["field"],
                "distractions": st.session_state.pred_inputs["distractions"]
            })
            st.session_state.page = "offer"
            st.rerun()

def page_offer():
    st.header("How your life will look after the Challenge")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    benefits = [
        "Healthy Diet: No sugar, no alcohol, no junk food; 5L water daily & deep sleep",
        "Wake up early at 4 AM",
        "1 hour exercise daily",
        "Sleep early on time",
        "Deep hands-on knowledge in your field",
        "A different character — laziness removed",
        "All major distractions controlled/removed",
        "A wealthy & investment mindset",
        "Unstoppable focus and character",
        "Positive thinking with high EQ"
    ]
    for i,b in enumerate(benefits,1):
        st.markdown(f"**{i}.** {b}")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Show Rules & Start Challenge"):
        st.session_state.page = "rules"
        st.rerun()
    if st.button("Back to Prediction"):
        st.session_state.page = "predict"
        st.rerun()

def page_rules():
    st.header("Stages & Rules")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
**Easy (Silver)** — **15 days** streak required:
- Work **2 hours/day**.
- Avoid distractions (no scrolling).
- Fill daily checkbox form before sleeping.

**Medium (Platinum)** — **30 days** streak required:
- Work **4 hours/day**.
- Drink **5L water/day** + **30 pushups**.
- Avoid distractions; fill nightly form.

**Hard (Gold)** — **60 days** streak required:
- Wake **4 AM**, sleep **9 PM**.
- **1 hour** morning exercise.
- Work **6 hours/day**.
- **5L water**, **no sugar**, **50 pushups**, **no junk food**.
- Daily positive mirror talk.

---

### ⚠️ The Failure Rule (Discipline Nudge)

If you fail any task, you have two choices:
1.  **Pay the Penalty (Day Counts as Success):** Pay the amount of pocket money you intended to save today. This money is **added to your savings**, and your **streak continues/increases**. The day is **recorded as SUCCESS (Paid Penalty)**.
2.  **Don't Count This Day (Skip Day):** The day is **NOT recorded** (no savings), your streak **resets to 0** (because you failed the effort), and the day is counted as **useless** to reflect the lost opportunity. You must re-do today's full effort tomorrow.

This enforces the habit: either you commit fully, or you pay to acknowledge failure and save for the future, or you reset your streak and count a useless day.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Start Challenge (Join now)"):
        if not st.session_state.user:
            st.error("Please login first.")
        else:
            update_profile(st.session_state.user, {"joined": True, "started_on": datetime.now().strftime("%Y-%m-%d"), "stage": "Silver", "streak_days": 0, "savings": 0.0, "useless_days": 0, "badges": []})
            st.success("Challenge started. Please complete your profile.")
            lottie = load_lottiefile("animations/success.json")
            if lottie:
                st_lottie(lottie, height=150)
            st.session_state.page = "profile"
            st.rerun()
    if st.button("Back to Offer"):
        st.session_state.page = "offer"
        st.rerun()

def page_profile():
    if not st.session_state.user:
        st.error("Login first to edit profile.")
        return
    u = st.session_state.user
    prof = store["users"][u]["profile"]
    st.header("Your Profile — Edit & Save")
    STAGE_GOAL_MAP = {"Silver": 2.0, "Platinum": 4.0, "Gold": 6.0}
    with st.form("profile_form"):
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            field = st.text_input("Chosen Field (What you want to become)", value=prof.get("field",""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests", []))
            distractions = st.multiselect("Your common distractions", DISTRACTIONS_MASTER, default=prof.get("distractions", []))
        with right:
            current_stage = prof.get("stage", "Silver")
            stage = st.selectbox("Current Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(current_stage))
            auto_hours = STAGE_GOAL_MAP.get(stage, 0.0)
            st.markdown(f"<p><strong>Hours/day Goal:</strong> {auto_hours} hours (Set automatically by Stage)</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Savings:</strong> {prof.get('savings',0.0)} PKR</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Streak days:</strong> {prof.get('streak_days',0)}</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Useless days:</strong> {prof.get('useless_days',0)}</p>", unsafe_allow_html=True)
        save = st.form_submit_button("Save Profile")
        st.markdown("</div>", unsafe_allow_html=True)
    if save:
        update_profile(u, {
            "field": field, 
            "interests": interests, 
            "hours_per_day": auto_hours, 
            "stage": stage, 
            "distractions": distractions
        })
        st.success("Profile saved. Opening Daily Routine.")
        lottie = load_lottiefile("animations/success.json")
        if lottie:
            st_lottie(lottie, height=150)
        st.session_state.page = "daily"
        st.rerun()
    st.markdown("---")
    st.subheader("Profile Summary")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    prof = store["users"][u]["profile"]
    st.markdown(f"<p><strong>Field:</strong> {prof.get('field','Not set')}</p>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Hours/day goal:</strong> {prof.get('hours_per_day',0)}</p>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Current Stage:</strong> {prof.get('stage','Silver')}</p>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Badges:</strong> {' '.join([f'✅ {b}' for b in prof.get('badges',[])]) or 'None'}</p>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Savings:</strong> {prof.get('savings',0.0)} PKR</p>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Streak days:</strong> {prof.get('streak_days',0)}</p>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Useless days:</strong> {prof.get('useless_days',0)}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def page_daily():
    if not st.session_state.user:
        st.error("Login first.")
        return
    username = st.session_state.user
    prof = store["users"][username]["profile"]
    check_and_update_stage(username, prof.get("streak_days", 0))
    st.header("Daily Routine — Stage-Specific Checklist")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Stage", f"{prof.get('stage','Silver')} ({prof.get('hours_per_day', 0.0)} hr goal)")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Current Streak", prof.get('streak_days',0))
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Total Savings (PKR)", prof.get('savings',0.0))
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'><strong>Badges:</strong> {' '.join([f'✅ {b}' for b in prof.get('badges',[])]) or 'None'}</p>", unsafe_allow_html=True)
    st.markdown("---")
    stage = prof.get("stage","Silver")
    if stage == "Silver":
        questions = [("work_done",f"Did you work at least {prof.get('hours_per_day', 2.0)} hours today in your field?"),
                     ("distraction",f"Did you avoid distractions today (no scrolling)?"),
                     ("avoid_junk","Did you avoid junk food today?")]
    elif stage == "Platinum":
        questions = [("work_done",f"Did you work at least {prof.get('hours_per_day', 4.0)} hours today in your field?"),
                     ("distraction","Did you avoid distractions today (no scrolling)?"),
                     ("pushups","Did you do at least 30 pushups today?"),
                     ("water_liters","Did you drink at least 5 liters of water today?"),
                     ("avoid_junk","Did you avoid junk food today?")]
    else:
        questions = [("work_done",f"Did you work at least {prof.get('hours_per_day', 6.0)} hours today in your field?"),
                     ("distraction","Did you avoid distractions today (no scrolling)?"),
                     ("pushups","Did you do at least 50 pushups today?"),
                     ("water_liters","Did you drink at least 5 liters of water today?"),
                     ("sugar_avoided","Did you avoid sugar today?"),
                     ("woke_4am","Did you wake ~4:00 AM today?"),
                     ("slept_9pm","Did you sleep around 9:00 PM last night?"),
                     ("avoid_junk","Did you avoid junk food today?")]
    today_key = datetime.now().strftime("%Y%m%d")
    responses = {}
    with st.form("daily_form"):
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for key,label in questions:
            widget_key = f"{username}_{today_key}_{key}" 
            responses[key] = st.checkbox(label, key=widget_key)
        pocket_key = f"{username}_{today_key}_pocket"
        pocket_money = st.number_input("Pocket money to save today (PKR):", 0.0, 10000.0, 0.0, 1.0, key=pocket_key)
        submit = st.form_submit_button("Submit Today's Check")
        st.markdown("</div>", unsafe_allow_html=True)
    if submit:
        success = all(responses.values())
        log = {
            "stage": stage,
            "work_done": responses.get("work_done", False),
            "distraction": responses.get("distraction", False), 
            "woke_4am": responses.get("woke_4am", None),
            "slept_9pm": responses.get("slept_9pm", None),
            "sugar_avoided": responses.get("sugar_avoided", None),
            "avoid_junk": responses.get("avoid_junk", None),
            "pocket_money": float(pocket_money)
        }
        log["pushups"] = 0
        if "pushups" in responses and responses["pushups"]: 
            log["pushups"] = 30 if stage == "Platinum" else 50
        log["water_liters"] = 0.0
        if "water_liters" in responses and responses["water_liters"]:
            log["water_liters"] = 5.0
        if success:
            st.markdown("<div class='center-box-success'>", unsafe_allow_html=True)
            if float(pocket_money) > 0:
                record_day_with_penalty(username, log, success_status="Success (Plus Bonus Savings)")
                st.success(f"🎉 PERFECT DAY! You completed all tasks AND saved {pocket_money} PKR! Streak continues!")
            else:
                record_day_with_penalty(username, log, success_status="Success")
                st.success("✅ Excellent — all tasks completed! Streak continues!")
            lottie = load_lottiefile("animations/success.json")
            if lottie:
                st_lottie(lottie, height=150)
            st.markdown("<h3>Choose Your Motivational Wallpaper!</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.image("images/motiv1.jpg", caption="Wallpaper 1: Rise Up!", use_column_width=True)
            with col2:
                st.image("images/motiv2.jpg", caption="Wallpaper 2: Keep Going!", use_column_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.balloons()
            st.rerun()
        else:
            st.markdown(
                """
                <div class='center-box'>
                  <h3>⚠️ Day Failed — Decide Your Penalty</h3>
                  <p>You missed one or more required tasks today. <strong>You must pay the penalty to save the day (SUCCESS).</strong></p>
                  <p>If you choose <strong>Don't Count This Day</strong>, your streak <strong>resets to 0</strong> and the day is counted as <strong>useless</strong>.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols = st.columns([1,1])
            with cols[0]:
                pay_amt = float(pocket_money) 
                if st.button(f"Pay {pay_amt} PKR & Count Day (SUCCESS)", key=f"pay_{username}_{today_key}"):
                    if pay_amt <= 0:
                        st.error("Enter an amount greater than 0 to pay the penalty and save the day.")
                    else:
                        log["pocket_money"] = pay_amt
                        record_day_with_penalty(username, log, success_status="Success (Paid Penalty)")
                        st.markdown("<div class='center-box-success'>", unsafe_allow_html=True)
                        st.success(f"Penalty paid {pay_amt} PKR. The day is saved as SUCCESS and your streak continues!")
                        lottie = load_lottiefile("animations/success.json")
                        if lottie:
                            st_lottie(lottie, height=150)
                        st.markdown("<h3>Choose Your Motivational Wallpaper!</h3>", unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image("images/motiv1.jpg", caption="Wallpaper 1: Rise Up!", use_column_width=True)
                        with col2:
                            st.image("images/motiv2.jpg", caption="Wallpaper 2: Keep Going!", use_column_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.rerun()
            with cols[1]:
                if st.button("Don't Count This Day (Skip & Reset Streak)", key=f"skip_{username}_{today_key}"):
                    record_failed_day_skip(username)
                    st.warning("This day will NOT be counted, streak reset to 0, and a useless day counted. You must do all of the same efforts **today** (re-submit this form tomorrow).")
                    st.rerun()
    logs = [l for l in store["logs"] if l["user"] == username]
    if logs:
        st.markdown("---")
        st.subheader(f"Full Activity Log (Current Stage: {stage})")
        df = pd.DataFrame(logs).sort_values("date", ascending=False)
        base_cols = ["date", "stage", "result", "work_done", "distraction"]
        platinum_cols = ["pushups", "water_liters"]
        gold_cols = ["sugar_avoided", "woke_4am", "slept_9pm"]
        all_cols = list(set(base_cols + platinum_cols + gold_cols + ["pocket_money"]))
        df_clean = pd.DataFrame({col: df.get(col) for col in all_cols})
        df_clean = df_clean.dropna(axis=1, how='all')
        display_names = {
            "work_done
