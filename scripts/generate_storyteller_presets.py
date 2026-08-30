"""
generate_storyteller_presets.py
Edge-TTS를 기반으로 다양한 중년 여성 스토리텔러 음색 프리셋을 생성하고
FFmpeg 마스터링 필터를 적용하여 비교 청취 가능한 HTML 플레이어를 제작합니다.
"""

import asyncio
import base64
import json
from pathlib import Path
import subprocess
import sys
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "output" / "storyteller_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_TEXT = "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었답니다..."

PRESETS = [
    {
        "id": "preset1_calm_middle_aged",
        "name": "1. 온화하고 기품 있는 중년 나레이터 (차분한 50대 톤)",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-20%",
        "pitch": "-20Hz",
        "eq": "equalizer=f=200:t=q:w=1.5:g=3.5,equalizer=f=3500:t=q:w=1.0:g=-2.0,compand=attacks=0.02:decays=0.2:points=-80/-80|-20/-16|0/-6"
    },
    {
        "id": "preset2_deep_folklore",
        "name": "2. 깊은 심야 설화 / 야담 이야기꾼 (중후하고 서글픈 톤)",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-28%",
        "pitch": "-30Hz",
        "eq": "equalizer=f=180:t=q:w=1.2:g=5.0,equalizer=f=1000:t=q:w=1.0:g=1.5,equalizer=f=4000:t=q:w=1.0:g=-3.0,compand=attacks=0.03:decays=0.3:points=-80/-80|-22/-15|0/-4"
    },
    {
        "id": "preset3_soft_storyteller",
        "name": "3. 따뜻한 옛날이야기 할머니/중년 여인 (포근하고 여유로운 톤)",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-25%",
        "pitch": "-15Hz",
        "eq": "equalizer=f=250:t=q:w=1.5:g=4.0,equalizer=f=5000:t=q:w=1.0:g=-2.5,compand=attacks=0.02:decays=0.25:points=-80/-80|-18/-14|0/-6"
    },
    {
        "id": "preset4_dramatic_narrator",
        "name": "4. 극적 긴장감의 정통 사극 해설자 (단단하고 명료한 톤)",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-18%",
        "pitch": "-25Hz",
        "eq": "equalizer=f=150:t=q:w=1.0:g=4.0,equalizer=f=2500:t=q:w=1.2:g=2.0,equalizer=f=6000:t=q:w=1.0:g=-2.0,compand=attacks=0.01:decays=0.15:points=-80/-80|-16/-12|0/-4"
    }
]

async def generate_all():
    print("🎙️ 중년 여성 스토리텔러 프리셋 생성 시작...")
    results = []

    for p in PRESETS:
        raw_mp3 = OUTPUT_DIR / f"{p['id']}_raw.mp3"
        final_mp3 = OUTPUT_DIR / f"{p['id']}.mp3"

        print(f"  → [{p['name']}] Edge-TTS 생성 중...")
        comm = edge_tts.Communicate(
            SAMPLE_TEXT,
            p["voice"],
            rate=p["rate"],
            pitch=p["pitch"]
        )
        await comm.save(str(raw_mp3))

        # FFmpeg 마스터링 적용
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_mp3),
            "-af", p["eq"],
            "-codec:a", "libmp3lame", "-b:a", "192k",
            str(final_mp3)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Base64 인코딩
        audio_b64 = base64.b64encode(final_mp3.read_bytes()).decode('utf-8')
        results.append({
            "id": p["id"],
            "name": p["name"],
            "rate": p["rate"],
            "pitch": p["pitch"],
            "audio_b64": audio_b64
        })

    # HTML 플레이어 제작
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>중년 여성 스토리텔러 목소리 청취 및 선택</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0f172a;
    color: #f8fafc;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 40px 20px;
    display: flex;
    justify-content: center;
  }}
  .container {{
    max-width: 800px;
    width: 100%;
  }}
  .header {{
    text-align: center;
    margin-bottom: 35px;
  }}
  .header h1 {{
    font-size: 26px;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 10px;
    letter-spacing: -0.5px;
  }}
  .header p {{
    color: #94a3b8;
    font-size: 15px;
  }}
  .script-box {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 30px;
    line-height: 1.7;
    font-size: 15px;
    color: #e2e8f0;
  }}
  .script-label {{
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    color: #38bdf8;
    margin-bottom: 8px;
  }}
  .card {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.2s ease;
  }}
  .card:hover {{
    border-color: #38bdf8;
    transform: translateY(-2px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
  }}
  .card-title {{
    font-size: 17px;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .card-meta {{
    font-size: 13px;
    color: #64748b;
    margin-bottom: 16px;
  }}
  .card-meta span {{
    display: inline-block;
    background: #0f172a;
    padding: 3px 8px;
    border-radius: 6px;
    margin-right: 6px;
    border: 1px solid #1e293b;
  }}
  audio {{
    width: 100%;
    height: 44px;
    border-radius: 8px;
    outline: none;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🎙️ 중년 여성 스토리텔러 음성 프리셋</h1>
    <p>Edge-TTS + 어쿠스틱 마스터링 필터가 적용된 4가지 목소리를 직접 들어보세요.</p>
  </div>

  <div class="script-box">
    <div class="script-label">테스트 대본 (슬라이드 1)</div>
    "{SAMPLE_TEXT}"
  </div>

  <div class="preset-list">
"""
    for res in results:
        html_content += f"""
    <div class="card">
      <div class="card-title">{res['name']}</div>
      <div class="card-meta">
        <span>속도: {res['rate']}</span>
        <span>피치: {res['pitch']}</span>
        <span>고급 EQ/컴프레서 적용</span>
      </div>
      <audio controls src="data:audio/mp3;base64,{res['audio_b64']}"></audio>
    </div>
"""
    html_content += """
  </div>
</div>
</body>
</html>
"""
    player_path = OUTPUT_DIR / "storyteller_presets_player.html"
    player_path.write_text(html_content, encoding='utf-8')
    print(f"✅ 프리셋 생성 완료! 플레이어: {player_path}")

if __name__ == "__main__":
    asyncio.run(generate_all())
