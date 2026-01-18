import cv2
import mediapipe as mp
import csv
import numpy as np
import os
import time
import random
import math

# --- Setup MediaPipe ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1, 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# --- Dataset Configuration ---
DATA_DIR = 'gesture_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- CONFIGURATION ---
PALM_LENGTH_THRESHOLD = 0.1 

# --- INDICES TO USE (NO THUMB) ---
LANDMARK_INDICES_TO_USE = [0] + list(range(5, 21))

# Map user input (1-4) to landmark indices
FINGER_MAP = {
    '1': [5, 6, 7, 8],      # Index
    '2': [9, 10, 11, 12],   # Middle
    '3': [13, 14, 15, 16],  # Ring
    '4': [17, 18, 19, 20]   # Pinky
}

FINGER_NAMES = {
    '1': "Idx",
    '2': "Mid",
    '3': "Ring",
    '4': "Pnky"
}

# --- Helper Functions ---
def extract_landmark_features(hand_landmarks, ignored_finger_indices=[]):
    features = []
    if hand_landmarks:
        base_x = hand_landmarks.landmark[0].x
        base_y = hand_landmarks.landmark[0].y
        base_z = hand_landmarks.landmark[0].z 

        # 1. Position Features (with Noise Injection)
        for i in LANDMARK_INDICES_TO_USE:
            if i in ignored_finger_indices:
                noise_x = random.uniform(-0.2, 0.2)
                noise_y = random.uniform(-0.2, 0.2)
                noise_z = random.uniform(-0.2, 0.2)
                features.extend([noise_x, noise_y, noise_z])
            else:
                landmark = hand_landmarks.landmark[i]
                features.extend([landmark.x - base_x, landmark.y - base_y, landmark.z - base_z])

        # 2. Inter-Fingertip Distances
        TIP_IDS = [8, 12, 16, 20]

        for i in range(len(TIP_IDS)):
            for j in range(i + 1, len(TIP_IDS)):
                id1 = TIP_IDS[i]
                id2 = TIP_IDS[j]

                # Find index in our custom list to retrieve correct feature data
                idx1_in_list = LANDMARK_INDICES_TO_USE.index(id1)
                idx2_in_list = LANDMARK_INDICES_TO_USE.index(id2)

                # Extract (x,y,z) from the features list we just built
                x1 = features[idx1_in_list*3]
                y1 = features[idx1_in_list*3 + 1]
                z1 = features[idx1_in_list*3 + 2]

                x2 = features[idx2_in_list*3]
                y2 = features[idx2_in_list*3 + 1]
                z2 = features[idx2_in_list*3 + 2]

                dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
                features.append(dist)

    return features

def is_back_of_hand(hand_landmarks):
    # Pinky > Index for Left Hand (Mirrored)
    return hand_landmarks.landmark[17].x > hand_landmarks.landmark[5].x

def check_palm_length(hand_landmarks):
    wrist = hand_landmarks.landmark[0]
    knuckles = [5, 9, 13, 17]
    avg_distance = 0
    for k in knuckles:
        knuckle = hand_landmarks.landmark[k]
        dist = math.sqrt((knuckle.x - wrist.x)**2 + (knuckle.y - wrist.y)**2)
        avg_distance += dist
    avg_distance /= 4
    return avg_distance > PALM_LENGTH_THRESHOLD

def draw_feedback(frame, orientation_ok, palm_length_ok):
    h, w, _ = frame.shape
    if not palm_length_ok:
        color = (0, 0, 255) # Red
        text = "BAD ANGLE: FLATTEN HAND"
    elif not orientation_ok:
        color = (0, 165, 255) # Orange
        text = "SHOW BACK OF HAND"
    else:
        color = (0, 255, 0) # Green
        text = "HAND POSITION: OK"
    cv2.putText(frame, text, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return frame

def draw_custom_landmarks(frame, hand_landmarks):
    h, w, _ = frame.shape
    # 1. Base landmarks (Gray)
    mp_drawing.draw_landmarks(
        frame, 
        hand_landmarks, 
        mp_hands.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(200, 200, 200), thickness=2, circle_radius=2), 
        mp_drawing.DrawingSpec(color=(220, 220, 220), thickness=2, circle_radius=2)  
    )
    # 2. Colored Tips
    tips = {8: (0, 255, 255), 12: (255, 255, 0), 16: (255, 0, 255), 20: (0, 0, 255)}
    for idx, color in tips.items():
        lm = hand_landmarks.landmark[idx]
        cx, cy = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (cx, cy), 12, (255, 255, 255), 2)
        cv2.circle(frame, (cx, cy), 8, color, cv2.FILLED)

