import streamlit as st
import pandas as pd
import numpy as np

st.title("🎯 Bonus Ball Analytics Lab")

MAX_NUMBER = 49

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # Assume bonus column is named "Bonus"
    if "Bonus" not in df.columns:
        st.error("No 'Bonus' column found.")
        st.stop()

    bonus_series = pd.to_numeric(df["Bonus"], errors="coerce").dropna().astype(int)

    st.subheader("Dataset Info")
    st.write("Total Bonus Draws:", len(bonus_series))

    # ---------- FREQUENCY SCORE ----------
    freq = bonus_series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_score = freq / freq.max()

    # ---------- RECENCY SCORE ----------
    last_occurrence = {}
    for num in range(1, MAX_NUMBER+1):
        occurrences = np.where(bonus_series.values == num)[0]
        if len(occurrences) > 0:
            last_occurrence[num] = len(bonus_series) - occurrences[-1]
        else:
            last_occurrence[num] = len(bonus_series)

    recency_score = pd.Series(last_occurrence)
    recency_score = recency_score / recency_score.max()

    # ---------- GAP SCORE (Overdue bias) ----------
    gap_score = recency_score.copy()

    # ---------- ROLLING WINDOW SCORE ----------
    window = 200 if len(bonus_series) > 200 else len(bonus_series)
    rolling_freq = bonus_series[-window:].value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    rolling_score = rolling_freq / rolling_freq.max() if rolling_freq.max() > 0 else rolling_freq

    # ---------- FINAL WEIGHTED SCORE ----------
    final_score = (
        0.35 * freq_score +
        0.30 * rolling_score +
        0.20 * gap_score +
        0.15 * recency_score
    )

    ranked = final_score.sort_values(ascending=False)

    st.subheader("🔥 Top 5 Predicted Bonus Candidates")
    st.write(ranked.head(5))

    # ---------- Backtest ----------
    st.subheader("📊 Backtest Last 100 Draws")

    test_window = 100 if len(bonus_series) > 100 else len(bonus_series)-1
    hits = 0

    for i in range(len(bonus_series) - test_window, len(bonus_series)-1):
        train = bonus_series[:i]
        test_value = bonus_series[i]

        freq_bt = train.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
        freq_bt = freq_bt / freq_bt.max() if freq_bt.max() > 0 else freq_bt

        top5 = freq_bt.sort_values(ascending=False).head(5).index.tolist()

        if test_value in top5:
            hits += 1

    hit_rate = hits / test_window if test_window > 0 else 0

    st.write("Top 5 Bonus Hit Rate:", round(hit_rate * 100, 2), "%")
