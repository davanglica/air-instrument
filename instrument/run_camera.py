import cv2
import mediapipe as mp
import joblib
import numpy as np
import os
import pygame # For audio playback
from collections import deque # For tracking hand movement history

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
    "fist": "fist_audio.mp3",
    "open_hand": "open_hand_audio.mp3",
    "point": "point_audio.mp3",
    # Add more mappings as you train new gestures and create corresponding audio files
}

loaded_sounds = {}
for gesture, filename in GESTURE_AUDIO_MAP.items():
    audio_path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(audio_path):
        try:
            loaded_sounds[gesture] = pygame.mixer.Sound(audio_path)
            print(f"Loaded audio for '{gesture}': {filename}")
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

# --- Main Program Loop ---
def run_gesture_audio_program():
    global current_left_gesture, right_hand_centroid_history, audio_is_playing, last_played_gesture

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    print("Starting real-time gesture detection and audio playback.")
    print("Show your left hand for gesture recognition.")
    print(f"Move your right hand 'frantically' (total displacement > {FRANTIC_MOVEMENT_THRESHOLD:.3f}) to trigger audio.")
    print("Press 'q' to quit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1) # Flip for mirror effect
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        left_hand_detected = False
        right_hand_landmarks = None
        
        # Reset current gesture if no hands are detected
        if not results.multi_hand_landmarks:
             current_left_gesture = "None"
             right_hand_centroid_history.clear() # Clear history if right hand is gone

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                hand_type = handedness.classification[0].label # 'Left' or 'Right'
                
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                features = extract_landmark_features(hand_landmarks)
                if not features:
                    continue
                    
                # Predict gesture for left hand
                if hand_type == 'Left':
                    left_hand_detected = True
                    if len(features) == 63: # Ensure features match expected model input size (21 * 3)
                        try:
                            prediction = model.predict(np.array(features).reshape(1, -1))
                            current_left_gesture = label_encoder.inverse_transform(prediction)[0]
                        except Exception as e:
                            current_left_gesture = f"Error: {e}"
                    else:
                        current_left_gesture = f"Feature mismatch ({len(features)} != 63)"

                # Capture right hand landmarks for movement detection
                if hand_type == 'Right':
                    right_hand_landmarks = hand_landmarks
        
        # --- Right Hand Frantic Movement Detection Logic ---
        is_frantically_moving = False
        if right_hand_landmarks:
            current_centroid = get_hand_centroid(right_hand_landmarks)
            if current_centroid:
                right_hand_centroid_history.append(current_centroid)
                
                if len(right_hand_centroid_history) == MOVEMENT_HISTORY_LENGTH:
                    # Calculate total displacement
                    total_displacement = 0.0
                    for i in range(1, MOVEMENT_HISTORY_LENGTH):
                        p1 = right_hand_centroid_history[i-1]
                        p2 = right_hand_centroid_history[i]
                        total_displacement += np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                    
                    if total_displacement > FRANTIC_MOVEMENT_THRESHOLD:
                        is_frantically_moving = True
                        
            cv2.putText(frame, f"RH Centroid Disp: {total_displacement:.3f}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
        else:
            right_hand_centroid_history.clear() # Clear history if right hand disappears

        # --- Audio Trigger Logic ---
        # Only trigger if a left hand gesture is recognized AND right hand is moving frantically
        if left_hand_detected and current_left_gesture != "None" and current_left_gesture != "Error" and is_frantically_moving:
            desired_sound = loaded_sounds.get(current_left_gesture)
            if desired_sound and not audio_channel.get_busy() and last_played_gesture != current_left_gesture:
                audio_channel.play(desired_sound)
                audio_is_playing = True
                last_played_gesture = current_left_gesture # Store which gesture just played audio
                print(f"Playing audio for gesture '{current_left_gesture}'!")
        elif not is_frantically_moving and audio_channel.get_busy():
            # If not frantically moving, stop audio. This makes it more responsive.
            audio_channel.stop()
            audio_is_playing = False
            last_played_gesture = None # Reset when audio stops
        
        if not audio_channel.get_busy():
            audio_is_playing = False
            
        # Display information on frame
        cv2.putText(frame, f"Left Hand Gesture: {current_left_gesture}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Right Hand: {'Detected' if right_hand_landmarks else 'Not Detected'}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"RH Moving Frantically: {is_frantically_moving}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Audio Playing: {audio_is_playing}", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)


        cv2.imshow('Gesture Control Audio Player', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    pygame.mixer.quit() # Clean up pygame mixer

if __name__ == "__main__":
    # Create the audio_files directory if it doesn't exist
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        print(f"Created directory: {AUDIO_DIR}.")
        print("Audio inmatch found. Please update audio or gesture list.")
        
    run_gesture_audio_program()