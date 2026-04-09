import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# --- 1. Page Configuration ---
st.set_page_config(page_title="Process Capability Pro Analyzer", layout="wide", page_icon="⚙️")
st.title("⚙️ Process Capability (Cp & Cpk) Pro Analyzer")
st.markdown("""
This advanced tool calculates and visualizes process capability indices (Cp, Cpk) based on your specifications. 
It includes integrated failure mode scenarios (A & B) for root cause analysis.
""")

# --- 2. Sidebar for User Inputs & Scenario Selection ---
st.sidebar.header("Step 1: Define Specifications")
target = st.sidebar.number_input("Target Value", value=100.0, step=0.5, help="The ideal product measurement.")
LSL = st.sidebar.number_input("Lower Spec Limit (LSL)", value=98.0, step=0.5, help="The minimum acceptable measurement.")
USL = st.sidebar.number_input("Upper Spec Limit (USL)", value=102.0, step=0.5, help="The maximum acceptable measurement.")

# Validate limits
if LSL >= USL:
    st.sidebar.error("Error: LSL must be less than USL.")
    st.stop()
if not (LSL <= target <= USL):
    st.sidebar.warning("Warning: Target is outside specification limits.")

st.sidebar.markdown("---")
st.sidebar.header("Step 2: Analysis Mode")

# NEW FEATURE: Scenario Selection
analysis_mode = st.sidebar.selectbox(
    "Choose Analysis Scenario:",
    (
        "Manual Input (Custom Process)",
        "Scenario A: Process Shifted (Good Consistency, Wrong Setting)",
        "Scenario B: High Variation (Unstable Process)"
    ),
    help="Select a preset to demonstrate specific Six Sigma failure modes, or input your own data."
)

st.sidebar.subheader("Actual Process Data")

# Logic to set parameters based on selected scenario or manual input
if "Scenario A" in analysis_mode:
    # Preset for Shifted Mean: Mean is bad, Std Dev is good
    default_mean = target + 1.5
    default_std = 0.5            # 'Consistent' process
    st.sidebar.info(f"Scenario A Activated: Process mean is intentionally shifted from Target ({default_mean}).")
elif "Scenario B" in analysis_mode:
    # Preset for High Variation: Mean is perfect, Std Dev is bad
    default_mean = target
    default_std = (USL - LSL) / 3.0 # This guarantees a low Cp/Cpk
    st.sidebar.info(f"Scenario B Activated: Process mean is Target, but variation ({default_std:.2f}) is intentionally high.")
else:
    # Manual Input defaults
    default_mean = 100.4
    default_std = 0.6

# Process Inputs (Sliders/Number inputs are set by defaults logic above)
process_mean = st.sidebar.number_input("Actual Process Mean", value=float(default_mean), step=0.1)
process_std = st.sidebar.number_input("Actual Standard Deviation (Sigma)", value=float(default_std), step=0.1, min_value=0.01)
n_samples = st.sidebar.slider("Sample Size for Simulation", min_value=100, max_value=10000, value=1000, step=100)

# --- 3. Generate Data & Calculate Statistics ---
np.random.seed(42) # Consistent simulation results
data = np.random.normal(loc=process_mean, scale=process_std, size=n_samples)

# Sample statistics
mu = np.mean(data)
sigma = np.std(data, ddof=1)

# Prevent division by zero
if sigma <= 0.0001:
    sigma = 0.0001

# Cp & Cpk Calculation
Cp = (USL - LSL) / (6 * sigma)
Cpl = (mu - LSL) / (3 * sigma)
Cpu = (USL - mu) / (3 * sigma)
Cpk = max(0, min(Cpl, Cpu)) # Cpk cannot be negative, set floor to 0

# --- 4. Main Dashboard Area: Metrics and Smart Diagnosis ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Process Mean", f"{mu:.3f}", help="Average of your actual measurements.")
col2.metric("Standard Deviation (σ)", f"{sigma:.3f}", help="Measure of process consistency/variation.")

# Color coding for Cp/Cpk (Industry Standard >= 1.33)
cp_cap = "Capable (>=1.33)" if Cp >= 1.33 else "Not Capable"
cpk_cap = "Capable (>=1.33)" if Cpk >= 1.33 else "Not Capable"

