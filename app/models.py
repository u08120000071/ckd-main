from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(UserMixin, db.Model):
    """Application user (doctor / admin)."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patients = db.relationship('Patient', backref='creator', lazy='dynamic')
    diagnoses = db.relationship('Diagnosis', backref='doctor', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Patient(db.Model):
    """Patient record."""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # Male / Female
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    diagnoses = db.relationship('Diagnosis', backref='patient', lazy='dynamic',
                                order_by='Diagnosis.created_at.desc()')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Patient {self.full_name}>'


class Diagnosis(db.Model):
    """CKD diagnosis record."""
    __tablename__ = 'diagnoses'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)

    # Input parameters
    serum_creatinine = db.Column(db.Float, nullable=False)   # mg/dL
    urine_acr = db.Column(db.Float, nullable=False)          # mg/g
    patient_age = db.Column(db.Integer, nullable=False)
    patient_gender = db.Column(db.String(10), nullable=False)

    # Flowchart clinical parameters
    blood_pressure = db.Column(db.Integer, nullable=True)     # mmHg
    specific_gravity = db.Column(db.Float, nullable=True)     # nominal (e.g. 1.005–1.025)
    albumin = db.Column(db.Integer, nullable=True)            # nominal (0–5)
    sugar_level = db.Column(db.Integer, nullable=True)        # nominal (0–5)
    red_blood_cells = db.Column(db.String(20), nullable=True) # normal / abnormal
    blood_urea = db.Column(db.Float, nullable=True)           # mg/dL
    sodium = db.Column(db.Float, nullable=True)               # mEq/L
    potassium = db.Column(db.Float, nullable=True)            # mEq/L
    hemoglobin = db.Column(db.Float, nullable=True)           # g/dL
    white_blood_cell_count = db.Column(db.Integer, nullable=True) # cells/mcL
    diabetes_mellitus = db.Column(db.String(10), nullable=True) # yes / no
    hypertension = db.Column(db.String(10), nullable=True)      # yes / no

    # Computed results
    egfr = db.Column(db.Float, nullable=False)               # mL/min/1.73 m²
    gfr_stage = db.Column(db.String(10), nullable=False)     # G1–G5
    albuminuria_stage = db.Column(db.String(10), nullable=False)  # A1–A3
    risk_level = db.Column(db.String(20), nullable=False)    # Low / Moderate / High / Very High
    recommendation = db.Column(db.Text, nullable=False)

    # ML & LLM Integration Results
    ml_prediction = db.Column(db.String(20), nullable=True)   # CKD Detected / No CKD Detected
    ml_confidence = db.Column(db.Float, nullable=True)        # 0.0 - 1.0
    gemini_report = db.Column(db.JSON, nullable=True)         # JSON format

    diagnosed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Diagnosis #{self.id} — {self.gfr_stage}/{self.albuminuria_stage}>'
