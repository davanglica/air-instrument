import cv2
import mediapipe as mp
import joblib
import numpy as np
import os
import pygame # For audio playback
from collections import deque # For tracking hand movement history
import pandas as pd # Import pandas to handle feature names for prediction

# --- Setup Paths ---
MODEL_DIR = 'trained_models'
MODEL_FILENAME = 'gesture_classifier.joblib'
LABEL_ENCODER_FILENAME = 'label_encoder.joblib'
AUDIO_DIR = 'audio_files' # Directory for your audio files

# --- Configuration for Frantic Movement Detection ---
# Number of frames to keep in history for right hand centroid
MOVEMENT_HISTORY_LENGTH = 10
# Threshold for total displacement to be considered "frantic"
# This value will likely need tuning based on your webcam, hand size, and desired sensitivity.
FRANTIC_MOVEMENT_THRESHOLD = 0.05 # Smaller values = more sensitive, larger values = less sensitive
                                 # This is normalized displacement across the frame (0.0 to 1.0)

# --- Load Model and Label Encoder ---
try:
    model = joblib.load(os.path.join(MODEL_DIR, MODEL_FILENAME))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, LABEL_ENCODER_FILENAME))
    print("Model and Label Encoder loaded successfully.")
except FileNotFoundError:
    print(f"Error: Model or Label Encoder not found in '{MODEL_DIR}'.")
    print("Please run 'train_model.py' first.")
    exit()

# --- Setup MediaPipe ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2, # Track both hands
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# --- Audio Setup (using Pygame Mixer) ---
pygame.mixer.init()
pygame.mixer.set_num_channels(8) # Increase channels to handle multiple sounds or quick re-triggers
audio_channel = pygame.mixer.Channel(0) # Use a dedicated channel for our primary audio

# Map gestures to audio files. Ensure these files exist in AUDIO_DIR!
# IMPORTANT: Adjust this dictionary based on your trained gesture names and audio files.
GESTURE_AUDIO_MAP = {
    "boom": "boom.mp3",
    "am7": "am7.mp3"
    # Add more mappings as you train new gestures and create corresponding audio files
}

loaded_sounds = {}
audio_loaded_successfully = False # Flag to track if any audio was loaded
for gesture, filename in GESTURE_AUDIO_MAP.items():
    audio_path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(audio_path):
        try:
            loaded_sounds[gesture] = pygame.mixer.Sound(audio_path)
            print(f"Loaded audio for '{gesture}': {filename}")
            audio_loaded_successfully = True
        except pygame.error as e:
            print(f"Error loading audio '{filename}' for gesture '{gesture}': {e}")
            loaded_sounds[gesture] = None # Mark as failed to load
    else:
        print(f"Warning: Audio file '{filename}' for gesture '{gesture}' not found at {audio_path}.")
        loaded_sounds[gesture] = None

# --- Function to extract hand landmarks (same as in create_dataset.py) ---
def extract_landmark_features(hand_landmarks):
    features = []
    if hand_landmarks:
        base_x = hand_landmarks.landmark[0].x
        base_y = hand_landmarks.landmark[0].y
        base_z = hand_landmarks.landmark[0].z

        for landmark in hand_landmarks.landmark:
            features.extend([landmark.x - base_x, landmark.y - base_y, landmark.z - base_z])
    return features

# --- Function to get hand centroid (normalized coordinates) ---
def get_hand_centroid(hand_landmarks):
    if not hand_landmarks:
        return None
    x_coords = [lm.x for lm in hand_landmarks.landmark]
    y_coords = [lm.y for lm in hand_landmarks.landmark]
    return (np.mean(x_coords), np.mean(y_coords))

# --- Global state variables ---
current_left_gesture = "None"
right_hand_centroid_history = deque(maxlen=MOVEMENT_HISTORY_LENGTH)
audio_is_playing = False
last_played_gesture = None # To prevent re-triggering the same audio repeatedly

# ... (keep all your imports at the top of the file) ...
# ... (keep the existing global variables like MODEL_DIR, mp_hands, GESTURE_AUDIO_MAP, etc.) ...

# --- Generate Feature Names (must match train_model.py) ---
# This is crucial for the model to understand the input
FEATURE_NAMES = [f'lm_{i}_{coord}' for i in range(21) for coord in ['x', 'y', 'z']]

