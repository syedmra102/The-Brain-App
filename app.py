# app.py
# The Brain That Helps You Use Your Brain - Streamlit Cloud version (single-file)
# - Local JSON storage (data.json)
# - Simple ML recommendation (cosine similarity on dummy features)
# - 105-day challenge flows: Easy (Silver), Medium (Platinum), Hard (Gold)
# Styling: blue background, white text, green buttons

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer

DATA_FILE = "data.json"

# ---------- Utilities for local storage ----------
def load_datafile():
    if not os.path.exists(DATA_FILE):
        empty = {"users": {}, "logs": []}
        with open(DATA_FILE, "w") as f:
            json.dump(empty, f)
        return empty
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_datafile(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)

data_store = load_datafile()

def create_user(username, password):
    if username in data_store["users"]:
        return False, "Username already exists."
    data_store["users"][username] = {
        "password": password,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile": {
            "field": "",
            "interests": [],
            "hours_per_day": 0.0,
            "stage": "Silver",
            "streak_days": 0,
            "savings": 0.0,
            "joined_challenge": False,
            "started_on": None
        },
        "badges": []
    }
    save_datafile(data_store)
    return True, "User created."

def check_user(username, password):
    u = data_store["users"].get(username)
    if not u:
        return False
    return u["password"] == password

def update_profile(username, profile_updates):
    user = data_store["users"].get(username)
    if not user:
        return False
    user["profile"].update(profile_updates)
    save_datafile(data_store)
    return True

def add_log(username, log):
    entry = {"user": username, "date": datetime.now().strftime("%Y-%m-%d"), **log}
    data_store["logs"].append(entry)
    # update streaks and savings
    user = data_store["users"].get(username)
    if user:
        profile = user["profile"]
        # simple all conditions met check
        stage = profile.get("stage", "Silver")
        if stage == "Silver":
            required_hours = 2
        elif stage == "Platinum":
            required_hours = 4
        else:
            required_hours = 6

        all_ok = log.get("work_done_hours", 0) >= required_hours and log.get("distractions_avoided", False)
        if stage in ("Platinum", "Gold"):
            # additional conditions
            if stage == "Platinum":
                all_ok = all_ok and (log.get("pushups", 0) >= 30) and (log.get("water_liters", 0) >= 5)
            if stage == "Gold":
                all_ok = all_ok and (log.get("pushups", 0) >= 50) and (log.get("water_liters", 0) >= 5) and log.get("sugar_avoided", False)
        if all_ok:
            profile["streak_days"] = profile.get("streak_days", 0) + 1
        else:
            # add the pocket money to savings if fail
            profile["savings"] = round(profile.get("savings", 0.0) + float(log.get("pocket_money", 0.0)), 2)
            profile["streak_days"] = 0
    save_datafile(data_store)

# ---------- Simple ML Recommendation ----------
# Dummy fields and associated tags/features
FIELDS = [
    {"field": "Programming", "tags": ["programming", "python", "web", "ai", "ml"]},
    {"field": "Sports", "tags": ["sports", "fitness", "cricket", "football", "exercise"]},
    {"field": "Music", "tags": ["music", "singing", "guitar", "composition"]},
    {"field": "Business", "tags": ["business", "sales", "startup", "finance", "investment"]},
    {"field": "Art", "tags": ["art", "design", "drawing", "painting", "creativity"]},
    {"field": "Science", "tags": ["science", "research", "biology", "physics", "chemistry"]},
    {"field": "Health", "tags": ["health", "nutrition", "diet", "wellness", "fitness"]},
]

all_tags = sorted({t for f in FIELDS for t in f["tags"]})
mlb = MultiLabelBinarizer(classes=all_tags)
field_matrix = mlb.fit_transform([f["tags"] for f in FIELDS])

def recommend_field(interests):
    # interests is a list like ['Programming', 'Music']
    # map interests to tags and compute cosine similarity
    # convert interests into tags: use same keywords if matching field names
    interest_tags = []
    for i in interests:
        lower = i.lower()
        for t in all_tags:
            if lower in t:
                interest_tags.append(t)
    # if no precise match, use interests names as tags fallback
    if not interest_tags:
        for i in interests:
            if i.lower() in ["sports", "programming", "music", "business", "art", "science", "health"]:
                # map to a canonical tag
                interest_tags.append(i.lower())
    if not interest_tags:
        # default
        return "Programming"
    vector = mlb.transform([interest_tags])[0].reshape(1, -1)
    sims = cosine_similarity(vector, field_matrix)[0]
    idx = int(np.argmax(sims))
    return FIELDS[idx]["field"]

