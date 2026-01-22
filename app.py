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
    .converge { color: #6200EA; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("Complete System: **Radar**, **Lab**, **Squads**, **Partners**, and **Multidimensional Scan**.")

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
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔭 Radar (Scan All)", 
            "🔬 Forensic Lab", 
            "⛓️ Squad Tracker", 
            "🤝 Partner Protocol",
            "🧩 Multidimensional Scan"
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
                    gap_new = idx_last - idx_prev
                    gap_old = idx_prev - idx_old
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
                            candidates.append({
                                "Number": num, "Type": type_, "Ratio": round(ratio,2), 
                                "Est. Arrival": f"{p_date} ({p_time})", "Priority": prio
                            })
            
            if candidates:
                cand_df = pd.DataFrame(candidates).sort_values('Priority')
                st.dataframe(cand_df, hide_index=True, use_container_width=True)
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
                    st.divider()

        # ==================================================
        # TAB 4: PARTNER PROTOCOL
        # ==================================================
        with tab4:
            st.subheader("🤝 The Partner Protocol")
            
            last_2 = df.tail(2)
            counts = {}
            for _, row in last_2.iterrows():
                for n in row[cols].values:
                    if n > 0: counts[n] = counts.get(n, 0) + 1
            signals = [n for n, c in counts.items() if c >= 2]
            if signals: st.error(f"🔥 **DOUBLE-TAP SIGNALS:** {signals}")

            st.divider()
            l_input = st.text_input("Enter Lunchtime Numbers (Space separated):", "")
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
                                bet_slip.append({
                                    "Scout": scout, "Last_Seen": last_row['Date'].strftime('%Y-%m-%d'),
                                    "Partner": partners[0], "Bet": "Pair"
                                })
                    if bet_slip:
                        res_df = pd.DataFrame(bet_slip)
                        st.dataframe(res_df)
                        st.markdown("### 📋 Copy for Excel")
                        st.code(res_df.to_csv(sep='\t', index=False), language='text')
                except: pass

        # ==================================================
        # TAB 5: MULTIDIMENSIONAL SCAN (NEW!)
        # ==================================================
        with tab5:
            st.subheader("🧩 Multidimensional Group Scan")
            st.markdown("Predict the **Date** for a specific Duo or Triple.")
            
            g_input = st.text_input("Enter Duo/Triple (e.g. 49 43):", "")
            
            if g_input:
                try:
                    target_group = [int(x) for x in g_input.split() if x.isdigit()]
                    st.write(f"Scanning dimensions for Group: **{target_group}**")
                    st.divider()

                    # 1. HARD LOCK SCAN (Joint History)
                    st.markdown("#### 🔒 Layer 1: The Hard Lock (Joint History)")
                    st.caption("Dates where this EXACT group appeared together.")
                    
                    joint_hits = []
                    for idx, row in df.iterrows():
                        # Check if target_group is a subset of the row numbers
                        row_vals = set(row[cols].values)
                        if set(target_group).issubset(row_vals):
                            joint_hits.append(idx)
                    
                    if len(joint_hits) > 0:
                        # Calculate Group Gaps
                        group_data = []
                        for i in range(len(joint_hits)):
                            idx = joint_hits[i]
                            date_str = df.iloc[idx]['Date'].strftime('%d %b %Y')
                            draw_name = df.iloc[idx]['Draw_Name']
                            
                            gap = "N/A"
                            if i > 0:
                                gap = joint_hits[i] - joint_hits[i-1]
                            
                            group_data.append({"Date": date_str, "Draw": draw_name, "Gap (Draws)": gap})
                            
                        g_df = pd.DataFrame(group_data)
                        st.dataframe(g_df)
                        
                        # Prediction based on Group Physics
                        if len(joint_hits) >= 3:
                            gap_new = joint_hits[-1] - joint_hits[-2]
                            gap_old = joint_hits[-2] - joint_hits[-3]
                            ratio = gap_new / gap_old if gap_old > 0 else 1
                            pred_gap = gap_new * ratio
                            p_date, p_time = calculate_landing_date(df.iloc[joint_hits[-1]]['Date'], df.iloc[joint_hits[-1]]['Draw_Name'], pred_gap)
                            
                            st.success(f"💎 **GROUP PREDICTION:** Expect re-convergence on **{p_date} ({p_time})**")
                            st.metric("Group Velocity (Ratio)", f"{ratio:.2f}")
                        else:
                            st.warning("Not enough joint history for a Hard Lock prediction (Need 3+ hits). Checking Layer 2...")
                    else:
                        st.warning("This group has NEVER appeared together in the uploaded history.")

                    st.divider()

                    # 2. WAVE CONVERGENCE (Intersection)
                    st.markdown("#### 🌊 Layer 2: Wave Convergence (Intersection)")
                    st.caption("Where do the individual flight paths collide?")
                    
                    convergence_dates = []
                    
                    cols_c = st.columns(len(target_group))
                    
                    for i, num in enumerate(target_group):
                        with cols_c[i]:
                            hits = []
                            for idx, row in df.iterrows():
                                if num in row[cols].values: hits.append(idx)
                            
                            if len(hits) >= 3:
                                idx_last = hits[-1]
                                idx_prev = hits[-2]
                                idx_old = hits[-3]
                                gap_new = idx_last - idx_prev
                                gap_old = idx_prev - idx_old
                                ratio = gap_new / gap_old if gap_old > 0 else 0
                                pred_gap = gap_new * ratio
                                
                                p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                                st.info(f"**#{num}** due: {p_date} ({p_time})")
                                convergence_dates.append(f"{p_date} ({p_time})")
                            else:
                                st.warning(f"#{num}: No data")
                    
                    # Check for Matches
                    if len(convergence_dates) > 0:
                        # Find duplicates in the list (Convergence)
                        from collections import Counter
                        counts = Counter(convergence_dates)
                        matches = [date for date, count in counts.items() if count > 1]
                        
                        if matches:
                            st.markdown("### 🎯 CONVERGENCE DETECTED")
                            for m in matches:
                                st.error(f"🔥 **HIGH PROBABILITY COLLISION:** {m}")
                            st.write("The individual physics models predict the numbers will land on this same date.")
                        else:
                            st.write("No exact date overlap detected yet. Watch the individual dates.")

                except Exception as e:
                    st.error(f"Error: {e}")

    except Exception as e:
        st.error(f"System Error: {e}")

else:
    st.info("Waiting for Data Feed...")