col3.metric("Cp (Potential)", f"{Cp:.2f}", delta=cp_cap, delta_color="normal" if Cp >= 1.33 else "inverse", help="Theoretical capability if process mean was centered perfectly.")
col4.metric("Cpk (Actual)", f"{Cpk:.2f}", delta=cpk_cap, delta_color="normal" if Cpk >= 1.33 else "inverse", help="Actual capability considering current process mean position.")

# NEW FEATURE: Dynamic Smart Diagnosis
st.markdown("---")
st.subheader("🤖 Process Diagnosis & Action Plan")

# Criteria used in Scenarios A and B
shifted_threshold = 0.5 * process_std # Mean is off by more than 0.5 sigma

if Cpk < 1.33:
    if Cp >= 1.33 and Cpk < 1.33:
        # Matches Scenario A
        st.error(f"**DIAGNOSIS (SCENARIO A DETECTED):** Your process is highly consistent (Low Variation, Good Cp) BUT it is **OFF-CENTER** (Low Cpk). The average is too close to a limit.")
        st.markdown(f"**Action Plan:** **CALIBRATE** the process immediately to shift the mean back toward the Target ({target}). No major process overhaul needed, just an adjustment.")
    elif Cp < 1.33:
        # Matches Scenario B
        st.error(f"**DIAGNOSIS (SCENARIO B DETECTED):** Your process is **UNSTABLE** (High Variation, Low Cp). It cannot consistently produce within limits, even if perfectly centered.")
        st.markdown(f"**Action Plan:** Initiate a **PROCESS IMPROVEMENT** project (DMAIC). Investigate root causes of variation (e.g., worn equipment, operator training, raw material quality). Calibration alone will not fix this.")
else:
    st.success(f"**DIAGNOSIS:** Your process is statistically **CAPABLE** (Cp & Cpk >= 1.33). Variation is low, and the process is properly centered.")
    st.markdown("**Action Plan:** Continue standard process monitoring using SPC (Statistical Process Control) charts.")


# --- 5. Main Visualization ---
st.markdown("---")
st.subheader("Visual Analysis: Measurement Distribution vs. Specification Limits")

fig, ax = plt.subplots(figsize=(10, 5))

# Plot Histogram and fitted Normal Distribution Curve
ax.hist(data, bins=40, density=True, alpha=0.6, color='skyblue', edgecolor='black', label='Measurement Data')
x_range = np.linspace(min(data.min(), LSL-3), max(data.max(), USL+3), 300)
pdf = stats.norm.pdf(x_range, mu, sigma)
ax.plot(x_range, pdf, 'k-', linewidth=2.5, label='Normal Distribution')

# Vertical Limit Lines
ax.axvline(LSL, color='red', linestyle='--', linewidth=2, label=f'Lower Limit (LSL={LSL})')
ax.axvline(USL, color='red', linestyle='--', linewidth=2, label=f'Upper Limit (USL={USL})')
ax.axvline(target, color='green', linestyle='-', linewidth=2, label=f'Target ({target})')
ax.axvline(mu, color='blue', linestyle=':', linewidth=2, label=f'Actual Mean ({mu:.2f})')

# Shade Defective Areas (Red Zones)
x_def_low = np.linspace(x_range[0], LSL, 100)
ax.fill_between(x_def_low, stats.norm.pdf(x_def_low, mu, sigma), color='red', alpha=0.3, label='Defective Area (Out of Spec)')
x_def_high = np.linspace(USL, x_range[-1], 100)
ax.fill_between(x_def_high, stats.norm.pdf(x_def_high, mu, sigma), color='red', alpha=0.3)

# Formatting
ax.set_title(f'Process Capability (Cp={Cp:.2f}, Cpk={Cpk:.2f})', fontsize=14, fontweight='bold')
ax.set_xlabel('Measurements')
ax.set_ylabel('Density / Frequency')
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1), fontsize=10)
ax.grid(axis='y', alpha=0.2)
plt.tight_layout()

st.pyplot(fig)