def draw_messages(frame, messages, start_y=30, line_height=40, font_scale=1, color=(0, 255, 0), thickness=2):
    for i, msg in enumerate(messages):
        y_pos = start_y + i * line_height
        cv2.putText(frame, msg, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
    return frame

# --- Main Dataset Collection Loop ---
def collect_gestures():
    cap = cv2.VideoCapture(4) 
    if not cap.isOpened():
        print(f"Error: Could not open video stream.")
        return

    gesture_name = ""
    ignored_input = ""
    ignored_indices_list = []
    ignored_display_names = "None"
    capturing_name = True
    capturing_ignore = False
    current_input_text = ""
    csv_file_path = "" 
    file_exists = False
    recording = False
    start_time = 0
    record_duration = 5 
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1) 
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        hand_orientation_ok = False
        hand_length_ok = False
        features_to_record = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                draw_custom_landmarks(frame, hand_landmarks)
                hand_orientation_ok = is_back_of_hand(hand_landmarks)
                hand_length_ok = check_palm_length(hand_landmarks)
                
                if hand_orientation_ok and hand_length_ok:
                    features_to_record = hand_landmarks
                
        frame = draw_feedback(frame, hand_orientation_ok, hand_length_ok)

        if capturing_name:
            camera_messages = ["Step 1: Enter Gesture Name", f"> {current_input_text}_", "(Press Enter)"]
        elif capturing_ignore:
             camera_messages = [f"Gesture: {gesture_name}", "Step 2: Ignore Fingers? (e.g. '34')", f"> {current_input_text}_", "(Press Enter)"]
        elif recording:
            if not hand_length_ok:
                 camera_messages = ["PAUSED: FLATTEN HAND"]
                 start_time += 0.033
            elif not hand_orientation_ok:
                camera_messages = ["PAUSED: SHOW BACK OF HAND"]
                start_time += 0.033
            else:
                time_left = max(0, int(record_duration - (time.time() - start_time)))
                camera_messages = [f"Collecting: {gesture_name}", f"Ignored: {ignored_display_names}", f"RECORDING... {time_left}s"]
        else: 
            camera_messages = [f"Ready: {gesture_name}", f"Ignored: {ignored_display_names}", "Press 's' to START, 'q' to QUIT"]
            
        frame = draw_messages(frame, camera_messages)
        cv2.imshow('Gesture Dataset Creator', frame)
        key = cv2.waitKey(1) & 0xFF

        if capturing_name:
            if key == 13 or key == 10: # Enter
                gesture_name = current_input_text.strip()
                if gesture_name:
                    capturing_name = False
                    capturing_ignore = True
                    current_input_text = ""
            elif key == 8 or key == 127: current_input_text = current_input_text[:-1]
            elif 32 <= key <= 126: current_input_text += chr(key)
        elif capturing_ignore:
            if key == 13 or key == 10: # Enter
                ignored_input = current_input_text.strip()
                ignored_indices_list = []
                display_names_list = []
                for char in ignored_input:
                    if char in FINGER_MAP:
                        ignored_indices_list.extend(FINGER_MAP[char])
                        if FINGER_NAMES[char] not in display_names_list:
                            display_names_list.append(FINGER_NAMES[char])
                ignored_display_names = ", ".join(display_names_list) if display_names_list else "None"
                capturing_ignore = False
                csv_file_path = os.path.join(DATA_DIR, f'{gesture_name}_data.csv')
                file_exists = os.path.exists(csv_file_path)
                current_input_text = ""
            elif key == 8 or key == 127: current_input_text = current_input_text[:-1]
            elif 32 <= key <= 126: current_input_text += chr(key)
        else:
            if key == ord('q'): break
            elif key == ord('s') and not recording:
                recording = True
                start_time = time.time()
                
        if recording and (time.time() - start_time) <= record_duration:
            if hand_orientation_ok and hand_length_ok and features_to_record:
                features = extract_landmark_features(features_to_record, ignored_indices_list)
                if features:
                    with open(csv_file_path, 'a', newline='') as f:
                        writer = csv.writer(f)
                        if not file_exists or os.stat(csv_file_path).st_size == 0:
                            # --- FIXED HEADER GENERATION ---
                            # 1. Standard Features (No Thumb)
                            header = [f'lm_{i}_{coord}' for i in LANDMARK_INDICES_TO_USE for coord in ['x', 'y', 'z']]
                            
                            # 2. Distance Features
                            TIP_IDS = [8, 12, 16, 20]
                            for i in range(len(TIP_IDS)):
                                for j in range(i + 1, len(TIP_IDS)):
                                    header.append(f'dist_{TIP_IDS[i]}_{TIP_IDS[j]}')
                            
                            header.append('label')
                            writer.writerow(header)
                            file_exists = True 
                        
                        row = features + [gesture_name]
                        writer.writerow(row)
        elif recording and (time.time() - start_time) > record_duration:
            recording = False

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    collect_gestures()