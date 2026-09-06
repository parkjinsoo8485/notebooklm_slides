import asyncio
import os
import sys
import subprocess
from pathlib import Path
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

OUT_DIR = WORKSPACE / "output" / "slide01_grandfather_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. 자연스러운 구연동화 호흡의 한국어 대본
KOREAN_TEXT = (
    "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, "
    "하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. "
    "차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
)

async def generate_korean_voices():
    print("🎙️ [Step 1] 한국어 네이티브 전문 신경망 음원 생성 중...")
    
    # A. 봉진 (중후하고 묵직한 구연)
    raw_bongjin = OUT_DIR / "raw_bongjin.mp3"
    c1 = edge_tts.Communicate(KOREAN_TEXT, voice="ko-KR-BongJinNeural", rate="-14%")
    await c1.save(str(raw_bongjin))
    print("   ✅ 봉진 신경망 생성 완료")

    # B. 인준 (지적이고 차분한 낭독)
    raw_injoon = OUT_DIR / "raw_injoon.mp3"
    c2 = edge_tts.Communicate(KOREAN_TEXT, voice="ko-KR-InJoonNeural", rate="-12%")
    await c2.save(str(raw_injoon))
    print("   ✅ 인준 신경망 생성 완료")

    # C. 순희 (따뜻한 할머니/이야기꾼)
    raw_sunhi = OUT_DIR / "raw_sunhi.mp3"
    c3 = edge_tts.Communicate(KOREAN_TEXT, voice="ko-KR-SunHiNeural", rate="-12%")
    await c3.save(str(raw_sunhi))
    print("   ✅ 순희 신경망 생성 완료")

def apply_rvc_and_mastering():
    raw_bongjin = OUT_DIR / "raw_bongjin.mp3"
    raw_injoon = OUT_DIR / "raw_injoon.mp3"
    raw_sunhi = OUT_DIR / "raw_sunhi.mp3"

    print("\n🧠 [Step 2] RVC v2 전문 낭독자 성대 이식 중...")
    rvc_model = WORKSPACE / "models" / "rvc" / "JK_Narrator" / "model.pth"
    rvc_index = WORKSPACE / "models" / "rvc" / "JK_Narrator" / "model.index"

    engine = RVCStandaloneInfer(model_path=rvc_model, index_path=rvc_index if rvc_index.exists() else None)

    # 1. BongJin -> RVC 성대 이식
    rvc_bongjin_wav = OUT_DIR / "rvc_bongjin.wav"
    engine.convert(input_wav_path=raw_bongjin, output_wav_path=rvc_bongjin_wav, f0_up_key=0, index_rate=0.6)

    # 2. InJoon -> RVC 성대 이식
    rvc_injoon_wav = OUT_DIR / "rvc_injoon.wav"
    engine.convert(input_wav_path=raw_injoon, output_wav_path=rvc_injoon_wav, f0_up_key=0, index_rate=0.6)

    # 3. 트랙 02 할아버지 전용 아날로그 마스터링
    print("\n✨ [Step 3] 트랙 02 할아버지 세월/연륜 아날로그 마스터링 중...")
    
    def master_audio(in_file, out_mp3, pitch_shift_semitones=-1.0, low_boost=4.5):
        # 1) 피치 시프트 (필요시 깊은 노인 흉성 추가)
        temp_wav = OUT_DIR / "temp_pitch.wav"
        if pitch_shift_semitones != 0:
            y, sr = librosa.load(str(in_file), sr=24000)
            y_shift = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift_semitones)
            sf.write(str(temp_wav), y_shift, sr, subtype='PCM_16')
            target_in = temp_wav
        else:
            target_in = in_file

        # 2) 진공관 EQ & 아날로그 컴프레서
        af_filter = (
            f"equalizer=f=120:width_type=o:width=1.2:g={low_boost}dB,"
            "equalizer=f=800:width_type=o:width=1.0:g=+2.0dB,"
            "equalizer=f=3400:width_type=o:width=1.0:g=-3.5dB,"
            "equalizer=f=7500:width_type=o:width=1.2:g=+1.5dB,"
            "compand=attacks=0.06:decays=0.25:points=-80/-80|-26/-20|-10/-7|0/-1.2:soft-knee=6,"
            "volume=1.2"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", str(target_in),
            "-af", af_filter,
            "-b:a", "320k",
            str(out_mp3)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if temp_wav.exists():
            temp_wav.unlink()

    # 트랙 A: [최고 완성도] 중후한 할아버지의 구수한 전래동화 구연 (BongJin + RVC + 노인 흉성 마스터링)
    out_a = OUT_DIR / "slide_001_grandfather_optionA_deep.mp3"
    master_audio(rvc_bongjin_wav, out_a, pitch_shift_semitones=-0.8, low_boost=4.5)

    # 트랙 B: [차분한 연륜] 자애롭고 또박또박한 할아버지의 회상 낭독 (InJoon + RVC + 노인 흉성 마스터링)
    out_b = OUT_DIR / "slide_001_grandfather_optionB_calm.mp3"
    master_audio(rvc_injoon_wav, out_b, pitch_shift_semitones=-0.5, low_boost=3.5)

    # 트랙 C: [맑은 고전] 순수 한국어 표준 구연 (BongJin + DSP 마스터링)
    out_c = OUT_DIR / "slide_001_grandfather_optionC_pure.mp3"
    master_audio(raw_bongjin, out_c, pitch_shift_semitones=-0.5, low_boost=4.0)

    print(f"\n🎉 [완성 1] Option A (중후한 할아버지 구연): {out_a.name}")
    print(f"🎉 [완성 2] Option B (자애로운 할아버지 낭독): {out_b.name}")
    print(f"🎉 [완성 3] Option C (순수 한국어 마스터 구연): {out_c.name}")

async def main():
    await generate_korean_voices()
    apply_rvc_and_mastering()

if __name__ == "__main__":
    asyncio.run(main())
