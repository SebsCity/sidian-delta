import streamlit as st
import pandas as pd
import numpy as np
import random
import sqlite3
import os

# ==========================================
# CONFIG & CACHING
# ==========================================
st.set_page_config(page_title="Sidian Strategic Pro", layout="wide", page_icon="⚡")

# Custom Styles
st.markdown("""
    <style>
    .gold-card { background: linear-gradient(135deg, #ffecb3 0%, #ffc107 100%); border-radius: 10px; padding: 20px; color: #000; text-align: center; border: 2px solid #daa520; }
    .sticky-card { background-color: #fdf6e3; border-left: 5px solid #b58900; padding: 15px; border-radius: 5px; }
    .elite-card { background-color: #e3f2fd; border-left: 5px solid #007bff; padding: 15px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

DB_PATH = "database/draws.db"
MAX_NUMBER = 49

# ==========================================
# DATABASE & DATA UTILS
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, bonus INTEGER)")
    conn.close()

init_db()

@st.cache_data
def get_cached_history():
    """Loads history from DB and caches it for speed."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
    conn.close()
    return df

# ==========================================
# OPTIMIZED FORENSIC ENGINES
# ==========================================
@st.cache_data
def perform_forensic_scan(df):
    """Heavy calculation for Sticky vs Elite logic."""
    if len(df) < 5: return None, None, None
    
    # 1. Extraction (Last 3 Draws = The 21)
    last_3 = df.head(3)
    excluded_list = []
    for _, row in last_3.iterrows():
        m_nums = [int(x) for x in str(row['numbers']).split(',') if x.isdigit()]
        excluded_list.extend(m_nums + [int(row['bonus'])])
    
    u21 = set(excluded_list)
    a28 = sorted(list(set(range(1, MAX_NUMBER + 1)) - u21))

    # 2. Stickiness Analysis (Scanning up to last 1000 draws for speed)
    sticky_scores = {n: 0 for n in u21}
    scan_limit = min(len(df), 1000)
    
    for i in range(scan_limit - 1):
        curr = set([int(x) for x in str(df.iloc[i]['numbers']).split(',') if x.isdigit()] + [int(df.iloc[i]['bonus'])])
        prev = set([int(x) for x in str(df.iloc[i+1]['numbers']).split(',') if x.isdigit()] + [int(df.iloc[i+1]['bonus'])])
        repeats = curr.intersection(prev)
        for n in repeats:
            if n in sticky_scores: sticky_scores[n] += 1
    
    top_sticky = pd.Series(sticky_scores).nlargest(3)

    # 3. Elite 4 Synthesis (Neighbors & Gaps)
    latest_main = sorted([int(x) for x in str(df.iloc[0]['numbers']).split(',') if x.isdigit()])
    elite_scores = pd.Series(0.0, index=a28)
    
    for x in latest_main:
        for offset in [-1, 1]:
            if (x + offset) in elite_scores.index: elite_scores[x+offset] += 2.0
            
    # Gap Logic
    gaps = [latest_main[i+1] - latest_main[i] for i in range(len(latest_main)-1)]
    if gaps:
        max_idx = np.argmax(gaps)
        for n in range(latest_main[max_idx]+1, latest_main[max_idx+1]):
            if n in elite_scores.index: elite_scores[n] += 1.5
            
    top_elite = elite_scores.nlargest(4)

    return u21, top_sticky, top_elite

# ==========================================
# MAIN INTERFACE
# ==========================================
st.title("⚡ Sidian Strategic Pro")
st.caption("Optimized Forensic Engine | Stickiness vs. Elite Logic")

history = get_cached_history()

with st.sidebar:
    st.header("📂 Data Center")
    uploaded = st.file_uploader("Upload 'A Lister' Sheet", type=["xlsx", "csv"])
    
    if uploaded:
        if st.button("🔄 Sync & Refresh Engine"):
            df_new = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
            # Find columns
            all_cols = df_new.columns.tolist()
            m_cols = [c for c in all_cols if any(w in c.lower() for w in ['main', 'num', 'ball'])][:6]
            b_col = [c for c in all_cols if 'bonus' in c.lower() or 'b' == c.lower().strip()][0]
            
            db_ready = pd.DataFrame()
            db_ready['numbers'] = df_new[m_cols].astype(str).agg(','.join, axis=1)
            db_ready['bonus'] = pd.to_numeric(df_new[b_col], errors='coerce')
            
            conn = sqlite3.connect(DB_PATH)
            db_ready.to_sql("draws", conn, if_exists="replace", index=True, index_label="id")
            conn.close()
            
            st.cache_data.clear() # IMPORTANT: Clears the cache for the new data
            st.success("Sync Complete!")
            st.rerun()

# --- THE FORENSIC DASHBOARD ---
if history.empty:
    st.info("👋 Welcome to Sidian Pro. Upload your history in the sidebar to activate the Forensic Engine.")
else:
    u21, sticky, elite = perform_forensic_scan(history)
    
    # 🌟 THE GOLD CHECK: Overlapping numbers
    overlaps = set(sticky.index).intersection(set(elite.index))
    
    if overlaps:
        st.markdown(f'<div class="gold-card"><h3>✨ HIGH CONVICTION ALERT</h3><p>The following numbers hit both Sticky and Elite patterns:</p><h1>{", ".join(["#"+str(x) for x in overlaps])}</h1></div>', unsafe_allow_html=True)
        st.divider()

    col_1, col_2 = st.columns(2)

    with col_1:
        st.markdown('<div class="sticky-card"><h3>🔄 Top 3 Sticky Repeaters</h3><p>Excluded pool (The 21) analysis.</p></div>', unsafe_allow_html=True)
        for num, val in sticky.items():
            st.subheader(f"#{num}")
            st.caption(f"Stickiness Score: {val} back-to-back repeats")

    with col_2:
        st.markdown('<div class="elite-card"><h3>🌟 The Elite 4 Fresh</h3><p>Available pool (The 28) analysis.</p></div>', unsafe_allow_html=True)
        for num, val in elite.items():
            st.subheader(f"#{num}")
            st.caption(f"Synthesis Strength: {int(val*20)}%")

    st.divider()
    with st.expander("🔍 View Current Exclusion List"):
        st.write(f"**Excluded 21:** {sorted(list(u21))}")
