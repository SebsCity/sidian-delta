import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="Sidian Master Scanner", page_icon="🧬")

st.title("🧬 The Sidian Master Scanner")
st.markdown("Upload your **merged master file** to run the Bouncing Ball analysis with **Date Prediction**.")

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("📂 Upload Master Sequence CSV", type=['csv', 'xlsx'])

# --- HELPER FUNCTION: Future Date Calculator ---
def get_future_draw(start_date, start_draw_name, draws_to_add):
    """
    Calculates the exact date and draw time by adding X draws to the start point.
    Handles the Lunch -> Tea -> Next Day Lunch transition.
    """
    current_date = pd.to_datetime(start_date)
    current_draw = start_draw_name.strip()
    
    # Round draws to nearest whole number for calendar scheduling
    steps = int(round(draws_to_add))
    
    if steps < 1:
        steps = 1 # Minimum 1 step forward
        
    for _ in range(steps):
        if current_draw == 'Lunchtime':
            current_draw = 'Teatime'
            # Date stays the same
        else:
            current_draw = 'Lunchtime'
            current_date = current_date + timedelta(days=1)
            
    return current_date.strftime('%A %d %b'), current_draw

if uploaded_file:
    # Load Data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Ensure Date is datetime for calculations
        df['Date'] = pd.to_datetime(df['Date'])
        
        st.success(f"Loaded {len(df)} draws successfully. Last Data Point: {df.iloc[-1]['Date'].strftime('%d %b %Y')}")
        
        # --- AUTOMATED SCANNER ---
        st.divider()
        st.subheader("🔬 Physics Scan Results (Live)")
        
        # User Input
        target_num = st.number_input("Enter a Number to Audit (e.g. 16)", min_value=1, max_value=49, value=16)
        
        # Find hits
        hits = []
        cols_to_check = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
        
        for idx, row in df.iterrows():
            if target_num in row[cols_to_check].values:
                hits.append(idx)
                
        if len(hits) < 3:
            st.warning("Not enough data to calculate bounce (Need at least 3 hits in history).")
        else:
            # Get Indices
            idx_last = hits[-1]
            idx_prev = hits[-2]
            idx_old = hits[-3]
            
            # Calculate Gaps
            gap_new = idx_last - idx_prev
            gap_old = idx_prev - idx_old
            
            # Get Dates
            last_date = df.iloc[idx_last]['Date']
            last_draw_name = df.iloc[idx_last]['Draw_Name']
            
            st.write(f"**Last Hit:** {last_date.strftime('%d %b')} ({last_draw_name})")
            st.write(f"**Recent Sequence:** Gap {gap_old} ➔ Gap {gap_new}")
            
            # Physics Ratio
            if gap_old > 0:
                ratio = gap_new / gap_old
                
                st.metric("Decay Ratio", f"{ratio:.2f}")
                
                # Predict Next Gap
                next_gap_float = gap_new * ratio
                
                # --- LOGIC ENGINE ---
                
                # 1. THE HOT ZONE (Widened to 1.1 to catch stable/accelerating)
                if ratio <= 1.1:
                    pred_date, pred_time = get_future_draw(last_date, last_draw_name, next_gap_float)
                    
                    if ratio < 0.8:
                        status = "🚀 ACCELERATING (Hot)"
                        color = "red"
                    else:
                        status = "⚠️ STABLE / ROLLING (Watch List)"
                        color = "orange"
                        
                    st.markdown(f":{color}[**{status}**]")
                    st.write(f"Predicted Gap: {round(next_gap_float, 1)} draws")
                    st.success(f"**Target:** {pred_date} ({pred_time})")
                    
                    if next_gap_float < 1.0:
                        st.error("🚨 IMMINENT ALERT: Physics predicts a BACK-TO-BACK hit!")

                # 2. THE SLEEPER WAKE-UP (Ratio > 4.0)
                elif ratio > 4.0:
                    st.markdown(":blue[**💤 SLEEPER WAKE-UP (Anomaly)**]")
                    st.info(f"Ratio {ratio:.1f} detected. This number just woke up from a long sleep.")
                    st.warning("**Strategy:** Sleepers often 'Double Tap' to regain average. Play for a repeat in 1-3 draws.")
                    
                # 3. THE COLD ZONE
                else:
                    st.write("🔵 Decelerating (Going Cold). No immediate signal.")

            else:
                st.warning("Cannot calculate ratio (Previous gap was 0).")

        st.divider()
        st.caption("Latest 5 Draws in Data:")
        st.dataframe(df.tail(5))
        
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.info("Make sure your CSV/Excel has columns: Date, N1...N6, Bonus, Draw_Name")

else:
    st.info("Waiting for file upload...")
