import customtkinter as ctk
from PIL import Image
import os
from tkinter import messagebox

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller

        # --- MAIN CONTENT AREA ---
        # We use a frame to hold everything except the footer
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Title
        title = ctk.CTkLabel(content_frame, text="どこでも楽器", font=("HG丸ｺﾞｼｯｸM-PRO", 32, "bold"), text_color="#F2A93B")
        title.place(relx=0.2, rely=0.15, anchor="w") 
        
        # Underline
        underline = ctk.CTkFrame(content_frame, height=3, width=220, fg_color="#F2A93B")
        underline.place(relx=0.2, rely=0.21, anchor="w")

        # --- LOAD IMAGES ---
        # Define paths
        guitar_path = os.path.join(controller.assets_dir, "music_guitar.png")
        kashi_path = os.path.join(controller.assets_dir, "music_kashi.png")
        shutdown_path = os.path.join(controller.assets_dir, "shut_down.png")
        # Ensure 'info.png' exists in your assets/images folder for the paper icon
        info_path = os.path.join(controller.assets_dir, "info.png") 

        # Load with error handling
        self.guitar_img = None
        self.kashi_img = None
        self.shutdown_img = None
        self.info_img = None

        try:
            if os.path.exists(guitar_path):
                self.guitar_img = ctk.CTkImage(light_image=Image.open(guitar_path), size=(120, 120))
            if os.path.exists(kashi_path):
                self.kashi_img = ctk.CTkImage(light_image=Image.open(kashi_path), size=(120, 120))
            if os.path.exists(shutdown_path):
                self.shutdown_img = ctk.CTkImage(light_image=Image.open(shutdown_path), size=(60, 60))
            if os.path.exists(info_path):
                self.info_img = ctk.CTkImage(light_image=Image.open(info_path), size=(24, 24))
        except Exception as e:
            print(f"Error loading images: {e}")

        # --- CENTRAL BUTTONS ---
        btn_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_container.place(relx=0.5, rely=0.5, anchor="center")

        # Play Button (Left) - Orange
        self.play_btn = ctk.CTkButton(
            btn_container, 
            text="演奏", 
            width=240, height=300, 
            corner_radius=15,
            fg_color="#FF7F50", 
            hover_color="#FF6347", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 40, "bold"),
            image=self.guitar_img, # <--- Image restored
            compound="top",
            command=lambda: controller.show_frame("AirGuitarPage") 
        )
        self.play_btn.grid(row=0, column=0, padx=30)

        # Search Button (Right) - Blue
        self.search_btn = ctk.CTkButton(
            btn_container, 
            text="歌詞・楽譜\n検索", 
            width=240, height=300, 
            corner_radius=15,
            fg_color="#89B4C4", 
            hover_color="#7097B7", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"),
            image=self.kashi_img, # <--- Image restored
            compound="top",
            command=lambda: controller.show_frame("SongSelectionPage") 
        )
        self.search_btn.grid(row=0, column=1, padx=30)

        # --- SHUTDOWN BUTTON ---
        # Positioned bottom right, above the footer
        self.shutdown_btn = ctk.CTkButton(
            content_frame,
            text="",
            image=self.shutdown_img,
            width=70, height=70,
            fg_color="transparent",
            hover_color="#FFE4C4",
            command=self.confirm_shutdown
        )
        self.shutdown_btn.place(relx=0.92, rely=0.85, anchor="center")

        # --- FOOTER BAR ---
        self.footer = ctk.CTkFrame(self, height=50, fg_color="#FAA18D", corner_radius=0)
        self.footer.pack(side="bottom", fill="x")
        
        # Prevent footer from shrinking to fit content
        self.footer.pack_propagate(False)

        # Info Button in Footer (Paper Icon)
        self.info_btn = ctk.CTkButton(
            self.footer,
            text=" デバイスについて",
            font=("HG丸ｺﾞｼｯｸM-PRO", 18, "bold"),
            text_color="#666666",
            image=self.info_img,
            fg_color="transparent",
            hover_color="#E8907C",
            height=40,
            anchor="center",
            command=lambda: controller.show_frame("AboutDevicePage")
        )
        self.info_btn.pack(expand=True)

    def confirm_shutdown(self):
        answer = messagebox.askyesno("Power Off", "Are you sure you want to shut down?")
        if answer:
            self.controller.quit_app()