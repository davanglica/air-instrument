import customtkinter as ctk
from PIL import Image

class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("どこでも楽器")
        self.geometry("900x550")
        
        # 外観モード（ライトモード固定）
        ctk.set_appearance_mode("light")

        # メインコンテナ
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, MainMenu):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0") # 背景色

        # タイトルロゴ（フォントを太く、大きく）
        self.label = ctk.CTkLabel(
            self, text="どこでも楽器", 
            text_color="#D2691E", 
            font=("HG丸ｺﾞｼｯｸM-PRO", 80, "bold")
        )
        self.label.pack(expand=True)

        # スタートボタン
        self.start_btn = ctk.CTkButton(
            self, text="画面をタッチしてスタート", 
            fg_color="transparent", 
            text_color="#D2691E",
            hover_color="#FFE4C4",
            font=("HG丸ｺﾞｼｯｸM-PRO", 20),
            command=lambda: controller.show_frame("MainMenu")
        )
        self.start_btn.pack(pady=50)

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFF0E0")

        # --- ヘッダー ---
        title = ctk.CTkLabel(self, text="どこでも楽器", font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"), text_color="#D2691E")
        title.pack(pady=20)

        # --- ボタンエリア ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(expand=True)

        # 楽器アイコン
        guitar_img = ctk.CTkImage(light_image=Image.open("music_guitar.png"), size=(100, 100))
        kashi_img = ctk.CTkImage(light_image=Image.open("music_kashi.png"), size=(100, 100))
        # 演奏ボタン
        self.play_btn = ctk.CTkButton(
            btn_frame, 
            text="演奏", 
            width=250, height=350,
            corner_radius=20,
            fg_color="#FF7F50", # 色変更
            hover_color="#FF6347",
            font=("HG丸ｺﾞｼｯｸM-PRO", 40, "bold"),
            image=guitar_img, # 画像
            compound="top"
        )
        self.play_btn.grid(row=0, column=0, padx=30)

        # 検索ボタン
        self.search_btn = ctk.CTkButton(
            btn_frame, 
            text="歌詞・楽譜\n検索", 
            width=250, height=350,
            corner_radius=20,
            fg_color="#4169E1", # 色変更
            hover_color="#7097B7",
            font=("HG丸ｺﾞｼｯｸM-PRO", 30, "bold"),
            image=kashi_img, # 画像
            compound="top"
        )
        self.search_btn.grid(row=0, column=1, padx=30)

if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()