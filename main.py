#MUREX EX 2 PROBLEM ONE

#IMPORTS
from datetime import date
from dateutil.relativedelta import relativedelta
from scipy.optimize import brentq
import numpy as np
import pandas as pd

#Bond Variables
valuation_date = date(2026, 1, 15)
maturity_date = date(2029, 1, 15)
notional = 10000000
spread = 0.0075
cupon_frequency = 4

print("Valuation date:", valuation_date)
print("Maturity date:", maturity_date)
print("Notional:", notional)
print("Spread:", spread)

pillar_months = [1, 3, 6, 9, 12, 18, 24, 36, 60]
pillars= []

#Convert maturity pillars to actual/365 and store converted in pillars list
for months in pillar_months:
    #Increment pillar date by months from valuation date
    pillar_date = valuation_date + relativedelta(months=months)
    days = (pillar_date - valuation_date).days
    t = days/365
    pillars.append(t)

'''
#maturity pillar conversion test.
for months, t in zip(pillar_months, pillars):
    print(f"{months}M: {t:.9f} years")
'''

projection_rates = [
    0.0272, 0.0276, 0.0281,
    0.0286, 0.0291, 0.0300,
    0.0308, 0.0320, 0.0334
]

discount_rates = [
    0.0248, 0.0251, 0.0256,
    0.0261, 0.0266, 0.0274,
    0.0282, 0.0294, 0.0308
]

#INTERPOLATES THE PILLAR INTO 3 MONTH GAPS
def interpolate_rate(t, pillars, rates):
    return np.interp(t, pillars, rates)


'''
print("INTERPROLATION TESTS")
t= 4/12
rate =  interpolate_rate(t, pillars, projection_rates)

print(rate)
'''
#Returns the discount factor for a given time t, given a set of pillars and rates
def discount_factor(t, pillars, rates):
    rate = interpolate_rate(t, pillars, rates)
    return np.exp(-rate*t)
'''
print("DISCOUNT FACTOR TESTS")
df = discount_factor(1, pillars, discount_rates)
print(f"1-year discount factor: {df:.9f}")
'''

#Generate Quarterly Cupon Dates
payment_dates = []
current_date = valuation_date

#Add dates in 3 month increments to payment dates list
while current_date < maturity_date:
    current_date += relativedelta(months=3)
    payment_dates.append(current_date)

'''
#Output List in Table Format
print("\nCupon Payment Dates:")
for i, payment_date in enumerate(payment_dates, start=1):
    print(f"Cupon {i}: {payment_date}")
'''
#Calculate Cupon Accrual Periods

previous_date = valuation_date

accrual_periods = []

for payment_date in payment_dates:
    days = (payment_date - previous_date).days
    alpha = days/365
    accrual_periods.append(alpha)

    '''
    print(f"{previous_date} to {payment_date}: "
          f"{days} days, alpha = {alpha:.6f}"
          )
    '''
    previous_date = payment_date

#FIND FORWARD RATES

def forward_rate(start_date, end_date):
    t1 = (start_date - valuation_date).days/365
    t2 = (end_date - valuation_date).days/365

    alpha = (end_date - start_date).days/365

    #AT VALUTATION DATE, THE DISCOUNT FACTOR EQUALS 1

    if t1 == 0:
        df1 = 1.0
    else:
        df1 = discount_factor(t1, pillars, projection_rates)

    df2 = discount_factor(t2, pillars, projection_rates)

    forward = (df1 / df2 - 1) / alpha

    return forward

'''
FIRST FORWARD RATE TEST

first_forward = forward_rate(
    valuation_date,
    payment_dates[0]
)

print(f"First forward rate: {first_forward:.6%}")

'''

#CALCULATE THE PROJECTED COUPON CASH FLOWS

cashflows = []
previous_date = valuation_date

for i, payment_date in enumerate(payment_dates, start=1):
    alpha = (payment_date - previous_date).days/365
    forward = forward_rate(previous_date, payment_date)
    coupon = notional * (forward + spread) * alpha
    cashflows.append(coupon)

    '''
    print(
        f"Coupon {i}: "
        f"Forward = {forward:.6%}, "
        f"Cash Flow = ${coupon:,.2f}"
    )
    '''

    previous_date = payment_date


#PRESENT VALUES OF CASH FLOWS

coupon_present_values = []

for payment_date, coupon in zip(payment_dates, cashflows):
    t = (payment_date - valuation_date).days/365

    df = discount_factor(t, pillars, discount_rates)

    pv = coupon * df

    coupon_present_values.append(pv)

    '''
    print(
        f"Date: {payment_date}, "
        f"DF: {df:.9f}, "
        f"PV: ${pv:,.2f}"
    )
    '''

# Present value of principal repayment

T = (maturity_date - valuation_date).days / 365

principal_df = discount_factor(T, pillars, discount_rates)

principal_pv = notional * principal_df

#TOTAL THEORETICAL NPV

total_coupon_pv = sum(coupon_present_values)

bond_npv = total_coupon_pv + principal_pv

print("\nBond Valuation Results")
print(f"PV of Coupons:   ${total_coupon_pv:,.2f}")
print(f"PV of Principal: ${principal_pv:,.2f}")
print(f"Theoretical NPV: ${bond_npv:,.2f}")

'''
ASSUMPTIONS Q1
Unadjusted quarterly payment dates.
Actual/365 accrual fractions.
Continuous compounding of zero rates.
Linear interpolation of zero rates.
No accrued interest at valuation.
'''

# MUREX EX 2 Q2

