#!/usr/bin/env python3
import sys, io, base64, subprocess
for attr in ('stdout', 'stderr'):
    s = getattr(sys, attr)
    if hasattr(s, 'buffer') and s.encoding != 'utf-8':
        setattr(sys, attr, io.TextIOWrapper(s.buffer, encoding='utf-8', errors='replace'))

from pathlib import Path
import soundfile as sf

ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
wav5 = ROOT / "output" / "cosyvoice2_ko_official" / "05_cross_lingual_ko.wav"
mp3_5 = wav5.with_suffix(".mp3")
wav6 = ROOT / "output" / "cosyvoice2_ko_official" / "06_zero_shot_ko_no_frontend.wav"
mp3_6 = wav6.with_suffix(".mp3")
ref = ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"

for src, dst in [(wav5, mp3_5), (wav6, mp3_6)]:
    if src.exists() and not dst.exists():
        subprocess.run(["ffmpeg", "-y", "-i", str(src), "-codec:a", "libmp3lame", "-b:a", "192k", str(dst)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

def dur_str(wav):
    if wav.exists():
        import soundfile as sf
        d, sr = sf.read(str(wav))
        return f"{len(d)/sr:.1f}s"
    return "?"

cards = ""

if mp3_5.exists():
    cards += f"""
    <div class="card">
      <b style="color:#f778ba;">05. cross_lingual + &lt;|ko|&gt; + text_frontend=False [공식 방법]</b>
      <p style="color:#94a3b8;font-size:12px;">{dur_str(wav5)} | RTF 3.93x | FP16 — 청취하여 외계음 여부 확인</p>
      <p style="color:#c9d1d9;background:#0d1117;padding:10px;border-radius:8px;">"안녕하세요, 테스트 음성입니다."</p>
      <audio controls style="width:100%;margin-top:8px" src="data:audio/mp3;base64,{b64(mp3_5)}"></audio>
    </div>"""

if mp3_6.exists():
    cards += f"""
    <div class="card">
      <b style="color:#7ee787;">06. zero_shot + 한국어 prompt_text + text_frontend=False</b>
      <p style="color:#94a3b8;font-size:12px;">{dur_str(wav6)} | FP16</p>
      <p style="color:#c9d1d9;background:#0d1117;padding:10px;border-radius:8px;">"안녕하세요, 테스트 음성입니다."</p>
      <audio controls style="width:100%;margin-top:8px" src="data:audio/mp3;base64,{b64(mp3_6)}"></audio>
    </div>"""

if not cards:
    cards = "<p style='color:#8b949e;'>아직 생성 중...</p>"

html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>CosyVoice2 공식 API 한국어 비교</title>
<style>body{{background:#0b0f19;color:#e6edf3;font-family:-apple-system,sans-serif;padding:30px;}}
.container{{max-width:860px;margin:0 auto;}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:15px;}}
.ref{{border-color:#d29922;margin-bottom:24px;}}
</style></head><body><div class="container">
<h1 style="color:#58a6ff;font-size:22px;">CosyVoice2 공식 API 한국어 테스트</h1>
<p style="color:#8b949e;font-size:13px;margin-bottom:20px;">
  공식 CosyVoice2 클래스 사용 — cross_lingual 및 zero_shot 방식 비교
</p>

<div class="card ref">
  <b style="color:#d29922;">레퍼런스 원음 (ref_songrim_clean_10s.wav)</b>
  <p style="color:#94a3b8;font-size:13px;">"빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."</p>
  <audio controls style="width:100%" src="data:audio/wav;base64,{b64(ref)}"></audio>
</div>

{cards}
</div></body></html>"""

player = ROOT / "output" / "cosyvoice2_strategy_player.html"
with open(player, "w", encoding="utf-8") as f:
    f.write(html)
print("Player updated!")