# --- Function to display multiple lines of text on the frame ---
# (Copied from create_dataset.py)
def draw_messages(frame, messages, start_y=30, line_height=40, font_scale=1, color=(0, 255, 0), thickness=2):
    for i, msg in enumerate(messages):
        y_pos = start_y + i * line_height
        cv2.putText(frame, msg, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
    return frame

# --- Main Program Loop ---
def run_gesture_audio_program():
    global current_left_gesture, right_hand_centroid_history, audio_is_playing, last_played_gesture

    cap = cv2.VideoCapture(4) # Using 4 as per your log
    if not cap.isOpened():
        print(f"CRITICAL ERROR: Could not open video stream from camera index 4. Check if it is available and permissions are correct. Exiting.")
        return

    print("INFO: Camera opened successfully. Entering main loop.")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to read frame from camera. Exiting loop.")
                break

            frame = cv2.flip(frame, 1)
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)

            left_hand_features = None
            right_hand_centroid = None
            
            # Reset gesture to "None" if no hands are detected
            current_left_gesture = "None"
            is_frantic = False

            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    # Draw landmarks on the frame
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Check handedness (Left vs Right)
                    hand_label = handedness.classification[0].label

                    if hand_label == "Left":
                        # This is the "chord" hand
                        left_hand_features = extract_landmark_features(hand_landmarks)
                    elif hand_label == "Right":
                        # This is the "strumming" hand
                        right_hand_centroid = get_hand_centroid(hand_landmarks)

            # --- 1. PREDICT GESTURE (LEFT HAND) ---
            if left_hand_features:
                try:
                    # Convert list of features to a pandas DataFrame with correct column names
                    features_df = pd.DataFrame([left_hand_features], columns=FEATURE_NAMES)
                    
                    prediction_idx = model.predict(features_df)[0]
                    current_left_gesture = label_encoder.classes_[prediction_idx]
                except Exception as e:
                    print(f"Error during prediction: {e}")
                    current_left_gesture = "Error"

            # --- 2. DETECT MOVEMENT (RIGHT HAND) ---
            if right_hand_centroid:
                right_hand_centroid_history.append(right_hand_centroid)
                
                # Check for frantic movement if we have enough history
                if len(right_hand_centroid_history) == MOVEMENT_HISTORY_LENGTH:
                    # Calculate total displacement
                    total_displacement = 0
                    for i in range(1, len(right_hand_centroid_history)):
                        x0, y0 = right_hand_centroid_history[i-1]
                        x1, y1 = right_hand_centroid_history[i]
                        total_displacement += np.sqrt((x1-x0)**2 + (y1-y0)**2)
                    
                    if total_displacement > FRANTIC_MOVEMENT_THRESHOLD:
                        is_frantic = True
                        
            else:
                # If right hand is not visible, clear history
                right_hand_centroid_history.clear()

            # --- 3. TRIGGER AUDIO ---
            if is_frantic and current_left_gesture != "None" and current_left_gesture != "Error":
                # Check if this gesture has a sound and it's loaded
                if current_left_gesture in loaded_sounds and loaded_sounds[current_left_gesture]:
                    # Play sound only if it's not already playing or if the gesture changed
                    if not audio_channel.get_busy() or last_played_gesture != current_left_gesture:
                        audio_channel.play(loaded_sounds[current_left_gesture])
                        last_played_gesture = current_left_gesture
                        print(f"Triggered audio for: {current_left_gesture}")
                
            elif not is_frantic:
                # If not strumming, reset the "last played" gesture
                last_played_gesture = None
                # Optional: Stop audio if you want it to cut off immediately
                # if audio_channel.get_busy():
                #     audio_channel.stop()

            # --- 4. DISPLAY INFO ---
            camera_messages = [
                f"Chord Hand (Left): {current_left_gesture}",
                f"Strum Hand (Right) Moving: {'YES' if is_frantic else 'No'}",
                f"Audio: {'PLAYING' if audio_channel.get_busy() else 'Stopped'}"
            ]
            frame = draw_messages(frame, camera_messages, start_y=30, color=(255, 0, 0))

            cv2.imshow('Gesture Control Audio Player', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("INFO: 'q' pressed. Exiting loop.")
                break
                
    except Exception as e:
        print(f"FATAL ERROR: An unexpected error occurred in the main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("INFO: Releasing camera and destroying windows.")
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        print("INFO: Program finished.")

if __name__ == "__main__":
    # Check and create AUDIO_DIR
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        print(f"Created directory: {AUDIO_DIR}")
        print(f"Please put your audio files (e.g., 'boom.mp3', 'am7.mp3') in this directory.")

    # Check if audio files exist before running
    if not audio_loaded_successfully:
         print(f"WARNING: No audio files were successfully loaded from {AUDIO_DIR}.")
         print("The program will run, but no sound will play.")
         print("Please check your GESTURE_AUDIO_MAP and the audio files.")

    print("Starting gesture audio program...")
    print("Show a gesture with your LEFT hand (chord).")
    print("Strum/wave your RIGHT hand to play the sound.")
    print("Press 'q' in the camera window to quit.")
    
    run_gesture_audio_program()