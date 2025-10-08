# app.py
# The Brain - 105 Days (v3)
# Single-file Streamlit app (local data.json storage)
# Features:
# - Login/Register with password length validation (ValueError)
# - ML-style percentile prediction (distractions input is on main ML page)
# - Flow: Prediction -> Offer -> Rules -> Profile -> Daily Routine (auto-navigation)
# - Profile editable (including distractions). Saving profile redirects to Daily Routine.
# - Sidebar shows profile summary including distractions.
# - Daily routine shows only tasks relevant to the current stage.
# - Silver stage includes a checkbox "Engaged in distractions today?" (interpreted as failure if True)
# - Blue background, white text, green buttons, navy sidebar
# - Uses st.rerun() (compatible with modern Streamlit)
#
# Save this file as app.py. Requirements: streamlit, pandas, numpy

import streamlit as st
import json
import os
from datetime import datetime
import numpy as np
import pandas as pd

DATA_FILE = "data.json"

# ----------------- Storage helpers -----------------
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

# ----------------- Styling -----------------
def inject_style():
    css = """
    <style>
    .stApp {
      background: linear-gradient(180deg,#0b57a4 0%, #0b69c3 100%);
      color: white;
      min-height: 100vh;
    }
    .stApp, .stApp * { color: #ffffff !important; }
    div.stButton > button, .stButton button {
      background-color: #1db954 !important;
      color: white !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
    }
    div.stButton > button:hover, .stButton button:hover {
      background-color: #169e43 !important;
      transform: translateY(-1px);
    }
    section[data-testid="stSidebar"] { background-color: #083d6b !important; }
    section[data-testid="stSidebar"] * { color: #eaf6ff !important; }
    input, textarea { background-color: rgba(255,255,255,0.04) !important; color: white !important; }
    .card { background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ----------------- User helpers -----------------
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
            "stage": "Silver",  # Silver / Platinum / Gold
            "streak_days": 0,
            "savings": 0.0,
            "started_on": None,
            "joined": False,
            "useless_days": 0,
            "distractions": []   # user-specified distractions
        }
    }
    save_store(store)
    return True

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

def add_daily_log(username, log):
    entry = {"user": username, "date": datetime.now().strftime("%Y-%m-%d"), **log}
    store["logs"].append(entry)
    # Update profile metrics
    profile = store["users"][username]["profile"]
    stage = profile.get("stage", "Silver")
    required_hours = 2 if stage == "Silver" else (4 if stage == "Platinum" else 6)
    # For Silver stage we interpret 'engaged_in_distraction' -> fail if True
    engaged_distraction = log.get("engaged_distraction", False)
    success = (log.get("work_done_hours", 0) >= required_hours) and (not engaged_distraction)
    if stage == "Platinum":
        success = success and (log.get("pushups", 0) >= 30) and (log.get("water_liters", 0) >= 5) and (not engaged_distraction)
    if stage == "Gold":
        success = success and (log.get("pushups", 0) >= 50) and (log.get("water_liters", 0) >= 5) and log.get("sugar_avoided", False) and log.get("woke_4am", False) and log.get("slept_9pm", False) and (not engaged_distraction)
    if success:
        profile["streak_days"] = profile.get("streak_days", 0) + 1
    else:
        # failed: add pocket money to savings and increment useless days
        profile["savings"] = round(profile.get("savings", 0.0) + float(log.get("pocket_money", 0.0)), 2)
        profile["useless_days"] = profile.get("useless_days", 0) + 1
    save_store(store)

def user_logs(username):
    return [l for l in store["logs"] if l["user"] == username]

# ----------------- Predictor (heuristic) -----------------
TRENDING_FIELDS = ["AI", "Programming", "Cybersecurity", "Data Science", "Content Creation", "Finance", "Health", "Design"]
DISTRACTIONS_MASTER = ["Social media", "Gaming", "YouTube", "Scrolling news", "TV/Netflix", "Sleep late", "Friends/Calls", "Browsing random sites"]

def predict_percentile(field, hours_per_day, distractions_list, sugar_avoided, exercise_daily, water_liters, junk_food, woke_4am, slept_9pm):
    field_popularity = {
        "AI": 60, "Programming": 55, "Cybersecurity": 50, "Data Science": 55,
        "Content Creation": 45, "Finance": 50, "Health": 50, "Design": 48
    }
    base = field_popularity.get(field, 50)
    hours_score = min(max(hours_per_day / 12, 0), 1) * 40
    distraction_penalty = min(len(distractions_list), 8) * 4
    sugar_bonus = 8 if sugar_avoided else -6
    exercise_bonus = 8 if exercise_daily else -8
    water_bonus = min(water_liters, 5) / 5 * 8
    junk_penalty = -6 if junk_food else 4
    sleep_bonus = 6 if (woke_4am and slept_9pm) else (-4 if not slept_9pm else 2)
    raw = base + hours_score - distraction_penalty + sugar_bonus + exercise_bonus + water_bonus + junk_penalty + sleep_bonus
    pct = int(np.clip((raw / 120) * 100, 1, 99))
    return pct

# ----------------- Pages -----------------
def page_login():
    st.markdown("<h2 style='color:white;'>Login or Register</h2>", unsafe_allow_html=True)
    with st.form("auth_form"):
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
            st.error(f"Registration error: {e}")
    if login_btn:
        if check_user(username, password):
            st.session_state.user = username
            st.success("Logged in.")
            # After login go to prediction page
            st.session_state.page = "predict"
            st.rerun()
        else:
            st.error("Invalid credentials.")

def page_predict():
    st.header("Quick Prediction — Where do you stand globally?")
    st.markdown("Answer a few quick questions. The model returns a rough percentile (1-99).")
    # Sidebar summary only
    with st.sidebar:
        st.markdown("### Profile Snapshot")
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.write(f"**User:** {st.session_state.user}")
            st.write(f"**Stage:** {p.get('stage')}")
            st.write(f"**Field:** {p.get('field') or 'Not set'}")
            st.write(f"**Hours/day goal:** {p.get('hours_per_day',0)}")
            st.write(f"**Savings:** {p.get('savings',0.0)} PKR")
            st.markdown("---")
        st.markdown("Quick Nav")
        if st.session_state.user:
            if st.button("Go to Profile"):
                st.session_state.page = "profile"
                st.rerun()
    # Main inputs (including distractions here)
    field = st.selectbox("Choose a trending field to evaluate", TRENDING_FIELDS)
    hours = st.slider("Hours/day you spend on this field", 0.0, 12.0, 2.0, 0.5)
    st.markdown("### Which distractions do you face now? (select all that apply)")
    current_distractions = st.multiselect("", DISTRACTIONS_MASTER, default=[])
    sugar = st.checkbox("I avoid sugar")
    exercise = st.checkbox("I exercise daily (30-60 min)")
    water = st.number_input("Liters of water/day", 0.0, 10.0, 2.0, 0.5)
    junk = st.checkbox("I eat junk food often")
    woke4 = st.checkbox("I wake ~4:00 AM")
    sleep9 = st.checkbox("I sleep ~9:00 PM")
    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, current_distractions, sugar, exercise, water, junk, woke4, sleep9)
        st.success(f"Estimated percentile: {pct}% — you're ahead of {pct}% of people.")
        if pct >= 60:
            st.info(f"You're performing well: top {pct}%. With a targeted plan you can reach the top 1%.")
        elif pct >= 40:
            st.info(f"You're around top {pct}%. A structured plan will accelerate you.")
        else:
            st.warning(f"You're in the {pct}% range. Don't worry — consistent habits will move you quickly.")
        st.markdown("---")
        st.write("Do you want our free stage-based plan (skills + health) to become top 1%?")
        if st.button("Yes — Make me top 1% (Free plan)"):
            st.session_state.page = "offer"
            # carry forward field/hours/distractions selection into profile if logged in
            if st.session_state.user:
                update_profile(st.session_state.user, {"field": field, "hours_per_day": hours, "distractions": current_distractions})
            st.rerun()

def page_offer():
    st.header("How your life will look after the Challenge")
    st.markdown("Complete the stage-based plan (Silver → Platinum → Gold) and you will gain these benefits in health, skills and mindset.")
    benefits = [
        "Healthy Diet: No sugar, no alcohol, no junk food; 5L water daily & deep sleep",
        "Wake up early at 4 AM",
        "1 hour exercise daily (pushups, yoga, etc.)",
        "Sleep early on time",
        "Deep hands-on knowledge in your field",
        "A different character — laziness removed",
        "All major distractions are controlled/removed",
        "A wealthy & investment mindset",
        "Unstoppable focus and character",
        "Positive thinking with strong EQ"
    ]
    for i, b in enumerate(benefits, 1):
        st.markdown(f"**{i}.** {b}")
    st.markdown("---")
    if st.button("Show Rules & Start Challenge"):
        st.session_state.page = "rules"
        st.rerun()
    if st.button("Back to Prediction"):
        st.session_state.page = "predict"
        st.rerun()

def page_rules():
    st.header("Stages & Rules (Read carefully)")
    st.markdown("""
    **Easy (Silver)** — 15 days:
    - Work 2 hours/day in your field.
    - Avoid distractions (no scrolling).
    - Fill daily form before sleeping.

    **Medium (Platinum)** — 30 days:
    - Work 4 hours/day.
    - Drink 5L water/day + do 30 pushups.
    - Avoid distractions; fill daily form.

    **Hard (Gold)** — 60 days:
    - Wake 4 AM, sleep 9 PM.
    - 1 hour morning exercise.
    - Work 6 hours/day.
    - 5L water/day, no sugar, 50 pushups, no junk food.
    - Daily positive mirror talk.
    """)
    st.write("")
    if st.button("Start Challenge (Join now)"):
        if not st.session_state.user:
            st.error("Please login first.")
        else:
            update_profile(st.session_state.user, {"joined": True, "started_on": datetime.now().strftime("%Y-%m-%d"), "stage": "Silver", "streak_days": 0, "savings": 0.0, "useless_days": 0})
            st.success("Challenge started. Now complete your profile.")
            st.session_state.page = "profile"
            st.rerun()
    if st.button("Back to Offer"):
        st.session_state.page = "offer"
        st.rerun()

def page_profile():
    if not st.session_state.user:
        st.error("Login first to edit profile.")
        return
    username = st.session_state.user
    prof = store["users"][username]["profile"]
    st.header("Your Profile (Edit & Save)")
    with st.form("profile_form"):
        left, right = st.columns(2)
        with left:
            field = st.text_input("Chosen Field", value=prof.get("field", ""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests", []))
            distractions = st.multiselect("Your common distractions (we'll remind you)", DISTRACTIONS_MASTER, default=prof.get("distractions", []))
        with right:
            hours = st.slider("Hours/day goal", 0.0, 12.0, float(prof.get("hours_per_day", 0.0)))
            stage = st.selectbox("Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(prof.get("stage","Silver")))
            st.write(f"Savings: {prof.get('savings',0.0)} PKR")
            st.write(f"Streak days: {prof.get('streak_days',0)}")
            st.write(f"Useless days: {prof.get('useless_days',0)}")
        save = st.form_submit_button("Save Profile")
    if save:
        update_profile(username, {"field": field, "interests": interests, "hours_per_day": hours, "stage": stage, "distractions": distractions})
        st.success("Profile saved.")
        # After saving profile, go to Daily Routine automatically
        st.session_state.page = "daily"
        st.rerun()
    st.markdown("---")
    st.subheader("Profile Summary")
    prof = store["users"][username]["profile"]
    st.write(f"- Field: {prof.get('field','Not set')}")
    st.write(f"- Interests: {', '.join(prof.get('interests', [])) or 'None'}")
    st.write(f"- Hours/day goal: {prof.get('hours_per_day', 0)}")
    st.write(f"- Stage: {prof.get('stage','Silver')}")
    st.write(f"- Distractions: {', '.join(prof.get('distractions',[])) or 'None'}")
    st.write(f"- Savings: {prof.get('savings',0.0)} PKR")
    st.write(f"- Streak days: {prof.get('streak_days',0)}")
    st.write(f"- Useless days: {prof.get('useless_days',0)}")

def page_daily():
    if not st.session_state.user:
        st.error("Login first.")
        return
    username = st.session_state.user
    prof = store["users"][username]["profile"]
    st.header("Daily Routine (Only tasks for your current stage)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Stage", prof.get("stage","Silver"))
    c2.metric("Streak", prof.get("streak_days",0))
    c3.metric("Savings (PKR)", prof.get("savings",0.0))
    st.markdown("---")
    stage = prof.get("stage", "Silver")

    # show his distractions in sidebar area replicate here
    st.markdown("**Your saved distractions:** " + (", ".join(prof.get("distractions", [])) if prof.get("distractions") else "None"))

    with st.form("daily_form"):
        # Silver needs special checkbox for "Did you engage in distractions today?"
        if stage == "Silver":
            engaged_distraction = st.checkbox("Did you engage in your distractions today? (If yes, check this box)")
            work_hours = st.number_input("Worked hours today (goal 2)", 0.0, 24.0, 0.0, 0.5)
            pushups = 0
            water_liters = 0.0
            sugar_avoided = True
            woke_4am = False
            slept_9pm = False
        elif stage == "Platinum":
            engaged_distraction = st.checkbox("Did you engage in your distractions today? (If yes, check this box)")
            work_hours = st.number_input("Worked hours today (goal 4)", 0.0, 24.0, 0.0, 0.5)
            pushups = st.number_input("Pushups today (goal 30)", 0, 500, 0)
            water_liters = st.number_input("Water liters (goal 5)", 0.0, 10.0, 0.0, 0.5)
            sugar_avoided = st.checkbox("Avoided sugar today?")
            woke_4am = False
            slept_9pm = False
        else:  # Gold
            engaged_distraction = st.checkbox("Did you engage in your distractions today? (If yes, check this box)")
            work_hours = st.number_input("Worked hours today (goal 6)", 0.0, 24.0, 0.0, 0.5)
            pushups = st.number_input("Pushups today (goal 50)", 0, 500, 0)
            water_liters = st.number_input("Water liters (goal 5)", 0.0, 10.0, 0.0, 0.5)
            sugar_avoided = st.checkbox("Avoided sugar today?")
            woke_4am = st.checkbox("Woke ~4 AM today?")
            slept_9pm = st.checkbox("Slept ~9 PM last night?")
        junk_food = st.checkbox("Ate junk food today?")
        pocket_money = st.number_input("If you fail, pocket money you will save today (PKR)", 0.0, 10000.0, 0.0, 1.0)
        submit = st.form_submit_button("Save Today's Check")
    if submit:
        log = {
            "engaged_distraction": bool(engaged_distraction),
            "distractions_avoided": not bool(engaged_distraction),
            "work_done_hours": float(work_hours),
            "pushups": int(pushups) if 'pushups' in locals() else 0,
            "water_liters": float(water_liters) if 'water_liters' in locals() else 0.0,
            "sugar_avoided": bool(sugar_avoided) if 'sugar_avoided' in locals() else True,
            "junk_food": bool(junk_food),
            "woke_4am": bool(woke_4am) if 'woke_4am' in locals() else False,
            "slept_9pm": bool(slept_9pm) if 'slept_9pm' in locals() else False,
            "pocket_money": float(pocket_money)
        }
        add_daily_log(username, log)
        # Evaluate success to show friendly message
        required_hours = 2 if stage == "Silver" else (4 if stage == "Platinum" else 6)
        success = (log["work_done_hours"] >= required_hours) and (not log["engaged_distraction"])
        if stage == "Platinum":
            success = success and (log["pushups"] >= 30) and (log["water_liters"] >= 5)
        if stage == "Gold":
            success = success and (log["pushups"] >= 50) and (log["water_liters"] >= 5) and log["sugar_avoided"] and log["woke_4am"] and log["slept_9pm"]
        if success:
            st.success("Great! Today's tasks completed. Take a motivational quote image and set it as your wallpaper to stay focused.")
        else:
            st.warning(f"Task not completed. {pocket_money} PKR added to your savings as penalty.")
        # stay on daily page and refresh stats
        st.session_state.page = "daily"
        st.rerun()

    # Show recent logs
    df = pd.DataFrame(user_logs(username))
    if not df.empty:
        st.markdown("---")
        st.subheader("Recent (latest 10)")
        st.dataframe(df.sort_values("date", ascending=False).head(10))

# ----------------- Main -----------------
def main():
    st.set_page_config(page_title="The Brain - 105 Days", layout="wide")
    inject_style()

    # session defaults
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "home"

    # Sidebar
    st.sidebar.title("Menu")
    if st.session_state.user:
        st.sidebar.markdown(f"**User:** {st.session_state.user}")
        p = store["users"][st.session_state.user]["profile"]
        st.sidebar.write(f"Stage: {p.get('stage','Silver')}")
        st.sidebar.write(f"Field: {p.get('field','Not set')}")
        st.sidebar.write(f"Hours/day: {p.get('hours_per_day',0)}")
        st.sidebar.write(f"Savings: {p.get('savings',0.0)} PKR")
        st.sidebar.write(f"Streak: {p.get('streak_days',0)}")
        st.sidebar.write(f"Useless days: {p.get('useless_days',0)}")
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Distractions**")
        ds = p.get("distractions", [])
        if ds:
            for d in ds:
                st.sidebar.write(f"- {d}")
        else:
            st.sidebar.write("None")
        st.sidebar.markdown("---")
        if st.sidebar.button("Prediction"):
            st.session_state.page = "predict"
            st.rerun()
        if st.sidebar.button("Offer / Benefits"):
            st.session_state.page = "offer"
            st.rerun()
        if st.sidebar.button("Rules"):
            st.session_state.page = "rules"
            st.rerun()
        if st.sidebar.button("Profile"):
            st.session_state.page = "profile"
            st.rerun()
        if st.sidebar.button("Daily Routine"):
            st.session_state.page = "daily"
            st.rerun()
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.page = "home"
            st.rerun()
    else:
        if st.sidebar.button("Home"):
            st.session_state.page = "home"
            st.rerun()

    # Router
    page = st.session_state.page
    if page == "home":
        st.markdown("<h1 style='color:white;'>🧠 The Brain — 105 Days Life Change</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#eaf6ff;'>Login / Register to start. Flow: Prediction → Offer → Rules → Profile → Daily Routine.</p>", unsafe_allow_html=True)
        page_login()
    elif page == "predict":
        page_predict()
    elif page == "offer":
        page_offer()
    elif page == "rules":
        page_rules()
    elif page == "profile":
        page_profile()
    elif page == "daily":
        page_daily()
    else:
        st.info("Unknown page — returning home.")
        st.session_state.page = "home"
        st.rerun()

if __name__ == "__main__":
    main()
