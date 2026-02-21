import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="Sidian Decision Matrix V3", layout="centered", page_icon="🎯")

MAX_NUMBER = 49
DB_PATH = "database/draws.db"

st.title("🎯 Sidian Decision Matrix V3")
st.caption("Adaptive Multi-Engine Confluence Intelligence")

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
# SIDEBAR CONTROLS (ADAPTIVE WEIGHTS)
# ==========================================
with st.sidebar:
    st.header("⚙️ Adaptive Controls")

    w_hybrid = st.slider("Hybrid Weight", 0.0, 1.0, 0.35)
    w_harmonic = st.slider("Harmonic Weight", 0.0, 1.0, 0.20)
    w_overdue = st.slider("Overdue Weight", 0.0, 1.0, 0.30)
    w_ripple = st.slider("Ripple Weight", 0.0, 1.0, 0.15)

    rolling_window = st.slider("Rolling Window (Recent Draws)", 20, 300, 100)

    normalize_factor = w_hybrid + w_harmonic + w_overdue + w_ripple
    if normalize_factor == 0:
        normalize_factor = 1

    # Data Upload
    file = st.file_uploader("Upload Draw History", type=["xlsx", "csv"])

    if file:
        df_new = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        if st.button("Commit to Database"):
            m_cols = [c for c in df_new.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
            b_col = [c for c in df_new.columns if 'bonus' in c.lower()][0]

            db_ready = pd.DataFrame()
            db_ready['numbers'] = df_new[m_cols].astype(str).agg(','.join, axis=1)
            db_ready['bonus'] = df_new[b_col].astype(int)

            conn = sqlite3.connect(DB_PATH)
            db_ready.to_sql("draws", conn, if_exists="replace", index=True, index_label="id")
            conn.close()
            st.success("Database Updated")
            st.rerun()

# ==========================================
# V3 ADAPTIVE ENGINE
# ==========================================
def calculate_v3(history_df, main_input):

    m_set = sorted([int(x) for x in main_input.split() if x.isdigit()])
    if len(m_set) == 0:
        return None

    history_df = history_df.head(rolling_window)
    bonus_series = history_df['bonus'].astype(int)

    base_index = range(1, MAX_NUMBER + 1)
    scores = pd.Series(0.0, index=base_index)

    # ------------------------------------------
    # 1️⃣ HYBRID ENGINE
    # ------------------------------------------
    hybrid = pd.Series(0.0, index=base_index)

    for x in m_set:
        for offset in [-1, 0, 1]:
            if 1 <= x + offset <= MAX_NUMBER:
                hybrid[x + offset] += 1.0

    hybrid = hybrid / hybrid.max() if hybrid.max() != 0 else hybrid

    # ------------------------------------------
    # 2️⃣ HARMONIC ENGINE
    # ------------------------------------------
    harmonic = pd.Series(0.0, index=base_index)
    avg = np.mean(m_set)

    for n in base_index:
        harmonic[n] = max(0, 1 - abs(n - avg) / MAX_NUMBER)

    harmonic = harmonic / harmonic.max()

    # ------------------------------------------
    # 3️⃣ ADAPTIVE OVERDUE ENGINE
    # ------------------------------------------
    last_seen = {i: -1 for i in base_index}

    for idx, val in enumerate(bonus_series[::-1]):
        if 1 <= val <= MAX_NUMBER:
            last_seen[val] = len(bonus_series) - idx

    gaps = pd.Series(
        [len(bonus_series) - last_seen[i] for i in base_index],
        index=base_index
    )

    decay = np.log1p(gaps)
    overdue = decay / decay.max() if decay.max() != 0 else decay

    # ------------------------------------------
    # 4️⃣ RIPPLE MEMORY ENGINE
    # ------------------------------------------
    ripple = pd.Series(0.0, index=base_index)

    if not bonus_series.empty:
        last_bonus = int(bonus_series.iloc[0])
        splits = []

        for i in range(len(history_df) - 1):
            if int(history_df.iloc[i+1]['bonus']) == last_bonus:
                nums = [
                    int(float(x))
                    for x in str(history_df.iloc[i]['numbers']).split(',')
                    if x != 'nan'
                ]
                splits.extend(nums)

        if splits:
            ripple_counts = pd.Series(splits).value_counts()
            ripple[ripple_counts.index] = ripple_counts.values

    ripple = ripple / ripple.max() if ripple.max() != 0 else ripple

    # ------------------------------------------
    # 🧠 VOLATILITY INDEX (New)
    # ------------------------------------------
    volatility = bonus_series.value_counts().std()
    st.metric("Market Volatility Index", round(volatility, 3))

    # ------------------------------------------
    # 🏆 FINAL WEIGHTED SCORE
    # ------------------------------------------
    final_scores = (
        (hybrid * w_hybrid) +
        (harmonic * w_harmonic) +
        (overdue * w_overdue) +
        (ripple * w_ripple)
    ) / normalize_factor

    final_scores = final_scores.sort_values(ascending=False)

    return final_scores, gaps

# ==========================================
# MAIN INTERFACE
# ==========================================
history = get_history()

if history.empty:
    st.info("Upload history data in sidebar to begin.")
else:
    st.subheader("🔮 Input Trigger Draw")
    user_input = st.text_input("Enter 6 Main Numbers (spaces only):")

    if user_input:
        results = calculate_v3(history, user_input)

        if results:
            final_scores, gaps = results

            st.divider()
            st.header("🏆 Adaptive Confluence Ranking")

            top7 = final_scores.head(7)

            for n, score in top7.items():
                strength = round(score, 3)
                if score > 0.65:
                    st.success(f"#{n} | Strength: {strength}")
                elif score > 0.45:
                    st.warning(f"#{n} | Strength: {strength}")
                else:
                    st.info(f"#{n} | Strength: {strength}")

            # ------------------------------------------
            # 📊 Pressure Visualization
            # ------------------------------------------
            st.divider()
            st.subheader("📊 Pressure Index (Overdue Decay)")
            fig = px.bar(
                x=gaps.index,
                y=gaps.values,
                labels={'x': 'Ball', 'y': 'Draws Since Seen'}
            )
            st.plotly_chart(fig, use_container_width=True)

            # ------------------------------------------
            # 📜 Archive
            # ------------------------------------------
            with st.expander("View Recent Draws"):
                st.dataframe(history.head(20), use_container_width=True)
