import asyncio
import os
import sys
import subprocess
from pathlib import Path
import json
import base64
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
OUT_DIR = WORKSPACE / "output" / "slide01_hyunsu_showcase"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCRIPT_TEXT = "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 쫓겨나고 말았습니다. 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었습니다."

PRESETS = [
    {
        "id": "hyunsu_master_warm",
        "badge": "👑 1. [현수] 스튜디오 마스터 (웜톤 EQ - 강력 추천)",
        "name": "✨ [슬라이드 01] 현수 스튜디오 마스터 음성",
        "desc": "남성 다국어 신경망 특유의 지적이고 묵직한 중저음에 220Hz 웜톤 EQ를 더해 깊은 울림과 신뢰감을 극대화한 대표 톤 (약 22초)",
        "rate": "-16%",
        "pitch": "-12Hz",
        "warmth_eq": True,
        "highlight": True
    },
    {
        "id": "hyunsu_deep_story",
        "badge": "🎙️ 2. [현수] 중후한 고전 야담 이야기꾼",
        "name": "📜 [슬라이드 01] 현수 중후한 고전 야담 톤",
        "desc": "여유로운 옛이야기 템포(-20%)와 묵직한 저음으로 비장미와 몰입감을 살린 정통 야담 톤 (약 24초)",
        "rate": "-20%",
        "pitch": "-18Hz",
        "warmth_eq": True,
        "highlight": True
    },
    {
        "id": "hyunsu_classic_clean",
        "badge": "📖 3. [현수] 맑고 정갈한 서사 낭독",
        "name": "📖 [슬라이드 01] 현수 맑은 정통 서사 낭독",
        "desc": "과장 없는 담백함과 정확한 표준 발음으로 역사 다큐멘터리처럼 전달하는 톤 (약 21초)",
        "rate": "-14%",
        "pitch": "-8Hz",
        "warmth_eq": False,
        "highlight": False
    },
    {
        "id": "brian_multilingual",
        "badge": "🌍 4. [브라이언] 글로벌 다국어 신경망 톤",
        "name": "🎙️ [슬라이드 01] 브라이언(Brian) 다국어 신경망 한국어 낭독",
        "desc": "영미권 대표 다국어 모델(BrianMultilingual)이 구사하는 깊고 이국적인 한국어 낭독 톤 (약 22초)",
        "voice_override": "en-US-BrianMultilingualNeural",
        "rate": "-14%",
        "pitch": "-10Hz",
        "warmth_eq": True,
        "highlight": False
    }
]

