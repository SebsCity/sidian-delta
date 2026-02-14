import streamlit as st
import pandas as pd
import numpy as np
import itertools
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split

st.set_page_config(layout="wide")
st.title("🎯 Lotto Prediction Engine V2.0 (1–49 + Bonus)")

# ==============================
# FILE UPLOAD
# ==============================
uploaded_file = st.file_uploader("Upload Excel Lotto Sheet", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    main_cols = df.columns[1:7]      # 6 main numbers
    bonus_col = df.columns[7]       # bonus column

    df_main = df[main_cols]
    df_bonus = df[[bonus_col]]

    st.success("File Loaded Successfully!")

    MAX_NUMBER = 49
    MID = 25

# ==============================
# FREQUENCY
# ==============================
    def calculate_frequency(df):
        freq = Counter(df.values.flatten())
        return freq

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
# ML DATASET (Rolling 5 Draws)
# ==============================
    def create_ml_dataset(df, window=5):
        X, y = [], []

        for i in range(window, len(df)):
            past_draws = df.iloc[i-window:i].values.flatten()
            next_draw = df.iloc[i].values

            feature = np.zeros(MAX_NUMBER)
            for n in past_draws:
                feature[n-1] += 1

            target = np.zeros(MAX_NUMBER)
            for n in next_draw:
                target[n-1] = 1

            X.append(feature)
            y.append(target)

        return np.array(X), np.array(y)

# ==============================
# STRUCTURAL ANALYSIS
# ==============================
    def analyze_structure(df):
        odd_even = []
        low_high = []
        sums = []

        for _, row in df.iterrows():
            nums = row.values
            odd = sum(n % 2 for n in nums)
            low = sum(n <= MID for n in nums)

            odd_even.append(odd)
            low_high.append(low)
            sums.append(sum(nums))

        return {
            "odd_even_mode": Counter(odd_even).most_common(2),
            "low_high_mode": Counter(low_high).most_common(2),
            "sum_mean": np.mean(sums),
            "sum_std": np.std(sums)
        }

# ==============================
# NORMALIZE FUNCTION
# ==============================
    def normalize_dict(d):
        max_val = max(d.values())
        return {k: v / max_val for k, v in d.items()}

# ==============================
# TRAIN MODELS
# ==============================
    freq = calculate_frequency(df_main)
    delay = calculate_delay(df_main)

    freq_norm = normalize_dict(freq)
    delay_norm = normalize_dict(delay)

    X, y = create_ml_dataset(df_main)

    if len(X) > 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False)

        model = MultiOutputClassifier(
            RandomForestClassifier(n_estimators=400, max_depth=12)
        )

        model.fit(X_train, y_train)
        ml_probs = model.predict_proba([X[-1]])

        ml_scores = {}
        for i in range(len(ml_probs)):
            ml_scores[i+1] = ml_probs[i][0][1]

        ml_norm = normalize_dict(ml_scores)
    else:
        ml_norm = {i: 0 for i in range(1, MAX_NUMBER+1)}

# ==============================
# FINAL NUMBER SCORING
# ==============================
    final_scores = {}

    for num in range(1, MAX_NUMBER+1):
        final_scores[num] = (
            0.4 * freq_norm.get(num, 0) +
            0.3 * delay_norm.get(num, 0) +
            0.3 * ml_norm.get(num, 0)
        )

    ranked_numbers = sorted(final_scores, key=final_scores.get, reverse=True)
    top_pool = ranked_numbers[:18]

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
    allowed_odds = [x[0] for x in structure["odd_even_mode"]]
    allowed_low = [x[0] for x in structure["low_high_mode"]]

    sum_mean = structure["sum_mean"]
    sum_std = structure["sum_std"]

# ==============================
# GENERATE COMBINATIONS
# ==============================
    scored_sets = []

    for combo in itertools.combinations(top_pool, 6):

        odd_count = sum(n % 2 for n in combo)
        low_count = sum(n <= MID for n in combo)
        total_sum = sum(combo)

        if odd_count not in allowed_odds:
            continue
        if low_count not in allowed_low:
            continue
        if not (sum_mean - sum_std <= total_sum <= sum_mean + sum_std):
            continue

        pair_score = sum(pair_counter.get(tuple(sorted(p)), 0)
                         for p in itertools.combinations(combo, 2))

        combo_score = sum(final_scores[n] for n in combo) + pair_score
        scored_sets.append((combo, combo_score))

    scored_sets.sort(key=lambda x: x[1], reverse=True)

# ==============================
# BONUS MODEL (Separate)
# ==============================
    bonus_freq = calculate_frequency(df_bonus)
    bonus_delay = calculate_delay(df_bonus)

    bonus_freq_norm = normalize_dict(bonus_freq)
    bonus_delay_norm = normalize_dict(bonus_delay)

    bonus_scores = {}
    for num in range(1, MAX_NUMBER+1):
        bonus_scores[num] = (
            0.6 * bonus_freq_norm.get(num, 0) +
            0.4 * bonus_delay_norm.get(num, 0)
        )

    best_bonus = max(bonus_scores, key=bonus_scores.get)

# ==============================
# DISPLAY RESULTS
# ==============================
    st.subheader("🏆 Top 5 Ranked Sets")

    for i in range(min(5, len(scored_sets))):
        st.write(f"Set {i+1}: {sorted(scored_sets[i][0])}  | Bonus: {best_bonus}")
