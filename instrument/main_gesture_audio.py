import cv2
import mediapipe as mp
import joblib
import numpy as np
import os
import pygame 
from collections import deque 
import pandas as pd 
import time  
import math

# --- Setup Paths ---
MODEL_DIR = 'trained_models'
MODEL_FILENAME = 'gesture_classifier.joblib'
LABEL_ENCODER_FILENAME = 'label_encoder.joblib'
AUDIO_DIR = 'audio_files' 

# --- Configuration ---
STRUM_HISTORY_LENGTH = 10   
STRUM_THRESHOLD = 0.12      
STRUM_COOLDOWN = 0.5        
PREDICTION_CONFIDENCE_THRESHOLD = 0.55
PALM_LENGTH_THRESHOLD = 0.1 # Threshold for flattening hand

# --- Load Model ---
try:
    model = joblib.load(os.path.join(MODEL_DIR, MODEL_FILENAME))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, LABEL_ENCODER_FILENAME))
    print("Model and Label Encoder loaded successfully.")
except FileNotFoundError:
    print(f"Error: Model not found. Run 'train_model.py' first.")
    exit()

# --- Setup MediaPipe ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2, 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# --- GESTURE INFO ---
GESTURE_INFO = {
    "a_major": {"file": "a_major.wav", "name": "A Major"},
    "a_minor": {"file": "a_minor.wav", "name": "A Minor"},
    "a_m7":    {"file": "a_m7.wav",    "name": "A m7"},
    "a_maj7":  {"file": "a_maj7.wav",  "name": "A Maj7"},
    "c_major": {"file": "c_major.wav", "name": "C Major"},
    "d_major": {"file": "d_major.wav", "name": "D Major"},
    "d_minor": {"file": "d_minor.wav", "name": "D Minor"},
    "e_major": {"file": "e_major.wav", "name": "E Major"},
    "e_m7":    {"file": "e_m7.wav",    "name": "E m7"},
    "f_major": {"file": "f_major.wav", "name": "F Major (Mini)"},
    "g_major": {"file": "g_major.wav", "name": "G Major"},
}

# --- Audio Setup ---
pygame.mixer.init()
pygame.mixer.set_num_channels(8) 
audio_channel = pygame.mixer.Channel(0) 
loaded_sounds = {}
for k, v in GESTURE_INFO.items():
    if os.path.exists(os.path.join(AUDIO_DIR, v["file"])):
        loaded_sounds[k] = pygame.mixer.Sound(os.path.join(AUDIO_DIR, v["file"]))
    else: loaded_sounds[k] = None

# --- Helper Functions ---
# INDICES TO USE (NO THUMB)
LANDMARK_INDICES_TO_USE = [0] + list(range(5, 21))

# Generate feature names for position (x,y,z)
FEATURE_NAMES = [f'lm_{i}_{coord}' for i in LANDMARK_INDICES_TO_USE for coord in ['x', 'y', 'z']]

# NEW: Add feature names for Fingertip Distances
# 8=IndexTip, 12=MidTip, 16=RingTip, 20=PinkyTip
TIP_IDS = [8, 12, 16, 20]
for i in range(len(TIP_IDS)):
    for j in range(i + 1, len(TIP_IDS)):
        FEATURE_NAMES.append(f'dist_{TIP_IDS[i]}_{TIP_IDS[j]}')

def extract_landmark_features(hand_landmarks):
    features = []
    if hand_landmarks:
        # 1. Standard Position Features (Relative to Wrist)
        base_x = hand_landmarks.landmark[0].x
        base_y = hand_landmarks.landmark[0].y
        base_z = hand_landmarks.landmark[0].z
        for i in LANDMARK_INDICES_TO_USE: 
            lm = hand_landmarks.landmark[i]
            features.extend([lm.x - base_x, lm.y - base_y, lm.z - base_z])
            
        # 2. NEW: Inter-Fingertip Distances
        # This explicitly tells the model "How far is Index from Middle?", etc.
        for i in range(len(TIP_IDS)):
            for j in range(i + 1, len(TIP_IDS)):
                id1 = TIP_IDS[i]
                id2 = TIP_IDS[j]
                
                lm1 = hand_landmarks.landmark[id1]
                lm2 = hand_landmarks.landmark[id2]
                
                # Euclidean distance formula
                dist = math.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2 + (lm1.z - lm2.z)**2)
                features.append(dist)

    return features

def is_back_of_hand(hand_landmarks):
    """Checks orientation (Pinky > Index for Left Hand)."""
    pinky_mcp_x = hand_landmarks.landmark[17].x
    index_mcp_x = hand_landmarks.landmark[5].x
    return pinky_mcp_x > index_mcp_x

def check_palm_length(hand_landmarks):
    """Checks if hand is pointing too much at camera (foreshortened)."""
    wrist = hand_landmarks.landmark[0]
    knuckles = [5, 9, 13, 17]
    avg_distance = 0
    for k in knuckles:
        knuckle = hand_landmarks.landmark[k]
        dist = math.sqrt((knuckle.x - wrist.x)**2 + (knuckle.y - wrist.y)**2)
        avg_distance += dist
    avg_distance /= 4
    return avg_distance > PALM_LENGTH_THRESHOLD

