import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

# --- Configuration ---
DATA_DIR = 'gesture_data'
MODEL_DIR = 'trained_models'
MODEL_FILENAME = 'gesture_classifier.joblib'
LABEL_ENCODER_FILENAME = 'label_encoder.joblib'

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

def train_gesture_model():
    all_data = []
    
    # Load all CSV files from the data directory
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('_data.csv')]
    if not csv_files:
        print(f"No CSV data files found in '{DATA_DIR}'. Please run create_dataset.py first.")
        return False

    for csv_file in csv_files:
        file_path = os.path.join(DATA_DIR, csv_file)
        # Read CSV. If there are bad lines, we will catch them later.
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
        except pd.errors.EmptyDataError:
            print(f"Skipping empty file: {csv_file}")
            continue

    if not all_data:
        print("No data loaded. Exiting training.")
        return False

    # Concatenate all dataframes
    # This aligns columns. If schemas mismatch, it introduces NaNs.
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Separate Features (X) and Labels (y)
    if 'label' not in combined_df.columns:
        print("Error: 'label' column missing from dataset.")
        return False

    X = combined_df.drop('label', axis=1)
    y = combined_df['label']

    if X.empty or y.empty:
        print("Combined dataset is empty. Cannot train model.")
        return False

    # --- CLEANING STEP: Handle duplicate headers or bad data ---
    print(f"Raw dataset shape: {X.shape}")
    
    # Convert all columns in X to numeric, coercing errors to NaN
    X = X.apply(pd.to_numeric, errors='coerce')
    
    # Check for NaNs (which indicate bad rows or schema mismatches)
    if X.isnull().values.any():
        print("WARNING: Found non-numeric data or missing columns. Cleaning...")
        # Get indices of rows that are NOT null
        valid_indices = ~X.isnull().any(axis=1)
        X = X[valid_indices]
        y = y[valid_indices]
        print(f"Cleaned dataset size: {X.shape}")

    if X.empty:
        print("\nERROR: All data was invalid after cleaning.")
        print("POSSIBLE CAUSE: You likely have old CSV files (without new distance features) mixed with new files.")
        print("SOLUTION: Go to 'gesture_data' folder, DELETE ALL .csv files, and run create_dataset.py again.")
        return False

    # Encode labels to numerical values
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

    print(f"Training data shape: {X_train.shape}, Labels shape: {y_train.shape}")
    print(f"Testing data shape: {X_test.shape}, Labels shape: {y_test.shape}")
    print(f"Unique gestures to train: {le.classes_}")

    # Initialize and train a RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy:.2f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Save the trained model and label encoder
    model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
    label_encoder_path = os.path.join(MODEL_DIR, LABEL_ENCODER_FILENAME)

    joblib.dump(model, model_path)
    joblib.dump(le, label_encoder_path)
    print(f"\nModel saved to {model_path}")
    print(f"Label Encoder saved to {label_encoder_path}")
    return True

if __name__ == "__main__":
    print("Starting gesture model training...")
    if train_gesture_model():
        print("Training complete!")
    else:
        print("Training failed.")