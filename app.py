import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG & SESSION STATE
# ==========================================
st.set_page_config(page_title="Sidian Decision Matrix", layout="wide", page_icon="🎯")

# Custom CSS for the Sidian "Gold" Highlighting
st.markdown("""
    <style>
    .gold-box {
        background-color: #FFD700;
        color: #000;
        padding: 10px;
        border-radius: 10px;
        border: 2px solid #DAA520;
        text-align: center;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .standard-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

MAX_NUMBER = 49 # Standard UK49s / SA Lotto
DB_PATH = "database/draws.db"

# ==========================================
# DATABASE & STORAGE
# ==========================================
def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, bonus INTEGER)")
    conn.close()

init_db()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
    conn.close()
    return df

# ==========================================
# ANALYTICS ENGINES
# ==========================================
def calculate_matrix(history_df, main_input):
    # Convert input to sorted list
    m_set = sorted([int(x) for x in main_input.split() if x.isdigit()])
    if len(m_set) < 1: return None
    
    bonus_series = history_df['bonus'].astype(int)
    
    # 1. HYBRID ENGINE (Neighbor + Gap Fill)
    hybrid_scores = pd.Series(0.0, index=range(1, MAX_NUMBER + 1))
    for x in m_set:
        for offset in [-1, 0, 1]:
            if 1 <= x+offset <= MAX_NUMBER: hybrid_scores[x+offset] += 1.5
    
    diffs = [m_set[i+1] - m_set[i] for i in range(len(m_set)-1)]
    if diffs:
        max_idx = np.argmax(diffs)
        for n in range(m_set[max_idx]+1, m_set[max_idx+1]): hybrid_scores[n] += 1.2
    hybrid_top = hybrid_scores.nlargest(5).index.tolist()

    # 2. HARMONIC BALANCE (Mathematical Center)
    avg = np.mean(m_set)
    harmonic = [int(round(avg - 1)), int(round(avg)), int(round(avg + 1))]
    harmonic = [n for n in harmonic if 1 <= n <= MAX_NUMBER]

    # 3. OVERDUE FACTOR (Decay Analysis)
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series[::-1]):
        if 1 <= val <= MAX_NUMBER: last_seen[val] = len(bonus_series) - idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))
    overdue = gaps.nlargest(5).index.tolist()

    # 4. RIPPLE SPLITS (Historical Aftershocks)
    last_bonus = int(bonus_series.iloc[0])
    splits = []
    for i in range(len(history_df) - 1):
        if int(history_df.iloc[i+1]['bonus']) == last_bonus:
            nums = [int(float(x)) for x in str(history_df.iloc[i]['numbers']).split(',') if x != 'nan']
            splits.extend(nums)
    ripple = pd.Series(splits).value_counts().head(5).index.tolist() if splits else []

    return {
        "Hybrid": hybrid_top,
        "Harmonic": harmonic,
        "Overdue": overdue,
        "Ripple": ripple,
        "Gaps": gaps
    }

# ==========================================
# MAIN UI
# ==========================================
st.title("🎯 Sidian Decision Matrix PRO")
st.caption("Strategic Decision Engine for Professional Analytics")

history = get_history()

with st.sidebar:
    st.header("⚙️ Sidian Data Sync")
    file = st.file_uploader("Upload 'A Lister' Sheet", type=["xlsx", "csv"])
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
            st.success("History Synced Successfully!")
            st.rerun()

# --- PREDICTION INTERFACE ---
if history.empty:
    st.info("👋 Welcome! Please upload your data sheet in the sidebar to begin.")
else:
    st.subheader("🔮 Input Recent Draw (The Trigger)")
    user_input = st.text_input("Enter 6 Main Numbers (Spaces only):", placeholder="e.g. 2 5 9 13 21 28")

    if user_input:
        results = calculate_matrix(history, user_input)
        
        if results:
            st.divider()
            st.header("📋 The Decision Matrix")
            st.write("Numbers appearing in **GOLD** are overlapping across multiple theories.")
            
            # Identify Overlaps
            all_nums = results["Hybrid"] + results["Harmonic"] + results["Overdue"] + results["Ripple"]
            counts = pd.Series(all_nums).value_counts()
            gold_list = counts[counts > 1].index.tolist()

            cols = st.columns(4)
            headers = ["🚀 Hybrid Engine", "⚖️ Harmonic Balance", "⏳ Overdue Factor", "🌊 Ripple Splits"]
            keys = ["Hybrid", "Harmonic", "Overdue", "Ripple"]

            for i, col in enumerate(cols):
                with col:
                    st.markdown(f"### {headers[i]}")
                    for n in results[keys[i]]:
                        if n in gold_list:
                            st.markdown(f'<div class="gold-box">#{n} (GOLD)</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="standard-box">#{n}</div>', unsafe_allow_html=True)

            # --- DECAY VISUAL ---
            st.divider()
            st.subheader("📊 Overdue Heatmap (Pressure Index)")
            gaps = results["Gaps"]
            fig = px.bar(x=gaps.index, y=gaps.values, color=gaps.values, color_continuous_scale='Reds',
                         labels={'x':'Ball Number', 'y':'Draws Since Seen'})
            st.plotly_chart(fig, use_container_width=True)

            # --- FORENSIC HISTORY ---
            with st.expander("View Forensic Archive"):
                st.dataframe(history.head(10), use_container_width=True)
