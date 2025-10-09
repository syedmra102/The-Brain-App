# app.py (v6) — The Brain (Final polished)
# - Blue background, white text, green buttons, navy sidebar
# - ML -> Offer -> Rules -> Profile -> Daily Routine flow (fixed)
# - Centered animated penalty box (CSS fade-in)
# - Pay & Count Day: penalty added to savings and day recorded (NOT useless)
# - Skip Day: day NOT recorded, useless_days incremented, streak reset
# - Separate clean log columns
# - "Today's Summary" card after success
# - Uses local data.json persistence (simple prototype DB)
# Requirements: streamlit, pandas, numpy

import streamlit as st
import json
import os
from datetime import datetime
import numpy as np
import pandas as pd

DATA_FILE = "data.json"

# ---------------- storage helpers ----------------
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

# ---------------- styling ----------------
def inject_style():
    css = """
    <style>
    .stApp {
      background: linear-gradient(180deg,#0b57a4 0%, #0b69c3 100%);
      color: white;
      min-height: 100vh;
      padding-bottom: 40px;
    }
    .stApp, .stApp * { color: #ffffff !important; font-family: "Segoe UI", Roboto, sans-serif; }
    div.stButton > button, .stButton button {
      background-color: #1db954 !important;
      color: white !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
    }
    section[data-testid="stSidebar"] { background-color: #083d6b !important; }
    section[data-testid="stSidebar"] * { color: #eaf6ff !important; }
    input, textarea { background-color: rgba(255,255,255,0.04) !important; color: white !important; }
    .card { background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; }
    /* Centered animated penalty box */
    @keyframes fadeInDown {
      0% { opacity: 0; transform: translateY(-10px) scale(0.98); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    .center-box {
      max-width:720px;
      margin: 20px auto;
      background: linear-gradient(180deg,#2b0000,#3a0000);
      border: 2px solid #ff4d4d;
      padding: 18px;
      border-radius: 12px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.45);
      animation: fadeInDown 0.35s ease-out;
    }
    .center-box h3 { color: #ffdcdc; margin-top:0; }
    .center-box p { color: #ffecec; }
    .center-box-success {
      max-width:720px;
      margin: 20px auto;
      background: linear-gradient(180deg,#003300,#004d00);
      border: 2px solid #2ecc71;
      padding: 18px;
      border-radius: 12px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.45);
      animation: fadeInDown 0.35s ease-out;
    }
    .summary-card {
      max-width:720px;
      margin: 12px auto;
      background: rgba(255,255,255,0.04);
      padding: 14px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.06);
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------------- user helpers ----------------
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
            "hours_per_day": 2.0,
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

# record functions: consistent logic
def record_success(username, log):
    """Record a normal success day: increment streak, append log, show summary later"""
    profile = store["users"][username]["profile"]
    profile["streak_days"] = profile.get("streak_days", 0) + 1
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
        "avoid_junk": log.get("avoid_junk"),
        "pocket_money": float(log.get("pocket_money", 0.0)),
        "counted": True,
        "result": "Success"
    }
    store["logs"].append(entry)
    save_store(store)

def record_failed_with_penalty(username, log):
    """
    User failed tasks but paid penalty:
    - Add pocket money to savings
    - Record the day as 'Failed (penalty paid)' (counted)
    - Do NOT increment useless_days
    - Reset streak to 0 (we choose to reset streak on failure)
    """
    profile = store["users"][username]["profile"]
    pay = float(log.get("pocket_money", 0.0))
    profile["savings"] = round(profile.get("savings", 0.0) + pay, 2)
    # Reset streak to 0 because tasks were missed
    profile["streak_days"] = 0
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
        "avoid_junk": log.get("avoid_junk"),
        "pocket_money": pay,
        "counted": True,
        "result": "Failed (penalty paid)"
    }
    store["logs"].append(entry)
    save_store(store)

def record_failed_skip(username):
    """
    User failed and skipped penalty:
    - Day is NOT recorded in logs
    - useless_days increments
    - streak resets to 0
    """
    profile = store["users"][username]["profile"]
    profile["useless_days"] = profile.get("useless_days", 0) + 1
    profile["streak_days"] = 0
    save_store(store)

# ---------------- progression / badges (same as before but safe) ----------------
def check_and_maybe_promote(username):
    """Check streak and promote stage / award badges when thresholds met."""
    profile = store["users"][username]["profile"]
    stage = profile.get("stage", "Silver")
    badges = profile.get("badges", [])
    streak = profile.get("streak_days", 0)

    promoted = False
    # thresholds
    if stage == "Silver" and streak >= 15:
        if "Silver" not in badges:
            badges.append("Silver")
        profile["stage"] = "Platinum"
        profile["streak_days"] = 0
        profile["hours_per_day"] = 4.0
        promoted = True
    elif stage == "Platinum" and streak >= 30:
        if "Platinum" not in badges and "Silver" in badges:
            badges.append("Platinum")
        profile["stage"] = "Gold"
        profile["streak_days"] = 0
        profile["hours_per_day"] = 6.0
        promoted = True
    elif stage == "Gold" and streak >= 60:
        if "Gold" not in badges and "Silver" in badges and "Platinum" in badges:
            badges.append("Gold")
            profile["joined"] = False  # finish
        promoted = True

    profile["badges"] = badges
    if promoted:
        save_store(store)
    return promoted

# ---------------- prediction ----------------
TRENDING_FIELDS = ["AI","Programming","Cybersecurity","Data Science","Content Creation","Finance","Health","Design"]
DISTRACTIONS_MASTER = ["Social media","Gaming","YouTube","Scrolling news","TV/Netflix","Sleep late","Friends/Calls","Browsing random sites"]

def predict_percentile(field, hours, distractions, avoid_sugar, exercise, water, avoid_junk, woke4, sleep9):
    base_map = {"AI":60,"Programming":55,"Cybersecurity":50,"Data Science":55,"Content Creation":45,"Finance":50,"Health":50,"Design":48}
    base = base_map.get(field,50)
    hours_score = min(max(hours/12,0),1)*40
    distraction_penalty = min(len(distractions),8)*4
    sugar_bonus = 8 if avoid_sugar else -6
    exercise_bonus = 8 if exercise else -8
    water_bonus = min(water,5)/5*8
    junk_bonus = 4 if avoid_junk else -6
    sleep_bonus = 6 if (woke4 and sleep9) else (-4 if not sleep9 else 2)
    raw = base + hours_score - distraction_penalty + sugar_bonus + exercise_bonus + water_bonus + junk_bonus + sleep_bonus
    pct = int(np.clip((raw/120)*100, 1, 99))
    return pct

# ---------------- pages ----------------
def page_login():
    st.markdown("<h2 style='color:white;'>Login / Register</h2>", unsafe_allow_html=True)
    with st.form("auth"):
        col1,col2 = st.columns([2,1])
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        with col2:
            login_btn = st.form_submit_button("Login")
            register_btn = st.form_submit_button("Register")
    if register_btn:
        try:
            create_user(username, password)
            st.success("Registered. Now login.")
        except Exception as e:
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
    st.header("Quick Prediction — your focus potential")
    st.markdown("Answer a few quick questions; distractions are on this page.")
    # sidebar snapshot
    with st.sidebar:
        st.markdown("### Snapshot")
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.write(f"User: {st.session_state.user}")
            st.write(f"Stage: {p.get('stage')}")
            st.write(f"Savings: {p.get('savings',0.0)} PKR")
            st.markdown(f"Badges: {' '.join([f'✅ {b}' for b in p.get('badges',[])]) or 'None'}")
        st.markdown("---")
        if st.session_state.user and st.button("Open Profile"):
            st.session_state.page = "profile"
            st.rerun()

    if "pred_inputs" not in st.session_state:
        st.session_state.pred_inputs = {}

    field = st.selectbox("Choose a trending field", TRENDING_FIELDS, index=TRENDING_FIELDS.index(st.session_state.pred_inputs.get("field", TRENDING_FIELDS[0])) if st.session_state.pred_inputs.get("field") in TRENDING_FIELDS else 0)
    hours = st.slider("Hours/day you spend on this field", 0.0, 12.0, float(st.session_state.pred_inputs.get("hours", 2.0)), 0.5)
    st.markdown("### Which distractions do you face now?")
    distractions = st.multiselect("", DISTRACTIONS_MASTER, default=st.session_state.pred_inputs.get("distractions", []))
    avoid_sugar = st.checkbox("I avoid sugar", value=st.session_state.pred_inputs.get("avoid_sugar", False))
    exercise = st.checkbox("I exercise daily (30-60 min)", value=st.session_state.pred_inputs.get("exercise", False))
    water = st.number_input("Liters of water/day", 0.0, 10.0, float(st.session_state.pred_inputs.get("water", 2.0)), 0.5)
    avoid_junk = st.checkbox("I avoid junk food today", value=st.session_state.pred_inputs.get("avoid_junk", False))
    woke4 = st.checkbox("I wake ~4:00 AM", value=st.session_state.pred_inputs.get("woke4", False))
    sleep9 = st.checkbox("I sleep ~9:00 PM", value=st.session_state.pred_inputs.get("sleep9", False))

    st.session_state.pred_inputs = {"field": field, "hours": hours, "distractions": distractions,
                                    "avoid_sugar": avoid_sugar, "exercise": exercise, "water": water,
                                    "avoid_junk": avoid_junk, "woke4": woke4, "sleep9": sleep9}

    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, distractions, avoid_sugar, exercise, water, avoid_junk, woke4, sleep9)
        st.success(f"Estimated Focus Potential: {pct}%. You are ahead of {pct}% of people.")
        st.markdown("---")
        st.write("Do you want our free stage-based plan to become top 1% (skills + health)?")
        if st.button("Yes — Make me top 1% (Free plan)"):
            if st.session_state.user:
                update_profile(st.session_state.user, {"field": field, "hours_per_day": hours, "distractions": distractions})
            st.session_state.page = "offer"
            st.rerun()

def page_offer():
    st.header("How your life will look after the Challenge")
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
    st.markdown("---")
    if st.button("Show Rules & Start Challenge"):
        st.session_state.page = "rules"
        st.rerun()
    if st.button("Back to Prediction"):
        st.session_state.page = "predict"
        st.rerun()

def page_rules():
    st.header("Stages & Rules")
    st.markdown("""
