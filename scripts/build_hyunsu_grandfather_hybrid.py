import asyncio
import os
import sys
import subprocess
from pathlib import Path
import json
import base64
import numpy as np
import soundfile as sf
import librosa
import torch
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.append(str((WORKSPACE / "scripts").resolve()))
from rvc_engine import RVCStandaloneInfer

OUT_DIR = WORKSPACE / "output" / "slide01_hyunsu_grandfather_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 슬라이드 01 대본 (한국어 표준 딕션)
SCRIPT_TEXT = "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 쫓겨나고 말았습니다. 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었습니다."

async def build_hyunsu_grandfather_hybrid():
    print("=" * 70)
    print(" 👴 [현수 딕션 + RVC 성대 이식] 할아버지 마스터 음성 생성")
    print("=" * 70)

    # 1. 현수(Hyunsu) 100% 완벽한 한국어 딕션 베이스 생성
    raw_hyunsu_mp3 = OUT_DIR / "base_hyunsu.mp3"
    comm = edge_tts.Communicate(SCRIPT_TEXT, "ko-KR-HyunsuMultilingualNeural", rate="-16%", pitch="-10Hz")
    await comm.save(str(raw_hyunsu_mp3))
    print("   ✅ [Step 1] 현수 100% 한국어 네이티브 딕션 베이스 생성 완료")

    # 2. RVC v2 성대 질감 변환
    print("\n🧠 [Step 2] RVC v2 신경망으로 성대 질감 변환 중...")
    rvc_model = WORKSPACE / "models" / "rvc" / "JK_Narrator" / "model.pth"
    rvc_index = WORKSPACE / "models" / "rvc" / "JK_Narrator" / "model.index"

    engine = RVCStandaloneInfer(model_path=rvc_model, index_path=rvc_index if rvc_index.exists() else None)
    
    # 기본 RVC 성대 변환
    rvc_wav = OUT_DIR / "rvc_hyunsu.wav"
    engine.convert(input_wav_path=raw_hyunsu_mp3, output_wav_path=rvc_wav, f0_up_key=0, index_rate=0.6)
    print("   ✅ [Step 2] RVC 성대 변환 완료")

    # 3. 할아버지 세월의 연륜 및 흉성 물리 음향 마스터링 (3가지 톤)
    print("\n✨ [Step 3] 할아버지 음색 전용 아날로그 마스터링...")

    def master_to_grandfather(in_wav, out_mp3, pitch_steps=-1.0, low_boost=4.5, trem_depth=0.03):
        # 1) 피치 시프트 & 미세 성대 연륜 호흡
        y, sr = librosa.load(str(in_wav), sr=24000)
        if pitch_steps != 0:
            y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_steps)
        
        # 미세 노인 호흡 떨림 (Flutter)
        if trem_depth > 0:
            t = np.arange(len(y)) / sr
            tremolo = 1.0 + trem_depth * np.sin(2 * np.pi * 5.0 * t)
            y = y * tremolo

        temp_wav = OUT_DIR / f"temp_{Path(out_mp3).stem}.wav"
        sf.write(str(temp_wav), y, sr, subtype='PCM_16')

        # 2) 진공관 웜 EQ & 할아버지 흉성 강화
        af = (
            f"equalizer=f=125:width_type=o:width=1.3:g={low_boost}dB,"   # 깊고 묵직한 할아버지 흉성
            "equalizer=f=850:width_type=o:width=1.1:g=+2.5dB,"          # 따뜻한 목소리 몸통감
            "equalizer=f=3400:width_type=o:width=1.0:g=-3.5dB,"         # 디지털 치찰음/금속성 억제
            "equalizer=f=7500:width_type=o:width=1.2:g=+1.8dB,"         # 부드러운 노인 숨결 에어감
            "compand=attacks=0.08:decays=0.3:points=-80/-80|-28/-22|-12/-8|0/-1.5:soft-knee=6,"
            "volume=1.25"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", str(temp_wav),
            "-af", af,
            "-b:a", "320k",
            str(out_mp3)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        if temp_wav.exists():
            temp_wav.unlink()

    # 옵션 1: [대표 추천 A] 중후하고 구수한 할아버지 옛이야기 구연
    opt1_mp3 = OUT_DIR / "slide_001_opt1_grandfather_deep.mp3"
    master_to_grandfather(rvc_wav, opt1_mp3, pitch_steps=-1.2, low_boost=5.0, trem_depth=0.035)

    # 옵션 2: [대표 추천 B] 자애롭고 정갈한 백발 할아버지 낭독
    opt2_mp3 = OUT_DIR / "slide_001_opt2_grandfather_calm.mp3"
    master_to_grandfather(rvc_wav, opt2_mp3, pitch_steps=-0.8, low_boost=4.0, trem_depth=0.02)

    # 옵션 3: [고전 야담] 묵직한 고전 판소리/야담 남성 해설
    opt3_mp3 = OUT_DIR / "slide_001_opt3_classic_storyteller.mp3"
    master_to_grandfather(rvc_wav, opt3_mp3, pitch_steps=-0.4, low_boost=4.5, trem_depth=0.0)

    # 옵션 4: [비교용] 현수 원본 스튜디오 마스터
    opt4_mp3 = OUT_DIR / "slide_001_opt4_raw_hyunsu.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(raw_hyunsu_mp3),
        "-af", "equalizer=f=200:width_type=o:width=1.3:g=3.5,equalizer=f=3400:width_type=o:width=1.2:g=-2.5,volume=1.18",
        "-b:a", "320k", str(opt4_mp3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print("\n🎉 모든 할아버지 하이브리드 음원 생성 완료!")

    # 4. HTML 플레이어 빌드
    def to_b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

    tracks = [
        {
            "badge": "👑 대표 추천 A: 중후하고 구수한 할아버지",
            "name": "👴 [슬라이드 01] 현수 딕션 + 중후한 할아버지 옛이야기 구연",
            "desc": "현수(Hyunsu)의 100% 완벽한 한국어 발음 + RVC 성대 이식 + 깊은 흉성(-1.2반음, 125Hz 흉성 강화)의 구수한 정통 할아버지 구연",
            "duration": "00:22",
            "b64": to_b64(opt1_mp3),
            "highlight": True
        },
        {
            "badge": "✨ 대표 추천 B: 자애롭고 정갈한 할아버지",
            "name": "📖 [슬라이드 01] 현수 딕션 + 자애로운 백발 할아버지 낭독",
            "desc": "손주에게 들려주듯 차분하고 온화한 어조로 한 글자 한 글자 정갈하게 낭독하는 백발 할아버지 톤",
            "duration": "00:22",
            "b64": to_b64(opt2_mp3),
            "highlight": True
        },
        {
            "badge": "🎙️ 고전 판소리/야담 해설",
            "name": "📜 [슬라이드 01] 현수 딕션 + 묵직한 고전 판소리/야담 해설 톤",
            "desc": "선명하고 단단한 중저음의 딕션으로 비장미와 몰입감을 이끄는 정통 고전 해설 톤",
            "duration": "00:21",
            "b64": to_b64(opt3_mp3),
            "highlight": False
        },
        {
            "badge": "🌐 현수 원본 베이스 (비교용)",
            "name": "🎙️ [슬라이드 01] 현수 원본 스튜디오 마스터 음성",
            "desc": "성대 변환 전의 순수 HyunsuMultilingualNeural 스튜디오 웜톤 원음",
            "duration": "00:20",
            "b64": to_b64(opt4_mp3),
            "highlight": False
        }
    ]

    tracks_json = json.dumps(tracks, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 현수 딕션 + RVC 할아버지 성대 이식 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #070a11;
  --card-bg: rgba(18, 25, 42, 0.92);
  --accent: #f59e0b;
  --accent-glow: rgba(245, 158, 11, 0.4);
  --emerald: #10b981;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --border: rgba(255, 255, 255, 0.12);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: radial-gradient(circle at 50% 10%, #17243e 0%, var(--bg) 100%);
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
  background: linear-gradient(135deg, #ffffff 0%, #fed7aa 50%, var(--accent) 100%);
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
  background: rgba(28, 38, 64, 0.96);
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
    <div class="tag">👴 HYUNSU + RVC HYBRID VOCAL ENGINE</div>
    <h1>[송림야담] 현수 딕션 + RVC 할아버지 성대 이식 청음실</h1>
    <p class="sub"><strong>현수(Hyunsu)의 100% 완벽한 한국어 딕션과 억양</strong> 위에 <strong>RVC v2 신경망으로 할아버지의 구수한 성대와 흉성</strong>을 1:1 이식했습니다.</p>
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

    html_path = WORKSPACE / "output" / "slide01_hyunsu_grandfather_player.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"🎉 청음실 HTML 업데이트 완료: {html_path}")

if __name__ == "__main__":
    asyncio.run(build_hyunsu_grandfather_hybrid())
