import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Bonus Ball Analytics", page_icon="🎯")
st.title("🎯 Bonus Ball Analytics Lab")

MAX_NUMBER = 49

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    # Load Data
    df = pd.read_excel(uploaded_file)

    # Validate Column
    if "Bonus" not in df.columns:
        st.error("No 'Bonus' column found. Please ensure your Excel sheet has a column named 'Bonus'.")
        st.stop()

    # Clean Data: Convert to numeric, drop NaNs, and ensure they are within range
    bonus_series = pd.to_numeric(df["Bonus"], errors="coerce").dropna().astype(int)
    bonus_series = bonus_series[bonus_series.between(1, MAX_NUMBER)]
    
    st.subheader("📊 Dataset Info")
    col1, col2 = st.columns(2)
    col1.metric("Total Draws", len(bonus_series))
    col2.metric("Unique Numbers", bonus_series.nunique())

    # --- HELPER FUNCTION FOR SCORING ---
    def get_scores(series, n_range=MAX_NUMBER):
        # 1. Frequency Score
        freq = series.value_counts().reindex(range(1, n_range + 1), fill_value=0)
        freq_s = freq / freq.max() if freq.max() > 0 else freq
        
        # 2. Recency/Gap Score (Optimized)
        # We find the last index of each number
        last_idx = {i: -1 for i in range(1, n_range + 1)}
        for idx, val in enumerate(series):
            last_idx[val] = idx
        
        recency = pd.Series([len(series) - last_idx[i] for i in range(1, n_range + 1)], index=range(1, n_range + 1))
        rec_s = recency / recency.max()
        
        # 3. Rolling Window (Last 100)
        window_size = 100 if len(series) > 100 else len(series)
        roll_freq = series.iloc[-window_size:].value_counts().reindex(range(1, n_range + 1), fill_value=0)
        roll_s = roll_freq / roll_freq.max() if roll_freq.max() > 0 else roll_freq
        
        # Weighted Total
        final = (0.40 * freq_s) + (0.35 * roll_s) + (0.25 * rec_s)
        return final

    # ---------- CURRENT PREDICTION ----------
    st.divider()
    current_scores = get_scores(bonus_series)
    ranked = current_scores.sort_values(ascending=False).head(5)
    
    st.subheader("🔥 Top 5 Predicted Bonus Candidates")
    # Displaying as a nice dataframe
    results_df = pd.DataFrame({"Score": ranked.values}, index=ranked.index)
    st.table(results_df)

    # ---------- BACKTEST SECTION ----------
    st.divider()
    st.subheader("🧪 Walk-Forward Backtest")
    st.info("The backtest simulates history to see how many times the 'Top 5' would have contained the actual result.")

    if st.button("Run Backtest"):
        hits = 0
        start_point = 200  # Minimum data needed to start predicting
        
        if len(bonus_series) <= start_point:
            st.warning(f"Not enough data for backtest. Need more than {start_point} rows.")
        else:
            progress_bar = st.progress(0)
            bonus_vals = bonus_series.values
            total_iterations = len(bonus_vals) - start_point
            
            for i in range(start_point, len(bonus_vals)):
                # Training data is everything up to the current draw
                train_data = pd.Series(bonus_vals[:i])
                actual_draw = bonus_vals[i]
                
                # Get scores based ONLY on past data
                scores = get_scores(train_data)
                top5 = scores.nlargest(5).index.tolist()
                
                if actual_draw in top5:
                    hits += 1
                
                # Update progress occasionally to save resources
                if i % 10 == 0:
                    progress_bar.progress((i - start_point) / total_iterations)

            progress_bar.empty()
            
            # Results
            total_tests = len(bonus_vals) - start_point
            hit_rate = (hits / total_tests) * 100
            random_rate = (5 / MAX_NUMBER) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Tests", total_tests)
            c2.metric("Hits", hits)
            c3.metric("Hit Rate", f"{hit_rate:.2f}%")
            
            st.write(f"**Random Baseline:** {random_rate:.2f}%")
            
            if hit_rate > random_rate:
                st.success(f"Success! Model is {hit_rate - random_rate:.2f}% better than random guessing.")
            else:
                st.warning("Model is currently performing worse than or equal to random chance.")

else:
    st.info("Please upload an Excel file to begin the analysis.")