# ---------- Styling ----------
def set_styles():
    st.markdown(
        """
        <style>
        /* Page background */
        .stApp {
            background: linear-gradient(180deg, #0b57a4, #0b69c3);
            color: white;
        }
        /* White text for most components */
        .big-title { color: white; font-weight:700; }
        .subtitle { color: #eaf6ff; }
        /* Green buttons */
        div.stButton > button, .stButton button {
            background-color: #1db954;
            color: white;
            border: none;
        }
        /* Form inputs style tweaks */
        .stTextInput>div>div>input { background-color: rgba(255,255,255,0.06); color: white; }
        .stSelectbox>div>div>div { background-color: rgba(255,255,255,0.04); color: white; }
        textarea, .stTextArea>div>div>textarea { background-color: rgba(255,255,255,0.04); color: white; }
        .stSlider>div>div>div>input { color: white; }
        .streamlit-expanderHeader { color: white; }
        /* Cards */
        .card {
            background: rgba(255,255,255,0.03);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 0.7rem;
        }
        .small-muted { color: #d7eefc; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------- Pages / Flows ----------
def show_landing():
    st.markdown('<h1 class="big-title">🧠 The Brain - 105 Days Life Change Challenge</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Do you want to change your life in 105 days? Free. Choose your field, choose your level, and start a real transformation.</p>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="card"><b>What you will get after 105 days:</b><ul><li>Healthy habits: no sugar, 5L water, good sleep</li><li>Wake up at 4 AM & exercise</li><li>Deep hands-on knowledge in your field</li><li>A wealthy & focused mindset with unstoppable discipline</li></ul></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("**How it works:** Choose a level (Easy / Medium / Hard). Follow daily tasks, fill a 30-second form each night, build streaks, and earn motivational wallpapers & badges.")
    st.write("")

def show_rules_and_stages():
    st.header("Stages & Rules")
    st.markdown("""
    **Stages**:
    - **Easy (Silver)** — 15 days: 2 hours/day work, avoid distractions, daily form.
    - **Medium (Platinum)** — 30 days: 4 hours/day, 5L water, 30 pushups, daily form.
    - **Hard (Gold)** — 60 days: 6 hours/day, wake 4AM, sleep 9PM, 5L water, 50 pushups, no sugar.
    """)
    st.markdown("**Rules**: Fill daily form each night. Fail to do tasks → put pocket money in your saving box. Complete tasks → get motivational wallpaper & quote. Take screenshot, set as wallpaper, and keep going!")

def show_stage_details():
    st.subheader("Stage Details")
    st.markdown("""
    **Easy (Silver)**:
    - Work 2 hours/day
    - Avoid distractions
    - Fill form daily (before sleeping)
    
    **Medium (Platinum)**:
    - Work 4 hours/day
    - Drink 5L water and do 30 pushups
    - Avoid distractions
    - Fill form daily
    
    **Hard (Gold)**:
    - Wake at 4 AM, sleep at 9 PM
    - 1 hour exercise each morning
    - 6 hours/day work focused
    - 5L water, no sugar, 50 pushups
    - Positive mirror talk daily
    """)

def start_challenge_for_user(username):
    user = data_store["users"].get(username)
    if not user:
        return False
    if user["profile"].get("joined_challenge"):
        return False
    user["profile"]["joined_challenge"] = True
    user["profile"]["started_on"] = datetime.now().strftime("%Y-%m-%d")
    save_datafile(data_store)
    return True

def get_user_logs(username):
    logs = [l for l in data_store["logs"] if l["user"] == username]
    df = pd.DataFrame(logs) if logs else pd.DataFrame(columns=["date"])
    return df

def dashboard(username):
    st.header(f"Welcome back, {username}!")
    user = data_store["users"].get(username)
    profile = user["profile"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Stage", profile.get("stage","Silver"))
    col2.metric("Streak (days)", profile.get("streak_days",0))
    col3.metric("Savings (PKR)", profile.get("savings",0.0))
    st.write("")
    st.subheader("Your Roadmap")
    st.write(f"Field: **{profile.get('field','Not set')}** | Hours/day goal: **{profile.get('hours_per_day',0)}**")
    st.write("Progress Calendar:")
    df_logs = get_user_logs(username)
    if not df_logs.empty:
        df_logs['date'] = pd.to_datetime(df_logs['date'])
        st.dataframe(df_logs[['date','work_done_hours','distractions_avoided','pushups','water_liters','sugar_avoided']].sort_values('date', ascending=False).head(20))
    else:
        st.info("No logs yet — start filling the daily form!")

    st.subheader("Daily Check-In")
    with st.form("daily_form"):
        st.write("Tick what you did today (honesty is the only rule!)")
        distractions_avoided = st.checkbox("Avoided distractions (no scrolling)")
        if profile.get("stage","Silver") == "Silver":
            work_req = 2
        elif profile.get("stage","Silver") == "Platinum":
            work_req = 4
        else:
            work_req = 6
        work_done_hours = st.number_input(f"Worked hours today (goal: {work_req})", 0.0, 24.0, 0.0)
        pushups = st.number_input("Pushups today", 0, 500, 0)
        water_liters = st.number_input("Water consumed (liters)", 0.0, 10.0, 0.0)
        sugar_avoided = st.checkbox("Avoided sugar today")
        pocket_money = st.number_input("Pocket money to save if you fail (PKR)", 0.0, 10000.0, 0.0)
        review = st.text_area("Short review of your day")
        submitted = st.form_submit_button("Submit Day")

        if submitted:
            log = {
                "distractions_avoided": bool(distractions_avoided),
                "work_done_hours": float(work_done_hours),
                "pushups": int(pushups),
                "water_liters": float(water_liters),
                "sugar_avoided": bool(sugar_avoided),
                "pocket_money": float(pocket_money),
                "review": review
            }
            add_log(username, log)
            st.success("Day submitted! Keep the streak alive (or learn from mistakes).")
            # trophy message
            st.balloons()

# ---------- App Start ----------
def main():
    st.set_page_config(page_title="The Brain - 105 Days", layout="wide")
    set_styles()

    # Session state
    if "user" not in st.session_state:
        st.session_state.user = None

    # Top nav (simple)
    st.sidebar.title("Menu")
    if st.session_state.user:
        st.sidebar.write(f"Logged in as: **{st.session_state.user}**")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()
        if st.sidebar.button("Dashboard"):
            st.session_state.page = "dashboard"
    else:
        st.sidebar.write("Not logged in")
        if st.sidebar.button("Home"):
            st.session_state.page = "home"

    page = st.session_state.get("page", "home")

    # If not logged in: show login / register
    if not st.session_state.user:
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.subheader("Login or Register")
        with st.form("auth_form"):
            col1, col2 = st.columns([2,1])
            with col1:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
            with col2:
                login_btn = st.form_submit_button("Login")
                register_btn = st.form_submit_button("Register")
        if register_btn and username and password:
            ok, msg = create_user(username, password)
            if ok:
                st.success(msg + " Now login.")
            else:
                st.error(msg)
        if login_btn and username and password:
            ok = check_user(username, password)
            if ok:
                st.session_state.user = username
                st.success("Logged in!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials.")

    # After login
    if st.session_state.user:
        username = st.session_state.user
        user = data_store["users"].get(username)
        profile = user["profile"]
        # Profile edit
        st.sidebar.markdown("### Your Profile")
        with st.sidebar.form("profile_form"):
            chosen_field = st.text_input("Chosen Field", value=profile.get("field",""))
            interests = st.multiselect("Interests", ["Sports","Programming","Music","Art","Science","Business","Health"], default=profile.get("interests",[]))
            hours_per_day = st.slider("Daily Hours goal", 0.0, 12.0, float(profile.get("hours_per_day",0.0)))
            stage = st.selectbox("Stage", ["Silver","Platinum","Gold"], index=["Silver","Platinum","Gold"].index(profile.get("stage","Silver")))
            save_prof = st.form_submit_button("Save Profile")
            if save_prof:
                update_profile(username, {"field": chosen_field, "interests": interests, "hours_per_day": hours_per_day, "stage": stage})
                st.sidebar.success("Profile saved!")

        # Choose main page behavior
        if page == "home":
            show_landing()
            st.write("")
            # ML model recommend field
            st.subheader("Quick Recommendation (ML)")
            rec_col1, rec_col2 = st.columns([2,3])
            with rec_col1:
                picks = st.multiselect("Choose interests (for ML recommendation)", ["Sports","Programming","Music","Art","Science","Business","Health"])
                if st.button("Recommend field for me"):
                    rec = recommend_field(picks)
                    st.success(f"Recommended field: **{rec}**")
            with rec_col2:
                st.info("This small ML model uses simple keyword mapping to recommend a field based on your selected interests. It's lightweight for demo/prototype.")
            st.write("")
            st.markdown("---")
            st.header("Start the 105 Days Challenge")
            st.markdown("Do you want to change everything in your life (health, discipline, focus, skills)? It's free. Choose level and continue.")
            level = st.selectbox("Choose your level", ["Easy (Silver - 15 days)", "Medium (Platinum - 30 days)", "Hard (Gold - 60 days)"])
            if st.button("Next"):
                st.session_state.page = "stages"
                st.experimental_rerun()

        elif page == "stages":
            show_rules_and_stages()
            st.write("")
            show_stage_details()
            st.write("")
            if st.button("I Agree — Rewind my life and start the challenge"):
                # set user's chosen stage by reading last chosen in sidebar profile; default Silver
                user_profile = data_store["users"][username]["profile"]
                # map selection: choose stage from sidebar selection already saved; if not saved, infer from selected level on home
                chosen_stage = user_profile.get("stage", "Silver")
                # mark joined
                started = start_challenge_for_user(username)
                if started:
                    st.success("Challenge started! Open Dashboard and fill daily form every night.")
                else:
                    st.info("You already started. Go to Dashboard.")
            if st.button("Back"):
                st.session_state.page = "home"
                st.experimental_rerun()

        elif page == "dashboard":
            dashboard(username)

    else:
        # Public view for not logged-in users
        st.markdown('<h1 class="big-title">🧠 The Brain - 105 Days Life Change</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Login or register from the left to start your transformation.</p>', unsafe_allow_html=True)
        st.write("")
        st.info("This demo app uses local file storage (data.json). On Streamlit Cloud, data is persisted across sessions in the app files area unless the app is redeployed. For a production setup use Firebase or a proper database.")

if __name__ == "__main__":
    main()
