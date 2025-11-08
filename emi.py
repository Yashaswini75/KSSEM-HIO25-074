import math

def calculate_emi(principal, annual_rate, tenure_years):
    """
    Calculate monthly EMI based on principal, annual interest rate, and tenure (years).
    """
    if principal <= 0 or annual_rate <= 0 or tenure_years <= 0:
        return 0

    monthly_rate = (annual_rate / 12) / 100
    tenure_months = tenure_years * 12

    emi = (principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months)) / (
        math.pow(1 + monthly_rate, tenure_months) - 1
    )
    return round(emi, 2)
