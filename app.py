import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px

# ==========================================
# CONFIG & THEME
# ==========================================
st.set_page_config(page_title="Sidian 28-Ball Precision", layout="wide", page_icon="🎯")
st.title("🎯 Sidian 28-Ball Precision Predictor")
st.caption("Automated Exclusion + Bayesian Scoring | 2026 Forensic Calibration")

MAX_NUMBER = 49
ANCHOR = 28

# ==========================================
# CORE ENGINES
# ==========================================
def identify_exclusion_pool(df):
    """Identifies the unique numbers from the last 3 draws (Top 3 rows)."""
    # Assuming standard A-Lister format (Main_1 to Main_6 and Bonus)
    m_cols = [c for c in df.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
    b_col = [c for c in df.columns if 'bonus' in c.lower()][0]
    
    last_3 = df.head(3)
    all_recent = []
    for _, row in last_3.iterrows():
        all_recent.extend([int(float(row[c])) for c in m_cols])
        all_recent.append(int(float(row[b_col])))
    
    unique_excluded = set([n for n in all_recent if 1 <= n <= MAX_NUMBER])
    return unique_excluded

def get_best_candidate(available_pool, latest_main, history_df):
    """Ranks the pool to find the single best 'Likely Candidate'."""
    scores = pd.Series(0.0, index=available_pool)
    m = sorted(latest_main)
    
    # 1. Neighbor Logic (+1/-1 Pressure)
    for x in m:
        for offset in [-1, 1]:
            n = x + offset
            if n in scores.index: scores[n] += 2.0
            
    # 2. Gap Filling (Physical Balancing)
    gaps = [m[i+1] - m[i] for i in range(len(m)-1)]
    if gaps:
        max_idx = np.argmax(gaps)
        for n in range(m[max_idx]+1, m[max_idx+1]):
            if n in scores.index: scores[n] += 1.5
            
    # 3. Decay Pressure (Long-term due)
    bonus_col = history_df.columns[-1]
    bonus_hist = history_df[bonus_col].dropna().astype(int).tolist()
    last_seen = {i: 999 for i in available_pool}
    for idx, val in enumerate(bonus_hist):
        if val in last_seen and last_seen[val] == 999:
            last_seen[val] = idx
    
    for n in available_pool:
        scores[n] += (last_seen[n] / 50.0) # More weight for longer absence

    return scores.idxmax(), scores.nlargest(5)

# ==========================================
# MAIN INTERFACE
# ==========================================
st.sidebar.header("📂 Data Integration")
file = st.sidebar.file_uploader("Upload 'A Lister' CSV/Excel", type=["csv", "xlsx"])

if file:
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    
    # 1. Automatic Exclusion
    excluded = identify_exclusion_pool(df)
    pool_28 = sorted(list(set(range(1, 50)) - excluded))
    
    # 2. Prediction Prep
    m_cols = [c for c in df.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
    latest_main = [int(float(x)) for x in df.iloc[0][m_cols]]
    
    best_one, top_ranks = get_best_candidate(pool_28, latest_main, df)

    # UI Columns
    col_main, col_stats = st.columns([1, 1])

    with col_main:
        st.header("🏆 The Likely Candidate")
        st.markdown(f"""
            <div style="background-color:#FFD700; padding:30px; border-radius:15px; text-align:center;">
                <h1 style="color:black; font-size:80px; margin:0;">#{best_one}</h1>
                <p style="color:black; font-size:20px;">Highest Probability from the 28-Pool</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("🔥 Top 5 Heat-Rank")
        for num, score in top_ranks.items():
            st.write(f"Ball **#{num}** | Score: {score:.2f}")
            st.progress(min(score/5.0, 1.0))

    with col_stats:
        st.header("📊 Current State")
        st.metric("Excluded (The 21)", len(excluded))
        st.metric("Targeted (The 28)", len(pool_28))
        
        # Displaying the 21 unique numbers excluded
        st.write("**Recently Drawn (Excluded):**")
        st.write(f"*{', '.join(map(str, sorted(list(excluded))))}*")

    # 3. Precision Sets (Anchored on 28)
    st.divider()
    st.header("🚀 Generated Precision Sets (Anchored on 28)")
    sets = []
    while len(sets) < 3:
        weights = [5.0 if n == best_one else 10.0 if n == ANCHOR else 1.0 for n in pool_28]
        sample = sorted(list(set(random.choices(pool_28, weights=weights, k=10))))
        if ANCHOR in sample:
            final = sample[:6]
            if len(final) == 6 and final not in sets:
                sets.append(final)
    
    cols = st.columns(3)
    for i, s in enumerate(sets):
        with cols[i]:
            st.markdown(f"**Set {chr(65+i)}**")
            st.write(", ".join(map(str, s)))

else:
    st.info("💡 Upload your history file to exclude the last 21 numbers and identify the #1 likely candidate.")
