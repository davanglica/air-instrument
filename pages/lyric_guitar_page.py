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
        
        # State
        self.current_song_data = None
        self.current_block_index = 0
        self.active_song_chords = [] 
        self.required_sequence = []
        self.current_sequence_progress = 0
        self.is_transitioning = False
        self.transition_delay = 1000
        self.prev_left_wrist = None
        self.prev_right_wrist = None
        self.SMOOTHING_FACTOR = 0.5

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=10)

        arrow_path = os.path.join(self.controller.assets_dir, "arrow.png")
        try:
            arrow_img = ctk.CTkImage(light_image=Image.open(arrow_path), size=(40, 40))
        except:
            arrow_img = None

        self.back_btn = ctk.CTkButton(
            header_frame, text="", image=arrow_img, width=50, height=50, 
            fg_color="transparent", hover_color="#FFE4C4",
            command=self.go_back
        )
        self.back_btn.pack(side="left")

        self.title_label = ctk.CTkLabel(
            header_frame, text="Lyric Mode", font=("HG丸ｺﾞｼｯｸM-PRO", 20, "bold"), text_color="#555"
        )
        self.title_label.pack(side="left", padx=20)

        # Camera
        self.cam_container = ctk.CTkFrame(self, fg_color="black", corner_radius=0) 
        self.cam_container.pack(fill="both", expand=True, padx=0, pady=(10, 0))

        self.cam_label = ctk.CTkLabel(self.cam_container, text="", corner_radius=0)
        self.cam_label.pack(fill="both", expand=True, padx=0, pady=0)

        # Lyrics Panel
        self.lyrics_frame = ctk.CTkFrame(self, fg_color="#FFF0E0", height=150)
        self.lyrics_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        self.text_container = ctk.CTkFrame(self.lyrics_frame, fg_color="transparent")
        self.text_container.pack(fill="both", expand=True)

        self.chord_display_label = ctk.CTkLabel(
            self.text_container, text="", font=("Consolas", 32, "bold"), text_color="#FF4500", anchor="center"
        )
        self.chord_display_label.pack(fill="x", pady=(5, 0))

        self.lyric_display_label = ctk.CTkLabel(
            self.text_container, text="Ready...", font=("Consolas", 24), text_color="#333", anchor="center"
        )
        self.lyric_display_label.pack(fill="x", pady=(0, 5))

        # CV Setup
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # --- ADDED "7" TO MODES ---
        self.MODES = ["major", "minor", "m7", "maj7", "7"] 
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

    def parse_chord_to_sound(self, chord_name):
        match = re.match(r"^([A-G][#b]?)(.*)$", chord_name)
        if not match: return None
        root_str = match.group(1).lower()
        suffix = match.group(2)
        
        # --- IMPROVED 7 DETECTION ---
        mode = "major"
        if suffix == "m": mode = "minor"
        elif suffix == "m7": mode = "m7"
        elif suffix == "maj7": mode = "maj7"
        elif suffix == "7": mode = "7"  # Maps G7 -> mode="7"
        
        if len(root_str) > 1: root_str = root_str[0] 
        return {"label": chord_name, "root": root_str, "mode": mode}

    def load_song_json(self, filename):
        filepath = os.path.join(self.controller.lyrics_dir, filename)
        if not os.path.exists(filepath): return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.current_song_data = data
        self.current_block_index = 0
        self.is_transitioning = False
        t_time = data.get('meta', {}).get('transition_time', 1.0)
        self.transition_delay = int(t_time * 1000)

        title = data.get('meta', {}).get('title', 'Unknown')
        self.title_label.configure(text=f"Playing: {title}")
        
        chords_used = data.get('meta', {}).get('chords_used', [])
        self.active_song_chords = []
        for chord in chords_used:
            parsed = self.parse_chord_to_sound(chord)
            if parsed:
                self.active_song_chords.append(parsed)
        
        if not self.active_song_chords:
            self.active_song_chords.append({"label": "No Chords", "root": "c", "mode": "major"})

        self.chord_display_label.configure(text_color="#FF4500")
        self.update_lyric_display()

    def format_chord_string(self, chords_dict, text_length):
        buffer = [" "] * max(text_length, 40)
        sorted_indices = sorted([int(k) for k in chords_dict.keys()])
        self.required_sequence = [chords_dict[str(k)] for k in sorted_indices]
        self.current_sequence_progress = 0 
        
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
            
            if not self.required_sequence:
                self.trigger_auto_transition()
        else:
            self.lyric_display_label.configure(text="Finished!")
            self.chord_display_label.configure(text="")
            self.required_sequence = []

    def check_chord_progression(self, played_chord_label):
        if self.is_transitioning or not self.required_sequence: return
        if self.current_sequence_progress < len(self.required_sequence):
            expected_chord = self.required_sequence[self.current_sequence_progress]
            if played_chord_label == expected_chord:
                self.current_sequence_progress += 1
                if self.current_sequence_progress >= len(self.required_sequence):
                    self.trigger_auto_transition()

    def trigger_auto_transition(self):
        self.is_transitioning = True
        self.chord_display_label.configure(text_color="#32CD32")
        self.after(self.transition_delay, self.advance_line)

    def advance_line(self):
        if self.current_song_data and self.current_block_index < len(self.current_song_data['lyrics']) - 1:
            self.current_block_index += 1
            self.chord_display_label.configure(text_color="#FF4500") 
            self.update_lyric_display()
            self.is_transitioning = False
        else:
            self.lyric_display_label.configure(text="Finished!")
            self.chord_display_label.configure(text="")

    def start_camera(self):
        if not self.is_running:
            self.cap = cv2.VideoCapture(0)
            self.is_running = True
            self.prev_left_wrist = None
            self.prev_right_wrist = None
            self.update_frame()

    def stop_camera(self):
        self.is_running = False
        if self.cap: self.cap.release()
        self.cam_label.configure(image=None)

    def go_back(self):
        self.stop_camera()
        self.controller.show_frame("SongSelectionPage")

    def draw_centered_text(self, img, text, center_x, center_y, font, scale, color, thickness):
        text_size, _ = cv2.getTextSize(text, font, scale, thickness)
        text_w, text_h = text_size
        x = int(center_x - text_w // 2)
        y = int(center_y + text_h // 2)
        cv2.putText(img, text, (x, y), font, scale, color, thickness)

    def smooth_coordinates(self, current, previous):
        if previous is None: return current
        x = self.SMOOTHING_FACTOR * current[0] + (1 - self.SMOOTHING_FACTOR) * previous[0]
        y = self.SMOOTHING_FACTOR * current[1] + (1 - self.SMOOTHING_FACTOR) * previous[1]
        return [x, y]

    def update_frame(self):
        if not self.is_running: return
        ret, frame = self.cap.read()
        if not ret:
            self.after(10, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        
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

        NECK_Y_START = int(h * 0.4)
        NECK_HEIGHT = int(h * 0.25)
        NECK_X_START = int(w * 0.05)
        NECK_WIDTH = int(w * 0.55)
        STRUM_Y = int(h * 0.5)

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        
        # --- DRAW FRETBOARD (UNIFORM SIZING) ---
        cv2.rectangle(frame, (NECK_X_START, NECK_Y_START), (NECK_X_START + NECK_WIDTH, NECK_Y_START + NECK_HEIGHT), (240, 240, 240), -1) 
        cv2.rectangle(frame, (NECK_X_START, NECK_Y_START), (NECK_X_START + NECK_WIDTH, NECK_Y_START + NECK_HEIGHT), (50, 50, 50), 2) 
        
        num_chords = len(self.active_song_chords)
        
        # --- NEW LOGIC: UNIFORM WIDTH ---
        # Instead of dividing total width by num_chords, we use a FIXED width
        # similar to the free play mode (e.g. ~1/7th of total width)
        FIXED_ZONE_WIDTH = int(NECK_WIDTH / 7) # Standard size based on 7 notes
        
        # Calculate Total Width of active chords area
        total_active_width = num_chords * FIXED_ZONE_WIDTH
        
        # Center the active area
        active_start_x = NECK_X_START + (NECK_WIDTH - total_active_width) // 2
        
        for i in range(num_chords):
            bx = int(active_start_x + (i * FIXED_ZONE_WIDTH))
            
            # Draw Divider (Skip first one)
            if i > 0: 
                cv2.line(frame, (bx, NECK_Y_START), (bx, NECK_Y_START + NECK_HEIGHT), (100, 100, 100), 2)
            
            chord_label = self.active_song_chords[i]['label']
            center_x = bx + FIXED_ZONE_WIDTH/2
            center_y = NECK_Y_START + NECK_HEIGHT/2
            self.draw_centered_text(frame, chord_label, center_x, center_y, cv2.FONT_HERSHEY_SIMPLEX, 1.2, (10, 10, 10), 3)

        s_start = int(w * 0.7)
        cv2.line(frame, (s_start, STRUM_Y), (w, STRUM_Y), (0, 0, 255), 5)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            raw_left = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x * w, landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y * h]
            raw_right = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x * w, landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y * h]

            p_left_wrist = self.smooth_coordinates(raw_left, self.prev_left_wrist)
            p_right_wrist = self.smooth_coordinates(raw_right, self.prev_right_wrist)
            self.prev_left_wrist = p_left_wrist
            self.prev_right_wrist = p_right_wrist

            # Selection Logic (Updated for Uniform Width)
            current_chord_idx = -1
            if num_chords > 0 and (NECK_Y_START - 50) < p_left_wrist[1] < (NECK_Y_START + NECK_HEIGHT + 50):
                # Calculate relative to the CENTERED start position
                rel_x = p_left_wrist[0] - active_start_x
                if 0 <= rel_x <= total_active_width:
                    current_chord_idx = int(rel_x // FIXED_ZONE_WIDTH)
                    if current_chord_idx >= num_chords: current_chord_idx = num_chords - 1

            if current_chord_idx != -1:
                active_x = int(active_start_x + (current_chord_idx * FIXED_ZONE_WIDTH))
                overlay = frame.copy()
                cv2.rectangle(overlay, (active_x, NECK_Y_START), (int(active_x + FIXED_ZONE_WIDTH), NECK_Y_START + NECK_HEIGHT), (0, 255, 255), -1)
                cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

            # Strumming
            if p_right_wrist[0] > s_start:
                if p_right_wrist[1] > STRUM_Y: 
                    if self.sound_val == 0:
                        self.sound_val = 1
                        if current_chord_idx != -1:
                            chord_data = self.active_song_chords[current_chord_idx]
                            self.check_chord_progression(chord_data['label'])
                            
                            root = chord_data['root']
                            mode = chord_data['mode']
                            if mode in self.sounds and root in self.sounds[mode]:
                                self.sounds[mode][root].play()
                elif p_right_wrist[1] < STRUM_Y:
                    self.sound_val = 0
            
            cv2.circle(frame, (int(p_right_wrist[0]), int(p_right_wrist[1])), 18, (0, 0, 255), -1)
            cv2.circle(frame, (int(p_left_wrist[0]), int(p_left_wrist[1])), 18, (0, 255, 0), -1)

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ctk.CTkImage(light_image=img, size=(target_w, target_h))
        self.cam_label.configure(image=imgtk)

        self.after(10, self.update_frame)