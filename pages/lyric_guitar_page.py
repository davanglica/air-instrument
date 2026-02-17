import customtkinter as ctk
import os
import cv2
import mediapipe as mp
import pygame
import json
import re
import math 
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

        # --- HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=20, pady=(10, 0))
        header_frame.pack_propagate(False)

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

        # --- LYRICS PANEL ---
        self.lyrics_frame = ctk.CTkFrame(self, fg_color="#FFF0E0", height=100)
        self.lyrics_frame.pack(side="bottom", fill="x", padx=20, pady=(0, 10))
        self.lyrics_frame.pack_propagate(False)
        
        self.text_container = ctk.CTkFrame(self.lyrics_frame, fg_color="transparent")
        self.text_container.pack(fill="both", expand=True)

        self.chord_display_label = ctk.CTkLabel(
            self.text_container, text="", font=("Consolas", 20, "bold"), text_color="#FF4500", anchor="center"
        )
        self.chord_display_label.pack(fill="x", pady=(0, 0))

        self.lyric_display_label = ctk.CTkLabel(
            self.text_container, text="Ready...", font=("Consolas", 18), text_color="#333", anchor="center"
        )
        self.lyric_display_label.pack(fill="x", pady=(0, 0))

        # --- CAMERA ---
        self.cam_container = ctk.CTkFrame(self, fg_color="black", corner_radius=0) 
        self.cam_container.pack(side="top", fill="both", expand=True, padx=0, pady=(5, 5))

        self.cam_label = ctk.CTkLabel(self.cam_container, text="", corner_radius=0)
        self.cam_label.pack(fill="both", expand=True, padx=0, pady=0)

        # CV Setup
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
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
        
        mode = "major"
        if suffix == "m": mode = "minor"
        elif suffix == "m7": mode = "m7"
        elif suffix == "maj7": mode = "maj7"
        elif suffix == "7": mode = "7"
        
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
        self.title_label.configure(text=f"演奏モード: {title}")
        
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
        buffer_len = max(text_length + 5, 50)
        buffer = [" "] * buffer_len
        sorted_indices = sorted([int(k) for k in chords_dict.keys()])
        self.required_sequence = [chords_dict[str(k)] for k in sorted_indices]
        self.current_sequence_progress = 0 
        for idx_str, chord_name in chords_dict.items():
            idx = int(idx_str)
            if idx < buffer_len:
                for i, char in enumerate(chord_name):
                    if idx + i < buffer_len: buffer[idx + i] = char
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
            if not self.required_sequence: self.trigger_auto_transition()
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
        
        # Center Crop
        scale = max(target_w / w_orig, target_h / h_orig) 
        new_w = int(w_orig * scale)
        new_h = int(h_orig * scale)
        resized_frame = cv2.resize(frame, (new_w, new_h))
        x_start = (new_w - target_w) // 2
        y_start = (new_h - target_h) // 2
        frame = resized_frame[y_start:y_start+target_h, x_start:x_start+target_w]
        
        h, w, c = frame.shape 

        # --- GRID LOGIC ---
        num_chords = len(self.active_song_chords)
        
        # Limit before wrapping
        MAX_PER_ROW = 4 
        
        # Determine Rows (1 or 2)
        if num_chords > MAX_PER_ROW:
            rows = 2
            chords_per_row = math.ceil(num_chords / 2) 
        else:
            rows = 1
            chords_per_row = num_chords

        # --- FIX: THICKER BOXES ---
        # Increased from 0.15 to 0.22 (22% of screen height)
        BOX_H = int(h * 0.30)
        
        # Calculate Y Start to be centered around Strum Line (0.5)
        TOTAL_GRID_HEIGHT = rows * BOX_H
        STRUM_Y = int(h * 0.5)
        GRID_START_Y = int(STRUM_Y - (TOTAL_GRID_HEIGHT / 2))

        # Fixed Width per box (based on available width on left side)
        AVAILABLE_W = int(w * 0.65)
        
        if chords_per_row > 0:
            BOX_W = int(AVAILABLE_W / chords_per_row)
            # Cap max width so they don't look huge if there's only 1 chord
            MAX_BOX_W = int(w / 6)
            if BOX_W > MAX_BOX_W: BOX_W = MAX_BOX_W
        else:
            BOX_W = int(w / 6)

        GRID_START_X = int(w * 0.05) # 5% Left Margin

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        
        # --- DRAW CHORDS ---
        chord_rects = [] # Store coords for collision detection
        
        for i in range(num_chords):
            row = i // chords_per_row
            col = i % chords_per_row
            
            bx = GRID_START_X + (col * BOX_W)
            by = GRID_START_Y + (row * BOX_H)
            
            cv2.rectangle(frame, (bx, by), (bx + BOX_W, by + BOX_H), (240, 240, 240), -1)
            cv2.rectangle(frame, (bx, by), (bx + BOX_W, by + BOX_H), (50, 50, 50), 2)
            
            chord_label = self.active_song_chords[i]['label']
            center_x = bx + BOX_W/2
            center_y = by + BOX_H/2
            self.draw_centered_text(frame, chord_label, center_x, center_y, cv2.FONT_HERSHEY_SIMPLEX, 1.2, (10, 10, 10), 3)
            
            chord_rects.append({'x': bx, 'y': by, 'w': BOX_W, 'h': BOX_H, 'idx': i})

        # Draw Strum Line (Red)
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

            # Selection
            current_chord_idx = -1
            
            for box in chord_rects:
                if (box['x'] < p_left_wrist[0] < box['x'] + box['w']) and \
                   (box['y'] < p_left_wrist[1] < box['y'] + box['h']):
                    current_chord_idx = box['idx']
                    
                    # Highlight active
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (box['x'], box['y']), (box['x'] + box['w'], box['y'] + box['h']), (0, 255, 255), -1)
                    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
                    break

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