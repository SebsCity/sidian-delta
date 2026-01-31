import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sidian Intersection Lab", page_icon="⚡", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .big-stat { font-size: 32px; font-weight: bold; color: #1E88E5; }
    .win-card { background-color: #E8F5E9; border-left: 5px solid #2E7D32; padding: 15px; margin-bottom: 10px; }
    .fail-card { background-color: #FFEBEE; border-left: 5px solid #C62828; padding: 15px; margin-bottom: 10px; }
    .neutral-card { background-color: #F5F5F5; border-left: 5px solid #9E9E9E; padding: 15px; margin-bottom: 10px; }
    .pred-box { background-color: #FFF3E0; border: 2px solid #FF9800; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ The Sidian Intersection: Forensic Lab")
st.markdown("""
**The 'Unthinkable' Technique:** We trap the winning numbers between the **Bonus Gravity** (Same Unit) and the **N6 Magnetism** (Sum 11-18).
""")

# --- SIDEBAR: DATA LOAD ---
with st.sidebar:
    st.header("📂 1. Upload History")
    uploaded_file = st.file_uploader("Upload 'The Full List' (CSV/Excel)", type=['csv', 'xlsx'])

# --- LOGIC ENGINE ---
def get_intersection_prediction(last_bonus, last_n6):
    """
    Returns (Status, PredictionList, Reason)
    Status: 'OPEN' (Valid Prediction) or 'CLOSED' (Math doesn't work)
    """
    b_unit = int(last_bonus) % 10
    n6_unit = int(last_n6) % 10
    
    # 1. Gravity Stream (All numbers ending in Bonus Unit)
    gravity_stream = [n for n in range(1, 50) if n % 10 == b_unit]
    
    # 2. Magnetic Filter (Sum Rule)
    # Check if this Unit + N6 Unit creates a valid bond (11-18)
    bond_sum = b_unit + n6_unit
    
    if 11 <= bond_sum <= 18:
        return "OPEN", gravity_stream, f"✅ Bond Active (Sum {bond_sum})"
    else:
        return "CLOSED", [], f"⛔ Bond Inactive (Sum {bond_sum} is outside 11-18)"

# --- MAIN APP ---
if uploaded_file:
    # Load Data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Clean Data
        cols = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]
        df = df.dropna(subset=cols)
        for c in cols: df[c] = df[c].astype(int)
        
        # Tabs
        tab1, tab2 = st.tabs(["🧪 Simulation & Practice", "📜 Backtest History"])
        
        # ==========================================
        # TAB 1: PRACTICE SIMULATOR
        # ==========================================
        with tab1:
            st.subheader("Manual Intersection Test")
            c1, c2 = st.columns(2)
            with c1:
                in_bonus = st.number_input("Enter Bonus Ball", min_value=1, max_value=49, value=17)
            with c2:
                in_n6 = st.number_input("Enter N6 Ball", min_value=1, max_value=49, value=47)
            
            # Run Logic
            status, preds, msg = get_intersection_prediction(in_bonus, in_n6)
            
            st.divider()
            
            if status == "OPEN":
                st.success(f"INTERSECTION OPEN! {msg}")
                st.markdown(f"### 🎯 Prediction Stream (Play These):")
                st.markdown(f"<div class='pred-box'>{str(preds)}</div>", unsafe_allow_html=True)
                
                # Highlight the "Hot" ones (just heuristic for now based on conversation)
                st.info("💡 **Tip:** Focus on the 'Mirror' (e.g., 7 & 37) or the 'High 40s' if available.")
            else:
                st.error(f"INTERSECTION CLOSED. {msg}")
                st.warning("⚠️ **Strategy:** The Bonus Unit and N6 Unit do not attract. Do NOT use the Sidian Intersection for this draw. Use the Standard N6 Corridor instead.")

        # ==========================================
        # TAB 2: BACKTEST HISTORY
        # ==========================================
        with tab2:
            st.subheader("Historical Success Rate")
            
            if st.button("Run Full Backtest"):
                results = []
                active_events = 0
                hits = 0
                
                progress = st.progress(0)
                
                # Loop through history
                # We look at Row i (Input) -> Row i+1 (Result)
                for i in range(len(df) - 1):
                    # Inputs
                    prev_row = df.iloc[i]
                    p_bonus = prev_row['Bonus']
                    p_n6 = prev_row['N6']
                    
                    # Result (Target Draw)
                    target_row = df.iloc[i+1]
                    target_nums = set([target_row[c] for c in cols if c != 'Bonus']) # Exclude bonus from win check? Usually main set matches.
                    target_nums_all = set([target_row[c] for c in cols])
                    
                    # Logic
                    status, preds, reason = get_intersection_prediction(p_bonus, p_n6)
                    
                    if status == "OPEN":
                        active_events += 1
                        # Check Hit (Did ANY predicted number appear in the next draw?)
                        # We usually check Main Set (N1-N6) for a win
                        hit_nums = set(preds).intersection(target_nums)
                        
                        is_win = len(hit_nums) > 0
                        if is_win: hits += 1
                        
                        results.append({
                            "Draw Index": i,
                            "Input": f"Bonus {p_bonus} / N6 {p_n6}",
                            "Prediction": str(preds),
                            "Result": "WIN" if is_win else "MISS",
                            "Hit Numbers": str(list(hit_nums)) if is_win else "-"
                        })
                    
                    if i % 100 == 0: progress.progress(i / len(df))
                
                progress.progress(100)
                
                # Display Stats
                st.divider()
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Total 'Open' Opportunities", active_events)
                sc2.metric("Successful Predictions", hits)
                if active_events > 0:
                    rate = (hits / active_events) * 100
                    sc3.metric("Success Rate", f"{rate:.1f}%")
                
                st.markdown("### 📝 Event Log (Last 50 Events)")
                
                # Show dataframe of results
                res_df = pd.DataFrame(results)
                # Sort by Draw Index Descending
                res_df = res_df.sort_values(by="Draw Index", ascending=False).head(50)
                
                for _, row in res_df.iterrows():
                    color_class = "win-card" if row['Result'] == "WIN" else "fail-card"
                    icon = "✅" if row['Result'] == "WIN" else "❌"
                    st.markdown(f"""
                    <div class="{color_class}">
                        <strong>{icon} {row['Result']}</strong> | {row['Input']} <br>
                        Predicted: {row['Prediction']} <br>
                        <em>Hits: {row['Hit Numbers']}</em>
                    </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Waiting for data upload...")
