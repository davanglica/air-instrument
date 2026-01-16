# read_chart.py

import re

def parse_chart_text(text: str):
    lines = re.split(r"\r?\n", text)
    meta = {}
    events = {
        "bpmChanges": [],
        "timeSignatures": [],
        "lyrics": [],
        "notes": {},
    }
    warnings = []

    def to_num(s):
        try:
            return float(s)
        except:
            return None

    for raw in lines:
        line = raw.strip()
        if not line or not line.startswith("#"):
            continue

        if re.match(r"^#TITLE\b", line, re.I):
            meta["title"] = re.sub(r"^#TITLE\b\s*", "", line, flags=re.I)
            continue
        if re.match(r"^#ARTIST\b", line, re.I):
            meta["artist"] = re.sub(r"^#ARTIST\b\s*", "", line, flags=re.I)
            continue
        if re.match(r"^#BPM\b", line, re.I):
            meta["bpm"] = to_num(re.sub(r"^#BPM\b\s*", "", line, flags=re.I))
            continue
        if re.match(r"^#LEVEL\b", line, re.I):
            meta["level"] = to_num(re.sub(r"^#LEVEL\b\s*", "", line, flags=re.I))
            continue
        if re.match(r"^#VOLUME\b", line, re.I):
            meta["volume"] = to_num(re.sub(r"^#VOLUME\b\s*", "", line, flags=re.I))
            continue
        if re.match(r"^#WAV\b", line, re.I):
            meta["wav"] = re.sub(r"^#WAV\b\s*", "", line, flags=re.I)
            continue

        m = re.match(r"^#(\d{3})(\d{3})\s*:\s*(.*)$", line)
        if not m:
            warnings.append(f"未知の行: {line}")
            continue

        measure = int(m.group(1))
        cmd = int(m.group(2))
        payload = m.group(3).strip()

        if cmd == 1:
            events["bpmChanges"].append({"measure": measure, "bpm": to_num(payload)})

        elif cmd == 2:
            n, d = map(to_num, payload.split(":"))
            events["timeSignatures"].append({
                "measure": measure,
                "numerator": n,
                "denominator": d,
            })

        elif cmd == 3:
            events["lyrics"].append({"measure": measure, "text": payload})

        elif 101 <= cmd <= 199:
            key = str(cmd - 100)
            pattern = re.sub(r"\s+", "", payload)
            divisions = len(pattern)
            indices = [i + 1 for i, c in enumerate(pattern) if c == "1"]

            events["notes"].setdefault(key, []).append({
                "measure": measure,
                "divisions": divisions,
                "pattern": pattern,
                "indices": indices,
            })
        else:
            warnings.append(f"未対応コマンド: {line}")

    return {"meta": meta, "events": events, "warnings": warnings}
