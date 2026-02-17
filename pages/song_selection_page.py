import customtkinter as ctk
import os
import json
from PIL import Image

class SongSelectionPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller
        
        self.selected_filename = None
        self.row_widgets = {}
        self.is_navigating = False 

        # --- SCROLL STATE ---
        self.drag_start_y = 0
        self.start_fraction = 0.0
        self.is_scrolling = False
        self.scroll_locked = False # New Lock Flag

        # --- HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        arrow_path = os.path.join(self.controller.assets_dir, "arrow.png")
        try:
            arrow_img = ctk.CTkImage(light_image=Image.open(arrow_path), size=(30, 30))
        except:
            arrow_img = None

        self.back_btn = ctk.CTkButton(
            header_frame, text="", image=arrow_img, width=50, height=50, 
            fg_color="transparent", hover_color="#FFE4C4", 
            command=lambda: controller.show_frame("MainMenu")
        )
        self.back_btn.pack(side="left")

        title = ctk.CTkLabel(header_frame, text="曲を選択", font=("HG丸ｺﾞｼｯｸM-PRO", 28, "bold"), text_color="#D2691E")
        title.pack(side="left", padx=10)

        # --- LIST ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Access the underlying Canvas
        self.canvas = self.scroll_frame._parent_canvas

        self.load_song_list()

    def load_song_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.row_widgets = {}
        self.selected_filename = None
        self.is_navigating = False
        self.scroll_locked = False

        if not os.path.exists(self.controller.lyrics_dir): return

        files = [f for f in os.listdir(self.controller.lyrics_dir) if f.endswith(".json")]
        
        pinned_song = "Twinkle_Twinkle_Little_Star.json" 
        if pinned_song in files:
            files.remove(pinned_song) 
            files.insert(0, pinned_song) 

        if not files:
            ctk.CTkLabel(self.scroll_frame, text="No songs found.", text_color="#555").pack()
            return

        for i, filename in enumerate(files):
            path = os.path.join(self.controller.lyrics_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('meta', {})
                    song_title = meta.get('title', filename.replace(".json", ""))
                    artist_name = meta.get('artist', 'Unknown Artist')
                    self.create_song_row(i + 1, song_title, artist_name, filename)
            except: pass

    def create_song_row(self, index, title, artist, filename):
        # Frame with takefocus=False to prevent auto-scroll jumps
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=10, height=110)
        row_frame.pack(fill="x", pady=6, padx=5)
        row_frame.pack_propagate(False) 
        
        self.row_widgets[filename] = row_frame

        # Index
        index_label = ctk.CTkLabel(row_frame, text=str(index), font=("Arial", 24), text_color="#555", width=60)
        index_label.pack(side="left", padx=(10, 0))

        # Text Info
        text_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=10)

        title_label = ctk.CTkLabel(text_frame, text=title, font=("HG丸ｺﾞｼｯｸM-PRO", 22, "bold"), text_color="black", anchor="w")
        title_label.pack(fill="x", pady=(12, 0))

        artist_label = ctk.CTkLabel(text_frame, text=artist, font=("HG丸ｺﾞｼｯｸM-PRO", 16), text_color="gray", anchor="w")
        artist_label.pack(fill="x", pady=(0, 12))

        # --- BINDINGS ---
        elements = [row_frame, index_label, text_frame, title_label, artist_label]
        
        for element in elements:
            element.bind("<Button-1>", lambda e: self.on_touch_start(e))
            element.bind("<B1-Motion>", lambda e: self.on_touch_drag(e))
            element.bind("<ButtonRelease-1>", lambda e, fn=filename: self.on_touch_release(e, fn))

    def on_touch_start(self, event):
        # If locked (selection in progress), ignore everything
        if self.scroll_locked: return

        self.drag_start_y = event.y_root
        self.is_scrolling = False
        self.start_fraction = self.canvas.yview()[0]

    def on_touch_drag(self, event):
        # If locked, DO NOT SCROLL
        if self.scroll_locked: return

        pixel_delta = self.drag_start_y - event.y_root
        
        if abs(pixel_delta) > 5:
            self.is_scrolling = True
            bbox = self.canvas.bbox("all")
            if not bbox: return
            content_height = bbox[3]
            if content_height < 1: content_height = 1

            fraction_delta = pixel_delta / content_height
            new_pos = self.start_fraction + fraction_delta
            
            # Clamp value
            if new_pos < 0: new_pos = 0
            if new_pos > 1: new_pos = 1
            
            self.canvas.yview_moveto(new_pos)

    def on_touch_release(self, event, filename):
        if self.scroll_locked: return
        if not self.is_scrolling:
            self.handle_row_click(filename)

    def handle_row_click(self, filename):
        if self.is_navigating: return

        self.is_navigating = True
        self.scroll_locked = True # LOCK SCROLLING INSTANTLY
        
        # 1. Reset previous
        if self.selected_filename and self.selected_filename in self.row_widgets:
            self.row_widgets[self.selected_filename].configure(fg_color="white")
        
        # 2. Highlight new
        self.selected_filename = filename
        if filename in self.row_widgets:
            self.row_widgets[filename].configure(fg_color="#F2A93B")
        
        # 3. Wait and Transition
        self.after(1000, lambda: self.transition_to_song(filename))

    def transition_to_song(self, filename):
        self.controller.frames["LyricGuitarPage"].load_song_json(filename)
        self.controller.show_frame("LyricGuitarPage")
        
        # Reset states
        self.is_navigating = False
        self.scroll_locked = False