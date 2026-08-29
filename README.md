# Chronic Kidney Disease (CKD) Early Detection & Clinical Support System

Welcome! This application is designed to help healthcare professionals and researchers detect early signs of **Chronic Kidney Disease (CKD)**. It combines a machine learning classification model with AI-driven clinical insights from Google Gemini to give doctors clear, actionable patient risk assessments.

---

## 🌟 What This System Does

- **Predicts CKD Risk**: Uses a trained Decision Tree model to analyze 14 key health indicators (such as blood pressure, hemoglobin, blood urea, and serum creatinine) and predict risk.
- **AI-Powered Clinical Insights**: Integrates with Google Gemini to generate readable diagnostic summaries, key observations, and recommended follow-ups for doctors.
- **Patient Record Management**: Lets clinicians save patient profiles, track historical lab results, and review past assessments over time.
- **Instant Medical Reports**: Generates polished patient reports ready for download in PDF or DOCX format.
- **Simple Admin Setup**: Ships with pre-configured authentication and automatically sets up an initial administrator profile so you can get started right away.
- **Easy Model Retraining**: Includes a standalone script so you can easily retrain the machine learning model whenever you update your dataset.

---

## 🛠️ Built With

- **Backend**: Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Database**: SQLite (default for quick local testing) or PostgreSQL for production
- **Machine Learning**: `scikit-learn`, `pandas`, `numpy`, `joblib`
- **AI Integration**: Google Gemini API
- **Document Generation**: `WeasyPrint`, `ReportLab`, `python-docx`
- **Frontend**: HTML5, CSS3, Jinja2 Templates

---

## 📁 Project Structure

Here is a quick overview of how the project is organized:

```text
ckd-main/
├── app/                      # Main Flask application directory
│   ├── routes/               # Page controllers (auth, dashboard, main navigation)
│   ├── static/               # CSS styles, JS scripts, and saved ML models
│   ├── templates/            # HTML views rendered with Jinja2
│   ├── utils/                # Helper modules & background utilities
│   ├── diagnosis.py          # Core clinical diagnostic calculations
│   ├── forms.py              # User input forms & validation rules
│   ├── gemini_service.py     # Gemini AI prompt engine & API client
│   ├── ml_model.py           # Model loader & risk scoring engine
│   └── models.py             # Database schemas (User, Patient, Diagnosis)
├── data/
│   └── kidney_disease_train.csv # Clinical training dataset
├── config.py                 # App configuration settings
├── run.py                    # Server startup script
├── train_model.py            # Model training & serialization script
├── ckd_db_dump.sql           # Initial database schema dump
├── requirements.txt          # Required Python packages
└── README.md                 # Project README
```

---

## 🚀 Quickstart Guide

Follow these steps to set up and run the application locally on your machine.

### 1. Prerequisites
Make sure you have **Python 3.9+** and `pip` installed.

### 2. Set Up a Virtual Environment

```bash
# Clone or open the project folder
cd ckd-main

# Create a virtual environment
python -m venv venv

# Activate it:
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root folder of the project with your local configurations:

```env
FLASK_ENV=development
SECRET_KEY=change-this-to-a-secret-key
DATABASE_URL=sqlite:///ckd.db
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🤖 Retraining the ML Model

The prediction model evaluates 14 clinical features:
`age`, `bp` (blood pressure), `sg` (specific gravity), `al` (albumin), `su` (sugar), `bu` (blood urea), `sc` (serum creatinine), `sod` (sodium), `pot` (potassium), `hemo` (hemoglobin), `wc` (white blood cell count), `rbc` (red blood cells), `htn` (hypertension), and `dm` (diabetes mellitus).

If you want to update the training dataset or tweak the model, run:

```bash
python train_model.py
```

This cleans the data, trains a Decision Tree classifier, and saves the updated model file to `app/static/model/decision_tree.joblib`.

---

## 🏃 Running the Server

Start the local development server by running:

```bash
python run.py
```

Open your browser and navigate to **`http://localhost:5000`**.

### Initial Login Credentials
When the app launches for the first time, it automatically creates a default admin account so you can log in immediately:
- **Username**: `admin`
- **Password**: `admin123`

> 💡 **Tip:** Be sure to change the admin password or create your own user accounts once you're logged in!

---

## 📖 Deep Dive & Documentation

If you'd like to explore the research methodology or technical details further, check out these guides:
- 📄 [Academic Report (Chapters 3 & 4)](Academic_Report_Ch3_Ch4.md) – In-depth background on methodology, model evaluation, and system design.
- 📄 [System Libraries & Functions Reference](System_Libraries_Functions_Doc.md) – Complete breakdown of the internal helper functions and software dependencies.

---

## 📄 License & Usage Note

This project is created for educational, research, and clinical decision support purposes. Feel free to adapt and build upon it!
