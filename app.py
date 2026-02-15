import streamlit as st
import pandas as pd
import numpy as np
import itertools
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split

st.set_page_config(layout="wide")
st.title("🎯 Lotto Engine V2.1 — Stability Mode B (2-Hit Optimized)")

uploaded_file = st.file_uploader("Upload Excel Lotto Sheet", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    main_cols = df.columns[1:7]
    bonus_col = df.columns[7]

    df_main = df[main_cols]
    df_bonus = df[[bonus_col]]

    MAX_NUMBER = 49
    MID = 25

# ==============================
# FREQUENCY
# ==============================
    def calculate_frequency(df):
        return Counter(df.values.flatten())

# ==============================
# DELAY
# ==============================
    def calculate_delay(df):
        delay = {}
        for num in range(1, MAX_NUMBER + 1):
            appearances = df[df.isin([num]).any(axis=1)]
            if not appearances.empty:
                last_seen = appearances.index.max()
                delay[num] = len(df) - last_seen
            else:
                delay[num] = len(df)
        return delay

# ==============================
# ML (Rolling 5 Draws)
# ==============================
    def create_ml_dataset(df, window=5):
        X, y = [], []
        for i in range(window, len(df)):
            past = df.iloc[i-window:i].values.flatten()
            next_draw = df.iloc[i].values

            feature = np.zeros(MAX_NUMBER)
            for n in past:
                feature[n-1] += 1

            target = np.zeros(MAX_NUMBER)
            for n in next_draw:
                target[n-1] = 1

            X.append(feature)
            y.append(target)

        return np.array(X), np.array(y)

# ==============================
# STRUCTURE ANALYSIS
# ==============================
    def analyze_structure(df):
        sums, odd_even, low_high = [], [], []

        for _, row in df.iterrows():
            nums = row.values
            sums.append(sum(nums))
            odd_even.append(sum(n % 2 for n in nums))
            low_high.append(sum(n <= MID for n in nums))

        return {
            "sum_mean": np.mean(sums),
            "sum_std": np.std(sums),
            "odd_modes": [x[0] for x in Counter(odd_even).most_common(2)],
            "low_modes": [x[0] for x in Counter(low_high).most_common(2)]
        }

# ==============================
# NORMALIZE
# ==============================
    def normalize_dict(d):
        max_val = max(d.values()) if max(d.values()) > 0 else 1
        return {k: v/max_val for k, v in d.items()}

# ==============================
# CALCULATE SCORES (Stability Weighted)
# ==============================
    freq = calculate_frequency(df_main)
    delay = calculate_delay(df_main)

    freq_norm = normalize_dict(freq)
    delay_norm = normalize_dict(delay)

    X, y = create_ml_dataset(df_main)

    if len(X) > 10:
        model = MultiOutputClassifier(
            RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42)
        )
        model.fit(X[:-1], y[:-1])
        ml_probs = model.predict_proba([X[-1]])

        ml_scores = {i+1: ml_probs[i][0][1] for i in range(len(ml_probs))}
        ml_norm = normalize_dict(ml_scores)
    else:
        ml_norm = {i: 0 for i in range(1, MAX_NUMBER+1)}

# Stability Weights (Mode A+)
    final_scores = {}
    for num in range(1, MAX_NUMBER+1):
        final_scores[num] = (
            0.55 * freq_norm.get(num, 0) +
            0.30 * delay_norm.get(num, 0) +
            0.15 * ml_norm.get(num, 0)
        )

    ranked_numbers = sorted(final_scores, key=final_scores.get, reverse=True)

# Smaller Pool for Density
    TOP_POOL = ranked_numbers[:15]
    CORE_3 = ranked_numbers[:3]
    CORE_2 = ranked_numbers[:2]

# ==============================
# PAIR STRENGTH
# ==============================
    pair_counter = Counter()
    for _, row in df_main.iterrows():
        pair_counter.update(itertools.combinations(sorted(row.values), 2))

# ==============================
# STRUCTURE FILTER
# ==============================
    structure = analyze_structure(df_main)
    sum_mean = structure["sum_mean"]
    sum_std = structure["sum_std"]
    allowed_odds = structure["odd_modes"]
    allowed_low = structure["low_modes"]

# ==============================
# GENERATE SETS
# ==============================
    def score_combo(combo):
        pair_score = sum(pair_counter.get(tuple(sorted(p)), 0)
                         for p in itertools.combinations(combo, 2))
        return sum(final_scores[n] for n in combo) + pair_score

    def valid_structure(combo, tight=True):
        odd_count = sum(n % 2 for n in combo)
        low_count = sum(n <= MID for n in combo)
        total_sum = sum(combo)

        band = 0.7 if tight else 0.9

        return (
            odd_count in allowed_odds and
            low_count in allowed_low and
            (sum_mean - band*sum_std <= total_sum <= sum_mean + band*sum_std)
        )

# Clustered Sets (1–3)
    clustered_sets = []
    for combo in itertools.combinations(TOP_POOL, 6):
        if not all(n in combo for n in CORE_3):
            continue
        if not valid_structure(combo, tight=True):
            continue
        clustered_sets.append((combo, score_combo(combo)))

    clustered_sets.sort(key=lambda x: x[1], reverse=True)
    clustered_sets = clustered_sets[:3]

# Semi-Diversified Sets (4–5)
    diversified_sets = []
    for combo in itertools.combinations(TOP_POOL, 6):
        if not all(n in combo for n in CORE_2):
            continue
        if valid_structure(combo, tight=False):
            diversified_sets.append((combo, score_combo(combo)))

    diversified_sets.sort(key=lambda x: x[1], reverse=True)

    final_sets = clustered_sets + diversified_sets[:2]

# ==============================
# BONUS MODEL (Frequency Dominant)
# ==============================
    bonus_freq = calculate_frequency(df_bonus)
    bonus_delay = calculate_delay(df_bonus)

    bonus_freq_norm = normalize_dict(bonus_freq)
    bonus_delay_norm = normalize_dict(bonus_delay)

    bonus_scores = {}
    for num in range(1, MAX_NUMBER+1):
        bonus_scores[num] = (
            0.7 * bonus_freq_norm.get(num, 0) +
            0.3 * bonus_delay_norm.get(num, 0)
        )

    best_bonus = max(bonus_scores, key=bonus_scores.get)

# ==============================
# DISPLAY
# ==============================
    st.subheader("🏆 Stability Mode B — Top 5 Sets")

    for i, (combo, score) in enumerate(final_sets):
        st.write(f"Set {i+1}: {sorted(combo)}  | Bonus: {best_bonus}")
