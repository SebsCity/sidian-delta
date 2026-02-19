import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG & SESSION STATE
# ==========================================
st.set_page_config(page_title="Sidian Bonus Lab PRO", layout="wide", page_icon="🚀")

# Initialize Session State to keep data across refreshes
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

st.title("🎯 Sidian Bonus Lab PRO")
st.caption("Synchronized Hybrid Engine: History + Manual Trigger")

MAX_NUMBER = 49
DB_PATH = "database/draws.db"

# ==========================================
# DATABASE LOGIC
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY AUTOINCREMENT, numbers TEXT, bonus INTEGER)")
    conn.commit()
    conn.close()

init_db()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT numbers, bonus FROM draws", conn)
    conn.close()
    return df

# ==========================================
# CALCULATION ENGINE
# ==========================================
def run_prediction_engine(history_df, manual_input_str):
    # 1. Clean Bonus Data for Stats
    bonus_series = pd.to_numeric(history_df['bonus'], errors='coerce').dropna().astype(int)
    
    # 2. Base Stats (Frequency + Decay)
    freq = bonus_series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_s = (freq - freq.min()) / (freq.max() - freq.min()) if freq.max() > freq.min() else freq
    
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER: last_seen[val] = idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))
    gap_s = (gaps - gaps.min()) / (gaps.max() - gaps.min()) if gaps.max() > gaps.min() else gaps
    
    # 3. Correlation (Buddy System)
    current_draw = [int(x) for x in manual_input_str.split() if x.isdigit()]
    buddy_weights = pd.Series(0.0, index=range(1, MAX_NUMBER+1))
    
    for row in history_df.itertuples():
        hist_nums = [int(float(x)) for x in str(row.numbers).split(',') if x != 'nan']
        match_count = len(set(current_draw).intersection(set(hist_nums)))
        if match_count > 0:
            buddy_weights[int(row.bonus)] += (match_count ** 2)
    
    buddy_s = (buddy_weights / buddy_weights.max()) if buddy_weights.max() > 0 else buddy_weights
    
    # 4. Final Weighted Rank
    final_score = (0.70 * buddy_s) + (0.20 * gap_s) + (0.10 * freq_s)
    return final_score.nlargest(3), gaps

# ==========================================
# MAIN UI
# ==========================================
col_data, col_pred = st.columns([1, 2])

with col_data:
    st.subheader("📁 1. Load Data")
    file = st.file_uploader("Upload History (Excel/CSV)", type=["xlsx", "csv"])
    
    if file:
        df_new = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        if st.button("Commit to Sidian Database"):
            conn = sqlite3.connect(DB_PATH)
            # Make sure your Excel has 'Main_1' to 'Main_6' and 'Bonus'
            df_new['numbers'] = df_new[['Main_1','Main_2','Main_3','Main_4','Main_5','Main_6']].astype(str).agg(','.join, axis=1)
            df_new[['numbers', 'Bonus']].to_sql("draws", conn, if_exists="replace", index=False)
            conn.close()
            st.session_state.data_loaded = True
            st.success("Database Ready!")

with col_pred:
    st.subheader("🔮 2. Prediction Hub")
    history = get_history()
    
    if history.empty:
        st.info("Awaiting data upload...")
    else:
        st.write(f"Analyzing {len(history)} historical draws.")
        
        with st.form("prediction_form"):
            manual_input = st.text_input("Paste Current Main Draw (Spaces only):", placeholder="e.g. 5 12 23 34 41 47")
            run_btn = st.form_submit_button("Generate Top 3 Bonuses")
            
            if run_btn:
                if manual_input:
                    top3, current_gaps = run_prediction_engine(history, manual_input)
                    
                    st.divider()
                    st.write("### 🎯 Predicted Bonus Sequence")
                    res_cols = st.columns(3)
                    for i, (num, val) in enumerate(top3.items()):
                        with res_cols[i]:
                            st.metric(f"Rank {i+1}", f"#{num}")
                            st.progress(min(val, 1.0))
                            st.caption(f"Gap: {current_gaps[num]} draws")
                else:
                    st.error("Please enter the main draw numbers.")

# ==========================================
# VISUALS
# ==========================================
if not history.empty:
    st.divider()
    _, gaps = run_prediction_engine(history, "0") # Dummy input just for gaps
    fig = px.bar(x=gaps.index, y=gaps.values, color=gaps.values, color_continuous_scale='Reds', title="Overdue Pressure Index")
    st.plotly_chart(fig, use_container_width=True)
