import customtkinter as ctk
from PIL import Image
import os
from tkinter import simpledialog

class AboutDevicePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller

        # --- MAIN CONTENT ---
        # Title (Top Left)
        title = ctk.CTkLabel(self, text="どこでも楽器", font=("HG丸ｺﾞｼｯｸM-PRO", 32, "bold"), text_color="#F2A93B")
        title.place(relx=0.1, rely=0.15, anchor="w")
        underline = ctk.CTkFrame(self, height=3, width=220, fg_color="#F2A93B")
        underline.place(relx=0.1, rely=0.21, anchor="w")

        # Subtitle (Center)
        subtitle = ctk.CTkLabel(self, text="デバイスについて", font=("HG丸ｺﾞｼｯｸM-PRO", 28, "bold"), text_color="#FA8072") # Salmon color
        subtitle.place(relx=0.5, rely=0.3, anchor="center")

        # Body Text (Center)
        body_text = ctk.CTkLabel(
            self, 
            text="text here for later", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 24, "bold"), 
            text_color="#FA8072"
        )
        body_text.place(relx=0.5, rely=0.5, anchor="center")

        # --- FEATURE 3: SECRET DOOR ---
        door_path = os.path.join(controller.assets_dir, "door.png")
        try:
            door_img = ctk.CTkImage(light_image=Image.open(door_path), size=(60, 100))
        except:
            door_img = None

        self.door_btn = ctk.CTkButton(
            self,
            text="",
            image=door_img,
            width=70, height=110,
            fg_color="transparent",
            hover_color="#FFE4C4",
            command=self.prompt_admin_password
        )
        self.door_btn.place(relx=0.9, rely=0.85, anchor="center")

        # Back Button (To return to main menu)
        # Using the same arrow style as other pages
        arrow_path = os.path.join(controller.assets_dir, "arrow.png")
        try:
            arrow_img = ctk.CTkImage(light_image=Image.open(arrow_path), size=(40, 40))
        except:
            arrow_img = None
            
        self.back_btn = ctk.CTkButton(
            self, text="", image=arrow_img, width=50, height=50, 
            fg_color="transparent", hover_color="#FFE4C4",
            command=lambda: controller.show_frame("MainMenu")
        )
        self.back_btn.place(relx=0.05, rely=0.05, anchor="nw")

    def prompt_admin_password(self):
        # Create a custom dialog or use simpledialog
        password = ctk.CTkInputDialog(text="Enter Admin Password:", title="Admin Access").get_input()
        
        if password == "1111":
            # Correct Password -> Shut Down
            self.controller.quit_app()
        elif password is not None:
            # Wrong Password (ignore cancel)
            print("Wrong password entered")