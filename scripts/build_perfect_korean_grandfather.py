import asyncio
import os
import sys
import subprocess
from pathlib import Path
import json
import base64

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import edge_tts
import soundfile as sf
import librosa
import torch

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.append(str((WORKSPACE / "scripts").resolve()))
from rvc_engine import RVCStandaloneInfer

OUT_DIR = WORKSPACE / "output" / "slide01_grandfather_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 슬라이드 01 대본 (한국어 표준 구연)
SCRIPT_TEXT = "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."

async def build_all():
    print("=" * 70)
    print(" 🎙️ 트랙 02 할아버지 전래동화 구연 한국어 마스터 음원 생성")
    print("=" * 70)

    # 1. 한국어 전용 신경망 베이스 생성
    # 현수 (중후한 남성)
    out_hyunsu = OUT_DIR / "base_hyunsu.mp3"
    comm1 = edge_tts.Communicate(SCRIPT_TEXT, "ko-KR-HyunsuMultilingualNeural", rate="-14%")
    await comm1.save(str(out_hyunsu))
    print("   ✅ 현수 신경망 생성 완료")

    # 인준 (지적이고 차분한 남성)
    out_injoon = OUT_DIR / "base_injoon.mp3"
    comm2 = edge_tts.Communicate(SCRIPT_TEXT, "ko-KR-InJoonNeural", rate="-12%")
    await comm2.save(str(out_injoon))
    print("   ✅ 인준 신경망 생성 완료")

    # 순희 (따뜻한 여성/어머니 톤)
    out_sunhi = OUT_DIR / "base_sunhi.mp3"
    comm3 = edge_tts.Communicate(SCRIPT_TEXT, "ko-KR-SunHiNeural", rate="-16%")
    await comm3.save(str(out_sunhi))
    print("   ✅ 순희 신경망 생성 완료")

    # 2. RVC v2 전문 낭독자 성대 이식
    print("\n🧠 [Step 2] RVC v2 전문 낭독자 성대 이식 중...")
    rvc_model = WORKSPACE / "models" / "rvc" / "JK_Narrator" / "model.pth"
    rvc_index = WORKSPACE / "models" / "rvc" / "JK_Narrator" / "model.index"
    engine = RVCStandaloneInfer(model_path=rvc_model, index_path=rvc_index if rvc_index.exists() else None)

    # Hyunsu -> RVC
    rvc_hyunsu_wav = OUT_DIR / "rvc_hyunsu.wav"
    engine.convert(input_wav_path=out_hyunsu, output_wav_path=rvc_hyunsu_wav, f0_up_key=0, index_rate=0.6)

    # InJoon -> RVC
    rvc_injoon_wav = OUT_DIR / "rvc_injoon.wav"
    engine.convert(input_wav_path=out_injoon, output_wav_path=rvc_injoon_wav, f0_up_key=0, index_rate=0.6)

    # 3. 트랙 02 할아버지의 따뜻한 흉성/세월의 연륜 진공관 마스터링
    def master_grandfather(in_audio, out_mp3, pitch_n=-0.8, low_g=4.5):
        temp_wav = OUT_DIR / f"temp_{Path(out_mp3).stem}.wav"
        if pitch_n != 0:
            y, sr = librosa.load(str(in_audio), sr=24000)
            y_shift = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_n)
            sf.write(str(temp_wav), y_shift, sr, subtype='PCM_16')
            target = temp_wav
        else:
            target = in_audio

        af = (
            f"equalizer=f=120:width_type=o:width=1.2:g={low_g}dB,"
            "equalizer=f=800:width_type=o:width=1.0:g=+2.0dB,"
            "equalizer=f=3400:width_type=o:width=1.0:g=-3.5dB,"
            "equalizer=f=7500:width_type=o:width=1.2:g=+1.5dB,"
            "compand=attacks=0.06:decays=0.25:points=-80/-80|-26/-20|-10/-7|0/-1.2:soft-knee=6,"
            "volume=1.25"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", str(target),
            "-af", af,
            "-b:a", "320k",
            str(out_mp3)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if temp_wav.exists():
            temp_wav.unlink()

    # 트랙 1: [최고 강력 추천 A] 중후한 할아버지의 구수한 전래동화 구연 (Hyunsu + RVC 성대 이식 + Grandfather EQ)
    opt1_mp3 = OUT_DIR / "slide_001_opt1_grandfather_deep.mp3"
    master_grandfather(rvc_hyunsu_wav, opt1_mp3, pitch_n=-0.8, low_g=4.5)

    # 트랙 2: [강력 추천 B] 자애롭고 정갈한 할아버지의 회상 낭독 (InJoon + RVC 성대 이식 + Grandfather EQ)
    opt2_mp3 = OUT_DIR / "slide_001_opt2_grandfather_calm.mp3"
    master_grandfather(rvc_injoon_wav, opt2_mp3, pitch_n=-0.5, low_g=3.5)

    # 트랙 3: [고전 정통 남성 구연] 현수 신경망 + 아날로그 웜 마스터링
    opt3_mp3 = OUT_DIR / "slide_001_opt3_korean_classic.mp3"
    master_grandfather(out_hyunsu, opt3_mp3, pitch_n=-0.4, low_g=4.0)

    # 트랙 4: [따뜻한 할머니/어머니 톤] 순희 신경망 + 아날로그 웜 마스터링
    opt4_mp3 = OUT_DIR / "slide_001_opt4_grandmother_warm.mp3"
    master_grandfather(out_sunhi, opt4_mp3, pitch_n=0, low_g=2.5)

    print("\n🎉 모든 교정 음원 생성 완료!")

    # 4. 플레이어 HTML 빌드
    def to_b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

    REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "03_elderly_grandfather_folklore.mp3"

    tracks = [
        {
            "badge": "👑 강력 추천 A: 중후한 할아버지 구연",
            "name": "👴 [슬라이드 01] 중후하고 구수한 할아버지 옛이야기 구연",
            "desc": "100% 또렷한 한국어 발음 + RVC 성대 이식 + 트랙 02 할아버지의 세월과 연륜이 묻어나는 깊은 흉성",
            "duration": "00:23",
            "b64": to_b64(opt1_mp3),
            "highlight": True
        },
        {
            "badge": "✨ 강력 추천 B: 자애로운 할아버지 낭독",
            "name": "📖 [슬라이드 01] 자애롭고 정갈한 할아버지 회상 낭독",
            "desc": "손주에게 들려주듯 차분하고 또박또박 감정을 실어 낭독하는 포근한 할아버지 톤",
            "duration": "00:22",
            "b64": to_b64(opt2_mp3),
            "highlight": True
        },
        {
            "badge": "🎙️ 고전 정통 구연",
            "name": "📜 [슬라이드 01] 정통 고전 판소리/야담 남성 구연",
            "desc": "선명한 한국어 딕션과 묵직한 호흡의 정통 고전 구연 톤",
            "duration": "00:23",
            "b64": to_b64(opt3_mp3),
            "highlight": False
        },
        {
            "badge": "👵 따뜻한 할머니/어머니",
            "name": "👵 [슬라이드 01] 따뜻한 할머니의 옛날이야기 구연",
            "desc": "포근하고 정감 넘치는 옛날 할머니 구연동화 톤",
            "duration": "00:24",
            "b64": to_b64(opt4_mp3),
            "highlight": False
        },
        {
            "badge": "📻 원본 레퍼런스 육성",
            "name": "👴 [참조] 트랙 02 할아버지 실제 육성 원음",
            "desc": "세월의 연륜과 구수한 호흡의 실제 할아버지 음원 (2분 30초)",
            "duration": "02:30",
            "b64": to_b64(REF_GRANDFATHER),
            "highlight": False
        }
    ]

    tracks_json = json.dumps(tracks, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 한국어 100% 완벽 교정 - 트랙 02 할아버지 구연 슬라이드 01 청음실</title>
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
  background: rgba(16, 185, 129, 0.2);
  color: var(--emerald);
  border: 1px solid var(--emerald);
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
  background: rgba(26, 38, 66, 0.96);
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
    <div class="tag">🇰🇷 100% NATIVE KOREAN RESTORATION</div>
    <h1>[송림야담] 한국어 네이티브 완벽 교정 할아버지 구연 슬라이드 01</h1>
    <p class="sub">어눌한 외국어식 발음을 완벽히 걷어내고, 또렷한 100% 표준 한국어 딕션 위에 트랙 02 할아버지의 구수한 연륜과 성대를 완벽 결합했습니다.</p>
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

    html_path = WORKSPACE / "output" / "slide01_grandfather_player.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"🎉 최종 교정 청음실 HTML 업데이트 완료: {html_path}")

if __name__ == "__main__":
    asyncio.run(build_all())
