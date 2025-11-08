# bank_matching.py
import pandas as pd
import streamlit as st
from pathlib import Path

BANKS_CSV = Path("data") / "banks.csv"

def load_banks():
    return pd.read_csv(BANKS_CSV)

def compute_approval(user_profile, bank_row):
    score = 0
    reasons = []

    # GPA check
    gpa = user_profile.get('extracted_gpa')
    try:
        if gpa is not None and not pd.isna(gpa):
            if float(gpa) >= float(bank_row['min_gpa']):
                score += 40
            else:
                reasons.append(f"GPA {gpa} below min {bank_row['min_gpa']}")
        else:
            reasons.append("GPA missing")
    except Exception:
        reasons.append("GPA parse error")

    # Income check
    inc = user_profile.get('extracted_income')
    try:
        if inc is not None and not pd.isna(inc):
            if float(inc) <= float(bank_row['max_income']):
                score += 30
            else:
                reasons.append(f"Income {inc} > max {bank_row['max_income']}")
        else:
            reasons.append("Income missing")
    except Exception:
        reasons.append("Income parse error")

    # baseline
    score += 30

    # interest influence
    try:
        rate = float(bank_row.get('base_interest_rate', 0))
        if rate <= 10.5:
            score += 5
        elif rate > 12:
            score -= 5
    except Exception:
        pass

    final_score = max(0, min(100, int(score)))
    if final_score >= 75:
        why = "Good fit — meets most criteria."
    else:
        why = "; ".join(reasons) if reasons else "Partial fit."
    return final_score, why


def rank_banks_for_user(user_profile):
    banks = load_banks().to_dict(orient='records')
    results = []

    for b in banks:
        score, why = compute_approval(user_profile, b)
        results.append({
            'bank_id': int(b['bank_id']),
            'bank_name': b['bank_name'],
            'score': score,
            'why': why,
            'interest': float(b.get('base_interest_rate', 0)),
            'max_amount': int(b.get('max_loan_amount', 500000)),
            'approval': int(b.get('approval_rate', 90)),
            'description': b.get('description', "This bank offers education loans under PM-Vidyalaxmi and CSIS schemes.")
        })

    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return results


def display_ranked_banks(user_profile):
    st.markdown("<h2 style='color:#1E90FF;'>🏦 Recommended Banks for You</h2>", unsafe_allow_html=True)
    ranked = rank_banks_for_user(user_profile)

    for i, bank in enumerate(ranked, start=1):
        with st.container():
            st.markdown(f"""
                <div style='background: #f9fafc; padding: 20px; border-radius: 15px; margin-bottom: 20px; 
                            box-shadow: 0 4px 8px rgba(0,0,0,0.05);'>
                    <h4>🏦 {i}. {bank['bank_name']}</h4>
                    <p style='color:#333;'>{bank['description']}</p>
                    <b>Interest Rate:</b> {bank['interest']}% p.a.<br>
                    <b>Max Loan Amount:</b> ₹{bank['max_amount']:,}<br>
                    <b>Approval Rate:</b> {bank['approval']}%<br>
                    <b>Match Score:</b> {bank['score']} / 100<br>
                    <i style='color:gray;'>{bank['why']}</i>
                </div>
            """, unsafe_allow_html=True)

            # Apply Loan Button
            if st.button(f"💰 Apply Loan - {bank['bank_name']}", key=f"apply_{i}"):
                st.session_state["selected_bank"] = bank
                st.switch_page("pages/loan_calculator.py")

    # Summary
    st.markdown("""
    <br><h4>🧩 Summary Insight</h4>
    <p style='color:#333;'>
    PM-Vidyalaxmi and CSIS remain the foundation for government-linked student loans. 
    Banks like SBI, PNB, and BoB offer higher approval odds due to advanced subsidy integration.
    </p>
    """, unsafe_allow_html=True)
