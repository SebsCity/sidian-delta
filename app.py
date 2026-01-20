import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="Sidian Precision Engine", page_icon="🎯", layout="wide")

# --- CUSTOM CSS FOR PRESENCE ---
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .hot { color: #FF4B4B; }
    .cold { color: #1E88E5; }
    .success { color: #00C853; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("The system that predicted the **Number 4 Double-Tap**.")

# --- SIDEBAR: DATA LOADER ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])
    st.info("Ensure your file is chronological (Lunch -> Tea -> Lunch).")

# --- HELPER: FUTURE DATE CALCULATOR ---
def calculate_landing_date(last_date, last_draw, draws_ahead):
    """
    Projects the exact date and draw time based on 'draws_ahead'.
    Handles the Lunch/Tea toggle and Day increment.
    """
    current_date = pd.to_datetime(last_date)
    current_draw = str(last_draw).strip()
    
    # We round to the nearest whole draw, but keep the float for precision display
    steps = int(round(draws_ahead))
    if steps < 1: steps = 1  # Minimum 1 draw forward
    
    for _ in range(steps):
        if 'Lunchtime' in current_draw:
            current_draw = 'Teatime'
        else:
            current_draw = 'Lunchtime'
            current_date = current_date + timedelta(days=1)
            
    return current_date.strftime('%d %b %Y'), current_draw

# --- MAIN ENGINE ---
if uploaded_file:
    # 1. Load Data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep='\t' if 'tsv' in uploaded_file.name else ',')
            if len(df.columns) < 2: df = pd.read_csv(uploaded_file, sep='\t')
        else:
            df = pd.read_excel(uploaded_file)
        
        df['Date'] = pd.to_datetime(df['Date'])
        last_row = df.iloc[-1]
        st.success(f"✅ System Online. Last Data Point: **{last_row['Date'].strftime('%d %b')} ({last_row['Draw_Name']})**")
        
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # 2. Create Tabs
    tab1, tab2 = st.tabs(["🔭 The Radar (All Numbers)", "🔬 Forensic Lab (Single Number)"])

    # ==================================================
    # TAB 1: THE RADAR (Scans 1-49 for 'Number 4' patterns)
    # ==================================================
    with tab1:
        st.subheader("🔭 Daily Target Scan")
        st.caption("Scanning 1-49 for decay patterns...")
        
        candidates = []
        
        # Scan loop
        for num in range(1, 50):
            # Get hits
            cols = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
            hits = []
            for idx, row in df.iterrows():
                if num in row[cols].values:
                    hits.append(idx)
            
            if len(hits) >= 3:
                # Math
                idx_last = hits[-1]
                idx_prev = hits[-2]
                idx_old = hits[-3]
                
                gap_new = idx_last - idx_prev
                gap_old = idx_prev - idx_old
                
                # Current Gap (Draws since last hit)
                draws_since = (len(df) - 1) - idx_last
                
                if gap_old > 0:
                    ratio = gap_new / gap_old
                    predicted_gap = gap_new * ratio
                    
                    # THE PRECISION FILTER
                    # We want numbers where 'Draws Since' is CLOSE to 'Predicted Gap'
                    remaining_time = predicted_gap - draws_since
                    
                    # Logic: If it is due within 2 draws (or overdue)
                    if remaining_time < 2.5:
                        
                        # Classify the Physics
                        if ratio < 0.8:
                            physics_type = "🚀 Accelerating"
                            priority = 1 # Top Priority
                        elif ratio > 1.2:
                            physics_type = "🛑 Decelerating"
                            priority = 2
                        elif ratio > 4.0:
                             physics_type = "💤 Sleeper Wake-Up"
                             priority = 1
                        else:
                            physics_type = "⚖️ Rolling"
                            priority = 3
                            
                        # Calculate Date
                        pred_date, pred_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], predicted_gap)
                        
                        candidates.append({
                            "Number": num,
                            "Type": physics_type,
                            "Ratio": round(ratio, 2),
                            "Est. Gap": round(predicted_gap, 1),
                            "Due Date": f"{pred_date} ({pred_time})",
                            "Priority": priority,
                            "Remaining": round(remaining_time, 1)
                        })

        # Display Results
        if candidates:
            cand_df = pd.DataFrame(candidates).sort_values(by=['Priority', 'Remaining'])
            
            st.markdown("### 🚨 Immediate Threats (Top Priority)")
            st.dataframe(cand_df[cand_df['Priority'] == 1].style.format({"Ratio": "{:.2f}"}), hide_index=True)
            
            st.markdown("### 📉 The 'Number 4' Patterns (Decelerating)")
            st.caption("These numbers are slowing down. Like #4, they often hit exactly when the gap doubles.")
            st.dataframe(cand_df[cand_df['Priority'] == 2], hide_index=True)
            
        else:
            st.info("No immediate impact vectors found.")

    # ==================================================
    # TAB 2: FORENSIC LAB (Deep Dive)
    # ==================================================
    with tab2:
        st.subheader("🔬 Single Number Flight Path")
        target = st.number_input("Enter Number to Audit:", min_value=1, max_value=49, value=4)
        
        # Get hits again for deep dive
        cols = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
        hits = []
        for idx, row in df.iterrows():
            if target in row[cols].values:
                hits.append(idx)
                
        if len(hits) >= 3:
            idx_last = hits[-1]
            idx_prev = hits[-2]
            idx_old = hits[-3]
            
            gap_new = idx_last - idx_prev
            gap_old = idx_prev - idx_old
            
            ratio = gap_new / gap_old if gap_old > 0 else 0
            predicted_gap = gap_new * ratio
            
            # Display Flight Data
            c1, c2, c3 = st.columns(3)
            c1.metric("1. Previous Gap", f"{gap_old} Draws")
            c2.metric("2. Current Gap", f"{gap_new} Draws")
            c3.metric("3. Decay Ratio", f"{ratio:.2f}")
            
            st.divider()
            
            # THE PREDICTION BOX
            pred_date, pred_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], predicted_gap)
            
            st.markdown(f"#### 🎯 Prediction for #{target}")
            
            if ratio > 1.2:
                 st.info(f"Physics: **DECELERATION** (Slowing Down).")
                 st.write(f"The ball is losing energy. It should land around **Gap {round(predicted_gap)}**.")
            elif ratio < 0.8:
                 st.error(f"Physics: **ACCELERATION** (Speeding Up).")
                 st.write(f"The ball is gaining speed. It should land quickly around **Gap {round(predicted_gap)}**.")
            else:
                 st.warning(f"Physics: **STABLE ROLL**.")
            
            st.success(f"**Estimated Arrival:** {pred_date} - {pred_time}")
            
            # The "Number 4" Cluster Check
            st.markdown("---")
            st.markdown("**🧲 Magnetic Cluster Check**")
            st.caption("Does this number have active friends?")
            
            # Who did it draw with last time?
            last_partners = df.iloc[idx_last][cols].values
            partners = [x for x in last_partners if x != target and x > 0]
            st.write(f"Last paired with: {partners}")
            st.write("Check if any of these partners are in the 'Immediate Threats' list on Tab 1. If yes, the magnet is active.")

        else:
            st.warning("Not enough data to model flight path.")
else:
    st.info("Waiting for Master Sequence file...")
