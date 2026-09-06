import base64
import json
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
GRANDFATHER_AUDIO = WORKSPACE / "output" / "slide01_grandfather_samples" / "slide_001_grandfather_xtts_mastered.mp3"
TRACK1_AUDIO = WORKSPACE / "output" / "slide01_xtts_cloned" / "slide_001_track1_yadam_mastered.mp3"
REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "03_elderly_grandfather_folklore.mp3"
EDGE_PREV = WORKSPACE / "output" / "rvc_ultimate_samples" / "slide_001_edge_mastered.mp3"

HTML_PATH = WORKSPACE / "output" / "slide01_grandfather_player.html"

def to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

RAW_SCRIPT = "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이 하루아침에 억울한 역모의 누명을 쓰고 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. 차가운 달빛조차 서럽게 얼어붙던 어느 쓸쓸한 늦가을 밤의 비극이었답니다."

tracks = [
    {
        "badge": "🔥 NEW: 트랙 02 할아버지 구연 복제 완성본",
        "name": "👴 [슬라이드 01] 트랙 02 따뜻한 할아버지 전래동화 구연 낭독",
        "desc": "세월의 연륜과 깊이가 묻어나는 자애롭고 포근한 할아버지 목소리. 기계음 없이 자연스러운 옛이야기 구연 호흡과 온기 (약 47초)",
        "duration": "00:47",
        "b64": to_b64(GRANDFATHER_AUDIO),
        "tag": "Track 02 Voice Cloning + Warm Tube DSP",
        "highlight": True
    },
    {
        "badge": "👑 이전 생성: 트랙 01 야담 이야기꾼",
        "name": "🎙️ [슬라이드 01] 트랙 01 구수한 조선 야담 이야기꾼 낭독",
        "desc": "감정이 살아있는 완급 조절과 구수한 억양의 조선 야담 전문 낭독 톤 (약 48초)",
        "duration": "00:48",
        "b64": to_b64(TRACK1_AUDIO),
        "tag": "Track 01 Voice Cloning",
        "highlight": False
    },
    {
        "badge": "📻 원본 레퍼런스 육성",
        "name": "📖 [참조] 트랙 02 할아버지 전래동화 실제 육성 원음",
        "desc": "목소리와 말투의 원본이 된 실제 할아버지 낭독자의 원음 (2분 30초)",
        "duration": "02:30",
        "b64": to_b64(REF_GRANDFATHER),
        "tag": "100% Authentic Human Voice",
        "highlight": False
    },
    {
        "badge": "⚠️ 비교군: 기존 AI 기계음",
        "name": "❌ [비교군] 기존 Edge-TTS 표준 신경망",
        "desc": "딱딱하고 일정한 음절 박자로 인해 기계음으로 느껴졌던 기존 음성 (22초)",
        "duration": "00:22",
        "b64": to_b64(EDGE_PREV),
        "tag": "Legacy Edge-TTS",
        "highlight": False
    }
]

tracks_json = json.dumps(tracks, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 트랙 02 할아버지 전래동화 구연 슬라이드 01 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #080b12;
  --card-bg: rgba(18, 25, 42, 0.9);
  --accent: #f59e0b;
  --accent-glow: rgba(245, 158, 11, 0.4);
  --emerald: #10b981;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --border: rgba(255, 255, 255, 0.12);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: radial-gradient(circle at 50% 10%, #1c2a4a 0%, var(--bg) 100%);
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
  background: rgba(245, 158, 11, 0.2);
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
  background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
p.sub {{
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1.6;
}}
.script-box {{
  background: rgba(18, 25, 42, 0.9);
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
  background: rgba(28, 40, 68, 0.95);
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
  background: rgba(245, 158, 11, 0.25);
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
    <div class="tag">👴 ELDERLY GRANDFATHER VOICE CLONING</div>
    <h1>[송림야담] 트랙 02 할아버지 전래동화 구연 슬라이드 01 청음실</h1>
    <p class="sub">선택하신 [트랙 02번 따뜻한 할아버지 목소리]의 연륜과 구수한 호흡을 1:1로 복제하여 낭독한 슬라이드 01 대사</p>
  </div>

  <div class="script-box">
    <div class="script-title">📜 낭독 대본 (슬라이드 01)</div>
    <div class="script-text">
      "{RAW_SCRIPT}"
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

// 동시 재생 방지
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

HTML_PATH.write_text(html_content, encoding="utf-8")
print(f"🎉 할아버지 버전 플레이어 생성 완료: {HTML_PATH}")
