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

# --- Main Dataset Collection Loop ---
def collect_gestures():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    gesture_name = input("Enter gesture name to collect (e.g., 'fist', 'open_hand', 'point'): ").strip()
    if not gesture_name:
        print("Gesture name cannot be empty. Exiting.")
        cap.release()
        return

    csv_file_path = os.path.join(DATA_DIR, f'{gesture_name}_data.csv')
    
    # Check if file exists to decide if header is needed
    file_exists = os.path.exists(csv_file_path)

    with open(csv_file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists or os.stat(csv_file_path).st_size == 0: # Add header only if file is new or empty
            # Create header for 21 landmarks * 3 coordinates + 1 for label
            header = [f'lm_{i}_{coord}' for i in range(21) for coord in ['x', 'y', 'z']]
            header.append('label')
            writer.writerow(header)
        
        print(f"Collecting data for '{gesture_name}'. Press 's' to start recording, 'q' to quit.")
        
        recording = False
        start_time = time.time()
        record_duration = 5 # seconds per gesture
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Flip frame horizontally for a mirror effect
            frame = cv2.flip(frame, 1)
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    # For simplicity in dataset collection, let's just use the first detected hand
                    # In main program, we'll differentiate left/right
                    
                    # Draw landmarks on the frame
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    if recording:
                        features = extract_landmark_features(hand_landmarks)
                        if features:
                            row = features + [gesture_name]
                            writer.writerow(row)
                            cv2.putText(frame, "RECORDING...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            
            if recording and (time.time() - start_time) > record_duration:
                recording = False
                print(f"Finished recording {record_duration} seconds for '{gesture_name}'.")
                print("Press 's' to record again for the same gesture, or 'q' to quit.")


            cv2.imshow('Gesture Dataset Creator', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s') and not recording:
                recording = True
                start_time = time.time()
                print(f"Started recording for '{gesture_name}'...")
                
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    print("Welcome to the Gesture Dataset Creator!")
    print("You will be prompted to enter a gesture name. Then, press 's' to start recording.")
    print("Hold your hand steady in the gesture for a few seconds. Press 'q' to exit.")
    collect_gestures()
    print("Dataset collection complete. You can run this script again for different gestures.")