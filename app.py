import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# 1. Page Configuration
st.set_page_config(page_title="Process Capability Dashboard", layout="wide")
st.title("⚙️ Process Capability (Cp & Cpk) Analyzer")
st.markdown("""
This tool calculates and visualizes process capability indices based on user-defined specification limits. 
Adjust the parameters on the sidebar to see how the process performance changes in real-time.
""")

# 2. Sidebar for User Inputs
st.sidebar.header("Input Parameters")

# User defines the limits
target = st.sidebar.number_input("Target Value", value=100.0, step=0.5)
LSL = st.sidebar.number_input("Lower Specification Limit (LSL)", value=98.0, step=0.5)
USL = st.sidebar.number_input("Upper Specification Limit (USL)", value=102.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("Simulate Process Data")
# User defines how the current process is actually behaving
process_mean = st.sidebar.number_input("Actual Process Mean", value=100.4, step=0.1)
process_std = st.sidebar.number_input("Actual Standard Deviation", value=0.6, step=0.1)
n_samples = st.sidebar.slider("Sample Size", min_value=100, max_value=5000, value=1000, step=100)

# 3. Generate Data & Calculate Statistics
np.random.seed(42)
data = np.random.normal(loc=process_mean, scale=process_std, size=n_samples)

mu = np.mean(data)
sigma = np.std(data, ddof=1)

# Prevent division by zero if sigma is extremely small
if sigma == 0:
    sigma = 0.0001

Cp = (USL - LSL) / (6 * sigma)
Cpl = (mu - LSL) / (3 * sigma)
Cpu = (USL - mu) / (3 * sigma)
Cpk = min(Cpl, Cpu)

# 4. Display Key Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Process Mean", f"{mu:.3f}")
col2.metric("Standard Deviation", f"{sigma:.3f}")
col3.metric("Cp (Potential)", f"{Cp:.2f}")
col4.metric("Cpk (Actual)", f"{Cpk:.2f}", delta="Capable (>=1.33)" if Cpk >= 1.33 else "Not Capable", delta_color="normal" if Cpk >= 1.33 else "inverse")

# 5. Visualization
fig, ax = plt.subplots(figsize=(10, 5))

# Histogram and Normal Distribution
ax.hist(data, bins=30, density=True, alpha=0.6, color='skyblue', edgecolor='black', label='Data Histogram')
x = np.linspace(min(data.min(), LSL-2), max(data.max(), USL+2), 100)
pdf = stats.norm.pdf(x, mu, sigma)
ax.plot(x, pdf, 'k-', linewidth=2, label='Normal Distribution')

# Limit Lines
ax.axvline(LSL, color='red', linestyle='dashed', linewidth=2, label=f'LSL ({LSL})')
ax.axvline(USL, color='red', linestyle='dashed', linewidth=2, label=f'USL ({USL})')
ax.axvline(target, color='green', linestyle='solid', linewidth=2, label=f'Target ({target})')

# Highlight out-of-spec areas
x_out_low = np.linspace(x[0], LSL, 50)
ax.fill_between(x_out_low, stats.norm.pdf(x_out_low, mu, sigma), color='red', alpha=0.3, label='Defective')
x_out_high = np.linspace(USL, x[-1], 50)
ax.fill_between(x_out_high, stats.norm.pdf(x_out_high, mu, sigma), color='red', alpha=0.3)

ax.set_title('Process Capability Distribution', fontsize=14)
ax.set_xlabel('Measurements')
ax.set_ylabel('Frequency')
ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1))
ax.grid(axis='y', alpha=0.3)

# Show plot in Streamlit
st.pyplot(fig)