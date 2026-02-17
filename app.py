import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Page Config
st.set_page_config(page_title="Sidian Bonus Lab", layout="wide", page_icon="🎯")

# Styling
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Sidian Bonus Ball Analytics Lab")
st.caption("Advanced Statistical Ranking & Probability Engine")

MAX_NUMBER = 49

# --- HELPER FUNCTION FOR SCORING ---
def get_scores(series, n_range=MAX_NUMBER):
    # 1. All-Time Frequency
    freq = series.value_counts().reindex(range(1, n_range + 1), fill_value=0)
    freq_s = freq / freq.max() if freq.max() > 0 else freq
    
    # 2. Recency/Gap (How long since last seen)
    last_idx = {i: -1 for i in range(1, n_range + 1)}
    for idx, val in enumerate(series):
        if 1 <= val <= n_range:
            last_idx[val] = idx
    
    gaps = pd.Series([len(series) - last_idx[i] for i in range(1, n_range + 1)], index=range(1, n_range + 1))
    rec_s = gaps / gaps.max()
    
    # 3. Rolling Momentum (Last 100 draws)
    window_size = 100 if len(series) > 100 else len(series)
    roll_freq = series.iloc[-window_size:].value_counts().reindex(range(1, n_range + 1), fill_value=0)
    roll_s = roll_freq / roll_freq.max() if roll_freq.max() > 0 else roll_freq
    
    # Weighted Scoring Logic
    # 40% Weight on Gap (Pressure), 30% on Momentum, 30% on History
    final = (0.30 * freq_s) + (0.30 * roll_s) + (0.40 * rec_s)
    
    # 4. Cold Filter: Penalize numbers that have disappeared for too long (over 120 draws)
    cold_mask = gaps > 120
    final[cold_mask] = final[cold_mask] * 0.5
    
    return final, gaps

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Draw History (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if "Bonus" not in df.columns:
        st.error("Error: Column named 'Bonus' not found in Excel file.")
        st.stop()

    # Clean data
    bonus_series = pd.to_numeric(df["Bonus"], errors="coerce").dropna().astype(int)
    bonus_series = bonus_series[bonus_series.between(1, MAX_NUMBER)]

    # --- TABBED INTERFACE ---
    tab1, tab2, tab3 = st.tabs(["🔮 Live Prediction", "📉 Trend Analysis", "🧪 Backtest"])

    with tab1:
        st.subheader("Next Draw Probability")
        final_scores, current_gaps = get_scores(bonus_series)
        
        # Calculate Top 3 Percentage
        top_3_raw = final_scores.nlargest(3)
        total_top_weight = top_3_raw.sum()
        top_3_probs = (top_3_raw / total_top_weight) * 100

        cols = st.columns(3)
        for i, (num, prob) in enumerate(top_3_probs.items()):
            with cols[i]:
                st.metric(label=f"Rank {i+1} Candidate", value=f"#{num}", delta=f"{prob:.1f}% Match")
                st.progress(int(prob))
                st.caption(f"Current Gap: {int(current_gaps[num])} draws")

        st.divider()
        st.subheader("🤝 The Buddy System")
        # Shift analysis to find what follows a specific number
        pairing_df = pd.DataFrame({'Current': bonus_series, 'Next': bonus_series.shift(-1)}).dropna()
        look_up = st.selectbox("If the LAST Bonus Ball was:", range(1, MAX_NUMBER + 1), index=int(bonus_series.iloc[-1])-1)
        buddies = pairing_df[pairing_df['Current'] == look_up]['Next'].value_counts().head(3)
        
        if not buddies.empty:
            st.write(f"Historically, when **#{look_up}** is drawn, these 3 numbers often appear next:")
            st.write(f"👉 {', '.join([f'#{n}' for n in buddies.index])}")
        else:
            st.write("Not enough historical data for this specific sequence.")

    with tab2:
        st.subheader("Numerical Decay (Elasticity)")
        decay_df = pd.DataFrame({
            "Number": current_gaps.index,
            "Draws Since Last Seen": current_gaps.values,
            "Pressure": (current_gaps.values / MAX_NUMBER).round(2)
        })
        
        fig = px.bar(decay_df, x='Number', y='Draws Since Last Seen', color='Pressure',
                     color_continuous_scale='Reds', title="Which numbers are 'Overdue'?")
        fig.add_hline(y=MAX_NUMBER, line_dash="dash", annotation_text="Avg Cycle (49)")
        st.plotly_chart(fig, use_container_width=True)
        

    with tab3:
        st.subheader("Historical Accuracy Test")
        if st.button("Run Walk-Forward Backtest"):
            hits = 0
            start_point = 200
            bonus_vals = bonus_series.values
            
            if len(bonus_vals) <= start_point:
                st.warning("Need at least 200 draws to run a valid backtest.")
            else:
                bar = st.progress(0)
                total = len(bonus_vals) - start_point
                
                for i in range(start_point, len(bonus_vals)):
                    train = pd.Series(bonus_vals[:i])
                    actual = bonus_vals[i]
                    scores, _ = get_scores(train)
                    top5 = scores.nlargest(5).index.tolist()
                    if actual in top5:
                        hits += 1
                    if i % 20 == 0:
                        bar.progress((i - start_point) / total)
                
                bar.empty()
                hit_rate = (hits / total) * 100
                st.success(f"Backtest Complete! Hit Rate for Top 5: {hit_rate:.2f}%")
                st.write(f"Random Baseline: {(5/49)*100:.2f}%")

else:
    st.info("👋 Welcome. Please upload your Bonus Ball Excel history to begin.")

