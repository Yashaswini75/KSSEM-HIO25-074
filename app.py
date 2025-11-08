import streamlit as st
import pandas as pd
from pathlib import Path
import json
import matplotlib.pyplot as plt
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from auth_csv import login, register
from ocr_pipeline import process_upload
from bank_matching import rank_banks_for_user
from apply import append_application, list_user_applications
from emi import calculate_emi
#from flask import Flask, render_template
#import pandas as pd

# import your blueprint
#from pages.my_loans import my_loans

# initialize the Flask app
#app = Flask(__name__)

# register blueprint
#app.register_blueprint(my_loans)

#@app.route('/')
#def home():
    #return render_template('index.html')


# ---------------------------------------------------
# Page Config
# ---------------------------------------------------
st.set_page_config(page_title="FinBridge", page_icon="💼", layout="wide")

# ---------------------------------------------------
# Initialize Session State
# ---------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None


def navigate(page_name: str):
    """Simple page navigator that updates session state."""
    st.session_state["page"] = page_name


def safe_rerun():
    """Try to trigger a Streamlit rerun in a version-tolerant way.

    Preference order:
    1. st.rerun()
    2. st.experimental_rerun()
    3. fallback: stop execution and ask user to refresh
    """
    # Prefer the stable API when available
    try:
        # st.rerun exists in modern Streamlit versions
        if hasattr(st, "rerun"):
            st.rerun()
            return
    except Exception:
        # If calling st.rerun raised (e.g., called inside callback), try experimental
        pass

    # Try the older experimental API if present
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        pass

    # Final fallback: stop the script and prompt the user to refresh the page
    try:
        st.info("Please refresh the app to continue (unable to programmatically rerun).")
    except Exception:
        # ignore UI problems
        pass
    st.stop()


def login_register_ui():
    st.title("🔐 Login / Register")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            ok, res = login(email, pw)
            if ok:
                st.session_state["authenticated"] = True
                # res may be dict or message
                if isinstance(res, dict):
                    st.session_state["user_email"] = res.get("email")
                    st.session_state["user_name"] = res.get("name") or res.get("full_name") or res.get("email")
                else:
                    st.session_state["user_email"] = email
                    st.session_state["user_name"] = email
                st.success("Login successful!")
                safe_rerun()
            else:
                st.error(res)

    with tab2:
        name = st.text_input("Full Name", key="reg_name")
        new_email = st.text_input("Email", key="reg_email")
        new_pass = st.text_input("Password", type="password", key="reg_pw")
        if st.button("Register"):
            ok, msg = register(new_email, new_pass, name, "")
            if ok:
                st.success(msg)
            else:
                st.error(msg)


def sidebar_navigation():
    with st.sidebar:
        st.title("Navigation")
        pages = ["Home", "Upload Docs", "Recommendations", "Calculator", "Loan Application", "Schedule Appointment", "My Loans"]

        # If a previous run requested a sidebar change, apply it now before
        # instantiating the radio widget. We must NOT write the radio-backed
        # key during a run where the radio already exists (Streamlit forbids
        # that), so we stage changes in `next_side_nav` and apply them here.
        if "next_side_nav" in st.session_state:
            st.session_state["side_nav"] = st.session_state.pop("next_side_nav")

        # Ensure the radio widget's stored value aligns with the current page
        # If the radio hasn't been created yet in this session, seed it from
        # st.session_state['page'] so programmatic navigation updates are
        # reflected after a rerun.
        if "side_nav" not in st.session_state:
            st.session_state["side_nav"] = st.session_state.get("page", "Home")

        try:
            idx = pages.index(st.session_state.get("page", "Home"))
        except Exception:
            idx = 0

        choice = st.radio("Navigation Menu", pages, index=idx, label_visibility="hidden", key="side_nav")
        if choice != st.session_state.get("page"):
            navigate(choice)
            safe_rerun()

        st.markdown("---")
        st.write(f"👤 {st.session_state.get('user_name') or 'Guest'}")
        if st.button("Logout"):
            # preserve minimal state
            st.session_state.clear()
            st.session_state["authenticated"] = False
            safe_rerun()


def save_uploaded_file(uploaded_file):
    Path("uploads").mkdir(exist_ok=True)
    dest = Path("uploads") / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


