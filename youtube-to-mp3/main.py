import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pytube import YouTube
import moviepy.editor as mp
import os
import re

# --- Core Functions ---

def sanitize_filename(title):
    """Removes invalid characters from a string to make it a valid filename."""
    return re.sub(r'[\\/*?:"<>|]', "", title)

def download_and_convert(url, output_path, status_var, progress_bar):
    """
    Downloads a YouTube video, converts it to MP3, and updates the GUI.
    This function is designed to be run in a separate thread to keep the GUI responsive.
    """
    try:
        # 1. Update status and reset progress bar
        status_var.set("Connecting to YouTube...")
        progress_bar['value'] = 0
        
        # 2. Get YouTube video details
        yt = YouTube(url)
        status_var.set(f"Fetching audio for: {yt.title}")
        
        # 3. Download the best audio-only stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        if not audio_stream:
            raise ValueError("No audio-only stream found for this video.")
            
        status_var.set("Downloading audio stream...")
        # Note: Pytube doesn't have a reliable progress hook for direct download to a file.
        # We will simulate progress during the download and conversion phases.
        progress_bar['value'] = 25
        
        downloaded_file = audio_stream.download(output_path=output_path)
        base, ext = os.path.splitext(downloaded_file)
        progress_bar['value'] = 50

        # 4. Convert the downloaded file to MP3
        status_var.set("Converting to MP3...")
        sanitized_title = sanitize_filename(yt.title)
        mp3_file_path = os.path.join(output_path, f"{sanitized_title}.mp3")

        video_clip = mp.AudioFileClip(downloaded_file)
        video_clip.write_audiofile(mp3_file_path)
        video_clip.close()
        
        progress_bar['value'] = 90
        
        # 5. Clean up the original downloaded file
        os.remove(downloaded_file)
        
        # 6. Final status update
        progress_bar['value'] = 100
        status_var.set(f"Success! Saved to: {mp3_file_path}")
        messagebox.showinfo("Success", f"Successfully converted and saved:\n{sanitized_title}.mp3")

    except Exception as e:
        # Handle any errors during the process
        status_var.set(f"Error: {e}")
        messagebox.showerror("Error", f"An error occurred:\n{e}")
    finally:
        # Reset progress bar after a delay
        root.after(5000, lambda: progress_bar.config(value=0))
        root.after(5000, lambda: status_var.set("Ready. Paste a YouTube URL above."))


def start_download_thread():
    """Starts the download process in a new thread."""
    url = url_entry.get()
    if not url:
        messagebox.showwarning("Warning", "Please enter a YouTube URL.")
        return

    output_path = output_dir_var.get()
    if not output_path:
        messagebox.showwarning("Warning", "Please select an output directory.")
        return
        
    # Run the main logic in a thread to prevent the GUI from freezing
    download_thread = threading.Thread(target=download_and_convert, args=(url, output_path, status_var, progress_bar))
    download_thread.start()

def select_output_directory():
    """Opens a dialog to select the output folder."""
    directory = filedialog.askdirectory()
    if directory:
        output_dir_var.set(directory)

# --- GUI Setup ---

# Main window
root = tk.Tk()
root.title("YouTube to MP3 Converter")
root.geometry("600x300")
root.resizable(False, False)

# Style
style = ttk.Style()
style.theme_use('clam')
style.configure('TButton', font=('Helvetica', 10), padding=5)
style.configure('TLabel', font=('Helvetica', 10))
style.configure('TEntry', font=('Helvetica', 10))

# Main frame
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill=tk.BOTH, expand=True)

# URL Input
url_frame = ttk.Frame(main_frame)
url_frame.pack(fill=tk.X, pady=5)
url_label = ttk.Label(url_frame, text="YouTube URL:")
url_label.pack(side=tk.LEFT, padx=(0, 10))
url_entry = ttk.Entry(url_frame, width=60)
url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

# Output Directory Selection
output_frame = ttk.Frame(main_frame)
output_frame.pack(fill=tk.X, pady=10)
output_label = ttk.Label(output_frame, text="Save To:")
output_label.pack(side=tk.LEFT, padx=(0, 10))
output_dir_var = tk.StringVar(value=os.path.join(os.path.expanduser('~'), 'Downloads'))
output_dir_entry = ttk.Entry(output_frame, textvariable=output_dir_var, state='readonly')
output_dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
browse_button = ttk.Button(output_frame, text="Browse...", command=select_output_directory)
browse_button.pack(side=tk.LEFT, padx=(10, 0))

# Download Button
download_button = ttk.Button(main_frame, text="Download & Convert", command=start_download_thread)
download_button.pack(pady=15, ipady=5, fill=tk.X)

# Status Label and Progress Bar
status_frame = ttk.Frame(main_frame)
status_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

status_var = tk.StringVar()
status_var.set("Ready. Paste a YouTube URL above.")
status_label = ttk.Label(status_frame, textvariable=status_var, wraplength=560)
status_label.pack(anchor='w')

progress_bar = ttk.Progressbar(status_frame, orient='horizontal', mode='determinate')
progress_bar.pack(fill=tk.X, pady=(5, 0), ipady=4)

# Run the application
root.mainloop()
