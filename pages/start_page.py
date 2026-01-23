import customtkinter as ctk

class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")
        
        self.label = ctk.CTkLabel(self, text="どこでも楽器", text_color="#D2691E", font=("HG丸ｺﾞｼｯｸM-PRO", 80, "bold"))
        self.label.pack(expand=True)

        self.start_btn = ctk.CTkButton(
            self, text="画面をタッチしてスタート", fg_color="transparent", text_color="#D2691E",
            hover_color="#FFE4C4", font=("HG丸ｺﾞｼｯｸM-PRO", 20),
            command=lambda: controller.show_frame("MainMenu")
        )
        self.start_btn.pack(pady=50)