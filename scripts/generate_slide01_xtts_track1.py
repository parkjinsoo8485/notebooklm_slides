import os, sys, subprocess
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import torch
from TTS.api import TTS

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
SOURCE_AUDIO = WORKSPACE / "output" / "human_voice_showcase" / "02_authentic_yadam_storyteller.mp3"
REF_WAV = WORKSPACE / "references" / "yadam_track1_ref.wav"
OUT_DIR = WORKSPACE / "output" / "slide01_xtts_cloned"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. 트랙 1번에서 가장 깨끗하고 구수한 낭독 구간 12초 추출 (22050Hz 모노)
print("✂️ [Step 1] 트랙 1번 조선 야담 이야기꾼 레퍼런스 음원(12초) 추출 중...")
subprocess.run([
    "ffmpeg", "-y", "-i", str(SOURCE_AUDIO),
    "-ss", "15", "-t", "12",
    "-ar", "22050", "-ac", "1",
    str(REF_WAV)
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"   ✅ 레퍼런스 준비 완료: {REF_WAV.name}")

# 2. XTTS-v2 모델 로드 (CUDA 가속)
print("\n🧠 [Step 2] XTTS-v2 Voice Cloning 신경망 모델 로딩 중 (CUDA)...")
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# 3. 슬라이드 01 대본 합성
RAW_SCRIPT = "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이 하루아침에 억울한 역모의 누명을 쓰고 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. 차가운 달빛조차 서럽게 얼어붙던 어느 쓸쓸한 늦가을 밤의 비극이었답니다."

print(f"\n🎙️ [Step 3] 트랙 1번 이야기꾼 말투/호흡으로 슬라이드 01 생성 중...")
out_wav = OUT_DIR / "slide_001_xtts_track1_raw.wav"

tts.tts_to_file(
    text=RAW_SCRIPT,
    speaker_wav=str(REF_WAV),
    language="ko",
    file_path=str(out_wav),
    temperature=0.75,
    repetition_penalty=2.0
)
print(f"   ✅ XTTS-v2 원음 생성 완료: {out_wav.name}")

# 4. 스튜디오 마스터링 (자연스러운 흉성/에어감)
final_mp3 = OUT_DIR / "slide_001_track1_yadam_mastered.mp3"
subprocess.run([
    "ffmpeg", "-y", "-i", str(out_wav),
    "-af", "compand=attacks=0.05:decays=0.2:points=-80/-80|-24/-20|-10/-8|0/-1:soft-knee=4,volume=1.2",
    "-b:a", "320k",
    str(final_mp3)
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

print(f"✨ [Step 4] 최종 완성: {final_mp3.name}")
