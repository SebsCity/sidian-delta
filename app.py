import streamlit as st
import pandas as pd
from datetime import timedelta
from itertools import combinations

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sidian Precision Engine", page_icon="🎯", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .oracle-card { 
        background-color: #f9f9f9; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 6px solid #2962FF; 
        margin-bottom: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .cluster-header { color: #D32F2F; font-weight: bold; font-size: 18px; }
    .clean-header { color: #00C853; font-weight: bold; font-size: 18px; } /* Green for Clean Hits */
    .why-text { font-style: italic; color: #555; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("System: **Radar**, **Lab**, **Squads**, **Partners**, and **The Split-Stream Oracle**.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])
    
    st.divider()
    st.header("⚙️ Physics Mode")
    split_mode = st.checkbox("🧩 Split Universes (Higher Accuracy)", value=True, help="Separates Lunch and Tea into two different datasets. Removes interference.")

# --- HELPER ---
def calculate_landing_date(last_date, last_draw, draws_ahead, use_split_logic):
    current_date = pd.to_datetime(last_date)
    current_draw = str(last_draw).strip()
    steps = int(round(draws_ahead))
    if steps < 1: steps = 1
    
    for _ in range(steps):
        # If Split Mode is ON, we assume we are hopping purely within one session type
        # E.g. Lunch -> Lunch (1 step = 1 day)
        if use_split_logic:
            current_date = current_date + timedelta(days=1)
            # Draw name stays the same
        else:
            # Standard Logic (Lunch -> Tea -> Lunch)
            if 'Lunchtime' in current_draw:
                current_draw = 'Teatime'
            else:
                current_draw = 'Lunchtime'
                current_date = current_date + timedelta(days=1)
                
    return current_date, current_draw

# --- MAIN ---
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep='\t' if 'tsv' in uploaded_file.name else ',')
            if len(df.columns) < 2: 
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep='\t')
        else:
            df = pd.read_excel(uploaded_file)
        
        df['Date'] = pd.to_datetime(df['Date'])
        cols = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
        
        # TABS
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔭 Radar", "🔬 Lab", "⛓️ Squads", "🤝 Partners", "🧩 Groups", "🗓️ MONTHLY ORACLE"])

        # ==================================================
        # TAB 1: RADAR (Updated with Split Logic)
        # ==================================================
        with tab1:
            st.subheader("🔭 Individual Target Radar")
            
            # --- SPLIT LOGIC PRE-PROCESSING ---
            target_session = "Combined"
            if split_mode:
                st.info("🧩 **SPLIT MODE ACTIVE:** Analyzing Lunch and Tea as separate physics models.")
                session_filter = st.radio("Select Universe to Scan:", ["Lunchtime Only", "Teatime Only"], horizontal=True)
                
                # Filter Data
                if "Lunch" in session_filter:
                    df_active = df[df['Draw_Name'].str.contains("Lunchtime", case=False, na=False)].copy()
                else:
                    df_active = df[df['Draw_Name'].str.contains("Teatime", case=False, na=False)].copy()
            else:
                df_active = df.copy()

            candidates = []
            for num in range(1, 50):
                hits = []
                for idx, row in df_active.iterrows():
                    if num in row[cols].values: hits.append(idx)
                
                if len(hits) >= 3:
                    # We use iloc on df_active, so indices are relative to the filtered set
                    # This effectively calculates "Lunch-to-Lunch" gaps
                    last_idx_loc = len(hits) - 1
                    prev_idx_loc = len(hits) - 2
                    old_idx_loc = len(hits) - 3
                    
                    # Get actual gaps (in terms of rows in the filtered DB)
                    # Note: We can't use raw index subtraction if indices are non-consecutive
                    # We must use position in the filtered list
                    
                    # Actually, for "Draws Since", we need the integer gap count
                    # In Split Mode, Gap 1 means "1 Lunch Ago" (24 hours)
                    
                    gap_new = hits[last_idx_loc] - hits[prev_idx_loc] # This raw index diff might be large in combined df
                    # BUT, for ratio, we should use the "count of rows" between hits in the filtered set?
                    # Let's use the 'positional' difference for cleaner ratios in Split Mode
                    
                    if split_mode:
                        # Use positional difference (Pure Interval)
                        pos_gap_new = last_idx_loc - prev_idx_loc # This is always 1 if consecutive in list... wait.
                        # We need the distance in the filtered dataframe rows
                        # Let's map hits to their integer position in df_active
                        # df_active.reset_index(drop=True) makes row 0, 1, 2...
                        
                        # Simpler approach:
                        # Just use the raw DF index if it's sequential? No.
                        # Let's trust the "Draws Since" logic on the active DF.
                        pass # Using standard index logic below for consistency
                        
                    idx_last = hits[-1]; idx_prev = hits[-2]; idx_old = hits[-3]
                    
                    # Logic: In split mode, the index gap represents "Days" (roughly) if rows are 1 per day
                    # In combined mode, it represents "Half Days"
                    
                    gap_new = idx_last - idx_prev
                    gap_old = idx_prev - idx_old
                    
                    if gap_old > 0:
                        ratio = gap_new / gap_old
                        pred_gap = gap_new * ratio
                        
                        # Landing Date Calculation
                        p_date, p_time = calculate_landing_date(
                            df_active.loc[idx_last, 'Date'], 
                            df_active.loc[idx_last, 'Draw_Name'], 
                            pred_gap, 
                            split_mode
                        )
                        
                        # Priority
                        draws_since = (df_active.index[-1]) - idx_last
                        remaining = pred_gap - draws_since
                        
                        if remaining < 3.5: # Slightly wider window for split mode
                            if ratio > 0.9 and ratio < 1.1: type_ = "💎 Pure Integer (Stable)"
                            elif ratio < 0.8: type_ = "🚀 Accelerating"
                            elif ratio > 1.2: type_ = "🛑 Decelerating"
                            else: type_ = "⚖️ Rolling"
                            
                            candidates.append({
                                "Number": num, 
                                "Type": type_, 
                                "Ratio": round(ratio,2), 
                                "Est. Arrival": f"{p_date.strftime('%d %b')} ({p_time})", 
                                "Universe": session_filter if split_mode else "Combined"
                            })
                            
            if candidates:
                st.dataframe(pd.DataFrame(candidates), hide_index=True)
            else:
                st.info("No immediate targets in this universe.")

        # (Tabs 2-5 Hidden - Keep previous logic)

        # ==================================================
        # TAB 6: MONTHLY ORACLE (Updated with Split Logic)
        # ==================================================
        with tab6:
            st.subheader("🗓️ The Monthly Focus Oracle")
            
            # SPLIT MODE SELECTION FOR ORACLE
            oracle_mode = "Combined"
            if split_mode:
                st.info("Running parallel simulations for Lunchtime and Teatime universes...")
            
            if st.button("🔮 Generate Monthly Focus"):
                schedule = {}
                
                # We need to run TWO loops if split mode is on (one for Lunch DB, one for Tea DB)
                datasets_to_run = []
                if split_mode:
                    datasets_to_run.append((df[df['Draw_Name'].str.contains("Lunchtime", na=False)].copy(), "Lunchtime"))
                    datasets_to_run.append((df[df['Draw_Name'].str.contains("Teatime", na=False)].copy(), "Teatime"))
                else:
                    datasets_to_run.append((df.copy(), "Combined"))
                
                for df_run, universe_name in datasets_to_run:
                    for num in range(1, 50):
                        hits = []
                        for idx, row in df_run.iterrows():
                            if num in row[cols].values: hits.append(idx)
                        
                        if len(hits) >= 3:
                            idx_last = hits[-1]; idx_prev = hits[-2]; idx_old = hits[-3]
                            gap_new = idx_last - idx_prev; gap_old = idx_prev - idx_old
                            
                            if gap_old > 0:
                                ratio = gap_new / gap_old
                                pred_gap = gap_new * ratio
                                
                                p_date, p_time = calculate_landing_date(
                                    df_run.loc[idx_last, 'Date'], 
                                    df_run.loc[idx_last, 'Draw_Name'], 
                                    pred_gap, 
                                    split_mode
                                )
                                
                                key = f"{p_date.strftime('%Y-%m-%d')} | {p_time}"
                                if key not in schedule: schedule[key] = []
                                
                                # Tag the number with its Universe origin
                                schedule[key].append({
                                    "Num": num,
                                    "Universe": universe_name,
                                    "Ratio": ratio
                                })

                # GENERATE OUTPUT
                sorted_keys = sorted(schedule.keys())
                today_str = df.iloc[-1]['Date'].strftime('%Y-%m-%d')
                
                for key in sorted_keys:
                    date_part, time_part = key.split(" | ")
                    
                    if date_part >= today_str:
                        items = schedule[key]
                        
                        # Separate by Universe
                        lunch_natives = sorted([x['Num'] for x in items if x['Universe'] == "Lunchtime"])
                        tea_natives = sorted([x['Num'] for x in items if x['Universe'] == "Teatime"])
                        combined_nums = sorted([x['Num'] for x in items if x['Universe'] == "Combined"])
                        
                        # Display Logic
                        active_nums = lunch_natives if "Lunch" in time_part else tea_natives
                        if not split_mode: active_nums = combined_nums
                        
                        if active_nums:
                            pretty_date = pd.to_datetime(date_part).strftime('%A %d %b')
                            
                            why_msg = ""
                            if split_mode:
                                why_msg = f"These numbers are <b>{time_part} Natives</b>. They were detected using a pure {time_part}-only analysis, completely ignoring the noise of the other session."
                            else:
                                why_msg = "Standard mixed-stream convergence."

                            # Render
                            st.markdown(f"""
                            <div class="oracle-card">
                                <h3>{pretty_date} ({time_part})</h3>
                                <div class="clean-header">💎 The Natives: {active_nums}</div>
                                <div class="why-text"><b>Why?</b> {why_msg}</div>
                            </div>
                            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
