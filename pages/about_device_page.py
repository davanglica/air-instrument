import customtkinter as ctk
from PIL import Image
import os
from tkinter import simpledialog

class AboutDevicePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller

        # --- HEADER (Text Title) ---
        # Reverted to text as requested
        title = ctk.CTkLabel(
            self, 
            text="どこでも楽器", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 32, "bold"), 
            text_color="#F2A93B"
        )
        title.place(relx=0.1, rely=0.1, anchor="w")

        # --- SUBTITLE ---
        subtitle = ctk.CTkLabel(
            self, 
            text="デバイスについて", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 28, "bold"), 
            text_color="#555555" 
        ) 
        subtitle.place(relx=0.5, rely=0.25, anchor="center")

        # --- CREDITS TEXT ---
        credits_text = (
            "R7創造設計 2班\n"
            "プロジェクトリーダー：岩田　凌旺\n\n"
            "ソフトウェア担当：\n"
            "・アンジェリカ　ダヴィナ\n"
            "・齋藤　錬太朗\n\n"
            "ハードウェア担当：\n"
            "・荒井　良斗\n"
            "・吉見　秋亮\n"
            "・生島　遊"
        )

        body_text = ctk.CTkLabel(
            self, 
            text=credits_text, 
            font=("HG丸ｺﾞｼｯｸM-PRO", 15, "bold"), 
            text_color="#555555", 
            justify="left"
        )
        body_text.place(relx=0.5, rely=0.60, anchor="center")

        # --- SECRET DOOR ---
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

        # --- BACK BUTTON ---
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
        password = simpledialog.askstring("Admin Access", "Enter Password:", parent=self)
        
        if password == "1111":
            self.controller.quit_app()
        elif password is not None:
            print("Wrong password entered")