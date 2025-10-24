import cv2
import mediapipe as mp
import csv
import numpy as np
import os
import time

# --- Setup MediaPipe ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1, # Only need to track one hand for dataset creation
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# --- Dataset Configuration ---
DATA_DIR = 'gesture_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- Function to extract hand landmarks ---
def extract_landmark_features(hand_landmarks):
    features = []
    if hand_landmarks:
        # Normalize landmarks relative to the wrist (or first landmark)
        base_x = hand_landmarks.landmark[0].x
        base_y = hand_landmarks.landmark[0].y
        base_z = hand_landmarks.landmark[0].z # Not always used but good to include for 3D

        for landmark in hand_landmarks.landmark:
            features.extend([landmark.x - base_x, landmark.y - base_y, landmark.z - base_z])
    return features

# --- Function to display multiple lines of text on the frame ---
def draw_messages(frame, messages, start_y=30, line_height=40, font_scale=1, color=(0, 255, 0), thickness=2):
    for i, msg in enumerate(messages):
        y_pos = start_y + i * line_height
        cv2.putText(frame, msg, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
    return frame

# --- Main Dataset Collection Loop ---
def collect_gestures():
    # --- CHANGE THIS LINE TO YOUR CAMERA INDEX ---
    cap = cv2.VideoCapture(4) # Using 5 for /dev/video5
    if not cap.isOpened():
        print(f"Error: Could not open video stream from camera index 5. Check if /dev/video5 is available and permissions are correct.")
        return

    # Initial prompt, will be displayed both on terminal and camera
    initial_prompt = "Enter gesture name to collect (e.g., 'fist'): "
    print(initial_prompt, end='') # Use end='' to keep input on same line in terminal
    
    gesture_name = ""
    # We'll use a state machine for input capture on the camera feed
    capturing_name = True
    current_input_text = ""
    
    # Text messages to display on camera
    camera_messages = ["Initializing...", ""] # Placeholder for dynamic messages

    csv_file_path = "" # Will be set once gesture_name is finalized
    file_exists = False
    
    recording = False
    start_time = 0
    record_duration = 5 # seconds per gesture
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame from camera. Exiting.")
            break

        frame = cv2.flip(frame, 1) # Flip frame horizontally for a mirror effect
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
        # Update camera messages based on current state
        if capturing_name:
            camera_messages = [
                initial_prompt,
                f"> {current_input_text}_" # Show current input, cursor underscore
            ]
        elif not gesture_name: # If somehow name capture is done but name is empty
             camera_messages = ["Gesture name cannot be empty. Press 'q' to exit."]
        elif recording:
            time_left = max(0, int(record_duration - (time.time() - start_time)))
            camera_messages = [
                f"Collecting '{gesture_name}'...",
                f"RECORDING... {time_left}s left",
                "Keep your LEFT hand steady in gesture.",
                "Press 'q' to quit."
            ]
        else: # Not recording, name finalized
            camera_messages = [
                f"Ready to record '{gesture_name}'.",
                "Press 's' to START recording.",
                "Press 'q' to quit."
            ]
            
        frame = draw_messages(frame, camera_messages)

        cv2.imshow('Gesture Dataset Creator', frame)

        key = cv2.waitKey(1) & 0xFF

        if capturing_name:
            if key == ord('\r') or key == ord('\n'): # Enter key
                gesture_name = current_input_text.strip()
                if not gesture_name:
                    print("Gesture name cannot be empty. Please try again.")
                    current_input_text = "" # Clear for re-entry
                else:
                    capturing_name = False
                    csv_file_path = os.path.join(DATA_DIR, f'{gesture_name}_data.csv')
                    file_exists = os.path.exists(csv_file_path)
                    print(f"Chosen gesture name: '{gesture_name}'") # Also print to terminal for confirmation
            elif key == 8 or key == 127: # Backspace or Delete
                current_input_text = current_input_text[:-1]
            elif 32 <= key <= 126: # Printable characters (ASCII)
                current_input_text += chr(key)
        else: # Not capturing name, ready for recording
            if key == ord('q'):
                break
            elif key == ord('s') and not recording:
                recording = True
                start_time = time.time()
                print(f"Started recording for '{gesture_name}'...")
                
        # Handle actual recording and writing to CSV when in recording state
        if recording and (time.time() - start_time) <= record_duration:
            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    features = extract_landmark_features(hand_landmarks)
                    if features:
                        # Ensure header is written once
                        with open(csv_file_path, 'a', newline='') as f:
                            writer = csv.writer(f)
                            if not file_exists or os.stat(csv_file_path).st_size == 0:
                                header = [f'lm_{i}_{coord}' for i in range(21) for coord in ['x', 'y', 'z']]
                                header.append('label')
                                writer.writerow(header)
                                file_exists = True # Mark as written
                            
                            row = features + [gesture_name]
                            writer.writerow(row)
        elif recording and (time.time() - start_time) > record_duration:
            recording = False
            print(f"Finished recording {record_duration} seconds for '{gesture_name}'.")
            print("Press 's' to record again for the same gesture, or 'q' to quit.")

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    print("Welcome to the Gesture Dataset Creator!")
    print("Instructions will also appear on the camera feed.")
    collect_gestures()
    print("Dataset collection complete. You can run this script again for different gestures.")