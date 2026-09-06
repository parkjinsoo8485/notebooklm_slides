import base64
import json
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

OUT_DIR = Path(r"C:\My_Project\src\notebooklm_slides\output\human_voice_showcase")
HTML_PATH = Path(r"C:\My_Project\src\notebooklm_slides\output\authentic_human_storyteller_player.html")

def to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

tracks = [
    {
        "badge": "👑 트랙 01 (추천 A: 구수한 조선 야담)",
        "name": "조선 야담 전문 이야기꾼 (실제 명품 육성 낭독)",
        "desc": "구수한 억양, 생동감 넘치는 호흡, 조선 시대 설화와 야담에 가장 완벽하게 어울리는 실제 낭독자 육성 (2분 30초)",
        "duration": "02:30",
        "file": OUT_DIR / "02_authentic_yadam_storyteller.mp3",
        "tag": "실제 인간 육성 낭독 원음"
    },
    {
        "badge": "👴 트랙 02 (추천 B: 노인/할아버지 구연)",
        "name": "따뜻하고 깊이 있는 할아버지 전래동화 구연",
        "desc": "연륜이 묻어나는 편안하고 깊은 목소리, 자애롭고 정겨운 옛이야기 구연 톤 (2분 30초)",
        "duration": "02:30",
        "file": OUT_DIR / "03_elderly_grandfather_folklore.mp3",
        "tag": "실제 인간 육성 낭독 원음"
    },
    {
        "badge": "📜 트랙 03 (추천 C: 정통 역사 서사형)",
        "name": "고전 역사 설화 다큐멘터리 성우 나레이션",
        "desc": "단아하고 정갈하며 비장미가 감도는 정통 고전 서사형 나레이터 육성 (1분 10초)",
        "duration": "01:10",
        "file": OUT_DIR / "01_korean_historical_narrator.mp3",
        "tag": "실제 인간 육성 낭독 원음"
    }
]

for t in tracks:
    t["b64"] = to_b64(t["file"])
    del t["file"]

tracks_json = json.dumps(tracks, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 실제 오픈 노인/야담/구연 낭독자 원음 청음실 (총 6분+)</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #090c13;
  --card-bg: rgba(18, 26, 43, 0.9);
  --accent: #f59e0b;
  --accent-glow: rgba(245, 158, 11, 0.35);
  --emerald: #10b981;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --border: rgba(255, 255, 255, 0.12);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: radial-gradient(circle at 50% 10%, #17243d 0%, var(--bg) 100%);
  color: var(--text);
  font-family: 'Pretendard', sans-serif;
  min-height: 100vh;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
}}
.container {{
  max-width: 960px;
  width: 100%;
}}
.header {{
  text-align: center;
  margin-bottom: 35px;
}}
.tag {{
  display: inline-block;
  padding: 6px 16px;
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 1px;
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
.info-box {{
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 30px;
  backdrop-filter: blur(12px);
}}
.info-title {{
  color: var(--emerald);
  font-weight: 800;
  font-size: 15px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.info-desc {{
  font-size: 14px;
  color: #cbd5e1;
  line-height: 1.6;
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
}}
.track-card:hover, .track-card.active {{
  border-color: var(--accent);
  transform: translateY(-3px);
  box-shadow: 0 14px 35px var(--accent-glow);
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
  background: rgba(245, 158, 11, 0.2);
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
  font-size: 21px;
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
    <div class="tag">🎙️ AUTHENTIC HUMAN STORYTELLER ARCHIVE</div>
    <h1>[송림야담] 실제 오픈 노인/야담/구연 낭독자 원음 청음실</h1>
    <p class="sub">기계음이 전혀 없는 100% 실제 사람(이야기꾼·성우)의 호흡, 억양, 성대 질감이 담긴 오픈 레퍼런스 음원 (총 6분 10초)</p>
  </div>

  <div class="info-box">
    <div class="info-title">💡 기술적 안내: 왜 Edge-TTS + RVC는 기계음으로 들렸을까요?</div>
    <div class="info-desc">
      RVC는 '목소리 껍데기(음색 주파수)'만 바꾸는 기술입니다. 바탕이 된 Edge-TTS의 <strong>일정한 억양(Flat Cadence)과 인공지능 특유의 규칙적인 음절 박자</strong>가 그대로 남아있어 뇌에서 '기계음'으로 인지하게 됩니다.<br>
      아래 실제 사람의 낭독 음원들을 들어보시고 가장 마음에 드는 톤을 선택해주시면, <strong>이 사람의 호흡과 연기 억양 자체를 1:1로 복제하는 모델(Zero-Shot Voice Cloning / F5-TTS)</strong>을 통해 120개 슬라이드 전체를 진짜 사람 낭독으로 생성해 드립니다.
    </div>
  </div>

  <div class="track-list" id="trackList"></div>
</div>

<script>
const tracks = {tracks_json};
const container = document.getElementById('trackList');

tracks.forEach((t, idx) => {{
  const card = document.createElement('div');
  card.className = 'track-card' + (idx === 0 ? ' active' : '');
  
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
print(f"🎉 실제 육성 청음실 플레이어 생성 완료: {HTML_PATH}")
