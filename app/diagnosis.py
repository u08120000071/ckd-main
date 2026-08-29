"""
CKD Diagnosis Engine
====================
Calculates eGFR using the CKD-EPI 2021 equation (race-free),
classifies GFR stage (G1–G5) and albuminuria category (A1–A3),
and assesses overall CKD risk per KDIGO heat-map.
"""

import math


# ---------------------------------------------------------------------------
# eGFR Calculation — CKD-EPI 2021 (race-free)
# ---------------------------------------------------------------------------

def calculate_egfr(serum_creatinine: float, age: int, gender: str) -> float:
    """
    Calculate eGFR using the CKD-EPI 2021 creatinine equation.

    Parameters
    ----------
    serum_creatinine : float   — mg/dL
    age              : int     — years
    gender           : str     — "Male" or "Female"

    Returns
    -------
    float — eGFR in mL/min/1.73 m²
    """
    scr = serum_creatinine
    is_female = gender.lower().startswith('f')

    if is_female:
        kappa = 0.7
        alpha = -0.241
        sex_coeff = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_coeff = 1.0

    scr_over_kappa = scr / kappa
    min_val = min(scr_over_kappa, 1.0)
    max_val = max(scr_over_kappa, 1.0)

    egfr = 142 * (min_val ** alpha) * (max_val ** -1.200) * (0.9938 ** age) * sex_coeff

    return round(egfr, 2)


# ---------------------------------------------------------------------------
# GFR Staging (KDIGO)
# ---------------------------------------------------------------------------

GFR_STAGES = [
    ('G1', 90, None, 'Normal or high'),
    ('G2', 60, 89, 'Mildly decreased'),
    ('G3a', 45, 59, 'Mildly to moderately decreased'),
    ('G3b', 30, 44, 'Moderately to severely decreased'),
    ('G4', 15, 29, 'Severely decreased'),
    ('G5', 0, 14, 'Kidney failure'),
]


def classify_gfr_stage(egfr: float) -> tuple[str, str]:
    """Return (stage_code, stage_label) for a given eGFR value."""
    if egfr >= 90:
        return 'G1', 'Normal or high'
    elif egfr >= 60:
        return 'G2', 'Mildly decreased'
    elif egfr >= 45:
        return 'G3a', 'Mildly to moderately decreased'
    elif egfr >= 30:
        return 'G3b', 'Moderately to severely decreased'
    elif egfr >= 15:
        return 'G4', 'Severely decreased'
    else:
        return 'G5', 'Kidney failure'


# ---------------------------------------------------------------------------
# Albuminuria Staging (KDIGO)
# ---------------------------------------------------------------------------

def classify_albuminuria(acr: float) -> tuple[str, str]:
    """Return (category, label) for a given urine ACR (mg/g)."""
    if acr < 30:
        return 'A1', 'Normal to mildly increased'
    elif acr <= 300:
        return 'A2', 'Moderately increased'
    else:
        return 'A3', 'Severely increased'


# ---------------------------------------------------------------------------
# Risk Assessment — KDIGO GFR × Albuminuria Heat-Map
# ---------------------------------------------------------------------------

# Rows = GFR stage, Cols = Albuminuria category
RISK_MATRIX = {
    #              A1            A2            A3
    'G1':  ['Low',        'Moderate',   'High'],
    'G2':  ['Low',        'Moderate',   'High'],
    'G3a': ['Moderate',   'High',       'Very High'],
    'G3b': ['High',       'Very High',  'Very High'],
    'G4':  ['Very High',  'Very High',  'Very High'],
    'G5':  ['Very High',  'Very High',  'Very High'],
}

RECOMMENDATIONS = {
    'Low': (
        'Low risk of CKD progression. Continue routine monitoring with annual '
        'eGFR and urine ACR testing. Maintain healthy lifestyle, control blood '
        'pressure and blood sugar if applicable.'
    ),
    'Moderate': (
        'Moderate risk of CKD progression. Schedule follow-up every 6 months. '
        'Optimise blood pressure control (target < 130/80 mmHg). Consider ACEi/ARB '
        'therapy. Monitor for cardiovascular risk factors.'
    ),
    'High': (
        'High risk of CKD progression. Refer to nephrology if not already under '
        'specialist care. Intensify blood pressure and glycaemic control. Monitor '
        'eGFR and ACR every 3–4 months. Evaluate for complications (anaemia, '
        'bone disease, acidosis).'
    ),
    'Very High': (
        'Very high risk of kidney failure. Urgent nephrology referral required. '
        'Prepare for renal replacement therapy planning (dialysis or transplant) '
        'if eGFR < 20. Aggressively manage complications. Monitor monthly.'
    ),
}


