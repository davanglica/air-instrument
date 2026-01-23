import customtkinter as ctk
from PIL import Image
import os

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")

        # FIX 3: Smaller Title Font (30 -> 24)
        title = ctk.CTkLabel(self, text="どこでも楽器", font=("HG丸ｺﾞｼｯｸM-PRO", 24, "bold"), text_color="#D2691E")
        title.pack(pady=10) # Less padding

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(expand=True)
        
        # Load Images (Resize slightly smaller: 100x100 -> 80x80)
        guitar_path = os.path.join(controller.assets_dir, "music_guitar.png")
        kashi_path = os.path.join(controller.assets_dir, "music_kashi.png")

        try:
            self.guitar_img = ctk.CTkImage(light_image=Image.open(guitar_path), size=(80, 80))
            self.kashi_img = ctk.CTkImage(light_image=Image.open(kashi_path), size=(80, 80))
        except:
            self.guitar_img = None
            self.kashi_img = None

        # FIX 4: Smaller Buttons
        # Width: 250 -> 220
        # Height: 350 -> 250 (This fixes the vertical overflow)
        # Font: 40 -> 24
        
        self.play_btn = ctk.CTkButton(
            btn_frame, 
            text="演奏 (Free Play)", 
            width=220, height=250, 
            corner_radius=20,
            fg_color="#FF7F50", 
            hover_color="#FF6347", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 24, "bold"),
            image=self.guitar_img,
            compound="top",
            command=lambda: controller.show_frame("AirGuitarPage") 
        )
        self.play_btn.grid(row=0, column=0, padx=20)

        self.search_btn = ctk.CTkButton(
            btn_frame, 
            text="曲を選ぶ (Guided)", 
            width=220, height=250, 
            corner_radius=20,
            fg_color="#4169E1", 
            hover_color="#7097B7", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 24, "bold"),
            image=self.kashi_img,
            compound="top",
            command=lambda: controller.show_frame("SongSelectionPage") 
        )
        self.search_btn.grid(row=0, column=1, padx=20)