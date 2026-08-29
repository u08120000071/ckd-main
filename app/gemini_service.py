import os
import json
import urllib.request
import urllib.error

def generate_local_fallback(data: dict, ml_prediction: str, ml_confidence: float) -> dict:
    """
    Generate premium-grade clinical insights using rules based on patient metrics.
    Ensures app works offline or when API key is missing.
    """
    age = data.get('age', 45)
    gender = data.get('gender', 'Unknown')
    creatinine = data.get('serum_creatinine')
    acr = data.get('urine_acr')
    bp = data.get('blood_pressure')
    htn = data.get('hypertension')
    dm = data.get('diabetes_mellitus')
    hemo = data.get('hemoglobin')
    k = data.get('potassium')
    
    # 1. Insights & Risk Analysis
    insights = []
    analysis = []
    precautions = []
    lifestyle = []
    follow_up = []

    is_ckd = "CKD Detected" in ml_prediction
    conf_pct = int(ml_confidence * 100)

    insights.append(
        f"Based on the Decision Tree model trained on the UCI CKD dataset, the patient is classified as "
        f"'{ml_prediction}' with a confidence of {conf_pct}%. "
    )

    if creatinine:
        if (gender == 'Male' and creatinine > 1.2) or (gender == 'Female' and creatinine > 1.0):
            insights.append(f"Serum Creatinine ({creatinine} mg/dL) is elevated above normal gender thresholds, pointing towards reduced glomerular filtration.")
        else:
            insights.append(f"Serum Creatinine ({creatinine} mg/dL) is within normal baseline range.")

    if is_ckd:
        analysis.append("Risk analysis suggests active kidney damage or impaired filtration function. The presence of risk factors needs urgent monitoring to prevent progressive loss of nephrons.")
    else:
        analysis.append("Risk analysis indicates a low likelihood of active chronic kidney disease; however, pre-existing comorbidities like hypertension or diabetes require continuous vigilance.")

    # 2. Add alerts for specific parameters
    if htn == 'yes' or (bp and bp >= 140):
        insights.append(f"Blood pressure control is compromised (BP: {bp or 'Elevated'} mmHg with history of hypertension).")
        precautions.append("Initiate or adjust ACE inhibitors (ACEIs) or Angiotensin Receptor Blockers (ARBs) as first-line therapy for kidney protection.")
        lifestyle.append("Restrict dietary sodium intake to < 2.0g per day (approx. 5g salt).")
        follow_up.append("Monitor blood pressure twice daily and target a reading below 130/80 mmHg.")
    else:
        lifestyle.append("Maintain low-sodium dietary habits to protect baseline vascular pressure.")

    if dm == 'yes':
        insights.append("Active Diabetes Mellitus increases the risk of diabetic nephropathy via glomerular hyperfiltration.")
        precautions.append("Optimize glycemic controls; consider SGLT2 inhibitors or GLP-1 receptor agonists if indicated.")
        lifestyle.append("Maintain tight blood glucose monitoring; target HbA1c < 7.0%.")
        follow_up.append("Schedule quarterly HbA1c tests and yearly diabetic retinopathy eye exams.")

    if hemo and hemo < 12.0:
        insights.append(f"Hemoglobin is low ({hemo} g/dL), suggesting possible anemia of chronic disease, a common complication of CKD.")
        precautions.append("Perform iron studies (Ferritin, TSAT) to evaluate for anemia etiology.")
        lifestyle.append("Consume iron-rich foods and ensure adequate Vitamin B12 and folate intake.")
        follow_up.append("Repeat complete blood count (CBC) in 4–6 weeks.")

    if k and k > 5.0:
        insights.append(f"Potassium is elevated ({k} mEq/L), indicating hyperkalemia risks due to reduced renal excretion.")
        precautions.append("Avoid potassium-sparing diuretics and evaluate current medications.")
        lifestyle.append("Limit high-potassium foods (avocados, bananas, spinach, potatoes).")
        follow_up.append("Re-evaluate serum electrolytes in 48-72 hours.")

    # Fill defaults to ensure 3 bullets per category
    if len(precautions) < 3:
        precautions.append("Review all prescriptions; avoid nephrotoxic drugs, especially NSAIDs (e.g., ibuprofen, naproxen).")
        precautions.append("Ensure adequate hydration, matching fluid intake with output levels.")
        precautions.append("Consult a nephrologist if GFR drops below 30 mL/min/1.73 m².")
    
    if len(lifestyle) < 3:
        lifestyle.append("Engage in moderate physical activity for 30 minutes, 5 days a week.")
        lifestyle.append("Cease smoking immediately, as nicotine accelerates renal microvascular deterioration.")
        lifestyle.append("Limit high-protein diets; target moderate intake (0.8 g/kg body weight) to reduce glomerular load.")

    if len(follow_up) < 3:
        follow_up.append("Re-check Serum Creatinine and Urine ACR in 3 months to monitor GFR trajectory.")
        follow_up.append("Schedule an ultrasound scan of the kidneys to check for structural changes or scarring.")
        follow_up.append("Maintain an active log of clinical vitals for review at the next outpatient clinic visit.")

    return {
        "medical_insights": " ".join(insights),
        "risk_analysis": " ".join(analysis),
        "suggested_precautions": precautions[:4],
        "lifestyle_recommendations": lifestyle[:4],
        "follow_up_recommendations": follow_up[:4]
    }

