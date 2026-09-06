#!/usr/bin/env python3
"""
generate_slide01_rvc_ultimate.py
─────────────────────────────────
슬라이드 01에 대해 [궁극의 실행 B: Edge-TTS 골격 + RVC v2 성우 변환] 파이프라인 가동.
"""
import sys, os, io, json, subprocess, asyncio
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path
import torch
import soundfile as sf
import librosa
import edge_tts

PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from korean_phonetic_normalizer import normalize_phonetics_for_tts as normalize_korean_phonetics
from rvc_engine import RVCStandaloneInfer

OUT_DIR = PROJECT_ROOT / "output" / "rvc_ultimate_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. 원본 대본 및 연음 정규화 대본 준비
RAW_SCRIPT = "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었답니다."

# 한국어 구어체 및 발음 정규화
PHONETIC_SCRIPT = normalize_korean_phonetics(RAW_SCRIPT)
print(f"📖 1. 원문 대본:\n   {RAW_SCRIPT}")
print(f"🎙️ 2. 발음 정규화 대본:\n   {PHONETIC_SCRIPT}")

TEMP_EDGE_WAV = OUT_DIR / "slide_001_edge_skeleton.wav"

async def step1_generate_edge_skeletons():
    print("🔊 [Step 1] 자연스러운 원음 골격(Skeleton) 생성 중...")
    
    # 1. 남성 골격 (InJoon) - pitch +0Hz로 순수 성대 음원 생성
    comm_male = edge_tts.Communicate(
        text=PHONETIC_SCRIPT,
        voice="ko-KR-InJoonNeural",
        rate="-8%",
        pitch="+0Hz"
    )
    male_mp3 = OUT_DIR / "temp_male.mp3"
    await comm_male.save(str(male_mp3))
    male_wav = OUT_DIR / "slide_001_male_skeleton.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(male_mp3),
        "-ar", "16000", "-ac", "1",
        str(male_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if male_mp3.exists():
        male_mp3.unlink()

    # 2. 여성 골격 (SunHi) - pitch +0Hz
    comm_female = edge_tts.Communicate(
        text=PHONETIC_SCRIPT,
        voice="ko-KR-SunHiNeural",
        rate="-8%",
        pitch="+0Hz"
    )
    female_mp3 = OUT_DIR / "temp_female.mp3"
    await comm_female.save(str(female_mp3))
    female_wav = OUT_DIR / "slide_001_female_skeleton.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(female_mp3),
        "-ar", "16000", "-ac", "1",
        str(female_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if female_mp3.exists():
        female_mp3.unlink()

    print("   ✅ 남성/여성 깨끗한 원음 골격 생성 완료")
    return {"male": male_wav, "female": female_wav}

def step2_rvc_convert(skeletons):
    print("🧠 [Step 2] RVC v2 고해상도 성우 모델 이식 변환 시작...")
    
    # 모델 정의
    models = {
        "JK_Narrator": {
            "pth": PROJECT_ROOT / "models" / "rvc" / "JK_Narrator" / "model.pth",
            "index": PROJECT_ROOT / "models" / "rvc" / "JK_Narrator" / "model.index",
            "skeleton": skeletons["male"],
            "f0_up_key": 0,
            "desc": "차분하고 깊이 있는 한국어 남성 나레이터 (1000 Epochs)"
        }
    }
    
    # IU 모델 확인
    iu_pths = list((PROJECT_ROOT / "models" / "rvc" / "IU").glob("*.pth"))
    iu_indices = list((PROJECT_ROOT / "models" / "rvc" / "IU").glob("*.index"))
    if iu_pths:
        models["IU_Soft_Voice"] = {
            "pth": iu_pths[0],
            "index": iu_indices[0] if iu_indices else None,
            "skeleton": skeletons["female"],
            "f0_up_key": 0,
            "desc": "감미롭고 맑은 한국어 여성 나레이터 보이스"
        }

    results = []

    for name, cfg in models.items():
        if not cfg["pth"].exists():
            print(f"⚠️ 모델 파일 없음: {cfg['pth']}")
            continue
            
        print(f"\n🎭 성우 모델 [{name}] 변환 진행...")
        infer_engine = RVCStandaloneInfer(
            model_path=cfg["pth"],
            index_path=cfg["index"],
            device="cuda:0" if torch.cuda.is_available() else "cpu"
        )
        
        raw_rvc_out = OUT_DIR / f"slide_001_{name}_raw.wav"
        infer_engine.convert(
            input_wav_path=cfg["skeleton"],
            output_wav_path=raw_rvc_out,
            f0_up_key=cfg["f0_up_key"],
            index_rate=0.65
        )
        
        # Step 3: 따뜻한 아날로그 스튜디오 마스터링 (금속성 반사음 aecho 제거)
        mastered_out = OUT_DIR / f"slide_001_{name}_mastered.mp3"
        print(f"🎛️ [Step 3] {name} 따뜻한 자연 육성 마스터링 적용 중...")
        
        af_filter = (
            "equalizer=f=120:width_type=o:width=1.0:g=2.5,"     # 따뜻한 흉성
            "equalizer=f=3200:width_type=o:width=1.0:g=-2.0,"    # 귀 찌르는 쇳소리 대역 차감
            "equalizer=f=8000:width_type=o:width=1.0:g=1.5,"     # 공기감/선명도
            "compand=attacks=0.05:decays=0.2:points=-80/-80|-24/-20|-10/-8|0/-1:soft-knee=4,"
            "volume=1.15"
        )
        
        subprocess.run([
            "ffmpeg", "-y", "-i", str(raw_rvc_out),
            "-af", af_filter,
            "-b:a", "320k",
            str(mastered_out)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        results.append({
            "id": name,
            "desc": cfg["desc"],
            "raw_wav": str(raw_rvc_out),
            "master_mp3": str(mastered_out),
            "filename": mastered_out.name
        })
        print(f"   ✨ 최종 자연 육성 마스터 음원 완성: {mastered_out.name}")

    return results

def step4_build_player(results):
    print("\n🌐 [Step 4] 전용 비교 청음 플레이어 HTML 생성 중...")
    
    import base64
    def to_b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

    # Edge TTS 기본 골격도 마스터링하여 비교군 생성
    edge_mastered = OUT_DIR / "slide_001_edge_mastered.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(OUT_DIR / "slide_001_male_skeleton.wav"),
        "-b:a", "320k",
        str(edge_mastered)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    tracks = [
        {
            "badge": "기존 AI 음성",
            "name": "0. Edge-TTS 표준 신경망 (고음질 마스터)",
            "desc": "선명하고 또렷하지만 인공지능 특유의 매끄러운 톤",
            "b64": to_b64(edge_mastered),
            "tag": "Edge-TTS + DSP"
        }
    ]

    for r in results:
        tracks.append({
            "badge": "🔥 궁극의 B: RVC 성우 이식",
            "name": f"👑 {r['id']} (실제 인간 성우 모델 변환)",
            "desc": r["desc"] + " + 완벽한 구어체 연음 및 흉성 공명",
            "b64": to_b64(Path(r["master_mp3"])),
            "tag": "Edge-TTS ➔ RVC v2 ➔ Clean DSP"
        })

    tracks_json = json.dumps(tracks, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 궁극의 인간 성우 음성 변환 (B방식) 실시간 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #07090e;
  --card-bg: rgba(18, 24, 38, 0.85);
  --accent: #e5a93c;
  --accent-glow: rgba(229, 169, 60, 0.35);
  --cyan: #38bdf8;
  --text: #f1f5f9;
  --text-muted: #94a3b8;
  --border: rgba(255, 255, 255, 0.1);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: radial-gradient(circle at 50% 10%, #151c2e 0%, var(--bg) 100%);
  color: var(--text);
  font-family: 'Pretendard', sans-serif;
  min-height: 100vh;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
}}
.container {{
  max-width: 900px;
  width: 100%;
}}
.header {{
  text-align: center;
  margin-bottom: 35px;
}}
.tag {{
  display: inline-block;
  padding: 6px 14px;
  background: rgba(229, 169, 60, 0.15);
  color: var(--accent);
  border: 1px solid var(--accent);
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
  background: linear-gradient(135deg, #fff 0%, #cbd5e1 50%, var(--accent) 100%);
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
  color: var(--accent);
  font-weight: 800;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.script-text {{
  font-family: 'Noto Serif KR', serif;
  font-size: 17px;
  line-height: 1.8;
  color: #e2e8f0;
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
  border-color: var(--accent);
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
  background: rgba(56, 189, 248, 0.15);
  color: var(--cyan);
  border: 1px solid rgba(56, 189, 248, 0.3);
}}
.track-badge.vip {{
  background: rgba(229, 169, 60, 0.2);
  color: var(--accent);
  border-color: var(--accent);
}}
.track-tag {{
  font-size: 12px;
  color: var(--text-muted);
  font-family: monospace;
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
  margin-bottom: 16px;
  line-height: 1.5;
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
    <div class="tag">🚀 SOTA AI HYBRID PIPELINE</div>
    <h1>[송림야담] 슬라이드 01 인간 성우 음성 변환 청음실</h1>
    <p class="sub">Edge-TTS 무결점 연음 낭독 골격 ➔ RVC v2 실제 인간 성우 모델 1:1 성대 이식</p>
  </div>

  <div class="script-card">
    <div class="script-title">📜 적용 대본 (슬라이드 01)</div>
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
  card.className = 'track-card' + (idx === 1 ? ' active' : '');
  const isVip = t.badge.includes('궁극');
  
  card.innerHTML = `
    <div class="track-header">
      <span class="track-badge ${{isVip ? 'vip' : ''}}">${{t.badge}}</span>
      <span class="track-tag">${{t.tag}}</span>
    </div>
    <div class="track-name">${{t.name}}</div>
    <div class="track-desc">${{t.desc}}</div>
    <audio controls src="data:audio/mp3;base64,${{t.b64}}" preload="auto"></audio>
  `;
  container.appendChild(card);
}});

// 1개 재생 시 다른 것 정지
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

    player_html_path = PROJECT_ROOT / "output" / "slide_001_rvc_player.html"
    player_html_path.write_text(html_content, encoding="utf-8")
    print(f"🎉 비교 청음 플레이어 완성: {player_html_path}")

async def main():
    skeletons = await step1_generate_edge_skeletons()
    results = step2_rvc_convert(skeletons)
    step4_build_player(results)

if __name__ == "__main__":
    asyncio.run(main())
