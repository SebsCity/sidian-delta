import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Sidian Bonus Lab", layout="wide")
st.title("🎯 Bonus Ball Analytics Lab")

MAX_NUMBER = 49

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Validation: Expecting 'Bonus' and 'Main_1', 'Main_2', etc.
    if "Bonus" not in df.columns:
        st.error("Missing 'Bonus' column.")
        st.stop()

    bonus_series = pd.to_numeric(df["Bonus"], errors="coerce").dropna().astype(int)
    
    # ---------- 1. THE "COLD" FILTER ----------
    # Identify numbers that are statistically 'dead' (no appearance in a long time)
    # We will penalize these so they don't clog your Top 5.
    last_seen = {i: len(bonus_series) for i in range(1, MAX_NUMBER + 1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER:
            last_seen[val] = len(bonus_series) - idx
    
    gap_series = pd.Series(last_seen)
    # Numbers that haven't appeared in 2.5x the expected cycle (49 * 2.5)
    cold_threshold = MAX_NUMBER * 2.5
    is_cold = gap_series > cold_threshold

    # ---------- 2. THE "BUDDY" SYSTEM (Pairing) ----------
    # If your Excel has main numbers (e.g., 'Num1', 'Num2'...), we find correlations.
    # For this snippet, we'll check if the Bonus Ball likes to follow itself or specific neighbors.
    st.subheader("🤝 The Buddy System (Lead/Lag Analysis)")
    
    # Shifted series to see what usually follows what
    pairing_df = pd.DataFrame({'Current': bonus_series, 'Next': bonus_series.shift(-1)}).dropna()
    # If the user clicks a number, show its 'Buddies'
    check_num = st.selectbox("Check 'Buddies' for Number:", range(1, MAX_NUMBER + 1), index=6)
    buddies = pairing_df[pairing_df['Current'] == check_num]['Next'].value_counts().head(3)
    st.write(f"When **{check_num}** is the Bonus, these often follow: {', '.join(buddies.index.astype(str))}")

    # ---------- 3. VISUALIZING THE "DECAY" ----------
    # Shows how 'due' a number is compared to its average appearance rate
    st.subheader("📉 The Decay Chart (Gap Analysis)")
    
    avg_gap = MAX_NUMBER # Theoretically hits every 49 draws
    decay_data = pd.DataFrame({
        "Number": gap_series.index,
        "Current Gap": gap_series.values,
        "Theoretical Average": avg_gap
    })
    
    # Calculate a "Decay Pressure" score
    decay_data['Pressure'] = decay_data['Current Gap'] / decay_data['Theoretical Average']
    
    fig = px.bar(decay_data, x='Number', y='Current Gap', 
                 color='Pressure', color_continuous_scale='Reds',
                 title="Current Gap per Number (Higher = More 'Due')")
    fig.add_hline(y=avg_gap, line_dash="dash", annotation_text="Avg Cycle")
    st.plotly_chart(fig, use_container_広告=True)

    # ---------- FINAL RANKING ENGINE ----------
    st.divider()
    
    # Weights
    w_freq = 0.30
    w_recency = 0.40  # We weigh the 'Gap' heavily
    w_rolling = 0.30
    
    # Calculation
    freq = bonus_series.value_counts().reindex(range(1, MAX_NUMBER + 1), fill_value=0)
    freq_s = freq / freq.max()
    
    rec_s = gap_series / gap_series.max()
    
    window = 100 if len(bonus_series) > 100 else len(bonus_series)
    roll_freq = bonus_series.iloc[-window:].value_counts().reindex(range(1, MAX_NUMBER + 1), fill_value=0)
    roll_s = roll_freq / roll_freq.max() if roll_freq.max() > 0 else roll_freq

    final_score = (w_freq * freq_s) + (w_recency * rec_s) + (w_rolling * roll_s)
    
    # Apply Cold Filter (Penalize numbers that are too cold)
    final_score[is_cold] = final_score[is_cold] * 0.5 

    ranked = final_score.sort_values(ascending=False).head(5)

    st.subheader("🔥 Top 5 Optimized Sequence")
    cols = st.columns(5)
    for i, (num, score) in enumerate(ranked.items()):
        cols[i].metric(label=f"Rank {i+1}", value=f"#{num}", delta=f"{score:.2f} Score")

    st.caption("Sequence is ordered from Highest Probability to Least Possible within the Top 5.")

else:
    st.info("Upload your history to calculate the Buddy System and Decay metrics.")