def draw_custom_landmarks(frame, hand_landmarks):
    """Draws hand landmarks with emphasized, colorful fingertips."""
    h, w, _ = frame.shape
    
    # 1. Draw connections and base landmarks (Neutral Gray)
    mp_drawing.draw_landmarks(
        frame, 
        hand_landmarks, 
        mp_hands.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(200, 200, 200), thickness=2, circle_radius=2),
        mp_drawing.DrawingSpec(color=(220, 220, 220), thickness=2, circle_radius=2)
    )
    
    # 2. Draw Emphasized Tips
    tips = {
        8:  (0, 255, 255),   # Index: Yellow
        12: (255, 255, 0),   # Middle: Cyan
        16: (255, 0, 255),   # Ring: Magenta
        20: (0, 0, 255)      # Pinky: Red
    }
    
    for idx, color in tips.items():
        lm = hand_landmarks.landmark[idx]
        cx, cy = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (cx, cy), 12, (255, 255, 255), 2)
        cv2.circle(frame, (cx, cy), 8, color, cv2.FILLED)

def draw_messages(frame, messages, start_y=30, color=(0, 255, 0)):
    for i, msg in enumerate(messages):
        cv2.putText(frame, msg, (10, start_y + i*40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    return frame

# --- Main Loop ---
def run_gesture_audio_program():
    global current_left_gesture
    
    # State Variables
    right_hand_strum_history = deque(maxlen=STRUM_HISTORY_LENGTH) 
    current_left_gesture = "None"
    last_strum_time = 0 
    
    cap = cv2.VideoCapture(4) 
    if not cap.isOpened(): return

    print("INFO: Ready. Press 'q' to quit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        left_hand_features = None
        fingertip_y = None 
        is_strumming = False 
        
        hand_orientation_ok = False
        hand_length_ok = False

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                
                # USE CUSTOM DRAWING
                draw_custom_landmarks(frame, hand_landmarks)
                
                label = handedness.classification[0].label
                
                if label == "Left":
                    hand_orientation_ok = is_back_of_hand(hand_landmarks)
                    hand_length_ok = check_palm_length(hand_landmarks)
                    
                    if hand_orientation_ok and hand_length_ok:
                        left_hand_features = extract_landmark_features(hand_landmarks)
                    else:
                        left_hand_features = None
                        
                elif label == "Right":
                    fingertip_y = hand_landmarks.landmark[8].y 

        # --- PREDICTION ---
        if left_hand_features:
            try:
                features_df = pd.DataFrame([left_hand_features], columns=FEATURE_NAMES)
                probs = model.predict_proba(features_df)[0]
                best_idx = np.argmax(probs)
                if probs[best_idx] > PREDICTION_CONFIDENCE_THRESHOLD:
                    current_left_gesture = label_encoder.classes_[best_idx]
            except Exception:
                current_left_gesture = "Error"
        else:
             pass # Stop updating if hand is bad

        # --- DIRECTIONAL STRUM DETECTION ---
        if fingertip_y is not None:
            right_hand_strum_history.append(fingertip_y)
            if len(right_hand_strum_history) == STRUM_HISTORY_LENGTH:
                displacement = right_hand_strum_history[-1] - right_hand_strum_history[0]
                current_time = time.time()
                if displacement > STRUM_THRESHOLD:
                    if (current_time - last_strum_time) > STRUM_COOLDOWN:
                        is_strumming = True
                        last_strum_time = current_time 
                        right_hand_strum_history.clear() 
        else:
            right_hand_strum_history.clear()

        # --- AUDIO TRIGGER ---
        if is_strumming and current_left_gesture in loaded_sounds and loaded_sounds[current_left_gesture]:
            audio_channel.play(loaded_sounds[current_left_gesture])
            print(f"DOWN STRUM! ({current_left_gesture})")

        # --- DISPLAY STATUS & FEEDBACK ---
        display_name = GESTURE_INFO.get(current_left_gesture, {"name": current_left_gesture})["name"]
        
        # Calculate cooldown visual
        time_since_strum = time.time() - last_strum_time
        on_cooldown = time_since_strum < STRUM_COOLDOWN
        status_text = "COOLDOWN" if on_cooldown else "READY"
        status_color = (0, 0, 255) if on_cooldown else (0, 255, 0)
        
        # Override status for Hand Errors (Highest Priority)
        # Note: We only check these if a Left hand was actually detected. 
        # If no hand is detected, we just show "Ready" or last chord.
        if results.multi_hand_landmarks:
             # Check if we found a left hand but failed checks
             # (Simplified logic: if we have prediction data, hand is good. If not, check why)
             if not left_hand_features and current_left_gesture != "None":
                 if not hand_length_ok:
                     status_text = "BAD ANGLE: FLATTEN HAND"
                     status_color = (0, 0, 255)
                 elif not hand_orientation_ok:
                     status_text = "SHOW BACK OF HAND"
                     status_color = (0, 165, 255)

        frame = draw_messages(frame, [
            f"Chord: {display_name}", 
            f"Strum: {status_text}"
        ], color=status_color)
        
        cv2.imshow('Gesture Control', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    pygame.mixer.quit()

if __name__ == "__main__":
    run_gesture_audio_program()