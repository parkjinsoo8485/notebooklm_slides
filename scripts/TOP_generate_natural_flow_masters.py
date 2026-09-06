#!/usr/bin/env python3
"""
generate_natural_flow_masters.py
────────────────────────────────
[문장 연결 & 쉼표 호흡 완전 정상화]
불필요한 쉼표와 말줄임표를 전면 제거하고,
전문 방송 성우의 물 흐르듯 유려한 완급 조절과 자연스러운 문장 연결을 완성한 마스터.
"""
import sys, os, io, json, subprocess, asyncio
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path
import edge_tts
import whisper

PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
OUT_DIR = PROJECT_ROOT / "output" / "natural_flow_masters"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 인위적 쉼표와 말줄임표를 완전 제거한 [자연스러운 성우 낭독 대본]
NATURAL_SCRIPT = "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이 하루아침에 억울한 역모의 누명을 쓰고 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."

PRESETS = [
    {
        "id": "1_injoon_natural_master",
        "badge": "👑 1번 추천: 중후한 원로 남성 성우 (자연스러운 완급)",
        "name": "1. [중후한 원로 남성 성우 - 물 흐르듯 유려한 야담 낭독]",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-20%",
        "filter": (
            "equalizer=f=120:width_type=o:width=1.2:g=3.8,"
            "equalizer=f=280:width_type=o:width=1.4:g=2.2,"
            "equalizer=f=3500:width_type=o:width=1.0:g=-3.0,"
            "highshelf=f=6000:g=-2.5,"
            "aecho=0.8:0.6:20|35:0.08|0.04,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        ),
        "desc": "끊김 없이 문장이 자연스럽게 이어지며, 60~70대 어르신이 가장 편안하게 몰입할 수 있는 묵직한 원로 성우 톤"
    },
    {
        "id": "2_sunhi_natural_warm",
        "badge": "💎 2번: 품격 있는 원로 여성 성우 (매끄러운 서사)",
        "name": "2. [품격 있는 원로 여성 성우 - 부드러운 고전 낭독]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-20%",
        "filter": (
            "equalizer=f=190:width_type=o:width=1.3:g=4.0,"
            "equalizer=f=450:width_type=o:width=1.4:g=2.0,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "highshelf=f=6500:g=-3.0,"
            "aecho=0.8:0.6:22|38:0.10|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        ),
        "desc": "어색한 쉼 없이 부드럽게 문맥을 살려 낭독하는 기품 있는 원로 여성 성우 톤"
    },
    {
        "id": "3_hyunsu_calm_story",
        "badge": "📜 3번: 차분한 남성 나레이터 (단정한 호흡)",
        "name": "3. [차분한 남성 나레이터 - 정통 역사 실록 톤]",
        "voice": "ko-KR-HyunsuMultilingualNeural",
        "rate": "-18%",
        "filter": (
            "equalizer=f=150:width_type=o:width=1.3:g=3.5,"
            "equalizer=f=350:width_type=o:width=1.2:g=1.8,"
            "equalizer=f=3800:width_type=o:width=1.0:g=-3.0,"
            "aecho=0.8:0.6:18|32:0.07|0.03,"
            "volume=1.20"
        ),
        "desc": "명료한 딕션과 정돈된 문장 연결로 역사 다큐멘터리의 신뢰감을 주는 톤"
    },
    {
        "id": "4_injoon_deep_midnight",
        "badge": "🌌 4번: 심야 비장 설화 (깊은 여운과 호흡)",
        "name": "4. [심야 비장 설화 마스터 - 느긋하고 비장한 낭독]",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-24%",
        "filter": (
            "equalizer=f=110:width_type=o:width=1.4:g=4.5,"
            "equalizer=f=3200:width_type=o:width=1.0:g=-4.0,"
            "highshelf=f=5500:g=-3.5,"
            "aecho=0.8:0.7:26|45:0.14|0.06,"
            "volume=1.30"
        ),
        "desc": "문맥을 해치지 않는 절제된 호흡과 깊은 여운으로 비극적 서사를 극대화한 심야 전설 톤"
    }
]

async def generate():
    print("🌊 [Natural Flow] 문장 연결 및 쉼표 정상화 음원 생성 시작...")
    whisper_model = whisper.load_model("base")
    tracks = []
    
    for p in PRESETS:
        raw_mp3 = OUT_DIR / f"raw_{p['id']}.mp3"
        master_mp3 = OUT_DIR / f"master_{p['id']}.mp3"
        
        # 자연스러운 대본으로 Edge TTS 생성
        comm = edge_tts.Communicate(NATURAL_SCRIPT, p["voice"], rate=p["rate"])
        await comm.save(str(raw_mp3))
        
        # FFmpeg 스튜디오 마스터링 DSP
        subprocess.run([
            "ffmpeg", "-y", "-i", str(raw_mp3),
            "-af", p["filter"],
            "-b:a", "320k",
            str(master_mp3)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if raw_mp3.exists():
            raw_mp3.unlink()
            
        # Whisper STT 검증
        stt_res = whisper_model.transcribe(str(master_mp3), language="ko")
        stt_text = stt_res["text"].strip()
        print(f"\n✨ [{p['name']}] 생성 완료")
        print(f"   📝 STT 실측: {stt_text}")
        
        import base64
        with open(master_mp3, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("ascii")
            
        tracks.append({
            "badge": p["badge"],
            "name": p["name"],
            "desc": p["desc"],
            "stt": stt_text,
            "b64": b64_str
        })
        
    # 플레이어 HTML 작성
    tracks_json = json.dumps(tracks, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 자연스러운 문장 연결 & 완급 조절 마스터 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #090c10;
  --card-bg: rgba(22, 29, 44, 0.88);
  --accent: #d97706;
  --accent-glow: rgba(217, 119, 6, 0.35);
  --green: #10b981;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --border: rgba(255, 255, 255, 0.12);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: radial-gradient(circle at 50% 10%, #1c2438 0%, var(--bg) 100%);
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
  padding: 6px 14px;
  background: rgba(16, 185, 129, 0.18);
  color: var(--green);
  border: 1px solid var(--green);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 12px;
}}
h1 {{
  font-family: 'Noto Serif KR', serif;
  font-size: 32px;
  font-weight: 900;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #fff 0%, #fde68a 50%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
p.sub {{
  color: var(--text-muted);
  font-size: 15px;
}}
.script-card {{
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 30px;
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}}
.script-title {{
  font-size: 13px;
  color: #fbbf24;
  font-weight: 800;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.script-text {{
  font-family: 'Noto Serif KR', serif;
  font-size: 18px;
  line-height: 1.9;
  color: #f1f5f9;
}}
.track-list {{
  display: flex;
  flex-direction: column;
  gap: 20px;
}}
.track-card {{
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}}
.track-card:hover, .track-card.active {{
  border-color: #fbbf24;
  transform: translateY(-2px);
  box-shadow: 0 12px 30px var(--accent-glow);
}}
.track-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}}
.track-badge {{
  font-size: 12px;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(217, 119, 6, 0.25);
  color: #fbbf24;
  border: 1px solid #fbbf24;
}}
.track-tag {{
  font-size: 12px;
  color: var(--green);
  font-weight: 700;
}}
.track-name {{
  font-size: 19px;
  font-weight: 800;
  margin-bottom: 6px;
  color: #fff;
}}
.track-desc {{
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 12px;
  line-height: 1.5;
}}
.stt-box {{
  background: rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: #fde68a;
  margin-bottom: 16px;
  border-left: 3px solid #fbbf24;
}}
audio {{
  width: 100%;
  border-radius: 8px;
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
    <div class="tag">🌊 NATURAL PHRASING & PROSODY</div>
    <h1>[송림야담] 자연스러운 문장 연결 & 완급 조절 청음실</h1>
    <p class="sub">어색한 쉼표 파편화 완전 제거 ➔ 물 흐르듯 이어지는 전문 방송 성우 호흡</p>
  </div>

  <div class="script-card">
    <div class="script-title">📜 적용 대본 (쉼표 파편화 제거 ➔ 자연 유연 호흡)</div>
    <div class="script-text">
      "{NATURAL_SCRIPT}"
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
      <span class="track-tag">✅ 자연스러운 문장 연결</span>
    </div>
    <div class="track-name">${{t.name}}</div>
    <div class="track-desc">${{t.desc}}</div>
    <div class="stt-box"><strong>실측 음성인식:</strong> "${{t.stt}}"</div>
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

    player_path = PROJECT_ROOT / "output" / "natural_storyteller_player.html"
    player_path.write_text(html_content, encoding="utf-8")
    print(f"\n🎉 자연스러운 문장 연결 플레이어 완성: {player_path}")

if __name__ == "__main__":
    asyncio.run(generate())
