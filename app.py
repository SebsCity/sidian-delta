import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="Sidian Decision Matrix", layout="wide", page_icon="🎯")
st.title("🎯 Sidian Bonus Decision Matrix")
st.caption("Hybrid Intelligence: Theory vs. Decay vs. Ripple Analysis")

MAX_NUMBER = 49 # Standard UK49s / SA Lotto
DB_PATH = "database/draws.db"

# ==========================================
# CORE ENGINES
# ==========================================
def get_analysis_data(history_df, main_input):
    m_set = sorted([int(x) for x in main_input.split() if x.isdigit()])
    bonus_series = history_df['bonus'].astype(int)
    
    # 1. HARMONIC BALANCE (Mean Sync)
    # The "Gravity" of the set.
    avg = np.mean(m_set)
    harmonic_candidates = [int(round(avg - 1)), int(round(avg)), int(round(avg + 1))]
    harmonic_candidates = [n for n in harmonic_candidates if 1 <= n <= MAX_NUMBER]

    # 2. OVERDUE FACTOR (Decay)
    # The "Elasticity" - which numbers are due to snap?
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series[::-1]):
        if 1 <= val <= MAX_NUMBER and last_seen[val] == -1:
            last_seen[val] = len(bonus_series) - idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))
    top_overdue = gaps.nlargest(5).index.tolist()

    # 3. RIPPLE SPLITS (Lead-Lag)
    # What usually follows the LAST drawn bonus ball?
    last_bonus = int(bonus_series.iloc[0]) # Assuming newest first
    splits = []
    for i in range(len(history_df) - 1):
        if int(history_df.iloc[i+1]['bonus']) == last_bonus:
            nums = [int(float(x)) for x in str(history_df.iloc[i]['numbers']).split(',') if x != 'nan']
            splits.extend(nums)
    
    top_splits = pd.Series(splits).value_counts().head(5).index.tolist() if splits else []

    # 4. NEIGHBOR/GAP SYNTHESIS (The Hybrid Top 3)
    # This is the logic that caught #22 earlier.
    scores = pd.Series(0.0, index=range(1, MAX_NUMBER + 1))
    for x in m_set:
        for offset in [-1, 0, 1]:
            if 1 <= x+offset <= MAX_NUMBER: scores[x+offset] += 1.5
    
    diffs = [m_set[i+1] - m_set[i] for i in range(len(m_set)-1)]
    if diffs:
        max_idx = np.argmax(diffs)
        for n in range(m_set[max_idx]+1, m_set[max_idx+1]): scores[n] += 1.2
        
    hybrid_top3 = scores.nlargest(3).index.tolist()

    return {
        "hybrid": hybrid_top3,
        "harmonic": harmonic_candidates,
        "overdue": top_overdue,
        "splits": top_splits,
        "gaps": gaps
    }

# ==========================================
# UI & DATABASE
# ==========================================
if not os.path.exists(DB_PATH):
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, bonus INTEGER)")
    conn.close()

with st.sidebar:
    st.header("📂 Data Master")
    uploaded = st.file_uploader("Upload 'A Lister' Sheet", type=["xlsx", "csv"])
    if uploaded:
        df_new = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
        if st.button("Sync & Overwrite"):
            m_cols = [c for c in df_new.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
            b_col = [c for c in df_new.columns if 'bonus' in c.lower()][0]
            db_ready = pd.DataFrame()
            db_ready['numbers'] = df_new[m_cols].astype(str).agg(','.join, axis=1)
            db_ready['bonus'] = df_new[b_col].astype(int)
            conn = sqlite3.connect(DB_PATH)
            db_ready.to_sql("draws", conn, if_exists="replace", index=True, index_label="id")
            conn.close()
            st.success("History Synced!")
            st.rerun()

# MAIN INTERFACE
conn = sqlite3.connect(DB_PATH)
history = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
conn.close()

if history.empty:
    st.info("Please upload your data sheet in the sidebar.")
else:
    st.subheader("🔮 Step 1: Input Current Draw (The 6 Main Numbers)")
    user_input = st.text_input("Spaces Only:", placeholder="e.g. 2 5 9 13 21 28")

    if user_input:
        analysis = get_analysis_data(history, user_input)
        
        st.divider()
        st.header("📋 The Sidian Decision Matrix")
        st.write("Review the categories below. Look for **overlapping** numbers to identify the strongest play.")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.info("🚀 **Hybrid Top 3**")
            st.write("Best Neighbor/Gap match.")
            for n in analysis['hybrid']:
                st.subheader(f"#{n}")

        with c2:
            st.success("⚖️ **Harmonic Balance**")
            st.write("Balance points of the set.")
            for n in analysis['harmonic']:
                st.subheader(f"#{n}")

        with c3:
            st.warning("⏳ **Overdue Factor**")
            st.write("Highest 'Decay' pressure.")
            for n in analysis['overdue'][:3]: # Top 3 overdue
                st.subheader(f"#{n}")

        with c4:
            st.error("🌊 **Ripple Splits**")
            st.write("Follows the last Bonus.")
            for n in analysis['splits'][:3]:
                st.subheader(f"#{n}")

        st.divider()
        st.subheader("📊 Overdue Heatmap (Decay Status)")
        gaps = analysis['gaps']
        fig = px.bar(x=gaps.index, y=gaps.values, color=gaps.values, color_continuous_scale='Reds', labels={'x':'Ball', 'y':'Draws Since Seen'})
        st.plotly_chart(fig, use_container_width=True)
