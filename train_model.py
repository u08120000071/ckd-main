import os
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score
import joblib

def clean_categorical(val):
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

def train():
    basedir = os.path.abspath(os.path.dirname(__file__))
    csv_path = os.path.join(basedir, 'data', 'kidney_disease_train.csv')
    df = pd.read_csv(csv_path)

    # 1. Clean the target 'classification'
    df['classification'] = df['classification'].astype(str).str.strip().str.lower()
    df['classification'] = df['classification'].replace({'ckd\t': 'ckd', 'notckd': 'notckd'})
    # Filter rows where classification is valid
    df = df[df['classification'].isin(['ckd', 'notckd'])]
    df['target'] = df['classification'].map({'ckd': 1, 'notckd': 0})

    # Define the 14 features we collect
    numeric_features = ['age', 'bp', 'sg', 'al', 'su', 'bu', 'sc', 'sod', 'pot', 'hemo', 'wc']
    categorical_features = ['rbc', 'htn', 'dm']
    features = numeric_features + categorical_features

    # Preprocess each feature and record imputation values
    imputation_values = {}
    
    # 2. Clean numeric columns (convert to numeric, coercing errors to NaN)
    for col in numeric_features:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        # Compute median
        median_val = float(df[col].median())
        if pd.isna(median_val):
            median_val = 0.0
        imputation_values[col] = median_val
        df[col] = df[col].fillna(median_val)

    # 3. Clean categorical columns
    for col in categorical_features:
        df[col] = df[col].apply(clean_categorical)
        # Compute mode (most frequent non-NaN value)
        mode_series = df[col].dropna().mode()
        mode_val = str(mode_series[0]) if not mode_series.empty else 'no'
        if col == 'rbc' and mode_series.empty:
            mode_val = 'normal'
        imputation_values[col] = mode_val
        df[col] = df[col].fillna(mode_val)

    # 4. Map categorical features to numeric indicators
    # rbc: normal -> 1, abnormal -> 0
    # htn: yes -> 1, no -> 0
    # dm: yes -> 1, no -> 0
    df['rbc_encoded'] = df['rbc'].map({'normal': 1, 'abnormal': 0})
    df['htn_encoded'] = df['htn'].map({'yes': 1, 'no': 0})
    df['dm_encoded'] = df['dm'].map({'yes': 1, 'no': 0})

    # Build X and y
    encoded_features = []
    for col in features:
        if col == 'rbc':
            encoded_features.append('rbc_encoded')
        elif col == 'htn':
            encoded_features.append('htn_encoded')
        elif col == 'dm':
            encoded_features.append('dm_encoded')
        else:
            encoded_features.append(col)

    X = df[encoded_features]
    y = df['target']

    print("Training features:", features)
    print("Encoded feature names:", encoded_features)
    print("X shape:", X.shape)
    print("y distribution:\n", y.value_counts())

    # 5. Train Decision Tree (no artificial depth limit so all critical splits are captured)
    model = DecisionTreeClassifier(random_state=42, min_samples_leaf=2)
    model.fit(X, y)
    
    train_acc = model.score(X, y)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"Training Accuracy: {train_acc * 100:.2f}%")
    print(f"Cross-Validation Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
    print(f"Tree Depth: {model.get_depth()}, Leaves: {model.get_n_leaves()}")
    print("Feature importances:")
    for name, imp in zip(encoded_features, model.feature_importances_):
        if imp > 0.01:
            print(f"  {name}: {imp:.4f}")

    # 6. Save model and metadata
    model_dir = os.path.join(basedir, 'app', 'static', 'model')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'decision_tree.joblib')

    payload = {
        'model': model,
        'features': features,
        'encoded_features': encoded_features,
        'imputation_values': imputation_values,
        'category_mapping': {
            'rbc': {'normal': 1, 'abnormal': 0},
            'htn': {'yes': 1, 'no': 0},
            'dm': {'yes': 1, 'no': 0}
        }
    }

    joblib.dump(payload, model_path)
    print(f"Model and metadata saved successfully to {model_path}!")

if __name__ == '__main__':
    train()
