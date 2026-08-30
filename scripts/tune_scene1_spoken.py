import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "output"
SAMPLES_DIR = OUTPUT_DIR / "voice_samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

TARGET_SCENE_TEXT = "추운 겨울바람이 문풍지를 세차게 흔들었지만, 마님을 향한 돌쇠의 우직한 마음은 결코 흔들리지 않았습니다."

# 구어체(말하듯 전달) 호흡 전처리 함수
def format_spoken_storytelling(text, mode="natural_talk"):
    t = text.strip()
    if mode == "gentle_whisper":
        # 나지막이 읊조리듯 말하는 구연 톤
        t = re.sub(r'흔들었지만,\s*', '흔들었지만… ', t)
        t = re.sub(r'않았습니다\.\s*', '않았습니다… ', t)
    elif mode == "warm_storyteller":
        # 다정하게 청자에게 말을 건네는 구어체
        t = re.sub(r'흔들었지만,\s*', '흔들었지만 ', t)
        t = re.sub(r'결코\s*', '결코, ', t)
        t = re.sub(r'않았습니다\.\s*', '않았습니다… ', t)
    else:
        # 심리스 슬로우 구어체
        t = t.replace(", ", " ").replace(".", "… ")
    return t

SPOKEN_TUNED_PRESETS = [
    {
        "id": "scene_1_spoken_15_warm",
        "name": "1. [말하듯 나긋나긋한 구연 톤 (속도 -15% / 피치 -3Hz)]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-15%",
        "pitch": "-3Hz",
        "mode": "gentle_whisper",
        "desc": "책 읽는 느낌을 전면 배제! 서두르지 않고 나지막하게 말을 건네듯 깊은 온기를 담아 읊어주는 최고 추천 톤 (가장 추천 ★★★★★)"
    },
    {
        "id": "scene_1_spoken_13_flow",
        "name": "2. [부드러운 대화형 스토리 톤 (속도 -13% / 피치 -3Hz)]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-13%",
        "pitch": "-3Hz",
        "mode": "warm_storyteller",
        "desc": "적당한 여유와 함께 말의 억양과 감정선이 살아있는 자연스러운 구어체 톤"
    },
    {
        "id": "scene_1_spoken_16_deep",
        "name": "3. [심야 힐링 딥 보이스 (속도 -16% / 피치 -4Hz)]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-16%",
        "pitch": "-4Hz",
        "mode": "gentle_whisper",
        "desc": "더욱 깊고 차분하게 가라앉혀 수면 유도와 깊은 서정미를 극대화한 나직한 톤"
    }
]

async def generate_spoken_samples():
    for preset in SPOKEN_TUNED_PRESETS:
        out_file = SAMPLES_DIR / f"{preset['id']}.mp3"
        processed_text = format_spoken_storytelling(TARGET_SCENE_TEXT, preset["mode"])

        communicate = edge_tts.Communicate(
            processed_text,
            preset["voice"],
            rate=preset["rate"],
            pitch=preset["pitch"]
        )
        await communicate.save(str(out_file))
        print(f"  [✓] 구어체 샘플 생성: {preset['name']} -> {out_file.name}")

def update_spoken_html():
    html_file = SAMPLES_DIR / "compare_voices.html"

    cards_html = ""
    for preset in SPOKEN_TUNED_PRESETS:
        is_highlight = "highlight" if "1." in preset["name"] else ""
        cards_html += f"""
      <div class="voice-card {is_highlight}">
        <div class="voice-header">
          <div class="voice-name">{preset['name']}</div>
          <span class="voice-tag">구어체 튜닝</span>
        </div>
        <div class="sample-text-box">
          "{TARGET_SCENE_TEXT}"
        </div>
        <div class="voice-desc">{preset['desc']}</div>
        <audio controls src="{preset['id']}.mp3"></audio>
      </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Scene 1. 구어체(말하듯 전달) 정밀 튜닝 비교실</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Pretendard', sans-serif;
      background-color: #06080d;
      color: #e2e8f0;
      padding: 40px 20px;
      display: flex;
      justify-content: center;
    }}
    .container {{
      max-width: 940px;
      width: 100%;
    }}
    .header {{
      text-align: center;
      margin-bottom: 34px;
    }}
    .header h1 {{
      font-size: 29px;
      color: #f8fafc;
      margin-bottom: 10px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}
    .header p {{
      color: #94a3b8;
      font-size: 16px;
    }}
    .engine-badge {{
      display: inline-block;
      margin-top: 10px;
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.2), rgba(245, 158, 11, 0.2));
      border: 1px solid rgba(56, 189, 248, 0.4);
      padding: 6px 18px;
      border-radius: 30px;
      font-size: 13.5px;
      font-weight: 700;
      color: #38bdf8;
    }}
    .section-label {{
      font-size: 21px;
      font-weight: 800;
      color: #f59e0b;
      margin: 28px 0 16px 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .voice-grid {{
      display: grid;
      gap: 20px;
    }}
    .voice-card {{
      background: #0f1522;
      border: 1px solid #243042;
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      transition: all 0.25s ease;
    }}
    .voice-card.highlight {{
      border-color: #38bdf8;
      background: linear-gradient(180deg, #132238 0%, #0d1524 100%);
      box-shadow: 0 10px 30px rgba(56, 189, 248, 0.2);
    }}
    .voice-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .voice-name {{
      font-size: 18.5px;
      font-weight: 800;
      color: #f8fafc;
    }}
    .voice-tag {{
      font-size: 12.5px;
      font-weight: 700;
      padding: 5px 14px;
      border-radius: 20px;
      background: rgba(56, 189, 248, 0.2);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.5);
    }}
    .sample-text-box {{
      font-size: 18px;
      line-height: 1.65;
      color: #ffffff;
      background: #080c14;
      padding: 16px 20px;
      border-radius: 12px;
      border-left: 4px solid #38bdf8;
      font-style: italic;
    }}
    .voice-desc {{
      font-size: 14.5px;
      color: #cbd5e1;
      line-height: 1.6;
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
      <h1>🎙️ Scene 1. '말하듯 전달하는 구어체' 정밀 튜닝 비교실</h1>
      <p>천재대박 연구사님 지시: 책 읽는 느낌을 지우고, 속도를 늦추어 나지막이 말을 건네는 구연 톤 완성</p>
      <div class="engine-badge">✨ 속도(-15% ~ -16%) 완급 조절 & 자연스러운 어조 마스터링</div>
    </div>

    <div class="section-label">🎧 Scene 1. 템포 및 구어체 완급조절 비교 (3종)</div>
    <div class="voice-grid">
      {cards_html}
    </div>
  </div>
</body>
</html>
"""
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n✨ 구어체 튜닝 비교 청취 페이지 갱신 완료: {html_file}")

async def main():
    print("🎙️ Scene 1 구어체 정밀 튜닝 음성 생성 중...")
    await generate_spoken_samples()
    update_spoken_html()

if __name__ == "__main__":
    asyncio.run(main())
