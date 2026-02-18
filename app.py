# ==========================================
# PRECISION TRIGGER ENGINE
# ==========================================
if manual_list is not None:
    st.subheader("🎯 Precision Bonus Prediction")
    
    df_history = load_from_db()
    if df_history.empty:
        st.warning("Database is empty. Please upload historical data first.")
    else:
        # 1. SCAN FOR CO-OCCURRENCE
        # We look for rows where the main numbers match your input
        df_history["numbers_list"] = df_history["numbers"].str.split(",")
        
        # Calculate 'Buddy Score' for every bonus ball
        buddy_counts = pd.Series(0, index=range(1, MAX_NUMBER + 1))
        
        for idx, row in df_history.iterrows():
            draw_set = set(int(x) for x in row["numbers_list"] if x.strip().isdigit())
            input_set = set(manual_list)
            
            # How many of your 6 numbers are in this historical draw?
            matches = len(draw_set.intersection(input_set))
            
            if matches > 0:
                # Weight the bonus by how many numbers matched (High match = high influence)
                weight = matches / len(manual_set) 
                bonus_val = int(row["bonus"])
                if 1 <= bonus_val <= MAX_NUMBER:
                    buddy_counts[bonus_val] += weight

        # 2. INTEGRATE WITH HYBRID ENGINE
        # Get base scores (Frequency + Decay) from the main data
        base_scores, current_gaps = advanced_scores(bonus_series)
        
        # Normalize buddy counts to a 0-1 scale
        if buddy_counts.max() > 0:
            buddy_score_norm = buddy_counts / buddy_counts.max()
        else:
            buddy_score_norm = buddy_counts

        # FINAL FORMULA: 70% Buddy Correlation + 30% Statistical Pressure
        precision_score = (0.70 * buddy_score_norm) + (0.30 * base_scores)
        
        # 3. EXTRACT TOP 3
        top3 = precision_score.nlargest(3)
        total_top = top3.sum()
        top3_pct = (top3 / total_top) * 100 if total_top > 0 else pd.Series([33.3]*3)

        # --- VISUAL DISPLAY ---
        st.info(f"Trigger Active: Scanning for correlations with numbers {list(manual_list)}")
        
        p_cols = st.columns(3)
        for i, (num, pct) in enumerate(top3_pct.items()):
            with p_cols[i]:
                # Visual Feedback
                st.markdown(f"### Rank {i+1}: **#{num}**")
                st.write(f"Confidence: **{pct:.1f}%**")
                st.progress(int(pct))
                
                # Contextual info
                num_gap = int(current_gaps[num])
                st.caption(f"Pressure: {'🔥 High' if num_gap > 49 else '❄️ Low'} (Gap: {num_gap})")
