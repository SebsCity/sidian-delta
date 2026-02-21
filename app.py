import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="Sidian Strategic Engine", layout="wide", page_icon="🧬")

MAX_NUMBER = 49
DB_PATH = "draws.db"

# ==========================================
# DATABASE INIT
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numbers TEXT,
            bonus INTEGER
        )
    """)
    conn.close()

init_db()

# ==========================================
# DATA TRANSFORMATION (EXCEL SAFE)
# ==========================================
def transform_sheet(df):
    """
    Converts Excel sheet into:
    numbers (comma separated string)
    bonus (integer)
    """

    df = df.dropna(how="all")
    df = df.reset_index(drop=True)

    # Identify numeric columns automatically
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 6:
        st.error("Sheet must contain at least 6 numeric columns.")
        st.stop()

    main_cols = numeric_cols[:6]

    bonus_col = numeric_cols[6] if len(numeric_cols) > 6 else None

    formatted = []

    for _, row in df.iterrows():
        mains = [int(row[c]) for c in main_cols if not pd.isna(row[c])]
        if len(mains) == 6:
            bonus = int(row[bonus_col]) if bonus_col else 0
            formatted.append(( ",".join(map(str, mains)), bonus ))

    return formatted

# ==========================================
# ANALYTICS ENGINE
# ==========================================
def analyze_history(df):

    last_3 = df.head(3)

    # --- Extract 21 ---
    excluded = []
    for _, row in last_3.iterrows():
        mains = [int(x) for x in row['numbers'].split(',')]
        excluded.extend(mains + [int(row['bonus'])])

    unique_21 = set(excluded)
    available_28 = sorted(list(set(range(1, MAX_NUMBER + 1)) - unique_21))

    # --- Stickiness ---
    sticky_scores = {n: 0 for n in unique_21}

    for i in range(len(df)-1):
        curr = set(df.iloc[i]['numbers'].split(','))
        curr = set(map(int, curr)) | {int(df.iloc[i]['bonus'])}

        prev = set(df.iloc[i+1]['numbers'].split(','))
        prev = set(map(int, prev)) | {int(df.iloc[i+1]['bonus'])}

        repeats = curr.intersection(prev)

        for n in repeats:
            if n in sticky_scores:
                sticky_scores[n] += 1

    top_sticky = pd.Series(sticky_scores).nlargest(3)

    # --- Elite Logic ---
    latest_main = list(map(int, df.iloc[0]['numbers'].split(',')))
    elite_scores = pd.Series(0.0, index=available_28)

    # Neighbor logic
    for x in latest_main:
        for offset in [-1, 1]:
            if (x + offset) in elite_scores.index:
                elite_scores[x + offset] += 1.5

    # Gap logic
    m = sorted(latest_main)
    gaps = [m[i+1] - m[i] for i in range(len(m)-1)]
    if gaps:
        max_idx = np.argmax(gaps)
        for n in range(m[max_idx]+1, m[max_idx+1]):
            if n in elite_scores.index:
                elite_scores[n] += 1.2

    top_elite = elite_scores.nlargest(4)

    return unique_21, top_sticky, top_elite

# ==========================================
# UI
# ==========================================
st.title("🧬 Sidian Strategic Engine")
st.caption("Android Stable | Excel Compatible | Recursive Forensic Logic")

# ==========================================
# SIDEBAR DATA UPLOAD
# ==========================================
with st.sidebar:
    st.header("📂 Upload Data")

    uploaded = st.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

    if uploaded:
        df_new = pd.read_excel(uploaded) if uploaded.name.endswith(".xlsx") else pd.read_csv(uploaded)

        if st.button("Sync Database"):
            formatted = transform_sheet(df_new)

            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM draws")
            conn.executemany("INSERT INTO draws (numbers, bonus) VALUES (?, ?)", formatted)
            conn.commit()
            conn.close()

            st.success("Database Synced Successfully!")
            st.rerun()

# ==========================================
# LOAD HISTORY
# ==========================================
conn = sqlite3.connect(DB_PATH)
history = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
conn.close()

if history.empty:
    st.info("Upload and sync your sheet to begin.")
else:
    u21, sticky, elite = analyze_history(history)

    st.header("📋 Forensic Recommendation Matrix")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔄 Top 3 Sticky Repeaters")
        for num, hits in sticky.items():
            st.write(f"#{num} — Stickiness: {hits}")

    with col2:
        st.subheader("🌟 Elite 4 Fresh Candidates")
        for num, score in elite.items():
            st.write(f"#{num} — Strength: {int(score*20)}%")

    st.divider()
    st.subheader("📍 21 Exclusion Pool")
    st.write(sorted(list(u21)))
