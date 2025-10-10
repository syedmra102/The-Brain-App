# app.py
"""
Brain App — Premium Ice-Blue Multi-Page Streamlit Site
Single-file Streamlit app (Home | Dashboard | Motivation | About | Contact)
Background: aesthetic snow mountain (sharp, non-blurred from Unsplash)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import random
import base64
from datetime import datetime

st.set_page_config(page_title="The Brain App", layout="wide", page_icon="🧠")

# ---------------------------
# Asset URLs (Unsplash - high quality snow mountain)
# ---------------------------
BG_IMAGE = "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1950&q=80"  # sharp aesthetic snow mountain
LOGO = "https://cdn-icons-png.flaticon.com/512/10307/10307982.png"

# ---------------------------
# CSS: ice-blue glass + shine overlay + responsive tweaks
# ---------------------------
def inject_css():
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    :root {{
      --ice-1: #e9f7ff;
      --ice-2: #d4f1ff;
      --accent: #0aa7ff;
      --deep: #012033;
      --card: rgba(255,255,255,0.86);
      --card-border: rgba(10,167,255,0.12);
      --shadow: 0 10px 30px rgba(6,40,70,0.12);
    }}

    /* full background (sharp) */
    .stApp {{
      background-image: url("{BG_IMAGE}");
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
      font-family: 'Poppins', sans-serif;
      color: var(--deep);
      min-height: 100vh;
    }}

    /* moving gentle light shimmer layer (keeps background sharp) */
    .shine {{
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background:
        linear-gradient(110deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 20%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0.01) 80%, rgba(255,255,255,0.04) 100%);
      mix-blend-mode: screen;
      animation: shimmer 14s linear infinite;
      opacity: 0.95;
    }}
    @keyframes shimmer {{
      0% {{ transform: translateX(-12%); }}
      50% {{ transform: translateX(12%); }}
      100% {{ transform: translateX(-12%); }}
    }}

    /* ensure app content above overlays */
    .app-wrap {{
      position: relative;
      z-index: 1;
      padding: 22px 26px;
    }}

    /* Sidebar design (crisp white with subtle blue border) */
    section[data-testid="stSidebar"] {{
      background: rgba(255,255,255,0.93) !important;
      border-right: 1px solid rgba(10,167,255,0.08);
      box-shadow: 0 8px 30px rgba(6,40,70,0.06);
    }}
    section[data-testid="stSidebar"] .css-1d391kg {{
      padding-top: 14px;
    }}
    section[data-testid="stSidebar"] * {{ color: var(--deep) !important; }}

    /* glass card */
    .glass {{
      background: var(--card);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 18px;
      border: 1px solid var(--card-border);
      box-shadow: var(--shadow);
    }}
    .glass h2, .glass h3 {{
      margin: 4px 0 12px 0 !important;
      color: var(--deep) !important;
    }}
    .glass p, .glass li {{
      color: var(--deep) !important;
    }}

    /* title accent */
    .title-accent {{
      display:inline-block;
      padding:8px 16px;
      border-radius:12px;
      background: linear-gradient(90deg, rgba(10,167,255,0.12), rgba(0,160,255,0.06));
      box-shadow: 0 8px 30px rgba(10,167,255,0.06);
    }}

    /* Buttons: ice-blue glow */
    div.stButton > button, .stButton button {{
      background: linear-gradient(135deg, #007BFF, #00C6FF) !important;
      color: white !important;
      padding: 10px 18px !important;
      border-radius: 12px !important;
      border: none !important;
      font-weight: 600 !important;
      box-shadow: 0 10px 30px rgba(10,167,255,0.16) !important;
    }}
    div.stButton > button:hover, .stButton button:hover {{
      transform: translateY(-3px);
      box-shadow: 0 16px 50px rgba(10,167,255,0.22) !important;
    }}

    /* Inputs clean white */
    .stTextInput>div>div>input, .stNumberInput input, .stSelectbox>div>div>div {{
      background: #fff !important;
      color: #042235 !important;
      border-radius: 10px !important;
      border: 1px solid rgba(1,32,51,0.06) !important;
      padding: 10px !important;
    }}

    /* responsive tweaks */
    @media (max-width: 760px) {{
      .app-wrap {{ padding: 12px 12px; }}
      .glass {{ padding: 14px; border-radius: 10px; }}
      .stButton>button {{ width: 100% !important; }}
    }}

    /* hide default footer */
    footer {{ visibility: hidden; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    # shimmer overlay div
    st.markdown('<div class="shine"></div>', unsafe_allow_html=True)

inject_css()

# ---------------------------
# Small site utilities (fake auth for demo)
# ---------------------------
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None
    if "progress" not in st.session_state:
        # progress example: days completed out of 105
        st.session_state.progress = {"days_done": 12, "current_stage": "Silver", "streak": 8}
    if "quotes_seen" not in st.session_state:
        st.session_state.quotes_seen = []

init_session()

# ---------------------------
# Sidebar (multi-page nav)
# ---------------------------
with st.sidebar:
    st.image(LOGO, width=88)
    st.markdown("<h2 style='margin:6px 0 0 0;'>🧠 Brain App</h2>", unsafe_allow_html=True)
    st.markdown("<small>Ice-blue • Premium • Focus</small>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigate", ("Home", "Dashboard", "Motivation", "About", "Contact"))
    st.markdown("---")
    if st.session_state.logged_in:
        st.write(f"Signed in as: **{st.session_state.user}**")
        if st.button("Sign out"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()
    else:
        # mini login form
        st.markdown("### Demo Sign In")
        u = st.text_input("Username", key="s_user")
        p = st.text_input("Password", type="password", key="s_pass")
        if st.button("Sign in (demo)"):
            if u.strip() == "":
                st.error("Enter a username to sign in (demo).")
            else:
                st.session_state.logged_in = True
                st.session_state.user = u.strip()
                st.success("Signed in (demo).")
                st.experimental_rerun()
        st.markdown("---")
        st.write("Or continue as guest")

# ---------------------------
# Helper: progress chart sample
# ---------------------------
def gen_progress_df(days_done=12, total=105):
    days = list(range(1, total+1))
    status = ["Done" if d <= days_done else "Pending" for d in days]
    df = pd.DataFrame({"day": days, "status": status, "value": [1 if s=="Done" else 0 for s in status]})
    df["cumulative"] = df["value"].cumsum()
    return df

# ---------------------------
# Page: Home
# ---------------------------
if page == "Home":
    st.markdown('<div class="app-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex;gap:20px;align-items:center;">', unsafe_allow_html=True)
    st.markdown(f'<div style="flex:1;"><h1 style="margin:0;"> <span class="title-accent">Change your life in 105 days</span></h1><p style="margin-top:12px; font-size:18px;">Build discipline, health & deep skills — one daily mission at a time. The Brain App helps students & teachers focus and grow.</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="width:220px;text-align:center;"><img src="{LOGO}" width="160"/><p style="font-size:13px;margin:6px 0 0 0;color:#034;opacity:.8;">Demo • AI-ready</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # three feature columns
    st.markdown('<div style="display:flex;gap:18px;margin-top:20px;flex-wrap:wrap;">', unsafe_allow_html=True)
    st.markdown('<div style="flex:1;min-width:220px;" class="glass"><h3>Focus-First</h3><p>Distraction-free routines and daily check-ins.</p></div>', unsafe_allow_html=True)
    st.markdown('<div style="flex:1;min-width:220px;" class="glass"><h3>Teacher Hubs</h3><p>Teachers publish short daily statuses & students preview teaching style.</p></div>', unsafe_allow_html=True)
    st.markdown('<div style="flex:1;min-width:220px;" class="glass"><h3>AI Insights</h3><p>Personalized nudges, progress analytics, and motivational prompts.</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # CTA
    st.markdown('<div style="margin-top:18px;">', unsafe_allow_html=True)
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown('<p style="font-size:15px;margin:6px 0 8px 0;color:#012;">Ready to start? Sign in on the left or continue as guest.</p>', unsafe_allow_html=True)
    with col2:
        if st.button("Start 105-Day Challenge"):
            st.session_state.progress["days_done"] = 0
            st.session_state.progress["streak"] = 0
            st.success("Your 105-Day challenge has been reset (demo). Good luck!")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Page: Dashboard
# ---------------------------
elif page == "Dashboard":
    st.markdown('<div class="app-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown(f"<h2>📊 Dashboard</h2>", unsafe_allow_html=True)

    # simple KPIs
    days_done = st.session_state.progress.get("days_done", 12)
    streak = st.session_state.progress.get("streak", 8)
    col1, col2, col3 = st.columns(3)
    col1.metric("Days Completed", f"{days_done}/105")
    col2.metric("Current Stage", st.session_state.progress.get("current_stage","Silver"))
    col3.metric("Streak (days)", f"{streak}")

    # progress timeline chart
    df = gen_progress_df(days_done, 105)
    fig = px.area(df, x="day", y="cumulative", labels={"cumulative":"Days Done"}, title="Cumulative Progress Over 105 Days")
    fig.update_layout(margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0)")
    st.plotly_chart(fig, use_container_width=True)

    # daily check form
    st.markdown('<div style="margin-top:18px;">', unsafe_allow_html=True)
    st.markdown("<h3>Today's Check</h3>", unsafe_allow_html=True)
    colA, colB = st.columns([2,1])
    with colA:
        worked = st.checkbox("I worked focused in my field for required hours")
        exercised = st.checkbox("I exercised today (30+ min)")
        water = st.checkbox("I drank 5L water")
    with colB:
        pocket = st.number_input("Pocket savings today (PKR)", min_value=0.0, value=0.0, step=10.0)
        if st.button("Submit Today's Check"):
            if worked:
                st.session_state.progress["days_done"] += 1
                st.session_state.progress["streak"] += 1
                st.success("Nice — day counted. Keep the streak!")
            else:
                st.warning("Day not counted: complete the main task to keep streak.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Page: Motivation
# ---------------------------
elif page == "Motivation":
    st.markdown('<div class="app-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2>💬 Daily Motivation</h2>", unsafe_allow_html=True)

    quotes = [
        "Discipline beats motivation.",
        "Small steps every day — big results.",
        "You are the sum of your habits.",
        "Focus > Time. Make the hours matter.",
        "Consistency compounds like interest.",
        "Reset, refocus, repeat."
    ]
    q = random.choice([qq for qq in quotes if qq not in st.session_state.quotes_seen] or quotes)
    st.session_state.quotes_seen.append(q)
    st.markdown(f'<div style="font-size:20px;padding:12px 16px;border-radius:10px;background:linear-gradient(90deg, rgba(10,167,255,0.06), rgba(0,198,255,0.03));">{q}</div>', unsafe_allow_html=True)
    st.markdown("<br>")

    # make a wallpaper (quote on beautiful card) for users to download
    if st.button("Create Quote Wallpaper (Download)"):
        # simple SVG generation for a crisp wallpaper
        svg = f'''
        <svg width="1200" height="675" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="g" x1="0" x2="1">
              <stop offset="0%" stop-color="#eaf7ff"/>
              <stop offset="100%" stop-color="#d4f1ff"/>
            </linearGradient>
          </defs>
          <rect width="100%" height="100%" fill="url(#g)"/>
          <image href="{BG_IMAGE}" x="0" y="0" width="1200" height="675" opacity="0.35" preserveAspectRatio="xMidYMid slice"/>
          <rect x="60" y="430" width="1080" height="180" rx="14" fill="rgba(255,255,255,0.9)"/>
          <text x="120" y="520" font-family="Poppins" font-size="36" fill="#01233a">{q}</text>
          <text x="120" y="565" font-family="Poppins" font-size="18" fill="#02314a">— The Brain App</text>
        </svg>
        '''
        b64 = base64.b64encode(svg.encode()).decode()
        href = f'data:image/svg+xml;base64,{b64}'
        st.markdown(f'<a href="{href}" download="brain-quote.svg"><button class="css-1q8dd3e edgvbvh3">Download Wallpaper</button></a>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Page: About & Contact
# ---------------------------
elif page == "About":
    st.markdown('<div class="app-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2>About The Brain App</h2>", unsafe_allow_html=True)
    st.markdown("""
      <p>The Brain App is focused on building discipline, reducing distractions, and growing deep, hands-on skills via daily missions and teacher-led content.</p>
      <ul>
        <li>105-Day structured challenge (Silver/Platinum/Gold)</li>
        <li>Teacher tuition centers & preview statuses</li>
        <li>AI-driven nudges and progress analytics</li>
      </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Contact":
    st.markdown('<div class="app-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2>Contact</h2>", unsafe_allow_html=True)
    name = st.text_input("Your name", key="c_name")
    email = st.text_input("Your email", key="c_email")
    msg = st.text_area("Message", key="c_msg")
    if st.button("Send Message"):
        if name.strip() and email.strip() and msg.strip():
            st.success("Message sent — we'll get back to you (demo).")
        else:
            st.error("Please fill all fields.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# small footer
st.markdown('<div style="text-align:center;padding:10px 0;color:rgba(1,32,51,0.7);">Built with ❤️ — The Brain App • Demo</div>', unsafe_allow_html=True)