def assess_risk(gfr_stage: str, alb_category: str,
                hypertension: str = None, diabetes_mellitus: str = None,
                blood_pressure: int = None) -> tuple[str, str]:
    """
    Return (risk_level, recommendation) based on the KDIGO heat-map,
    with clinical co-morbidity escalation per guideline best practice.

    Active hypertension, diabetes mellitus, or elevated BP (>=140 mmHg)
    each escalate the baseline KDIGO risk by one tier (capped at Very High).
    """
    col_index = {'A1': 0, 'A2': 1, 'A3': 2}[alb_category]
    risk = RISK_MATRIX[gfr_stage][col_index]

    # Co-morbidity risk escalation
    risk_tiers = ['Low', 'Moderate', 'High', 'Very High']
    tier_index = risk_tiers.index(risk)

    escalation = 0
    if hypertension and hypertension.lower() == 'yes':
        escalation += 1
    if diabetes_mellitus and diabetes_mellitus.lower() == 'yes':
        escalation += 1
    if blood_pressure is not None and blood_pressure >= 140:
        escalation += 1

    # Cap escalation: max one tier bump for co-morbidities combined
    if escalation > 0:
        tier_index = min(tier_index + 1, len(risk_tiers) - 1)

    risk = risk_tiers[tier_index]
    return risk, RECOMMENDATIONS[risk]


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def run_diagnosis(serum_creatinine: float, age: int, gender: str,
                  urine_acr: float = None, albumin: int = None,
                  hypertension: str = None, diabetes_mellitus: str = None,
                  blood_pressure: int = None) -> dict:
    """
    Run a full CKD diagnosis and return all results as a dict.

    Co-morbidities (hypertension, diabetes, elevated BP) are factored
    into the final KDIGO risk assessment as clinical escalation modifiers.
    """
    # Estimate urine ACR from dipstick albumin level if ACR is not provided
    if urine_acr is None:
        if albumin == 0:
            urine_acr = 15.0
        elif albumin == 1:
            urine_acr = 150.0
        elif albumin is not None and albumin >= 2:
            urine_acr = 450.0
        else:
            urine_acr = 15.0

    egfr = calculate_egfr(serum_creatinine, age, gender)
    gfr_stage, gfr_label = classify_gfr_stage(egfr)
    alb_cat, alb_label = classify_albuminuria(urine_acr)
    risk_level, recommendation = assess_risk(
        gfr_stage, alb_cat,
        hypertension=hypertension,
        diabetes_mellitus=diabetes_mellitus,
        blood_pressure=blood_pressure,
    )

    return {
        'egfr': egfr,
        'gfr_stage': gfr_stage,
        'gfr_label': gfr_label,
        'urine_acr_estimated': urine_acr,
        'albuminuria_stage': alb_cat,
        'albuminuria_label': alb_label,
        'risk_level': risk_level,
        'recommendation': recommendation,
    }


# ---------------------------------------------------------------------------
# Clinical Calibration — reconcile ML prediction with KDIGO staging
# ---------------------------------------------------------------------------

def calibrate_prediction(ml_pred: str, ml_conf: float,
                         risk_level: str, gfr_stage: str,
                         albuminuria_stage: str) -> tuple[str, float]:
    """
    Reconcile the ML Decision Tree prediction with the deterministic
    KDIGO clinical staging to eliminate contradictions.

    Clinical rationale:
      - KDIGO staging (eGFR + ACR) is the internationally accepted
        gold-standard diagnostic criterion for CKD.
      - The ML model is a screening aid trained on the UCI dataset; its
        binary classification can disagree with nuanced clinical staging.
      - When KDIGO evidence clearly indicates kidney disease, the ML
        prediction is overridden to maintain clinical integrity.

    Override triggers (any one is sufficient):
      1. KDIGO risk level is Moderate, High, or Very High.
      2. GFR stage is G3a or worse (eGFR < 60).
      3. Albuminuria category is A2 or A3 (ACR >= 30 mg/g).
    """
    # Define clinical thresholds that confirm CKD
    elevated_risk = risk_level in ('Moderate', 'High', 'Very High')
    advanced_gfr = gfr_stage in ('G3a', 'G3b', 'G4', 'G5')
    significant_albuminuria = albuminuria_stage in ('A2', 'A3')

    needs_override = elevated_risk or advanced_gfr or significant_albuminuria

    if needs_override and ml_pred == 'No CKD Detected':
        # Override ML prediction to align with clinical evidence
        ml_pred = 'CKD Detected'

        # Set confidence proportional to the clinical severity
        if gfr_stage in ('G4', 'G5') or risk_level == 'Very High':
            ml_conf = 0.98
        elif gfr_stage in ('G3a', 'G3b') or risk_level == 'High':
            ml_conf = 0.92
        else:  # Moderate risk / A2 albuminuria
            ml_conf = 0.85

    return ml_pred, ml_conf
