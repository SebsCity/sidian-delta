import streamlit as st

# Page Configuration
st.set_page_config(page_title="The Sidian Auditor", page_icon="🎱", layout="centered")

# Title and Description
st.title("🎱 The Sidian Triad Auditor")
st.markdown("""
**Protocol:**
1. Input the **Date** of the draw you are playing.
2. Input the **Previous Bonus Ball**.
3. Input the **Lowest Main Number** (from the previous draw) for the Gap Method.
""")

st.divider()

# --- INPUT SECTION ---
col1, col2, col3 = st.columns(3)

with col1:
    play_date = st.number_input("📅 Date of Draw (D)", min_value=1, max_value=31, value=17)

with col2:
    bonus_ball = st.number_input("🔵 Last Bonus Ball (B)", min_value=1, max_value=49, value=14)

with col3:
    lowest_main = st.number_input("📉 Lowest Main (M)", min_value=1, max_value=49, value=9)

st.divider()

# --- LOGIC CORE ---

# Method 1: The Date Driver (B + D) & (B - D)
# Logic: Primary flow. Add Date to Bonus.
target_1_sum = bonus_ball + play_date
target_1_diff = abs(bonus_ball - play_date)

# Method 2: The Inverse 49 (The Trap)
# Logic: 49 - (Difference of Bonus and Date) AND 49 - (Sum of Bonus and Date)
# This catches cases like Dec 7 (34-7=27 -> 49-27=22) and Dec 3 (34+3=37 -> 49-37=12)
diff_b_d = abs(bonus_ball - play_date)
sum_b_d = bonus_ball + play_date

target_2_inv_diff = 49 - diff_b_d
target_2_inv_sum = 49 - sum_b_d if sum_b_d < 49 else "N/A (Sum > 49)"

# Method 3: The Gap (The Mechanic)
# Logic: Difference between Bonus and Lowest Main
target_3_gap = abs(bonus_ball - lowest_main)


# --- DISPLAY RESULTS ---

st.subheader("🏁 Audit Results")

# Display Option 1
st.info(f"**Option 1: The Date Driver (Natural Flow)**")
c1, c2 = st.columns(2)
c1.metric(label="Sum (B + D)", value=target_1_sum if target_1_sum <= 49 else f"{target_1_sum} (Check Digit Sum)")
c2.metric(label="Diff (B - D)", value=target_1_diff)

# Display Option 2
st.warning(f"**Option 2: The Inverse 49 (The Trap)**")
c3, c4 = st.columns(2)
c3.metric(label="Inverse of Diff [49 - (B-D)]", value=target_2_inv_diff, help="Classic trap method (e.g. Dec 7)")
c4.metric(label="Inverse of Sum [49 - (B+D)]", value=target_2_inv_sum, help="Used when Bonus + Date is high (e.g. Dec 3)")

# Display Option 3
st.success(f"**Option 3: The Gap Method (Internal)**")
st.metric(label="Main vs Bonus Gap |M - B|", value=target_3_gap, help="Feeder number from internal draw difference")

st.divider()

# --- SUMMARY TABLE ---
st.markdown("### 📋 Quick Reference Line")
results_list = [
    target_1_sum if target_1_sum <= 49 else None,
    target_1_diff,
    target_2_inv_diff,
    target_2_inv_sum if isinstance(target_2_inv_sum, int) else None,
    target_3_gap
]
# Filter None values and sort unique
final_line = sorted(list(set([x for x in results_list if x is not None and x > 0])))

st.write("Based on the forensic inputs, your calculated hot numbers are:")
st.code(f"{final_line}", language="python")

