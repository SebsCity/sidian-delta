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
    .scout { color: #2962FF; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("The complete physics suite: **Radar**, **Lab**, **Squads**, and **Partners**.")

# --- SIDEBAR: DATA LOADER ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])
    st.info("Ensure data is sorted: Lunch -> Tea -> Lunch.")

# --- HELPER FUNCTION: DATE PREDICTOR ---
def calculate_landing_date(last_date, last_draw, draws_ahead):
    """Projects future dates based on draw counts."""
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
            # Try determining separator (Tab or Comma)
            df = pd.read_csv(uploaded_file, sep='\t' if 'tsv' in uploaded_file.name else ',')
            if len(df.columns) < 2: 
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep='\t')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Ensure Date Format
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Identify Number Columns (N1-N6 + Bonus)
        cols = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
        
        # Show Status
        last_row = df.iloc[-1]
        st.success(f"✅ System Online. Last Data Point: **{last_row['Date'].strftime('%d %b')} ({last_row['Draw_Name']})**")

        # 2. CREATE TABS
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔭 Radar (Scan All)", 
            "🔬 Forensic Lab (Deep Dive)", 
            "⛓️ Squad Tracker (Clusters)", 
            "🤝 Partner Protocol (Escorts)"
        ])

        # ==================================================
        # TAB 1: THE RADAR (Physics Scan)
        # ==================================================
        with tab1:
            st.subheader("🔭 Individual Target Radar")
            st.caption("Scans 1-49 for Accelerators (Speeding Up) and Decelerators (Slowing Down).")
            
            candidates = []
            
            for num in range(1, 50):
                hits = []
                for idx, row in df.iterrows():
                    if num in row[cols].values: hits.append(idx)
                
                if len(hits) >= 3:
                    # Physics Math
                    idx_last = hits[-1]
                    idx_prev = hits[-2]
                    idx_old = hits[-3]
                    
                    gap_new = idx_last - idx_prev
                    gap_old = idx_prev - idx_old
                    draws_since = (len(df) - 1) - idx_last
                    
                    if gap_old > 0:
                        ratio = gap_new / gap_old
                        pred_gap = gap_new * ratio
                        remaining = pred_gap - draws_since
                        
                        # Filter: Only show imminent hits (Due within 2.5 draws)
                        if remaining < 2.5:
                            if ratio < 0.8: type_, prio = "🚀 Accelerating", 1
                            elif ratio > 1.2: type_, prio = "🛑 Decelerating", 2
                            elif ratio > 4.0: type_, prio = "💤 Sleeper Wake-Up", 1
                            else: type_, prio = "⚖️ Rolling", 3
                            
                            p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                            
                            candidates.append({
                                "Number": num, 
                                "Physics Type": type_, 
                                "Ratio": round(ratio,2), 
                                "Est. Arrival": f"{p_date} ({p_time})", 
                                "Priority": prio
                            })
            
            if candidates:
                cand_df = pd.DataFrame(candidates).sort_values('Priority')
                st.dataframe(cand_df, hide_index=True, use_container_width=True)
            else:
                st.info("No immediate impact vectors found.")

        # ==================================================
        # TAB 2: FORENSIC LAB (Single Number Audit)
        # ==================================================
        with tab2:
            st.subheader("🔬 Single Number Flight Path")
            target = st.number_input("Enter Number to Audit:", 1, 49, 49)
            
            hits = []
            for idx, row in df.iterrows():
                if target in row[cols].values: hits.append(idx)
                
            if len(hits) >= 3:
                idx_last = hits[-1]
                idx_prev = hits[-2]
                idx_old = hits[-3]
                gap_new = idx_last - idx_prev
                gap_old = idx_prev - idx_old
                ratio = gap_new / gap_old if gap_old > 0 else 0
                pred_gap = gap_new * ratio
                
                # Display Metrics
                c1, c2, c3 = st.columns(3)
                c1.metric("Previous Gap", gap_old)
                c2.metric("Current Gap", gap_new)
                c3.metric("Decay Ratio", f"{ratio:.2f}")
                
                p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                
                st.markdown(f"#### 🎯 Projection for #{target}")
                st.success(f"**Estimated Arrival:** {p_date} - {p_time}")
                
                st.divider()
                st.markdown("**🧲 Magnetic Cluster Check**")
                last_row = df.iloc[idx_last]
                partners = [x for x in last_row[cols].values if x != target and x > 0]
                st.write(f"Last seen with: **{partners}**")
                st.caption("If any of these partners are active on the Radar, this number is magnetically locked.")
            else:
                st.warning("Not enough history to model this number.")

        # ==================================================
        # TAB 3: SQUAD TRACKER (Clusters)
        # ==================================================
        with tab3:
            st.subheader("⛓️ Squad & Cluster Detection")
            st.markdown("Detects **Triads** (Groups of 3) where 2 members have returned, making the 3rd **CRITICAL**.")
            
            recent_draws = df.tail(15) # Scan last 15 draws
            squads = []
            
            for idx, row in recent_draws.iterrows():
                draw_nums = [x for x in row[cols].values if x > 0]
                # Check all combinations of 3
                combos = list(combinations(draw_nums, 3))
                
                for squad in combos:
                    s_stat = {'Members': squad, 'Origin': f"{row['Date'].strftime('%d %b')}", 'Returned': [], 'Missing': []}
                    future = df.loc[idx+1:] # Look ahead
                    
                    for m in squad:
                        # Check if member returned
                        if any(m in r[cols].values for _, r in future.iterrows()): 
                            s_stat['Returned'].append(m)
                        else: 
                            s_stat['Missing'].append(m)
                    
                    # ALERT LOGIC: 2 Returned, 1 Missing
                    if len(s_stat['Returned']) >= 2 and len(s_stat['Missing']) > 0:
                        squads.append(s_stat)
            
            if squads:
                for s in squads:
                    st.error(f"🚨 CLUSTER ALERT: {s['Members']} (Origin: {s['Origin']})")
                    st.write(f"✅ Returned: {s['Returned']}")
                    st.markdown(f"🔥 **MISSING (BET NOW):** :red[**{s['Missing']}**]")
                    st.divider()
            else:
                st.success("No active squad triggers found.")

        # ==================================================
        # TAB 4: PARTNER PROTOCOL (Escorts)
        # ==================================================
        with tab4:
            st.subheader("🤝 The Partner Protocol")
            st.markdown("Use this for **Lunchtime-to-Teatime** strategy.")
            
            c1, c2 = st.columns(2)
            
            # 1. SIGNAL DETECTOR
            with c1:
                st.markdown("#### 📡 Signal Detector")
                st.caption("Numbers that hit TWICE in the last 24h.")
                last_2 = df.tail(2)
                counts = {}
                for _, row in last_2.iterrows():
                    for n in row[cols].values:
                        if n > 0: counts[n] = counts.get(n, 0) + 1
                
                signals = [n for n, c in counts.items() if c >= 2]
                if signals:
                    st.error(f"🔥 **ACTIVE SIGNALS:** {signals}")
                else:
                    st.info("No double-taps detected.")

            # 2. LUNCHTIME SCOUT INPUT
            with c2:
                st.markdown("#### 🥪 Lunchtime Scout Check")
                st.caption("Enter today's Lunch results to find Teatime partners.")
                l_input = st.text_input("Lunch Numbers (e.g. 49 12 5):", "")
            
            if l_input:
                st.divider()
                st.markdown("### 👇 Teatime Predictions")
                try:
                    lunch_nums = [int(x) for x in l_input.split() if x.isdigit()]
                    
                    for scout in lunch_nums:
                        # Find last history (excluding today's manual input)
                        hits = []
                        for idx, row in df.iterrows():
                            if scout in row[cols].values: hits.append(idx)
                        
                        if len(hits) >= 1:
                            last_idx = hits[-1]
                            last_row = df.iloc[last_idx]
                            partners = [x for x in last_row[cols].values if x != scout and x > 0]
                            
                            if partners:
                                st.markdown(f"**Scout {scout}** (Last seen {last_row['Date'].strftime('%d %b')}) is escorting:")
                                st.success(f"🔥 **BET PAIR:** {scout} + {partners[0]}")
                                if len(partners) > 1:
                                    st.caption(f"Backup Partners: {partners[1:]}")
                                st.markdown("---")
                except:
                    st.error("Invalid number format.")

    except Exception as e:
        st.error(f"System Error: {e}")
        st.info("Please verify your file format.")

else:
    st.info("Waiting for Data Feed... Upload your Master File in the sidebar.")
