import streamlit as st

st.set_page_config(page_title="Loan Application - Personal Info", page_icon="🧾", layout="centered")

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
        .stTextInput>div>div>input, .stTextArea textarea {
            border: 1px solid #007BFF;
            border-radius: 8px;
        }
        .stSubheader, .stMarkdown, .stTextInput label, .stTextArea label {
            color: #003366;
        }
        h1, h2, h3 {
            color: #0047AB;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# 🧾 Page Content
# ------------------------
st.title("🧾 Loan Application")
st.subheader("👤 Personal Information")

# Get data from previous steps (uploaded OCR info)
user_profile = st.session_state.get("user_profile", {})

# Prefill fields from extracted details
full_name = st.text_input("Full Name", user_profile.get("Name", ""))
email = st.text_input("Email", st.session_state.get("user_email", ""))
phone = st.text_input("Phone Number", "9988776655")
aadhar = st.text_input("Aadhar Number", "890765XXXXXX1234")
father_name = st.text_input("Father's Name", "Suresh Kumar")
mother_name = st.text_input("Mother's Name", "Suman rao")
guardian_income = st.text_input("Guardian Income", user_profile.get("Income", "₹ 5,00,000"))
college_name = st.text_input("College Name", user_profile.get("College", "ABHIVAN ENGINEERING COLLEGE"))
admission_year = st.text_input("Admission Year", user_profile.get("Admission Year", "2021"))
address = st.text_area("Address", "Not Provided")

st.markdown("---")

if st.button("📅 Schedule Bank Appointment"):
    st.switch_page("pages/schedule_appointment.py")
