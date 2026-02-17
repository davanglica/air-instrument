import customtkinter as ctk
from PIL import Image
import os

class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller

        # --- LOAD TITLE IMAGE ---
        # We look for 'main_title.png' in the assets folder defined in main.py
        title_path = os.path.join(self.controller.assets_dir, "main_title.png")
        self.title_img = None

        try:
            if os.path.exists(title_path):
                pil_img = Image.open(title_path)
                
                # Resize logic: 
                # Original: 1114x749
                # Target: ~700 width fits nicely on 1024 screen
                # Aspect Ratio = 1.48
                # New Height = 700 / 1.48 = ~472
                self.title_img = ctk.CTkImage(light_image=pil_img, size=(500, 500/1.48))
        except Exception as e:
            print(f"Error loading title image: {e}")

        # --- LAYOUT ---
        # 1. The Logo (Center)
        if self.title_img:
            self.logo_label = ctk.CTkLabel(self, text="", image=self.title_img)
            self.logo_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            # Fallback text if image is missing
            self.logo_label = ctk.CTkLabel(
                self, 
                text="どこでも楽器", 
                font=("HG丸ｺﾞｼｯｸM-PRO", 60, "bold"), 
                text_color="#F2A93B"
            )
            self.logo_label.place(relx=0.5, rely=0.45, anchor="center")

        # 2. "Tap to Start" Prompt (Bottom)
        self.prompt_label = ctk.CTkLabel(
            self, 
            text="画面をタッチしてスタート", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 18, "bold"), 
            text_color="#D66048"
        )
        self.prompt_label.place(relx=0.5, rely=0.9, anchor="center")

        # --- CLICK EVENT ---
        # Bind the click to the entire frame and labels so touching anywhere works
        self.bind("<Button-1>", self.go_to_menu)
        self.logo_label.bind("<Button-1>", self.go_to_menu)
        self.prompt_label.bind("<Button-1>", self.go_to_menu)

    def go_to_menu(self, event):
        self.controller.show_frame("MainMenu")