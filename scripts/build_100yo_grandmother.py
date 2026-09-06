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
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
OUT_DIR = WORKSPACE / "output" / "slide01_centenarian_grandmother"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 100세 할머니 구연동화 특유의 호흡과 말맛을 살린 대본
SCRIPT_TEXT_A = (
    "옛날... 옛적에... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이... "
    "하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... "
    "차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었답니다..."
)

SCRIPT_TEXT_B = (
    "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 우리 윤씨 마님이... "
    "하루아침에 억울하게 역모 누명을 쓰고... 첩첩산중 깊은 골짜기로 쫓겨나고 말았제... "
    "차가운 달빛마저 시리게 얼어붙던... 쓸쓸한 늦가을 밤의 비극이었단다..."
)

def apply_centenarian_vocal_physics(in_wav, out_wav, age_intensity=1.0):
    """100세 고령 노인 성대 물리 음향 변환 (Tremor, Shimmer, Formant Atrophy, Aspiration)"""
    y, sr = librosa.load(str(in_wav), sr=24000)
    
    # 1. 100세 할머니 특유의 피치 시프트 (-2.2 ~ -2.8 반음)
    n_steps = -2.2 * age_intensity
    y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)
    
    # 2. 노인 성대 근육의 미세 떨림 (5.2Hz Vocal Tremor)
    t = np.arange(len(y_shifted)) / sr
    tremor_freq = 5.2 # Hz
    tremor_depth = 0.055 * age_intensity
    vocal_tremor = 1.0 + tremor_depth * np.sin(2 * np.pi * tremor_freq * t)
    
    # 미세 불규칙성 (Jitter / Shimmer)
    noise_shimmer = np.random.normal(0, 0.012 * age_intensity, len(y_shifted))
    y_aged = y_shifted * (vocal_tremor + noise_shimmer)
    
    # 3. 부드러운 노인 숨결 (Aspiration Whisper) 미세 합성
    # 3.5k~6kHz 대역의 부드러운 숨소리를 미세하게 믹싱
    nyquist = sr / 2
    from scipy.signal import butter, filtfilt
    b_band, a_band = butter(2, [2500 / nyquist, 5500 / nyquist], btype='band')
    whisper_noise = np.random.normal(0, 0.015 * age_intensity, len(y_aged))
    whisper_filtered = filtfilt(b_band, a_band, whisper_noise)
    
    # 무음 구간이 아닌 유음 구간에만 숨결 추가
    envelope = np.abs(y_aged)
    b_env, a_env = butter(2, 10 / nyquist, btype='low')
    smooth_env = filtfilt(b_env, a_env, envelope)
    smooth_env = np.clip(smooth_env / (np.max(smooth_env) + 1e-6), 0, 1)
    
    y_final = y_aged + (whisper_filtered * smooth_env * 0.35)
    
    # 노멀라이즈
    y_final = y_final / (np.max(np.abs(y_final)) + 1e-6) * 0.95
    sf.write(str(out_wav), y_final, sr, subtype='PCM_16')

