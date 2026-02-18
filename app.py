import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
from scipy.stats import zscore

# ==========================================
# CONFIG
# ==========================================

st.set_page_config(page_title="Sidian Bonus Lab PRO", layout="wide", page_icon="🎯")
st.title("🎯 Sidian Bonus Lab PRO")
st.caption("Enterprise Hybrid Probability Engine")

MAX_NUMBER = 49
DB_PATH = "database/draws.db"

# ==========================================
# DATABASE SETUP
# ==========================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
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

def save_to_db(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("draws", conn, if_exists="append", index=False)
    conn.close()

def load_from_db():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM draws", conn)
    conn.close()
    return df

# ==========================================
# AUTO-DETECT BONUS COLUMN
# ==========================================

def detect_bonus_column(df):
    possible_names = ["bonus", "bonus_ball", "bonusball", "b", "extra"]
    for col in df.columns:
        if col.lower().strip() in possible_names:
            return col
    for col in df.columns:
        if df[col].dropna().between(1, MAX_NUMBER).all():
            if df[col].nunique() > 10:
                return col
    return None

# ==========================================
# TRANSITION MATRIX
# ==========================================

def build_transition_matrix(series):
    matrix = np.zeros((MAX_NUMBER, MAX_NUMBER))
    for i in range(len(series)-1):
        matrix[series.iloc[i]-1, series.iloc[i+1]-1] += 1
    row_sums = matrix.sum(axis=1)
    row_sums[row_sums == 0] = 1
    matrix = matrix / row_sums[:, None]
    return matrix

def monte_carlo(matrix, last, sims=5000):
    results = []
    current = last - 1
    for _ in range(sims):
        probs = matrix[current]
        next_n = np.random.choice(range(MAX_NUMBER), p=probs)
        results.append(next_n+1)
    return pd.Series(results).value_counts()/sims

# ==========================================
# ADVANCED SCORING
# ==========================================

def advanced_scores(series):
    freq = series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_prob = (freq+1)/(len(series)+MAX_NUMBER)

    last_seen = {i:-1 for i in range(1,MAX_NUMBER+1)}
    for idx,val in enumerate(series):
        last_seen[val] = idx

    gaps = pd.Series([len(series)-last_seen[i] for i in range(1,MAX_NUMBER+1)],
                     index=range(1,MAX_NUMBER+1))

    gap_z = pd.Series(zscore(gaps), index=gaps.index)
    gap_norm = (gap_z-gap_z.min())/(gap_z.max()-gap_z.min())

    momentum = series.iloc[-50:].value_counts().reindex(range(1,MAX_NUMBER+1),fill_value=0)
    momentum_prob = momentum/50

    final = 0.4*freq_prob + 0.3*momentum_prob + 0.3*gap_norm
    return final, gaps

# ==========================================
# SIDEBAR INPUT
# ==========================================

st.sidebar.header("📂 Data Input")
mode = st.sidebar.radio("Select Input Method", ["Upload File","Paste Data","Load From Database"])

bonus_series = None

# ---- Upload ----
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
                st.error("Could not auto-detect Bonus column.")
                st.stop()

            bonus_series = pd.to_numeric(df[bonus_col], errors="coerce").dropna().astype(int)
            bonus_series = bonus_series[bonus_series.between(1,MAX_NUMBER)]

            main_numbers = df.drop(columns=[bonus_col])
            main_numbers = main_numbers.apply(pd.to_numeric, errors="coerce")

            db_df = pd.DataFrame({
                "draw_date": pd.Timestamp.now(),
                "numbers": main_numbers.astype(str).agg(",".join, axis=1),
                "bonus": bonus_series
            })

            save_to_db(db_df)

            st.success(f"Loaded {len(bonus_series)} draws & saved to DB.")

        except Exception as e:
            st.error(f"Error: {e}")

# ---- Paste ----
elif mode == "Paste Data":
    text = st.sidebar.text_area("Paste Bonus Numbers (one per line)")
    if text:
        nums = [int(x.strip()) for x in text.split() if x.strip().isdigit()]
        bonus_series = pd.Series(nums)
        bonus_series = bonus_series[bonus_series.between(1,MAX_NUMBER)]
        st.success(f"Loaded {len(bonus_series)} entries.")

# ---- Load DB ----
elif mode == "Load From Database":
    df = load_from_db()
    if not df.empty:
        bonus_series = df["bonus"]
        st.success(f"Loaded {len(bonus_series)} draws from DB.")

# ==========================================
# MANUAL DRAW TRIGGER (NEW)
# ==========================================

st.sidebar.header("🎯 Manual Draw Trigger")
manual_nums_input = st.sidebar.text_input(
    "Enter 6 main numbers separated by commas",
    value=""
)

if manual_nums_input:
    try:
        manual_list = [int(x.strip()) for x in manual_nums_input.split(",") if x.strip().isdigit()]
        if len(manual_list) != 6:
            st.sidebar.error("Please enter exactly 6 numbers.")
            manual_list = None
        else:
            manual_list = pd.Series(manual_list)
    except Exception as e:
        st.sidebar.error(f"Invalid input: {e}")
        manual_list = None
else:
    manual_list = None

# ==========================================
# MAIN ENGINE
# ==========================================

if bonus_series is not None and len(bonus_series) > 100:

    tab1, tab2, tab3 = st.tabs(["🔮 Prediction","📊 Trend","🧪 Backtest"])

    # -------- PREDICTION --------
    with tab1:
        st.subheader("Automatic Bonus Prediction (Historical + Hybrid)")
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

        # -------- MANUAL TRIGGER --------
        if manual_list is not None:
            st.subheader("Manual Draw Trigger Bonus Prediction")
            df_history = load_from_db()
            df_history["numbers_list"] = df_history["numbers"].str.split(",")

            match_bonus = []
            for idx, row in df_history.iterrows():
                draw_nums = set(int(x) for x in row["numbers_list"])
                match_count = len(draw_nums.intersection(set(manual_list)))
                if match_count >= 3:  # minimum 3 matching numbers to trigger
                    match_bonus.append(row["bonus"])

            if match_bonus:
                match_series = pd.Series(match_bonus)
                scores, gaps = advanced_scores(match_series)
                matrix = build_transition_matrix(match_series)
                last = match_series.iloc[-1]
                markov_probs = monte_carlo(matrix,last)
                hybrid = 0.6*scores + 0.4*markov_probs
                top5 = hybrid.nlargest(5)

                cols = st.columns(5)
                for i,(num,val) in enumerate(top5.items()):
                    with cols[i]:
                        st.metric(f"Rank {i+1}", f"#{num}", f"{val*100:.2f}%")
                        st.caption(f"Gap: {int(gaps[num])}")
            else:
                st.info("No historical draws match your input sufficiently to generate predictions.")

    # -------- TREND --------
    with tab2:
        df_plot = pd.DataFrame({
            "Number":gaps.index,
            "Gap":gaps.values
        })
        fig = px.bar(df_plot,x="Number",y="Gap",title="Overdue Pressure Index")
        st.plotly_chart(fig,use_container_width=True)

    # -------- BACKTEST --------
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
