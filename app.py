import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os

# ==========================================
# CONFIG & THEME
# ==========================================
st.set_page_config(page_title="Sidian Decision Matrix", layout="wide", page_icon="🎯")

# Professional Sidebar Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border: 1px solid #e6e9ef; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

DB_PATH = "database/draws.db"
MAX_NUMBER = 49 # Adjusted to your draw set

# ==========================================
# DATABASE & CORE ENGINE
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, bonus INTEGER)")
    conn.close()

init_db()

def get_ripple_splits(history_df, target_num):
    """Finds the 3 main numbers most likely to follow a specific bonus."""
    splits = []
    for i in range(len(history_df) - 1):
        if int(history_df.iloc[i+1]['bonus']) == target_num:
            nxt = str(history_df.iloc[i]['numbers']).split(',')
            splits.extend([int(float(x)) for x in nxt if str(x).lower() != 'nan'])
    if splits:
        return pd.Series(splits).value_counts().head(3).index.tolist()
    return ["N/A"]

# ==========================================
# RETRACTABLE SIDEBAR (DATA UPLOAD)
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/data-configuration.png", width=60)
    st.header("Sidian Data Master")
    uploaded_file = st.file_uploader("Upload A-Lister Sheet", type=["xlsx", "csv"])
    
    if uploaded_file:
        df_new = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        if st.button("Overwrite & Sync Database"):
            try:
                m_cols = [c for c in df_new.columns if 'main' in c.lower() or 'num' in c.lower()][:6]
                b_col = [c for c in df_new.columns if 'bonus' in c.lower()][0]
                db_ready = pd.DataFrame()
                db_ready['numbers'] = df_new[m_cols].astype(str).agg(','.join, axis=1)
                db_ready['bonus'] = df_new[b_col].astype(int)
                conn = sqlite3.connect(DB_PATH)
                db_ready.to_sql("draws", conn, if_exists="replace", index=True)
                conn.close()
                st.success("Database Synced!")
                st.rerun()
            except Exception as e:
                st.error(f"Sync Failed: {e}")

# ==========================================
# MAIN INTERFACE: PREDICTION & DECISION
# ==========================================
st.title("🎯 Sidian Decision Matrix")
st.caption("Strategic Analysis of Top 3 Bonus Candidates")

conn = sqlite3.connect(DB_PATH)
history = pd.read_sql("SELECT * FROM draws ORDER BY id DESC", conn)
conn.close()

if history.empty:
    st.warning("👈 Open the left panel and upload your 'Full A Lister' sheet to begin.")
else:
    st.subheader("1. Input Current Draw")
    user_input = st.text_input("Enter 6 Main Numbers (Spaces Only):", placeholder="e.g. 2 5 9 13 21 28")

    if user_input:
        m_list = [int(x) for x in user_input.split() if x.isdigit()]
        if len(m_list) == 6:
            # Stats for Matrix
            h_balance = np.mean(m_list)
            bonus_history = history['bonus'].astype(int)
            
            # Prediction Candidates (Manual Override for your selected Top 3)
            candidates = [13, 14, 20]
            
            st.divider()
            st.header("2. Candidate Decision Matrix")
            cols = st.columns(3)
            
            for i, num in enumerate(candidates):
                with cols[i]:
                    st.metric(f"Candidate Rank {i+1}", f"#{num}")
                    
                    # --- Harmonic Balance ---
                    dist = abs(h_balance - num)
                    balance_pct = max(0, 100 - (dist * 5))
                    st.write(f"**Harmonic Sync:** {balance_pct:.1f}%")
                    st.progress(int(balance_pct)/100)
                    
                    # --- Overdue Factor ---
                    last_idx = bonus_history[bonus_history == num].index
                    gap = (last_idx[0] if not last_idx.empty else len(bonus_history))
                    st.write(f"**Overdue Factor:** {gap} draws")
                    
                    # --- Ripple Splits ---
                    splits = get_ripple_splits(history, num)
                    st.write("**Predicted Ripple Splits:**")
                    st.code(" | ".join(map(str, splits)))
                    
                    st.markdown("---")
                    # Derivation Identification
                    if num in m_list: st.success("Theory: Direct Mirror")
                    elif any(abs(num - x) == 1 for x in m_list): st.info("Theory: Neighbor")
                    else: st.warning("Theory: Gap Fill")

            # Visualizing the Pressure
            st.divider()
            st.subheader("📉 Market Decay (The Overdue Landscape)")
            # Simple bar chart for all candidates
            st.bar_chart(bonus_history.value_counts().head(15))

        else:
            st.error("Please enter exactly 6 main numbers.")
