#!/usr/bin/env python3
"""
CosyVoice2 한국어 Zero-Shot 합성 — 공식 AutoModel API 사용
────────────────────────────────────────────────────────────
example.py 분석으로 확인된 올바른 한국어 사용법:
  - cross_lingual 모드: <|ko|> 태그 + prompt_wav만 사용 (prompt_text 불필요)
  - zero_shot 모드:    prompt_text는 프롬프트 오디오 언어(한국어)여야 함
  - text_frontend=False: 외부 정규화 없이 그대로 모델에 전달
"""
import sys, os, time, base64, subprocess
from pathlib import Path
import soundfile as sf
import torch

# 경로 설정
PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
COSYVOICE_DIR = PROJECT_ROOT / "third_party" / "CosyVoice"
MATCHA_DIR = COSYVOICE_DIR / "third_party" / "Matcha-TTS"
MODEL_DIR = COSYVOICE_DIR / "pretrained_models" / "CosyVoice2-0.5B"
OUT_DIR = PROJECT_ROOT / "output" / "cosyvoice2_ko_official"

sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))
OUT_DIR.mkdir(parents=True, exist_ok=True)

REF_WAV = PROJECT_ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"
PROMPT_TEXT = "빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."

# 테스트용 초단문
TEST_TEXT = "안녕하세요, 테스트 음성입니다."

from cosyvoice.cli.cosyvoice import CosyVoice2

print("=" * 60)
print("  CosyVoice2 공식 API로 한국어 합성 테스트")
print("=" * 60)
print(f"  레퍼런스: {REF_WAV.name}")
print(f"  테스트 텍스트: {TEST_TEXT}")
print()

cosyvoice = CosyVoice2(str(MODEL_DIR), fp16=True)
print(f"  모델 로드 완료 (SR: {cosyvoice.sample_rate}Hz)")

results = []

# ── 방법 1: cross_lingual (<|ko|> 태그 + text_frontend=False) ──
print("\n[방법 1] inference_cross_lingual + <|ko|> + text_frontend=False")
t0 = time.time()
chunks1 = []
for out in cosyvoice.inference_cross_lingual(
        f"<|ko|>{TEST_TEXT}",
        str(REF_WAV),
        stream=False,
        text_frontend=False):
    chunks1.append(out["tts_speech"])

if chunks1:
    audio1 = torch.cat(chunks1, dim=1)
    dur1 = audio1.shape[-1] / cosyvoice.sample_rate
    elapsed1 = time.time() - t0
    wav1 = OUT_DIR / "05_cross_lingual_ko.wav"
    sf.write(str(wav1), audio1.cpu().numpy().squeeze(), cosyvoice.sample_rate, subtype="PCM_16")
    print(f"  ✔ 생성 완료: {dur1:.1f}초 오디오 (소요: {elapsed1:.1f}초)")
    results.append({"name": "05. cross_lingual + <|ko|>", "wav": wav1, "dur": dur1, "elapsed": elapsed1})
else:
    print("  ❌ 실패")

# ── 방법 2: zero_shot + 한국어 prompt_text + text_frontend=False ──
print("\n[방법 2] inference_zero_shot + 한국어 prompt_text + text_frontend=False")
t0 = time.time()
chunks2 = []
for out in cosyvoice.inference_zero_shot(
        TEST_TEXT,
        PROMPT_TEXT,
        str(REF_WAV),
        stream=False,
        text_frontend=False):
    chunks2.append(out["tts_speech"])

if chunks2:
    audio2 = torch.cat(chunks2, dim=1)
    dur2 = audio2.shape[-1] / cosyvoice.sample_rate
    elapsed2 = time.time() - t0
    wav2 = OUT_DIR / "06_zero_shot_ko_no_frontend.wav"
    sf.write(str(wav2), audio2.cpu().numpy().squeeze(), cosyvoice.sample_rate, subtype="PCM_16")
    print(f"  ✔ 생성 완료: {dur2:.1f}초 오디오 (소요: {elapsed2:.1f}초)")
    results.append({"name": "06. zero_shot + 한국어 prompt_text (text_frontend=False)", "wav": wav2, "dur": dur2, "elapsed": elapsed2})
