import customtkinter as ctk
import os
import cv2
import mediapipe as mp
import pygame
import json
import re
from PIL import Image

class LyricGuitarPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller
        self.cap = None
        self.is_running = False
        
        self.current_song_data = None
        self.current_block_index = 0
        
        # This list will hold the specific chords for the active song
        # Format: [{'label': 'Am', 'root': 'a', 'mode': 'minor'}, ...]
        self.active_song_chords = [] 

        # --- HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=10)

        self.back_btn = ctk.CTkButton(
            header_frame, text="←", width=50, height=50, corner_radius=25,
            fg_color="#FF7F50", font=("Arial", 24, "bold"),
            command=self.go_back
        )
        self.back_btn.pack(side="left")

        self.title_label = ctk.CTkLabel(
            header_frame, text="Lyric Mode", font=("HG丸ｺﾞｼｯｸM-PRO", 20, "bold"), text_color="#555"
        )
        self.title_label.pack(side="left", padx=20)

        # --- CAMERA ---
        self.cam_container = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.cam_container.pack(fill="both", expand=True, padx=40, pady=(10, 10))

        self.cam_label = ctk.CTkLabel(self.cam_container, text="", corner_radius=15)
        self.cam_label.pack(fill="both", expand=True, padx=5, pady=5)

        # --- LYRICS PANEL ---
        self.lyrics_frame = ctk.CTkFrame(self, fg_color="#FFF0E0", height=150)
        self.lyrics_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        self.prev_line_btn = ctk.CTkButton(self.lyrics_frame, text="<", width=40, command=self.prev_line)
        self.prev_line_btn.pack(side="left", padx=10)

        self.text_container = ctk.CTkFrame(self.lyrics_frame, fg_color="transparent")
        self.text_container.pack(side="left", fill="both", expand=True)

        self.chord_display_label = ctk.CTkLabel(
            self.text_container, text="", font=("Consolas", 24, "bold"), text_color="#FF4500", anchor="w"
        )
        self.chord_display_label.pack(fill="x", pady=(5, 0))

        self.lyric_display_label = ctk.CTkLabel(
            self.text_container, text="Ready...", font=("Consolas", 20), text_color="#333", anchor="w"
        )
        self.lyric_display_label.pack(fill="x", pady=(0, 5))

        self.next_line_btn = ctk.CTkButton(self.lyrics_frame, text=">", width=40, command=self.next_line)
        self.next_line_btn.pack(side="right", padx=10)

        # --- CV SETUP ---
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # Sound System
        self.MODES = ["major", "minor", "m7", "maj7"]
        self.NOTES = ["c", "d", "e", "f", "g", "a", "b"]
        self.sounds = {}
        self.sound_val = 0
        self.load_sounds()

    def load_sounds(self):
        if not os.path.exists(self.controller.audio_dir): return
        for mode in self.MODES:
            self.sounds[mode] = {}
            for note in self.NOTES:
                filename = f"{note}_{mode}.wav"
                path = os.path.join(self.controller.audio_dir, filename)
                if os.path.exists(path):
                    self.sounds[mode][note] = pygame.mixer.Sound(path)

    # --- NEW: PARSE CHORDS FOR THIS SONG ---
    def parse_chord_to_sound(self, chord_name):
        """Converts 'Am' -> root='a', mode='minor'"""
        # 1. Regex to split Root (A-G#) from Mode (m, m7, etc)
        match = re.match(r"^([A-G][#b]?)(.*)$", chord_name)
        if not match: return None

        root_str = match.group(1).lower() # 'C' -> 'c'
        suffix = match.group(2)
        
        # 2. Map suffix to filename mode
        mode = "major" # Default (e.g. for 'C')
        if suffix == "m": mode = "minor"
        elif suffix == "m7": mode = "m7"
        elif suffix == "maj7": mode = "maj7"
        
        # 3. Handle Sharps/Flats if necessary (Simple mapping for now)
        # Assuming your files are simple c, d, e. If you have sharps, add logic here.
        if len(root_str) > 1:
            # Fallback for sharps if you don't have files: strip it
            root_str = root_str[0] 

        return {"label": chord_name, "root": root_str, "mode": mode}

    def load_song_json(self, filename):
        filepath = os.path.join(self.controller.lyrics_dir, filename)
        if not os.path.exists(filepath): return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.current_song_data = data
        self.current_block_index = 0
        
        title = data.get('meta', {}).get('title', 'Unknown')
        self.title_label.configure(text=f"Playing: {title}")
        
        # --- BUILD THE CUSTOM FRETBOARD ---
        chords_used = data.get('meta', {}).get('chords_used', [])
        self.active_song_chords = []
        
        for chord in chords_used:
            parsed = self.parse_chord_to_sound(chord)
            if parsed:
                self.active_song_chords.append(parsed)
        
        # If no chords found, add a dummy one to prevent crashes
        if not self.active_song_chords:
            self.active_song_chords.append({"label": "No Chords", "root": "c", "mode": "major"})

        self.update_lyric_display()

    # [Formatting Helper]
    def format_chord_string(self, chords_dict, text_length):
        buffer = [" "] * max(text_length, 50)
        for idx_str, chord_name in chords_dict.items():
            idx = int(idx_str)
            if idx < len(buffer):
                for i, char in enumerate(chord_name):
                    if idx + i < len(buffer):
                        buffer[idx + i] = char
        return "".join(buffer).rstrip()

    def update_lyric_display(self):
        if not self.current_song_data: return
        blocks = self.current_song_data.get('lyrics', [])
        if 0 <= self.current_block_index < len(blocks):
            block = blocks[self.current_block_index]
            text = block.get('text', '')
            chords_dict = block.get('chords', {})
            chord_str = self.format_chord_string(chords_dict, len(text))
            
            self.lyric_display_label.configure(text=text)
            self.chord_display_label.configure(text=chord_str)
        else:
            self.lyric_display_label.configure(text="End of Song")
            self.chord_display_label.configure(text="")

    def next_line(self):
        if self.current_song_data and self.current_block_index < len(self.current_song_data['lyrics']) - 1:
            self.current_block_index += 1
            self.update_lyric_display()

    def prev_line(self):
        if self.current_song_data and self.current_block_index > 0:
            self.current_block_index -= 1
            self.update_lyric_display()

    def start_camera(self):
        if not self.is_running:
            self.cap = cv2.VideoCapture(0)
            self.is_running = True
            self.update_frame()

    def stop_camera(self):
        self.is_running = False
        if self.cap: self.cap.release()
        self.cam_label.configure(image=None)

    def go_back(self):
        self.stop_camera()
        self.controller.show_frame("SongSelectionPage")

    def update_frame(self):
        if not self.is_running: return
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

        # --- DRAWING CONSTANTS ---
        NECK_Y_START = int(h * 0.4)
        NECK_HEIGHT = int(h * 0.25)
        NECK_X_START = int(w * 0.05)
        NECK_WIDTH = int(w * 0.55)
        STRUM_Y = int(h * 0.5)

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        
        # --- DRAW CUSTOM FRETBOARD ---
        # Draw background
        cv2.rectangle(frame, (NECK_X_START, NECK_Y_START), (NECK_X_START + NECK_WIDTH, NECK_Y_START + NECK_HEIGHT), (200, 200, 200), 2)
        
        # Calculate dynamic width based on number of chords in song
        num_chords = len(self.active_song_chords)
        if num_chords > 0:
            zone_width = NECK_WIDTH / num_chords
            
            for i in range(num_chords):
                bx = int(NECK_X_START + (i * zone_width))
                # Draw Divider
                if i > 0: 
                    cv2.line(frame, (bx, NECK_Y_START), (bx, NECK_Y_START + NECK_HEIGHT), (150, 150, 150), 2)
                
                # Draw Label (The specific chord name!)
                chord_label = self.active_song_chords[i]['label']
                label_x = int(bx + zone_width/2 - 20)
                label_y = int(NECK_Y_START + NECK_HEIGHT/2 + 10)
                
                # Highlight logic handled later, this is static drawing
                cv2.putText(frame, chord_label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (50, 50, 50), 2)

        # Draw Strum Line
        s_start = int(w * 0.7)
        cv2.line(frame, (s_start, STRUM_Y), (w, STRUM_Y), (0, 0, 255), 4)

        # --- HAND TRACKING ---
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            p_left_wrist = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x * w, landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y * h]
            p_right_wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x * w, landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y * h]

            # 1. Selection Logic (Modified for Active Song Chords)
            current_chord_idx = -1
            if num_chords > 0 and (NECK_Y_START - 50) < p_left_wrist[1] < (NECK_Y_START + NECK_HEIGHT + 50):
                rel_x = p_left_wrist[0] - NECK_X_START
                if 0 <= rel_x <= NECK_WIDTH:
                    current_chord_idx = int(rel_x // zone_width)
                    if current_chord_idx >= num_chords: current_chord_idx = num_chords - 1

            if current_chord_idx != -1:
                # Highlight active zone
                active_x = int(NECK_X_START + (current_chord_idx * zone_width))
                overlay = frame.copy()
                cv2.rectangle(overlay, (active_x, NECK_Y_START), (int(active_x + zone_width), NECK_Y_START + NECK_HEIGHT), (0, 255, 0), -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

            # 2. Strumming Logic (Using Active Song Data)
            if p_right_wrist[0] > s_start:
                if p_right_wrist[1] > STRUM_Y: 
                    if self.sound_val == 0:
                        self.sound_val = 1
                        if current_chord_idx != -1:
                            # PLAY THE MAPPED SOUND
                            chord_data = self.active_song_chords[current_chord_idx]
                            root = chord_data['root']
                            mode = chord_data['mode']
                            
                            if mode in self.sounds and root in self.sounds[mode]:
                                self.sounds[mode][root].play()
                            else:
                                print(f"Sound missing: {root}_{mode}")
                elif p_right_wrist[1] < STRUM_Y:
                    self.sound_val = 0
            
            # Draw Hands
            cv2.circle(frame, (int(p_right_wrist[0]), int(p_right_wrist[1])), 15, (0, 0, 255), -1)
            cv2.circle(frame, (int(p_left_wrist[0]), int(p_left_wrist[1])), 15, (0, 255, 255), -1)

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ctk.CTkImage(light_image=img, size=(target_w, target_h))
        self.cam_label.configure(image=imgtk)

        self.after(10, self.update_frame)