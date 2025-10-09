# app.py (v5.0) - Enhanced Behavioral Nudge System
# - Implements automatic stage progression (Silver, Platinum, Gold).
# - Adds motivational quote nudge for discipline.
# - Refines penalty flow and wording.
# - Shows stage-relevant logs and badge status.
# - Focus on Linear Scoring Model for transparency.
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


# ---------------- Storage helpers ----------------
# ... (load_store and save_store definitions, which you kept) ...

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
            "badges": [] # New: To track earned badges
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
# ... (rest of the user helpers like record_failed_day_with_penalty, etc. should follow) ...

# ---------------- Pages ----------------
def page_login():
    st.markdown("<h2 style='color:white;'>Login / Register</h2>", unsafe_allow_html=True)
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
            # Default navigation is set to 'predict' after successful login
            st.session_state.page = "predict" 
            st.rerun()
        else:
            st.error("Invalid credentials.")


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
    /* Center box - Penalty Warning */
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
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------------- User helpers ----------------
# ... (create_user, check_user, update_profile remain the same) ...
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
            "badges": [] # New: To track earned badges
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

def record_failed_day_with_penalty(username, log):
    """Record a failed day and add penalty to savings and increment useless_days."""
    profile = store["users"][username]["profile"]
    pay = float(log.get("pocket_money", 0.0))
    # NOTE: The penalty flow is handled by the buttons in page_daily now.
    # The 'pocket_money' field here is the penalty amount *chosen* by the user to save.
    profile["savings"] = round(profile.get("savings", 0.0) + pay, 2)
    profile["useless_days"] = profile.get("useless_days", 0) + 1
    # Reset streak on failure
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
        "pocket_money": pay,
        "counted": True,
        "result": "Failed (penalty paid)"
    }
    store["logs"].append(entry)
    save_store(store)

def record_success_day(username, log):
    profile = store["users"][username]["profile"]
    profile["streak_days"] = profile.get("streak_days", 0) + 1
    # Check for stage progression on success
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
        "pocket_money": float(log.get("pocket_money", 0.0)),
        "counted": True,
        "result": "Success"
    }
    store["logs"].append(entry)
    save_store(store)

def user_logs(username):
    return [l for l in store["logs"] if l["user"] == username]

def check_and_update_stage(username, current_streak):
    profile = store["users"][username]["profile"]
    current_stage = profile.get("stage", "Silver")
    current_badges = profile.get("badges", [])
    
    if current_stage == "Silver" and current_streak >= 15:
        profile["stage"] = "Platinum"
        profile["streak_days"] = 0 # Reset streak for next stage
        if "Silver" not in current_badges:
            profile["badges"].append("Silver")
            st.success("🏆 CONGRATULATIONS! You earned the **Silver Badge** and advanced to the **Platinum Stage**!")
    
    elif current_stage == "Platinum" and current_streak >= 30:
        profile["stage"] = "Gold"
        profile["streak_days"] = 0 # Reset streak for next stage
        if "Platinum" not in current_badges:
            profile["badges"].append("Platinum")
            st.success("🌟 PHENOMENAL! You earned the **Platinum Badge** and advanced to the **Gold Stage**!")

    elif current_stage == "Gold" and current_streak >= 60:
        if "Gold" not in current_badges:
            profile["badges"].append("Gold")
            st.balloons()
            st.success("👑 MISSION COMPLETE! You earned the **Gold Badge** and finished the **105-Day Challenge!**")
            profile["joined"] = False # End of challenge

    save_store(store)


# ---------------- Predictor ----------------
TRENDING_FIELDS = ["AI", "Programming", "Cybersecurity", "Data Science", "Content Creation", "Finance", "Health", "Design"]
DISTRACTIONS_MASTER = ["Social media", "Gaming", "YouTube", "Scrolling news", "TV/Netflix", "Sleep late", "Friends/Calls", "Browsing random sites"]

def predict_percentile(field, hours_per_day, distractions_list, sugar_avoided, exercise_daily, water_liters, avoid_junkfood, woke_4am, slept_9pm):
    # NOTE: The current function uses a simple Linear Scoring Model, which is the 
    # most transparent and best model for a behavioral-nudge system.
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

# ---------------- Pages ----------------
# ... (page_login remains the same) ...

