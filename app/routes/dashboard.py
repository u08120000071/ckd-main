import os
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, redirect, url_for, flash, send_file, request
from flask_login import login_required, current_user

from app import db
from app.models import Patient, Diagnosis
from app.forms import PatientForm, DiagnosisForm
from app.diagnosis import run_diagnosis, calibrate_prediction
from app.ml_model import predict_ckd
from app.gemini_service import generate_gemini_report
from app.utils.pdf_generator import generate_diagnosis_pdf

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with action cards."""
    total_patients = Patient.query.count()
    total_diagnoses = Diagnosis.query.count()
    recent_diagnoses = (
        Diagnosis.query
        .order_by(Diagnosis.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        'dashboard/index.html',
        total_patients=total_patients,
        total_diagnoses=total_diagnoses,
        recent_diagnoses=recent_diagnoses,
    )


# ------------------------------------------------------------------
# Patient Management
# ------------------------------------------------------------------

@dashboard_bp.route('/patients')
@login_required
def patient_list():
    """View all patient records."""
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('patients/list.html', patients=patients)


@dashboard_bp.route('/patients/register', methods=['GET', 'POST'])
@login_required
def patient_register():
    """Register a new patient."""
    form = PatientForm()

    if form.validate_on_submit():
        import secrets
        # Split full name into first and last
        names = form.full_name.data.strip().split(maxsplit=1)
        first_name = names[0] if names else "Unknown"
        last_name = names[1] if len(names) > 1 else ""

        # Auto-generate patient ID if not provided
        patient_id = form.patient_id.data.strip() if form.patient_id.data else f"PT-{secrets.token_hex(2).upper()}"

        # Ensure patient_id is unique
        while Patient.query.filter_by(patient_id=patient_id).first() is not None:
            patient_id = f"PT-{secrets.token_hex(2).upper()}"

        patient = Patient(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            age=form.age.data,
            gender=form.gender.data,
            phone=form.contact_info.data,
            created_by=current_user.id,
        )
        db.session.add(patient)
        db.session.commit()
        flash(f'Patient {patient.full_name} registered successfully with ID {patient.patient_id}.', 'success')
        return redirect(url_for('dashboard.patient_detail', patient_id=patient.id))

    return render_template('patients/register.html', form=form)


@dashboard_bp.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    """View a single patient and their diagnosis history."""
    patient = Patient.query.get_or_404(patient_id)
    diagnoses = patient.diagnoses.all()
    return render_template('patients/detail.html', patient=patient, diagnoses=diagnoses)


@dashboard_bp.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def patient_edit(patient_id):
    """Edit an existing patient's details."""
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)

    # Pre-fill the composite full_name field on GET
    if request.method == 'GET':
        form.full_name.data = patient.full_name
        form.patient_id.data = patient.patient_id
        form.contact_info.data = patient.phone

    if form.validate_on_submit():
        names = form.full_name.data.strip().split(maxsplit=1)
        patient.first_name = names[0] if names else "Unknown"
        patient.last_name = names[1] if len(names) > 1 else ""
        patient.age = form.age.data
        patient.gender = form.gender.data
        patient.phone = form.contact_info.data

        # Update patient_id only if changed and not empty
        new_pid = form.patient_id.data.strip() if form.patient_id.data else patient.patient_id
        if new_pid != patient.patient_id:
            existing = Patient.query.filter_by(patient_id=new_pid).first()
            if existing and existing.id != patient.id:
                flash('That Patient ID is already in use.', 'danger')
                return render_template('patients/edit.html', form=form, patient=patient)
            patient.patient_id = new_pid

        db.session.commit()
        flash(f'Patient {patient.full_name} updated successfully.', 'success')
        return redirect(url_for('dashboard.patient_detail', patient_id=patient.id))

    return render_template('patients/edit.html', form=form, patient=patient)


# ------------------------------------------------------------------
# Diagnosis
# ------------------------------------------------------------------

