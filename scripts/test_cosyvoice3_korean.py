#!/usr/bin/env python3
"""
Fun-CosyVoice 3.0 (한국어 공식 지원 모델) Zero-Shot & Cross-Lingual 음성 복제
────────────────────────────────────────────────────────────────────────────
- 모델: Fun-CosyVoice3-0.5B-2512
- 프롬프트: ref_songrim_clean_10s.wav (BGM 제거 10.15초 원음)
- 대본: 슬라이드 1번 문장 및 초단문 테스트
"""
import sys, os, time, base64, subprocess, io
for attr in ("stdout", "stderr"):
    s = getattr(sys, attr)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, attr, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path
import soundfile as sf
import torch

PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
COSYVOICE_DIR = PROJECT_ROOT / "third_party" / "CosyVoice"
MATCHA_DIR = COSYVOICE_DIR / "third_party" / "Matcha-TTS"
MODEL_DIR = COSYVOICE_DIR / "pretrained_models" / "Fun-CosyVoice3-0.5B"
OUT_DIR = PROJECT_ROOT / "output" / "cosyvoice3_korean_results"

sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))
OUT_DIR.mkdir(parents=True, exist_ok=True)

REF_WAV = PROJECT_ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"
PROMPT_TEXT = "You are a helpful assistant.<|endofprompt|>빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."

TEST_TEXT_1 = "You are a helpful assistant.<|endofprompt|>안녕하세요, 테스트 음성입니다."
TEST_TEXT_2 = "You are a helpful assistant.<|endofprompt|>옛날 옛적 한양 북촌 명문가의 어질고 고왔던 윤 씨 마님이, 하루아침에 억울한 누명을 쓰고 깊은 산골로 내쫓기고 말았더랬지요."

from cosyvoice.cli.cosyvoice import AutoModel

print("=" * 65)
print(" 🚀 Fun-CosyVoice 3.0 한국어 공식 음성 합성 시작")
print("=" * 65)

cosyvoice = AutoModel(model_dir=str(MODEL_DIR), fp16=True)
print(f"✔ 모델 로드 성공 (SR: {cosyvoice.sample_rate}Hz)")

# 테스트 1: 초단문
print("\n▶ [테스트 1] 초단문 합성: '안녕하세요, 테스트 음성입니다.'")
t0 = time.time()
chunks1 = []
for out in cosyvoice.inference_zero_shot(TEST_TEXT_1, PROMPT_TEXT, str(REF_WAV), stream=False, text_frontend=False):
    chunks1.append(out["tts_speech"])

if chunks1:
    audio1 = torch.cat(chunks1, dim=1)
    dur1 = audio1.shape[-1] / cosyvoice.sample_rate
    elapsed1 = time.time() - t0
    wav1 = OUT_DIR / "01_cosyvoice3_초단문.wav"
    mp31 = OUT_DIR / "01_cosyvoice3_초단문.mp3"
    sf.write(str(wav1), audio1.cpu().numpy().squeeze(), cosyvoice.sample_rate, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-i", str(wav1), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp31)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✔ 완료: {dur1:.1f}초 (소요: {elapsed1:.1f}초, RTF: {elapsed1/dur1:.2f}x)")

# 테스트 2: 슬라이드 1번 본 대본
print("\n▶ [테스트 2] 슬라이드 1번 대본 합성")
t0 = time.time()
chunks2 = []
for out in cosyvoice.inference_zero_shot(TEST_TEXT_2, PROMPT_TEXT, str(REF_WAV), stream=False, text_frontend=False):
    chunks2.append(out["tts_speech"])

if chunks2:
    audio2 = torch.cat(chunks2, dim=1)
    dur2 = audio2.shape[-1] / cosyvoice.sample_rate
    elapsed2 = time.time() - t0
    wav2 = OUT_DIR / "02_cosyvoice3_슬라이드1.wav"
    mp32 = OUT_DIR / "02_cosyvoice3_슬라이드1.mp3"
    sf.write(str(wav2), audio2.cpu().numpy().squeeze(), cosyvoice.sample_rate, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-i", str(wav2), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp32)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✔ 완료: {dur2:.1f}초 (소요: {elapsed2:.1f}초, RTF: {elapsed2/dur2:.2f}x)")

# HTML 플레이어 생성
def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

ref_b64 = b64(REF_WAV)
mp31_b64 = b64(mp31) if mp31.exists() else ""
mp32_b64 = b64(mp32) if mp32.exists() else ""

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Fun-CosyVoice 3.0 한국어 공식 음성 합성 결과</title>
    <style>
        body {{ background:#0b0f19; color:#e6edf3; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; padding:30px; }}
        .container {{ max-width:860px; margin:0 auto; }}
        .card {{ background:#161b22; border:1px solid #30363d; border-radius:12px; padding:20px; margin-bottom:15px; }}
        .ref {{ border-color:#d29922; margin-bottom:24px; }}
        .badge {{ background:#238636; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; }}
    </style>
</head>
<body>
<div class="container">
    <h1 style="color:#58a6ff;font-size:24px;margin-bottom:6px;">🎉 Fun-CosyVoice 3.0 한국어 공식 합성 결과</h1>
    <p style="color:#8b949e;font-size:14px;margin-bottom:24px;">
        한국어 정식 학습 모델(Fun-CosyVoice3-0.5B-2512) 기반 제로샷 음성 복제
    </p>

    <div class="card ref">
        <strong style="color:#d29922;">🎧 레퍼런스 원음 (ref_songrim_clean_10s.wav)</strong>
        <p style="font-size:14px;color:#c9d1d9;background:#0d1117;padding:10px;border-radius:8px;margin-top:8px;">
            "빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."
        </p>
        <audio controls style="width:100%;margin-top:10px;" src="data:audio/wav;base64,{ref_b64}"></audio>
    </div>

    <div class="card">
        <h3 style="margin-top:0;color:#7ee787;font-size:16px;">
            01. 초단문 테스트 <span class="badge">한국어 정식 모델</span>
        </h3>
        <p style="font-size:12px;color:#8b949e;">⏱️ 재생 시간: {dur1:.1f}초 | ⚡ 합성 소요: {elapsed1:.1f}초</p>
        <p style="font-size:14px;color:#c9d1d9;background:#0d1117;padding:10px;border-radius:8px;">
            "안녕하세요, 테스트 음성입니다."
        </p>
        <audio controls style="width:100%;margin-top:10px;" src="data:audio/mp3;base64,{mp31_b64}"></audio>
    </div>

    <div class="card">
        <h3 style="margin-top:0;color:#f778ba;font-size:16px;">
            02. 슬라이드 1번 본 대본 <span class="badge">야담 복제</span>
        </h3>
        <p style="font-size:12px;color:#8b949e;">⏱️ 재생 시간: {dur2:.1f}초 | ⚡ 합성 소요: {elapsed2:.1f}초</p>
        <p style="font-size:14px;color:#c9d1d9;background:#0d1117;padding:10px;border-radius:8px;">
            "옛날 옛적 한양 북촌 명문가의 어질고 고왔던 윤 씨 마님이, 하루아침에 억울한 누명을 쓰고 깊은 산골로 내쫓기고 말았더랬지요."
        </p>
        <audio controls style="width:100%;margin-top:10px;" src="data:audio/mp3;base64,{mp32_b64}"></audio>
    </div>
</div>
</body>
</html>"""

player_path = PROJECT_ROOT / "output" / "cosyvoice3_player.html"
with open(player_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n🌐 플레이어 생성 완료: {player_path}")