def generate_gemini_report(data: dict, ml_prediction: str, ml_confidence: float) -> dict:
    """
    Call Gemini API with structured JSON response config.
    Falls back to generate_local_fallback if key is missing or call fails.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Check config or .env explicitly if needed
        from flask import current_app
        api_key = current_app.config.get("GEMINI_API_KEY")

    if not api_key:
        return generate_local_fallback(data, ml_prediction, ml_confidence)

    # Formulate patient clinical prompt
    prompt = (
        f"You are an expert clinical nephrologist. Analyze the following patient case:\n"
        f"Demographics: Age {data.get('age')}, Gender {data.get('gender')}\n"
        f"Decision Tree Prediction: {ml_prediction} (Confidence: {int(ml_confidence * 100)}%)\n"
        f"Clinical Measurements:\n"
        f"- Serum Creatinine: {data.get('serum_creatinine')} mg/dL\n"
        f"- Urine ACR: {data.get('urine_acr')} mg/g\n"
        f"- Blood Pressure: {data.get('blood_pressure')} mmHg\n"
        f"- Specific Gravity: {data.get('specific_gravity')}\n"
        f"- Albumin (Dipstick): {data.get('albumin')}+\n"
        f"- Sugar Level: {data.get('sugar_level')}\n"
        f"- Red Blood Cells: {data.get('red_blood_cells')}\n"
        f"- Blood Urea: {data.get('blood_urea')} mg/dL\n"
        f"- Sodium: {data.get('sodium')} mEq/L\n"
        f"- Potassium: {data.get('potassium')} mEq/L\n"
        f"- Hemoglobin: {data.get('hemoglobin')} g/dL\n"
        f"- WBC Count: {data.get('white_blood_cell_count')} cells/mcL\n"
        f"- Hypertension: {data.get('hypertension')}\n"
        f"- Diabetes Mellitus: {data.get('diabetes_mellitus')}\n\n"
        f"Provide professional medical insights, risk analysis, suggested precautions, lifestyle recommendations, and follow-up recommendations."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload_data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "medical_insights": {"type": "STRING"},
                    "risk_analysis": {"type": "STRING"},
                    "suggested_precautions": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "lifestyle_recommendations": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "follow_up_recommendations": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": ["medical_insights", "risk_analysis", "suggested_precautions", "lifestyle_recommendations", "follow_up_recommendations"]
            }
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            text_out = res_body['candidates'][0]['content']['parts'][0]['text']
            return json.loads(text_out)
    except Exception as e:
        print(f"Gemini API call failed, falling back to local engine. Error: {e}")
        return generate_local_fallback(data, ml_prediction, ml_confidence)
