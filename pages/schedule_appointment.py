import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Schedule Appointment", page_icon="📅", layout="centered")

# ------------------------
# 🌈 Custom UI Styling
# ------------------------
st.markdown("""
    <style>
        body {
            background-color: #f8fbff;
        }
        .stButton>button {
            background-color: #007BFF;
            color: white;
            border-radius: 10px;
            height: 3em;
            width: 100%;
            font-weight: bold;
        }
        .stDateInput, .stTimeInput {
            border: 1px solid #007BFF;
            border-radius: 8px;
        }
        .stMarkdown, .stSubheader, label {
            color: #003366;
        }
        h1, h2, h3 {
            color: #0047AB;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# 📅 Page Content
# ------------------------
st.title("📅 Schedule Bank Appointment")
st.subheader("Meet Your Bank Manager")

bank = st.session_state.get("selected_bank", {}).get("bank_name", "Your Selected Bank")

st.markdown(f"### 🏦 Bank: **{bank}**")
st.markdown("Select a date and time for your appointment:")

# Date and Time Selection
today = datetime.now().date()
date = st.date_input("Choose Date", min_value=today, max_value=today + timedelta(days=14))
time = st.time_input("Choose Time")

st.markdown("---")

if st.button("📞 Confirm Appointment"):
    st.success(f"✅ Appointment scheduled with {bank} manager on **{date} at {time}**.")
    st.markdown("📲 The bank manager will contact you shortly for verification.")
