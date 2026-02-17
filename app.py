import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Sidian Bonus Lab", layout="wide")

# --- CORE SCORING ENGINE ---
def get_advanced_scores(series, n_range=49):
    freq = series.value_counts().reindex(range(1, n_range + 1), fill_value=0)
    freq_s = freq / freq.max() if freq.max() > 0 else freq
    
    last_idx = {i: -1 for i in range(1, n_range + 1)}
    for idx, val in enumerate(series):
        if 1 <= val <= n_range: last_idx[val] = idx
    
    gaps = pd.Series([len(series) - last_idx[i] for i in range(1, n_range + 1)], index=range(1, n_range + 1))
    rec_s = gaps / gaps.max()
    
    final = (0.50 * rec_s) + (0.50 * freq_s)
    # Cold filter
    final[gaps > 120] *= 0.5
    return final, gaps

st.title("🎯 Sidian Bonus Ball Predictor")

uploaded_file = st.file_uploader("Upload Draw History (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Required columns check
    required = ["Main_1", "Main_2", "Main_3", "Main_4", "Main_5", "Main_6", "Bonus"]
    if not all(col in df.columns for col in required):
        st.error(f"Your Excel must have these columns: {', '.join(required)}")
        st.stop()

    # --- SECTION: MANUAL DRAW INPUT ---
    st.divider()
    st.header("🔢 Step 1: Input Current Draw")
    st.write("Type the 6 main numbers from the draw to predict the Bonus:")
    
    input_cols = st.columns(6)
    draw_input = []
    for i in range(6):
        num = input_cols[i].number_input(f"No. {i+1}", min_value=1, max_value=49, value=i+1, key=f"in_{i}")
        draw_input.append(num)

    # --- CALCULATION LOGIC ---
    if st.button("Calculate 3 Most Likely Bonus Balls"):
        # 1. Statistical Score (History + Gaps)
        bonus_history = pd.to_numeric(df["Bonus"], errors="coerce").dropna().astype(int)
        base_scores, current_gaps = get_advanced_scores(bonus_history)
        
        # 2. Buddy/Trigger Score (Main Numbers Correlation)
        # We check how many times each bonus ball appeared alongside the numbers you just typed
        buddy_weights = pd.Series(0, index=range(1, 50))
        main_cols = ["Main_1", "Main_2", "Main_3", "Main_4", "Main_5", "Main_6"]
        
        for num in draw_input:
            # Find rows where this number was in the main set
            mask = df[main_cols].isin([num]).any(axis=1)
            correlated_bonuses = df[mask]["Bonus"].value_counts()
            buddy_weights = buddy_weights.add(correlated_bonuses, fill_value=0)
        
        buddy_score_norm = buddy_weights / buddy_weights.max() if buddy_weights.max() > 0 else buddy_weights
        
        # 3. Combine: 60% Buddy Correlation + 40% Base Statistics
        final_prediction_score = (0.60 * buddy_score_norm) + (0.40 * base_scores)
        
        # Get Top 3
        top_3 = final_prediction_score.nlargest(3)
        total_weight = top_3.sum()
        top_3_pct = (top_3 / total_weight) * 100

        # --- DISPLAY RESULTS ---
        st.subheader("🔥 Top 3 Predicted Bonus Numbers")
        res_cols = st.columns(3)
        for i, (num, prob) in enumerate(top_3_pct.items()):
            with res_cols[i]:
                st.metric(label=f"Possibility {i+1}", value=f"#{num}", delta=f"{prob:.1f}% Score")
                st.write(f"Confidence Level")
                st.progress(int(prob))
                st.caption(f"Gap: {int(current_gaps[num])} draws since last appearance")

    # --- VISUAL DECAY ---
    st.divider()
    _, current_gaps = get_advanced_scores(pd.to_numeric(df["Bonus"], errors="coerce").dropna())
    fig = px.bar(x=current_gaps.index, y=current_gaps.values, labels={'x':'Ball Number', 'y':'Draws Since Seen'}, title="Bonus Ball Decay (Wait Time)")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Upload your Excel file to begin. Ensure columns are named 'Main_1' through 'Main_6' and 'Bonus'.")
