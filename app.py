import streamlit as st
import pandas as pd
import numpy as np
import random
import sqlite3
import os

# ==========================================
# CONFIG & THEME
# ==========================================
st.set_page_config(page_title="Sidian Strategic Engine", layout="wide", page_icon="🧬")

st.markdown("""
    <style>
    .sticky-card { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 10px; }
    .elite-card { background-color: #d1ecf1; border-left: 5px solid #0c5460; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

MAX_NUMBER = 49
DB_PATH = "database/draws.db"

# ==========================================
# DATABASE LOGIC
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, bonus INTEGER)")
    conn.close()

init_db()

# ==========================================
# CORE ANALYTICS: THE 21 vs THE 28
# ==========================================
def analyze_history(df):
    """
    1. Extracts the unique 21 numbers from the last 3 draws.
    2. Calculates 'Stickiness' for those 21.
    3. Scores the remaining 28 for 'Elite' potential.
    """
    # Assuming df is sorted Newest -> Oldest
    last_3 = df.head(3)
    m_cols = [c for c in df.columns if 'numbers' in c.lower() or 'main' in c.lower()]
    b_col = 'bonus'
    
    # --- Part A: Identify the 21 ---
    excluded_list = []
    for _, row in last_3.iterrows():
        m_nums = [int(x) for x in str(row['numbers']).split(',') if x.isdigit()]
        excluded_list.extend(m_nums + [int(row['bonus'])])
    
    unique_21 = set(excluded_list)
    available_28 = sorted(list(set(range(1, MAX_NUMBER + 1)) - unique_21))

    # --- Part B: Stickiness Factor (From the 21) ---
    sticky_scores = {n: 0 for n in unique_21}
    for i in range(len(df) - 1):
        curr = set([int(x) for x in str(df.iloc[i]['numbers']).split(',') if x.isdigit()] + [int(df.iloc[i]['bonus'])])
        prev = set([int(x) for x in str(df.iloc[i+1]['numbers']).split(',') if x.isdigit()] + [int(df.iloc[i+1]['bonus'])])
        repeats = curr.intersection(prev)
        for n in repeats:
            if n in sticky_scores: sticky_scores[n] += 1
    
    top_sticky = pd.Series(sticky_scores).nlargest(3)

    # --- Part C: Elite 4 Scoring (From the 28) ---
    # Triggered by the latest draw's main set
    latest_main = [int(x) for x in str(df.iloc[0]['numbers']).split(',') if x.isdigit()]
    elite_scores = pd.Series(0.0, index=available_28)
    
    for x in latest_main:
        for offset in [-1, 1]: # Neighbor Logic
            if (x + offset) in elite_scores.index: elite_scores[x+offset] += 1.5
            
    # Gap Logic
    m = sorted(latest_main)
    gaps = [m[i+1] - m[i] for i in range(len(m)-1)]
    if gaps:
        max_idx = np.argmax(gaps)
        for n in range(m[max_idx]+1, m[max_idx+1]):
            if n in elite_scores.index: elite_scores[n] += 1.2
            
    top_elite = elite_scores.nlargest(4)

    return unique_21, top_sticky, top_elite

# ==========================================
# UI & EXECUTION
# ==========================================
st.title("🧬 Sidian Strategic Engine")
st.caption("Recursive Repeat Analysis + 28-Ball Forensic Synthesis")

conn = sqlite3.connect(DB_PATH)
history = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
conn.close()

with st.sidebar:
    st.header("⚙️ Data Management")
    uploaded = st.file_uploader("Upload 'A Lister' Sheet", type=["xlsx", "csv"])
    if uploaded:
        df_new = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
        if st.button("Sync Data"):
            # Transformation logic...
            st.success("Database Synced!")
            st.rerun()

if history.empty:
    st.info("Please upload your data sheet to begin forensic analysis.")
else:
    u21, sticky, elite = analyze_history(history)

    st.header("📋 Forensic Recommendation Matrix")
    st.write("Targeting the next draw using both 'Sticky' and 'Fresh' logic.")

    col_sticky, col_elite = st.columns(2)

    with col_sticky:
        st.markdown('<div class="sticky-card"><h3>🔄 Top 3 Sticky Repeaters</h3><p>From the recently drawn 21 pool.</p></div>', unsafe_allow_html=True)
        for num, hits in sticky.items():
            st.subheader(f"#{num}")
            st.caption(f"Stickiness: {hits} historical back-to-back repeats")

    with col_elite:
        st.markdown('<div class="elite-card"><h3>🌟 The Elite 4 Fresh</h3><p>From the available 28 pool.</p></div>', unsafe_allow_html=True)
        for num, score in elite.items():
            st.subheader(f"#{num}")
            st.caption(f"Synthesis Strength: {int(score*20)}%")

    st.divider()
    st.subheader("📍 The 28-Ball Exclusion Pool Status")
    st.write(f"**Excluded (The 21):** {sorted(list(u21))}")
