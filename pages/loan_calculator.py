import streamlit as st
import math

st.set_page_config(page_title="Loan Calculator", page_icon="💰", layout="centered")

st.title("💰 Loan Calculator")

# Check if a bank was selected
if "selected_bank" not in st.session_state:
    st.warning("⚠️ Please go to 'Recommendations' and click 'Apply Loan' for a bank first.")
    st.stop()

# Retrieve bank details
bank = st.session_state["selected_bank"]
bank_name = bank["bank_name"]
interest = float(bank.get("base_interest_rate", 10.0))
max_amount = float(bank.get("max_amount", 500000))  # fallback

st.subheader(f"🏦 {bank_name}")
st.markdown(f"**Interest Rate:** {interest}% per annum")

# Loan amount slider
loan_amount = st.slider(
    "Select Loan Amount",
    min_value=10000,
    max_value=int(max_amount),
    value=int(max_amount * 0.5),
    step=5000,
    format="₹%d"
)

# Tenure slider (in years)
tenure = st.slider("Select Tenure (Years)", 1, 10, 5)

# EMI Calculation
r = interest / (12 * 100)
n = tenure * 12
emi = (loan_amount * r * (1 + r) ** n) / ((1 + r) ** n - 1)
total_payment = emi * n
total_interest = total_payment - loan_amount

# Display results
st.markdown("### 📊 Loan Summary")
st.write(f"**Loan Amount:** ₹{loan_amount:,.0f}")
st.write(f"**Tenure:** {tenure} years")
st.write(f"**Interest Rate:** {interest}%")
st.write(f"**Monthly EMI:** ₹{emi:,.2f}")
st.write(f"**Total Payment:** ₹{total_payment:,.2f}")
st.write(f"**Total Interest:** ₹{total_interest:,.2f}")

st.success("✅ You can proceed with this loan if you're satisfied with the terms.")
if st.button("➡️ Continue to Personal Address"):
    st.switch_page("pages/personal_info.py")

