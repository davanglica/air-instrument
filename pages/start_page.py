import customtkinter as ctk

class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller
        
        # 1. Main Title
        self.label = ctk.CTkLabel(
            self, text="どこでも楽器", 
            text_color="#D2691E", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 80, "bold")
        )
        self.label.pack(expand=True)

        # 2. Instruction Text (Label, not a button)
        self.sub_label = ctk.CTkLabel(
            self, text="画面をタッチしてスタート", 
            text_color="#D2691E",
            font=("HG丸ｺﾞｼｯｸM-PRO", 20)
        )
        self.sub_label.pack(pady=50)

        # 3. MAKE EVERYTHING CLICKABLE
        # Bind the click event to the Frame (background)
        self.bind("<Button-1>", self.start_app)
        # Bind the click event to the Labels (text)
        self.label.bind("<Button-1>", self.start_app)
        self.sub_label.bind("<Button-1>", self.start_app)

    def start_app(self, event):
        self.controller.show_frame("MainMenu")