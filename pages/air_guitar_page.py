import customtkinter as ctk
from PIL import Image
import os
import cv2
import mediapipe as mp
import pygame

class AirGuitarPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller
        self.cap = None
        self.is_running = False

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=10)

        self.back_btn = ctk.CTkButton(
            header_frame, text="←", width=50, height=50, corner_radius=25,
            fg_color="#FF7F50", font=("Arial", 24, "bold"),
            command=lambda: controller.show_frame("MainMenu")
        )
        self.back_btn.pack(side="left")

        self.mode_label = ctk.CTkLabel(
            header_frame, text="Playing Mode", font=("HG丸ｺﾞｼｯｸM-PRO", 20, "bold"), text_color="#555"
        )
        self.mode_label.pack(side="left", padx=20)

        # Camera Area
        self.cam_container = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.cam_container.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        self.cam_label = ctk.CTkLabel(self.cam_container, text="", corner_radius=15)
        self.cam_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Logic Variables
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        self.MODES = ["major", "minor", "m7", "maj7"]
        self.NOTES = ["c", "d", "e", "f", "g", "a", "b"]
        self.sounds = {}
        self.current_mode = "major"
        self.sound_val = 0
        
        self.load_sounds()
        self.buttons = []
    
    def load_sounds(self):
        print(f"Loading sounds from: {self.controller.audio_dir}")
        if not os.path.exists(self.controller.audio_dir):
            return

        for mode in self.MODES:
            self.sounds[mode] = {}
            for note in self.NOTES:
                filename = f"{note}_{mode}.wav"
                path = os.path.join(self.controller.audio_dir, filename)
                if os.path.exists(path):
                    self.sounds[mode][note] = pygame.mixer.Sound(path)

    def start_camera(self):
        if not self.is_running:
            self.cap = cv2.VideoCapture(0)
            self.is_running = True
            self.update_frame()

    def stop_camera(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.cam_label.configure(image=None)

    def update_frame(self):
        if not self.is_running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.after(10, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        
        # Zoom Logic
        target_w = self.cam_label.winfo_width()
        target_h = self.cam_label.winfo_height()
        if target_w < 10: target_w = 800
        if target_h < 10: target_h = 600

        h_orig, w_orig = frame.shape[:2]
        scale = max(target_w / w_orig, target_h / h_orig)
        new_w = int(w_orig * scale)
        new_h = int(h_orig * scale)
        frame = cv2.resize(frame, (new_w, new_h))
        
        start_x = (new_w - target_w) // 2
        start_y = (new_h - target_h) // 2
        frame = frame[start_y:start_y+target_h, start_x:start_x+target_w]

        h, w, c = frame.shape 

        # Pose Processing
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        image_rgb.flags.writeable = True

        # Draw UI
        BUTTON_H = int(h * 0.15)
        BUTTON_W = int(w * 0.15)
        BUTTON_Y = 20
        BUTTON_GAP = 20
        BUTTON_START_X = 20
        NECK_Y_START = int(h * 0.4)
        NECK_HEIGHT = int(h * 0.25)
        NECK_X_START = int(w * 0.05)
        NECK_WIDTH = int(w * 0.55)
        STRUM_Y = int(h * 0.5)

        self.buttons = []
        for i, mode in enumerate(self.MODES):
            x = BUTTON_START_X + (i * (BUTTON_W + BUTTON_GAP))
            self.buttons.append({"label": mode, "x": x, "y": BUTTON_Y, "w": BUTTON_W, "h": BUTTON_H, "mode": mode})
            
            color = (0, 200, 0) if self.current_mode == mode else (80, 80, 80)
            cv2.rectangle(frame, (int(x), int(BUTTON_Y)), (int(x+BUTTON_W), int(BUTTON_Y+BUTTON_H)), color, -1)
            cv2.putText(frame, mode, (int(x+10), int(BUTTON_Y+BUTTON_H/1.5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.rectangle(frame, (NECK_X_START, NECK_Y_START), (NECK_X_START + NECK_WIDTH, NECK_Y_START + NECK_HEIGHT), (200, 200, 200), 2)
        zone_width = NECK_WIDTH / len(self.NOTES)
        for i in range(len(self.NOTES)):
            bx = int(NECK_X_START + (i * zone_width))
            if i > 0: cv2.line(frame, (bx, NECK_Y_START), (bx, NECK_Y_START + NECK_HEIGHT), (150, 150, 150), 2)
            cv2.putText(frame, self.NOTES[i].upper(), (int(bx + zone_width/2 - 10), int(NECK_Y_START + NECK_HEIGHT/2 + 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 100), 2)

        s_start = int(w * 0.7)
        cv2.line(frame, (s_start, STRUM_Y), (w, STRUM_Y), (0, 0, 255), 4)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            p_left_wrist = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x * w, landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y * h]
            p_right_wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x * w, landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y * h]

            if p_left_wrist[1] < (BUTTON_Y + BUTTON_H + 50):
                for btn in self.buttons:
                    if btn['x'] < p_left_wrist[0] < btn['x'] + btn['w']:
                        self.current_mode = btn['mode']
            
            current_note_idx = -1
            if (NECK_Y_START - 50) < p_left_wrist[1] < (NECK_Y_START + NECK_HEIGHT + 50):
                rel_x = p_left_wrist[0] - NECK_X_START
                if 0 <= rel_x <= NECK_WIDTH:
                    current_note_idx = int(rel_x // zone_width)
                    if current_note_idx >= len(self.NOTES): current_note_idx = len(self.NOTES) - 1

            if current_note_idx != -1:
                active_x = int(NECK_X_START + (current_note_idx * zone_width))
                overlay = frame.copy()
                cv2.rectangle(overlay, (active_x, NECK_Y_START), (int(active_x + zone_width), NECK_Y_START + NECK_HEIGHT), (0, 255, 0), -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

            if p_right_wrist[0] > s_start:
                if p_right_wrist[1] > STRUM_Y: 
                    if self.sound_val == 0:
                        self.sound_val = 1
                        if current_note_idx != -1:
                            note_key = self.NOTES[current_note_idx]
                            if note_key in self.sounds[self.current_mode]:
                                self.sounds[self.current_mode][note_key].play()
                elif p_right_wrist[1] < STRUM_Y:
                    self.sound_val = 0
            
            cv2.circle(frame, (int(p_right_wrist[0]), int(p_right_wrist[1])), 15, (0, 0, 255), -1)
            cv2.circle(frame, (int(p_left_wrist[0]), int(p_left_wrist[1])), 15, (0, 255, 255), -1)

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ctk.CTkImage(light_image=img, size=(w, h))
        
        self.cam_label.configure(image=imgtk)
        self.cam_label.image = imgtk

        if self.is_running:
            self.after(10, self.update_frame)