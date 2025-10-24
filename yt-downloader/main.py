import yt_dlp
import os

def download_youtube_as_mp3(video_url, output_path='downloads'):
    """
    Downloads the audio from a YouTube video and converts it to MP3 format.

    Args:
        video_url (str): The URL of the YouTube video.
        output_path (str): The directory where the MP3 file will be saved.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # yt-dlp options dictionary
    ydl_opts = {
        'format': 'bestaudio/best',  # Download the best audio format
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),  # Output file template
        'postprocessors': [{  # Post-process to extract audio and convert to mp3
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # Set MP3 quality (e.g., 192kbps)
        }],
        'logger': None,  # Suppress logging for clean output
        'progress_hooks': [lambda d: print(f"Status: {d['status']}")], # Simple progress logging
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Starting download and conversion for: {video_url}")
            info = ydl.extract_info(video_url, download=True)
            # Find the expected final file name
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
            print(f"Successfully downloaded and converted to MP3: {filename}")
    except yt_dlp.utils.DownloadError as e:
        print(f"An error occurred during download: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Example Usage ---
# Replace this URL with the actual YouTube link you want to download
youtube_link = 'https://www.youtube.com/watch?v=0GDfOAuUvQ0&t=10912s' 
download_directory = 'youtube_mp3_files'
 
# Call the function
download_youtube_as_mp3(youtube_link, download_directory)