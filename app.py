# ==========================================
# TAB 3: THE RESONANCE CHAMBER (Harmonic Pairs)
# ==========================================
with tab3:
    st.header("🔊 The Resonance Chamber")
    st.caption("Decipher the 'Speaker Analogy': Predict which pair lands next based on the last pair.")

    # 1. Select the Trigger Pair from the Last Draw
    # (User looks at the latest results and picks two numbers that drew together)
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        trigger_1 = st.number_input("Trigger Number A (e.g. 5)", min_value=1, max_value=49, value=5)
    with col_r2:
        trigger_2 = st.number_input("Trigger Number B (e.g. 17)", min_value=1, max_value=49, value=17)

    st.divider()

    if st.button("🔉 Pulse the Speaker (Scan History)"):
        # Logic: Find every time A and B drew together
        # Then see what 'A' drew with NEXT, and how long it took (The Height)
        
        # Flatten data for search
        # (Assuming 'df' is loaded from the Merger or Scanner tab)
        # We need the df here. If not loaded, warn user.
        if 'df' not in locals():
            st.error("Please upload your Master File in the Scanner Tab first!")
        else:
            matches = []
            cols_check = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
            
            # 1. Find the Triggers
            for i in range(len(df) - 1): # Stop 1 before end to look forward
                row = df.iloc[i]
                vals = row[cols_check].values
                
                if trigger_1 in vals and trigger_2 in vals:
                    # FOUND A TRIGGER PAIR
                    # Now look forward to find the NEXT time 'Trigger 1' dropped
                    
                    found_next = False
                    for j in range(i + 1, len(df)):
                        next_row = df.iloc[j]
                        next_vals = next_row[cols_check].values
                        
                        if trigger_1 in next_vals:
                            # It hit the speaker again!
                            # Calculate Height (Gap)
                            height = j - i
                            
                            # Who was the NEW partner? (The Harmonic)
                            # Find neighbor numbers in that row
                            partners = [x for x in next_vals if x != trigger_1 and x > 0]
                            
                            matches.append({
                                "Date_Trigger": row['Date'],
                                "Height (Draws)": height,
                                "Next_Partner_List": partners
                            })
                            found_next = True
                            break
                    
                    if not found_next:
                        matches.append({
                             "Date_Trigger": row['Date'],
                             "Height (Draws)": "Still Bouncing...",
                             "Next_Partner_List": []
                        })

            # 2. Analyze the Resonance
            if len(matches) > 0:
                st.write(f"Found {len(matches)} historical resonances for Pair {trigger_1}-{trigger_2}.")
                
                # Show details
                total_height = 0
                count = 0
                partner_frequency = {}
                
                for m in matches:
                    h = m['Height (Draws)']
                    if isinstance(h, int):
                        total_height += h
                        count += 1
                        
                        # Count partners
                        for p in m['Next_Partner_List']:
                            partner_frequency[p] = partner_frequency.get(p, 0) + 1

                if count > 0:
                    avg_height = total_height / count
                    
                    # Sort partners by frequency
                    sorted_partners = sorted(partner_frequency.items(), key=lambda x: x[1], reverse=True)
                    best_partner = sorted_partners[0][0] if sorted_partners else "None"
                    
                    st.subheader("📊 The Acoustic Report")
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Average Bounce Height", f"{avg_height:.1f} Draws", help="This is your DATE prediction.")
                    c2.metric("Strongest Harmonic Echo", f"{best_partner}", help="This is the number most likely to pair with A next.")
                    
                    st.info(f"**Prediction:** Number {trigger_1} will return in approx **{round(avg_height)} draws**, likely paired with **{best_partner}**.")
                    
                    # Visualization of the Wave
                    st.write("🌊 **Resonance Log:**")
                    st.dataframe(pd.DataFrame(matches))
                    
                else:
                    st.warning("This pair has appeared, but Number A hasn't landed again yet. It is currently mid-air.")
            else:
                st.error("This pair has never appeared together in your history file.")
