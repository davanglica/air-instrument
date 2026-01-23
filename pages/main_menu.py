import customtkinter as ctk
from PIL import Image
import os

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")

        title = ctk.CTkLabel(self, text="どこでも楽器", font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"), text_color="#D2691E")
        title.pack(pady=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(expand=True)
        
        # Load Images
        guitar_path = os.path.join(controller.assets_dir, "music_guitar.png")
        kashi_path = os.path.join(controller.assets_dir, "music_kashi.png")

        try:
            self.guitar_img = ctk.CTkImage(light_image=Image.open(guitar_path), size=(100, 100))
            self.kashi_img = ctk.CTkImage(light_image=Image.open(kashi_path), size=(100, 100))
        except:
            self.guitar_img = None
            self.kashi_img = None

        # --- BUTTONS ---
        # FIX: Added bg_color="#FFF0E0" to both buttons
        
        self.play_btn = ctk.CTkButton(
            btn_frame, 
            text="演奏 (Free Play)", 
            width=250, height=350, 
            corner_radius=20,
            fg_color="#FF7F50", 
            bg_color="#FFF0E0",   # <--- THIS FIXES THE SQUARE CORNERS
            hover_color="#FF6347", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"),
            image=self.guitar_img,
            compound="top",
            command=lambda: controller.show_frame("AirGuitarPage") 
        )
        self.play_btn.grid(row=0, column=0, padx=30)

        self.search_btn = ctk.CTkButton(
            btn_frame, 
            text="曲を選ぶ (Guided)", 
            width=250, height=350, 
            corner_radius=20,
            fg_color="#4169E1", 
            bg_color="#FFF0E0",   # <--- THIS FIXES THE SQUARE CORNERS
            hover_color="#7097B7", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"),
            image=self.kashi_img,
            compound="top",
            command=lambda: controller.show_frame("SongSelectionPage") 
        )
        self.search_btn.grid(row=0, column=1, padx=30)