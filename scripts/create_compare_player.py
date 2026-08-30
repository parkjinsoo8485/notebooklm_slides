import base64
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

raw_tts = Path("output/temp_tts/raw_tts_001.mp3")
rvc_mp3 = Path("output/audio/slide_001.mp3")

raw_b64 = base64.b64encode(raw_tts.read_bytes()).decode('utf-8') if raw_tts.exists() else ''
rvc_b64 = base64.b64encode(rvc_mp3.read_bytes()).decode('utf-8') if rvc_mp3.exists() else ''

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>음성 비교 플레이어 (Edge-TTS vs RVC)</title>
<style>
  body {{ background: #0f172a; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; display: flex; justify-content: center; }}
  .box {{ max-width: 650px; width: 100%; }}
  .card {{ background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 20px; border: 1px solid #334155; }}
  h2 {{ font-size: 18px; margin-bottom: 8px; color: #38bdf8; }}
  p {{ font-size: 14px; color: #94a3b8; margin-bottom: 12px; }}
  audio {{ width: 100%; }}
</style>
</head>
<body>
<div class="box">
  <h1 style="margin-bottom:24px; font-size: 24px;">🎙️ 음성 비교 청취 (슬라이드 1)</h1>
  <div class="card">
    <h2>1. Edge-TTS 순수 마스터링 (중년 여성 스토리텔러 톤)</h2>
    <p>기계음 없는 부드럽고 자연스러운 고음질 한국어 음성</p>
    <audio controls src="data:audio/mp3;base64,{raw_b64}"></audio>
  </div>
  <div class="card">
    <h2>2. RVC 변환 음성 (JK_Narrator 모델 적용)</h2>
    <p>RVC 음색 변환 신경망을 통과한 음성</p>
    <audio controls src="data:audio/mp3;base64,{rvc_b64}"></audio>
  </div>
</div>
</body>
</html>"""

Path("output/compare_player.html").write_text(html, encoding="utf-8")
print("✅ 비교 플레이어 생성 완료 -> output/compare_player.html")
