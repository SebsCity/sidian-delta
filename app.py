import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sidian Master Scanner", page_icon="🧬")

st.title("🧬 The Sidian Master Scanner")
st.markdown("Upload your **merged single file** (Lunch/Tea in order) to run the Bouncing Ball analysis.")

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("📂 Upload Master Sequence CSV", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"Loaded {len(df)} draws successfully.")
    
    # --- AUTOMATED SCANNER ---
    st.divider()
    st.subheader("🔬 Physics Scan Results (Live)")
    
    # 1. Flatten Data to find recent hitters
    # We take the last 20 draws to see what is active
    recent_slice = df.tail(30).reset_index(drop=True)
    
    # Allow user to pick a number to inspect
    target_num = st.number_input("Enter a Number to Audit (e.g. 16)", min_value=1, max_value=49, value=16)
    
    # Find all occurrences of this number in the ENTIRE history
    # Create a simple list of indices where the number appeared
    hits = []
    
    # Iterate through the dataframe to find rows where the number appeared
    # (Checking columns N1 to N6 and Bonus)
    cols_to_check = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
    
    for idx, row in df.iterrows():
        if target_num in row[cols_to_check].values:
            hits.append(idx)
            
    if len(hits) < 2:
        st.warning("Not enough data to calculate bounce (Need at least 2 hits).")
    else:
        # Calculate Gaps
        last_hit_index = hits[-1]
        prev_hit_index = hits[-2]
        gap_current = (len(df) - 1) - last_hit_index  # Draws since last hit
        
        gap_between_hits = last_hit_index - prev_hit_index
        
        st.write(f"**Last Hit:** Draw #{last_hit_index} ({df.iloc[last_hit_index]['Date']} {df.iloc[last_hit_index]['Draw_Name']})")
        st.write(f"**Previous Hit:** Draw #{prev_hit_index}")
        st.write(f"**Gap Size:** {gap_between_hits} draws")
        
        if len(hits) >= 3:
            prev_prev_hit = hits[-3]
            gap_older = prev_hit_index - prev_prev_hit
            
            # Physics Ratio
            ratio = gap_between_hits / gap_older if gap_older > 0 else 0
            
            st.metric("Decay Ratio", f"{ratio:.2f}")
            
            if ratio < 0.8:
                st.error("🚀 ACCELERATING (Speeding Up)")
                predicted_next = gap_between_hits * ratio
                st.info(f"**Prediction:** Next hit in approx {round(predicted_next)} draws.")
            elif ratio > 1.2:
                st.info("🔵 SLOWING DOWN (Going Cold)")
            else:
                st.warning("⚪ STABLE / ROLLING")
                
    st.divider()
    st.caption("Latest Data in File:")
    st.dataframe(df.tail(5))
