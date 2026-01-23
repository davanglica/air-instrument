import customtkinter as ctk
import os
import json
from PIL import Image

class SongSelectionPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller

        # --- HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        # 1. Load Arrow Image
        arrow_path = os.path.join(self.controller.assets_dir, "arrow.png")
        try:
            # Resize 500x500 -> 40x40 for the button
            arrow_img = ctk.CTkImage(light_image=Image.open(arrow_path), size=(40, 40))
        except:
            print("Error: arrow.png not found")
            arrow_img = None

        # 2. Back Button (Icon Style)
        self.back_btn = ctk.CTkButton(
            header_frame, 
            text="",                # No text
            image=arrow_img,        # Arrow Icon
            width=50, height=50, 
            fg_color="transparent", # Transparent background
            hover_color="#FFE4C4",  # Light hover effect
            command=lambda: controller.show_frame("MainMenu")
        )
        self.back_btn.pack(side="left")

        title = ctk.CTkLabel(header_frame, text="曲を選択してください", font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"), text_color="#D2691E")
        title.pack(side="left", padx=20)

        # --- LIST AREA ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=20)

        self.load_song_list()

    def load_song_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.controller.lyrics_dir):
            return

        files = [f for f in os.listdir(self.controller.lyrics_dir) if f.endswith(".json")]
        if not files:
            ctk.CTkLabel(self.scroll_frame, text="No songs found.", text_color="#555").pack()
            return

        for filename in files:
            path = os.path.join(self.controller.lyrics_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('meta', {})
                    title = meta.get('title', filename)
                    artist = meta.get('artist', 'Unknown')
                    
                    btn_text = f"{title}\n{artist}"
                    btn = ctk.CTkButton(
                        self.scroll_frame,
                        text=btn_text,
                        font=("HG丸ｺﾞｼｯｸM-PRO", 20),
                        height=80,
                        fg_color="white",
                        text_color="black",
                        hover_color="#FFE4C4",
                        border_color="#D2691E",
                        border_width=2,
                        command=lambda f=filename: self.select_song(f)
                    )
                    btn.pack(fill="x", pady=10)
            except:
                pass

    def select_song(self, filename):
        self.controller.frames["LyricGuitarPage"].load_song_json(filename)
        self.controller.show_frame("LyricGuitarPage")