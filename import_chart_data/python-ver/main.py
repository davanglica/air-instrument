import time
import tkinter as tk
from tkinter import font

from read_chart import parse_chart_text
from get_time_from_chart import build_timeline


class LyricsGUI:
    def __init__(self, root, lyrics_events):
        self.root = root
        self.root.title("Lyrics Viewer")
        self.root.geometry("800x450")

        self.lyrics_events = lyrics_events
        self.start_time = time.time()

        # 上部（将来拡張用）
        self.main_frame = tk.Frame(root, bg="black")
        self.main_frame.pack(fill="both", expand=True)

        # 下部（歌詞表示）
        self.lyrics_frame = tk.Frame(root, bg="gray20", height=90)
        self.lyrics_frame.pack(side="bottom", fill="x")
        self.lyrics_frame.pack_propagate(False)

        self.lyrics_font = font.Font(size=22, weight="bold")

        self.label = tk.Label(
            self.lyrics_frame,
            text="",
            fg="white",
            bg="gray20",
            font=self.lyrics_font,
            anchor="center",
            wraplength=760
        )
        self.label.pack(fill="both", expand=True)

        self.update()

    def update(self):
        now = time.time() - self.start_time

        for e in reversed(self.lyrics_events):
            if now >= e["time"]:
                self.label.config(text=e["text"])
                break

        self.root.after(30, self.update)


def build_lyrics_events(parsed):
    meta = parsed["meta"]
    events = parsed["events"]

    default_bpm = meta.get("bpm", 120)
    default_ts = {"numerator": 4, "denominator": 4}

    bpm_changes = events.get("bpmChanges", [])
    ts_changes = events.get("timeSignatures", [])

    # 歌詞・BPM・拍子を含めた最大小節数を取得
    max_measure = 1
    for e in events.get("lyrics", []):
        max_measure = max(max_measure, e["measure"])
    for e in bpm_changes + ts_changes:
        max_measure = max(max_measure, e["measure"])

    # ★ 正しいタイムライン生成
    timeline = build_timeline(
        max_measure,
        default_bpm,
        default_ts,
        bpm_changes,
        ts_changes
    )

    lyrics_events = []
    for e in events.get("lyrics", []):
        m = e["measure"]
        lyrics_events.append({
            "time": timeline["cumTime"][m],
            "text": e["text"]
        })

    return sorted(lyrics_events, key=lambda x: x["time"])


if __name__ == "__main__":
    with open("test.txt", encoding="utf-8") as f:
        text = f.read()

    parsed = parse_chart_text(text)

    lyrics_events = build_lyrics_events(parsed)

    root = tk.Tk()
    app = LyricsGUI(root, lyrics_events)
    root.mainloop()
