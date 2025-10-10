# app.py (v5.3) - Final Code with Exceptional Classy Styling

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

# ---------------- Classy Dark Theme Styling ----------------
def inject_style():
    # We will use the Google Font 'Poppins' for a modern, clean look.
    # The background image is key for the "exceptional" feel.
    # IMPORTANT: Change the background-image URL to your image path.
    # For local testing, ensure 'assets/dark_bg.jpg' is correct.
    # For deployment (e.g., Streamlit Community Cloud), this path often needs adjustment.
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    /* Global Styles & Background */
    .stApp {
        font-family: 'Poppins', sans-serif;
        /* Replace 'assets/dark_bg.jpg' with your actual image path or URL */
        background-image: url("https://i.imgur.com/kS5xW1L.jpg"); 
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        min-height: 100vh;
        color: #EAF6FF; /* Off-white text for high contrast */
        padding-bottom: 40px;
    }
    
    /* Ensure all text is visible over the dark background */
    .stApp, .stApp * { color: #EAF6FF; } 
    
    /* Headers - Stronger color and font weight */
    h1, h2, h3, h4 { 
        color: #A0D3FF !important; /* Soft blue for headings */
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.4);
    }
    
    /* Sidebar - Semi-transparent, dark background */
    section[data-testid="stSidebar"] { 
        background-color: rgba(10, 25, 40, 0.9) !important; /* Dark navy, slightly transparent */
        border-right: 2px solid #204060;
        box-shadow: 3px 0 10px rgba(0,0,0,0.6);
    } 
    section[data-testid="stSidebar"] * { 
        color: #EAF6FF !important; /* Light text in sidebar */
        font-weight: 300;
    }

    /* Buttons - Primary Action Look */
    div.stButton > button, .stButton button {
        background-color: #1DB954 !important; /* Vibrant Green */
        color: black !important; /* Black text on green for contrast */
        font-weight: 600 !important;
        border: none !important;
        border-radius: 20px !important; /* Rounded pill shape */
        padding: 10px 20px !important;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover, .stButton button:hover {
        background-color: #169E43 !important; /* Darker green on hover */
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 4px 10px rgba(29, 185, 84, 0.5);
    }
    
    /* Input Fields & Text Areas - Subtle, transparent dark */
    input, textarea { 
        background-color: rgba(255,255,255,0.06) !important; 
        color: white !important; 
        border: 1px solid #304050;
        border-radius: 8px;
        padding: 10px;
    }
    
    /* Cards/Boxes - Subtle frosted glass effect */
    .card, div[data-testid="stVerticalBlock"] > div:has(div.stExpander) { 
        background: rgba(255,255,255,0.05); 
        backdrop-filter: blur(5px);
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    /* Metrics - Clean and prominent */
    div[data-testid="stMetric"] > div[data-testid="stVerticalBlock"] > div:nth-child(1) {
        font-size: 0.9rem; /* Label size */
        color: #A0D3FF !important; /* Metric label color */
    }
    div[data-testid="stMetric"] > div[data-testid="stVerticalBlock"] > div:nth-child(2) > div:nth-child(1) {
        font-size: 1.8rem; /* Value size */
        font-weight: 700;
        color: #1DB954 !important; /* Highlight value */
    }
    
    /* Custom Warning Boxes (Penalties) */
    .center-box {
        max-width:700px;
        margin: 30px auto;
        background: rgba(43, 0, 0, 0.8); /* Dark red background */
        border: 2px solid #FF4D4D;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
    }
    .center-box h3 { color: #FFB3B3; margin-top:0; }
    .center-box p { color: #FFEAEA; }
    
    /* Custom Success Boxes */
    .center-box-success {
        max-width:700px;
        margin: 30px auto;
        background: rgba(0, 43, 0, 0.8); /* Dark green background */
        border: 2px solid #4DFF4D;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
    }
    .center-box-success h3 { color: #B3FFB3; margin-top:0; }
    .center-box-success p { color: #EAFFEA; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------------- ALL OTHER CODE REMAINS THE SAME ----------------

# The rest of your functions (create_user, check_user, update_profile, 
# record_failed_day_skip, record_day_with_penalty, check_and_update_stage, 
# predict_percentile, page_login, page_predict, page_offer, page_rules, 
# page_profile, page_daily, main) are unchanged from your original request.

# ... (Insert the rest of your original app.py code here) ...

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
    
    # Reset streak because failure occurred
    profile["streak_days"] = 0 
    
    # Increment useless day count ONLY if they fail AND skip the penalty.
    profile["useless_days"] = profile.get("useless_days", 0) + 1
    
    # DO NOT append to logs, as requested ("not countable")
    save_store(store)

def record_day_with_penalty(username, log, success_status="Success (Paid Penalty)"):
    """
    Records a day where penalty was paid. This guarantees a 'Success' status 
    for the day, even if tasks were missed.
    """
    profile = store["users"][username]["profile"]
    pay = float(log.get("pocket_money", 0.0))
    
    # Update savings immediately
    profile["savings"] = round(profile.get("savings", 0.0) + pay, 2)
    
    # Success, so increase streak (unless it was already at the max for the stage)
    # The check_and_update_stage handles the progression and streak reset
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
        "result": success_status # "Success (Paid Penalty)" or "Success"
    }
    store["logs"].append(entry)
    save_store(store)


def check_and_update_stage(username, current_streak):
    profile = store["users"][username]["profile"]
    current_stage = profile.get("stage", "Silver")
    current_badges = profile.get("badges", [])
    
    # Stage goals (minimum streak days required)
    SILVER_DAYS = 15
    PLATINUM_DAYS = 30
    GOLD_DAYS = 60
    
    promoted = False

    # 1. Promote from Silver -> Platinum (Requires 15 days)
    if current_stage == "Silver" and current_streak >= SILVER_DAYS:
        if "Silver" not in current_badges:
            profile["badges"].append("Silver")
            st.success("🏆 CONGRATULATIONS! You earned the **Silver Badge**!")
            
        profile["stage"] = "Platinum"
        profile["streak_days"] = 0 # Reset streak for next stage
        profile["hours_per_day"] = 4.0 # Set hours goal for the new stage
        st.success("🌟 You have advanced to the **Platinum Stage**! New goals await.")
        promoted = True
    
    # 2. Promote from Platinum -> Gold (Requires 30 days AND Silver Badge)
    elif current_stage == "Platinum" and current_streak >= PLATINUM_DAYS:
        if "Silver" in current_badges:
            if "Platinum" not in current_badges:
                profile["badges"].append("Platinum")
                st.success("🌟 PHENOMENAL! You earned the **Platinum Badge**!")
            
            profile["stage"] = "Gold"
            profile["streak_days"] = 0 # Reset streak for next stage
            profile["hours_per_day"] = 6.0 # Set hours goal for the new stage
            st.success("👑 You have advanced to the **Gold Stage**! You are nearly unstoppable.")
            promoted = True
        else:
            st.warning("You must earn the Silver Badge before progressing to Platinum stage! (Error in log history, please contact support).")
            
    # 3. Complete Gold Stage (Requires 60 days AND Silver + Platinum Badges)
    elif current_stage == "Gold" and current_streak >= GOLD_DAYS:
        if "Silver" in current_badges and "Platinum" in current_badges:
            if "Gold" not in current_badges:
                profile["badges"].append("Gold")
                st.balloons()
                st.success("👑 MISSION COMPLETE! You earned the **Gold Badge** and finished the **105-Day Challenge!**")
                profile["joined"] = False # End of challenge
            promoted = True # Not a stage change, but a completion status

    if promoted:
        save_store(store)


# ---------------- Predictor and Pages (Unchanged) ----------------
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
    st.markdown("<h2 style='color:#A0D3FF;'>Login / Register</h2>", unsafe_allow_html=True)
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
    st.markdown("Answer a few quick questions to estimate your current focus potential.")
    # Sidebar quick snapshot
    with st.sidebar:
        st.markdown("### Snapshot")
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.write(f"User: {st.session_state.user}")
            st.write(f"Stage: **{p.get('stage')}**")
            st.write(f"Field: {p.get('field') or 'Not set'}")
            st.write(f"Savings: **{p.get('savings',0.0)} PKR**")
            st.markdown(f"**Badges:** {' '.join([f'✅ {b}' for b in p.get('badges',[])]) or 'None'}")
        st.markdown("---")
        if st.session_state.user and st.button("Open Profile"):
            st.session_state.page = "profile"
            st.rerun()

    if "pred_inputs" not in st.session_state:
        st.session_state.pred_inputs = {}

    field = st.selectbox("Choose a trending field", TRENDING_FIELDS, index=TRENDING_FIELDS.index(st.session_state.pred_inputs.get("field", TRENDING_FIELDS[0])) if st.session_state.pred_inputs.get("field") in TRENDING_FIELDS else 0)
    hours = st.slider("Hours/day you spend on this field", 0.0, 12.0, float(st.session_state.pred_inputs.get("hours", 2.0)), 0.5)
    st.markdown("### Which distractions do you face now?")
    current_distractions = st.multiselect("", DISTRACTIONS_MASTER, default=st.session_state.pred_inputs.get("distractions", []))
    sugar = st.checkbox("I avoid sugar", value=st.session_state.pred_inputs.get("avoid_sugar", False))
    exercise = st.checkbox("I exercise daily (30-60 min)", value=st.session_state.pred_inputs.get("exercise", False))
    water = st.number_input("Liters of water/day", 0.0, 10.0, float(st.session_state.pred_inputs.get("water", 2.0)), 0.5)
    avoid_junk = st.checkbox("I avoid junk food today", value=st.session_state.pred_inputs.get("avoid_junk", False))
    woke4 = st.checkbox("I wake ~4:00 AM", value=st.session_state.pred_inputs.get("woke4", False))
    sleep9 = st.checkbox("I sleep ~9:00 PM", value=st.session_state.pred_inputs.get("sleep9", False))

    st.session_state.pred_inputs = {
        "field": field, "hours": hours, "distractions": current_distractions,
        "avoid_sugar": sugar, "exercise": exercise, "water": water,
        "avoid_junk": avoid_junk, "woke4": woke4, "sleep9": sleep9
    }

    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, current_distractions, sugar, exercise, water, avoid_junk, woke4, sleep9)
        st.success(f"Estimated Focus Potential: **{pct}%**. You are ahead of **{pct}%** of people.")
        if pct >= 60:
            st.info(f"You're in top {pct}%. With a focused plan **top 1% is reachable**.")
        elif pct >= 40:
            st.info(f"You are around top {pct}%. A plan will **accelerate progress**.")
        else:
            st.warning(f"You are around {pct}%. **Start consistent daily habits**.")
        
        st.markdown("---")
        st.write("Do you want our free stage-based plan to become top 1% (skills + health)?")
        if st.button("Yes — Make me top 1% (Free plan)", key="accept_plan"):
            st.session_state.page = "offer"
            
        if st.session_state.user:
            update_profile(st.session_state.user, {
            "field": st.session_state.pred_inputs["field"],
            "distractions": st.session_state.pred_inputs["distractions"]
                })
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
    if st.button("Start Challenge (Join now)"):
        if not st.session_state.user:
            st.error("Please login first.")
        else:
            update_profile(st.session_state.user, {"joined": True, "started_on": datetime.now().strftime("%Y-%m-%d"), "stage": "Silver", "streak_days": 0, "savings": 0.0, "useless_days": 0, "badges": []})
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

    STAGE_GOAL_MAP = {"Silver": 2.0, "Platinum": 4.0, "Gold": 6.0}

    with st.form("profile_form"):
        left, right = st.columns(2)
        with left:
            field = st.text_input("Chosen Field (What you want to become)", value=prof.get("field",""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests", []))
            distractions = st.multiselect("Your common distractions", DISTRACTIONS_MASTER, default=prof.get("distractions", []))
        with right:
            current_stage = prof.get("stage", "Silver")
            stage = st.selectbox("Current Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(current_stage))
            
            auto_hours = STAGE_GOAL_MAP.get(stage, 0.0)
            st.markdown(f"**Hours/day Goal:** **{auto_hours} hours** (Set automatically by Stage)")

            st.write(f"Savings: **{prof.get('savings',0.0)} PKR**")
            st.write(f"Streak days: **{prof.get('streak_days',0)}**")
            st.write(f"Useless days: **{prof.get('useless_days',0)}**")

        save = st.form_submit_button("Save Profile")
    if save:
        update_profile(u, {
            "field": field, 
            "interests": interests, 
            "hours_per_day": auto_hours, 
            "stage": stage, 
            "distractions": distractions
        })
        st.success("Profile saved. Opening Daily Routine.")
        st.session_state.page = "daily"
        st.rerun()
    st.markdown("---")
    st.subheader("Profile Summary")
    prof = store["users"][u]["profile"]
    st.write(f"- Field: **{prof.get('field','Not set')}**")
    st.write(f"- Hours/day goal: **{prof.get('hours_per_day',0)}**")
    st.write(f"- Current Stage: **{prof.get('stage','Silver')}**")
    st.write(f"- Badges Earned: **{' '.join([f'✅ {b}' for b in prof.get('badges',[])]) or 'None'}**")
    st.write(f"- Savings: **{prof.get('savings',0.0)} PKR**")
    st.write(f"- Streak days: **{prof.get('streak_days',0)}**")
    st.write(f"- Useless days: **{prof.get('useless_days',0)}**")


def page_daily():
    if not st.session_state.user:
        st.error("Login first.")
        return
    username = st.session_state.user
    prof = store["users"][username]["profile"]
    
    # Check and update stage at the start of the page load
    check_and_update_stage(username, prof.get("streak_days", 0))

    st.header("Daily Routine — stage-specific checklist")
    c1, c2, c3 = st.columns(3)
    c1.metric("Stage", f"{prof.get('stage','Silver')} ({prof.get('hours_per_day', 0.0)} hr goal)")
    c2.metric("Current Streak", prof.get("streak_days",0))
    c3.metric("Total Savings (PKR)", prof.get("savings",0.0)) # Display total savings here
    st.markdown(f"**Badges:** {' '.join([f'✅ {b}' for b in prof.get('badges',[])]) or 'None'}")
    st.markdown("---")

    stage = prof.get("stage","Silver")
    
    # Define questions based on stage
    if stage == "Silver":
        questions = [("work_done",f"Did you work at least {prof.get('hours_per_day', 2.0)} hours today in your field?"),
                      ("distraction","Did you avoid distractions today (no scrolling)?"),
                      ("avoid_junk","Did you avoid junk food today?")]
    elif stage == "Platinum":
        questions = [("work_done",f"Did you work at least {prof.get('hours_per_day', 4.0)} hours today in your field?"),
                      ("distraction","Did you avoid distractions today (no scrolling)?"),
                      ("pushups","Did you do at least 30 pushups today?"),
                      ("water_liters","Did you drink at least 5 liters of water today?"),
                      ("avoid_junk","Did you avoid junk food today?")]
    else: # Gold
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
        for key,label in questions:
            widget_key = f"{username}_{today_key}_{key}" 
            responses[key] = st.checkbox(label, key=widget_key)
        pocket_key = f"{username}_{today_key}_pocket"
        pocket_money = st.number_input("Pocket money to save today (PKR):", 0.0, 10000.0, 0.0, 1.0, key=pocket_key)
        submit = st.form_submit_button("Submit Today's Check")
        
    if submit:
        success = all(responses.values())
        
        # Build log dictionary from responses, converting stage-specific inputs
        log = {
            "stage": stage,
            # We track the actual completion status of each task for the log
            "work_done": responses.get("work_done", False),
            "distraction": responses.get("distraction", False), 
            "woke_4am": responses.get("woke_4am", None),
            "slept_9pm": responses.get("slept_9pm", None),
            "sugar_avoided": responses.get("sugar_avoided", None),
            "avoid_junk": responses.get("avoid_junk", None),
            "pocket_money": float(pocket_money)
        }
        
        # Handle stage-specific numeric logging (pushups, water)
        log["pushups"] = 0
        if "pushups" in responses and responses["pushups"]: 
            log["pushups"] = 30 if stage == "Platinum" else 50 # If checked, they met the minimum
        
        log["water_liters"] = 0.0
        if "water_liters" in responses and responses["water_liters"]:
            log["water_liters"] = 5.0
            
        if success:
            # Case 1: All tasks completed (with or without penalty paid)
            if float(pocket_money) > 0:
                record_day_with_penalty(username, log, success_status="Success (Plus Bonus Savings)")
                st.markdown("""<div class="center-box-success">
                  <h3>🎉 PERFECT DAY!</h3>
                  <p>You completed all tasks AND saved <strong>{pocket_money} PKR</strong>! Streak continues! 
                  <strong>Last task: Search a motivational quote image on Google and set it as your wallpaper!</strong></p>
                  </div>""".format(pocket_money=pocket_money), unsafe_allow_html=True)
            else:
                record_day_with_penalty(username, log, success_status="Success")
                st.markdown("""<div class="center-box-success">
                  <h3>✅ Excellent — all tasks completed!</h3>
                  <p>Streak continues! 
                  <strong>Last task: Search a motivational quote image on Google and set it as your wallpaper!</strong></p>
                  </div>""", unsafe_allow_html=True)
            st.balloons()
            st.rerun()
            
        else:
            # Case 2: One or more tasks failed
            st.markdown(
                """
                <div class="center-box">
                  <h3>⚠️ Day Failed — Decide Your Penalty</h3>
                  <p>You missed one or more required tasks today. **You must pay the penalty to save the day (SUCCESS).**</p>
                  <p>If you choose **Don't Count This Day**, your streak **resets to 0** and the day is counted as **useless**.</p>
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
                        st.markdown("""<div class="center-box-success">
                            <h3>Penalty Paid: {pay_amt} PKR</h3>
                            <p>The day is saved as SUCCESS and your streak continues! 
                            <strong>Last task: Set that motivational quote wallpaper!</strong></p>
                            </div>""".format(pay_amt=pay_amt), unsafe_allow_html=True)
                        st.rerun()
            with cols[1]:
                if st.button("Don't Count This Day (Skip & Reset Streak)", key=f"skip_{username}_{today_key}"):
                    # Log an empty day and reset streak
                    record_failed_day_skip(username)
                    st.warning("This day will NOT be counted, streak reset to 0, and a useless day counted. You must do all of the same efforts **today** (re-submit this form tomorrow).")
                    st.rerun()

    # ---------------- show ALL logs table ----------------
    logs = [l for l in store["logs"] if l["user"] == username]
    if logs:
        st.markdown("---")
        st.subheader(f"Full Activity Log (Current Stage: {stage})")
        df = pd.DataFrame(logs).sort_values("date", ascending=False)
        
        # Determine columns to show based on the user's current stage
        base_cols = ["date", "stage", "result", "work_done", "distraction"]
        platinum_cols = ["pushups", "water_liters"]
        gold_cols = ["sugar_avoided", "woke_4am", "slept_9pm"]
        
        # Get all unique columns that have been logged for this user
        all_cols = list(set(base_cols + platinum_cols + gold_cols + ["pocket_money"]))
        
        # Ensure all required columns for display exist in the DataFrame
        df_clean = pd.DataFrame({col: df.get(col) for col in all_cols})
        df_clean = df_clean.dropna(axis=1, how='all') # Drop columns where all values are NaN
        
        # Custom renaming for the display (optional but nice)
        display_names = {
            "work_done": "Work $\checkmark$", "distraction": "Distraction X", 
            "pushups": "Pushups", "water_liters": "Water (L)", 
            "sugar_avoided": "No Sugar $\checkmark$", "woke_4am": "Wake 4AM $\checkmark$", 
            "slept_9pm": "Sleep 9PM $\checkmark$", "pocket_money": "Savings (PKR)",
            "result": "Day Result", "stage": "Stage"
        }
        df_clean = df_clean.rename(columns=display_names)
        
        st.dataframe(df_clean.reset_index(drop=True), hide_index=True, use_container_width=True)


# ---------------- Main ----------------
def main():
    st.set_page_config(page_title="The Brain - 105 Days", layout="wide")
    inject_style()

    # session defaults
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "pred_inputs" not in st.session_state:
        st.session_state.pred_inputs = {}

    # Sidebar
    st.sidebar.title("Menu")
    if st.session_state.user:
        st.sidebar.markdown(f"**User:** {st.session_state.user}")
        p = store["users"][st.session_state.user]["profile"]
        st.sidebar.write(f"Stage: **{p.get('stage','Silver')}**")
        st.sidebar.write(f"Hours/day: {p.get('hours_per_day',0)}")
        st.sidebar.write(f"Savings: **{p.get('savings',0.0)} PKR**")
        st.sidebar.write(f"Streak: **{p.get('streak_days',0)}**")
        st.sidebar.write(f"Useless days: {p.get('useless_days',0)}")
        st.sidebar.markdown(f"**Badges:** {' '.join([f'✅ {b}' for b in p.get('badges',[])]) or 'None'}")
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Focus Nudges**")
        ds = p.get("distractions", [])
        if ds:
            for d in ds:
                st.sidebar.write(f"- ❌ {d}")
        else:
            st.sidebar.write("None set")
        st.sidebar.markdown("---")
        
        # Sidebar Navigation Buttons
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
        st.markdown("<h1 style='color:#A0D3FF;'>🧠 The Brain — 105 Days Life Change</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#A0D3FF;'>Login / Register to start. Flow: **Prediction → Offer → Rules → Profile → Daily Routine.**</p>", unsafe_allow_html=True)
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
