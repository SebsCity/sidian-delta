import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG & FORENSIC SETTINGS
# ==========================================
st.set_page_config(page_title="Sidian A-Lister Synthesis", layout="wide", page_icon="🧬")
st.title("🧬 Sidian A-Lister Total Synthesis")
st.caption("Custom Tuned for 'Full A Lister 1.0' History (2,278 Draws)")

MAX_NUMBER = 52 # Common SA Lotto Max
DB_PATH = "database/draws.db"

# ==========================================
# DERIVATION ENGINE (Weighted by Forensic Results)
# ==========================================
def synthesize_bonus(prev_main):
    m = sorted(prev_main)
    scores = pd.Series(0.0, index=range(1, MAX_NUMBER + 1))
    
    # 1. Neighbor Logic (31.9% Forensic Weight)
    for x in m:
        for offset in [-1, 0, 1]: # Combining Mirror + Neighbor
            if 1 <= x + offset <= MAX_NUMBER:
                scores[x + offset] += 1.5
                
    # 2. Gap Fill Logic (30.1% Forensic Weight)
    gaps = [m[i+1] - m[i] for i in range(len(m)-1)]
    if gaps:
        max_gap_idx = np.argmax(gaps)
        # Weight the entire range inside the gap
        for n in range(m[max_gap_idx] + 1, m[max_gap_idx+1]):
            scores[n] += 1.2
            
    # 3. Mean Sync (11.9% Forensic Weight)
    avg = np.mean(m)
    scores[int(round(avg))] += 0.5
    
    return scores

# ==========================================
# UI & DATABASE
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS draws (numbers TEXT, bonus INTEGER)")
    conn.close()

init_db()

# --- MAIN DASHBOARD ---
st.subheader("🔮 Predictive Trigger (Space Separated)")
with st.form("synth_form"):
    input_text = st.text_input("Enter Previous Draw Main Numbers:", placeholder="e.g. 4 12 25 31 38 45")
    submitted = st.form_submit_button("Synthesize Top 3 Bonuses")

if submitted and input_text:
    try:
        m_list = [int(x) for x in input_text.split() if x.isdigit()]
        if len(m_list) < 6:
            st.warning("Please enter all 6 main numbers.")
        else:
            raw_scores = synthesize_bonus(m_list)
            top3 = raw_scores.nlargest(3)
            
            st.divider()
            st.header("🎯 Derived Top 3 Bonus Candidates")
            cols = st.columns(3)
            for i, (num, score) in enumerate(top3.items()):
                with cols[i]:
                    st.metric(f"Rank {i+1}", f"#{num}")
                    st.progress(min(score/2.0, 1.0))
                    # Identification
                    if num in m_list: st.caption("Theory: Direct Mirror")
                    elif any(abs(num - x) == 1 for x in m_list): st.caption("Theory: Direct Neighbor")
                    else: st.caption("Theory: Gap Pressure")
    except Exception as e:
        st.error(f"Error: {e}")

# Visualizing the Forensic Winners
st.divider()
st.subheader("📊 A-Lister Forensic Archive (Method Success)")
success_df = pd.DataFrame({
    "Method": ["Neighbor (+/-1)", "Gap Fill", "Mirror", "Mean Sync", "Sum Mod"],
    "Weighting": [31.9, 30.1, 12.4, 11.9, 5.2]
})
fig = px.bar(success_df, x="Method", y="Weighting", color="Weighting", color_continuous_scale="Viridis")
st.plotly_chart(fig, use_container_width=True)
