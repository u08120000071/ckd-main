import os
import joblib
import numpy as np

# Cache for the loaded model and metadata
_MODEL_CACHE = None

def get_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        basedir = os.path.abspath(os.path.dirname(__file__))
        model_path = os.path.join(basedir, 'static', 'model', 'decision_tree.joblib')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Trained model not found at {model_path}. Please run train_model.py first.")
        _MODEL_CACHE = joblib.load(model_path)
    return _MODEL_CACHE

def predict_ckd(data: dict) -> tuple[str, float]:
    """
    Predict CKD and return (prediction_label, confidence_score).
    Input data keys should align with the 14 features:
      age, blood_pressure (bp), specific_gravity (sg), albumin (al), sugar_level (su),
      red_blood_cells (rbc), blood_urea (bu), serum_creatinine (sc), sodium (sod),
      potassium (pot), hemoglobin (hemo), white_blood_cell_count (wc),
      hypertension (htn), diabetes_mellitus (dm)
    """
    payload = get_model()
    model = payload['model']
    imputation_values = payload['imputation_values']
    category_mapping = payload['category_mapping']
    encoded_features = payload['encoded_features']

    # Map form keys to model feature keys
    # Form input names / Database columns vs model dataset column names
    key_mapping = {
        'age': 'age',
        'blood_pressure': 'bp',
        'specific_gravity': 'sg',
        'albumin': 'al',
        'sugar_level': 'su',
        'red_blood_cells': 'rbc',
        'blood_urea': 'bu',
        'serum_creatinine': 'sc',
        'sodium': 'sod',
        'potassium': 'pot',
        'hemoglobin': 'hemo',
        'white_blood_cell_count': 'wc',
        'hypertension': 'htn',
        'diabetes_mellitus': 'dm'
    }

    # Clean and impute patient features
    processed_values = {}
    
    # 1. First extract values and handle missing values
    for form_key, model_key in key_mapping.items():
        val = data.get(form_key)
        if val is None or val == '':
            processed_values[model_key] = imputation_values[model_key]
        else:
            processed_values[model_key] = val

    # 2. Encode categorical variables
    # rbc: normal -> 1, abnormal -> 0
    # htn: yes -> 1, no -> 0
    # dm: yes -> 1, no -> 0
    for cat_col in ['rbc', 'htn', 'dm']:
        val_str = str(processed_values[cat_col]).strip().lower()
        # Handle maps
        map_dict = category_mapping[cat_col]
        
        # Simple lookup with fallback to mode's mapped value
        if val_str in map_dict:
            processed_values[f'{cat_col}_encoded'] = map_dict[val_str]
        else:
            # Clean matching fallback
            if 'yes' in val_str:
                processed_values[f'{cat_col}_encoded'] = 1
            elif 'no' in val_str:
                processed_values[f'{cat_col}_encoded'] = 0
            elif 'normal' in val_str:
                processed_values[f'{cat_col}_encoded'] = 1
            elif 'abnormal' in val_str:
                processed_values[f'{cat_col}_encoded'] = 0
            else:
                default_mode = imputation_values[cat_col]
                processed_values[f'{cat_col}_encoded'] = map_dict.get(default_mode, 0)

    # 3. Assemble final features vector matching encoded_features list
    features_vector = []
    for col in encoded_features:
        features_vector.append(float(processed_values[col]))

    # Run inference
    X_input = np.array([features_vector])
    pred = int(model.predict(X_input)[0])
    probs = model.predict_proba(X_input)[0]
    
    confidence = float(probs[pred])
    pred_label = "CKD Detected" if pred == 1 else "No CKD Detected"
    
    return pred_label, confidence
