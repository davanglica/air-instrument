import customtkinter as ctk
from PIL import Image
import os
from tkinter import messagebox

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller

        # --- MAIN CONTENT AREA ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Title (No Underline)
        # Positioned at relx=0.25 to match the left-aligned look in your reference
        title = ctk.CTkLabel(
            content_frame, 
            text="どこでも楽器", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 46, "bold"), 
            text_color="#F2A93B"
        )
        title.place(relx=0.27, rely=0.15, anchor="center") 
        
        # REMOVED: underline frame

        # --- LOAD IMAGES ---
        guitar_path = os.path.join(controller.assets_dir, "music_guitar.png")
        kashi_path = os.path.join(controller.assets_dir, "music_kashi.png")
        shutdown_path = os.path.join(controller.assets_dir, "shut_down.png")
        info_path = os.path.join(controller.assets_dir, "info.png")

        self.guitar_img = None
        self.kashi_img = None
        self.shutdown_img = None
        self.info_img = None

        try:
            if os.path.exists(guitar_path): self.guitar_img = ctk.CTkImage(light_image=Image.open(guitar_path), size=(130, 130))
            if os.path.exists(kashi_path): self.kashi_img = ctk.CTkImage(light_image=Image.open(kashi_path), size=(130, 130))
            if os.path.exists(shutdown_path): self.shutdown_img = ctk.CTkImage(light_image=Image.open(shutdown_path), size=(60, 60))
            if os.path.exists(info_path): self.info_img = ctk.CTkImage(light_image=Image.open(info_path), size=(30, 30)) 
        except Exception as e:
            print(f"Error loading images: {e}")

        # --- CENTRAL BUTTONS ---
        # LOWERED: Changed rely from 0.55 to 0.60 to move them down
        
        # Play Button (Tall Rectangle)
        self.play_btn = ctk.CTkButton(
            content_frame, 
            text="演奏", 
            width=260, height=340, 
            corner_radius=40,
            bg_color="transparent",
            fg_color="#D66048",     
            hover_color="#C05038", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 40, "bold"),
            image=self.guitar_img, 
            compound="top",
            command=lambda: controller.show_frame("AirGuitarPage") 
        )
        self.play_btn.place(relx=0.33, rely=0.60, anchor="center")

        # Search Button (Tall Rectangle)
        self.search_btn = ctk.CTkButton(
            content_frame, 
            text="曲を選ぶ", 
            width=260, height=340, 
            corner_radius=40,
            bg_color="transparent",
            fg_color="#3B9AB2",     
            hover_color="#2A8095", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 32, "bold"),
            image=self.kashi_img, 
            compound="top",
            command=lambda: controller.show_frame("SongSelectionPage") 
        )
        self.search_btn.place(relx=0.67, rely=0.60, anchor="center")

        # --- SHUTDOWN BUTTON ---
        self.shutdown_btn = ctk.CTkButton(
            content_frame, 
            text="", 
            image=self.shutdown_img, 
            width=70, height=70,
            fg_color="transparent", 
            hover_color="#FFE4C4", 
            bg_color="transparent", 
            command=self.confirm_shutdown
        )
        self.shutdown_btn.place(relx=0.92, rely=0.88, anchor="center")

        # --- FOOTER BAR ---
        self.footer = ctk.CTkFrame(self, height=50, fg_color="#E08E79", corner_radius=0) 
        self.footer.pack(side="bottom", fill="x")
        self.footer.pack_propagate(False)

        # Info Button
        self.info_btn = ctk.CTkButton(
            self.footer, text=" デバイスについて", font=("HG丸ｺﾞｼｯｸM-PRO", 18, "bold"),
            text_color="#555555", image=self.info_img, fg_color="transparent",
            hover_color="#D07E69", height=40, anchor="center",
            bg_color="transparent",
            command=lambda: controller.show_frame("AboutDevicePage")
        )
        self.info_btn.pack(expand=True)

    def confirm_shutdown(self):
        answer = messagebox.askyesno("Power Off", "Are you sure you want to shut down?")
        if answer: self.controller.quit_app()