# app.py
import streamlit as st
import base64
from pathlib import Path
import time

# ---- Paths to your images in the environment (provided by you) ----
IMG1_PATH = "/mnt/data/my background.webp"  # first image
IMG2_PATH = "/mnt/data/myaa.jpg"            # second image

# ---- helper: encode local image to base64 for CSS embedding ----
def img_to_data_uri(path: str):
    p = Path(path)
    if not p.exists():
        return ""
    mime = "image/webp" if p.suffix.lower() == ".webp" else "image/jpeg"
    data = p.read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"

BG1_URI = img_to_data_uri(IMG1_PATH)
BG2_URI = img_to_data_uri(IMG2_PATH)

# ---- Inject CSS with placeholders for two backgrounds ----
def inject_css():
    # CSS contains two classes .bg-1 and .bg-2 which we swap via JS or class toggle.
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    :root {{
      --accent-1: #007BFF;
      --accent-2: #00C6FF;
      --ink: #00325a;
      --card-bg: rgba(255,255,255,0.85);
      --glass-border: rgba(176,224,255,0.6);
    }}

    html, body, [data-testid="stAppViewContainer"] {{
      height: 100%;
      margin: 0;
      font-family: 'Poppins', sans-serif;
    }}

    /* Container that holds the app background */
    .bg-root {{
      position: fixed;
      inset: 0;
      z-index: -1;
      transition: opacity 0.8s ease;
    }}

    .bg-1 {{
      background-image: url("{BG1_URI}");
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      width: 100%;
      height: 100%;
    }}
    .bg-2 {{
      background-image: url("{BG2_URI}");
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      width: 100%;
      height: 100%;
    }}

    /* Ensure sharp: do not blur or darken background */
    .bg-overlay {{
      position: absolute;
      inset: 0;
      pointer-events: none;
    }}

    /* Main app content sits above */
    .app-content {{
      position: relative;
      z-index: 1;
    }}

    /* Glass card (white-blue theme, crisp not blurred) */
    .glass {{
      background: var(--card-bg);
      border-radius: 18px;
      padding: 28px;
      margin-bottom: 22px;
      box-shadow: 0 8px 30px rgba(2,32,71,0.08);
      border: 1px solid var(--glass-border);
      color: var(--ink);
    }}

    h1, h2, h3 {{
      color: var(--ink) !important;
      margin: 6px 0 14px 0 !important;
    }}
    p, li, label, span {{
      color: var(--ink) !important;
    }}

    /* Sidebar custom */
    section[data-testid="stSidebar"] {{
      background: rgba(255,255,255,0.95) !important;
      border-right: 1px solid rgba(0,120,200,0.08);
    }}
    section[data-testid="stSidebar"] * {{
      color: var(--ink) !important;
    }}

    /* Buttons */
    div.stButton > button, .stButton button {{
      background: linear-gradient(135deg, var(--accent-1), var(--accent-2)) !important;
      color: white !important;
      border-radius: 12px !important;
      padding: 10px 18px !important;
      border: none !important;
      box-shadow: 0 6px 18px rgba(0,123,255,0.12) !important;
      font-weight: 600 !important;
    }}
    div.stButton > button:hover, .stButton button:hover {{
      transform: translateY(-3px);
    }}

    /* Inputs: white inputs with subtle blue border */
    .stTextInput>div>div>input, .stNumberInput input, .stSelectbox>div>div>div, textarea {{
      background: #ffffff !important;
      color: #001428 !important;
      border-radius: 10px !important;
      border: 1px solid rgba(0,120,200,0.12) !important;
      padding: 10px !important;
    }}

    /* Responsive: adjust sidebar and card padding on small screens */
    @media (max-width: 600px) {{
      .glass {{
        padding: 18px;
        border-radius: 14px;
      }}
      .stApp {{
        background-attachment: scroll;
      }}
      .stSidebar {{
        position: relative;
      }}
    }}
    </style>
    """

    # Add the container elements and CSS into the page
    st.markdown(css, unsafe_allow_html=True)

    # Add two divs for backgrounds. We will toggle their visibility via JS.
    # Initially show bg-1.
    bg_html = """
    <div id="bg-root" class="bg-root">
      <div id="bg1" class="bg-1" style="opacity:1;"></div>
      <div id="bg2" class="bg-2" style="opacity:0;"></div>
      <div class="bg-overlay"></div>
    </div>
    """
    st.markdown(bg_html, unsafe_allow_html=True)

# ---- JS snippet to toggle backgrounds and optionally auto-rotate ----
def inject_js():
    js = """
    <script>
    const setBackground = (n) => {
      const b1 = document.getElementById('bg1');
      const b2 = document.getElementById('bg2');
      if(!b1||!b2) return;
      if(n===1){ b1.style.opacity = 1; b2.style.opacity = 0; }
      else { b1.style.opacity = 0; b2.style.opacity = 1; }
    }

    // Listen for custom events from Streamlit
    window.addEventListener('message', event => {
      if(!event.data) return;
      const msg = event.data;
      if(msg.type === 'SET_BG'){
        setBackground(msg.value);
      }
      if(msg.type === 'AUTO_ROTATE'){
        // msg.value = {enabled: true/false, interval: seconds}
        if(msg.value.enabled){
          let cur = 1;
          window._brain_interval && clearInterval(window._brain_interval);
          window._brain_interval = setInterval(() => {
            cur = cur === 1 ? 2 : 1;
            setBackground(cur);
          }, msg.value.interval*1000);
        } else {
          window._brain_interval && clearInterval(window._brain_interval);
        }
      }
    }, false);
    </script>
    """
    st.components.v1.html(js, height=0, scrolling=False)

# ---- helper to send message to JS via Streamlit (postMessage hack) ----
def send_bg_message(n):
    # We cannot directly call postMessage easily; instead we create a tiny HTML that posts to window.
    html = f"""
    <script>
      window.postMessage({{type:'SET_BG', value:{n}}}, "*");
    </script>
    """
    st.components.v1.html(html, height=0)

def send_auto_rotate(enabled: bool, interval_sec: int = 8):
    html = f"""
    <script>
      window.postMessage({{type:'AUTO_ROTATE', value:{{enabled:{str(enabled).lower()}, interval:{interval_sec}}} }}, "*");
    </script>
    """
    st.components.v1.html(html, height=0)

# ---- App pages ----
def page_home():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h1>Welcome to The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<p>Sharp white-ice mountain backgrounds (no blur). Use the controls in the sidebar to switch backgrounds or enable auto-rotate.</p>", unsafe_allow_html=True)
    st.markdown("""
        <div style="display:flex; gap:20px; flex-wrap:wrap;">
          <div style="flex:1; min-width:260px;">
            <h3>Focus-first Design</h3>
            <p>Clean, crisp UI with white-blue cards that remain readable on top of a sharp photographic background.</p>
          </div>
          <div style="flex:1; min-width:260px;">
            <h3>Teacher-led Learning</h3>
            <p>Teachers create tuition centers, share daily statuses, and students join focused courses without distraction.</p>
          </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def page_predict():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2>🔮 Quick Prediction</h2>", unsafe_allow_html=True)
    name = st.text_input("Your name")
    hours = st.slider("Hours/day you study", 0, 24, 4)
    distractions = st.selectbox("Main distraction", ["None","Social media","YouTube","Gaming","Sleepiness"])
    if st.button("Estimate focus percentile"):
        # simplistic formula to give a feel
        base = 35
        score = base + hours*3 - (0 if distractions=="None" else 8)
        pct = max(1, min(99, int(score)))
        st.success(f"{name or 'User'}, estimated focus percentile: {pct}%")
    st.markdown('</div>', unsafe_allow_html=True)