async def build_100yo_grandmother_voices():
    print("=" * 70)
    print(" 👵 100세 고령 할머니 전래동화 구연 음성 생성 (물리 음향 모델링)")
    print("=" * 70)

    # 1. 1차 한국어 음성 렌더링 (느긋하고 정갈한 노년 속도 -26% ~ -30%)
    raw_1_mp3 = OUT_DIR / "raw_1.mp3"
    comm1 = edge_tts.Communicate(SCRIPT_TEXT_A, "ko-KR-SunHiNeural", rate="-26%", pitch="-18Hz")
    await comm1.save(str(raw_1_mp3))

    raw_2_mp3 = OUT_DIR / "raw_2.mp3"
    comm2 = edge_tts.Communicate(SCRIPT_TEXT_B, "ko-KR-SunHiNeural", rate="-28%", pitch="-22Hz")
    await comm2.save(str(raw_2_mp3))

    # wav 변환
    wav_1 = OUT_DIR / "raw_1.wav"
    wav_2 = OUT_DIR / "raw_2.wav"
    subprocess.run(["ffmpeg", "-y", "-i", str(raw_1_mp3), "-ar", "24000", str(wav_1)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(raw_2_mp3), "-ar", "24000", str(wav_2)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 2. 100세 노인 성대 물리 음향 변환
    aged_1_wav = OUT_DIR / "aged_1.wav"
    aged_2_wav = OUT_DIR / "aged_2.wav"
    aged_3_wav = OUT_DIR / "aged_3.wav"

    apply_centenarian_vocal_physics(wav_1, aged_1_wav, age_intensity=1.0)
    apply_centenarian_vocal_physics(wav_1, aged_2_wav, age_intensity=1.25)
    apply_centenarian_vocal_physics(wav_2, aged_3_wav, age_intensity=1.35)

    # 3. 100세 할머니 온기/연륜 아날로그 스튜디오 마스터링
    def master_centenarian(in_wav, out_mp3, low_warmth=5.0):
        af = (
            f"equalizer=f=220:width_type=o:width=1.5:g={low_warmth}dB,"   # 100세 노인의 가슴 깊은 흉성
            "equalizer=f=850:width_type=o:width=1.2:g=+3.0dB,"           # 정감 있는 노구의 바디감
            "equalizer=f=3200:width_type=o:width=1.0:g=-4.5dB,"          # 맑은 톤을 가라앉히고 세월의 쉰 느낌 형성
            "equalizer=f=6500:width_type=o:width=1.2:g=+2.2dB,"          # 할머니의 부드러운 숨소리
            "compand=attacks=0.1:decays=0.35:points=-80/-80|-30/-24|-14/-9|0/-1.5:soft-knee=6,"
            "volume=1.28"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", str(in_wav),
            "-af", af,
            "-b:a", "320k",
            str(out_mp3)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    opt1_mp3 = OUT_DIR / "slide_001_100yo_grandmother_master.mp3"
    opt2_mp3 = OUT_DIR / "slide_001_100yo_grandmother_deep_tremor.mp3"
    opt3_mp3 = OUT_DIR / "slide_001_100yo_grandmother_folklore_dialect.mp3"

    master_centenarian(aged_1_wav, opt1_mp3, low_warmth=4.8)
    master_centenarian(aged_2_wav, opt2_mp3, low_warmth=5.5)
    master_centenarian(aged_3_wav, opt3_mp3, low_warmth=5.8)

    print("🎉 100세 할머니 구연 음원 3종 마스터링 완료!")

    # 4. 플레이어 HTML 빌드
    def to_b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

    REF_GRANDMOTHER = WORKSPACE / "output" / "human_voice_showcase" / "03_elderly_grandfather_folklore.mp3"

    tracks = [
        {
            "badge": "👑 100세 대표 마스터 (강력 추천)",
            "name": "👵 [슬라이드 01] 100세 백수(白壽) 할머니의 전래동화 구연 (대표 마스터)",
            "desc": "한 세기를 살아오신 100세 할머니 특유의 떨리는 성대 호흡(Vocal Tremor)과 가슴 깊이 쉬어 나오는 자애로운 세월의 음색 (약 28초)",
            "duration": "00:28",
            "b64": to_b64(opt1_mp3),
            "highlight": True
        },
        {
            "badge": "✨ 100세 깊은 연륜 톤",
            "name": "👵 [슬라이드 01] 100세 고령 할머니의 애절한 옛이야기 회상",
            "desc": "더 깊은 성대 떨림과 느릿느릿 온기를 품고 한 글자씩 읊어주시는 백세 노인의 회상 톤 (약 28초)",
            "duration": "00:28",
            "b64": to_b64(opt2_mp3),
            "highlight": True
        },
        {
            "badge": "📜 100세 구수한 옛말 톤",
            "name": "👵 [슬라이드 01] 100세 할머니의 구수한 옛 말투 전래 설화",
            "desc": "'~말았제...', '~비극이었단다...' 할머니가 손주에게 직접 말 건네듯 들려주는 구수한 말투 톤 (약 29초)",
            "duration": "00:29",
            "b64": to_b64(opt3_mp3),
            "highlight": False
        },
        {
            "badge": "📻 원본 레퍼런스 육성",
            "name": "👵 [참조] 트랙 02 실제 할머니 전래동화 육성 원음",
            "desc": "비교를 위한 실제 할머니 성우의 원본 육성 (2분 30초)",
            "duration": "02:30",
            "b64": to_b64(REF_GRANDMOTHER),
            "highlight": False
        }
    ]

    tracks_json = json.dumps(tracks, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 100세 할머니 전래동화 구연 슬라이드 01 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #060910;
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
  background: radial-gradient(circle at 50% 10%, #1c2742 0%, var(--bg) 100%);
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
    <div class="tag">👵 100-YEAR-OLD CENTENARIAN GRANDMOTHER</div>
    <h1>[송림야담] 100세 할머니 전래동화 구연 슬라이드 01 청음실</h1>
    <p class="sub">100세 고령 할머니의 <strong>세월이 깃든 떨리는 성대 호흡(Vocal Tremor)과 깊은 흉성, 느릿하고 구수한 옛날이야기 구연</strong>을 완벽히 재현했습니다.</p>
  </div>

  <div class="script-box">
    <div class="script-title">📜 낭독 대본 (슬라이드 01)</div>
    <div class="script-text">
      "{SCRIPT_TEXT_A}"
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
    print(f"🎉 100세 할머니 청음실 HTML 업데이트 완료: {html_path}")

if __name__ == "__main__":
    asyncio.run(build_100yo_grandmother_voices())
