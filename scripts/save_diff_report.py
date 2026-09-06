import json
import sys
from pathlib import Path

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(WORKSPACE / "scripts"))
from korean_phonetic_normalizer import normalize_phonetics_for_tts

slides = json.load(open(WORKSPACE / "output" / "slides_data.json", encoding="utf-8"))
out_lines = []
for s in slides:
    raw = s.get("voice_script", "")
    norm = normalize_phonetics_for_tts(raw)
    if raw != norm:
        out_lines.append(f"--- [Slide {s['slide_index']}] ---")
        out_lines.append(f"원문: {raw}")
        out_lines.append(f"교정: {norm}\n")

with open(WORKSPACE / "output" / "scratch_diff_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print(f"Diff report saved to scratch_diff_report.txt, total changed: {len(out_lines)//3}")
