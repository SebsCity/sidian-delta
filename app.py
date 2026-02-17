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
    st.subheader("🧪 Walk-Forward Backtest")

hits = 0
predictions = []
actuals = []

bonus_values = bonus_series.values
N = MAX_NUMBER

start_point = 200  # need some training history

for i in range(start_point, len(bonus_values)):

    train = bonus_values[:i]
    actual = bonus_values[i]

    train_series = pd.Series(train)

    # Frequency score
    freq = train_series.value_counts().reindex(range(1, N+1), fill_value=0)
    freq_score = freq / freq.max() if freq.max() > 0 else freq

    # Recency / gap score
    last_occurrence = {}
    for num in range(1, N+1):
        occurrences = np.where(train == num)[0]
        if len(occurrences) > 0:
            last_occurrence[num] = len(train) - occurrences[-1]
        else:
            last_occurrence[num] = len(train)

    recency_score = pd.Series(last_occurrence)
    recency_score = recency_score / recency_score.max()

    # Rolling window
    window = 100 if len(train) > 100 else len(train)
    rolling_freq = train_series[-window:].value_counts().reindex(range(1, N+1), fill_value=0)
    rolling_score = rolling_freq / rolling_freq.max() if rolling_freq.max() > 0 else rolling_freq

    # Final score
    final_score = (
        0.35 * freq_score +
        0.35 * rolling_score +
        0.30 * recency_score
    )

    top5 = final_score.sort_values(ascending=False).head(5).index.tolist()

    predictions.append(top5)
    actuals.append(actual)

    if actual in top5:
        hits += 1

total_tests = len(actuals)
hit_rate = hits / total_tests

st.write("Total Tests:", total_tests)
st.write("Total Hits:", hits)
st.write("Model Hit Rate:", round(hit_rate * 100, 2), "%")

# Random baseline
random_baseline = 5 / MAX_NUMBER
st.write("Random Baseline:", round(random_baseline * 100, 2), "%")

if hit_rate > random_baseline:
    st.success("Model outperforms random baseline.")
else:
    st.warning("Model does NOT outperform random baseline.")
