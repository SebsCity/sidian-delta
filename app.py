import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Sidian Automaton", layout="wide")

# --- SESSION STATE (To keep manual data alive) ---
if 'manual_draws' not in st.session_state:
    st.session_state.manual_draws = []

def get_numbers(row):
    """Extract numbers from a row regardless of column names"""
    cols = [c for c in row.index if str(c).startswith('N') or c == 'Bonus']
    return [int(x) for x in row[cols] if pd.notnull(x) and isinstance(x, (int, float))]

# --- SIDEBAR: DATA LOADER ---
with st.sidebar:
    st.header("1. Upload History")
    uploaded_file = st.file_uploader("Upload Excel/CSV", type=['xlsx', 'csv'])
    
    st.header("2. Manual Injector")
    st.caption("Add missing draws here:")
    with st.form("add_draw"):
        m_date = st.date_input("Date", datetime.today())
        m_nums = st.text_input("Numbers (e.g. 5,18,24,36,41,48,20)")
        submit_m = st.form_submit_button("Inject Draw")
        
        if submit_m and m_nums:
            try:
                n_list = [int(x.strip()) for x in m_nums.split(',')]
                if len(n_list) >= 6:
                    entry = {'Date': pd.Timestamp(m_date)}
                    for i in range(6): entry[f'N{i+1}'] = n_list[i]
                    if len(n_list) > 6: entry['Bonus'] = n_list[6]
                    st.session_state.manual_draws.append(entry)
                    st.success("Draw Added!")
                else:
                    st.error("Enter at least 6 numbers.")
            except:
                st.error("Invalid format. Use commas.")

    if st.session_state.manual_draws:
        if st.button("Clear Manual Data"):
            st.session_state.manual_draws = []
            st.rerun()

st.title("🎱 Sidian Automaton: 3D Logic Engine")

# --- MAIN LOGIC ---
if uploaded_file or st.session_state.manual_draws:
    # 1. Load Data
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
    else:
        df = pd.DataFrame(columns=['Date', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Bonus'])

    # 2. Clean Data
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # 3. Merge Manual Data
    if st.session_state.manual_draws:
        manual_df = pd.DataFrame(st.session_state.manual_draws)
        # Filter dupes
        existing_dates = set(df['Date'].dt.date)
        manual_df = manual_df[~manual_df['Date'].dt.date.isin(existing_dates)]
        df = pd.concat([df, manual_df], ignore_index=True)
    
    df = df.sort_values('Date').reset_index(drop=True)
    last_date = df.iloc[-1]['Date']
    
    st.info(f"System Loaded. Last Data Point: **{last_date.date()}**")

    # --- TAB LAYOUT ---
    tab1, tab2, tab3 = st.tabs(["🔍 The Auto-Scanner", "🗺️ Grid Analysis", "🔭 Deep Dive"])

    with tab1:
        st.subheader("⚠️ High Probability Alerts")
        target_date = st.date_input("Predicting For:", last_date + timedelta(days=1))
        
        candidates = []
        for num in range(1, 50):
            hits = []
            for idx, row in df.iterrows():
                if num in get_numbers(row):
                    hits.append(row['Date'])
            
            if len(hits) >= 3:
                last_hit = hits[-1]
                prev_hit = hits[-2]
                prev_prev = hits[-3]
                
                # Logic Vars
                current_gap = (pd.Timestamp(target_date) - last_hit).days
                last_interval = (last_hit - prev_hit).days
                prev_interval = (prev_hit - prev_prev).days
                
                score = 0
                reason = ""
                
                # PATTERN: Rapid Fire Echo
                if prev_interval > 15 and last_interval <= 6 and current_gap <= 6:
                    score = 95
                    reason = "🔥 Rapid Fire Echo"
                
                # PATTERN: Consistent Rhythm
                elif abs(last_interval - prev_interval) <= 1 and abs(current_gap - last_interval) <= 1:
                    score = 85
                    reason = "🥁 Consistent Rhythm"
                
                # PATTERN: The Accelerator
                elif prev_interval > last_interval and (prev_interval - last_interval) > 1:
                    expected = last_interval - (prev_interval - last_interval)
                    if abs(current_gap - expected) <= 2:
                        score = 80
                        reason = "⚡ Accelerating"
                
                # PATTERN: Overdue Echo (The Straggler)
                if prev_interval > 15 and last_interval <= 5 and current_gap >= 4 and current_gap <= 8:
                    score = 99
                    reason = "⚠️ Critical Straggler"

                if score > 0:
                    candidates.append({'Ball': num, 'Strategy': reason, 'Gap': current_gap, 'Score': score})
        
        if candidates:
            res = pd.DataFrame(candidates).sort_values('Score', ascending=False)
            st.dataframe(res, use_container_width=True)
        else:
            st.write("No critical patterns found for this specific date.")

    with tab2:
        st.subheader("The Empty Zones")
        last_nums = get_numbers(df.iloc[-1])
        grid = np.zeros((7, 7))
        for n in last_nums:
            if 1 <= n <= 49:
                r, c = (n-1)//7, (n-1)%7
                grid[r, c] = 1
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("Last Draw Matrix (1=Hit, 0=Empty)")
            st.write(grid)
        with col_g2:
            empty_rows = [r+1 for r in range(7) if sum(grid[r, :]) == 0]
            st.error(f"**Target Rows:** {empty_rows}")
            st.caption("These rows are completely empty. Expect fillers here.")

    with tab3:
        st.subheader("Single Number Trajectory")
        t_num = st.number_input("Check Number:", 1, 49, 40)
        hits = []
        for idx, row in df.iterrows():
            nums = get_numbers(row)
            if t_num in nums:
                pos = nums.index(t_num) + 1
                hits.append({'Date': row['Date'], 'Pos': pos})
        
        if hits:
            tdf = pd.DataFrame(hits)
            tdf['Prev'] = tdf['Date'].shift(1)
            tdf['Interval'] = (tdf['Date'] - tdf['Prev']).dt.days
            st.table(tdf[['Date', 'Pos', 'Interval']].tail(5))
        else:
            st.warning("No recent history.")

else:
    st.info("Upload your history file to start.")
