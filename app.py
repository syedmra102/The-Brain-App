# app.py
# The Brain - 105 Days (v4) — Fixed navigation + checkbox daily form + penalty modal
# Single-file Streamlit app (local data.json storage)
# Requirements: streamlit, pandas, numpy

import streamlit as st
import json, os
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

def record_failed_day(username, log):
    """Record a failed day (adds savings and useless_days)"""
    profile = store["users"][username]["profile"]
    profile["savings"] = round(profile.get("savings", 0.0) + float(log.get("pocket_money", 0.0)), 2)
    profile["useless_days"] = profile.get("useless_days", 0) + 1
    # also add log entry indicating failure
    entry = {"user": username, "date": datetime.now().strftime("%Y-%m-%d"), **log, "counted": True, "success": False}
    store["logs"].append(entry)
    save_store(store)

def record_success_day(username, log):
    """Record a successful day (increments streak)"""
    profile = store["users"][username]["profile"]
    profile["streak_days"] = profile.get("streak_days", 0) + 1
    entry = {"user": username, "date": datetime.now().strftime("%Y-%m-%d"), **log, "counted": True, "success": True}
    store["logs"].append(entry)
    save_store(store)

def user_logs(username):
    return [l for l in store["logs"] if l["user"] == username]

# ---------------- Predictor ----------------
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
            st.success("Registered: Please login.")
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
    st.header("Quick ML Prediction — Where do you stand now?")
    st.markdown("Answer a few questions below (distractions are on this page).")
    # Sidebar summary
    with st.sidebar:
        st.markdown("### Profile snapshot")
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.write(f"**User:** {st.session_state.user}")
            st.write(f"- Stage: {p.get('stage')}")
            st.write(f"- Field: {p.get('field') or 'Not set'}")
            st.write(f"- Savings: {p.get('savings',0.0)} PKR")
        st.markdown("---")
        if st.session_state.user and st.button("Open Profile"):
            st.session_state.page = "profile"
            st.rerun()

    # Main inputs (including distractions)
    field = st.selectbox("Choose a trending field", TRENDING_FIELDS)
    hours = st.slider("Hours per day you spend on this field", 0.0, 12.0, 2.0, 0.5)
    st.markdown("### Which distractions do you face right now? (select all)")
    current_distractions = st.multiselect("", DISTRACTIONS_MASTER, default=[])
    sugar = st.checkbox("I avoid sugar")
    exercise = st.checkbox("I exercise daily (30-60 min)")
    water = st.number_input("Liters of water/day", 0.0, 10.0, 2.0, 0.5)
    junk = st.checkbox("I eat junk food often")
    woke4 = st.checkbox("I wake ~4:00 AM")
    sleep9 = st.checkbox("I sleep ~9:00 PM")

    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, current_distractions, sugar, exercise, water, junk, woke4, sleep9)
        st.success(f"Estimated percentile: {pct}% — you are ahead of {pct}% people.")
        if pct >= 60:
            st.info(f"You're in top {pct}%. But top 1% is reachable with discipline.")
        elif pct >= 40:
            st.info(f"You are around top {pct}%. A plan will accelerate your progress.")
        else:
            st.warning(f"You are around {pct}%. Don't worry — start small and be consistent.")
        st.markdown("---")
        st.write("Would you like our free stage-based plan to reach top 1%?")
        if st.button("Yes — Make me top 1% (Free plan)"):
            # store selected field/hours/distractions to profile if logged in
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
        "Positive thinking and high EQ"
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
**Easy (Silver)** — 15 days:
- Work **2 hours/day**.
- Avoid distractions (no scrolling).
- Fill a short checkbox form each night.

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
            update_profile(st.session_state.user, {"joined": True, "started_on": datetime.now().strftime("%Y-%m-%d"), "stage":"Silver", "streak_days":0, "savings":0.0, "useless_days":0})
            st.success("Challenge started — please complete your profile.")
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
        left,right = st.columns(2)
        with left:
            field = st.text_input("Chosen Field", value=prof.get("field",""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests",[]))
            distractions = st.multiselect("Your common distractions", DISTRACTIONS_MASTER, default=prof.get("distractions",[]))
        with right:
            hours = st.slider("Hours/day goal", 0.0, 12.0, float(prof.get("hours_per_day",0.0)))
            stage = st.selectbox("Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(prof.get("stage","Silver")))
            st.write(f"Savings: {prof.get('savings',0.0)} PKR")
            st.write(f"Streak days: {prof.get('streak_days',0)}")
            st.write(f"Useless days: {prof.get('useless_days',0)}")
        save = st.form_submit_button("Save Profile")
    if save:
        update_profile(u, {"field": field, "interests": interests, "hours_per_day": hours, "stage": stage, "distractions": distractions})
        st.success("Profile saved — opening Daily Routine.")
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
    st.header("Daily Routine — only stage-specific checkboxes")
    cols = st.columns(3)
    cols[0].metric("Stage", prof.get("stage","Silver"))
    cols[1].metric("Streak", prof.get("streak_days",0))
    cols[2].metric("Savings (PKR)", prof.get("savings",0.0))
    st.markdown("---")

    stage = prof.get("stage","Silver")
    # build required task list depending on stage (display as checkboxes)
    # keys and human labels
    if stage == "Silver":
        reqs = [
            ("work_2h", "Did you work at least 2 hours today in your field?"),
            ("avoid_distractions", "Did you avoid distractions today (no scrolling)?")
        ]
    elif stage == "Platinum":
        reqs = [
            ("work_4h", "Did you work at least 4 hours today in your field?"),
            ("avoid_distractions", "Did you avoid distractions today (no scrolling)?"),
            ("pushups_30", "Did you do at least 30 pushups today?"),
            ("water_5l", "Did you drink at least 5 liters of water today?")
        ]
    else: # Gold
        reqs = [
            ("work_6h", "Did you work at least 6 hours today in your field?"),
            ("avoid_distractions", "Did you avoid distractions today (no scrolling)?"),
            ("pushups_50", "Did you do at least 50 pushups today?"),
            ("water_5l", "Did you drink at least 5 liters of water today?"),
            ("avoid_sugar", "Did you avoid sugar today?"),
            ("woke_4am", "Did you wake around 4:00 AM today?"),
            ("slept_9pm", "Did you sleep around 9:00 PM last night?")
        ]

    # create checkbox widgets with unique keys per user + date
    today_key = datetime.now().strftime("%Y%m%d")
    responses = {}
    with st.form("daily_check_form"):
        for key,label in reqs:
            widget_key = f"{username}_{today_key}_{key}"
            responses[key] = st.checkbox(label, key=widget_key)
        # optional junk food checkbox (not required but informative)
        junk_key = f"{username}_{today_key}_junk"
        junk_food = st.checkbox("Did you eat junk food today?", key=junk_key)
        pocket_key = f"{username}_{today_key}_pocket"
        pocket_money = st.number_input("If you fail and choose to pay, how much pocket money will you save today (PKR)?", 0.0, 10000.0, 0.0, 1.0, key=pocket_key)
        submit = st.form_submit_button("Submit Today's Check")

    if submit:
        # Evaluate success: all required boxes must be True
        success = all(responses.values())
        # create readable log data
        log = {
            "stage": stage,
            "responses": responses,
            "junk_food": bool(junk_food),
            "pocket_money": float(pocket_money)
        }
        if success:
            # record success (increment streak)
            record_success_day(username, log)
            st.success("Congratulations — you completed today's tasks! Take a motivational quote image and set it as wallpaper.")
            st.rerun()
        else:
            # open modal for penalty payment / don't count option
            with st.expander("⚠️ You missed some tasks — penalty required (click to open)"):
                st.write("You did not complete all required tasks for your stage.")
                st.write("You can either *pay pocket money* now (it will be added to your savings) or *choose not to pay* — if you choose not to pay, **this day will NOT be counted** (no log saved).")
                pay_amt = st.number_input("Enter pocket money amount to add to savings (PKR)", 0.0, 10000.0, float(pocket_money), 1.0, key=f"pen_{username}_{today_key}")
                col1,col2 = st.columns(2)
                if col1.button("Pay & Record failed day"):
                    if pay_amt <= 0:
                        st.error("Enter an amount greater than 0 to pay and record the day.")
                    else:
                        log["pocket_money"] = float(pay_amt)
                        record_failed_day(username, log)
                        st.success(f"Penalty paid {pay_amt} PKR. Failed day recorded and savings updated.")
                        st.rerun()
                if col2.button("I won't pay — Don't count this day"):
                    st.info("Okay — this day will NOT be counted. No record saved.")
                    st.rerun()

    # Show last 10 logs relevant to this user, and only columns relevant to stage (quick view)
    logs = user_logs(username)
    if logs:
        st.markdown("---")
        st.subheader("Recent activity (latest 10)")
        df = pd.DataFrame(logs).sort_values("date", ascending=False).head(10)
        # Present responses column nicely: only show keys in responses per-row
        def summarize_row(r):
            # r may contain 'responses' field
            res = r.get("responses", {})
            parts = []
            for k,v in res.items():
                parts.append(f"{k.split('_')[0]}: {'OK' if v else 'NO'}")
            pm = r.get("pocket_money", 0.0)
            return f"{', '.join(parts)} | pocket: {pm} | success: {r.get('success')}"
        df_display = pd.DataFrame({
            "date": df["date"],
            "summary": df.apply(summarize_row, axis=1),
            "counted": df.get("counted", True),
            "success": df.get("success", False)
        })
        st.dataframe(df_display)

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
