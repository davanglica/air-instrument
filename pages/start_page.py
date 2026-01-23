import customtkinter as ctk

class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        self.controller = controller
        
        # FIX 5: Reduce Title Font (80 -> 50)
        self.label = ctk.CTkLabel(
            self, text="どこでも楽器", 
            text_color="#D2691E", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 50, "bold") 
        )
        self.label.pack(expand=True)

        self.sub_label = ctk.CTkLabel(
            self, text="画面をタッチしてスタート", 
            text_color="#D2691E",
            font=("HG丸ｺﾞｼｯｸM-PRO", 18)
        )
        self.sub_label.pack(pady=30)

        self.bind("<Button-1>", self.start_app)
        self.label.bind("<Button-1>", self.start_app)
        self.sub_label.bind("<Button-1>", self.start_app)

    def start_app(self, event):
        self.controller.show_frame("MainMenu")