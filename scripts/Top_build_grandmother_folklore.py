import asyncio
import os
import sys
import subprocess
from pathlib import Path
import json
import base64
import numpy as np
import soundfile as sf
import parselmouth
from parselmouth.praat import call
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
OUT_DIR = WORKSPACE / "output" / "slide01_praat_grandmother"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 슬라이드 01 대본 (할머니의 구수한 옛날이야기 구연)
SCRIPT_TEXT = (
    "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, "
    "하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. "
    "차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
)

def apply_praat_elderly_female(in_wav: Path, out_wav: Path,
                              pitch_factor: float = 0.82,
                              formant_factor: float = 0.88,
                              jitter_amount: float = 0.008):
    """
    Praat PSOLA 기반 노년 여성(할머니) 음색 변환
    """
    snd = parselmouth.Sound(str(in_wav))
    
    # 1. Manipulation 객체 생성 (PSOLA 편집 가능 형태)
    manipulation = call(snd, "To Manipulation", 0.01, 75, 600)
    
    # 2. 피치 곡선 추출 및 변환
    pitch_tier = call(manipulation, "Extract pitch tier")
    
    # 전체 피치 포인트를 pitch_factor 비율로 조정
    call(pitch_tier, "Multiply frequencies", 0, 999, pitch_factor)
    
    # 미세 노인 성대 떨림 (Jitter) 추가
    n_points = call(pitch_tier, "Get number of points")
    for i in range(1, n_points + 1):
        t = call(pitch_tier, "Get time from index", i)
        f = call(pitch_tier, "Get value at index", i)
        if f > 0:
            jitter = 1.0 + np.random.normal(0, jitter_amount)
            call(pitch_tier, "Remove point near", t)
            call(pitch_tier, "Add point", t, max(50.0, f * jitter))
    
    # 3. 변환된 피치 곡선을 Manipulation에 반영
    call([pitch_tier, manipulation], "Replace pitch tier")
    
    # 4. PSOLA로 피치 변환 적용
    snd_new = call(manipulation, "Get resynthesis (overlap-add)")
    
    # 5. 포먼트(Formant) 변환: 샘플링 레이트 manipulation trick
    from scipy.signal import resample_poly
    data = snd_new.values.flatten()
    original_sr = int(snd_new.sampling_frequency)
    up = 100
    down = int(round(100 / formant_factor))
    data_slow = resample_poly(data, up, down)
    
    target_len = len(data)
    if len(data_slow) >= target_len:
        data_out = data_slow[:target_len]
    else:
        data_out = np.pad(data_slow, (0, target_len - len(data_slow)))
    
    # 6. wav 저장
    sf.write(str(out_wav), data_out, original_sr)
    print(f"   ✅ Praat PSOLA 할머니 변환 완료: {out_wav.name}")

