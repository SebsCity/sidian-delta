import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import beta, zscore

st.set_page_config(page_title="Sidian Bonus Lab PRO", layout="wide", page_icon="🚀")

st.title("🚀 Sidian Bonus Ball Analytics Lab PRO")
st.caption("Markov + Bayesian + Monte Carlo Engine")

MAX_NUMBER = 49

# =============================
# ADVANCED SCORING ENGINE
# =============================

def build_transition_matrix(series, n_range=MAX_NUMBER):
    matrix = np.zeros((n_range, n_range))
    for i in range(len(series) - 1):
        current = series.iloc[i] - 1
        nxt = series.iloc[i + 1] - 1
        matrix[current, nxt] += 1
    
    # Normalize rows to probabilities
    row_sums = matrix.sum(axis=1)
    row_sums[row_sums == 0] = 1
    matrix = matrix / row_sums[:, None]
    return matrix

def monte_carlo_sim(matrix, last_number, simulations=10000):
    results = []
    current = last_number - 1
    for _ in range(simulations):
        probs = matrix[current]
        next_num = np.random.choice(range(MAX_NUMBER), p=probs)
        results.append(next_num + 1)
    return pd.Series(results).value_counts() / simulations

def advanced_scores(series):
    # Historical frequency
    freq = series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_prob = (freq + 1) / (len(series) + MAX_NUMBER)  # Bayesian smoothing
    
    # Recency gap
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(series):
        last_seen[val] = idx
    
    gaps = pd.Series([len(series) - last_seen[i] for i in range(1, MAX_NUMBER+1)],
                     index=range(1, MAX_NUMBER+1))
    
    gap_z = pd.Series(zscore(gaps), index=gaps.index)
    
    # Momentum (last 50 draws)
    window = min(50, len(series))
    momentum = series.iloc[-window:].value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    momentum_prob = momentum / window
    
    # Combine adaptively
    final_score = (
        0.35 * freq_prob +
        0.30 * momentum_prob +
        0.35 * (gap_z - gap_z.min()) / (gap_z.max() - gap_z.min())
    )
    
    return final_score, gaps
