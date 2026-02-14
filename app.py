import streamlit as st
import pandas as pd
import numpy as np
import itertools
from collections import Counter
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split

st.set_page_config(layout="wide")

st.title("🎯 Advanced Lotto Prediction Dashboard")

# ==============================
# FILE UPLOAD
# ==============================

uploaded_file = st.file_uploader("Upload Excel Lotto Sheet", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    number_columns = df.columns[1:7]  # assumes first column is date
    df_numbers = df[number_columns]

    st.success("File loaded successfully!")

    # ==============================
    # FREQUENCY WEIGHTING
    # ==============================

    def calculate_frequency(df, recent_weight=2):
        all_numbers = df.values.flatten()
        freq = Counter(all_numbers)

        recent_df = df.tail(20)
        recent_numbers = recent_df.values.flatten()
        recent_freq = Counter(recent_numbers)

        for num in recent_freq:
            freq[num] += recent_freq[num] * recent_weight

        return freq

    freq = calculate_frequency(df_numbers)

    # ==============================
    # HOT + REBOUND
    # ==============================

    last_draw = set(df_numbers.tail(1).values.flatten())
    hot_numbers = sorted(freq, key=freq.get, reverse=True)[:15]
    rebound = [n for n in hot_numbers if n not in last_draw][:12]

    # ==============================
    # PAIR STRENGTH
    # ==============================

    pair_counter = Counter()

    for _, row in df_numbers.iterrows():
        nums = sorted(row.values)
        pairs = itertools.combinations(nums, 2)
        pair_counter.update(pairs)

    # ==============================
    # GENERATE PRIMARY SET
    # ==============================

    scored_sets = []

    for combo in itertools.combinations(rebound[:12], 6):
        freq_score = sum(freq[n] for n in combo)
        pair_score = sum(pair_counter.get(tuple(sorted(p)), 0)
                         for p in itertools.combinations(combo, 2))
        total = freq_score + pair_score
        scored_sets.append((combo, total))

    scored_sets.sort(key=lambda x: x[1], reverse=True)
    primary_set = scored_sets[0][0]

    # ==============================
    # STRONGEST 3
    # ==============================

    trio_scores = []

    for trio in itertools.combinations(primary_set, 3):
        freq_score = sum(freq[n] for n in trio)
        pair_score = sum(pair_counter.get(tuple(sorted(p)), 0)
                         for p in itertools.combinations(trio, 2))
        trio_scores.append((trio, freq_score + pair_score))

    trio_scores.sort(key=lambda x: x[1], reverse=True)
    best_three = trio_scores[0][0]

    # ==============================
    # MACHINE LEARNING MODEL
    # ==============================

    max_number = int(df_numbers.max().max())

    def create_ml_dataset(df):
        X = []
        y = []

        for i in range(len(df) - 1):
            current_draw = df.iloc[i].values
            next_draw = df.iloc[i + 1].values

            feature_vector = np.zeros(max_number)
            for n in current_draw:
                feature_vector[n - 1] = 1

            target_vector = np.zeros(max_number)
            for n in next_draw:
                target_vector[n - 1] = 1

            X.append(feature_vector)
            y.append(target_vector)

        return np.array(X), np.array(y)

    X, y = create_ml_dataset(df_numbers)

    if len(X) > 10:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        model = MultiOutputClassifier(RandomForestClassifier(n_estimators=200))
        model.fit(X_train, y_train)

        ml_probs = model.predict_proba([X[-1]])

        prob_scores = []
        for i in range(len(ml_probs)):
            prob_scores.append(ml_probs[i][0][1])

        ml_prediction = np.argsort(prob_scores)[-6:] + 1
    else:
        ml_prediction = []

    # ==============================
    # BACKTEST TRACKER
    # ==============================

    def backtest(df, window=50):
        hits = []

        for i in range(window, len(df) - 1):
            train_df = df.iloc[:i]
            test_draw = set(df.iloc[i + 1].values)

            freq_local = calculate_frequency(train_df)
            hot_local = sorted(freq_local, key=freq_local.get, reverse=True)[:6]

            predicted = set(hot_local)
            hit_count = len(predicted.intersection(test_draw))
            hits.append(hit_count)

        return hits

    if len(df_numbers) > 60:
        hit_results = backtest(df_numbers)
        avg_hits = np.mean(hit_results)
    else:
        hit_results = []
        avg_hits = 0

    # ==============================
    # HEATMAP VISUALIZATION
    # ==============================

    freq_df = pd.DataFrame.from_dict(freq, orient="index", columns=["Frequency"])
    freq_df = freq_df.sort_index()

    fig, ax = plt.subplots()
    heat_data = np.array(freq_df["Frequency"]).reshape(1, -1)
    ax.imshow(heat_data)
    ax.set_yticks([])
    ax.set_xticks(range(len(freq_df.index)))
    ax.set_xticklabels(freq_df.index, rotation=90)
    st.pyplot(fig)

    # ==============================
    # DISPLAY RESULTS
    # ==============================

    st.subheader("🎯 Primary 6-Number Set")
    st.write(sorted(primary_set))

    st.subheader("🔥 Strongest 3")
    st.write(sorted(best_three))

    st.subheader("🤖 ML Suggested 6")
    st.write(sorted(ml_prediction))

    st.subheader("📊 Backtest Average Hits (Hot Model)")
    st.write(round(avg_hits, 2))