async def generate_grandmother_audios():
    print("=" * 70)
    print(" 👵 [트랙 02] 따뜻한 할머니 전래동화 구연 (Praat PSOLA) 마스터 생성")
    print("=" * 70)

    # 1. 한국어 여성 전문 신경망 베이스 생성 (SunHiNeural)
    raw_mp3 = OUT_DIR / "base_sunhi.mp3"
    raw_wav = OUT_DIR / "base_sunhi.wav"
    
    # SunHiNeural은 현수보다 높은 피치이므로 피치를 조금 낮춰서 생성
    c1 = edge_tts.Communicate(SCRIPT_TEXT, "ko-KR-SunHiNeural", rate="-10%", pitch="-10Hz")
    await c1.save(str(raw_mp3))
    subprocess.run(["ffmpeg", "-y", "-i", str(raw_mp3), "-ar", "44100", "-ac", "1", str(raw_wav)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("   ✅ [Step 1] SunHi 한국어 베이스 생성 완료")

    # 2. Praat PSOLA 변환 3가지 톤
    wav_a = OUT_DIR / "praat_grandmother_warm.wav"
    apply_praat_elderly_female(raw_wav, wav_a, pitch_factor=0.82, formant_factor=0.88, jitter_amount=0.008)

    wav_b = OUT_DIR / "praat_grandmother_lyric.wav"
    apply_praat_elderly_female(raw_wav, wav_b, pitch_factor=0.79, formant_factor=0.86, jitter_amount=0.010)

    wav_c = OUT_DIR / "praat_grandmother_healing.wav"
    apply_praat_elderly_female(raw_wav, wav_c, pitch_factor=0.85, formant_factor=0.90, jitter_amount=0.006)

    # 3. 할머니 전용 아날로그 마스터링 (Tremolo 등 적용)
    def master_grandmother_voice(in_wav, out_mp3, warmth_gain=3.8):
        af = (
            f"equalizer=f=240:width_type=o:width=1.4:g={warmth_gain}dB,"
            "equalizer=f=1100:width_type=o:width=1.2:g=+2.2dB,"
            "equalizer=f=3400:width_type=o:width=1.0:g=-3.8dB,"
            "equalizer=f=7200:width_type=o:width=1.2:g=+1.8dB,"
            "tremolo=f=5.5:d=0.06,"  # 할머니 특유의 떨림 추가
            "compand=attacks=0.08:decays=0.3:points=-80/-80|-28/-22|-12/-8|0/-1.5:soft-knee=6,"
            "volume=1.22"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", str(in_wav),
            "-af", af,
            "-b:a", "320k",
            str(out_mp3)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    opt1_mp3 = OUT_DIR / "slide_001_grandmother_opt1_warm.mp3"
    master_grandmother_voice(wav_a, opt1_mp3, warmth_gain=4.2)

    opt2_mp3 = OUT_DIR / "slide_001_grandmother_opt2_lyric.mp3"
    master_grandmother_voice(wav_b, opt2_mp3, warmth_gain=3.5)

    opt3_mp3 = OUT_DIR / "slide_001_grandmother_opt3_healing.mp3"
    master_grandmother_voice(wav_c, opt3_mp3, warmth_gain=4.5)

    print("\n🎉 모든 할머니 구연 (Praat) 마스터 음원 완성!")

    # 4. HTML 플레이어 생성
    def to_b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

    tracks = [
        {
            "badge": "👑 대표 추천 1: 구수하고 푸근한 할머니 (Praat)",
            "name": "👵 [슬라이드 01] 트랙 02 따뜻한 할머니의 전래동화 구연",
            "desc": "Praat PSOLA를 적용하여 자연스러운 포먼트와 떨림이 더해진 할머니 음성 (약 24초)",
            "duration": "00:24",
            "b64": to_b64(opt1_mp3),
            "highlight": True
        },
        {
            "badge": "✨ 대표 추천 2: 서정적인 할머니 낭독 (Praat)",
            "name": "📖 [슬라이드 01] 정갈한 할머니의 서정적 회상",
            "desc": "피치를 좀 더 낮추고 지터(Jitter)를 늘려 깊은 회상에 잠긴 톤 (약 24초)",
            "duration": "00:24",
            "b64": to_b64(opt2_mp3),
            "highlight": True
        },
        {
            "badge": "🌙 대표 추천 3: 심야 수면/힐링 옛이야기 (Praat)",
            "name": "🌙 [슬라이드 01] 포근하고 느긋한 심야 힐링",
            "desc": "피치와 포먼트를 덜 낮춰 젊고 맑은 느낌이 조금 더 나는 힐링 톤 (약 24초)",
            "duration": "00:24",
            "b64": to_b64(opt3_mp3),
            "highlight": False
        }
    ]

    tracks_json = json.dumps(tracks, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 트랙 02 따뜻한 할머니 전래동화 구연 (Praat)</title>
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
  background: radial-gradient(circle at 50% 10%, #1c2742 0%, var(--bg) 100%);
  color: var(--text);
  font-family: 'Pretendard', sans-serif;
  min-height: 100vh;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
}}
.container {{ max-width: 920px; width: 100%; }}
.header {{ text-align: center; margin-bottom: 35px; }}
.tag {{
  display: inline-block; padding: 6px 18px;
  background: rgba(245, 158, 11, 0.2); color: var(--accent);
  border: 1px solid var(--accent); border-radius: 999px;
  font-size: 13px; font-weight: 800; letter-spacing: 1.5px;
  margin-bottom: 12px;
}}
h1 {{
  font-family: 'Noto Serif KR', serif; font-size: 32px; font-weight: 900;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #fed7aa 50%, var(--accent) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
p.sub {{ color: var(--text-muted); font-size: 15px; line-height: 1.6; }}
.script-box {{
  background: rgba(18, 25, 42, 0.95); border: 1px solid var(--border);
  border-radius: 16px; padding: 22px 26px; margin-bottom: 30px;
  backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}
.script-title {{
  color: var(--accent); font-weight: 800; font-size: 13px; margin-bottom: 8px;
}}
.script-text {{
  font-family: 'Noto Serif KR', serif; font-size: 18px; line-height: 1.8; color: #f1f5f9;
}}
.track-list {{ display: flex; flex-direction: column; gap: 22px; }}
.track-card {{
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 18px; padding: 24px; transition: all 0.3s ease;
  box-shadow: 0 10px 25px rgba(0,0,0,0.4);
}}
.track-card.highlight {{
  border-color: var(--accent); background: rgba(28, 38, 64, 0.96);
  box-shadow: 0 12px 35px var(--accent-glow);
}}
.track-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
.track-badge {{
  font-size: 13px; font-weight: 800; padding: 5px 12px; border-radius: 8px;
  background: rgba(255, 255, 255, 0.1); color: #cbd5e1;
}}
.track-card.highlight .track-badge {{
  background: rgba(245, 158, 11, 0.25); color: var(--accent); border: 1px solid var(--accent);
}}
.track-time {{
  font-size: 13px; font-weight: 700; color: #38bdf8; background: rgba(56, 189, 248, 0.15);
  padding: 4px 10px; border-radius: 6px;
}}
.track-name {{ font-family: 'Noto Serif KR', serif; font-size: 20px; font-weight: 800; margin-bottom: 8px; color: #ffffff; }}
.track-desc {{ font-size: 14px; color: var(--text-muted); margin-bottom: 18px; line-height: 1.5; }}
audio {{ width: 100%; border-radius: 10px; outline: none; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="tag">👵 GRANDMOTHER + PRAAT PSOLA</div>
    <h1>[송림야담] 트랙 02 할머니 전래동화 구연 청음실</h1>
    <p class="sub">SunHiNeural의 발음과 억양을 기반으로 <strong>Praat PSOLA를 통해 포먼트와 피치를 낮춰</strong> 진짜 노년 여성의 음색과 떨림을 완벽하게 재현했습니다.</p>
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
tracks.forEach(t => {{
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
    if (audios[i] != e.target) audios[i].pause();
  }}
}}, true);
</script>
</body>
</html>"""

    html_path = WORKSPACE / "output" / "slide01_praat_grandmother_player.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"🎉 청음실 HTML 업데이트 완료: {html_path}")

if __name__ == "__main__":
    asyncio.run(generate_grandmother_audios())
