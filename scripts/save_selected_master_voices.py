#!/usr/bin/env python3
"""
save_selected_master_voices.py
───────────────────────────────
사용자가 선정한 최상위 2대 공식 실제 육성 보이스 영구 저장 및 등록

1. [보이스 A] 전통 야담 구연가 (구수한 판소리 완급 조절)
   - 출처: 한국구비문학대계 설화 아카이브 (공공누리 제1유형 출처표시)
   - 특징: 사투리 억양과 구전 야담 특유의 리듬감이 살아 숨 쉬는 우리 민족 고유의 전기수 낭독 톤

2. [보이스 B] 표준어 남성 성우 (중후하고 안정된 서사 톤)
   - 출처: Zeroth-Korean #104 (CC BY 4.0 - 저작권 완전 무료)
   - 특징: 잡음과 울림이 전혀 없는 스튜디오 원음으로, 묵직하고 차분하게 역사의 비극을 이끌어가는 정통 성우 톤
"""

import os, sys, shutil, json, subprocess, io
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path


WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
MASTER_DIR = WORKSPACE / "master_voice_standard"
AUDIO_DIR = MASTER_DIR / "audio_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

PUBLIC_DIR = WORKSPACE / "output" / "public_voices_slide01"

# 1. 파일 복사 및 보존
VOICE_SPECS = {
    "version": "2026.09.06",
    "status": "OFFICIALLY_APPROVED",
    "voices": {
        "folklore_storyteller": {
            "id": "folklore_storyteller",
            "name": "전통 야담 구연가 (구수한 판소리 완급 조절)",
            "license": "공공누리 제1유형 (출처표시 시 상업적 이용 및 변경 허용)",
            "source": "한국구비문학대계 설화 아카이브 (한국학중앙연구원)",
            "description": "사투리 억양과 구전 야담 특유의 리듬감이 살아 숨 쉬는 우리 민족 고유의 전기수 낭독 톤",
            "engine": "GPT-SoVITS V2 Zero-Shot + Studio Mastering DSP",
            "ref_audio": "audio_samples/ref_folklore_storyteller.wav",
            "prompt_text": "마을의 장터는 이른 아침부터 모여든 사람들로 북적였고",
            "sample_slide01": "audio_samples/sample_slide01_folklore_storyteller.mp3",
            "dsp_filter": "equalizer=f=150:width_type=o:width=1.3:g=+2.5dB,equalizer=f=2200:width_type=o:width=1.0:g=-2.5dB,loudnorm=I=-16:LRA=11:TP=-1.5",
            "recommended_usage": "전통 야담, 민담, 도령/머슴/민초 대화 및 사투리 구연 파트"
        },
        "standard_male_104": {
            "id": "standard_male_104",
            "name": "표준어 남성 (중후하고 안정된 서사 톤)",
            "license": "CC BY 4.0 (상업적 이용 및 변형 100% 완전 자유 허용)",
            "source": "Zeroth-Korean Speech Corpus #104 (OpenSLR 40)",
            "description": "잡음과 울림이 전혀 없는 스튜디오 원음으로, 묵직하고 차분하게 역사의 비극을 이끌어가는 정통 성우 톤",
            "engine": "GPT-SoVITS V2 Zero-Shot + Studio Mastering DSP",
            "ref_audio": "audio_samples/ref_zeroth_male_104.wav",
            "prompt_text": "한 잔의 커피가 소비자에게 전해지기 위해선 여러 차례의 공정을 거쳐야 한다",
            "sample_slide01": "audio_samples/sample_slide01_zeroth_male_104.mp3",
            "dsp_filter": "equalizer=f=130:width_type=o:width=1.3:g=+3.0dB,equalizer=f=2500:width_type=o:width=1.0:g=-2.5dB,loudnorm=I=-16:LRA=11:TP=-1.5",
            "recommended_usage": "메인 역사 내레이션, 공식 다큐멘터리 서사, 비장한 전개"
        }
    }
}

def copy_and_save():
    # 1. 전통 야담 구연가 파일 복사
    ref_storyteller_src = WORKSPACE / "output/korean_storyteller_3to5s_samples/sample1_storyteller_intro_4.4s.wav"
    gen_storyteller_src = PUBLIC_DIR / "slide01_4_classic_storyteller.mp3"
    shutil.copyfile(ref_storyteller_src, AUDIO_DIR / "ref_folklore_storyteller.wav")
    shutil.copyfile(gen_storyteller_src, AUDIO_DIR / "sample_slide01_folklore_storyteller.mp3")

    # 2. 표준어 남성 성우 104 파일 복사
    ref_male_src = WORKSPACE / "data/clean_public_voices/extracted_speakers/speaker_104_104_003_0294.wav"
    gen_male_src = PUBLIC_DIR / "slide01_1_male_standard_104.mp3"
    shutil.copyfile(ref_male_src, AUDIO_DIR / "ref_zeroth_male_104.wav")
    shutil.copyfile(gen_male_src, AUDIO_DIR / "sample_slide01_zeroth_male_104.mp3")

    # 3. JSON 명세서 저장
    spec_path = MASTER_DIR / "selected_master_voices.json"
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(VOICE_SPECS, f, ensure_ascii=False, indent=2)

    print(f"✅ 공식 마스터 보이스 2종 저장 완료:")
    print(f"   1. {AUDIO_DIR / 'sample_slide01_folklore_storyteller.mp3'}")
    print(f"   2. {AUDIO_DIR / 'sample_slide01_zeroth_male_104.mp3'}")
    print(f"   📄 명세서: {spec_path}")

if __name__ == "__main__":
    copy_and_save()
