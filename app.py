# Ensure session_persisted exists
if 'session_persisted' not in st.session_state:
    st.session_state.session_persisted = False

# Get query params
query_params = st.experimental_get_query_params()

# FIX: Improved persistence check to prevent logout on refresh
if not st.session_state.session_persisted:
    try:
        # Check if user is already logged in or can be restored
        if st.session_state.logged_in and st.session_state.user and 'username' in st.session_state.user:
            # Ensure user is not on auth pages
            if st.session_state.page in ["signin", "signup", "forgot_password"]:
                st.session_state.page = "ml_dashboard"
                st.session_state.session_persisted = True
                st.rerun()
        else:
            # Attempt to restore session from query params or user data
            username = None
            if 'username' in query_params:
                username = query_params['username'][0]
            elif st.session_state.user and 'username' in st.session_state.user:
                username = st.session_state.user['username']

            if username:
                user_doc = db.collection('users').document(username).get()
                if user_doc.exists:
                    user_info = user_doc.to_dict()
                    st.session_state.user = {
                        "username": username,
                        "email": user_info.get("email", ""),
                        "role": user_info.get("role", "student")
                    }
                    # Restore user profile
                    profile_doc = db.collection('user_profiles').document(username).get()
                    if profile_doc.exists:
                        st.session_state.user_profile = profile_doc.to_dict()
                    else:
                        st.session_state.user_profile = {}
                    # Restore challenge data
                    st.session_state.challenge_data = load_challenge_data(username)
                    st.session_state.logged_in = True
                    st.session_state.page = "ml_dashboard"
                    st.session_state.session_persisted = True
                    # Ensure query params are set
                    st.experimental_set_query_params(username=username)
                    st.rerun()
                else:
                    # User not found in Firebase, reset to signin
                    st.session_state.user = None
                    st.session_state.logged_in = False
                    st.session_state.user_profile = {}
                    st.session_state.challenge_data = {}
                    st.session_state.page = "signin"
                    st.experimental_set_query_params()
                    st.session_state.session_persisted = True
                    st.rerun()
            else:
                # No user data, ensure on signin page
                st.session_state.user = None
                st.session_state.logged_in = False
                st.session_state.user_profile = {}
                st.session_state.challenge_data = {}
                st.session_state.page = "signin"
                st.experimental_set_query_params()
                st.session_state.session_persisted = True
                st.rerun()
    except Exception as e:
        # Handle any errors by resetting to signin
        st.session_state.user = None
        st.session_state.logged_in = False
        st.session_state.user_profile = {}
        st.session_state.challenge_data = {}
        st.session_state.page = "signin"
        st.experimental_set_query_params()
        st.session_state.session_persisted = True
        st.rerun()
else:
    # Session already persisted, verify user state
    if st.session_state.logged_in and st.session_state.user and 'username' in st.session_state.user:
        if st.session_state.page in ["signin", "signup", "forgot_password"]:
            st.session_state.page = "ml_dashboard"
            st.rerun()
    else:
        if st.session_state.page not in ["signin", "signup", "forgot_password"]:
            st.session_state.page = "signin"
            st.experimental_set_query_params()
            st.rerun()
