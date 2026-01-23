import os
import sys
import re
import json
import difflib
import requests
import urllib.parse
import urllib3
import unicodedata  # <--- THE MAGIC FIX
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
OUTPUT_DIR = "lyrics"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def clean_filename(text):
    return re.sub(r'[<>:"/\\|?*]', '', text).strip()

def normalize_jp(text):
    # Standardize spaces and text width
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'[、。！？]', '', text)
    return text

# ==========================================
# PART 1: GET LRC
# ==========================================
def get_lrc_data():
    print("\n--- Step 1: Find Synced Lyrics (LRCLIB) ---")
    query = input("Enter song name (e.g. カナリヤ): ").strip()
    if not query: return None

    try:
        response = requests.get(
            "https://lrclib.net/api/search", 
            params={"q": query},
            headers=HEADERS,
            verify=False,
            timeout=10
        )
        results = response.json()
    except Exception as e:
        print(f"LRC Search Failed: {e}")
        return None

    valid = [t for t in results if t.get('syncedLyrics')]
    if not valid:
        print("No synced lyrics found.")
        return None

    print(f"\nFound {len(valid)} results:")
    for i, t in enumerate(valid):
        print(f"{i + 1}. {t['trackName']} - {t['artistName']} ({t['albumName']})")

    while True:
        sel = input("\nSelect number (0 to exit): ").strip()
        if sel == '0': return None
        if sel.isdigit() and 1 <= int(sel) <= len(valid):
            track = valid[int(sel) - 1]
            break
        print("Invalid number.")

    base_name = clean_filename(query)
    filename = os.path.join(OUTPUT_DIR, f"{base_name}.lrc")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(track['syncedLyrics'])
    
    return filename, base_name, track['trackName'], track['artistName']

# ==========================================
# PART 2: J-TOTAL MUSIC (With NFKC Normalization)
# ==========================================
def get_jtotal_data(title, artist):
    print("\n--- Step 2: Auto-Get Chords (Target: J-Total Music) ---")
    
    search_query = f"site:music.j-total.net {title} {artist}"
    print(f"Searching: {search_query}")
    
    ddg_url = "https://html.duckduckgo.com/html/"
    data = {'q': search_query}
    found_url = None
    
    try:
        resp = requests.post(ddg_url, data=data, headers=HEADERS, verify=False, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        first_result = soup.find('a', class_='result__a')
        
        if first_result:
            found_url = first_result['href']
            print(f"Auto-selected: {found_url}")
        else:
            print(">> No results found via search engine.")
            
    except Exception as e:
        print(f"Search Error: {e}")

    if not found_url:
        found_url = input(">> Paste J-Total URL manually: ").strip()

    if not found_url: return []

    # --- CHECK FOR BEGINNER LINK ---
    try:
        resp = requests.get(found_url, headers=HEADERS, verify=False, timeout=10)
        resp.encoding = 'shift_jis'
        soup = BeautifulSoup(resp.text, 'html.parser')

        easy_link = soup.find('a', string=re.compile(r'簡単コード'))
        if easy_link and easy_link.get('href'):
            import urllib.parse
            new_url = urllib.parse.urljoin(found_url, easy_link['href'])
            print(f">> FOUND Beginner Version! Switching to: {new_url}")
            found_url = new_url
            resp = requests.get(found_url, headers=HEADERS, verify=False, timeout=10)
            resp.encoding = 'shift_jis'
            soup = BeautifulSoup(resp.text, 'html.parser')
        else:
            print(">> No Beginner version found. Using standard chords.")

        # --- FIND LARGEST CONTAINER ---
        all_tts = soup.find_all('tt')
        target = None
        max_len = 0
        if all_tts:
            for tt in all_tts:
                text_len = len(tt.get_text())
                if text_len > max_len:
                    max_len = text_len
                    target = tt
        else:
            target = soup.find('div', class_='box_kashi') or soup.body

        for br in target.find_all('br'): br.replace_with('\n')
        
        text_content = target.get_text()
        raw_lines = text_content.split('\n')
        
        data = []
        # Updated Regex: Handles slashes, numbers, dims, sus, adds
        chord_regex = re.compile(r'\b([A-G][b#]?(?:m|M|maj|min|sus|dim|aug|add|on|7|9|5|11|13)*\d*(?:/[A-G][b#]?)?)\b')
        
        current_chords = []
        
        print("\n[DEBUG] Processing Lines...")
        for line in raw_lines:
            # --- THE FIX: NORMALIZE JAPANESE CHARACTERS ---
            # Converts 'Ｃ' -> 'C', '＃' -> '#', '　' -> ' '
            clean_line = unicodedata.normalize('NFKC', line).strip()
            
            if not clean_line: continue
            if "簡単コード" in clean_line or "ランキング" in clean_line: continue

            # Extract info using the CLEANED line
            found_chords = chord_regex.findall(clean_line)
            # Check for Japanese in the ORIGINAL line (safer)
            has_japanese = re.search(r'[ぁ-んァ-ン一-龯]', line)
            
            if found_chords and not has_japanese:
                # Accumulate chords (Handles cases where J-Total splits chords across 2 lines)
                current_chords.extend(found_chords)
            elif has_japanese:
                # If lyrics line has chords inline (unlikely for J-Total but possible), grab them
                if found_chords: current_chords = found_chords 
                
                data.append({
                    "text": clean_line,
                    "chords": current_chords
                })
                current_chords = [] 
            else:
                pass

        print(f"Scraped {len(data)} lines.")
        if len(data) > 0:
            print(f"[DEBUG] First Line: {data[0]['text']}")
            print(f"[DEBUG] Chords: {data[0]['chords']}")
        return data

    except Exception as e:
        print(f"Scraping Error: {e}")
        return []

# ==========================================
# PART 3: MERGER (High Precision)
# ==========================================
def merge(lrc_path, chord_data):
    print("\n--- Step 3: Merging ---")
    
    lrc_lines = []
    with open(lrc_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'\[(\d{2}:\d{2}\.\d{2})\](.*)', line)
            if m:
                lrc_lines.append({
                    "time": m.group(1), 
                    "text": m.group(2).strip(),
                    "chords": []
                })

    if not chord_data: return lrc_lines

    cursor = 0
    match_count = 0
    
    for l_line in lrc_lines:
        l_norm = normalize_jp(l_line['text'])
        if not l_norm: continue
        
        best_r = 0.0
        best_idx = -1
        
        for i in range(cursor, min(cursor + 25, len(chord_data))):
            u_line = chord_data[i]
            u_norm = normalize_jp(u_line['text'])
            if not u_norm: continue

            r = difflib.SequenceMatcher(None, l_norm, u_norm).ratio()
            if l_norm in u_norm or u_norm in l_norm:
                r += 0.5
            
            if r > 0.6 and r > best_r:
                best_r = r
                best_idx = i
        
        if best_idx != -1:
            l_line['chords'] = chord_data[best_idx]['chords']
            cursor = best_idx 
            match_count += 1

    print(f"Merged {match_count} lines.")
    return lrc_lines

# ==========================================
# MAIN
# ==========================================
def main():
    setup_directories()
    res = get_lrc_data()
    if not res: return
    lrc_path, base_name, title, artist = res
    
    chord_data = get_jtotal_data(title, artist)
    final_data = merge(lrc_path, chord_data)
    
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSaved: {json_path}")

if __name__ == "__main__":
    main()