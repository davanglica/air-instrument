import customtkinter as ctk
import os
import pygame

from pages.start_page import StartPage
from pages.main_menu import MainMenu
from pages.air_guitar_page import AirGuitarPage
from pages.song_selection_page import SongSelectionPage
from pages.lyric_guitar_page import LyricGuitarPage
from pages.about_device_page import AboutDevicePage # <--- NEW IMPORT

class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Force Scaling for small screens
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

        self.title("どこでも楽器")
        self.geometry("1024x600")
        
        # --- FEATURE 1: FORCE FULL SCREEN ---
        self.attributes('-fullscreen', True)
        
        # Bind Escape key to exit fullscreen (Optional, useful for debugging)
        self.bind("<Escape>", lambda event: self.attributes("-fullscreen", False))

        ctk.set_appearance_mode("light")

        # --- PATH SETUP ---
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Assets (Images)
        self.assets_dir = os.path.join(self.base_dir, "assets", "images")
        if not os.path.exists(self.assets_dir):
            self.assets_dir = os.path.join(self.base_dir, "assets")

        # Audio (Air Guitar)
        self.audio_dir = os.path.join(self.base_dir, "air_guitar", "audio")

        # Lyrics
        self.lyrics_dir = os.path.join(self.base_dir, "lyrics") 
        
        pygame.mixer.init()

        # --- CONTAINER ---
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Added AboutDevicePage to the list
        for F in (StartPage, MainMenu, AirGuitarPage, SongSelectionPage, LyricGuitarPage, AboutDevicePage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        # Stop cameras if running
        if "AirGuitarPage" in self.frames:
            self.frames["AirGuitarPage"].stop_camera()
        if "LyricGuitarPage" in self.frames:
            self.frames["LyricGuitarPage"].stop_camera()

        # Start camera if needed
        if page_name == "AirGuitarPage":
            self.frames["AirGuitarPage"].start_camera()
        elif page_name == "LyricGuitarPage":
            self.frames["LyricGuitarPage"].start_camera()

        frame = self.frames[page_name]
        frame.tkraise()

    def quit_app(self):
        """Clean shutdown of the application"""
        self.destroy()

if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()