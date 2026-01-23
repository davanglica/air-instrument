import customtkinter as ctk
import os
import pygame

from pages.start_page import StartPage
from pages.main_menu import MainMenu
from pages.air_guitar_page import AirGuitarPage
from pages.song_selection_page import SongSelectionPage
from pages.lyric_guitar_page import LyricGuitarPage

class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- FIX 1: FORCE SCALING TO 100% ---
        # This prevents the "huge font" issue on small screens
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

        self.title("どこでも楽器")
        
        # --- FIX 2: MATCH SCREEN RESOLUTION ---
        # 1024x600 is your exact screen size
        self.geometry("1024x600")
        
        # Optional: Uncomment this if you want to force full screen without window bars
        # self.attributes('-fullscreen', True) 

        ctk.set_appearance_mode("light")

        # --- PATH SETUP ---
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.base_dir, "assets", "images")
        self.audio_dir = os.path.join(self.base_dir, "air_guitar", "audio")
        self.lyrics_dir = os.path.join(self.base_dir, "search-function", "lyrics")
        
        pygame.mixer.init()

        # --- CONTAINER ---
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, MainMenu, AirGuitarPage, SongSelectionPage, LyricGuitarPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        if "AirGuitarPage" in self.frames:
            self.frames["AirGuitarPage"].stop_camera()
        if "LyricGuitarPage" in self.frames:
            self.frames["LyricGuitarPage"].stop_camera()

        if page_name == "AirGuitarPage":
            self.frames["AirGuitarPage"].start_camera()
        elif page_name == "LyricGuitarPage":
            self.frames["LyricGuitarPage"].start_camera()

        frame = self.frames[page_name]
        frame.tkraise()

if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()