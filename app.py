    # ... (Keep previous file loading code) ...

    if len(hits) >= 3:
        idx_last = hits[-1]
        idx_prev = hits[-2]
        idx_old = hits[-3]
        
        # Calculate Gaps
        gap_new = idx_last - idx_prev
        gap_old = idx_prev - idx_old
        
        # Get Dates
        last_date = df.iloc[idx_last]['Date']
        last_draw_name = df.iloc[idx_last]['Draw_Name']
        
        # Physics Ratio
        if gap_old > 0:
            ratio = gap_new / gap_old
            
            st.write(f"**Last Hit:** {last_date.strftime('%d %b')} ({last_draw_name})")
            st.write(f"**Sequence:** Gap {gap_old} ➔ Gap {gap_new}")
            st.metric("Physics Ratio", f"{ratio:.2f}")
            
            # --- CALCULATE PREDICTION ---
            # Standard Decay Prediction
            next_gap_float = gap_new * ratio
            
            # --- LOGIC ADJUSTMENTS ---
            
            # 1. THE HOT ZONE (Widened to 1.1)
            # Catches numbers that are maintaining speed or slightly accelerating
            if ratio <= 1.1:
                pred_date, pred_time = get_future_draw(last_date, last_draw_name, next_gap_float)
                
                if ratio < 0.8:
                    status = "🚀 ACCELERATING (Hot)"
                    color = "red"
                else:
                    status = "⚠️ STABLE / ROLLING (Watch List)"
                    color = "orange"
                    
                st.markdown(f":{color}[**{status}**]")
                st.write(f"Predicted Gap: {round(next_gap_float, 1)} draws")
                st.success(f"**Target:** {pred_date} ({pred_time})")
                
            # 2. THE SLEEPER WAKE-UP (Ratio > 4.0)
            # Catches your 'Ratio 9' anomaly. 
            # Theory: If it slept for 9x longer, it owes us a 'Correction Bounce'.
            elif ratio > 4.0:
                st.markdown(":blue[**💤 SLEEPER WAKE-UP (Anomaly)**]")
                st.info("This number just woke up from a long sleep.")
                st.warning("**Strategy:** Sleepers often 'Double Tap' (repeat quickly) to regain average. Play for a repeat in 1-3 draws.")
                
            # 3. THE COLD ZONE (1.1 to 4.0)
            else:
                st.write("🔵 Decelerating (Going Cold). No immediate signal.")

        else:
            st.warning("Cannot calculate ratio (Previous gap was 0).")
