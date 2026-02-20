import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG & SESSION STATE
# ==========================================
st.set_page_config(page_title="Sidian A-Lister Synthesis", layout="wide", page_icon="🧬")

st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #007bff; }
    .main-header { font-size: 32px; font-weight: bold; color: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)

MAX_NUMBER = 49 # Set to 52 or 58 if using different Lotto variations
DB_PATH = "database/draws.db"

# ==========================================
# DATABASE & DATA CLEANING
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, bonus INTEGER)")
    conn.close()

init_db()

def load_local_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
    conn.close()
    return df

# ==========================================
# FORENSIC LOGIC: PILLAR CALCULATORS
# ==========================================
def check_pillars(prev_main, curr_bonus):
    """Detects which mathematical theory matches the bonus ball."""
    m = sorted([int(float(x)) for x in prev_main if str(x).lower() != 'nan'])
    if not m: return {}
    
    results = {
        "Neighbor": any(abs(curr_bonus - x) <= 1 for x in m),
        "Mirror": curr_bonus in m,
        "Mean_Sync": abs(np.mean(m) - curr_bonus) <= 3,
        "Gap_Fill": False
    }
    
    # Gap Fill Calculation
    gaps = [m[i+1] - m[i] for i in range(len(m)-1)]
    if gaps:
        max_gap_idx = np.argmax(gaps)
        if m[max_gap_idx] < curr_bonus < m[max_gap_idx+1]:
            results["Gap_Fill"] = True
            
    return results

# ==========================================
# THE PREDICTION ENGINE
# ==========================================
def run_synthesis(history_df, current_m_input):
    if len(history_df) < 10:
        return None, None, "Need at least 10 draws in history."

    # 1. Forensic Phase: Identify which theory is currently winning
    theory_hits = {"Neighbor": 0, "Mirror": 0, "Mean_Sync": 0, "Gap_Fill": 0}
    draws_analyzed = 0
    
    # Analyze history (Draw N Bonus vs Draw N-1 Main Set)
    for i in range(len(history_df)-1):
        curr_b = int(history_df.iloc[i]['bonus'])
        prev_m = history_df.iloc[i+1]['numbers'].split(',')
        hits = check_pillars(prev_m, curr_b)
        for k, v in hits.items():
            if v: theory_hits[k] += 1
        draws_analyzed += 1

    # Calculate success rates
    winning_theory = max(theory_hits, key=theory_hits.get)
    
    # 2. Synthesis Phase: Apply winning logic to the current input
    m_input = sorted([int(x) for x in current_m_input.split() if x.isdigit()])
    if len(m_input) < 6:
        return None, None, "Please enter all 6 main numbers."

    scores = pd.Series(0.0, index=range(1, MAX_NUMBER + 1))
    for num in range(1, MAX_NUMBER + 1):
        test_hits = check_pillars(m_input, num)
        # Apply weights based on forensic success
        if test_hits["Neighbor"]: scores[num] += 1.5
        if test_hits["Gap_Fill"]: scores[num] += 1.2
        if test_hits["Mirror"]: scores[num] += 1.0
        if test_hits["Mean_Sync"]: scores[num] += 0.5
    
    # 3. Gap Analysis (Decay)
    bonus_series = history_df['bonus'].astype(int)
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series[::-1]): # Oldest to newest
        if 1 <= val <= MAX_NUMBER: last_seen[val] = len(bonus_series) - idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))

    return scores.nlargest(3), theory_hits, gaps

# ==========================================
# MAIN INTERFACE
# ==========================================
st.title("🧬 Sidian Total Synthesis Lab")
st.caption("Forensic Analysis & Prediction Engine for the A-Lister Dataset")

history = load_local_history()

tabs = st.tabs(["🔮 Synthesis Hub", "📊 Forensic Analysis", "📁 Data Management"])

with tabs[0]:
    if history.empty:
        st.info("👋 Welcome! Please go to the 'Data Management' tab and upload your Excel sheet to activate the engine.")
    else:
        st.subheader("Step 1: Input Previous Draw Main Set")
        st.write("Paste the 6 main numbers from the draw immediately before the one you want to predict.")
        
        with st.form("synth_form"):
            user_m = st.text_input("Main Numbers (Spaces Only):", placeholder="e.g. 2 5 9 13 21 28")
            btn = st.form_submit_button("Synthesize Top 3 Bonuses")
            
            if btn:
                top3, theory_stats, current_gaps = run_synthesis(history, user_m)
                if top3 is not None:
                    st.divider()
                    st.header("🎯 Predicted Top 3 Candidates")
                    c1, c2, c3 = st.columns(3)
                    cols = [c1, c2, c3]
                    
                    for i, (num, val) in enumerate(top3.items()):
                        with cols[i]:
                            st.metric(f"Rank {i+1}", f"#{num}")
                            st.progress(min(val/2.0, 1.0))
                            st.caption(f"Pressure: {current_gaps[num]} draws overdue")
                else:
                    st.error(theory_stats)

with tabs[1]:
    st.header("Machine Signature: Forensic Review")
    if not history.empty:
        _, stats, _ = run_synthesis(history, "1 2 3 4 5 6") # Dummy call for stats
        
        df_stats = pd.DataFrame({"Method": stats.keys(), "Hits": stats.values()})
        df_stats['Success Rate (%)'] = (df_stats['Hits'] / len(history) * 100).round(1)
        
        col_chart, col_data = st.columns([2, 1])
        with col_chart:
            fig = px.bar(df_stats, x="Method", y="Success Rate (%)", color="Method", title="Winning Derivation Theories")
            st.plotly_chart(fig, use_container_width=True)
        with col_data:
            st.write("**Forensic Conclusion:**")
            winning = df_stats.loc[df_stats['Hits'].idxmax(), 'Method']
            st.success(f"The machine is currently in a **{winning}** cycle. High priority given to this logic.")

with tabs[2]:
    st.header("Data Management")
    uploaded_file = st.file_uploader("Upload 'Full A Lister' Excel", type=["xlsx", "csv"])
    
    if uploaded_file:
        df_new = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        st.write("Preview of Upload:", df_new.head(3))
        
        if st.button("Overwrite Database & Sync History"):
            # Ensure columns are present
            try:
                # Combining Main_1 to Main_6
                m_cols = [c for c in df_new.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
                b_col = [c for c in df_new.columns if 'bonus' in c.lower()][0]
                
                # Format for DB
                db_ready = pd.DataFrame()
                db_ready['numbers'] = df_new[m_cols].astype(str).agg(','.join, axis=1)
                db_ready['bonus'] = df_new[b_col].astype(int)
                
                conn = sqlite3.connect(DB_PATH)
                db_ready.to_sql("draws", conn, if_exists="replace", index=True, index_label="id")
                conn.close()
                st.success("History Synced! You can now use the Synthesis Hub.")
                st.rerun()
            except Exception as e:
                st.error(f"Format Error: Ensure columns are named 'Main_1...6' and 'Bonus'. Error: {e}")
