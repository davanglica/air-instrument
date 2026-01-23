import os
import sys
import re
import json
import requests
import urllib3
import unicodedata
from bs4 import BeautifulSoup
from urllib.parse import unquote

# --- CONFIGURATION ---
OUTPUT_DIR = "lyrics"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

# Headers pretending to be a standard browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def clean_filename(text):
    return re.sub(r'[<>:"/\\|?*]', '', text).strip()

# ==========================================
#  LAYOUT ENGINE
# ==========================================
def get_char_width(char):
    # 2 for Full-width (Japanese), 1 for Half-width
    w = unicodedata.east_asian_width(char)
    return 2 if w in ['W', 'F', 'A'] else 1

def map_chords_to_lyrics(raw_chord_line, raw_lyric_line):
    # 1. Build Visual Ruler for Lyrics
    lyric_map = {}
    current_visual_pos = 0
    clean_lyric_text = unicodedata.normalize('NFKC', raw_lyric_line).rstrip()
    
    for idx, char in enumerate(raw_lyric_line):
        w = get_char_width(char)
        for p in range(current_visual_pos, current_visual_pos + w):
            lyric_map[p] = idx
        current_visual_pos += w

    # 2. Map Chords
    chord_map = {}
    current_visual_pos = 0
    buffer_chord = ""
    buffer_start_pos = -1
    
    # Regex for chord characters
    is_chord_char = re.compile(r'[A-G0-9#bmsusdimaugaddnt/Ａ-Ｇ０-９＃ｂｍ]', re.IGNORECASE)

    for i, char in enumerate(raw_chord_line):
        w = get_char_width(char)
        if is_chord_char.match(char):
            if buffer_chord == "": buffer_start_pos = current_visual_pos
            buffer_chord += char
        else:
            if buffer_chord:
                clean_chord = unicodedata.normalize('NFKC', buffer_chord)
                target_idx = lyric_map.get(buffer_start_pos)
                if target_idx is None:
                    target_idx = len(raw_lyric_line) - 1 if len(raw_lyric_line) > 0 else 0
                
                str_idx = str(target_idx)
                if str_idx in chord_map: chord_map[str_idx] += " " + clean_chord
                else: chord_map[str_idx] = clean_chord
                
                buffer_chord = ""
                buffer_start_pos = -1
        current_visual_pos += w
        
    if buffer_chord:
        clean_chord = unicodedata.normalize('NFKC', buffer_chord)
        target_idx = lyric_map.get(buffer_start_pos)
        if target_idx is None:
            target_idx = len(raw_lyric_line) - 1 if len(raw_lyric_line) > 0 else 0
        str_idx = str(target_idx)
        if str_idx in chord_map: chord_map[str_idx] += " " + clean_chord
        else: chord_map[str_idx] = clean_chord

    return clean_lyric_text, chord_map

# ==========================================
#  MAIN SCRAPER
# ==========================================
def get_jtotal_song():
    print("\n--- J-Total Scraper (Version 15: Robust) ---")
    query = input("Enter song name (e.g. カナリヤ): ").strip()
    if not query: return

    # 1. AUTO-SEARCH ATTEMPT
    search_query = f"site:music.j-total.net {query}"
    print(f"Searching: {search_query}")
    
    found_url = None
    
    try:
        # Try Google Search (Simpler HTML structure)
        google_url = "https://www.google.com/search"
        resp = requests.get(google_url, params={'q': search_query}, headers=HEADERS, verify=False, timeout=10)
        
        # Check if we got blocked (Google often sends 429)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Look for links containing j-total
            for link in soup.find_all('a', href=True):
                href = link['href']
                if "music.j-total.net" in href:
                    # Clean up Google's redirect mess
                    # URL usually looks like: /url?q=https://music.j-total.net...&sa=...
                    match = re.search(r'(https://music\.j-total\.net/.*?)&', href)
                    if match:
                        found_url = match.group(1)
                    else:
                        # Sometimes it's direct in the result
                        if href.startswith("https"): found_url = href
                    
                    if found_url:
                        print(f"Auto-selected: {found_url}")
                        break
        else:
            print(f"Search blocked (Status {resp.status_code})")

    except Exception as e:
        print(f"Auto-Search Error: {e}")

    # 2. MANUAL FALLBACK (The safety net)
    if not found_url:
        print("\n>> Auto-search failed (Anti-bot detected).")
        # THIS was missing in the last version!
        found_url = input(">> Please paste the J-Total URL manually: ").strip()

    if not found_url:
        print("No URL provided. Exiting.")
        return

    # 3. SCRAPE
    try:
        print(f"Scraping: {found_url}")
        resp = requests.get(found_url, headers=HEADERS, verify=False, timeout=10)
        resp.encoding = 'shift_jis'
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Beginner Mode Check
        easy_link = soup.find('a', string=re.compile(r'簡単コード'))
        if easy_link and easy_link.get('href'):
            import urllib.parse
            found_url = urllib.parse.urljoin(found_url, easy_link['href'])
            print(f">> Switching to Beginner Version: {found_url}")
            resp = requests.get(found_url, headers=HEADERS, verify=False, timeout=10)
            resp.encoding = 'shift_jis'
            soup = BeautifulSoup(resp.text, 'html.parser')

        # Find Content
        all_tts = soup.find_all('tt')
        valid_tts = [t for t in all_tts if len(t.get_text()) > 50]
        target = max(valid_tts, key=lambda t: len(t.get_text())) if valid_tts else soup.find('div', class_='box_kashi')
        if not target: target = soup.body

        for br in target.find_all('br'): br.replace_with('\n')
        text_content = target.get_text()
        raw_lines = text_content.split('\n')

        json_output = []
        chord_buffer = None
        
        print("\n[DEBUG] Parsing lines...")
        
        for line in raw_lines:
            line = line.rstrip() 
            if not line: continue
            
            # Detect Japanese (Lyrics)
            has_japanese = re.search(r'[ぁ-んァ-ン一-龯]', line)
            # Detect English/Numbers (Potential Chords)
            has_alpha = re.search(r'[A-Za-z]', line)
            
            # Skip UI Headers
            if any(x in line for x in ["Capo", "Key", "BPM", "簡単コード", "ランキング", "戻る"]): continue

            if has_japanese:
                # LYRIC LINE
                if chord_buffer:
                    clean_lyric, anchored_chords = map_chords_to_lyrics(chord_buffer, line)
                else:
                    clean_lyric = unicodedata.normalize('NFKC', line)
                    anchored_chords = {}

                json_output.append({
                    "text": clean_lyric,
                    "chords": anchored_chords
                })
                chord_buffer = None
                
            elif has_alpha and not has_japanese:
                # CHORD LINE
                chord_buffer = line

        print(f"Scraped {len(json_output)} lines.")
        
        base_name = clean_filename(query)
        json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=4, ensure_ascii=False)
            
        print(f"Saved to: {json_path}")
        if len(json_output) > 0:
            print("[Preview 1st Line]:")
            print(json.dumps(json_output[0], indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Scraping Error: {e}")

if __name__ == "__main__":
    setup_directories()
    get_jtotal_song()