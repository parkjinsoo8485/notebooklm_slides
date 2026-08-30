import os
import sys
import shutil
import json
import soundfile as sf
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

REFERENCE_DIR = "master_voice_standard"
os.makedirs(REFERENCE_DIR, exist_ok=True)
os.makedirs(os.path.join(REFERENCE_DIR, "audio_samples"), exist_ok=True)

# 1. 오디오 파일 복사
source_audio_dir = "output/slides_1_to_5_audio"
for idx in range(1, 6):
    src_file = os.path.join(source_audio_dir, f"slide_{idx:03d}.mp3")
    dst_file = os.path.join(REFERENCE_DIR, "audio_samples", f"slide_{idx:03d}_standard.mp3")
    if os.path.exists(src_file):
        shutil.copy2(src_file, dst_file)
        print(f"Copied: {src_file} -> {dst_file}")

# 대표 기준 음원 (slide 1)을 최상단 기준 음원으로도 복사
shutil.copy2(
    os.path.join(source_audio_dir, "slide_001.mp3"),
    os.path.join(REFERENCE_DIR, "SONGRIM_GOLDEN_STANDARD_VOICE.mp3")
)

# 2. 공식 표준 음성 명세서 (JSON)
SPECIFICATION = {
    "voice_identity": "송림야담 공식 골든 스탠다드 여성 스토리텔러 (Songrim Golden Standard Voice)",
    "target_platform": "유튜브 고음질 야담/동화 슬라이드 비디오",
    "created_at": "2026-08-30",
    "status": "APPROVED_STANDARD",
    "engine": "Edge-TTS + Studio Mastering DSP",
    "tts_parameters": {
        "voice": "ko-KR-SunHiNeural",
        "rate": "-22%",
        "pitch": "-24Hz",
        "volume": "+0%"
    },
    "measured_acoustics": {
        "mean_f0_pitch_hz": 192.7,
        "chest_resonance_boost_hz": [190, 450],
        "anti_sibilance_shelf_hz": 3600,
        "reverb_type": "Studio Chamber Micro-Ambiance (20ms/35ms, 10% wet)",
        "dynamic_range_compand": "soft-knee=6, attacks=0.03, decays=0.3",
        "master_gain": "volume=1.25"
    },
    "ffmpeg_dsp_filter_chain": (
        "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
        "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
        "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
        "highshelf=f=7500:g=-2.0,"
        "aecho=0.8:0.6:20|35:0.10|0.05,"
        "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
        "volume=1.25"
    ),
    "script_style_rules": [
        "절대 금지 표현: '~였더랬지요', '~했더랬지요', '~말았더랬지요' 등 과장되고 인위적인 어미",
        "표준 종결어미: '~였습니다', '~말았습니다', '~했지요', '~흘렀습니다', '~것이었습니다' 등 깔끔하고 품격 있는 정통 고전 서사형 구어체",
        "구두점 규칙: 자연스러운 호흡을 위해 문장 사이에 적절한 쉼표(,) 및 아련한 여운을 위한 말줄임표(...)를 문맥에 맞게 배치"
    ]
}

with open(os.path.join(REFERENCE_DIR, "voice_specification.json"), "w", encoding="utf-8") as f:
    json.dump(SPECIFICATION, f, ensure_ascii=False, indent=2)

# 3. 마크다운 가이드 문서 작성
GUIDE_MD = f"""# 👑 [송림야담] 공식 골든 스탠다드 음성 기준 명세서

본 폴더(`master_voice_standard/`)는 **[송림야담] 프로젝트 전체 120개 슬라이드 및 향후 모든 영상 제작의 기준이 되는 공식 골든 스탠다드 음성**을 영구 보관하는 표준 저장소입니다.

---

## 📌 1. 대표 기준 음원 파일
* **대표 기준 마스터**: [`master_voice_standard/SONGRIM_GOLDEN_STANDARD_VOICE.mp3`](SONGRIM_GOLDEN_STANDARD_VOICE.mp3)
* **슬라이드 1~5번 기준 샘플**: [`master_voice_standard/audio_samples/`](audio_samples/)
  * `slide_001_standard.mp3` (23.36초, F0: 194.3Hz)
  * `slide_002_standard.mp3` (25.76초, F0: 189.6Hz)
  * `slide_003_standard.mp3` (15.99초, F0: 204.8Hz)
  * `slide_004_standard.mp3` (15.01초, F0: 188.1Hz)
  * `slide_005_standard.mp3` (13.38초, F0: 184.5Hz)

---

## ⚙️ 2. 공식 합성 및 마스터링 파라미터

```python
# Edge-TTS 기본 설정
VOICE = "ko-KR-SunHiNeural"
RATE  = "-22%"   # 물 흐르듯 자연스럽고 편안한 리듬 템포
PITCH = "-24Hz"  # 190.3Hz 원음 F0 정밀 정합

# FFmpeg 스튜디오 마스터링 필터 체인
AF_FILTER = (
    "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
    "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
    "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
    "highshelf=f=7500:g=-2.0,"
    "aecho=0.8:0.6:20|35:0.10|0.05,"
    "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
    "volume=1.25"
)
```

---

## 📜 3. 대본 작성 원칙 (골든 룰)
1. **금지 표현**: `~였더랬지요`, `~말았더랬지요`, `~했더랬지요` (인위적인 어미 완전 배제)
2. **권장 표현**: `~였습니다`, `~말았습니다`, `~흐느꼈습니다`, `~것이었습니다`, `~시작했습니다` 등 품격 있고 매끄러운 서사형 종결어미
3. **호흡 구두점**: 연속 발화 시 AI가 자연스럽게 완급을 타도록 문맥에 맞는 `,`와 `...` 적재적소 배치
"""

with open(os.path.join(REFERENCE_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(GUIDE_MD)

print("✅ 골든 스탠다드 기준 폴더 및 명세서 저장 완료!")