else:
    print("  ❌ 실패")

# ── 방법 3: cross_lingual, text_frontend=True (정규화 적용) ──
print("\n[방법 3] inference_cross_lingual + <|ko|> + text_frontend=True (정규화)")
t0 = time.time()
chunks3 = []
for out in cosyvoice.inference_cross_lingual(
        f"<|ko|>{TEST_TEXT}",
        str(REF_WAV),
        stream=False,
        text_frontend=True):
    chunks3.append(out["tts_speech"])

if chunks3:
    audio3 = torch.cat(chunks3, dim=1)
    dur3 = audio3.shape[-1] / cosyvoice.sample_rate
    elapsed3 = time.time() - t0
    wav3 = OUT_DIR / "07_cross_lingual_with_frontend.wav"
    sf.write(str(wav3), audio3.cpu().numpy().squeeze(), cosyvoice.sample_rate, subtype="PCM_16")
    print(f"  ✔ 생성 완료: {dur3:.1f}초 오디오 (소요: {elapsed3:.1f}초)")
    results.append({"name": "07. cross_lingual + text_frontend=True", "wav": wav3, "dur": dur3, "elapsed": elapsed3})
else:
    print("  ❌ 실패")

print("\n모든 테스트 완료!")
for r in results:
    print(f"  - {r['name']}: {r['dur']:.1f}s (RTF: {r['elapsed']/r['dur']:.1f}x)")

# MP3 변환
for r in results:
    mp3 = r["wav"].with_suffix(".mp3")
    subprocess.run(["ffmpeg", "-y", "-i", str(r["wav"]), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r["mp3"] = mp3

# HTML 플레이어 생성
def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

ref_b64 = b64(REF_WAV)

cards = ""
for r in results:
    if r.get("mp3") and r["mp3"].exists():
        cards += f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:15px;">
            <h3 style="margin-top:0;color:#7ee787;font-size:16px;">{r['name']}</h3>
            <p style="font-size:12px;color:#8b949e;">⏱️ {r['dur']:.1f}초 | RTF: {r['elapsed']/r['dur']:.1f}x</p>
            <p style="font-size:14px;color:#c9d1d9;background:#0d1117;padding:10px;border-radius:8px;">"{TEST_TEXT}"</p>
            <audio controls style="width:100%;margin-top:8px;" src="data:audio/mp3;base64,{b64(r['mp3'])}"></audio>
        </div>"""

html = f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>CosyVoice2 공식 API 한국어 비교</title>
<style>body{{background:#0b0f19;color:#e6edf3;font-family:-apple-system,sans-serif;padding:30px;}}
.container{{max-width:860px;margin:0 auto;}}</style>
</head>
<body><div class="container">
<h1 style="color:#58a6ff;font-size:22px;margin-bottom:6px;">🎙️ CosyVoice2 공식 API 한국어 3가지 방법 비교</h1>
<p style="color:#8b949e;font-size:13px;margin-bottom:24px;">AutoModel → CosyVoice2 공식 경로 사용 (이전 커스텀 엔진 폐기)</p>

<div style="background:#161b22;border:1px solid #d29922;border-radius:12px;padding:18px;margin-bottom:24px;">
    <strong style="color:#d29922;">🎧 레퍼런스 원음 (ref_songrim_clean_10s.wav)</strong>
    <p style="font-size:14px;color:#c9d1d9;background:#0d1117;padding:10px;border-radius:8px;">
        "{PROMPT_TEXT}"
    </p>
    <audio controls style="width:100%;margin-top:10px;" src="data:audio/wav;base64,{ref_b64}"></audio>
</div>
{cards}
</div></body></html>"""

player = PROJECT_ROOT / "output" / "cosyvoice2_strategy_player.html"
with open(player, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n플레이어 생성: {player}")