@dashboard_bp.route('/diagnosis/new/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def diagnosis_new(patient_id):
    """Generate a new CKD diagnosis for a patient."""
    patient = Patient.query.get_or_404(patient_id)
    form = DiagnosisForm()

    if form.validate_on_submit():
        # Get helper values
        def get_optional_select(field, type_fn=str):
            return type_fn(field.data) if (field.data and field.data != '') else None

        albumin_val = get_optional_select(form.albumin, int)

        results = run_diagnosis(
            serum_creatinine=form.serum_creatinine.data,
            age=patient.age,
            gender=patient.gender,
            urine_acr=form.urine_acr.data,
            albumin=albumin_val,
            hypertension=get_optional_select(form.hypertension),
            diabetes_mellitus=get_optional_select(form.diabetes_mellitus),
            blood_pressure=form.blood_pressure.data,
        )

        # Prepare inputs for ML and LLM models
        ml_input_data = {
            'age': patient.age,
            'gender': patient.gender,
            'blood_pressure': form.blood_pressure.data,
            'specific_gravity': get_optional_select(form.specific_gravity, float),
            'albumin': albumin_val,
            'sugar_level': get_optional_select(form.sugar_level, int),
            'red_blood_cells': get_optional_select(form.red_blood_cells),
            'blood_urea': form.blood_urea.data,
            'serum_creatinine': form.serum_creatinine.data,
            'sodium': form.sodium.data,
            'potassium': form.potassium.data,
            'hemoglobin': form.hemoglobin.data,
            'white_blood_cell_count': form.white_blood_cell_count.data,
            'hypertension': get_optional_select(form.hypertension),
            'diabetes_mellitus': get_optional_select(form.diabetes_mellitus),
            'urine_acr': form.urine_acr.data if form.urine_acr.data is not None else results['urine_acr_estimated']
        }

        # Run real-time machine learning prediction & Gemini analysis
        ml_pred, ml_conf = predict_ckd(ml_input_data)

        # Clinical calibration: reconcile ML with KDIGO staging
        ml_pred, ml_conf = calibrate_prediction(
            ml_pred, ml_conf,
            risk_level=results['risk_level'],
            gfr_stage=results['gfr_stage'],
            albuminuria_stage=results['albuminuria_stage'],
        )

        gemini_rep = generate_gemini_report(ml_input_data, ml_pred, ml_conf)

        diagnosis = Diagnosis(
            patient_id=patient.id,
            serum_creatinine=form.serum_creatinine.data,
            urine_acr=ml_input_data['urine_acr'],
            patient_age=patient.age,
            patient_gender=patient.gender,

            # Additional clinical parameters
            blood_pressure=form.blood_pressure.data,
            specific_gravity=ml_input_data['specific_gravity'],
            albumin=albumin_val,
            sugar_level=ml_input_data['sugar_level'],
            red_blood_cells=ml_input_data['red_blood_cells'],
            blood_urea=form.blood_urea.data,
            sodium=form.sodium.data,
            potassium=form.potassium.data,
            hemoglobin=form.hemoglobin.data,
            white_blood_cell_count=form.white_blood_cell_count.data,
            diabetes_mellitus=ml_input_data['diabetes_mellitus'],
            hypertension=ml_input_data['hypertension'],

            egfr=results['egfr'],
            gfr_stage=results['gfr_stage'],
            albuminuria_stage=results['albuminuria_stage'],
            risk_level=results['risk_level'],
            recommendation=results['recommendation'],
            
            # ML & LLM Integration Results
            ml_prediction=ml_pred,
            ml_confidence=ml_conf,
            gemini_report=gemini_rep,

            diagnosed_by=current_user.id,
        )
        db.session.add(diagnosis)
        db.session.commit()
        flash('Diagnosis generated successfully.', 'success')
        return redirect(url_for('dashboard.diagnosis_result', diagnosis_id=diagnosis.id))

    return render_template('diagnosis/form.html', patient=patient, form=form)


@dashboard_bp.route('/diagnosis/<int:diagnosis_id>')
@login_required
def diagnosis_result(diagnosis_id):
    """View a diagnosis result."""
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    return render_template('diagnosis/result.html', diagnosis=diagnosis)


@dashboard_bp.route('/diagnosis/<int:diagnosis_id>/pdf')
@login_required
def diagnosis_pdf(diagnosis_id):
    """Generate and return a professional PDF medical report."""
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    patient = diagnosis.patient
    physician_name = current_user.full_name or current_user.username
    
    pdf_buffer = generate_diagnosis_pdf(diagnosis, patient, physician_name)
    
    clean_name = patient.full_name.replace(" ", "_").replace("/", "-")
    filename = f"CKD_Report_{clean_name}_{patient.patient_id}.pdf"
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


@dashboard_bp.route('/diagnosis/<int:diagnosis_id>/edit', methods=['GET', 'POST'])
@login_required
def diagnosis_edit(diagnosis_id):
    """Edit an existing diagnosis — re-runs the clinical pipeline."""
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    patient = diagnosis.patient
    form = DiagnosisForm(obj=diagnosis)

    # Pre-fill select fields on GET (they store raw values, not choice keys)
    if request.method == 'GET':
        form.serum_creatinine.data = diagnosis.serum_creatinine
        form.urine_acr.data = diagnosis.urine_acr
        form.blood_pressure.data = diagnosis.blood_pressure
        form.blood_urea.data = diagnosis.blood_urea
        form.sodium.data = diagnosis.sodium
        form.potassium.data = diagnosis.potassium
        form.hemoglobin.data = diagnosis.hemoglobin
        form.white_blood_cell_count.data = diagnosis.white_blood_cell_count
        # Select fields need string values
        form.specific_gravity.data = str(diagnosis.specific_gravity) if diagnosis.specific_gravity is not None else ''
        form.albumin.data = str(diagnosis.albumin) if diagnosis.albumin is not None else ''
        form.sugar_level.data = str(diagnosis.sugar_level) if diagnosis.sugar_level is not None else ''
        form.red_blood_cells.data = diagnosis.red_blood_cells or ''
        form.hypertension.data = diagnosis.hypertension or ''
        form.diabetes_mellitus.data = diagnosis.diabetes_mellitus or ''

    if form.validate_on_submit():
        def get_optional_select(field, type_fn=str):
            return type_fn(field.data) if (field.data and field.data != '') else None

        albumin_val = get_optional_select(form.albumin, int)

        results = run_diagnosis(
            serum_creatinine=form.serum_creatinine.data,
            age=patient.age,
            gender=patient.gender,
            urine_acr=form.urine_acr.data,
            albumin=albumin_val,
            hypertension=get_optional_select(form.hypertension),
            diabetes_mellitus=get_optional_select(form.diabetes_mellitus),
            blood_pressure=form.blood_pressure.data,
        )

        ml_input_data = {
            'age': patient.age,
            'gender': patient.gender,
            'blood_pressure': form.blood_pressure.data,
            'specific_gravity': get_optional_select(form.specific_gravity, float),
            'albumin': albumin_val,
            'sugar_level': get_optional_select(form.sugar_level, int),
            'red_blood_cells': get_optional_select(form.red_blood_cells),
            'blood_urea': form.blood_urea.data,
            'serum_creatinine': form.serum_creatinine.data,
            'sodium': form.sodium.data,
            'potassium': form.potassium.data,
            'hemoglobin': form.hemoglobin.data,
            'white_blood_cell_count': form.white_blood_cell_count.data,
            'hypertension': get_optional_select(form.hypertension),
            'diabetes_mellitus': get_optional_select(form.diabetes_mellitus),
            'urine_acr': form.urine_acr.data if form.urine_acr.data is not None else results['urine_acr_estimated']
        }

        ml_pred, ml_conf = predict_ckd(ml_input_data)

        # Clinical calibration: reconcile ML with KDIGO staging
        ml_pred, ml_conf = calibrate_prediction(
            ml_pred, ml_conf,
            risk_level=results['risk_level'],
            gfr_stage=results['gfr_stage'],
            albuminuria_stage=results['albuminuria_stage'],
        )

        gemini_rep = generate_gemini_report(ml_input_data, ml_pred, ml_conf)

        # Update existing diagnosis record
        diagnosis.serum_creatinine = form.serum_creatinine.data
        diagnosis.urine_acr = ml_input_data['urine_acr']
        diagnosis.patient_age = patient.age
        diagnosis.patient_gender = patient.gender
        diagnosis.blood_pressure = form.blood_pressure.data
        diagnosis.specific_gravity = ml_input_data['specific_gravity']
        diagnosis.albumin = albumin_val
        diagnosis.sugar_level = ml_input_data['sugar_level']
        diagnosis.red_blood_cells = ml_input_data['red_blood_cells']
        diagnosis.blood_urea = form.blood_urea.data
        diagnosis.sodium = form.sodium.data
        diagnosis.potassium = form.potassium.data
        diagnosis.hemoglobin = form.hemoglobin.data
        diagnosis.white_blood_cell_count = form.white_blood_cell_count.data
        diagnosis.diabetes_mellitus = ml_input_data['diabetes_mellitus']
        diagnosis.hypertension = ml_input_data['hypertension']
        diagnosis.egfr = results['egfr']
        diagnosis.gfr_stage = results['gfr_stage']
        diagnosis.albuminuria_stage = results['albuminuria_stage']
        diagnosis.risk_level = results['risk_level']
        diagnosis.recommendation = results['recommendation']
        diagnosis.ml_prediction = ml_pred
        diagnosis.ml_confidence = ml_conf
        diagnosis.gemini_report = gemini_rep

        db.session.commit()
        flash('Diagnosis updated and re-evaluated successfully.', 'success')
        return redirect(url_for('dashboard.diagnosis_result', diagnosis_id=diagnosis.id))

    return render_template('diagnosis/edit.html', patient=patient, form=form, diagnosis=diagnosis)


@dashboard_bp.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
def patient_delete(patient_id):
    """Delete a patient and all associated diagnosis records."""
    patient = Patient.query.get_or_404(patient_id)
    name = patient.full_name
    
    # Delete associated diagnoses first to respect foreign keys
    for diagnosis in patient.diagnoses.all():
        db.session.delete(diagnosis)
        
    db.session.delete(patient)
    db.session.commit()
    
    flash(f'Patient {name} and all their diagnostic history deleted successfully.', 'danger')
    return redirect(url_for('dashboard.patient_list'))


@dashboard_bp.route('/diagnosis/<int:diagnosis_id>/delete', methods=['POST'])
@login_required
def diagnosis_delete(diagnosis_id):
    """Delete an individual diagnosis record."""
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    patient_id = diagnosis.patient_id
    
    db.session.delete(diagnosis)
    db.session.commit()
    
    flash('Diagnosis record deleted successfully.', 'danger')
    return redirect(url_for('dashboard.patient_detail', patient_id=patient_id))


# ------------------------------------------------------------------
# Training Dataset Viewer
# ------------------------------------------------------------------

@dashboard_bp.route('/training-dataset')
@login_required
def training_dataset():
    """Display the training dataset in a styled, paginated table."""
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    csv_path = os.path.join(basedir, 'data', 'kidney_disease_train.csv')

    page = request.args.get('page', 1, type=int)
    per_page = 25
    search = request.args.get('search', '', type=str).strip().lower()

    df = pd.read_csv(csv_path)
    total_rows_original = len(df)

    # Apply search filter across all columns
    if search:
        mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(search).any(), axis=1)
        df = df[mask]

    total_rows = len(df)
    total_pages = max(1, (total_rows + per_page - 1) // per_page)
    page = min(page, total_pages)

    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end]

    columns = list(page_df.columns)
    rows = page_df.values.tolist()

    return render_template(
        'dashboard/training_dataset.html',
        columns=columns,
        rows=rows,
        page=page,
        total_pages=total_pages,
        total_rows=total_rows,
        total_rows_original=total_rows_original,
        per_page=per_page,
        search=search,
    )


