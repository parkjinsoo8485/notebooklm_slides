import os, sys, subprocess
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import torch
import numpy as np
import soundfile as sf
from TTS.api import TTS

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
SOURCE_AUDIO = WORKSPACE / "output" / "human_voice_showcase" / "03_elderly_grandfather_folklore.mp3"
REF_WAV = WORKSPACE / "references" / "grandfather_ref.wav"
OUT_DIR = WORKSPACE / "output" / "slide01_grandfather_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. 트랙 02번 할아버지 음원에서 가장 자애롭고 정갈한 낭독 구간 14초 추출 (24kHz 모노)
print("✂️ [Step 1] 트랙 02 할아버지 전래동화 레퍼런스 음원(14초) 추출 중...")
subprocess.run([
    "ffmpeg", "-y", "-i", str(SOURCE_AUDIO),
    "-ss", "20", "-t", "14",
    "-ar", "24000", "-ac", "1",
    str(REF_WAV)
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"   ✅ 레퍼런스 추출 완료: {REF_WAV.name}")

# 2. 슬라이드 01 대본
RAW_SCRIPT = "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이 하루아침에 억울한 역모의 누명을 쓰고 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. 차가운 달빛조차 서럽게 얼어붙던 어느 쓸쓸한 늦가을 밤의 비극이었답니다."

# 3. XTTS-v2 Zero-Shot Voice Cloning (할아버지 말투/호흡 1:1 합성)
print("\n🧠 [Step 2] XTTS-v2 신경망 모델로 할아버지 목소리/말투 1:1 복제 합성 중...")
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

xtts_raw_wav = OUT_DIR / "slide_001_grandfather_xtts_raw.wav"
tts.tts_to_file(
    text=RAW_SCRIPT,
    speaker_wav=str(REF_WAV),
    language="ko",
    file_path=str(xtts_raw_wav),
    temperature=0.72,
    repetition_penalty=2.0
)
print(f"   ✅ XTTS-v2 할아버지 복제 생성 완료: {xtts_raw_wav.name}")

# 4. 스튜디오 아날로그 마스터링 (따뜻하고 포근한 노인 흉성 EQ)
xtts_mastered_mp3 = OUT_DIR / "slide_001_grandfather_xtts_mastered.mp3"
af_filter = (
    "equalizer=f=110:width_type=o:width=1.2:g=3.0,"     # 포근하고 깊은 할아버지 저음
    "equalizer=f=3500:width_type=o:width=1.0:g=-2.5,"   # 귀를 자극하는 거친 고역 완화
    "equalizer=f=7500:width_type=o:width=1.0:g=1.2,"    # 부드러운 숨결 에어감
    "compand=attacks=0.06:decays=0.25:points=-80/-80|-24/-20|-10/-8|0/-1:soft-knee=4,"
    "volume=1.2"
)

subprocess.run([
    "ffmpeg", "-y", "-i", str(xtts_raw_wav),
    "-af", af_filter,
    "-b:a", "320k",
    str(xtts_mastered_mp3)
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

print(f"✨ [Step 3] 최종 할아버지 마스터 음원 완성: {xtts_mastered_mp3.name}")
