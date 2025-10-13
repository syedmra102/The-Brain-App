def performance_test_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
    
    # ONLY HEADINGS CENTERED - NO COLUMNS
    st.markdown("<h1 style='text-align: center;'>Performance Predictor</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Discover Your Top Percentile</h3>", unsafe_allow_html=True)
    
    # User progress slider (NOT centered) - NO DASHBOARD BUTTON
    user = st.session_state.user
    st.write(f"User: {user['username']}")
    
    # Initialize session state for results
    if 'prediction_results' not in st.session_state:
        st.session_state.prediction_results = None
    
    # FORM STARTS HERE
    with st.form("performance_form"):
        st.subheader("Your Daily Habits")
        
        hours = st.slider("Daily Study Hours", 0.5, 12.0, 5.0, 0.5)
        distraction_count = st.slider("Daily Distractions", 0, 15, 5)
        
        st.subheader("Lifestyle Habits")
        avoid_sugar = st.selectbox("Avoid Sugar", ["Yes", "No"])
        avoid_junk_food = st.selectbox("Avoid Junk Food", ["Yes", "No"])
        drink_5L_water = st.selectbox("Drink 5L Water Daily", ["Yes", "No"])
        sleep_early = st.selectbox("Sleep Before 11 PM", ["Yes", "No"])
        exercise_daily = st.selectbox("Exercise Daily", ["Yes", "No"])
        wakeup_early = st.selectbox("Wake Up Before 7 AM", ["Yes", "No"])
        
        predict_btn = st.form_submit_button("Predict My Performance")
        
        if predict_btn:
            with st.spinner("Analyzing your performance..."):
                time.sleep(1)
                
                habits = {}
                for col in model_data['categorical_columns']:
                    value = locals()[col]
                    habits[col] = model_data['encoders'][col].transform([value])[0]
                
                percentile = predict_performance(hours, distraction_count, habits)
                feature_percentiles = calculate_feature_percentiles(hours, distraction_count, habits)
                
                st.session_state.prediction_results = {
                    'percentile': percentile,
                    'feature_percentiles': feature_percentiles
                }
    
    # FORM ENDS HERE - EVERYTHING BELOW IS OUTSIDE THE FORM
    
    # Show results ONLY if prediction was made
    if st.session_state.prediction_results is not None:
        results = st.session_state.prediction_results
        percentile = results['percentile']
        feature_percentiles = results['feature_percentiles']
        
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; color: #7C3AED;'>Your Performance: Top {percentile:.1f}%</h2>", unsafe_allow_html=True)
        
        # DARK BLUE CHART
        fig, ax = plt.subplots(figsize=(12, 6))
        features = list(feature_percentiles.keys())
        percentiles = list(feature_percentiles.values())
        
        # DARK BLUE color (#1E3A8A)
        bars = ax.bar(features, percentiles, color='#1E3A8A', edgecolor='#1E40AF', linewidth=1.5)
        ax.set_ylabel('Performance Percentile', fontweight='bold')
        ax.set_title('Performance Breakdown Analysis', fontweight='bold', fontsize=14)
        ax.set_ylim(0, 100)
        plt.xticks(rotation=45, ha='right', fontweight='bold')
        
        # Add value labels
        for bar, percentile_val in zip(bars, percentiles):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'Top {percentile_val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        # Dark blue grid
        ax.grid(True, alpha=0.3, color='#1E40AF')
        ax.set_facecolor('#F8FAFC')
        
        st.pyplot(fig)
        
        # 105 Days Challenge - BUTTON OUTSIDE FORM
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>105 Days to Top 1% Challenge</h2>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
            <h3 style='text-align: center;'>Currently at Top {percentile:.1f}% → Goal: Top 1%</h3>
            <p style='text-align: center;'>Join our 105-day transformation program to become among the top performers worldwide!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # BUTTON OUTSIDE FORM - NO ERROR
        if st.button("I Want to Become Top 1%!"):
            st.session_state.challenge_accepted = True
            st.success("Welcome to the 105-Day Challenge! Your transformation journey starts now!")

    # Only back button - NO DASHBOARD BUTTON
    st.button("Back to Dashboard", on_click=lambda: st.session_state.update({"page":"dashboard"}))