# ------------------------------------------------------------------
# Model Performance & Evaluation Dashboard
# ------------------------------------------------------------------

@dashboard_bp.route('/model-performance')
@login_required
def model_performance():
    """Evaluate model on the test set and display statistics/performance metrics."""
    from app.ml_model import get_model
    
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    test_csv_path = os.path.join(basedir, 'data', 'kidney_disease_test.csv')
    
    # Load model payload
    payload = get_model()
    model = payload['model']
    imputation_values = payload['imputation_values']
    category_mapping = payload['category_mapping']
    encoded_features = payload['encoded_features']
    
    # Load test set
    df_test = pd.read_csv(test_csv_path)
    
    # Preprocess test set using identical logic
    df_test['classification'] = df_test['classification'].astype(str).str.strip().str.lower()
    df_test['classification'] = df_test['classification'].replace({'ckd\t': 'ckd', 'notckd': 'notckd'})
    df_test = df_test[df_test['classification'].isin(['ckd', 'notckd'])].copy()
    
    df_test['target'] = df_test['classification'].map({'ckd': 1, 'notckd': 0})
    
    # Clean numeric columns (convert to numeric, fillna using imputation_values)
    numeric_features = ['age', 'bp', 'sg', 'al', 'su', 'bu', 'sc', 'sod', 'pot', 'hemo', 'wc']
    for col in numeric_features:
        df_test[col] = pd.to_numeric(df_test[col], errors='coerce')
        df_test[col] = df_test[col].fillna(imputation_values[col])
        
    # Clean categorical columns
    def clean_categorical_local(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip().lower()
        if 'yes' in val_str:
            return 'yes'
        if 'no' in val_str:
            return 'no'
        if 'normal' in val_str:
            return 'normal'
        if 'abnormal' in val_str:
            return 'abnormal'
        return val_str

    categorical_features = ['rbc', 'htn', 'dm']
    for col in categorical_features:
        df_test[col] = df_test[col].apply(clean_categorical_local)
        df_test[col] = df_test[col].fillna(imputation_values[col])
        
    # Map categoricals to numeric indicators
    df_test['rbc_encoded'] = df_test['rbc'].map(category_mapping['rbc']).fillna(0)
    df_test['htn_encoded'] = df_test['htn'].map(category_mapping['htn']).fillna(0)
    df_test['dm_encoded'] = df_test['dm'].map(category_mapping['dm']).fillna(0)
    
    # Select features
    X_test = df_test[encoded_features]
    y_true = df_test['target'].values
    
    # Run prediction
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] # probability of CKD
    
    # Compute metrics
    total = len(y_true)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    # Build list of detailed test cases for evaluation display
    detailed_cases = []
    for i in range(len(df_test)):
        row = df_test.iloc[i]
        pred_label = "CKD" if y_pred[i] == 1 else "Healthy"
        true_label = "CKD" if y_true[i] == 1 else "Healthy"
        correct = (pred_label == true_label)
        prob = y_prob[i]
        confidence_val = prob if y_pred[i] == 1 else (1 - prob)
        
        detailed_cases.append({
            'num': i + 1,
            'age': int(row['age']) if not pd.isna(row['age']) else '—',
            'hemo': f"{row['hemo']:.1f}" if not pd.isna(row['hemo']) else '—',
            'sg': f"{row['sg']:.3f}" if not pd.isna(row['sg']) else '—',
            'al': int(row['al']) if not pd.isna(row['al']) else '—',
            'sc': f"{row['sc']:.1f}" if not pd.isna(row['sc']) else '—',
            'htn': str(row['htn']).upper(),
            'dm': str(row['dm']).upper(),
            'true_label': true_label,
            'pred_label': pred_label,
            'confidence': f"{confidence_val * 100:.1f}%",
            'correct': correct
        })
        
    # Feature importances
    feature_importances = []
    for name, imp in zip(encoded_features, model.feature_importances_):
        clean_name = name.replace('_encoded', '').upper()
        feature_importances.append({
            'name': clean_name,
            'importance': float(imp)
        })
    feature_importances = sorted(feature_importances, key=lambda x: x['importance'], reverse=True)
    
    return render_template(
        'dashboard/model_performance.html',
        total=total,
        tp=tp,
        tn=tn,
        fp=fp,
        fn=fn,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        specificity=specificity,
        detailed_cases=detailed_cases,
        feature_importances=feature_importances
    )