**Silver (Easy)** — 15 days:
- Work 2 hours/day
- Avoid distractions
- Fill daily checkbox form

**Platinum (Medium)** — 30 days:
- Work 4 hours/day
- 5L water/day + 30 pushups
- Avoid distractions; fill form

**Gold (Hard)** — 60 days:
- Wake 4 AM, sleep 9 PM
- 1 hour exercise, 6 hours/day work
- 5L water, no sugar, 50 pushups, avoid junk food
    """)
    if st.button("Start Challenge (Join now)"):
        if not st.session_state.user:
            st.error("Please login first.")
        else:
            update_profile(st.session_state.user, {"joined": True, "started_on": datetime.now().strftime("%Y-%m-%d"), "stage": "Silver", "streak_days": 0, "savings": 0.0, "useless_days": 0, "badges": []})
            st.success("Challenge started. Complete your profile.")
            st.session_state.page = "profile"
            st.rerun()
    if st.button("Back to Offer"):
        st.session_state.page = "offer"
        st.rerun()

def page_profile():
    if not st.session_state.user:
        st.error("Login first.")
        return
    u = st.session_state.user
    prof = store["users"][u]["profile"]
    st.header("Your Profile — Edit & Save")
    STAGE_GOAL = {"Silver":2.0,"Platinum":4.0,"Gold":6.0}
    with st.form("profile_form"):
        left,right = st.columns(2)
        with left:
            field = st.text_input("Chosen Field", value=prof.get("field",""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests",[]))
            distractions = st.multiselect("Your common distractions", DISTRACTIONS_MASTER, default=prof.get("distractions", []))
        with right:
            stage = st.selectbox("Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(prof.get("stage","Silver")))
            auto_hours = STAGE_GOAL.get(stage, 2.0)
            st.markdown(f"**Hours/day goal:** {auto_hours} hours (set by stage)")
            st.write(f"Savings: {prof.get('savings',0.0)} PKR")
            st.write(f"Streak days: {prof.get('streak_days',0)}")
            st.write(f"Useless days: {prof.get('useless_days',0)}")
        save = st.form_submit_button("Save Profile")
    if save:
        update_profile(u, {"field": field, "interests": interests, "hours_per_day": auto_hours, "stage": stage, "distractions": distractions})
        st.success("Profile saved — opening Daily Routine.")
        st.session_state.page = "daily"
        st.rerun()

    st.markdown("---")
    st.subheader("Profile Summary")
    st.write(f"- Field: **{prof.get('field','Not set')}**")
    st.write(f"- Hours/day goal: **{prof.get('hours_per_day',0)}**")
    st.write(f"- Stage: **{prof.get('stage','Silver')}**")
    st.write(f"- Badges: {' '.join([f'✅ {b}' for b in prof.get('badges',[])]) or 'None'}")
    st.write(f"- Savings: **{prof.get('savings',0.0)} PKR**")
    st.write(f"- Streak days: **{prof.get('streak_days',0)}**")
    st.write(f"- Useless days: **{prof.get('useless_days',0)}**")

def page_daily():
    if not st.session_state.user:
        st.error("Login first.")
        return
    username = st.session_state.user
    prof = store["users"][username]["profile"]

    # show header + metrics
    st.header("Daily Routine")
    c1,c2,c3 = st.columns(3)
    c1.metric("Stage", f"{prof.get('stage','Silver')} ({prof.get('hours_per_day',2)} hr goal)")
    c2.metric("Streak", prof.get("streak_days",0))
    c3.metric("Savings (PKR)", prof.get("savings",0.0))
    st.markdown(f"Badges: {' '.join([f'✅ {b}' for b in prof.get('badges',[])]) or 'None'}")
    st.markdown("---")

    stage = prof.get("stage","Silver")
    # questions per stage
    if stage == "Silver":
        q = [("work_done", f"Did you work at least {prof.get('hours_per_day',2)} hours today?"),
             ("avoid_distractions","Did you avoid distractions today (no scrolling)?"),
             ("avoid_junk","Did you avoid junk food today?")]
    elif stage == "Platinum":
        q = [("work_done", f"Did you work at least {prof.get('hours_per_day',4)} hours today?"),
             ("avoid_distractions","Did you avoid distractions today (no scrolling)?"),
             ("pushups","Did you do at least 30 pushups?"),
             ("water","Did you drink at least 5 liters of water?"),
             ("avoid_junk","Did you avoid junk food today?")]
    else: # Gold
        q = [("work_done", f"Did you work at least {prof.get('hours_per_day',6)} hours today?"),
             ("avoid_distractions","Did you avoid distractions today (no scrolling)?"),
             ("pushups","Did you do at least 50 pushups?"),
             ("water","Did you drink at least 5 liters of water?"),
             ("avoid_sugar","Did you avoid sugar today?"),
             ("woke_4am","Did you wake ~4:00 AM today?"),
             ("slept_9pm","Did you sleep around 9:00 PM last night?"),
             ("avoid_junk","Did you avoid junk food today?")]

    today_key = datetime.now().strftime("%Y%m%d")
    responses = {}
    with st.form("daily"):
        for key,label in q:
            widget = f"{username}_{today_key}_{key}"
            responses[key] = st.checkbox(label, key=widget)
        pocket_key = f"{username}_{today_key}_pocket"
        pocket_money = st.number_input("Pocket money to save today (PKR):", 0.0, 10000.0, 0.0, 1.0, key=pocket_key)
        submit = st.form_submit_button("Submit Today's Check")
    # on submit
    if submit:
        # success if all True
        success = all(responses.values())
        # build log
        log = {
            "work_done": responses.get("work_done", False),
            "distraction": not responses.get("avoid_distractions", False),
            "pushups": 30 if responses.get("pushups") else (50 if responses.get("pushups") and stage=="Gold" else 0),
            "water_liters": 5.0 if responses.get("water") else 0.0,
            "woke_4am": responses.get("woke_4am", None),
            "slept_9pm": responses.get("slept_9pm", None),
            "sugar_avoided": responses.get("avoid_sugar", None),
            "avoid_junk": responses.get("avoid_junk", None),
            "pocket_money": float(pocket_money)
        }

        if success:
            # record success
            record_success(username, log)
            # check promotion
            check_and_maybe_promote(username)
            # show today's summary card
            st.markdown(
                f"""
                <div class="center-box-success">
                  <h3>✅ Today's Summary</h3>
                  <p>Great job — you completed all required tasks today. Keep momentum!</p>
                  <p><b>Last task:</b> Go to Google, search for a motivational quote image you like, and set it as your wallpaper so the mission is always visible when you wake up.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.balloons()
            st.rerun()
        else:
            # show animated centered penalty box
            st.markdown(
                """
                <div class="center-box">
                  <h3>⚠️ You missed required tasks today</h3>
                  <p>Choose one option below:</p>
                  <ol>
                    <li><b>Pay & Count Day</b> — Pay the pocket money now; it will be added to your savings and the day will be recorded (result: Failed (penalty paid)).</li>
                    <li><b>Don't Count This Day</b> — The day will NOT be recorded. Your streak resets and a useless day will be added.</li>
                  </ol>
                </div>
                """,
                unsafe_allow_html=True
            )
            col1,col2 = st.columns([1,1])
            with col1:
                pay_amt_key = f"pay_{username}_{today_key}"
                pay_amt = st.number_input("Enter pocket money to pay now (PKR):", 0.0, 10000.0, float(pocket_money), 1.0, key=pay_amt_key)
                if st.button("Pay & Count Day (Record Failed Day)", key=f"paybtn_{username}_{today_key}"):
                    if pay_amt <= 0:
                        st.error("Enter an amount greater than 0 to pay and record the day.")
                    else:
                        log["pocket_money"] = float(pay_amt)
                        record_failed_with_penalty(username, log)
                        # do NOT increment useless_days when paying
                        st.success(f"Penalty paid {pay_amt} PKR. The day is recorded as 'Failed (penalty paid)'. Savings updated.")
                        st.info("Last task: search a motivational quote image and set it as wallpaper to keep motivated.")
                        st.rerun()
            with col2:
                if st.button("Don't Count This Day (Skip & Mark Useless)", key=f"skipbtn_{username}_{today_key}"):
                    record_failed_skip(username)
                    st.warning("This day will NOT be counted. Streak reset to 0 and one useless day added. Come back tomorrow stronger.")
                    st.rerun()

    # ---------------- logs table (separate columns) ----------------
    logs = [l for l in store["logs"] if l["user"] == username]
    if logs:
        st.markdown("---")
        st.subheader("Activity Log (all recorded days)")
        df = pd.DataFrame(logs).sort_values("date", ascending=False)
        # normalize columns
        columns = ["date","stage","result","work_done","distraction","avoid_junk","pushups","water_liters","sugar_avoided","woke_4am","slept_9pm","pocket_money","counted"]
        df_display = pd.DataFrame({c: df.get(c) for c in columns})
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