def bond_price_from_yield(yield_rate):
    price = 0

    for payment_date,  coupon in zip(payment_dates, cashflows):
        t = (payment_date - valuation_date).days/365
        pv = coupon * np.exp(-yield_rate * t)
        price += pv

    #discounted principal repayment
    T = (maturity_date - valuation_date).days /365
    price += notional * np.exp(-yield_rate * T)

    return price

def yield_equation(yield_rate):
    return bond_price_from_yield(yield_rate) - bond_npv


#USE ROOT FINDER TO FIND THE YIELD THAT APROX MATCHES THE NPV
bond_yield = brentq( yield_equation, -0.10, 0.20)

print(f"Bond Yield: {bond_yield:.6%}")

recalculated_price = bond_price_from_yield(bond_yield)

'''
print(f"Original NPV:     ${bond_npv:,.2f}")
print(f"Recalculated NPV: ${recalculated_price:,.2f}")
print(f"Difference:       ${recalculated_price - bond_npv:.8f}")
'''

#MUREX EX 2 Q3
def value_bond(proj_rates, disc_rates):

    schedule = []
    npv = 0.0
    previous_date = valuation_date

    for i, payment_date in enumerate(payment_dates, start=1):

        t1 = (previous_date - valuation_date).days / 365
        t2 = (payment_date - valuation_date).days / 365
        alpha = (payment_date - previous_date).days / 365

        # Project forward rate
        df1 = discount_factor(t1, pillars, proj_rates)
        df2 = discount_factor(t2, pillars, proj_rates)

        forward = (df1 / df2 - 1) / alpha

        # Calculate cash flows
        coupon = notional * (forward + spread) * alpha
        principal = notional if payment_date == maturity_date else 0

        total_cf = coupon + principal

        # Discount cash flows
        df_discount = discount_factor(t2, pillars, disc_rates)
        pv = total_cf * df_discount

        npv += pv

        schedule.append({
            "Coupon": i,
            "Start Date": previous_date,
            "Payment Date": payment_date,
            "Forward Rate": forward,
            "Coupon CF": coupon,
            "Principal": principal,
            "Discount Factor": df_discount,
            "PV": pv
        })

        previous_date = payment_date

    return npv, schedule

def calculate_npv(proj_rates, disc_rates):
    npv, _ = value_bond(proj_rates, disc_rates)
    return npv

#BASE VALUATION WITH ORIGINAL RATES
bond_npv, schedule = value_bond(
    projection_rates,
    discount_rates
)
'''
#TEST: Calculate NPV with original rates
base_npv = calculate_npv(projection_rates, discount_rates)
print(f"Base NPV: ${base_npv:,.2f}")
'''

# One basis point
bp = 0.0001

# Convert lists to NumPy arrays
proj = np.array(projection_rates)
disc = np.array(discount_rates)

# Projection curve parallel DV01
proj_npv_up = calculate_npv(proj + bp, disc)
proj_npv_down = calculate_npv(proj - bp, disc)

proj_dv01 = (proj_npv_down - proj_npv_up) / 2

# Discount curve parallel DV01
disc_npv_up = calculate_npv(proj, disc + bp)
disc_npv_down = calculate_npv(proj, disc - bp)

disc_dv01 = (disc_npv_down - disc_npv_up) / 2

print(f"\nProjection Curve DV01: ${proj_dv01:,.2f}")
print(f"Discount Curve DV01:   ${disc_dv01:,.2f}")

# Individual pillar DV01 calculations

pillar_names = [
    "1M", "3M", "6M", "9M", "1Y",
    "18M", "2Y", "3Y", "5Y"
]

projection_pillar_dv01 = []
discount_pillar_dv01 = []

for i in range(len(pillars)):

    # Projection curve pillar bump
    proj_up = proj.copy()
    proj_down = proj.copy()

    proj_up[i] += bp
    proj_down[i] -= bp

    npv_up = calculate_npv(proj_up, disc)
    npv_down = calculate_npv(proj_down, disc)

    dv01 = (npv_down - npv_up) / 2

    projection_pillar_dv01.append(dv01)

    # Discount curve pillar bump
    disc_up = disc.copy()
    disc_down = disc.copy()

    disc_up[i] += bp
    disc_down[i] -= bp

    npv_up = calculate_npv(proj, disc_up)
    npv_down = calculate_npv(proj, disc_down)

    dv01 = (npv_down - npv_up) / 2

    discount_pillar_dv01.append(dv01)


print("\nPillar DV01 Results")

print(f"{'Pillar':<10} {'Projection':>15} {'Discount':>15}")

for i, name in enumerate(pillar_names):

    print(
        f"{name:<10} "
        f"{projection_pillar_dv01[i]:>15,.2f} "
        f"{discount_pillar_dv01[i]:>15,.2f}"
    )


print("\nDV01 Validation")

print("Projection:")
print("Parallel:", proj_dv01)
print("Sum of pillars:", sum(projection_pillar_dv01))

print("\nDiscount:")
print("Parallel:", disc_dv01)
print("Sum of pillars:", sum(discount_pillar_dv01))
print("\n")

#GENERATE SCEDULE
cashflow_table = pd.DataFrame(schedule)

print(cashflow_table.to_string(
    index=False,
    formatters={
        "Forward Rate": "{:.4%}".format,
        "Coupon CF": "{:,.2f}".format,
        "Principal": "{:,.2f}".format,
        "Discount Factor": "{:.8f}".format,
        "PV": "{:,.2f}".format
    }
))

cashflow_table.to_csv(
    "bond_cashflow_schedule.csv",
    index=False
)