import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG & UI
# ==========================================
st.set_page_config(page_title="Sidian 28-Ball Engine", layout="wide", page_icon="🎯")
st.title("🎯 Sidian 28-Ball Precision Engine")
st.caption("Automated Exclusion + Forensic Synthesis | Professional Grade")

MAX_NUMBER = 49
ANCHOR = 28

# ==========================================
# CORE ANALYTICS FUNCTIONS
# ==========================================
def identify_exclusion_pool(df):
    """Extracts unique numbers from the last 3 rows (Last 21 balls)."""
    # Assuming the file is sorted newest to oldest. 
    # If oldest to newest, we take df.tail(3)
    last_3 = df.head(3) 
    
    # Identify main and bonus columns
    m_cols = [c for c in df.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
    b_col = [c for c in df.columns if 'bonus' in c.lower()][0]
    
    all_recent = []
    for _, row in last_3.iterrows():
        nums = [int(float(row[c])) for c in m_cols] + [int(float(row[b_col]))]
        all_recent.extend(nums)
        
    return set(all_recent), last_3

def score_pool(available_pool, latest_draw_nums, history_df):
    """Determines the 4 strongest candidates using Sidian Synthesis."""
    scores = pd.Series(0.0, index=available_pool)
    m = sorted(latest_draw_nums)
    
    # 1. Neighbor Logic (+/- 1)
    for x in m:
        for offset in [-1, 1]:
            n = x + offset
            if n in scores.index: scores[n] += 1.5
            
    # 2. Gap Fill Logic
    gaps = [m[i+1] - m[i] for i in range(len(m)-1)]
    if gaps:
        max_idx = np.argmax(gaps)
        for n in range(m[max_idx]+1, m[max_idx+1]):
            if n in scores.index: scores[n] += 1.2
            
    # 3. Decay/Overdue Pressure
    bonus_history = history_df.iloc[:, -1].astype(int) # Assuming last col is bonus
    last_seen = {i: 999 for i in available_pool}
    for idx, val in enumerate(bonus_history):
        if val in last_seen and last_seen[val] == 999:
            last_seen[val] = idx
    
    for n in available_pool:
        pressure = last_seen[n] / 100.0 # Normalized pressure
        scores[n] += min(pressure, 1.0)

    return scores.nlargest(4)

# ==========================================
# MAIN APP INTERFACE
# ==========================================
st.sidebar.header("📂 Data Integration")
file = st.sidebar.file_uploader("Upload 'Full A Lister' Dataset", type=["csv", "xlsx"])

if file:
    # 1. Load Data
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    
    # 2. Automated Exclusion
    excluded_set, last_3_df = identify_exclusion_pool(df)
    full_pool = set(range(1, 50))
    available_pool = sorted(list(full_pool - excluded_set))
    
    # Display Exclusion Results
    st.sidebar.success(f"Excluded {len(excluded_set)} unique balls from last 3 draws.")
    st.sidebar.write("The 28-Ball Pool is active.")

    # 3. Determine Elite 4 Candidates
    # Use the VERY latest draw as the trigger for Synthesis
    latest_m_cols = [c for c in df.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
    latest_main = [int(float(x)) for x in df.iloc[0][latest_m_cols]]
    
    elite_4 = score_pool(available_pool, latest_main, df)
    
    # UI Layout
    col_elite, col_sets = st.columns([1, 2])
    
    with col_elite:
        st.header("🌟 The Elite 4")
        st.write("Strongest candidates from the 28-pool based on current machine signature.")
        for num, score in elite_4.items():
            st.metric(f"Candidate #{num}", f"{int(score*20)}% Strength")
            st.progress(min(score/4.0, 1.0))
        
    with col_sets:
        st.header("🚀 Precision Sets (Pick-3 Optimized)")
        
        # Generation Logic
        precision_sets = []
        attempts = 0
        elite_nums = list(elite_4.index)
        
        while len(precision_sets) < 3 and attempts < 2000:
            attempts += 1
            # CDM Weighting: Prioritize Elite 4 + Anchor 28
            weights = []
            for n in available_pool:
                w = 1.0
                if n in elite_nums: w *= 5.0
                if n == ANCHOR: w *= 8.0
                weights.append(w)
            
            sample = random.choices(available_pool, weights=weights, k=10)
            candidate = set(sample)
            candidate.add(ANCHOR)
            
            final_set = sorted(list(candidate))[:6]
            if len(final_set) < 6: continue
            
            # Heuristic Filters
            sum_val = sum(final_set)
            if 120 <= sum_val <= 190 and final_set not in precision_sets:
                precision_sets.append(final_set)
        
        # Display Sets
        s_cols = st.columns(3)
        for i, s in enumerate(precision_sets):
            with s_cols[i]:
                st.subheader(f"Set {chr(65+i)}")
                for val in s:
                    if val in elite_nums: st.markdown(f"🔥 **{val}** (Elite)")
                    elif val == ANCHOR: st.markdown(f"📍 **{val}** (Anchor)")
                    else: st.write(val)
                st.caption(f"Sum: {sum(s)}")

    # Visual Pressure Map
    st.divider()
    st.subheader("📊 28-Pool Pressure Map")
    # Showing all 49, highlighting the 28 available
    pressure_data = []
    for i in range(1, 50):
        status = "Available" if i in available_pool else "Excluded"
        pressure_data.append({"Ball": i, "Status": status})
    
    fig = px.bar(pressure_data, x="Ball", color="Status", 
                 color_discrete_map={"Available": "#007bff", "Excluded": "#e9ecef"},
                 title="Current Exclusion Status (The 21 vs The 28)")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("💡 Please upload your 'Full A Lister' file to automatically exclude the last 21 numbers and generate Elite candidates.")
