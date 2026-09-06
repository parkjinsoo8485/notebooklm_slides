import json
from pathlib import Path

workspace = Path(r"C:\My_Project\src\notebooklm_slides")
out = workspace / "output"
audio_dir = out / "audio"
sub_dir = out / "subtitles"
slides_file = out / "slides_data.json"

with open(slides_file, "r", encoding="utf-8") as f:
    slides = json.load(f)

print(f"Total slides in json: {len(slides)}")
missing_audio = []
missing_sub = []
total_dur = 0.0

for s in slides:
    idx = s["slide_index"]
    dur = s.get("audio_duration", 0.0)
    total_dur += dur
    a_path = audio_dir / f"slide_{idx:03d}.mp3"
    s_path = sub_dir / f"slide_{idx:03d}.srt"
    if not a_path.exists() or a_path.stat().st_size < 1000:
        missing_audio.append(idx)
    if not s_path.exists() or s_path.stat().st_size < 10:
        missing_sub.append(idx)

print(f"Missing or invalid audio: {len(missing_audio)} {missing_audio}")
print(f"Missing or invalid subtitles: {len(missing_sub)} {missing_sub}")
print(f"Total story duration: {int(total_dur // 60)}분 {int(total_dur % 60)}초 ({total_dur:.1f}초)")
print(f"Slide 1 duration: {slides[0]['audio_duration']}s")
print(f"Slide 120 duration: {slides[119]['audio_duration']}s")
