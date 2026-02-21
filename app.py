import streamlit as st
import pandas as pd
from collections import Counter

# Set page to mobile-friendly wide mode
st.set_page_config(page_title="Sidian Bonus Lab", layout="centered")

st.title("🎰 Sidian Synthesis Engine")
st.markdown("### Predictive Analytics via Historical Data")

# --- SECTION 1: DATA UPLOAD ---
st.sidebar.header("Data Management")
uploaded_file = st.sidebar.file_uploader("Upload 'Full A Lister 1.0' Excel", type=["xlsx", "xls"])

def process_data(file):
    try:
        # Read the Excel file
        df = pd.read_excel(file)
        # Clean data: Ensure only numeric values are processed
        numeric_data = df.select_dtypes(include=['number']).values.flatten()
        return Counter(numeric_data), df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None, None

freq_map, raw_df = None, None
if uploaded_file:
    freq_map, raw_df = process_data(uploaded_file)
    st.sidebar.success("Datasheet Loaded Successfully!")
else:
    st.info("Please upload your historical Excel file in the sidebar to begin.")

# --- SECTION 2: INPUT DRAWS ---
st.divider()
st.subheader("Input 3 Previous Draws")
st.caption("Enter 6 main numbers + 1 bonus for each (21 total numbers)")

def get_draw_input(label, key_suffix):
    col1, col2 = st.columns([3, 1])
    with col1:
        nums = st.text_input(f"{label} (6 Main):", placeholder="e.g. 2, 14, 25, 30, 31, 44", key=f"n_{key_suffix}")
    with col2:
        bonus = st.text_input(f"Bonus:", placeholder="7", key=f"b_{key_suffix}")
    
    if nums and bonus:
        try:
            combined = [int(n.strip()) for n in nums.split(',')]
            combined.append(int(bonus.strip()))
            if len(combined) == 7:
                return combined
            else:
                st.warning(f"{label} must have exactly 7 numbers total.")
        except ValueError:
            st.error(f"Use numbers and commas only in {label}")
    return []

d1 = get_draw_input("Draw 1 (Latest)", "one")
d2 = get_draw_input("Draw 2", "two")
d3 = get_draw_input("Draw 3", "three")

# --- SECTION 3: PREDICTION LOGIC ---
if st.button("Determine Likely 4 Numbers", type="primary"):
    all_recent = d1 + d2 + d3
    
    if len(all_recent) < 21:
        st.warning("Please fill in all 3 draws (21 numbers total) before predicting.")
    elif freq_map is None:
        st.error("Historical datasheet missing. Please upload your Excel file.")
    else:
        # ANALYSIS: 
        # We look for 'Hot Numbers' (High Frequency) 
        # that have NOT appeared in the last 3 draws (Expected to return)
        recent_set = set(all_recent)
        
        # Sort history by most frequent
        sorted_freq = sorted(freq_map.items(), key=lambda x: x[1], reverse=True)
        
        predictions = []
        for num, count in sorted_freq:
            if num not in recent_set:
                predictions.append(int(num))
            if len(predictions) == 4:
                break
        
        # Display Results
        st.divider()
        st.balloons()
        st.write("### 🔮 Predicted Numbers:")
        cols = st.columns(4)
        for i, p_num in enumerate(predictions):
            cols[i].metric(label=f"Number {i+1}", value=p_num)
        
        st.caption("Logic: High-frequency historical numbers excluded from the last 21 draws.")

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.write("Developed for **Sidian Brand**")