# ---------------- main ----------------
def main():
    st.set_page_config(page_title="The Brain - 105 Days", layout="wide")
    inject_style()

    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "pred_inputs" not in st.session_state:
        st.session_state.pred_inputs = {}

    # sidebar
    st.sidebar.title("Menu")
    if st.session_state.user:
        p = store["users"][st.session_state.user]["profile"]
        st.sidebar.markdown(f"**User:** {st.session_state.user}")
        st.sidebar.write(f"Stage: **{p.get('stage','Silver')}**")
        st.sidebar.write(f"Hours/day: {p.get('hours_per_day', 2)}")
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
            st.sidebar.write("None set")
        st.sidebar.markdown("---")
        if st.sidebar.button("Prediction"):
            st.session_state.page = "predict"; st.rerun()
        if st.sidebar.button("Offer / Benefits"):
            st.session_state.page = "offer"; st.rerun()
        if st.sidebar.button("Rules"):
            st.session_state.page = "rules"; st.rerun()
        if st.sidebar.button("Profile"):
            st.session_state.page = "profile"; st.rerun()
        if st.sidebar.button("Daily Routine"):
            st.session_state.page = "daily"; st.rerun()
        if st.sidebar.button("Logout"):
            st.session_state.user = None; st.session_state.page = "home"; st.rerun()
    else:
        if st.sidebar.button("Home"):
            st.session_state.page = "home"; st.rerun()

    # router
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
