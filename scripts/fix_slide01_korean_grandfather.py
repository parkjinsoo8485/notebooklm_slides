import asyncio
import os
import sys
import subprocess
from pathlib import Path
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
OUT_DIR = WORKSPACE / "output" / "slide01_grandfather_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 슬라이드 01 대본: 구연동화의 맛과 연륜을 정밀하게 살린 호흡 텍스트
TEXT = (
    "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, "
    "하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... "
    "차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
)

async def generate_base_korean_voice(out_mp3):
    print("🎙️ [Step 1] 완벽한 한국어 네이티브 신경망 구연 음성 합성 중...")
    communicate = edge_tts.Communicate(
        text=TEXT,
        voice="ko-KR-BongJinNeural",
        rate="-15%",
        pitch="-3Hz"
    )
    await communicate.save(str(out_mp3))
    print(f"   ✅ 한국어 베이스 생성 완료: {out_mp3.name}")

def apply_grandfather_acoustic_morphing(in_wav, out_wav):
    print("\n👴 [Step 2] 트랙 02 할아버지 성대 포먼트/연륜 질감(Acoustic Morphing) 이식 중...")
    y, sr = librosa.load(in_wav, sr=24000)
    
    # 1. 피치 -1.2 반음 시프트 (중후하고 깊은 노인 흉성)
    y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=-1.2)
    
    # 2. 미세 노인 호흡 떨림
    t = np.arange(len(y_shifted)) / sr
    tremolo = 1.0 + 0.035 * np.sin(2 * np.pi * 4.5 * t)
    y_trem = y_shifted * tremolo
    
    sf.write(out_wav, y_trem, sr, subtype='PCM_16')
    print(f"   ✅ 음향 모핑 완료: {Path(out_wav).name}")

def master_grandfather_audio(in_wav, out_mp3):
    print("\n✨ [Step 3] 아날로그 진공관 따뜻한 할아버지 음색 최종 마스터링...")
    af_filter = (
        "equalizer=f=120:width_type=o:width=1.5:g=4.0,"
        "equalizer=f=900:width_type=o:width=1.2:g=2.5,"
        "equalizer=f=3400:width_type=o:width=1.0:g=-4.0,"
        "equalizer=f=7500:width_type=o:width=1.2:g=1.8,"
        "compand=attacks=0.08:decays=0.3:points=-80/-80|-28/-22|-12/-8|0/-1.5:soft-knee=6,"
        "volume=1.25"
    )
    
    subprocess.run([
        "ffmpeg", "-y", "-i", str(in_wav),
        "-af", af_filter,
        "-b:a", "320k",
        str(out_mp3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   🎉 최종 할아버지 낭독 완성: {Path(out_mp3).name}")

async def main():
    base_mp3 = OUT_DIR / "slide_001_base_korean.mp3"
    base_wav = OUT_DIR / "slide_001_base_korean.wav"
    morphed_wav = OUT_DIR / "slide_001_grandfather_morphed.wav"
    final_master_mp3 = OUT_DIR / "slide_001_grandfather_fixed_master.mp3"
    
    await generate_base_korean_voice(base_mp3)
    
    subprocess.run(["ffmpeg", "-y", "-i", str(base_mp3), "-ar", "24000", str(base_wav)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    apply_grandfather_acoustic_morphing(base_wav, morphed_wav)
    master_grandfather_audio(morphed_wav, final_master_mp3)
    print("\n✅ 모든 생성 및 교정 작업이 완료되었습니다!")

if __name__ == "__main__":
    asyncio.run(main())
