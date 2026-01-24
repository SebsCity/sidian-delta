import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from itertools import combinations

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sidian Precision Engine", page_icon="🎯", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .oracle-date { color: #6200EA; font-size: 22px; font-weight: bold; }
    .collision { background-color: #FFEBEE; padding: 10px; border-radius: 5px; border-left: 5px solid #FF1744; }
    .normal { background-color: #F1F8E9; padding: 10px; border-radius: 5px; border-left: 5px solid #00C853; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("System: **Radar**, **Lab**, **Squads**, **Partners**, **Groups**, and **The Universal Oracle**.")

# --- SIDEBAR: DATA LOADER ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])

# --- HELPER FUNCTION: DATE PREDICTOR ---
def calculate_landing_date(last_date, last_draw, draws_ahead):
    current_date = pd.to_datetime(last_date)
    current_draw = str(last_draw).strip()
    steps = int(round(draws_ahead))
    
    # If steps is 0 or negative (Overdue), we default to "NEXT DRAW" concept internally
    # But for calculation, we project forward
    if steps < 1: steps = 1
    
    for _ in range(steps):
        if 'Lunchtime' in current_draw:
            current_draw = 'Teatime'
        else:
            current_draw = 'Lunchtime'
            current_date = current_date + timedelta(days=1)
            
    return current_date, current_draw

# --- MAIN SYSTEM ---
if uploaded_file:
    try:
        # 1. LOAD DATA
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep='\t' if 'tsv' in uploaded_file.name else ',')
            if len(df.columns) < 2: 
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep='\t')
        else:
            df = pd.read_excel(uploaded_file)
        
        df['Date'] = pd.to_datetime(df['Date'])
        cols = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
        
        # 2. CREATE TABS
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🔭 Radar", 
            "🔬 Lab", 
            "⛓️ Squads", 
            "🤝 Partners",
            "🧩 Group Scan",
            "🔮 UNIVERSAL ORACLE"
        ])

        # ==================================================
        # TAB 1: RADAR
        # ==================================================
        with tab1:
            st.subheader("🔭 Individual Target Radar")
            candidates = []
            for num in range(1, 50):
                hits = []
                for idx, row in df.iterrows():
                    if num in row[cols].values: hits.append(idx)
                
                if len(hits) >= 3:
                    idx_last = hits[-1]; idx_prev = hits[-2]; idx_old = hits[-3]
                    gap_new = idx_last - idx_prev; gap_old = idx_prev - idx_old
                    if gap_old > 0:
                        ratio = gap_new / gap_old
                        pred_gap = gap_new * ratio
                        idx_due = idx_last + pred_gap
                        draws_remaining = idx_due - (len(df)-1)
                        
                        if draws_remaining < 2.5:
                            if ratio < 0.8: type_, prio = "🚀 Accelerating", 1
                            elif ratio > 1.2: type_, prio = "🛑 Decelerating", 2
                            elif ratio > 4.0: type_, prio = "💤 Sleeper", 1
                            else: type_, prio = "⚖️ Rolling", 3
                            
                            p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                            candidates.append({"Number": num, "Type": type_, "Ratio": round(ratio,2), "Est. Arrival": f"{p_date.strftime('%d %b')} ({p_time})", "Priority": prio})
            if candidates:
                st.dataframe(pd.DataFrame(candidates).sort_values('Priority'), hide_index=True, use_container_width=True)
            else:
                st.info("No immediate impact vectors found.")

        # ==================================================
        # TAB 2: LAB
        # ==================================================
        with tab2:
            st.subheader("🔬 Single Number Audit")
            target = st.number_input("Enter Number:", 1, 49, 49)
            hits = []
            for idx, row in df.iterrows():
                if target in row[cols].values: hits.append(idx)
            if len(hits) >= 3:
                idx_last = hits[-1]; idx_prev = hits[-2]; idx_old = hits[-3]
                gap_new = idx_last - idx_prev; gap_old = idx_prev - idx_old
                ratio = gap_new / gap_old if gap_old > 0 else 0
                pred_gap = gap_new * ratio
                p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                st.success(f"Target: {p_date.strftime('%d %b')} - {p_time}")

        # ==================================================
        # TAB 3: SQUADS
        # ==================================================
        with tab3:
            st.subheader("⛓️ Squad & Cluster Detection")
            recent_draws = df.tail(15)
            squads = []
            for idx, row in recent_draws.iterrows():
                draw_nums = [x for x in row[cols].values if x > 0]
                combos = list(combinations(draw_nums, 3))
                for squad in combos:
                    s_stat = {'Members': squad, 'Origin': f"{row['Date'].strftime('%d %b')}", 'Returned': [], 'Missing': []}
                    future = df.loc[idx+1:]
                    for m in squad:
                        if any(m in r[cols].values for _, r in future.iterrows()): s_stat['Returned'].append(m)
                        else: s_stat['Missing'].append(m)
                    if len(s_stat['Returned']) >= 2 and len(s_stat['Missing']) > 0: squads.append(s_stat)
            if squads:
                for s in squads:
                    st.error(f"🚨 CLUSTER: {s['Members']} (Origin: {s['Origin']})")
                    st.write(f"✅ Returned: {s['Returned']} | 🔥 **MISSING:** {s['Missing']}")

        # ==================================================
        # TAB 4: PARTNERS
        # ==================================================
        with tab4:
            st.subheader("🤝 The Partner Protocol")
            l_input = st.text_input("Enter Lunchtime Numbers:", "")
            if l_input:
                try:
                    lunch_nums = [int(x) for x in l_input.split() if x.isdigit()]
                    bet_slip = []
                    for scout in lunch_nums:
                        hits = []
                        for idx, row in df.iterrows():
                            if scout in row[cols].values: hits.append(idx)
                        if len(hits) >= 1:
                            last_idx = hits[-1]; last_row = df.iloc[last_idx]
                            partners = [x for x in last_row[cols].values if x != scout and x > 0]
                            if partners:
                                bet_slip.append({"Scout": scout, "Last_Seen": last_row['Date'].strftime('%Y-%m-%d'), "Partner": partners[0]})
                    if bet_slip:
                        st.dataframe(pd.DataFrame(bet_slip))
                        st.code(pd.DataFrame(bet_slip).to_csv(sep='\t', index=False), language='text')
                except: pass

        # ==================================================
        # TAB 5: GROUP SCAN
        # ==================================================
        with tab5:
            st.subheader("🧩 Group Scan")
            g_input = st.text_input("Enter Duo/Triple:", "")
            if g_input:
                try:
                    target_group = [int(x) for x in g_input.split() if x.isdigit()]
                    joint_hits = []
                    for idx, row in df.iterrows():
                        if set(target_group).issubset(set(row[cols].values)): joint_hits.append(idx)
                    if len(joint_hits) >= 3:
                        gap_new = joint_hits[-1] - joint_hits[-2]
                        gap_old = joint_hits[-2] - joint_hits[-3]
                        ratio = gap_new / gap_old if gap_old > 0 else 1
                        pred_gap = gap_new * ratio
                        p_date, p_time = calculate_landing_date(df.iloc[joint_hits[-1]]['Date'], df.iloc[joint_hits[-1]]['Draw_Name'], pred_gap)
                        st.success(f"💎 GROUP TARGET: **{p_date.strftime('%d %b')} ({p_time})**")
                    else: st.warning("Not enough joint history.")
                except: pass

        # ==================================================
        # TAB 6: THE UNIVERSAL ORACLE (New!)
        # ==================================================
        with tab6:
            st.subheader("🔮 The Universal Oracle (Flight Schedule)")
            st.markdown("Calculates the Physics Trajectory for **ALL 49 NUMBERS** and groups them by their **Due Date**.")
            
            if st.button("🔮 Generate Flight Schedule"):
                
                # Dictionary to hold the schedule: Key = "YYYY-MM-DD Time", Value = List of Numbers
                schedule = {}
                meta_data = {} # Stores details for tooltips
                
                # 1. SCAN ALL NUMBERS
                for num in range(1, 50):
                    hits = []
                    for idx, row in df.iterrows():
                        if num in row[cols].values: hits.append(idx)
                    
                    if len(hits) >= 3:
                        idx_last = hits[-1]
                        idx_prev = hits[-2]
                        idx_old = hits[-3]
                        
                        gap_new = idx_last - idx_prev
                        gap_old = idx_prev - idx_old
                        
                        if gap_old > 0:
                            ratio = gap_new / gap_old
                            pred_gap = gap_new * ratio
                            
                            # Calculate Date
                            p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                            
                            # Create Key
                            date_key = f"{p_date.strftime('%Y-%m-%d')} | {p_time}"
                            
                            # Add to Schedule
                            if date_key not in schedule:
                                schedule[date_key] = []
                            
                            schedule[date_key].append(num)
                            
                            # Store Meta Data
                            meta_data[num] = {
                                "Ratio": ratio,
                                "Type": "Accelerating" if ratio < 0.8 else "Decelerating" if ratio > 1.2 else "Rolling"
                            }
                
                # 2. DISPLAY RESULTS (Sorted by Date)
                sorted_keys = sorted(schedule.keys())
                
                # Filter out past dates (Keep today and future)
                today_str = df.iloc[-1]['Date'].strftime('%Y-%m-%d')
                
                st.divider()
                
                for key in sorted_keys:
                    date_part, time_part = key.split(" | ")
                    
                    # Simple string comparison for filtering "Future/Today"
                    if date_part >= today_str:
                        nums = schedule[key]
                        count = len(nums)
                        
                        # VISUAL LOGIC
                        if count >= 3:
                            style_class = "collision"
                            icon = "🔥 CRITICAL CONVERGENCE"
                        else:
                            style_class = "normal"
                            icon = "🗓️ Schedule"
                            
                        # Pretty Date
                        pretty_date = pd.to_datetime(date_part).strftime('%A %d %b')
                        
                        st.markdown(f"""
                        <div class="{style_class}">
                            <div class="oracle-date">{icon}: {pretty_date} ({time_part})</div>
                            Due Numbers: <b>{nums}</b>
                        </div>
                        <br>
                        """, unsafe_allow_html=True)
                        
                        # Expander for details
                        with st.expander(f"View Physics Details for {pretty_date} ({time_part})"):
                            det_cols = st.columns(len(nums))
                            for i, n in enumerate(nums):
                                info = meta_data[n]
                                with det_cols[i % 3]: # Wrap cols
                                    st.write(f"**#{n}**")
                                    st.caption(f"{info['Type']}")
                                    st.caption(f"Ratio: {info['Ratio']:.2f}")

    except Exception as e:
        st.error(f"System Error: {e}")

else:
    st.info("Waiting for Data Feed...")
