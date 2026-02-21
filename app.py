import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import re
import os

DB_PATH = "v5_draws.db"

# ==========================================
# DATABASE SETUP
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY,
            numbers TEXT,
            bonus INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM draws", conn)
    conn.close()
    return df

# ==========================================
# SAFE NUMBER PARSER (FIXES V3 FLOAT ERROR)
# ==========================================
def safe_int(x):
    try:
        return int(float(str(x).strip()))
    except:
        return None

# ==========================================
# CLEAN MANUAL INPUT (SPACES OR COMMAS)
# ==========================================
def parse_manual_input(text):
    parts = re.split(r"[,\s]+", text.strip())
    nums = [safe_int(p) for p in parts if safe_int(p) is not None]
    return nums

# ==========================================
# SELF-LEARNING FREQUENCY MODEL
# ==========================================
def train_model(history):
    freq = {}
    bonus_freq = {}

    for _, row in history.iterrows():
        nums = row["numbers"].split(",")
        for n in nums:
            n = safe_int(n)
            if n:
                freq[n] = freq.get(n, 0) + 1

        b = safe_int(row["bonus"])
        if b:
            bonus_freq[b] = bonus_freq.get(b, 0) + 1

    return freq, bonus_freq

def generate_prediction(freq, bonus_freq):
    sorted_nums = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    sorted_bonus = sorted(bonus_freq.items(), key=lambda x: x[1], reverse=True)

    top6 = [n for n, _ in sorted_nums[:6]]
    bonus = sorted_bonus[0][0] if sorted_bonus else None

    return top6, bonus

# ==========================================
# START APP
# ==========================================
init_db()

st.title("🔥 SIDIAN DELTA V5")
st.write("Self-Learning Engine + Clean Upload + Manual Testing")

# ==========================================
# SIDEBAR UPLOAD
# ==========================================
with st.sidebar:
    st.header("📂 Upload Draw History")

    file = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])

    if file:
        df_new = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        st.write("Preview:", df_new.head())

        if st.button("Commit to Database"):

            m_cols = df_new.columns[:6]
            b_col = df_new.columns[6] if len(df_new.columns) > 6 else None

            cleaned = pd.DataFrame()

            cleaned["numbers"] = df_new[m_cols].apply(
                lambda row: ",".join(
                    str(safe_int(x)) for x in row if safe_int(x) is not None
                ),
                axis=1
            )

            if b_col:
                cleaned["bonus"] = df_new[b_col].apply(safe_int)
            else:
                cleaned["bonus"] = None

            cleaned = cleaned.dropna()

            conn = sqlite3.connect(DB_PATH)
            cleaned.to_sql("draws", conn, if_exists="replace", index=False)
            conn.close()

            st.success(f"{len(cleaned)} rows committed successfully!")
            st.rerun()

# ==========================================
# MAIN PANEL
# ==========================================
history = get_history()

st.subheader("📊 Database Status")
st.write(f"Stored Draws: {len(history)}")

if len(history) > 0:
    freq, bonus_freq = train_model(history)

    st.subheader("🧠 Generate Prediction")
    if st.button("Run V5 Engine"):
        numbers, bonus = generate_prediction(freq, bonus_freq)
        st.success(f"Predicted Numbers: {numbers}")
        st.success(f"Predicted Bonus: {bonus}")

    # ==========================================
    # MANUAL BACKTEST INPUT
    # ==========================================
    st.subheader("🧪 Manual Backtest")

    manual_input = st.text_input(
        "Enter 6 numbers + bonus (spaces or commas allowed)",
        placeholder="5 12 19 27 33 41 9"
    )

    if manual_input:
        parsed = parse_manual_input(manual_input)

        if len(parsed) < 7:
            st.warning("Enter at least 6 numbers + 1 bonus")
        else:
            test_nums = parsed[:6]
            test_bonus = parsed[6]

            predicted_nums, predicted_bonus = generate_prediction(freq, bonus_freq)

            match_count = len(set(test_nums) & set(predicted_nums))
            bonus_match = (test_bonus == predicted_bonus)

            st.write(f"Matches: {match_count}/6")
            st.write(f"Bonus Match: {bonus_match}")
else:
    st.info("Upload draw history to activate V5 engine.")