def page_predict():
    st.header("Quick Prediction — Where do you stand?")
    st.markdown("Answer a few quick questions to estimate your current focus potential.")
    # Sidebar quick snapshot
    with st.sidebar:
        st.markdown("### Snapshot")
        if st.session_state.user:
            p = store["users"][st.session_state.user]["profile"]
            st.write(f"User: {st.session_state.user}")
            st.write(f"Stage: {p.get('stage')}")
            st.write(f"Field: {p.get('field') or 'Not set'}")
            st.write(f"Savings: {p.get('savings',0.0)} PKR")
            # Display Badges
            st.markdown(f"**Badges:** {' '.join([f'✅ {b}' for b in p.get('badges',[])]) or 'None'}")
        st.markdown("---")
        if st.session_state.user and st.button("Open Profile"):
            st.session_state.page = "profile"
            st.rerun()

    # Keep inputs in session_state so navigation survives
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

    # Save inputs to session so they persist across rerun/navigation
    st.session_state.pred_inputs = {
        "field": field, "hours": hours, "distractions": current_distractions,
        "avoid_sugar": sugar, "exercise": exercise, "water": water,
        "avoid_junk": avoid_junk, "woke4": woke4, "sleep9": sleep9
    }

    if st.button("Get Prediction"):
        pct = predict_percentile(field, hours, current_distractions, sugar, exercise, water, avoid_junk, woke4, sleep9)
        st.success(f"Estimated Focus Potential: {pct}%. You are ahead of {pct}% of people.")
        if pct >= 60:
            st.info(f"You're in top {pct}%. With a focused plan top 1% is reachable.")
        elif pct >= 40:
            st.info(f"You are around top {pct}%. A plan will accelerate progress.")
        else:
            st.warning(f"You are around {pct}%. Start consistent daily habits.")
        st.markdown("---")
        st.write("Do you want our free stage-based plan to become top 1% (skills + health)?")
        # Direct navigation to offer page
        if st.button("Yes — Make me top 1% (Free plan)", key="accept_plan"):
            if st.session_state.user:
                update_profile(st.session_state.user, {
                    "field": st.session_state.pred_inputs["field"],
                    "hours_per_day": st.session_state.pred_inputs["hours"],
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
    # Direct navigation to rules page
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
1.  **Pay the Penalty:** Pay the amount of pocket money you intended to save today. This money is **added to your savings**, but your **streak resets to 0**, and the day is counted as **useless**.
2.  **Don't Count:** The day is **NOT recorded**, meaning **no streak reset**, but also **no savings** and **no useless day** count. The day is effectively a skip.

This enforces the habit: either you commit fully, or you pay to acknowledge failure and save for the future.
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
    with st.form("profile_form"):
        left, right = st.columns(2)
        with left:
            field = st.text_input("Chosen Field", value=prof.get("field",""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=prof.get("interests", []))
            distractions = st.multiselect("Your common distractions", DISTRACTIONS_MASTER, default=prof.get("distractions", []))
        with right:
            hours = st.slider("Hours/day goal", 0.0, 12.0, float(prof.get("hours_per_day", 0.0)))
            # Allow stage to be updated manually only if not in badges
            current_stage_index = ["Silver","Platinum","Gold"].index(prof.get("stage","Silver"))
            stage_options = ["Silver", "Platinum", "Gold"]
            stage = st.selectbox("Stage", stage_options, index=current_stage_index)
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
    c1.metric("Stage", f"{prof.get('stage','Silver')} ({len(user_logs(username))} days total)")
    c2.metric("Current Streak", prof.get("streak_days",0))
    c3.metric("Savings (PKR)", prof.get("savings",0.0))
    st.markdown(f"**Badges:** {' '.join([f'✅ {b}' for b in prof.get('badges',[])]) or 'None'}")
    st.markdown("---")

    stage = prof.get("stage","Silver")
    # Define questions and their corresponding log keys
    if stage == "Silver":
        questions = [("work_done","Did you work at least 2 hours today in your field?"),
                     ("distraction","Did you avoid distractions today (no scrolling)?"),
                     ("avoid_junk","Did you avoid junk food today?")]
    elif stage == "Platinum":
        questions = [("work_done","Did you work at least 4 hours today in your field?"),
                     ("distraction","Did you avoid distractions today (no scrolling)?"),
                     ("pushups","Did you do at least 30 pushups today?"),
                     ("water_liters","Did you drink at least 5 liters of water today?"),
                     ("avoid_junk","Did you avoid junk food today?")]
    else: # Gold
        questions = [("work_done","Did you work at least 6 hours today in your field?"),
                     ("distraction","Did you avoid distractions today (no scrolling)?"),
                     ("pushups","Did you do at least 50 pushups today?"),
                     ("water_liters","Did you drink at least 5 liters of water today?"),
                     ("sugar_avoided","Did you avoid sugar today?"),
                     ("woke_4am","Did you wake ~4:00 AM today?"),
                     ("slept_9pm","Did you sleep around 9:00 PM last night?"),
                     ("avoid_junk","Did you avoid junk food today?")]
    
    # Map questions keys to log keys for log building
    log_keys = {
        "work_done": None, "distraction": None, "pushups": None, 
        "water_liters": None, "woke_4am": None, "slept_9pm": None, 
        "sugar_avoided": None, "avoid_junk": None
    }
    
    responses = {}
    with st.form("daily_form"):
        for key,label in questions:
            widget_key = f"{username}_{today_key}_{key}"
            responses[key] = st.checkbox(label, key=widget_key)
        pocket_key = f"{username}_{today_key}_pocket"
        pocket_money = st.number_input("Pocket money to save today (PKR):", 0.0, 10000.0, 0.0, 1.0, key=pocket_key)
        submit = st.form_submit_button("Submit Today's Check")
        
    if submit:
        # success if all responses True
        success = all(responses.values())
        
        # Build log dictionary from responses, converting stage-specific inputs
        log = {
            "stage": stage,
            "work_done": responses.get("work_done", False),
            "distraction": not responses.get("distraction", True), # True=Avoided -> False=Distracted
            "woke_4am": responses.get("woke_4am", None),
            "slept_9pm": responses.get("slept_9pm", None),
            "sugar_avoided": responses.get("sugar_avoided", None),
            "pocket_money": float(pocket_money)
        }
        
        # Handle stage-specific numeric logging (pushups, water)
        log["pushups"] = 0
        if "pushups" in responses: 
            if stage == "Platinum" and responses["pushups"]: log["pushups"] = 30
            elif stage == "Gold" and responses["pushups"]: log["pushups"] = 50
        
        log["water_liters"] = 0.0
        if "water_liters" in responses and responses["water_liters"]:
            log["water_liters"] = 5.0
            
        if success:
            record_success_day(username, log)
            st.success("✅ Excellent — all tasks completed! Streak continues! **Last task: Search a motivational quote image on Google and set it as your wallpaper!**")
            st.balloons()
            st.rerun()
        else:
            # Show centered warning box for penalty decision
            st.markdown(
                """
                <div class="center-box">
                  <h3>⚠️ Day Failed — Decide Your Penalty</h3>
                  <p>You missed required tasks today. To record this day (and save your pocket money), your streak must **reset to 0** and the day is counted as **useless**.</p>
                  <p>If you choose **Don't Count This Day**, the day will NOT be recorded (no streak reset, no savings, no useless day).</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols = st.columns([1,1])
            with cols[0]:
                if st.button(f"Pay {pocket_money} PKR & Count Day (Reset Streak)", key=f"pay_{username}_{today_key}"):
                    if float(pocket_money) <= 0:
                        st.error("Enter an amount greater than 0 to pay and record the day.")
                    else:
                        log["pocket_money"] = float(pocket_money)
                        record_failed_day_with_penalty(username, log)
                        st.success(f"Penalty paid {pocket_money} PKR. Streak reset to 0. Failed day recorded and savings updated. **Last task: Set that motivational quote wallpaper!**")
                        st.rerun()
            with cols[1]:
                if st.button("Don't Count This Day (Skip & Don't Save)", key=f"skip_{username}_{today_key}"):
                    st.info("This day will NOT be counted. No record saved.")
                    st.rerun()

    # ---------------- show clean logs table ----------------
    logs = user_logs(username)
    if logs:
        st.markdown("---")
        st.subheader(f"Recent Activity (Stage: {stage})")
        df = pd.DataFrame(logs).sort_values("date", ascending=False).head(10)
        
        # Determine columns to show based on the user's current stage
        base_cols = ["date", "stage", "result", "work_done", "distraction"]
        platinum_cols = ["pushups", "water_liters"]
        gold_cols = ["sugar_avoided", "woke_4am", "slept_9pm"]
        
        if stage == "Silver":
            display_cols = base_cols + ["pocket_money"]
        elif stage == "Platinum":
            display_cols = base_cols + platinum_cols + ["pocket_money"]
        else: # Gold
            display_cols = base_cols + platinum_cols + gold_cols + ["pocket_money"]
        
        # Ensure all required columns for display exist in the DataFrame
        df_clean = pd.DataFrame({col: df.get(col) for col in display_cols})
        
        # Custom renaming for the display (optional but nice)
        display_names = {
            "work_done": "Work $\checkmark$", "distraction": "Distraction X", 
            "pushups": "Pushups", "water_liters": "Water (L)", 
            "sugar_avoided": "No Sugar $\checkmark$", "woke_4am": "Wake 4AM $\checkmark$", 
            "slept_9pm": "Sleep 9PM $\checkmark$", "pocket_money": "Savings (PKR)",
            "result": "Day Result"
        }
        df_clean = df_clean.rename(columns=display_names)
        
        st.dataframe(df_clean.reset_index(drop=True), hide_index=True)


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
        st.sidebar.write(f"Savings: {p.get('savings',0.0)} PKR")
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
        st.markdown("<h1 style='color:white;'>🧠 The Brain — 105 Days Life Change</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#eaf6ff;'>Login / Register to start. Flow: **Prediction → Offer → Rules → Profile → Daily Routine.**</p>", unsafe_allow_html=True)
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
