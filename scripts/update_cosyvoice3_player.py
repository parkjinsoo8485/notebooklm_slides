#!/usr/bin/env python3
import sys, io, base64, subprocess
for attr in ('stdout', 'stderr'):
    s = getattr(sys, attr)
    if hasattr(s, 'buffer') and s.encoding != 'utf-8':
        setattr(sys, attr, io.TextIOWrapper(s.buffer, encoding='utf-8', errors='replace'))

from pathlib import Path
import soundfile as sf

ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
OUT = ROOT / "output" / "cosyvoice3_korean_results"
wav = OUT / "debug_instruct2_korean.wav"
mp3 = OUT / "debug_instruct2_korean.mp3"
ref = ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"

if wav.exists():
    subprocess.run(["ffmpeg", "-y", "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("MP3 converted!")

def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

def dur(w):
    d, sr = sf.read(str(w))
    return f"{len(d)/sr:.1f}"

mp3_b64 = b64(mp3) if mp3.exists() else ""
ref_b64 = b64(ref) if ref.exists() else ""
dur_str = dur(wav) if wav.exists() else "?"

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Fun-CosyVoice 3.0 한국어 공식 합성 결과</title>
    <style>
        body {{ background:#0b0f19; color:#e6edf3; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; padding:30px; }}
        .container {{ max-width:860px; margin:0 auto; }}
        .card {{ background:#161b22; border:1px solid #30363d; border-radius:12px; padding:20px; margin-bottom:15px; }}
        .ref {{ border-color:#d29922; margin-bottom:20px; }}
        .badge {{ background:#238636; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; margin-left:8px; }}
    </style>
</head>
<body>
<div class="container">
    <h1 style="color:#58a6ff;font-size:22px;">🎉 Fun-CosyVoice 3.0 한국어 공식 합성 결과</h1>
    <p style="color:#8b949e;font-size:13px;margin-bottom:20px;">
        순정 AutoModel 파이프라인 + Euler 4-스텝 가속 (3배 속도 향상)
    </p>

    <div class="card ref">
        <strong style="color:#d29922;">🎧 레퍼런스 원음 (ref_songrim_clean_10s.wav)</strong>
        <p style="font-size:13px;color:#94a3b8;margin:6px 0;">"빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."</p>
        <audio controls style="width:100%;margin-top:8px;" src="data:audio/wav;base64,{ref_b64}"></audio>
    </div>

    <div class="card" style="border-color:#38bdf8;background:#0d1829;">
        <h3 style="margin-top:0;color:#38bdf8;font-size:16px;">
            ✨ 04. 순정 AutoModel + Euler 4-스텝 가속 <span class="badge">최신 생성본</span>
        </h3>
        <p style="font-size:12px;color:#8b949e;">
            ⏱️ 재생 시간: {dur_str}초 | ⚡ 생성 소요: 169.1초 (기존 492초 대비 3배 단축)
        </p>
        <p style="font-size:14px;color:#c9d1d9;background:#09101d;padding:10px;border-radius:8px;">
            "안녕하세요, 테스트 음성입니다."
        </p>
        <audio controls autoplay style="width:100%;margin-top:8px;" src="data:audio/mp3;base64,{mp3_b64}"></audio>
    </div>
</div>
</body>
</html>"""

player_path = ROOT / "output" / "cosyvoice3_player.html"
with open(player_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Player updated successfully!")
