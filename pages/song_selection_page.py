import customtkinter as ctk
import os
import json
from PIL import Image

class SongSelectionPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller
        
        # State for Double-Click Logic
        self.selected_filename = None
        self.row_widgets = {} # Map filename -> frame widget

        # --- HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        arrow_path = os.path.join(self.controller.assets_dir, "arrow.png")
        try:
            arrow_img = ctk.CTkImage(light_image=Image.open(arrow_path), size=(30, 30))
        except:
            arrow_img = None

        self.back_btn = ctk.CTkButton(
            header_frame, 
            text="", 
            image=arrow_img,
            width=50, height=50, 
            fg_color="transparent", 
            hover_color="#FFE4C4", 
            command=lambda: controller.show_frame("MainMenu")
        )
        self.back_btn.pack(side="left")

        title = ctk.CTkLabel(
            header_frame, 
            text="曲を選択 (Select Song)", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 24, "bold"), 
            text_color="#D2691E"
        )
        title.pack(side="left", padx=10)

        # --- SCROLLABLE LIST ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.load_song_list()

    def load_song_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.row_widgets = {}
        self.selected_filename = None

        if not os.path.exists(self.controller.lyrics_dir):
            return

        files = [f for f in os.listdir(self.controller.lyrics_dir) if f.endswith(".json")]
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
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    def create_song_row(self, index, title, artist, filename):
        # Row Container
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=10, height=70)
        row_frame.pack(fill="x", pady=5, padx=5)
        row_frame.pack_propagate(False) 
        
        # Store ref for highlighting later
        self.row_widgets[filename] = row_frame

        # Index
        index_label = ctk.CTkLabel(row_frame, text=str(index), font=("Arial", 20), text_color="#555", width=50)
        index_label.pack(side="left", padx=(10, 0))

        # Text Info
        text_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=10)

        title_label = ctk.CTkLabel(text_frame, text=title, font=("HG丸ｺﾞｼｯｸM-PRO", 18, "bold"), text_color="black", anchor="w")
        title_label.pack(fill="x", pady=(10, 0))

        artist_label = ctk.CTkLabel(text_frame, text=artist, font=("HG丸ｺﾞｼｯｸM-PRO", 14), text_color="gray", anchor="w")
        artist_label.pack(fill="x", pady=(0, 10))

        # --- CLICK LOGIC ---
        def on_click(event):
            self.handle_row_click(filename)

        # Bind to everything
        row_frame.bind("<Button-1>", on_click)
        index_label.bind("<Button-1>", on_click)
        text_frame.bind("<Button-1>", on_click)
        title_label.bind("<Button-1>", on_click)
        artist_label.bind("<Button-1>", on_click)

    def handle_row_click(self, filename):
        # DOUBLE CLICK LOGIC
        if self.selected_filename == filename:
            # Second click -> Open
            self.controller.frames["LyricGuitarPage"].load_song_json(filename)
            self.controller.show_frame("LyricGuitarPage")
        else:
            # First click -> Highlight
            # Reset old
            if self.selected_filename and self.selected_filename in self.row_widgets:
                self.row_widgets[self.selected_filename].configure(fg_color="white")
            
            # Highlight new
            self.selected_filename = filename
            if filename in self.row_widgets:
                self.row_widgets[filename].configure(fg_color="#FFE4C4") # Highlight Color