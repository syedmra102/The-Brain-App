import streamlit as st

# Page setup
st.set_page_config(page_title="Simple App", layout="centered")

# Session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = 'main'

# Main page
def main_page():
    st.title("Main Dashboard")
    
    # Two columns for buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = 'analytics'
            
    with col2:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.page = 'settings'

# Analytics page  
def analytics_page():
    st.title("Analytics Page")
    
    if st.button("← Back to Main"):
        st.session_state.page = 'main'

# Settings page
def settings_page():
    st.title("Settings Page")
    
    if st.button("← Back to Main"):
        st.session_state.page = 'main'

# Run the app
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'analytics':
    analytics_page()
elif st.session_state.page == 'settings':
    settings_page()
