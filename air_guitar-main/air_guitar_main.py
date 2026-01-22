import cv2
import mediapipe as mp
import numpy as np
import pygame
import os
import tkinter as tk # Used to get your screen resolution automatically

# --- Configuration ---
pygame.mixer.init()

MODES = ["major", "minor", "m7", "maj7"]
NOTES = ["c", "d", "e", "f", "g", "a", "b"]
sounds = {}

# Load sounds
print("Loading sounds...")
for mode in MODES:
    sounds[mode] = {}
    for note in NOTES:
        filename = f"{note}_{mode}.wav"
        path = os.path.join("audio", filename)
        if os.path.exists(path):
            sounds[mode][note] = pygame.mixer.Sound(path)
        else:
            pass

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# --- GET SCREEN RESOLUTION AUTOMATICALLY ---
root = tk.Tk()
WINDOW_W = root.winfo_screenwidth()
WINDOW_H = root.winfo_screenheight()
root.destroy()

# UI CONSTANTS
BUTTON_Y = 20
BUTTON_H = int(WINDOW_H * 0.08) # Dynamic Height (8% of screen)
BUTTON_W = int(WINDOW_W * 0.10) # Dynamic Width (10% of screen)
BUTTON_GAP = 15
BUTTON_START_X = 20
BUTTON_COLOR_OFF = (80, 80, 80)
BUTTON_COLOR_ON = (0, 200, 0)
TEXT_COLOR = (255, 255, 255)

# Fretboard Constants
NECK_Y_START = int(WINDOW_H * 0.4)
NECK_HEIGHT = int(WINDOW_H * 0.25)
NECK_X_START = int(WINDOW_W * 0.05)
NECK_WIDTH = int(WINDOW_W * 0.55) 

# Strum Line Constants
STRUM_Y = int(WINDOW_H * 0.5) 
STRUM_COLOR = (255, 0, 0) 

current_mode = "major" 
sound_val = 0 

# Create Dynamic Buttons
buttons = []
for i, mode in enumerate(MODES):
    x = BUTTON_START_X + (i * (BUTTON_W + BUTTON_GAP))
    buttons.append({"label": mode, "x": x, "y": BUTTON_Y, "w": BUTTON_W, "h": BUTTON_H, "mode": mode})

cap = cv2.VideoCapture(0)

# --- SETUP FULLSCREEN WINDOW ---
window_name = 'Air Guitar'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        
        # --- ZOOM TO FILL (Screen Resolution) ---
        h_orig, w_orig = frame.shape[:2]
        
        scale_w = WINDOW_W / w_orig
        scale_h = WINDOW_H / h_orig
        scale = max(scale_w, scale_h)
        
        new_w = int(w_orig * scale)
        new_h = int(h_orig * scale)
        frame_resized = cv2.resize(frame, (new_w, new_h))
        
        start_x = (new_w - WINDOW_W) // 2
        start_y = (new_h - WINDOW_H) // 2
        
        image = frame_resized[start_y:start_y+WINDOW_H, start_x:start_x+WINDOW_W]
        
        # Update dimensions
        h, w, c = image.shape 
        
        # Process Pose
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        
        # --- DRAW INTERFACE ---
        
        # Draw Buttons
        for btn in buttons:
            color = BUTTON_COLOR_ON if current_mode == btn['mode'] else BUTTON_COLOR_OFF
            cv2.rectangle(image, (int(btn['x']), int(btn['y'])), (int(btn['x'] + btn['w']), int(btn['y'] + btn['h'])), color, -1)
            cv2.putText(image, btn['label'], (int(btn['x'] + 10), int(btn['y'] + (BUTTON_H/1.5))), cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2)

        # Draw Fretboard
        cv2.rectangle(image, (NECK_X_START, NECK_Y_START), (NECK_X_START + NECK_WIDTH, NECK_Y_START + NECK_HEIGHT), (200, 200, 200), 2)
        cv2.putText(image, "FRETBOARD AREA", (NECK_X_START, NECK_Y_START - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

        num_notes = len(NOTES)
        zone_width = NECK_WIDTH / num_notes
        
        for i in range(num_notes):
            bx = int(NECK_X_START + (i * zone_width))
            if i > 0: 
                cv2.line(image, (bx, NECK_Y_START), (bx, NECK_Y_START + NECK_HEIGHT), (150, 150, 150), 2)
            
            label_x = int(bx + zone_width/2 - 10)
            label_y = int(NECK_Y_START + NECK_HEIGHT/2 + 10)
            cv2.putText(image, NOTES[i].upper(), (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 100), 2)

        # Draw Strum Line
        s_start = int(w * 0.7) 
        s_end = w
        cv2.line(image, (s_start, STRUM_Y), (s_end, STRUM_Y), STRUM_COLOR, 4)
        cv2.putText(image, "STRUM HERE", (s_start, STRUM_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, STRUM_COLOR, 2)

        # --- HAND TRACKING LOGIC ---
        try:
            landmarks = results.pose_landmarks.landmark
            p_left_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x * w, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y * h]
            p_right_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x * w, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y * h]

            # 1. Button Logic
            if p_left_wrist[1] < (BUTTON_Y + BUTTON_H + 50): 
                for btn in buttons:
                    if (btn['x'] < p_left_wrist[0] < btn['x'] + btn['w']):
                        current_mode = btn['mode']

            # 2. Note Selection
            current_note_idx = -1
            if (NECK_Y_START - 50) < p_left_wrist[1] < (NECK_Y_START + NECK_HEIGHT + 50):
                rel_x = p_left_wrist[0] - NECK_X_START
                if 0 <= rel_x <= NECK_WIDTH:
                    current_note_idx = int(rel_x // zone_width)
                    if current_note_idx >= len(NOTES): current_note_idx = len(NOTES) - 1
            
            if current_note_idx != -1:
                active_x = int(NECK_X_START + (current_note_idx * zone_width))
                overlay = image.copy()
                cv2.rectangle(overlay, (active_x, NECK_Y_START), (int(active_x + zone_width), NECK_Y_START + NECK_HEIGHT), (0, 255, 0), -1)
                cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)

                preview_text = f"{NOTES[current_note_idx].upper()} {current_mode}"
                cv2.putText(image, f"Ready: {preview_text}", (int(w/2 - 100), 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # 3. Strum Trigger
            if p_right_wrist[0] > s_start:
                if p_right_wrist[1] > STRUM_Y: 
                    if sound_val == 0:
                        sound_val = 1
                        if current_note_idx != -1:
                            note_key = NOTES[current_note_idx]
                            if note_key in sounds[current_mode]:
                                sounds[current_mode][note_key].play()
                elif p_right_wrist[1] < STRUM_Y:
                    sound_val = 0

            cv2.circle(image, (int(p_right_wrist[0]), int(p_right_wrist[1])), 15, (0, 0, 255), -1) 
            cv2.circle(image, (int(p_left_wrist[0]), int(p_left_wrist[1])), 15, (0, 255, 255), -1)

        except Exception as e:
            pass

        # SHOW IMAGE IN FULLSCREEN WINDOW
        cv2.imshow(window_name, image)
        
        # Press 'q' to quit
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()