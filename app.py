import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
from scipy.stats import zscore
import os

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="Sidian Bonus Lab PRO", layout="wide", page_icon="🎯")
st.title("🎯 Sidian Bonus Lab PRO")
st.caption("Hybrid Statistical + Markov Probability Engine")

MAX_NUMBER = 49
DB_PATH = "draws.db"  # ROOT DIRECTORY (Cloud Safe)

# =====================================================
# DATABASE
# =====================================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date TEXT,
            numbers TEXT,
            bonus INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_draws(main_numbers, bonus_series):
    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame({
        "draw_date": pd.Timestamp.now(),
        "numbers": main_numbers.astype(str).agg(",".join, axis=1),
        "bonus": bonus_series
    })
    df.to_sql("draws", conn, if_exists="append", index=False)
    conn.close()

def load_bonus_series():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT bonus FROM draws", conn)
    conn.close()
    if df.empty:
        return None
    return df["bonus"]

# =====================================================
# AUTO-DETECT BONUS COLUMN
# =====================================================

def detect_bonus_column(df):
    possible = ["bonus", "bonus_ball", "bonusball", "extra", "b"]
    for col in df.columns:
        if col.lower().strip() in possible:
            return col

    # fallback: detect column mostly 1-49 values
    for col in df.columns:
        try:
            numeric = pd.to_numeric(df[col], errors="coerce").dropna()
            if numeric.between(1, MAX_NUMBER).mean() > 0.9:
                return col
        except:
            continue
    return None

# =====================================================
# MODEL ENGINE
# =====================================================

def build_transition_matrix(series):
    matrix = np.zeros((MAX_NUMBER, MAX_NUMBER))
    for i in range(len(series)-1):
        matrix[series.iloc[i]-1, series.iloc[i+1]-1] += 1
    row_sums = matrix.sum(axis=1)
    row_sums[row_sums == 0] = 1
    return matrix / row_sums[:, None]

def monte_carlo(matrix, last, sims=3000):
    results = []
    current = last - 1
    for _ in range(sims):
        probs = matrix[current]
        next_n = np.random.choice(range(MAX_NUMBER), p=probs)
        results.append(next_n+1)
    return pd.Series(results).value_counts()/sims

def advanced_scores(series):
    freq = series.value_counts().reindex(range(1,MAX_NUMBER+1), fill_value=0)
    freq_prob = (freq+1)/(len(series)+MAX_NUMBER)

    last_seen = {i:-1 for i in range(1,MAX_NUMBER+1)}
    for idx,val in enumerate(series):
        last_seen[val] = idx

    gaps = pd.Series(
        [len(series)-last_seen[i] for i in range(1,MAX_NUMBER+1)],
        index=range(1,MAX_NUMBER+1)
    )

    gap_z = pd.Series(zscore(gaps), index=gaps.index)
    gap_norm = (gap_z-gap_z.min())/(gap_z.max()-gap_z.min())

    window = min(50, len(series))
    momentum = series.iloc[-window:].value_counts().reindex(range(1,MAX_NUMBER+1), fill_value=0)
    momentum_prob = momentum/window

    final = 0.4*freq_prob + 0.3*momentum_prob + 0.3*gap_norm
    return final, gaps

# =====================================================
# SIDEBAR INPUT
# =====================================================

st.sidebar.header("📂 Data Input")
mode = st.sidebar.radio("Select Source", ["Upload File","Paste Data","Load Database"])

bonus_series = None

if mode == "Upload File":
    file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv","xlsx"])
    if file:
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file, engine="openpyxl")

            bonus_col = detect_bonus_column(df)
            if bonus_col is None:
                st.error("Could not detect Bonus column.")
                st.stop()

            bonus_series = pd.to_numeric(df[bonus_col], errors="coerce").dropna().astype(int)
            bonus_series = bonus_series[bonus_series.between(1,MAX_NUMBER)]

            main_numbers = df.drop(columns=[bonus_col])
            main_numbers = main_numbers.apply(pd.to_numeric, errors="coerce")

            save_draws(main_numbers, bonus_series)

            st.success(f"Loaded & saved {len(bonus_series)} draws.")

        except Exception as e:
            st.error(f"File error: {e}")

elif mode == "Paste Data":
    text = st.sidebar.text_area("Paste bonus numbers (one per line)")
    if text:
        nums = [int(x.strip()) for x in text.split() if x.strip().isdigit()]
        bonus_series = pd.Series(nums)
        bonus_series = bonus_series[bonus_series.between(1,MAX_NUMBER)]
        st.success(f"Loaded {len(bonus_series)} entries.")

elif mode == "Load Database":
    bonus_series = load_bonus_series()
    if bonus_series is not None:
        st.success(f"Loaded {len(bonus_series)} draws from DB.")

# =====================================================
# MAIN ANALYTICS
# =====================================================

if bonus_series is not None and len(bonus_series) > 100:

    tab1, tab2, tab3 = st.tabs(["🔮 Prediction","📊 Trend","🧪 Backtest"])

    # Prediction
    with tab1:
        scores, gaps = advanced_scores(bonus_series)
        matrix = build_transition_matrix(bonus_series)
        last = bonus_series.iloc[-1]
        markov_probs = monte_carlo(matrix,last)

        hybrid = 0.6*scores + 0.4*markov_probs
        top5 = hybrid.nlargest(5)

        cols = st.columns(5)
        for i,(num,val) in enumerate(top5.items()):
            with cols[i]:
                st.metric(f"Rank {i+1}", f"#{num}", f"{val*100:.2f}%")
                st.caption(f"Gap: {int(gaps[num])}")

    # Trend
    with tab2:
        df_plot = pd.DataFrame({"Number":gaps.index,"Gap":gaps.values})
        fig = px.bar(df_plot,x="Number",y="Gap",title="Overdue Pressure Index")
        st.plotly_chart(fig,use_container_width=True)

    # Backtest
    with tab3:
        if st.button("Run Walk-Forward Test"):
            hits=0
            start=200
            for i in range(start,len(bonus_series)):
                train=bonus_series[:i]
                scores,_=advanced_scores(train)
                if bonus_series.iloc[i] in scores.nlargest(5).index:
                    hits+=1
            rate=(hits/(len(bonus_series)-start))*100
            st.success(f"Top 5 Hit Rate: {rate:.2f}%")

else:
    st.info("Upload or load at least 100 draws to activate engine.")
