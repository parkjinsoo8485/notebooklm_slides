# 👑 [송림야담] 공식 골든 스탠다드 음성 기준 명세서

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

## 📜 3. 대본 작성 및 한국어 표준 발음 원칙 (골든 룰)
1. **금지 표현**: `~였더랬지요`, `~말았더랬지요`, `~했더랬지요` (인위적인 어미 완전 배제)
2. **권장 표현**: `~였습니다`, `~말았습니다`, `~흐느꼈습니다`, `~것이었습니다`, `~시작했습니다` 등 품격 있고 매끄러운 서사형 종결어미
3. **호흡 구두점**: 연속 발화 시 AI가 자연스럽게 완급을 타도록 문맥에 맞는 `,`와 `...` 적재적소 배치
4. **국립국어원 표준 발음 및 연음 규정 준수**:
   * 상세 규정: [`KOREAN_PRONUNCIATION_STANDARD.md`](KOREAN_PRONUNCIATION_STANDARD.md)
   * 관형격 조사 '의' ➔ `[에]` 발음 (`문밖의` ➔ `[문바께]`, `마님의` ➔ `[마니메]`)
   * 비음화/유음화/경음화 (`10년` ➔ `[심 년]`, `100년` ➔ `[뱅 년]`, `달빛조차` ➔ `[달비쪼차]`)
   * 화면 자막(정서법)과 음성 합성용 텍스트(발음 교정본)를 분리하는 **2-Track G2P 파이프라인**을 전면 적용
