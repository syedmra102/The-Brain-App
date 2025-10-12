def daily_tracking_ui():
    user_data = st.session_state.user_db[st.session_state.username]
    profile = user_data['profile']
    challenge = user_data['challenge']
    
    # Get today's date key for logging
    today_key = date.today().strftime('%Y-%m-%d')

    if challenge['status'] != 'Active':
        st.error("Please start the challenge first in the Setup page.")
        if st.button("Go to Setup"):
            st.session_state.page = 'challenge_setup'
            st.rerun()
        return

    # Initialize today's log if it doesn't exist (e.g., first log today)
    if today_key not in challenge['daily_log']:
        challenge['daily_log'][today_key] = {'status': 'Pending', 'rules_completed': 0, 'penalty_paid': 0.0, 'rules_list': {}}

    # --- TOP METRICS (FIXED 4 COLUMNS) ---
    current_stage_data = CHALLENGE_STAGES[challenge['stage']]
    days_in_stage = current_stage_data['duration']
    
    # Calculate days completed *by counting saved entries in daily_log* for the current stage
    saved_days_in_stage = sum(1 for log_entry in challenge['daily_log'].values() if log_entry['status'] != 'Pending')
    days_left = days_in_stage - saved_days_in_stage
    
    # Calculate perfect streak (days without penalty)
    # NOTE: This calculates the streak within the current stage only.
    perfect_streak = 0
    # Iterate through logs in reverse chronological order
    for log_date_str in sorted(challenge['daily_log'].keys(), reverse=True):
        log_entry = challenge['daily_log'][log_date_str]
        if log_entry['status'] == 'Perfect':
            perfect_streak += 1
        elif log_entry['status'] != 'Pending':
            # Streak broken if status is "Saved with Penalty" or "Failed"
            break
            
    
    st.title("📅 Daily Challenge Tracker")
    st.markdown(f"Hello, **{st.session_state.username}**! You are becoming a **{profile['goal']}**.")

    # Four dedicated columns for key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Stage", challenge['stage'])
    col2.metric("Days Remaining", days_left)
    col3.metric("Perfect Day Streak", perfect_streak) # <-- This is your "Days Streak"
    col4.metric("Total Penalty Saving", f"PKR {challenge['penalty_amount']:,.2f}")
    
    st.markdown("---")
    # ... rest of the function remains the same ...
    
    # Check if today has already been logged/saved
    if challenge['daily_log'][today_key]['status'] != 'Pending':
        st.success(f"🎉 **Day Saved!** Status: {challenge['daily_log'][today_key]['status']} | Penalty Paid: PKR {challenge['daily_log'][today_key]['penalty_paid']:.2f}")
        
        # Display saved checklist state
        st.markdown("**Today's Compliance:**")
        for rule, status in challenge['daily_log'][today_key]['rules_list'].items():
            icon = "✅" if status else "❌"
            st.markdown(f"{icon} {rule}")
        
        # Display Last Task message if flagged
        if challenge.get('last_task_message', False):
             st.markdown("---")
             st.subheader("Your Last Task for the Day:")
             st.info("Go to Google, find a good motivational image/quote, and **set it as your phone wallpaper**. When you wake up, you will be reminded of your mission!")
             
        # Option to move to the next day's form 
        st.markdown("---")
        st.warning("To start tracking tomorrow, you must click 'Start Next Day' to reset the form.")
        if st.button("Start Next Day (Reset Form)"):
            challenge['last_task_message'] = False # Clear flag
            st.rerun() # This reloads the page with a clean form for the new date
        
        # Do not show the form if the day is already saved
        show_form = False
    else:
        show_form = True

    # --- DAILY CHECKLIST INPUT (Only shown if day is 'Pending') ---
    if show_form:
        rules = challenge['current_rules']
        checklist = {}
        
        # Display the checklist. Use the existing key/default to prevent warnings.
        for rule in rules:
            if rule != 'Fill the form daily': 
                checklist[rule] = st.checkbox(f"✅ {rule}", key=f"check_{rule}_{today_key}")
        
        st.subheader("Penalty and Pocket Money")
        penalty_input = st.number_input("If you failed any task, enter your daily pocket money/earning for the penalty (PKR):", min_value=0.0, value=0.0, key=f'penalty_input_{today_key}')

        if st.button("Save Daily Routine"):
            
            # 1. Check Compliance
            completed_tasks = sum(checklist.values())
            total_tasks = len(rules) - 1
            tasks_skipped = total_tasks - completed_tasks
            
            log_status = "Pending" 
            penalty_status = 0.0
            
            # 2. Enforcement Logic
            if tasks_skipped == 0:
                log_status = "Perfect"
                
            elif tasks_skipped > 0 and penalty_input > 0.0 and tasks_skipped <= 2:
                log_status = "Saved with Penalty"
                penalty_status = penalty_input
                
            else:
                # Day NOT Accepted 
                if tasks_skipped > 2:
                    st.error("❌ Day NOT Accepted! You skipped more than 2 tasks (only 2 skips allowed with penalty).")
                elif tasks_skipped > 0 and penalty_input == 0.0:
                    st.error("❌ Day NOT Accepted! You failed tasks and did not pay the penalty.")
                return 
                
            # 3. Save Data and Update Stats
            
            # Save compliance for today's log entry
            rule_list_status = {rule: checklist[rule] for rule in checklist.keys()}
            
            # Update the daily log with final status
            challenge['daily_log'][today_key].update({
                'status': log_status,
                'rules_completed': completed_tasks,
                'penalty_paid': penalty_status,
                'rules_list': rule_list_status
            })
            
            # Update challenge totals (only if accepted)
            user_data['challenge']['stage_days_completed'] = saved_days_in_stage + 1 
            user_data['challenge']['penalty_amount'] += penalty_status
            user_data['challenge']['streak_days_penalty'] = user_data['challenge'].get('streak_days_penalty', 0) + 1 if log_status == "Saved with Penalty" else 0
            user_data['challenge']['last_task_message'] = True 
            
            # Show success message and check for stage completion
            if log_status == "Perfect":
                st.success("🎉 Day Saved! 100% Compliant! No Penalty!")
            else:
                 st.warning(f"⚠️ Day Saved with Penalty. PKR {penalty_status:,.2f} added to saving.")

            check_stage_completion(user_data)
            
            # Rerun to show the saved state and the Last Task message
            time.sleep(1) 
            st.rerun()

    # --- HISTORICAL VIEW ---
    st.markdown("---")
    st.header("Stage Progress Log")
    
    log_data = []
    # Sort the log keys to display days in order
    sorted_log_keys = sorted(challenge['daily_log'].keys())
    
    for log_date_str in sorted_log_keys:
        log_entry = challenge['daily_log'][log_date_str]
        
        # Only show saved days (status != Pending)
        if log_entry['status'] != 'Pending': 
            
            if log_entry['status'] == 'Perfect':
                status_icon = "🟢 Perfect"
            elif log_entry['status'] == 'Saved with Penalty':
                status_icon = "🟡 Penalty"
            else:
                status_icon = "❌ Failed" 

            log_data.append({
                "Date": log_date_str,
                "Status": status_icon,
                "Rules Completed": log_entry['rules_completed'],
                "Penalty": f"PKR {log_entry['penalty_paid']:,.2f}"
            })

    if log_data:
        df_log = pd.DataFrame(log_data)
        
        # Display data grid for easy viewing
        st.dataframe(df_log, use_container_width=True, hide_index=True)
    else:
        st.info("No days have been logged yet for this stage.")