# ---------------------------------------------------
# HOME PAGE
# ---------------------------------------------------
def home_page():
    st.markdown("""
        <div style='background-color:#0a66c2;padding:25px;border-radius:12px;color:white;text-align:center;margin-bottom:25px;'>
            <h2>Welcome to FinBridge</h2>
            <p>Your AI-powered student loan recommendation engine</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div style='background-color:white;padding:25px;border-radius:15px;box-shadow:0 2px 10px rgba(0,0,0,0.1);'>
                <h4>📄 1. Upload Documents</h4>
                <p>Upload your academic mark sheets and income proof. Our OCR technology will automatically extract your information.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Get Started"):
            # Request the sidebar to switch on the next run (safe because
            # we avoid writing the radio-backed key during the same run)
            st.session_state["next_side_nav"] = "Upload Docs"
            navigate("Upload Docs")
            safe_rerun()

        st.markdown("""
            <div style='background-color:white;padding:25px;border-radius:15px;margin-top:25px;box-shadow:0 2px 10px rgba(0,0,0,0.1);'>
                <h4>📅 3. Apply & Track</h4>
                <p>Auto-fill loan applications, calculate EMIs, and track your loan status with payment schedules and reminders.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Manage Loans"):
            st.session_state["next_side_nav"] = "My Loans"
            navigate("My Loans")
            safe_rerun()

    with col2:
        st.markdown("""
            <div style='background-color:white;padding:25px;border-radius:15px;box-shadow:0 2px 10px rgba(0,0,0,0.1);'>
                <h4>🤖 2. AI Recommendations</h4>
                <p>Get personalized loan recommendations from top banks based on your academic and financial profile.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("View Recommendations"):
            st.session_state["next_side_nav"] = "Recommendations"
            navigate("Recommendations")
            safe_rerun()

        st.markdown("""
            <div style='background-color:white;padding:25px;border-radius:15px;margin-top:25px;box-shadow:0 2px 10px rgba(0,0,0,0.1);'>
                <h4>🧮 4. Loan Calculator</h4>
                <p>Estimate your EMI, interest, and total repayment easily before applying.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Calculator"):
            st.session_state["next_side_nav"] = "Calculator"
            navigate("Calculator")
            safe_rerun()


# ---------------------------------------------------
# UPLOAD DOCUMENTS PAGE (UPDATED with Styled Table)
# ---------------------------------------------------
# ---------------------------------------------------
# UPLOAD DOCUMENTS PAGE (Enhanced UI)
# ---------------------------------------------------
def upload_page():
    user_email = st.session_state.get("user_email")
    user_name = st.session_state.get("user_name")

    if not user_email:
        st.warning("⚠️ Please log in first to upload documents.")
        return

    st.markdown("""
        <div style='background-color:#f0f6ff;
                    padding:25px;
                    border-radius:15px;
                    text-align:center;
                    margin-bottom:25px;
                    box-shadow:0 2px 8px rgba(0,123,255,0.15);'>
            <h2 style='color:#0a66c2;margin-bottom:5px;'>📄 Upload Your Documents</h2>
            <p style='color:#003366;font-size:15px;'>Upload your academic or financial PDFs — FinBridge will extract details automatically using OCR.</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📤 Upload PDF", type=["pdf"])
    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)

        # File info card
        st.markdown(f"""
            <div style='background-color:#ffffff;
                        border:2px solid #0a66c2;
                        border-radius:12px;
                        padding:15px;
                        margin-bottom:15px;
                        box-shadow:0 4px 10px rgba(0,123,255,0.15);'>
                <b>Filename:</b> {uploaded_file.name} <br>
                <b>Size:</b> {uploaded_file.size / 1024:.1f} KB
            </div>
        """, unsafe_allow_html=True)

        try:
            extracted = process_upload(user_email, [file_path])
            st.success(f"✅ Uploaded successfully: {uploaded_file.name}")

            # Default placeholders for missing values
            defaults = {
                "extracted_name": user_name or "SIYA",
                "extracted_course": "Computer Science and Engineering",
                "extracted_college": "ABHIYAN ENGINEERING COLLEGE",
                "extracted_gpa": "9.2",
                "extracted_income": "₹ 5,00,000",
                "extracted_admission_year": "2021",
                "extracted_dob": "01/01/2002",
                "extracted_usn": "CS21A001"
            }

            merged = {**defaults, **{k: v for k, v in extracted.items() if v not in [None, "", "Not Detected"]}}

            # Persist extracted info to session so other pages can auto-fill forms
            st.session_state['extracted_info'] = merged

            fields_to_show = {
                "Name": merged["extracted_name"],
                "Course": merged["extracted_course"],
                "College": merged["extracted_college"],
                "GPA / CGPA": merged["extracted_gpa"],
                "Income": merged["extracted_income"],
                "Admission Year": merged["extracted_admission_year"],
                "Date of Birth": merged["extracted_dob"],
                "USN": merged["extracted_usn"],
            }

            # --- Fancy Blue-White Card Layout for Extracted Details ---
            #st.markdown("### 🧾 Extracted Details")

            st.markdown("""
                <style>
                    .detail-card {
                        background-color: #ffffff;
                        border: 2px solid #007BFF;
                        border-radius: 15px;
                        padding: 20px;
                        margin-top: 20px;
                        box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
                    }
                    .detail-grid {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 12px 40px;
                    }
                    .detail-label {
                        font-weight: 600;
                        color: #003366;
                        font-size: 16px;
                    }
                    .detail-value {
                        background-color: #f0f6ff;
                        padding: 8px 12px;
                        border-radius: 8px;
                        font-size: 15px;
                        color: #0056b3;
                        border: 1px solid #cfe2ff;
                    }
                    h3 {
                        color: #0047AB;
                        text-align: center;
                        font-weight: 700;
                        margin-bottom: 10px;
                    }
                    .continue-btn button {
                        background-color: #0a66c2;
                        color: white !important;
                        border: none;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-weight: 600;
                        width: 100%;
                        margin-top: 15px;
                        transition: 0.2s ease-in-out;
                    }
                    .continue-btn button:hover {
                        background-color: #004aad;
                        transform: scale(1.02);
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="detail-card">', unsafe_allow_html=True)
            st.markdown('<h3>📋 Document Extraction Summary</h3>', unsafe_allow_html=True)
            st.markdown('<div class="detail-grid">', unsafe_allow_html=True)

            for field, value in fields_to_show.items():
                st.markdown(
                    f"""
                    <div>
                        <div class="detail-label">{field}</div>
                        <div class="detail-value">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div></div>", unsafe_allow_html=True)

            # No direct apply button here per user preference. Guide user to Recommendations.
            st.info("Document processed — go to Recommendations from the sidebar to apply for loans.")

        except Exception as e:
            st.error(f"❌ Error while processing: {e}")



# ---------------------------------------------------
# RECOMMENDATIONS PAGE
# ---------------------------------------------------
def recommendations_page():
    st.markdown("### 🤖 AI Loan Recommendations")
    st.write("Based on your profile, here are your best loan matches:")

    banks = [
        {
            "name": "State Bank of India (SBI)",
            "details": """
SBI integrates the PM-Vidyalaxmi scheme with its flagship Student Loan Scheme, automatically connecting eligible students to the Central Sector Interest Subsidy (CSIS) and Credit Guarantee Fund Scheme for Education Loans (CGFSEL).

Students from weaker sections can access **Padho Pardesh** (for overseas studies) and **Dr. Ambedkar Central Sector Scheme** (for OBC/EWS students), which are seamlessly verified via the Vidya Lakshmi Portal.

**Interest Rate:** Around 8.15%–10.50% p.a., with 0.50% concession for female students and top institutions.
""",
            "approval": "98%"
        },
        {
            "name": "Punjab National Bank (PNB)",
            "details": """
PNB’s **PNB Saraswati** and **PNB Pratibha** Education Loan schemes are directly linked to the PM-Vidyalaxmi and CSIS frameworks. The bank prioritizes economically weaker sections through real-time subsidy mapping and online application status tracking.

PNB also participates in **Dr. Ambedkar Scheme** for meritorious OBC students and **Padho Pardesh** for minority communities.

**Interest Rate:** 8.75%–10.25% p.a., with additional rebates under government schemes.
""",
            "approval": "96%"
        },
        {
            "name": "Bank of Baroda (BoB)",
            "details": """
BoB offers the **Baroda Gyan** and **Baroda Scholar** education loans via the PM-Vidyalaxmi portal, ensuring automatic integration with CSIS and CGFSEL.

It also provides the **Skill Loan Scheme** for vocational courses under the Government of India’s Skill India Mission.

**Interest Rate:** 8.55%–10.65% p.a., with concessions for girl students and premium institutions.
""",
            "approval": "94%"
        },
        {
            "name": "Canara Bank",
            "details": """
Canara Bank’s **Vidya Turant** and Education Loan Scheme are synchronized with PM-Vidyalaxmi, ensuring automatic verification for CSIS and CGFSEL benefits.

It also participates in **Dr. Ambedkar Interest Subsidy Scheme** and **Padho Pardesh** for minority and backward community students.

**Interest Rate:** 8.60%–10.40% p.a., with 0.40% concession for female candidates.
""",
            "approval": "92%"
        },
        {
            "name": "Union Bank of India",
            "details": """
Union Bank links PM-Vidyalaxmi and CSIS directly to its **Education Loan Scheme for Higher Studies**. The bank has digitized the moratorium interest subsidy claim process, reducing paperwork for students.

It also includes **Vocational and Skill Development Loans** under the **NSDC Skill India Scheme** for short-term technical programs.

**Interest Rate:** 8.70%–10.50% p.a., with interest-free moratorium for eligible applicants.
""",
            "approval": "90%"
        },
        {
            "name": "HDFC Bank",
            "details": """
Though a private sector bank, HDFC aligns selected education loans with PM-Vidyalaxmi and **National Scholarship Portal** for subsidy validation.

It also collaborates with **MahaDBT (Maharashtra)** and **Karnataka Udyogini Yojana** to support local students.

**Interest Rate:** 9.25%–11.50% p.a., depending on institution ranking and applicant profile.
""",
            "approval": "88%"
        },
        {
            "name": "ICICI Bank",
            "details": """
ICICI integrates the PM-Vidyalaxmi subsidy options with its **Education Loan for Higher Studies**, supported by an AI-based approval scoring system.

Apart from central subsidies, ICICI supports the **Dr. Ambedkar Scheme** and **National Minorities Development Loan Schemes** for select applicants.

**Interest Rate:** 9.00%–11.25% p.a., with dynamic concession for strong academic profiles.
""",
            "approval": "87%"
        },
        {
            "name": "Axis Bank",
            "details": """
Axis Bank’s **Education Loan Advantage Scheme** incorporates PM-Vidyalaxmi and CSIS-based subsidies for Indian and overseas studies.

It also offers **Women Empowerment Education Concessions** under the **Stand Up India** initiative, making it unique among private players.

**Interest Rate:** 8.90%–11.00% p.a., with up to 0.75% discount for top 100 institutes.
""",
            "approval": "86%"
        },
        {
            "name": "IDBI Bank",
            "details": """
IDBI includes PM-Vidyalaxmi, CSIS, and CGFSEL under its **Education Loan for India** product. The bank also implements the **Skill Loan Scheme** for vocational training under Skill India and **Dr. Ambedkar Scheme** for OBC/Minority groups.

Loans up to ₹7.5 lakh are collateral-free under the guarantee fund, and interest subsidy is auto-credited post verification.

**Interest Rate:** 8.85%–10.75% p.a., with female and merit-based concessions.
""",
            "approval": "84%"
        },
        {
            "name": "Indian Bank",
            "details": """
Indian Bank’s **IB Education Loan Scheme** fully integrates with PM-Vidyalaxmi, providing Aadhaar-linked verification for CSIS and **Padho Pardesh** eligibility.

It also offers **Skill India Loans** for technical or paramedical courses, especially targeting rural students through CSC (Common Service Centre) partnerships.

**Interest Rate:** 8.65%–10.60% p.a., with rebates for girl students and those from EWS backgrounds.
""",
            "approval": "82%"
        },
    ]

    # --- Display bank recommendations ---
    for i, bank in enumerate(banks, start=1):
        st.markdown(f"""
        <div style="
            background-color:#f8faff;
            padding:22px;
            border-radius:18px;
            margin-bottom:20px;
            box-shadow:0 2px 6px rgba(0,0,0,0.08);
        ">
            <h4 style="color:#2b4c7e; margin-bottom:10px;">🏦 {i}. {bank['name']}</h4>
            <p style="font-size:15px; line-height:1.7; color:#333;">{bank['details']}</p>
            <p style="font-weight:600; color:#2b9348; margin-top:8px;">✅ Approval Rate: {bank['approval']}</p>
        </div>
        """, unsafe_allow_html=True)
        # Streamlit button for each bank: go to Calculator with defaults
        apply_key = f"reco_apply_{i}"
        if st.button("Apply for Loan", key=apply_key):
            # Bank-specific defaults: max loan amount and fixed interest rate
            name = bank.get('name', '')
            # reasonable defaults; customize per bank where needed
            bank_defaults = {
                'State Bank of India': {'loan_min': 0, 'loan_max': 500000, 'rate': 8.15},
                'Punjab National Bank': {'loan_min': 0, 'loan_max': 450000, 'rate': 8.75},
                'Bank of Baroda': {'loan_min': 0, 'loan_max': 400000, 'rate': 8.55},
                'Canara Bank': {'loan_min': 0, 'loan_max': 400000, 'rate': 8.60},
                'Union Bank of India': {'loan_min': 0, 'loan_max': 400000, 'rate': 8.70},
                'HDFC Bank': {'loan_min': 0, 'loan_max': 350000, 'rate': 9.25},
                'ICICI Bank': {'loan_min': 0, 'loan_max': 350000, 'rate': 9.00},
                'Axis Bank': {'loan_min': 0, 'loan_max': 350000, 'rate': 8.90},
                'IDBI Bank': {'loan_min': 0, 'loan_max': 375000, 'rate': 8.85},
                'Indian Bank': {'loan_min': 0, 'loan_max': 300000, 'rate': 8.65},
            }

            # choose a match by substring to be resilient to parentheses in names
            chosen = None
            for k, v in bank_defaults.items():
                if k in name:
                    chosen = v
                    break

            if chosen is None:
                chosen = {'loan_min': 50000, 'loan_max': 350000, 'rate': 10.5}

            # prefill the calculator with bank-specific constraints and a fixed rate
            st.session_state['calc_prefill'] = {
                'bank_id': i,
                'bank_name': bank.get('name'),
                'loan_amount': chosen['loan_max'],
                'loan_min': chosen.get('loan_min', 0),
                'loan_max': chosen.get('loan_max', 350000),
                'fixed_rate': True,
                'fixed_rate_value': chosen.get('rate', 10.5),
                'tenure_years': 5,
                'processing_fee_pct': 1.0,
            }
            # Stage sidebar update for the next run so the radio reflects the new page
            st.session_state['next_side_nav'] = 'Calculator'
            navigate("Calculator")
            safe_rerun()

    # --- Summary Section ---
    st.markdown("""
    <div style="
        background-color:#eef3ff;
        border-left:6px solid #2b4c7e;
        padding:20px;
        border-radius:12px;
        margin-top:25px;
    ">
        <h4 style="color:#2b4c7e;">🧩 Summary Insight</h4>
        <p style="font-size:15px; line-height:1.6;">
        While PM-Vidyalaxmi and CSIS form the backbone of government-linked education loans across all banks,
        schemes like <b>Padho Pardesh</b>, <b>Dr. Ambedkar Interest Subsidy</b>, and <b>Skill India Loans</b> are selectively adopted —
        often based on a bank’s digital readiness, region-specific demand, or partnership with the
        <b>Ministry of Education</b> and <b>Minority Affairs</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)



# ---------------------------------------------------
# CALCULATOR PAGE
# ---------------------------------------------------
def calculator_page():
    st.title("📊 Loan EMI Calculator")
    st.markdown("Use the sliders below to estimate your loan EMI, interest, and total repayment.")

    # Prefill from recommendations if available
    prefill = st.session_state.get('calc_prefill', {}) or {}
    if prefill:
        st.markdown(f"**Selected bank:** {prefill.get('bank_name', '')}")

    # (Continue button inserted after sliders so values exist)

    principal_default = int(prefill.get('loan_amount', 350000))
    tenure_default = int(prefill.get('tenure_years', 8))

    # Bank-specific slider bounds
    loan_min = int(prefill.get('loan_min', 50000))
    loan_max = int(prefill.get('loan_max', 2000000))

    # If the bank defines a fixed interest, hide the interest slider and
    # use the predefined value. Otherwise, allow adjusting the rate.
    fixed_rate = bool(prefill.get('fixed_rate', False))
    fixed_rate_value = float(prefill.get('fixed_rate_value', 0.0)) if fixed_rate else None

    principal = st.slider("💰 Loan Amount (₹)", loan_min, loan_max, principal_default, 5000)

    if fixed_rate:
        # show the bank's fixed rate as a read-only metric
        st.markdown(f"**Interest Rate (fixed by bank):** {fixed_rate_value:.2f}%")
        annual_rate = fixed_rate_value
    else:
        annual_rate_default = float(prefill.get('annual_rate', 10.5))
        annual_rate = st.slider("📈 Interest Rate (%)", 5.0, 20.0, annual_rate_default, 0.1)

    tenure_years = st.slider("⏳ Loan Tenure (Years)", 1, 30, tenure_default, 1)

    # Button to continue to the multipage personal info screen (pages/personal_info.py)
    if st.button("Continue to Personal Info"):
        # Merge any extracted info with sensible defaults so the
        # Personal Info form is always shown with populated values.
        extracted = st.session_state.get('extracted_info', {}) or {}

        defaults = {
            'extracted_name': st.session_state.get('user_name') or "Applicant Name",
            'email': st.session_state.get('user_email') or "applicant@example.com",
            'phone': extracted.get('phone') or "9988776655",
            'extracted_usn': extracted.get('extracted_usn') or "CS21A001",
            'father_name': extracted.get('father_name') or "Suresh Kumar",
            'mother_name': extracted.get('mother_name') or "Suman rao",
            'address': extracted.get('address') or "Not Provided",
            'extracted_income': extracted.get('extracted_income') or "₹ 5,30,000",
            'extracted_college': extracted.get('extracted_college') or "ABHIYAN ENGINEERING COLLEGE",
            'extracted_admission_year': extracted.get('extracted_admission_year') or str(datetime.now().year),
        }

        # Values from `extracted` override defaults when present and non-empty
        merged = {**defaults, **{k: v for k, v in extracted.items() if v not in [None, "", "Not Detected"]}}

        # Persist merged extracted info so the Loan Application screen shows filled fields
        st.session_state['extracted_info'] = merged

        # Build a user_profile mapping expected by pages/personal_info.py
        user_profile = {
            "Name": merged.get('extracted_name'),
            "Income": merged.get('extracted_income'),
            "College": merged.get('extracted_college'),
            "Admission Year": merged.get('extracted_admission_year'),
        }
        st.session_state['user_profile'] = user_profile

        # store the current calculator choices into session to include in application
        st.session_state['application_prefill'] = {
            'bank_id': prefill.get('bank_id'),
            'bank_name': prefill.get('bank_name'),
            'loan_amount': principal,
            'tenure_years': tenure_years,
            'annual_rate': annual_rate,
        }

        # Switch to the existing multipage personal info page (preferred),
        # otherwise fall back to the in-app Loan Application page.
        try:
            st.switch_page("pages/personal_info.py")
        except Exception:
            st.session_state['next_side_nav'] = 'Loan Application'
            navigate('Loan Application')
            safe_rerun()

    emi = calculate_emi(principal, annual_rate, tenure_years)
    tenure_months = tenure_years * 12
    total_payment = round(emi * tenure_months, 2)
    total_interest = round(total_payment - principal, 2)
    processing_fee = 3500

    st.markdown("### 🧮 Loan Details")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Monthly EMI", f"₹{emi:,.2f}")
        st.metric("Total Repayment", f"₹{total_payment:,.2f}")
    with c2:
        st.metric("Total Interest", f"₹{total_interest:,.2f}")
        st.metric("Processing Fee", f"₹{processing_fee:,.2f}")

    st.success("💡 Adjust sliders to see how EMI changes!")


def loan_application_page():
    st.title("📝 Loan Application")
    st.markdown("Fill personal details below. Fields are pre-filled from your uploaded documents where available.")

    extracted = st.session_state.get('extracted_info', {}) or {}
    app_prefill = st.session_state.get('application_prefill', {}) or {}

    # Personal Info section
    st.subheader("Personal Info")
    full_name = st.text_input("Full Name", value=extracted.get('extracted_name') or st.session_state.get('user_name') or "", key='app_full_name')
    email = st.text_input("Email", value=st.session_state.get('user_email') or extracted.get('email') or "", key='app_email')
    phone = st.text_input("Phone Number", value=extracted.get('phone') or "", key='app_phone')
    aadhar = st.text_input("Aadhar Number", value=extracted.get('extracted_usn') or "", key='app_aadhar')
    father = st.text_input("Father's Name", value=extracted.get('father_name') or "", key='app_father')
    mother = st.text_input("Mother's Name", value=extracted.get('mother_name') or "", key='app_mother')
    guardian_income = st.text_input("Guardian Income", value=extracted.get('extracted_income') or "", key='app_guardian_income')
    college_name = st.text_input("College Name", value=extracted.get('extracted_college') or "", key='app_college')
    admission_year = st.text_input("Admission Year", value=extracted.get('extracted_admission_year') or "", key='app_admission_year')
    address = st.text_area("Address", value=extracted.get('address') or "", key='app_address')

    st.markdown("---")
    st.subheader("Application Summary")
    st.write(f"**Bank:** {app_prefill.get('bank_name', '')}")
    st.write(f"**Requested Loan Amount:** ₹{app_prefill.get('loan_amount', '')}")
    st.write(f"**Tenure (years):** {app_prefill.get('tenure_years', '')}")

    if st.button("Schedule Bank Appointment"):
        # collect filled data
        filled = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'aadhar': aadhar,
            'father_name': father,
            'mother_name': mother,
            'guardian_income': guardian_income,
            'college_name': college_name,
            'admission_year': admission_year,
            'address': address,
            'loan_amount': app_prefill.get('loan_amount'),
            'tenure_years': app_prefill.get('tenure_years'),
            'annual_rate': app_prefill.get('annual_rate'),
            'bank_name': app_prefill.get('bank_name')
        }
        user_email = st.session_state.get('user_email')
        bank_id = app_prefill.get('bank_id', 0) or 0
        # append application record
        try:
            app_id = append_application(user_email or email, bank_id, filled)
            st.session_state['last_app_id'] = app_id
            st.success(f"Application {app_id} saved. Proceed to schedule appointment.")
            st.session_state['next_side_nav'] = 'Schedule Appointment'
            navigate('Schedule Appointment')
            safe_rerun()
        except Exception as e:
            st.error(f"Could not save application: {e}")


def schedule_appointment_page():
    st.title("📅 Schedule Bank Appointment")
    app_id = st.session_state.get('last_app_id')
    app_prefill = st.session_state.get('application_prefill', {}) or {}
    user_email = st.session_state.get('user_email')
    bank_id = app_prefill.get('bank_id', 0) or 0

    if not app_id:
        st.warning("No application found. Please start from the Calculator and continue to Personal Info first.")
        return

    st.write(f"Scheduling appointment for Application ID: {app_id} — Bank: {app_prefill.get('bank_name','')}" )

    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Select Date")
    with col2:
        time = st.time_input("Select Time")

    if st.button("Confirm Appointment"):
        dt = datetime.combine(date, time)
        dt_str = dt.strftime("%Y-%m-%d %H:%M")
        try:
            from apply import schedule_appointment_custom
            appt_id, scheduled = schedule_appointment_custom(user_email, app_id, bank_id, dt_str)
            st.success(f"Appointment scheduled: {scheduled} (ID: {appt_id})")
            st.info("Call option: click 'Show Call Details' to view bank contact and prepare for the call.")
            if st.button("Show Call Details"):
                st.markdown("**Bank Manager Contact:** +91-XXXXXXXXXX (simulated)")
        except Exception as e:
            st.error(f"Failed to schedule appointment: {e}")


# ---------------------------------------------------
# MY LOANS PAGE
# ---------------------------------------------------
def my_loans_page():
    st.header("📅 My Loan Applications")

    # Dummy loan data for now (replace later with CSV or database)
    apps = [
        {"app_id": 1, "status": "Pending"},
        {"app_id": 2, "status": "Approved", "bank_name": "State Bank of India"}
    ]

    st.success(f"Found {len(apps)} loan application(s).")

    for app in apps:
        with st.expander(f"📄 Application ID: {app['app_id']} | Status: {app['status']}"):

            if app["status"].lower() == "approved":
                st.subheader("📈 Loan Payment Progress (Line Graph)")

                # Example payment history data
                data = {
                    "Date": [
                        "2025-09-01",
                        "2025-10-01",
                        "2025-11-01",
                        "2025-12-01"
                    ],
                    "Interest Paid": [2000, 1800, 1600, 1500],
                    "Principal Paid": [5000, 5500, 6000, 6500]
                }
                df = pd.DataFrame(data)
                df["Date"] = pd.to_datetime(df["Date"])

                # Line chart
                fig, ax = plt.subplots(figsize=(7, 3.5))
                ax.plot(df["Date"], df["Principal Paid"], marker='o', label="Principal Paid", linewidth=2)
                ax.plot(df["Date"], df["Interest Paid"], marker='s', label="Interest Paid", linewidth=2, linestyle="--")

                ax.set_xlabel("Payment Date")
                ax.set_ylabel("Amount (₹)")
                ax.set_title("Loan Repayment Over Time")
                ax.legend()
                ax.grid(True, linestyle='--', alpha=0.6)

                st.pyplot(fig)

                # Summary details
                total_paid = df["Principal Paid"].sum() + df["Interest Paid"].sum()
                total_amount = 100000
                remaining = total_amount - df["Principal Paid"].sum()

                st.write(f"**Total Loan Amount:** ₹{total_amount:,}")
                st.write(f"**Total Paid So Far:** ₹{total_paid:,}")
                st.write(f"**Remaining Principal:** ₹{remaining:,}")

                # ----------------------------
                #  LOAN TAKEOVER - TWO STEP FLOW
                # ----------------------------
                st.markdown("---")
                st.subheader("🔁 Loan Takeover")

                if "takeover_step" not in st.session_state:
                    st.session_state["takeover_step"] = 0
                if "chosen_bank" not in st.session_state:
                    st.session_state["chosen_bank"] = None

                # Step 0: start button
                if st.session_state["takeover_step"] == 0:
                    if st.button(f"Request Loan Takeover for Application {app['app_id']}"):
                        st.session_state["takeover_step"] = 1
                        st.rerun()

                # ----------------------------------------------------
                # STEP 1 - Choose Bank
                # ----------------------------------------------------
                elif st.session_state["takeover_step"] == 1:
                    st.info("Step 1 of 2 – Choose the bank you’d like to take over your loan.")

                    # Example bank list and rates (replace with data/banks.csv if available)
                    all_banks = [
                        {"id": "SBI", "name": "State Bank of India", "rate": 8.15},
                        {"id": "PNB", "name": "Punjab National Bank", "rate": 8.75},
                        {"id": "BoB", "name": "Bank of Baroda", "rate": 8.55},
                        {"id": "Canara", "name": "Canara Bank", "rate": 8.60},
                        {"id": "HDFC", "name": "HDFC Bank", "rate": 9.25},
                        {"id": "ICICI", "name": "ICICI Bank", "rate": 9.00},
                        {"id": "Axis", "name": "Axis Bank", "rate": 8.90},
                        {"id": "IDBI", "name": "IDBI Bank", "rate": 8.85},
                        {"id": "Indian", "name": "Indian Bank", "rate": 8.65},
                    ]

                    current_bank = app.get("bank_name") or app.get("bank_id") or ""
                    available_banks = [b for b in all_banks if b["name"] != current_bank and b["id"] != current_bank]

                    choice = st.selectbox(
                        "Select takeover bank",
                        ["-- select bank --"]
                        + [f"{b['name']} — {b['rate']} % p.a." for b in available_banks],
                        key=f"bank_select_{app['app_id']}"
                    )

                    if choice != "-- select bank --":
                        chosen = next(b for b in available_banks if f"{b['name']} — {b['rate']} % p.a." == choice)
                        st.session_state["chosen_bank"] = chosen
                        if st.button("Next → Preview Terms"):
                            st.session_state["takeover_step"] = 2
                            st.rerun()

                    if st.button("Cancel"):
                        st.session_state["takeover_step"] = 0
                        st.session_state["chosen_bank"] = None
                        st.rerun()

                # ----------------------------------------------------
                # STEP 2 - Preview & Confirm
                # ----------------------------------------------------
                elif st.session_state["takeover_step"] == 2:
                    chosen_bank = st.session_state["chosen_bank"]
                    st.info(f"Step 2 of 2 – Preview Takeover Details for {chosen_bank['name']}")

                    total_amount = float(app.get("total_amount", app.get("loan_amount", 0) or 100000))
                    paid_principal = float(app.get("paid_amount", app.get("principal_paid", 0) or 0))
                    remaining_principal = max(total_amount - paid_principal, 0.0)

                    tenure_years = float(app.get("tenure_years", 5))
                    total_months = int(tenure_years * 12)
                    payments_made = int(app.get("payments_made", 0))
                    remaining_months = max(total_months - payments_made, 1)

                    r = chosen_bank["rate"] / 12 / 100
                    emi = remaining_principal * r * (1 + r) ** remaining_months / ((1 + r) ** remaining_months - 1)
                    total_interest = emi * remaining_months - remaining_principal

                    st.markdown("### 🧾 Takeover Summary")
                    st.write(f"**Chosen Bank:** {chosen_bank['name']}")
                    st.write(f"**Rate of Interest:** {chosen_bank['rate']} % p.a.")
                    st.write(f"**Remaining Principal:** ₹ {remaining_principal:,.2f}")
                    st.write(f"**Remaining Tenure:** {remaining_months} months")
                    st.write(f"**Estimated EMI:** ₹ {emi:,.2f}")
                    st.write(f"**Total Interest (New Bank):** ₹ {total_interest:,.2f}")

                    # ----------------------------------------------------
                    # DOWNLOAD NOC FROM PREVIOUS BANK
                    # ----------------------------------------------------
                    import io
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4

                    previous_bank = app.get("bank_name", "Your Previous Bank")

                    st.markdown("### 🧾 Download NOC from Previous Bank")

                    if st.button(f"⬇️ Download NOC from {previous_bank}"):
                        # Generate NOC PDF dynamically
                        buffer = io.BytesIO()
                        c = canvas.Canvas(buffer, pagesize=A4)
                        text = c.beginText(60, 750)
                        text.setFont("Helvetica", 12)
                        text.textLine(f"Date: {pd.Timestamp.now().strftime('%d-%m-%Y')}")
                        text.textLine("")
                        text.textLine(f"To Whom It May Concern,")
                        text.textLine("")
                        text.textLine(f"This is to certify that {previous_bank} has no objection to the")
                        text.textLine(f"transfer of the existing loan (Application ID: {app['app_id']})")
                        text.textLine(f"to another financial institution as per the borrower's request.")
                        text.textLine("")
                        text.textLine("We confirm that all dues up to this date are settled,")
                        text.textLine("and we issue this No Objection Certificate accordingly.")
                        text.textLine("")
                        text.textLine(f"Sincerely,")
                        text.textLine(f"{previous_bank} - Loan Department")
                        c.drawText(text)
                        c.showPage()
                        c.save()

                        buffer.seek(0)
                        st.download_button(
                            label=f"📄 Click to Download NOC (from {previous_bank})",
                            data=buffer,
                            file_name=f"NOC_{previous_bank.replace(' ', '_')}_App{app['app_id']}.pdf",
                            mime="application/pdf"
                        )

                    # Confirm / Cancel buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirm Takeover"):
                            import csv, os
                            from datetime import datetime
                            takeover_row = {
                                "user_email": st.session_state.get("user_email", "unknown"),
                                "app_id": app["app_id"],
                                "new_bank_id": chosen_bank["id"],
                                "new_bank_name": chosen_bank["name"],
                                "new_rate": chosen_bank["rate"],
                                "remaining_principal": remaining_principal,
                                "requested_at": datetime.now().isoformat(),
                                "status": "requested"
                            }

                            os.makedirs("data", exist_ok=True)
                            path = "data/takeovers.csv"
                            write_header = not os.path.exists(path)
                            with open(path, "a", newline="", encoding="utf-8") as f:
                                writer = csv.DictWriter(f, fieldnames=list(takeover_row.keys()))
                                if write_header:
                                    writer.writeheader()
                                writer.writerow(takeover_row)

                            st.success("🎉 Takeover request submitted! A bank officer will contact you shortly.")
                            st.session_state["takeover_step"] = 0
                            st.session_state["chosen_bank"] = None

                    with col2:
                        if st.button("⬅️ Back to Bank Selection"):
                            st.session_state["takeover_step"] = 1
                            st.rerun()

            else:
                st.info("⏳ Application is still pending approval.")





# ---------------------------------------------------
# MAIN APP FLOW
# ---------------------------------------------------
if not st.session_state["authenticated"]:
    login_register_ui()
else:
    sidebar_navigation()
    page = st.session_state["page"]

    if page == "Home":
        home_page()
    elif page == "Upload Docs":
        upload_page()
    elif page == "Recommendations":
        recommendations_page()
    elif page == "Calculator":
        calculator_page()
    elif page == "Loan Application":
        loan_application_page()
    elif page == "Schedule Appointment":
        schedule_appointment_page()
    elif page == "My Loans":
        my_loans_page()
