import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats

# --- 1. Page Configuration ---
st.set_page_config(page_title="Process Capability Pro", layout="wide", page_icon="⚙️")
st.title("⚙️ Live Process Capability (Cp & Cpk) Analyzer")
st.markdown("""
**Operator Dashboard:** Paste your data from Excel or type measurements directly into the table below. 
The system will instantly calculate process capability once enough data is provided.
""")

# --- 2. Sidebar for Specifications ---
st.sidebar.header("Step 1: Specifications")
target = st.sidebar.number_input("Target Value", value=45.0, step=0.1)
LSL = st.sidebar.number_input("Lower Spec Limit (LSL)", value=43.0, step=0.1)
USL = st.sidebar.number_input("Upper Spec Limit (USL)", value=47.0, step=0.1)

if LSL >= USL:
    st.sidebar.error("Error: LSL must be less than USL.")
    st.stop()

# --- 3. Interactive Data Entry (Empty Template) ---
st.subheader("Step 2: Live Data Entry")
st.markdown("Click the first cell under **Values** and press `Ctrl+V` (or `Cmd+V`) to paste your data from Excel.")

# Initialize an empty template with 15 blank rows for easy pasting/typing
if 'operator_data' not in st.session_state:
    st.session_state.operator_data = pd.DataFrame({
        "Values": pd.Series([None] * 15, dtype=float),  # Empty numerical column
        "Time": pd.Series([""] * 15, dtype=str)  # Empty string column
    })

col_data, col_metrics = st.columns([1, 2])

with col_data:
    edited_df = st.data_editor(
        st.session_state.operator_data,
        num_rows="dynamic",  # Allows the table to expand automatically when 100 rows are pasted
        use_container_width=True,
        hide_index=False
    )

# Extract numerical data, dropping any empty (NaN) rows
raw_values = pd.to_numeric(edited_df["Values"], errors='coerce').dropna().values

# --- Smart Validation: Waiting for Operator Input ---
with col_metrics:
    st.subheader("Step 3: Real-Time Analysis")

    if len(raw_values) == 0:
        st.info("👈 Please enter or paste your measurements into the table on the left to begin the analysis.")
        st.stop()  # Halts the code here until data is entered

    if len(raw_values) < 30:
        st.warning(
            f"⚠️ You only have {len(raw_values)} valid samples. Six Sigma standards require a minimum of 30 samples (ideally 50-100) for reliable capability analysis.")
        if len(raw_values) < 2:
            st.stop()  # Needs at least 2 points to calculate standard deviation

    # --- 4. Statistical Calculations ---
    mu = np.mean(raw_values)
    sigma = np.std(raw_values, ddof=1)

    if sigma <= 0.0001:
        sigma = 0.0001  # Prevent division by zero

    Cp = (USL - LSL) / (6 * sigma)
    Cpl = (mu - LSL) / (3 * sigma)
    Cpu = (USL - mu) / (3 * sigma)
    Cpk = max(0, min(Cpl, Cpu))

    # --- 5. Metrics & Smart Diagnosis ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Process Mean", f"{mu:.3f}")
    m2.metric("Std Deviation (σ)", f"{sigma:.3f}")

    cp_cap = "Capable" if Cp >= 1.33 else "Not Capable"
    cpk_cap = "Capable" if Cpk >= 1.33 else "Not Capable"

    m3.metric("Cp (Potential)", f"{Cp:.2f}", delta=cp_cap, delta_color="normal" if Cp >= 1.33 else "inverse")
    m4.metric("Cpk (Actual)", f"{Cpk:.2f}", delta=cpk_cap, delta_color="normal" if Cpk >= 1.33 else "inverse")

    st.markdown("---")
    if Cpk < 1.33:
        if Cp >= 1.33 and Cpk < 1.33:
            st.error(
                f"**DIAGNOSIS (SCENARIO A):** Your process is highly consistent (Good Cp) BUT it is **OFF-CENTER** (Low Cpk).")
            st.markdown(
                f"**Action Plan:** **CALIBRATE** the equipment to shift the mean back toward the Target ({target}).")
        elif Cp < 1.33 and (Cp - Cpk) < 0.15:
            st.error(
                f"**DIAGNOSIS (SCENARIO B):** Your process is relatively centered, but **UNSTABLE** (High Variation, Low Cp).")
            st.markdown(
                f"**Action Plan:** Initiate a **PROCESS IMPROVEMENT** project. Investigate root causes of variation.")
        else:
            st.error(
                f"**DIAGNOSIS (SCENARIO C - MIXED):** Critical Failure! The process is **BOTH** off-center AND unstable.")
            st.markdown(
                f"**Action Plan:** 1) Calibrate to recenter, AND 2) Start root cause analysis to reduce variation.")
    else:
        st.success(f"**DIAGNOSIS:** Your process is statistically **CAPABLE** (Cp & Cpk >= 1.33).")
        st.markdown("**Action Plan:** Continue standard monitoring.")

# --- 6. Visualization ---
st.markdown("---")
fig, ax = plt.subplots(figsize=(12, 4))

ax.hist(raw_values, bins=max(5, int(len(raw_values) / 4)), density=True, alpha=0.6, color='steelblue',
        edgecolor='black', label='Actual Data')
x_range = np.linspace(min(min(raw_values), LSL - 1), max(max(raw_values), USL + 1), 300)
pdf = stats.norm.pdf(x_range, mu, sigma)
ax.plot(x_range, pdf, 'k-', linewidth=2, label='Normal Distribution')

ax.axvline(LSL, color='red', linestyle='--', linewidth=2, label=f'LSL ({LSL})')
ax.axvline(USL, color='red', linestyle='--', linewidth=2, label=f'USL ({USL})')
ax.axvline(target, color='green', linestyle='-', linewidth=2, label=f'Target ({target})')

ax.set_title(f'Process Distribution (n={len(raw_values)} samples)', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
plt.tight_layout()

st.pyplot(fig)