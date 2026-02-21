import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import re
from xgboost import XGBClassifier
from sklearn.preprocessing import MultiLabelBinarizer

DB_PATH = "v6_draws.db"
MAX_NUMBER = 49

# ==========================================
# DATABASE SETUP
# ==========================================
def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY,
            numbers TEXT,
            bonus INTEGER
        )
    """)
    conn.close()

init_db()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM draws ORDER BY id ASC", conn)
    conn.close()
    return df

# ==========================================
# SAFE PARSERS
# ==========================================
def safe_int(x):
    try:
        return int(float(str(x).strip()))
    except:
        return None

def parse_manual_input(text):
    parts = re.split(r"[,\s]+", text.strip())
    nums = [safe_int(p) for p in parts if safe_int(p) is not None]
    return nums

def parse_numbers_str(s):
    return [safe_int(x) for x in str(s).split(",") if safe_int(x) is not None]

# ==========================================
# DATA UPLOAD
# ==========================================
with st.sidebar:
    st.header("📂 Upload Draw History")
    file = st.file_uploader("CSV or XLSX", type=["csv", "xlsx"])
    if file:
        df_new = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        st.write("Preview:", df_new.head())
        if st.button("Commit to Database"):
            m_cols = df_new.columns[:6]
            b_col = df_new.columns[6] if len(df_new.columns) > 6 else None
            cleaned = pd.DataFrame()
            cleaned["numbers"] = df_new[m_cols].apply(
                lambda row: ",".join(str(safe_int(x)) for x in row if safe_int(x) is not None),
                axis=1
            )
            cleaned["bonus"] = df_new[b_col].apply(safe_int) if b_col else None
            cleaned = cleaned.dropna()
            conn = sqlite3.connect(DB_PATH)
            cleaned.to_sql("draws", conn, if_exists="replace", index=False)
            conn.close()
            st.success(f"{len(cleaned)} rows committed successfully!")
            st.rerun()

# ==========================================
# FEATURE ENGINEERING FOR AI
# ==========================================
def create_features(df):
    X = []
    y = []
    for i in range(len(df)-1):
        curr = parse_numbers_str(df.iloc[i]["numbers"])
        next_draw = parse_numbers_str(df.iloc[i+1]["numbers"])
        bonus_next = safe_int(df.iloc[i+1]["bonus"])

        # Feature vector: one-hot for numbers 1-49
        vec = np.zeros(MAX_NUMBER)
        for n in curr:
            vec[n-1] = 1

        # Additional features: sum, mean, odd/even ratio
        vec = np.append(vec, [sum(curr), np.mean(curr), sum(1 for x in curr if x%2==0)/6])
        X.append(vec)
        y.append(next_draw + [bonus_next])
    return np.array(X), y

# ==========================================
# TRAIN XGBOOST MULTI-TARGET MODEL
# ==========================================
def train_ai_model(df):
    X, y = create_features(df)
    mlb = MultiLabelBinarizer(classes=list(range(1, MAX_NUMBER+1)))
    Y_main = mlb.fit_transform([row[:6] for row in y])
    Y_bonus = np.array([row[6] for row in y])

    model_main = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model_bonus = XGBClassifier(use_label_encoder=False, eval_metric='logloss')

    model_main.fit(X, Y_main)
    model_bonus.fit(X, Y_bonus)

    return model_main, model_bonus, mlb

# ==========================================
# PREDICTION
# ==========================================
def predict_next(model_main, model_bonus, mlb, trigger_nums):
    vec = np.zeros(MAX_NUMBER)
    for n in trigger_nums:
        if 1 <= n <= MAX_NUMBER:
            vec[n-1] = 1
    vec = np.append(vec, [sum(trigger_nums), np.mean(trigger_nums), sum(1 for x in trigger_nums if x%2==0)/6])
    vec = vec.reshape(1, -1)

    # Predict probability for main numbers
    probs_main = model_main.predict_proba(vec)
    prob_sums = np.sum(np.array([p[:,1] for p in probs_main]), axis=0)
    top6_idx = prob_sums.argsort()[-6:][::-1] + 1

    # Predict bonus
    bonus_pred = int(model_bonus.predict(vec)[0])

    return list(top6_idx), bonus_pred

# ==========================================
# MAIN PANEL
# ==========================================
st.title("🔥 SIDIAN DELTA V6 – Adaptive AI Engine")
history = get_history()
st.subheader("📊 Database Status")
st.write(f"Stored Draws: {len(history)}")

if len(history) < 20:
    st.info("Upload at least 20 draws for AI training.")
else:
    if st.button("Train AI Engine"):
        with st.spinner("Training AI..."):
            model_main, model_bonus, mlb = train_ai_model(history)
            st.session_state["model_main"] = model_main
            st.session_state["model_bonus"] = model_bonus
            st.session_state["mlb"] = mlb
            st.success("AI Engine trained successfully!")

    st.subheader("🔮 Enter Trigger Draw")
    user_input = st.text_input("Enter 6 numbers (space or comma separated)", placeholder="e.g. 5 12 19 27 33 41")
    if user_input and "model_main" in st.session_state:
        trigger_nums = parse_manual_input(user_input)
        if len(trigger_nums) != 6:
            st.warning("Enter exactly 6 main numbers")
        else:
            pred_main, pred_bonus = predict_next(
                st.session_state["model_main"],
                st.session_state["model_bonus"],
                st.session_state["mlb"],
                trigger_nums
            )
            st.success(f"Predicted Next Main Numbers: {pred_main}")
            st.success(f"Predicted Next Bonus: {pred_bonus}")

    st.subheader("🧪 Manual Basket Backtest")
    manual_input = st.text_input(
        "Enter past draw to test (6 numbers + bonus, spaces/commas OK)",
        placeholder="5 12 19 27 33 41 9"
    )
    if manual_input and "model_main" in st.session_state:
        parsed = parse_manual_input(manual_input)
        if len(parsed) < 7:
            st.warning("Enter 6 main numbers + 1 bonus")
        else:
            test_nums = parsed[:6]
            test_bonus = parsed[6]
            pred_main, pred_bonus = predict_next(
                st.session_state["model_main"],
                st.session_state["model_bonus"],
                st.session_state["mlb"],
                test_nums
            )
            match_count = len(set(test_nums) & set(pred_main))
            bonus_match = (test_bonus == pred_bonus)
            st.write(f"Main Matches: {match_count}/6")
            st.write(f"Bonus Match: {bonus_match}")
