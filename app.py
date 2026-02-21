import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="Sidian V4 Self-Learning Engine", layout="centered", page_icon="🎯")

MAX_NUMBER = 49
DB_PATH = "database/draws.db"

st.title("🎯 Sidian Decision Matrix V4")
st.caption("Self-Learning Confluence Optimization Engine")

# ==========================================
# DATABASE
# ==========================================
def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY,
            numbers TEXT,
            bonus INTEGER
        )
    """)
    conn.close()

init_db()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
    conn.close()
    return df

# ==========================================
# SAFE NUMBER PARSER (NO MORE CRASHES)
# ==========================================
def parse_numbers(cell):
    nums = []
    raw = str(cell).split(',')
    for x in raw:
        x = x.strip()
        if x.isdigit():
            val = int(x)
            if 1 <= val <= MAX_NUMBER:
                nums.append(val)
    return nums

# ==========================================
# ENGINE CORE
# ==========================================
def generate_scores(history_df, trigger_numbers, weights):

    base_index = range(1, MAX_NUMBER + 1)
    scores = pd.Series(0.0, index=base_index)

    m_set = trigger_numbers
    bonus_series = history_df['bonus'].astype(int)

    # 1️⃣ Hybrid
    hybrid = pd.Series(0.0, index=base_index)
    for x in m_set:
        for offset in [-1, 0, 1]:
            if 1 <= x + offset <= MAX_NUMBER:
                hybrid[x + offset] += 1
    if hybrid.max() != 0:
        hybrid /= hybrid.max()

    # 2️⃣ Harmonic
    harmonic = pd.Series(0.0, index=base_index)
    avg = np.mean(m_set)
    for n in base_index:
        harmonic[n] = max(0, 1 - abs(n - avg) / MAX_NUMBER)
    harmonic /= harmonic.max()

    # 3️⃣ Overdue
    last_seen = {i: -1 for i in base_index}
    for idx, val in enumerate(bonus_series[::-1]):
        if 1 <= val <= MAX_NUMBER:
            last_seen[val] = len(bonus_series) - idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in base_index], index=base_index)
    overdue = np.log1p(gaps)
    if overdue.max() != 0:
        overdue /= overdue.max()

    # 4️⃣ Ripple
    ripple = pd.Series(0.0, index=base_index)
    if not bonus_series.empty:
        last_bonus = int(bonus_series.iloc[0])
        splits = []
        for i in range(len(history_df) - 1):
            if int(history_df.iloc[i+1]['bonus']) == last_bonus:
                splits.extend(parse_numbers(history_df.iloc[i]['numbers']))
        if splits:
            counts = pd.Series(splits).value_counts()
            ripple[counts.index] = counts.values
            ripple /= ripple.max()

    # Weighted sum
    scores = (
        hybrid * weights[0] +
        harmonic * weights[1] +
        overdue * weights[2] +
        ripple * weights[3]
    )

    return scores.sort_values(ascending=False)

# ==========================================
# SELF-LEARNING OPTIMIZER
# ==========================================
def optimize_weights(history_df, backtest_window=50):

    history_df = history_df.head(backtest_window)

    best_score = -1
    best_weights = None

    weight_options = [
        (0.4,0.2,0.3,0.1),
        (0.3,0.2,0.3,0.2),
        (0.35,0.2,0.35,0.1),
        (0.25,0.25,0.35,0.15),
        (0.3,0.25,0.25,0.2)
    ]

    for weights in weight_options:

        hits = 0

        for i in range(len(history_df) - 1):
            trigger = parse_numbers(history_df.iloc[i]['numbers'])
            actual_bonus = int(history_df.iloc[i]['bonus'])

            past_data = history_df.iloc[i+1:]
            if len(trigger) < 3:
                continue

            ranked = generate_scores(past_data, trigger, weights)
            top5 = ranked.head(5).index.tolist()

            if actual_bonus in top5:
                hits += 1

        if hits > best_score:
            best_score = hits
            best_weights = weights

    return best_weights, best_score

# ==========================================
# MAIN
# ==========================================
history = get_history()

if history.empty:
    st.info("Upload draw history to begin.")
else:

    st.sidebar.header("🧠 Self-Learning Mode")
    backtest_window = st.sidebar.slider("Backtest Window", 30, 200, 80)

    if st.sidebar.button("Run Weight Optimization"):
        with st.spinner("Training V4 Engine..."):
            best_weights, score = optimize_weights(history, backtest_window)
            st.session_state["best_weights"] = best_weights
            st.session_state["best_score"] = score

    if "best_weights" in st.session_state:
        st.sidebar.success(f"Optimized Weights: {st.session_state['best_weights']}")
        st.sidebar.info(f"Backtest Hits: {st.session_state['best_score']}")

    st.subheader("🔮 Enter Trigger Draw")
    user_input = st.text_input("Enter 6 Main Numbers (space separated)")

    if user_input and "best_weights" in st.session_state:

        trigger = [int(x) for x in user_input.split() if x.isdigit()]

        final_scores = generate_scores(history, trigger, st.session_state["best_weights"])

        st.divider()
        st.header("🏆 V4 Self-Learning Ranking")

        for n, score in final_scores.head(7).items():
            strength = round(score,3)
            if strength > 0.6:
                st.success(f"#{n} | Strength: {strength}")
            elif strength > 0.4:
                st.warning(f"#{n} | Strength: {strength}")
            else:
                st.info(f"#{n} | Strength: {strength}")

        with st.expander("View Recent Draws"):
            st.dataframe(history.head(20), use_container_width=True)
