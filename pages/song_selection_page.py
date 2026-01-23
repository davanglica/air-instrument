import customtkinter as ctk
import os
import json

class SongSelectionPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        self.back_btn = ctk.CTkButton(
            header_frame, text="←", width=50, height=50, corner_radius=25,
            fg_color="#FF7F50", font=("Arial", 24, "bold"),
            command=lambda: controller.show_frame("MainMenu")
        )
        self.back_btn.pack(side="left")

        title = ctk.CTkLabel(header_frame, text="曲を選択してください", font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"), text_color="#D2691E")
        title.pack(side="left", padx=20)

        # Scrollable Area
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=20)

        # Load Songs
        self.load_song_list()

    def load_song_list(self):
        # Clear old buttons
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.controller.lyrics_dir):
            lbl = ctk.CTkLabel(self.scroll_frame, text="Lyrics folder not found!", text_color="red")
            lbl.pack()
            return

        # Find .json files
        files = [f for f in os.listdir(self.controller.lyrics_dir) if f.endswith(".json")]

        if not files:
            lbl = ctk.CTkLabel(self.scroll_frame, text="No songs found.", text_color="#555")
            lbl.pack()
            return

        for filename in files:
            path = os.path.join(self.controller.lyrics_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('meta', {})
                    title = meta.get('title', filename)
                    artist = meta.get('artist', 'Unknown')
                    
                    # Create Button
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
                        # Pass filename to selection handler
                        command=lambda f=filename: self.select_song(f)
                    )
                    btn.pack(fill="x", pady=10)
            except:
                pass

    def select_song(self, filename):
        print(f"Selected song: {filename}")
        # Load data into the Guided Page
        self.controller.frames["LyricGuitarPage"].load_song_json(filename)
        # Switch View
        self.controller.show_frame("LyricGuitarPage")