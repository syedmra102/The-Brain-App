# app.py
# The Brain - 105 Days (streamlit single-file)
# - Local JSON storage (data.json)
# - Login/register with password length validation (ValueError)
# - ML-ish prediction based on user inputs
# - Challenge flow: Offer -> Rules -> Start -> Daily form (stage-specific)
# Styling: blue background, white text, green buttons, navy sidebar

import streamlit as st
import json, os
from datetime import datetime
import numpy as np
import pandas as pd

DATA_FILE = "data.json"

# ---------- Storage helpers ----------
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

# ---------- Styling ----------
def inject_style():
    css = """
    <style>
    .stApp {
      background: linear-gradient(180deg,#0b57a4 0%, #0b69c3 100%);
      color: white;
      min-height: 100vh;
    }
    /* Make general text white */
    .stApp, .stApp * { color: #ffffff !important; }
    /* Buttons green */
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
    /* Sidebar navy */
    section[data-testid="stSidebar"] {
      background-color: #083d6b !important;
    }
    section[data-testid="stSidebar"] * { color: #eaf6ff !important; }
    /* Inputs */
    input, textarea { background-color: rgba(255,255,255,0.04) !important; color: white !important; }
    .card { background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------- User utilities ----------
def create_user(username, password):
    if not username or not password:
        raise ValueError("Username and password required.")
    if len(password) < 6:
        # requested: try ValueError for password length
        raise ValueError("Password must be at least 6 characters.")
    if username in store["users"]:
        raise ValueError("Username already exists.")
    store["users"][username] = {
        "password": password,
        "profile": {
            "field": "",
            "interests": [],
            "hours_per_day": 0.0,
            "stage": "Silver",  # Silver/Platinum/Gold
            "streak_days": 0,
            "savings": 0.0,
            "started_on": None,
            "joined": False
        }
    }
    save_store(store)
    return True

def check_user(username, password):
    u = store["users"].get(username)
    if not u:
        return False
    return u["password"] == password

def update_profile(username, profile_updates):
    u = store["users"].get(username)
    if not u:
        return False
    u["profile"].update(profile_updates)
    save_store(store)
    return True

def add_daily_log(username, log):
    entry = {"user": username, "date": datetime.now().strftime("%Y-%m-%d"), **log}
    store["logs"].append(entry)
    # update streak & savings logic
    u = store["users"].get(username)
    if u:
        profile = u["profile"]
        stage = profile.get("stage", "Silver")
        required_hours = 2 if stage == "Silver" else (4 if stage == "Platinum" else 6)
        ok = log.get("work_done_hours", 0) >= required_hours and log.get("distractions_avoided", False)
        if stage == "Platinum":
            ok = ok and (log.get("pushups", 0) >= 30) and (log.get("water_liters", 0) >= 5)
        elif stage == "Gold":
            ok = ok and (log.get("pushups", 0) >= 50) and (log.get("water_liters", 0) >= 5) and log.get("sugar_avoided", False) and log.get("woke_4am", False) and log.get("slept_9pm", False)
        if ok:
            profile["streak_days"] = profile.get("streak_days", 0) + 1
        else:
            # failed: add pocket money to savings, and count as useless day (we track via logs)
            profile["savings"] = round(profile.get("savings", 0.0) + float(log.get("pocket_money", 0.0)), 2)
        save_store(store)
    save_store(store)

def user_logs_df(username):
    logs = [l for l in store["logs"] if l["user"] == username]
    return pd.DataFrame(logs) if logs else pd.DataFrame(columns=["date"])

# ---------- Trending fields & distractions ----------
TRENDING_FIELDS = ["AI", "Programming", "Cybersecurity", "Data Science", "Content Creation", "Finance", "Health", "Design"]
DISTRACTIONS_MASTER = ["Social media", "Gaming", "YouTube", "Scrolling news", "TV/Netflix", "Sleep late", "Friends/Calls", "Browsing random sites"]

# ---------- Simple ML-style prediction ----------
def predict_percentile(field, hours_per_day, distractions_list, sugar_avoided, exercise_daily, water_liters, junk_food, wake_time_early, sleep_early):
    """
    Returns an estimated percentile value (1-100).
    This is a deterministic heuristic model (not a trained ML model),
    combining healthy behaviors and dedication signals.
    """
    # Base by field popularity: some fields are heavy competition so baseline differs
    field_popularity = {
        "AI": 60, "Programming": 55, "Cybersecurity": 50, "Data Science": 55,
        "Content Creation": 45, "Finance": 50, "Health": 50, "Design": 48
    }
    base = field_popularity.get(field, 50)

    # hours effect (0-12)
    hours_score = min(max(hours_per_day / 12, 0), 1) * 40  # up to +40

    # distractions penalty
    distraction_count = len(distractions_list)
    distraction_penalty = min(distraction_count, 8) * 4  # up to -32

    # health bonuses
    sugar_bonus = 8 if sugar_avoided else -6
    exercise_bonus = 8 if exercise_daily else -8
    water_bonus = min(water_liters, 5) / 5 * 8  # up to +8
    junk_penalty = -6 if junk_food else 4
    sleep_bonus = 6 if (wake_time_early and sleep_early) else (-4 if not sleep_early else 2)

    raw_score = base + hours_score - distraction_penalty + sugar_bonus + exercise_bonus + water_bonus + junk_penalty + sleep_bonus

    # normalize to 1..99
    percentile = int(np.clip((raw_score / 120) * 100, 1, 99))
    # Make more human-friendly boundaries (1,5,10,25,40,60,80,95)
    return percentile

# ---------- Pages ----------
def page_login():
    st.markdown("<h2 style='color:white;'>Login or Register</h2>", unsafe_allow_html=True)
    with st.form("auth"):
        c1, c2 = st.columns([2,1])
        with c1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        with c2:
            login = st.form_submit_button("Login")
            register = st.form_submit_button("Register")
    msg = ""
    if register:
        try:
            create_user(username, password)
            st.success("Registered. Now please login.")
        except ValueError as e:
            st.error(f"Registration error: {str(e)}")
    if login:
        if check_user(username, password):
            st.session_state.user = username
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Login failed. Check username/password.")

def page_ml_predict():
    st.header("Predict your global standing (quick)")
    st.markdown("Choose your field and answer few quick things. The model will estimate what percentile you are at compared to others (very rough but useful).")

    # sidebar shows profile, distractions
    with st.sidebar:
        st.markdown("### Profile / Quick View")
        if st.session_state.user:
            u = store["users"][st.session_state.user]
            prof = u["profile"]
            st.markdown(f"**User:** {st.session_state.user}")
            st.markdown(f"- Stage: {prof.get('stage')}")
            st.markdown(f"- Field: {prof.get('field') or 'Not set'}")
            st.markdown(f"- Hours/day goal: {prof.get('hours_per_day',0)}")
            st.markdown("---")
        st.markdown("### Current distractions")
        current_d = st.multiselect("Select distractions you face now", DISTRACTIONS_MASTER, default=[])
        st.markdown("---")
    # Main inputs
    field = st.selectbox("Which field do you want to measure in?", TRENDING_FIELDS)
    hours = st.slider("How many hours a day you give to this field?", 0.0, 12.0, 2.0, 0.5)
    sugar_avoided = st.checkbox("Avoid sugar?")
    exercise_daily = st.checkbox("Exercise daily (any 30-60 min)?")
    water_liters = st.number_input("How many liters of water do you drink per day?", 0.0, 10.0, 2.0, 0.5)
    junk_food = st.checkbox("Do you eat junk food when you wake up or often?")
    woke_4am = st.checkbox("Do you wake up ~4:00 AM?")
    slept_9pm = st.checkbox("Do you sleep ~9:00 PM?")

    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, current_d, sugar_avoided, exercise_daily, water_liters, junk_food, woke_4am, slept_9pm)
        ahead = pct
        behind = 100 - pct
        st.success(f"Estimated percentile: {pct}% — you are ahead of {ahead}% of people and behind {behind}% of people globally (rough estimate).")
        # friendly phrasing they requested
        if pct >= 60:
            st.info(f"You are in top {pct}%. Nice! But you can become top 1% with a plan.")
        elif pct >= 40:
            st.info(f"You are around the top {pct}%. You are {100-pct}% behind the absolute top; a structured plan will boost you further.")
        else:
            st.warning(f"You are in the {pct}%. Don't worry — consistent changes can move you a lot.")
        st.markdown("---")
        st.write("**Free plan to become top 1%** — stage-based plan that also improves your health & skills.")
        if st.button("Yes, make me top 1%! (Free plan)"):
            st.session_state.offer_accepted = True
            st.rerun()

def page_offer_and_rules():
    st.header("How your life will look after the Challenge")
    st.markdown("If you finish the challenge (progressively through stages), your life will look like:")
    benefits = [
        "Healthy Diet: No sugar, no alcohol, no junk food; 5L water daily & deep sleep",
        "Waking up early at 4 AM",
        "1 hour exercise daily (pushups, yoga, etc.)",
        "Sleeping early (on time)",
        "Deep knowledge in your field with hands-on experience",
        "A different character — laziness removed",
        "All major distractions are controlled/removed",
        "A wealthy & investment mindset",
        "Unstoppable focus and character",
        "Positive mindset — high EQ & big thinking"
    ]
    for i, b in enumerate(benefits, 1):
        st.markdown(f"**{i}.** {b}")
    st.markdown("---")
    if st.button("Show Rules & Start Challenge"):
        st.session_state.show_rules = True
        st.rerun()

    if st.session_state.get("show_rules"):
        st.header("Stages & Rules")
        st.markdown("""
        **Easy (Silver)** — 15 days:
        - Work 2 hours/day in your field
        - Avoid distractions
        - Fill daily form before sleeping

        **Medium (Platinum)** — 30 days:
        - Work 4 hours/day
        - Drink 5L water/day & do 30 pushups
        - Avoid distractions; fill daily form

        **Hard (Gold)** — 60 days:
        - Wake at 4 AM, sleep at 9 PM
        - 1 hour morning exercise
        - Work 6 hours/day
        - 5L water, no sugar, 50 pushups, no junk food
        - Daily positive mirror talk
        """)
        if st.button("Start Challenge Now"):
            # start challenge: set user profile started_on and joined flag and stage silver
            if st.session_state.user:
                update_profile(st.session_state.user, {"joined": True, "started_on": datetime.now().strftime("%Y-%m-%d"), "stage": "Silver", "streak_days": 0})
                st.success("Challenge started! You are now in Silver stage.")
                st.rerun()
            else:
                st.error("Login first to start the challenge.")

def page_daily_logging():
    if not st.session_state.user:
        st.error("You must login to use the daily logging feature.")
        return
    username = st.session_state.user
    u = store["users"][username]
    prof = u["profile"]
    st.header(f"Daily logging — {username}")
    # Top metrics
    st.columns(3)
    c1, c2, c3 = st.columns(3)
    c1.metric("Stage", prof.get("stage", "Silver"))
    c2.metric("Streak days", prof.get("streak_days", 0))
    c3.metric("Savings (PKR)", prof.get("savings", 0.0))
    st.markdown("---")
    st.markdown("**Daily Form** (only show fields relevant to current stage). Checkboxes only.")
    stage = prof.get("stage", "Silver")
    with st.form("daily"):
        distractions_avoided = st.checkbox("Avoided distractions today (no scrolling)")
        if stage == "Silver":
            work_hours = st.number_input("Worked hours today (goal 2)", 0.0, 24.0, 0.0, 0.5)
            pushups = 0
            water_liters = 0.0
            sugar_avoided = True
            woke_4am = False
            slept_9pm = False
        elif stage == "Platinum":
            work_hours = st.number_input("Worked hours today (goal 4)", 0.0, 24.0, 0.0, 0.5)
            pushups = st.number_input("Pushups today (goal 30)", 0, 500, 0)
            water_liters = st.number_input("Water liters (goal 5)", 0.0, 10.0, 0.0, 0.5)
            sugar_avoided = st.checkbox("Avoided sugar today?")
            woke_4am = False
            slept_9pm = False
        else:  # Gold
            work_hours = st.number_input("Worked hours today (goal 6)", 0.0, 24.0, 0.0, 0.5)
            pushups = st.number_input("Pushups today (goal 50)", 0, 500, 0)
            water_liters = st.number_input("Water liters (goal 5)", 0.0, 10.0, 0.0, 0.5)
            sugar_avoided = st.checkbox("Avoided sugar today?")
            woke_4am = st.checkbox("Woke ~4 AM today?")
            slept_9pm = st.checkbox("Slept ~9 PM last night?")
        junk_food = st.checkbox("Ate junk food today?")
        pocket_money = st.number_input("If you fail today, how much pocket money will you save (PKR)?", 0.0, 10000.0, 0.0, 1.0)
        submit = st.form_submit_button("Submit Today")
    if submit:
        # Determine success based on stage
        required_hours = 2 if stage == "Silver" else (4 if stage == "Platinum" else 6)
        success = (work_hours >= required_hours) and distractions_avoided
        if stage == "Platinum":
            success = success and (pushups >= 30) and (water_liters >= 5)
        if stage == "Gold":
            success = success and (pushups >= 50) and (water_liters >= 5) and sugar_avoided and woke_4am and slept_9pm
        log = {
            "distractions_avoided": bool(distractions_avoided),
            "work_done_hours": float(work_hours),
            "pushups": int(pushups),
            "water_liters": float(water_liters),
            "sugar_avoided": bool(sugar_avoided),
            "junk_food": bool(junk_food),
            "woke_4am": bool(woke_4am),
            "slept_9pm": bool(slept_9pm),
            "pocket_money": float(pocket_money)
        }
        add_daily_log(username, log)
        if success:
            st.success("Well done! You completed today's tasks. Take a motivational quote image from Google and set it as your wallpaper.")
        else:
            st.warning(f"Task not completed. {pocket_money} PKR added to your savings as penalty.")
        st.rerun()

    # show logs summary
    df = user_logs_df(username)
    if not df.empty:
        st.subheader("Recent logs")
        st.dataframe(df.sort_values("date", ascending=False).head(15))

# ---------- Main ----------
def main():
    st.set_page_config(page_title="The Brain - 105 Days", layout="wide")
    inject_style()

    # session state defaults
    if "user" not in st.session_state:
        st.session_state.user = None
    if "offer_accepted" not in st.session_state:
        st.session_state.offer_accepted = False
    if "show_rules" not in st.session_state:
        st.session_state.show_rules = False

    # top navigation
    st.sidebar.title("Menu")
    if st.session_state.user:
        st.sidebar.markdown(f"**Logged in:** {st.session_state.user}")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()
        if st.sidebar.button("Daily Logging"):
            st.session_state.page = "daily"
        if st.sidebar.button("Prediction"):
            st.session_state.page = "predict"
        if st.sidebar.button("Offer & Rules"):
            st.session_state.page = "offer"
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Quick Profile")
        prof = store["users"][st.session_state.user]["profile"]
        st.sidebar.write(f"Field: {prof.get('field','Not set')}")
        st.sidebar.write(f"Stage: {prof.get('stage','Silver')}")
        st.sidebar.write(f"Hours/day goal: {prof.get('hours_per_day',0)}")
        st.sidebar.write(f"Savings: {prof.get('savings',0.0)} PKR")
    else:
        st.sidebar.write("Not logged in")
        if st.sidebar.button("Home"):
            st.session_state.page = "home"

    # page routing
    page = st.session_state.get("page", "home")

    if page == "home":
        st.markdown("<h1 style='color:white;'>🧠 The Brain — Make your life 1% better each day</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#eaf6ff;'>Login or register to start. You will first use a logging page and then the quick prediction model.</p>", unsafe_allow_html=True)
        page_login()
        if st.session_state.user:
            st.success("Logged in — open Prediction from sidebar or continue below.")
            if st.button("Go to Prediction"):
                st.session_state.page = "predict"
                st.rerun()

    elif page == "predict":
        page_ml_predict()

    elif page == "offer":
        page_offer_and_rules()

    elif page == "daily":
        page_daily_logging()

    else:
        st.info("Welcome — choose an action from the sidebar.")

if __name__ == "__main__":
    main()