def page_teachers():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2>👩‍🏫 Teachers</h2>", unsafe_allow_html=True)
    st.markdown("<p>Apply to become a teacher: create your tuition center, post daily teaching updates, and reach students worldwide.</p>", unsafe_allow_html=True)
    if st.button("Apply as Teacher"):
        st.info("Application received — we'll contact you by email (demo).")
    st.markdown('</div>', unsafe_allow_html=True)

def page_about():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2>About The Brain App</h2>", unsafe_allow_html=True)
    st.markdown("<p>A distraction-free learning hub with AI-ready features. Designed with white-ice mountain aesthetics — crisp, clear, and calm.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---- Main ----
def main():
    st.set_page_config(page_title="The Brain App - White Ice", layout="wide")
    inject_css()
    inject_js()  # JS that listens for postMessage

    # sidebar controls
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/10307/10307982.png", width=90)
        st.title("🧠 Brain App")
        st.write("White-ice mountain theme")
        st.markdown("---")
        st.markdown("**Background controls**")
        bg_choice = st.radio("Choose background:", ("Image 1 (my background.webp)", "Image 2 (myaa.jpg)"))
        auto = st.checkbox("Auto-rotate backgrounds every 8s", value=False)
        st.markdown("---")
        st.markdown("**Navigate**")
        page = st.radio("Page:", ("Home","Predict","Teachers","About"))

        st.markdown("---")
        st.markdown("Mobile-friendly: yes ✅")

    # apply background selection via postMessage
    # map bg_choice to 1 or 2
    selected = 1 if "Image 1" in bg_choice else 2
    send_bg_message(selected)
    send_auto_rotate(auto, 8)

    # page routing
    st.markdown('<div class="app-content">', unsafe_allow_html=True)
    if page == "Home":
        page_home()
    elif page == "Predict":
        page_predict()
    elif page == "Teachers":
        page_teachers()
    else:
        page_about()
    st.markdown('</div>', unsafe_allow_html=True)

    # small footer area
    st.markdown("<div style='padding:14px 0; color:#001428; text-align:center;'>Built with ❤️ — White Ice Mountain theme</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
