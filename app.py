# app.py (v4.2)
# The Brain - 105 Days (final)
# - Local data.json storage auto-created
# - Centered popup warning box for penalty (pay & count / skip)
# - Confetti animation (st.balloons) on success
# - Clean logs table with separate columns per stage
# - Blue bg, white text, green buttons, navy sidebar
# Requirements: streamlit, pandas, numpy

import streamlit as st
import json
import os
from datetime import datetime
import numpy as np
import pandas as pd

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
    .stApp {
      background: linear-gradient(180deg,#0b57a4 0%, #0b69c3 100%);
      color: white;
      min-height: 100vh;
      padding-bottom: 40px;
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
    /* Centered warning box */
    .center-box {
      max-width:700px;
      margin: 30px auto;
      background: #2b0000;
      border: 2px solid #ff4d4d;
      padding: 18px;
      border-radius: 12px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    }
    .center-box h3 { color: #ffdcdc; margin-top:0; }
    .center-box p { color: #ffecec; }
    .tiny-muted { color:#d7eefc; font-size:0.9rem }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

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
            "distractions": []
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

def record_failed_day(username, log):
    """Record a failed day (adds savings and useless_days)"""
    profile = store["users"][username]["profile"]
    # add pocket money to savings (log must contain pocket_money > 0)
    profile["savings"] = round(profile.get("savings", 0.0) + float(log.get("pocket_money", 0.0)), 2)
    profile["useless_days"] = profile.get("useless_days", 0) + 1
    entry = {
        "user": username,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "stage": profile.get("stage"),
        "work_done": log.get("work_done", False),
        "distraction": log.get("distraction", True),
        "pushups": log.get("pushups", None),
        "water_liters": log.get("water_liters", None),
        "slept_9pm": log.get("slept_9pm", None),
        "woke_4am": log.get("woke_4am", None),
        "sugar_avoided": log.get("sugar_avoided", None),
        "pocket_money": float(log.get("pocket_money", 0.0)),
        "result": "Failed (penalty paid)"
    }
    store["logs"].append(entry)
    save_store(store)

def record_success_day(username, log):
    """Record success day (increments streak)"""
    profile = store["users"][username]["profile"]
    profile["streak_days"] = profile.get("streak_days", 0) + 1
    entry = {
        "user": username,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "stage": profile.get("stage"),
        "work_done": log.get("work_done", True),
        "distraction": log.get("distraction", False),
        "pushups": log.get("pushups", None),
        "water_liters": log.get("water_liters", None),
        "slept_9pm": log.get("slept_9pm", None),
        "woke_4am": log.get("woke_4am", None),
        "sugar_avoided": log.get("sugar_avoided", None),
        "pocket_money": float(log.get("pocket_money", 0.0)),
        "result": "Success"
    }
    store["logs"].append(entry)
    save_store(store)

def user_logs(username):
    return [l for l in store["logs"] if l["user"] == username]

# ---------------- Predictor (heuristic) ----------------
TRENDING_FIELDS = ["AI", "Programming", "Cybersecurity", "Data Science", "Content Creation", "Finance", "Health", "Design"]
DISTRACTIONS_MASTER = ["Social media", "Gaming", "YouTube", "Scrolling news", "TV/Netflix", "Sleep late", "Friends/Calls", "Browsing random sites"]

def predict_percentile(field, hours_per_day, distractions_list, sugar_avoided, exercise_daily, water_liters, junk_food, woke_4am, slept_9pm):
    field_popularity = {"AI":60,"Programming":55,"Cybersecurity":50,"Data Science":55,"Content Creation":45,"Finance":50,"Health":50,"Design":48}
    base = field_popularity.get(field,50)
    hours_score = min(max(hours_per_day/12,0),1)*40
    distraction_penalty = min(len(distractions_list),8)*4
    sugar_bonus = 8 if sugar_avoided else -6
    exercise_bonus = 8 if exercise_daily else -8
    water_bonus = min(water_liters,5)/5*8
    junk_penalty = -6 if junk_food else 4
    sleep_bonus = 6 if (woke_4am and slept_9pm) else (-4 if not slept_9pm else 2)
    raw = base + hours_score - distraction_penalty + sugar_bonus + exercise_bonus + water_bonus + junk_penalty + sleep_bonus
    pct = int(np.clip((raw/120)*100, 1, 99))
    return pct

# ---------------- Pages ----------------
def page_login():
    st.markdown("<h2 style='color:white;'>Login or Register</h2>", unsafe_allow_html=True)
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
            st.success("Registered successfully. Please login.")
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
    st.header("Quick Prediction — Where you stand globally")
    st.markdown("Answer a few quick questions. Distractions selection is on this page.")
    # Sidebar snapshot
    with st.sidebar:
        st.markdown("### Profile snapshot")
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.write(f"User: {st.session_state.user}")
            st.write(f"Stage: {p.get('stage')}")
            st.write(f"Field: {p.get('field') or 'Not set'}")
            st.write(f"Savings: {p.get('savings',0.0)} PKR")
        st.markdown("---")
        if st.session_state.user and st.button("Open Profile"):
            st.session_state.page = "profile"
            st.rerun()

    field = st.selectbox("Choose a trending field", TRENDING_FIELDS)
    hours = st.slider("Hours/day you spend on this field", 0.0, 12.0, 2.0, 0.5)
    st.markdown("### Which distractions do you face now?")
    current_distractions = st.multiselect("", DISTRACTIONS_MASTER, default=[])
    sugar = st.checkbox("I avoid sugar")
    exercise = st.checkbox("I exercise daily (30-60 min)")
    water = st.number_input("Liters of water/day", 0.0, 10.0, 2.0, 0.5)
    junk = st.checkbox("I eat junk food often")
    woke4 = st.checkbox("I wake ~4:00 AM")
    sleep9 = st.checkbox("I sleep ~9:00 PM")

    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, current_distractions, sugar, exercise, water, junk, woke4, sleep9)
        st.success(f"Estimated percentile: {pct}% — you're ahead of {pct}% people.")
        if pct >= 60:
            st.info(f"You're in top {pct}%. With a focused plan you can reach top 1%.")
        elif pct >= 40:
            st.info(f"You are around top {pct}%. With consistency you'll climb faster.")
        else:
            st.warning(f"You are around {pct}%. Don't worry — start daily habits.")
        st.markdown("---")
        st.write("Do you want our free stage-based plan to reach top 1% (skills + health)?")
        if st.button("Yes — Make me top 1% (Free plan)"):
            if st.session_state.user:
                update_profile(st.session_state.user, {"field": field, "hours_per_day": hours, "distractions": current_distractions})
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
    st.header("Stages & Rules (Read carefully)")
    st.markdown("""
**Easy (Silver)** — 15 days:
- Work **2 hours/day**.
- Avoid distractions (no scrolling).
- Fill daily checkbox form before sleeping.

**Medium (Platinum)** — 30 days:
- Work **4 hours/day**.
- Drink **5L water/day** + **30 pushups**.
- Avoid distractions; fill nightly form.

**Hard (Gold)** — 60 days:
- Wake **4 AM**, sleep **9 PM**.
- **1 hour** exercise each morning.
- Work **6 hours/day**.
- **5L water**, **no sugar**, **50 pushups**, **no junk food**.
- Daily positive mirror talk.
    """)
    st.write("")
    if st.button("Start Challenge (Join now)"):
        if not st.session_state.user:
            st.error("Please login first.")
        else:
            update_profile(st.session_state.user, {"joined": True, "started_on": datetime.now().strftime("%Y-%m-%d"), "stage": "Silver", "streak_days": 0, "savings": 0.0, "useless_days": 0})
            st.success("Challenge started. Please complete your profile.")
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
    with st.form("profile_form"):
        left, right = st.columns(2)
        with left:
            field = st.text_input("Chosen Field", value=prof.get("field",""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests", []))
            distractions = st.multiselect("Your common distractions", DISTRACTIONS_MASTER, default=prof.get("distractions", []))
        with right:
            hours = st.slider("Hours/day goal", 0.0, 12.0, float(prof.get("hours_per_day", 0.0)))
            stage = st.selectbox("Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(prof.get("stage","Silver")))
            st.write(f"Savings: {prof.get('savings',0.0)} PKR")
            st.write(f"Streak days: {prof.get('streak_days',0)}")
            st.write(f"Useless days: {prof.get('useless_days',0)}")
        save = st.form_submit_button("Save Profile")
    if save:
        update_profile(u, {"field": field, "interests": interests, "hours_per_day": hours, "stage": stage, "distractions": distractions})
        st.success("Profile saved. Opening Daily Routine.")
        st.session_state.page = "daily"
        st.rerun()
    st.markdown("---")
    st.subheader("Profile Summary")
    st.write(f"- Field: {prof.get('field','Not set')}")
    st.write(f"- Interests: {', '.join(prof.get('interests',[])) or 'None'}")
    st.write(f"- Hours/day goal: {prof.get('hours_per_day',0)}")
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
    st.header("Daily Routine — stage-specific checklist")
    c1, c2, c3 = st.columns(3)
    c1.metric("Stage", prof.get("stage","Silver"))
    c2.metric("Streak", prof.get("streak_days",0))
    c3.metric("Savings (PKR)", prof.get("savings",0.0))
    st.markdown("---")

    stage = prof.get("stage","Silver")
    # define required checkbox questions per stage
    if stage == "Silver":
        questions = [
            ("work_2h", "Did you work at least 2 hours today in your field?"),
            ("avoid_distractions", "Did you avoid distractions today (no scrolling)?")
        ]
    elif stage == "Platinum":
        questions = [
            ("work_4h", "Did you work at least 4 hours today in your field?"),
            ("avoid_distractions", "Did you avoid distractions today (no scrolling)?"),
            ("pushups_30", "Did you do at least 30 pushups today?"),
            ("water_5l", "Did you drink at least 5 liters of water today?")
        ]
    else:  # Gold
        questions = [
            ("work_6h", "Did you work at least 6 hours today in your field?"),
            ("avoid_distractions", "Did you avoid distractions today (no scrolling)?"),
            ("pushups_50", "Did you do at least 50 pushups today?"),
            ("water_5l", "Did you drink at least 5 liters of water today?"),
            ("avoid_sugar", "Did you avoid sugar today?"),
            ("woke_4am", "Did you wake around 4:00 AM today?"),
            ("slept_9pm", "Did you sleep around 9:00 PM last night?")
        ]

    today_key = datetime.now().strftime("%Y%m%d")
    responses = {}
    with st.form("daily_check_form"):
        for key,label in questions:
            widget_key = f"{username}_{today_key}_{key}"
            responses[key] = st.checkbox(label, key=widget_key)
        # optional informative fields
        junk_key = f"{username}_{today_key}_junk"
        junk_food = st.checkbox("Did you eat junk food today?", key=junk_key)
        pocket_key = f"{username}_{today_key}_pocket"
        pocket_money = st.number_input("If you fail and choose to pay, pocket money to save today (PKR):", 0.0, 10000.0, 0.0, 1.0, key=pocket_key)
        submit = st.form_submit_button("Submit Today's Check")
    if submit:
        # success if all required questions are True
        success = all(responses.values())
        # build log dict with stage-relevant fields
        log = {
            "stage": stage,
            "work_done": responses.get(questions[0][0], False),
            "distraction": (not responses.get("avoid_distractions", True)) if "avoid_distractions" in dict(questions).keys() else False,
            "pushups": None,
            "water_liters": None,
            "slept_9pm": None,
            "woke_4am": None,
            "sugar_avoided": None,
            "pocket_money": float(pocket_money)
        }
        # fill detailed fields if present
        if stage in ("Platinum", "Gold"):
            log["pushups"] = responses.get("pushups_30", responses.get("pushups_50", None))
            log["water_liters"] = 5.0 if responses.get("water_5l", False) else 0.0
        if stage == "Gold":
            log["sugar_avoided"] = responses.get("avoid_sugar", False)
            log["woke_4am"] = responses.get("woke_4am", False)
            log["slept_9pm"] = responses.get("slept_9pm", False)

        if success:
            # record success
            record_success_day(username, log)
            st.success("Excellent — all tasks completed! Take a motivational quote image from Google and set it as your wallpaper to remind yourself of the mission.")
            st.balloons()  # animation
            st.rerun()
        else:
            # show centered warning box (red) for penalty decision
            st.markdown(
                """
                <div class="center-box">
                  <h3>⚠️ You missed some required tasks today</h3>
                  <p>You didn't complete all stage tasks. To count this day as a (failed) day and add penalty to savings, please pay pocket money below.<br>
                  If you choose <b>Don't Count This Day</b>, then nothing will be saved and the day will not be recorded.</p>
                """,
                unsafe_allow_html=True
            )
            col1, col2 = st.columns([1,1])
            with col1:
                pay_amt_key = f"pen_amt_{username}_{today_key}"
                pay_amt = st.number_input("Enter pocket money to pay now (PKR):", 0.0, 10000.0, float(pocket_money), 1.0, key=pay_amt_key)
                if st.button("Pay & Count Day (Record failed day)", key=f"pay_{username}_{today_key}"):
                    if pay_amt <= 0:
                        st.error("Enter an amount greater than 0 to pay and record the day.")
                    else:
                        log["pocket_money"] = float(pay_amt)
                        record_failed_day(username, log)
                        st.success(f"Penalty paid {pay_amt} PKR. Failed day recorded. Now: take a motivational quote image from Google and set it as wallpaper.")
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.rerun()
            with col2:
                if st.button("Don't Count This Day (Skip & Don't Save)", key=f"skip_{username}_{today_key}"):
                    st.info("This day will NOT be counted. No log saved. Remember to be consistent tomorrow.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.rerun()
            # close center-box tag if not closed
            if not st.session_state.get(f"pen_handled_{username}_{today_key}", False):
                # mark handled? optional - we rely on rerun after button
                pass

    # ---------------- Show clean logs table ----------------
    logs = user_logs(username)
    if logs:
        st.markdown("---")
        st.subheader("Recent activity (latest 10)")
        df = pd.DataFrame(logs).sort_values("date", ascending=False).head(10)
        # Normalize columns to include all possible keys
        # Make columns: date, stage, work_done, distraction, pushups, water_liters, woke_4am, slept_9pm, sugar_avoided, pocket_money, result
        def safe_get(row, key):
            return row.get(key, None) if isinstance(row, dict) else None
        rows = []
        for r in df.to_dict(orient="records"):
            rows.append({
                "date": r.get("date"),
                "stage": r.get("stage"),
                "work_done": r.get("work_done"),
                "distraction": r.get("distraction"),
                "pushups": r.get("pushups"),
                "water_liters": r.get("water_liters"),
                "woke_4am": r.get("woke_4am"),
                "slept_9pm": r.get("slept_9pm"),
                "sugar_avoided": r.get("sugar_avoided"),
                "pocket_money": r.get("pocket_money", 0.0),
                "result": r.get("result", r.get("result",""))
            })
        df_clean = pd.DataFrame(rows)
        # show table
        st.dataframe(df_clean.reset_index(drop=True))

# ---------------- Main ----------------
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
