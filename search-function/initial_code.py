import requests
import sys
import re

# --- FIX 1: FORCE UTF-8 ENCODING FOR WINDOWS TERMINALS ---
# This prevents crashes when printing or inputting Japanese text.
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

def get_synced_lyrics():
    print("\n--- LRCLIB Downloader (Synced Lyrics) ---")
    print("Supports: English, Japanese (Kanji/Kana), Romaji, etc.")
    
    try:
        query = input("Enter song name (e.g., 'アイドル' or 'Yoasobi'): ").strip()
    except UnicodeDecodeError:
        print("Error: Your terminal couldn't handle the Japanese input.")
        print("Try running this command in your terminal before starting python:")
        print("chcp 65001")
        return

    if not query:
        return

    print(f"Searching for: {query}...")

    # 1. SEARCH the API
    url = "https://lrclib.net/api/search"
    params = {"q": query}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    if not results:
        print("No synced lyrics found.")
        return

    # 2. FILTER & DISPLAY Options
    valid_options = []
    
    # Filter for songs that actually have synced lyrics
    for track in results:
        if track.get('syncedLyrics'):
            valid_options.append(track)

    if not valid_options:
        print("Found songs, but none have synced (.lrc) lyrics.")
        return

    print(f"\nFound {len(valid_options)} results:")
    for i, track in enumerate(valid_options):
        # We use .get() to avoid errors if a field is missing
        t_name = track.get('trackName', 'Unknown Title')
        a_name = track.get('artistName', 'Unknown Artist')
        al_name = track.get('albumName', 'Unknown Album')
        
        print(f"{i + 1}. {t_name} - {a_name} (Album: {al_name})")

    # 3. USER SELECTS
    choice = input("\nSelect a number to download .lrc: ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(valid_options):
        print("Invalid selection.")
        return

    selected_track = valid_options[int(choice) - 1]

    # 4. SAVE the .lrc file
    # --- FIX 2: PRESERVE JAPANESE CHARACTERS IN FILENAME ---
    original_filename = f"{selected_track['trackName']} - {selected_track['artistName']}"
    
    # Remove ONLY characters that are illegal in Windows filenames: < > : " / \ | ? *
    safe_filename = re.sub(r'[<>:"/\\|?*]', '', original_filename)
    filename = f"{safe_filename}.lrc"

    try:
        # Explicitly write with utf-8 encoding
        with open(filename, "w", encoding="utf-8") as f:
            f.write(selected_track['syncedLyrics'])
        
        print(f"\nSUCCESS! Saved to: {filename}")
        print("Content Preview:")
        print("-" * 20)
        # Safely print first 5 lines
        lines = selected_track['syncedLyrics'].split("\n")
        for line in lines[:5]:
            print(line)
        print("...")
        
    except OSError as e:
        print(f"Error saving file (maybe the filename is too long?): {e}")

if __name__ == "__main__":
    get_synced_lyrics()

# possible fix: only show the number of synced lyrics