async def build_hyunsu_showcase():
    print("=" * 70)
    print(" 🎙️ HyunsuMultilingualNeural 쇼케이스 음원 생성 시작")
    print("=" * 70)

    tracks = []
    for p in PRESETS:
        voice = p.get("voice_override", "ko-KR-HyunsuMultilingualNeural")
        raw_mp3 = OUT_DIR / f"{p['id']}_raw.mp3"
        final_mp3 = OUT_DIR / f"{p['id']}.mp3"

        comm = edge_tts.Communicate(SCRIPT_TEXT, voice, rate=p["rate"], pitch=p["pitch"])
        target = raw_mp3 if p["warmth_eq"] else final_mp3
        await comm.save(str(target))

        if p["warmth_eq"]:
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", str(raw_mp3),
                "-af", "equalizer=f=200:width_type=o:width=1.3:g=3.5,equalizer=f=3400:width_type=o:width=1.2:g=-2.5,volume=1.18",
                "-b:a", "192k", str(final_mp3)
            ]
            subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if raw_mp3.exists():
                raw_mp3.unlink()

        # duration
        ffprobe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(final_mp3)
        ]
        res = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, text=True)
        dur = float(res.stdout.strip())
        dur_str = f"{int(dur//60):02d}:{int(dur%60):02d}"

        with open(final_mp3, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")

        tracks.append({
            "badge": p["badge"],
            "name": p["name"],
            "desc": p["desc"],
            "duration": dur_str,
            "b64": b64,
            "highlight": p["highlight"]
        })
        print(f"   ✔ [{p['name']}] 생성 완료 ({dur_str})")

    tracks_json = json.dumps(tracks, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] HyunsuMultilingualNeural 마스터 음성 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #070a11;
  --card-bg: rgba(18, 25, 42, 0.92);
  --accent: #38bdf8;
  --accent-glow: rgba(56, 189, 248, 0.4);
  --emerald: #10b981;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --border: rgba(255, 255, 255, 0.12);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: radial-gradient(circle at 50% 10%, #0c2b48 0%, var(--bg) 100%);
  color: var(--text);
  font-family: 'Pretendard', sans-serif;
  min-height: 100vh;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
}}
.container {{
  max-width: 920px;
  width: 100%;
}}
.header {{
  text-align: center;
  margin-bottom: 35px;
}}
.tag {{
  display: inline-block;
  padding: 6px 18px;
  background: rgba(56, 189, 248, 0.2);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 1.5px;
  margin-bottom: 12px;
}}
h1 {{
  font-family: 'Noto Serif KR', serif;
  font-size: 32px;
  font-weight: 900;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #bae6fd 50%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
p.sub {{
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1.6;
}}
.script-box {{
  background: rgba(18, 25, 42, 0.95);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 26px;
  margin-bottom: 30px;
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}
.script-title {{
  color: var(--accent);
  font-weight: 800;
  font-size: 13px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.script-text {{
  font-family: 'Noto Serif KR', serif;
  font-size: 18px;
  line-height: 1.8;
  color: #f1f5f9;
}}
.track-list {{
  display: flex;
  flex-direction: column;
  gap: 22px;
}}
.track-card {{
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 25px rgba(0,0,0,0.4);
  position: relative;
}}
.track-card.highlight {{
  border-color: var(--accent);
  background: rgba(15, 36, 64, 0.96);
  box-shadow: 0 12px 35px var(--accent-glow);
}}
.track-card:hover {{
  transform: translateY(-3px);
}}
.track-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}}
.track-badge {{
  font-size: 13px;
  font-weight: 800;
  padding: 5px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
}}
.track-card.highlight .track-badge {{
  background: rgba(56, 189, 248, 0.25);
  color: var(--accent);
  border: 1px solid var(--accent);
}}
.track-time {{
  font-size: 13px;
  font-weight: 700;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  padding: 4px 10px;
  border-radius: 6px;
}}
.track-name {{
  font-family: 'Noto Serif KR', serif;
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 8px;
  color: #ffffff;
}}
.track-desc {{
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 18px;
  line-height: 1.5;
}}
audio {{
  width: 100%;
  border-radius: 10px;
  outline: none;
}}
audio::-webkit-media-controls-panel {{
  background-color: #1e293b;
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="tag">🌐 EDGE-TTS MULTILINGUAL NEURAL ENGINE</div>
    <h1>[송림야담] HyunsuMultilingualNeural 마스터 음성 청음실</h1>
    <p class="sub">별도의 복잡한 이식 없이 <strong>edge-tts에서 즉시 100% 사용 가능한 현수(HyunsuMultilingualNeural)</strong> 고품질 마스터 음성입니다.</p>
  </div>

  <div class="script-box">
    <div class="script-title">📜 낭독 대본 (슬라이드 01)</div>
    <div class="script-text">
      "{SCRIPT_TEXT}"
    </div>
  </div>

  <div class="track-list" id="trackList"></div>
</div>

<script>
const tracks = {tracks_json};
const container = document.getElementById('trackList');

tracks.forEach((t, idx) => {{
  const card = document.createElement('div');
  card.className = 'track-card' + (t.highlight ? ' highlight' : '');
  
  card.innerHTML = `
    <div class="track-header">
      <span class="track-badge">${{t.badge}}</span>
      <span class="track-time">⏱️ 재생시간: ${{t.duration}}</span>
    </div>
    <div class="track-name">${{t.name}}</div>
    <div class="track-desc">${{t.desc}}</div>
    <audio controls src="data:audio/mp3;base64,${{t.b64}}" preload="auto"></audio>
  `;
  container.appendChild(card);
}});

document.addEventListener('play', function(e) {{
  const audios = document.getElementsByTagName('audio');
  for (let i = 0; i < audios.length; i++) {{
    if (audios[i] != e.target) {{
      audios[i].pause();
    }}
  }}
}}, true);
</script>
</body>
</html>"""

    html_path = WORKSPACE / "output" / "slide01_hyunsu_player.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"🎉 Hyunsu 전용 청음실 HTML 생성 완료: {html_path}")

if __name__ == "__main__":
    asyncio.run(build_hyunsu_showcase())
