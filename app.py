import streamlit as st
import pandas as pd
from datetime import timedelta
from itertools import combinations

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sidian Precision Engine", page_icon="🎯", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .signal { color: #FF4B4B; font-weight: bold; }
    .partner { color: #00C853; font-weight: bold; }
    .oracle { color: #AA00FF; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("Complete System: **Radar**, **Lab**, **Squads**, **Partners**, **Groups**, and **The Oracle**.")

# --- SIDEBAR: DATA LOADER ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])

# --- HELPER FUNCTION: DATE PREDICTOR ---
def calculate_landing_date(last_date, last_draw, draws_ahead):
    current_date = pd.to_datetime(last_date)
    current_draw = str(last_draw).strip()
    steps = int(round(draws_ahead))
    if steps < 1: steps = 1
    
    for _ in range(steps):
        if 'Lunchtime' in current_draw:
            current_draw = 'Teatime'
        else:
            current_draw = 'Lunchtime'
            current_date = current_date + timedelta(days=1)
            
    return current_date.strftime('%d %b %Y'), current_draw

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
            "🔮 THE ORACLE"
        ])

        # ==================================================
        # TAB 1: THE RADAR
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
                    draws_since = (len(df) - 1) - idx_last
                    
                    if gap_old > 0:
                        ratio = gap_new / gap_old
                        pred_gap = gap_new * ratio
                        remaining = pred_gap - draws_since
                        if remaining < 2.5:
                            if ratio < 0.8: type_, prio = "🚀 Accelerating", 1
                            elif ratio > 1.2: type_, prio = "🛑 Decelerating", 2
                            elif ratio > 4.0: type_, prio = "💤 Sleeper", 1
                            else: type_, prio = "⚖️ Rolling", 3
                            p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                            candidates.append({"Number": num, "Type": type_, "Ratio": round(ratio,2), "Est. Arrival": f"{p_date} ({p_time})", "Priority": prio})
            if candidates:
                st.dataframe(pd.DataFrame(candidates).sort_values('Priority'), hide_index=True, use_container_width=True)
            else:
                st.info("No immediate impact vectors found.")

        # ==================================================
        # TAB 2: FORENSIC LAB
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
                st.success(f"Target: {p_date} - {p_time}")

        # ==================================================
        # TAB 3: SQUAD TRACKER
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
            else:
                st.success("No active squad triggers.")

        # ==================================================
        # TAB 4: PARTNER PROTOCOL
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
        # TAB 5: MULTIDIMENSIONAL SCAN
        # ==================================================
        with tab5:
            st.subheader("🧩 Group Scan")
            g_input = st.text_input("Enter Duo/Triple:", "")
            if g_input:
                try:
                    target_group = [int(x) for x in g_input.split() if x.isdigit()]
                    st.write(f"Scanning: {target_group}")
                    # 1. Joint History
                    joint_hits = []
                    for idx, row in df.iterrows():
                        if set(target_group).issubset(set(row[cols].values)): joint_hits.append(idx)
                    if len(joint_hits) >= 3:
                        gap_new = joint_hits[-1] - joint_hits[-2]
                        gap_old = joint_hits[-2] - joint_hits[-3]
                        ratio = gap_new / gap_old if gap_old > 0 else 1
                        pred_gap = gap_new * ratio
                        p_date, p_time = calculate_landing_date(df.iloc[joint_hits[-1]]['Date'], df.iloc[joint_hits[-1]]['Draw_Name'], pred_gap)
                        st.success(f"💎 GROUP TARGET: **{p_date} ({p_time})**")
                    else: st.warning("Not enough joint history.")
                except: pass

        # ==================================================
        # TAB 6: THE ORACLE (New!)
        # ==================================================
        with tab6:
            st.subheader("🔮 The Probability Oracle")
            st.markdown("Generates the **Top 3 Numbers** based on total historical Affinity with the previous draw.")
            
            # Input: Target Date
            target_date_input = st.date_input("Select Target Draw Date:")
            
            if st.button("🔮 Consult the Oracle"):
                st.divider()
                
                # 1. Identify the Trigger (The previous draw)
                # We assume the last row in the file is the 'Previous Draw' relative to prediction
                last_row = df.iloc[-1]
                trigger_nums = [x for x in last_row[cols].values if x > 0]
                
                st.write(f"**Trigger Draw:** {last_row['Date'].strftime('%d %b')} ({last_row['Draw_Name']})")
                st.write(f"**Active Numbers (Scouts):** {trigger_nums}")
                
                # 2. Affinity Calculation
                # For each number 1-49, how many times has it paired with ANY of the trigger numbers?
                affinity_scores = {}
                
                # Initialize
                for n in range(1, 50):
                    affinity_scores[n] = 0
                
                # Scan History
                for idx, row in df.iterrows():
                    row_nums = set(row[cols].values)
                    
                    # Optimization: Only check rows that contain at least one Trigger Number
                    # Intersection check
                    if not row_nums.isdisjoint(set(trigger_nums)):
                        # If a trigger number is present, who else is there?
                        present_triggers = row_nums.intersection(set(trigger_nums))
                        
                        # Weight: If multiple triggers are present, the bond is stronger
                        weight = len(present_triggers) 
                        
                        for num in row_nums:
                            if num > 0 and num not in present_triggers:
                                affinity_scores[num] += weight
                
                # 3. Day of Week Adjustment
                # Boost numbers that like this specific day (e.g., Tuesday)
                target_day_name = target_date_input.strftime('%A')
                st.caption(f"Applying **{target_day_name}** frequency weighting...")
                
                for idx, row in df.iterrows():
                    if row['Date'].strftime('%A') == target_day_name:
                         for num in row[cols].values:
                             if num > 0:
                                 # Small boost for Day of Week preference
                                 affinity_scores[num] += 0.5

                # 4. Sort and Predict
                # Remove the trigger numbers themselves (unless we expect repeats)
                # Usually we keep them as repeats are possible, but let's prioritize new numbers
                
                sorted_scores = sorted(affinity_scores.items(), key=lambda x: x[1], reverse=True)
                
                # Display Top 3
                top_3 = sorted_scores[:3]
                
                st.markdown("### 🏆 The Oracle's Decree")
                
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.markdown(f"<div class='oracle'># {top_3[0][0]}</div>", unsafe_allow_html=True)
                    st.caption(f"Affinity Score: {top_3[0][1]}")
                    st.progress(1.0)
                
                with c2:
                    st.markdown(f"<div class='oracle'># {top_3[1][0]}</div>", unsafe_allow_html=True)
                    st.caption(f"Affinity Score: {top_3[1][1]}")
                    st.progress(0.9)
                    
                with c3:
                    st.markdown(f"<div class='oracle'># {top_3[2][0]}</div>", unsafe_allow_html=True)
                    st.caption(f"Affinity Score: {top_3[2][1]}")
                    st.progress(0.8)
                
                st.success(f"**Most Probable Line:** {top_3[0][0]} - {top_3[1][0]} - {top_3[2][0]}")
                st.info("These numbers have the strongest historical magnetic connection to the numbers that just drew.")

    except Exception as e:
        st.error(f"System Error: {e}")

else:
    st.info("Waiting for Data Feed...")
