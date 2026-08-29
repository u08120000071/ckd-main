from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, IntegerField, SelectField,
    FloatField, SubmitField
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    """User login form."""
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={'placeholder': 'Enter username', 'autocomplete': 'username'}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=4, max=128)],
        render_kw={'placeholder': 'Enter password', 'autocomplete': 'current-password'}
    )
    submit = SubmitField('Sign In')


class PatientForm(FlaskForm):
    """New patient registration form."""
    full_name = StringField(
        'Full Name',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'placeholder': 'First and Last name'}
    )
    patient_id = StringField(
        'Patient ID (optional)',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'e.g. PT-1234 (auto-generated if blank)'}
    )
    age = IntegerField(
        'Age',
        validators=[DataRequired(), NumberRange(min=1, max=150)],
        render_kw={'placeholder': 'Age in years'}
    )
    gender = SelectField(
        'Gender',
        choices=[('', 'Select gender'), ('Male', 'Male'), ('Female', 'Female')],
        validators=[DataRequired()]
    )
    contact_info = StringField(
        'Contact Information / Phone (optional)',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'Phone or contact info'}
    )
    submit = SubmitField('Register Patient')


class DiagnosisForm(FlaskForm):
    """CKD diagnosis input form."""
    # Primary clinical metrics
    serum_creatinine = FloatField(
        'Serum Creatinine (mg/dL)',
        validators=[DataRequired(), NumberRange(min=0.1, max=30.0)],
        render_kw={'placeholder': 'e.g. 1.2', 'step': '0.01'}
    )
    urine_acr = FloatField(
        'Urine ACR (mg/g) (optional)',
        validators=[Optional(), NumberRange(min=0.0, max=10000.0)],
        render_kw={'placeholder': 'e.g. 45 (calculated from Albumin if blank)', 'step': '0.1'}
    )

    # Vitals & Risk Factors
    blood_pressure = IntegerField(
        'Blood Pressure (mmHg)',
        validators=[Optional(), NumberRange(min=30, max=250)],
        render_kw={'placeholder': 'e.g. 80'}
    )
    hypertension = SelectField(
        'Hypertension',
        choices=[('', 'Select Hypertension'), ('yes', 'Yes'), ('no', 'No')],
        validators=[Optional()]
    )
    diabetes_mellitus = SelectField(
        'Diabetes Mellitus',
        choices=[('', 'Select Diabetes'), ('yes', 'Yes'), ('no', 'No')],
        validators=[Optional()]
    )

    # Urine Parameters
    specific_gravity = SelectField(
        'Specific Gravity',
        choices=[('', 'Select Specific Gravity'), ('1.005', '1.005'), ('1.010', '1.010'), ('1.015', '1.015'), ('1.020', '1.020'), ('1.025', '1.025')],
        validators=[Optional()]
    )
    albumin = SelectField(
        'Albumin (Dipstick Level)',
        choices=[('', 'Select Albumin Level'), ('0', '0 (Negative)'), ('1', '1 (1+)'), ('2', '2 (2+)'), ('3', '3 (3+)'), ('4', '4 (4+)'), ('5', '5 (5+)')],
        validators=[Optional()]
    )
    sugar_level = SelectField(
        'Sugar Level',
        choices=[('', 'Select Sugar Level'), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
        validators=[Optional()]
    )
    red_blood_cells = SelectField(
        'Red Blood Cells',
        choices=[('', 'Select RBC Status'), ('normal', 'Normal'), ('abnormal', 'Abnormal')],
        validators=[Optional()]
    )

    # Blood Chemistry
    blood_urea = FloatField(
        'Blood Urea (mg/dL)',
        validators=[Optional(), NumberRange(min=1.0, max=400.0)],
        render_kw={'placeholder': 'e.g. 40.0', 'step': '0.1'}
    )
    sodium = FloatField(
        'Sodium (mEq/L)',
        validators=[Optional(), NumberRange(min=50.0, max=200.0)],
        render_kw={'placeholder': 'e.g. 138.0', 'step': '0.1'}
    )
    potassium = FloatField(
        'Potassium (mEq/L)',
        validators=[Optional(), NumberRange(min=1.0, max=15.0)],
        render_kw={'placeholder': 'e.g. 4.2', 'step': '0.1'}
    )
    hemoglobin = FloatField(
        'Hemoglobin (g/dL)',
        validators=[Optional(), NumberRange(min=1.0, max=25.0)],
        render_kw={'placeholder': 'e.g. 14.5', 'step': '0.1'}
    )
    white_blood_cell_count = IntegerField(
        'White Blood Cell Count (cells/mcL)',
        validators=[Optional(), NumberRange(min=100, max=50000)],
        render_kw={'placeholder': 'e.g. 8000'}
    )

    submit = SubmitField('Generate Diagnosis')
