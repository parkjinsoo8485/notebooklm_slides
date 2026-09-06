# [송림야담] 공식 음성 청음실 & 오픈 성우 음원 구축 종합 보고서

- **작성 일시**: 2026년 9월 6일
- **프로젝트**: 송림야담 (Songrim Yadam) AI 오디오북 & 쇼츠 파이프라인
- **버전**: v2.5 (공식 마스터 선정 및 오픈 코퍼스 구축 완료)
- **GitHub 저장소**: [parkjinsoo8485/notebooklm_slides](https://github.com/parkjinsoo8485/notebooklm_slides)

---

## 🌐 1. 공식 청음실 & 플레이어 링크 목록

마크다운 뷰어나 VS Code 미리보기에서 **아래 링크를 클릭**하시면 즉시 해당 청음실 또는 스크립트로 연결됩니다.

| 번호 | 청음실 명칭 | 클릭 연결 링크 (상대경로) | 브라우저 직접 열기 링크 | 주요 특징 및 수록 내용 |
| :---: | :--- | :---: | :---: | :--- |
| 🌐 | **통합 청음실 포털 허브** *(추천)* | [통합 포털 열기](./output/all_listening_rooms_hub.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/all_listening_rooms_hub.html) | 모든 청음실과 쇼케이스를 한 화면에서 선택하여 이동할 수 있는 중앙 포털 |
| 🎙️ | **오픈 성우 음원 보관소 & 청음실** | [성우 보관소 열기](./output/voice_actors_player.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/voice_actors_player.html) | 다운로드된 스튜디오 전문 성우 발화 30종 및 정통 성우 원음 청음실 |
| 👑 | **120개 슬라이드 전편 완독실** | [120개 완독실 열기](./output/full_story_player.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/full_story_player.html) | 실제 야담 할아버지 육성으로 1~120번 슬라이드 전편 자동 연속 재생 (자막 싱크 완비) |
| 🌟 | **실제 육성 6종 슬라이드 1번 쇼케이스** | [6종 쇼케이스 열기](./output/public_voices_slide01/public_voice_slide01_showcase.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/public_voices_slide01/public_voice_slide01_showcase.html) | 저작권 무료 6종 실제 육성(구연가, 성우, 할아버지, 할머니 등) 1:1 비교 쇼케이스 |
| 👵👴 | **에코 제거 노인 육성 마스터 청음실** | [노인 청음실 열기](./output/slide01_creative_elderly/slide01_creative_elderly_player.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/slide01_creative_elderly/slide01_creative_elderly_player.html) | 아이 목소리 간섭/하울링을 100% 제거한 깨끗한 할머니 & 할아버지 비교 청음실 |
| 📜 | **전통 야담 구연가 원음 샘플실** | [구연가 샘플실 열기](./output/korean_storyteller_3to5s_samples/player_storyteller.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/korean_storyteller_3to5s_samples/player_storyteller.html) | 한국구비문학대계 설화 아카이브 4.4초 단위 원음 슬라이스 클립 모음 |
| 👵 | **Praat PSOLA 노년 음색 4종 연구실** | [Praat 연구실 열기](./output/slide01_praat_grandmother_player.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/slide01_praat_grandmother_player.html) | 음향학적 알고리즘으로 성대 이완과 포먼트를 변환한 세대별 할머니 음색 |
| 🎧 | **정통 뉴럴 야담 전문 청음실** | [뉴럴 청음실 열기](./output/neural_yadam_player.html) | [file:// 링크](file:///C:/My_Project/src/notebooklm_slides/output/neural_yadam_player.html) | 고품질 뉴럴 엔진 기반의 슬라이드 1번 낭독 플레이어 |

---

## ⚡ 2. 공식 TOP_ 생성 파이썬 엔진 사용법

대표님께서 지정하신 최상위 보이스들을 독립적으로 실행하고 일괄 생성할 수 있도록 `TOP_` 접두사 스크립트로 구축되었습니다. 파일명을 클릭하면 코드를 바로 확인하실 수 있습니다.

### 📜 ① 전통 야담 구연가 마스터 생성 엔진
- **스크립트 파일**: [scripts/TOP_generate_folklore_storyteller_yadam.py](./scripts/TOP_generate_folklore_storyteller_yadam.py)  
  *(로컬 전체 경로: [file:///C:/My_Project/src/notebooklm_slides/scripts/TOP_generate_folklore_storyteller_yadam.py](file:///C:/My_Project/src/notebooklm_slides/scripts/TOP_generate_folklore_storyteller_yadam.py))*
- **음성 특징**: 사투리 억양과 구전 판소리 완급 조절이 살아있는 고유의 전기수 톤
- **저작권**: 한국구비문학대계 설화 아카이브 (한국학중앙연구원 - 공공누리 제1유형 출처표시)
- **실행 명령**:
  ```powershell
  # 1번 슬라이드 생성 (기본값, 마스터 샘플 자동 동시 갱신)
  python scripts/TOP_generate_folklore_storyteller_yadam.py --slides 1

  # 특정 슬라이드 구간 생성 (예: 1~10번)
  python scripts/TOP_generate_folklore_storyteller_yadam.py --slides 1-10

  # 120개 전체 슬라이드 일괄 생성
  python scripts/TOP_generate_folklore_storyteller_yadam.py --slides all
  ```

### 👴 ② 실제 야담 명인 할아버지 마스터 생성 엔진
- **스크립트 파일**: [scripts/TOP_generate_real_grandfather_yadam.py](./scripts/TOP_generate_real_grandfather_yadam.py)  
  *(로컬 전체 경로: [file:///C:/My_Project/src/notebooklm_slides/scripts/TOP_generate_real_grandfather_yadam.py](file:///C:/My_Project/src/notebooklm_slides/scripts/TOP_generate_real_grandfather_yadam.py))*
- **음성 특징**: 가슴을 울리는 깊은 흉성과 70대 연륜이 깃든 구수한 한(恨)의 서사 톤
- **저작권**: 실제 야담 명인 육성 (Public Archive / 자유 이용)
- **실행 명령**:
  ```powershell
  # 1번 슬라이드 생성
  python scripts/TOP_generate_real_grandfather_yadam.py --slides 1

  # 120개 전체 슬라이드 일괄 생성
  python scripts/TOP_generate_real_grandfather_yadam.py --slides all
  ```

### 🎛️ ③ 복수 마스터 보이스 선택 생성기 (CLI)
- **스크립트 파일**: [scripts/TOP_generate_selected_master_voices.py](./scripts/TOP_generate_selected_master_voices.py)  
  *(로컬 전체 경로: [file:///C:/My_Project/src/notebooklm_slides/scripts/TOP_generate_selected_master_voices.py](file:///C:/My_Project/src/notebooklm_slides/scripts/TOP_generate_selected_master_voices.py))*
- **지원 보이스**: `folklore_storyteller` (구연가), `standard_male_104` (정통 성우)
- **실행 명령**:
  ```powershell
  python scripts/TOP_generate_selected_master_voices.py --voice folklore_storyteller --slides 1
  python scripts/TOP_generate_selected_master_voices.py --voice standard_male_104 --slides 1-5
  ```

---

## 🎧 3. 저작권 무료 오픈 성우 & 훈련 코퍼스 구축 현황

GPT-SoVITS 모델 파인튜닝 및 레퍼런스 합성에 필요한 무반향(Dry) 스튜디오 고음질 원음을 다운로드하여 체계적으로 분류·저장하였습니다.

- **보관 디렉터리 링크**: [data/clean_voice_actors/](./data/clean_voice_actors/) 및 [data/gpt_sovits_training_corpus/](./data/gpt_sovits_training_corpus/)
- **공식 사양 JSON**: [master_voice_standard/selected_master_voices.json](./master_voice_standard/selected_master_voices.json)

1. **스튜디오 전문 성우 발화 세트** (`korean_tts_training_studio`):
   - 출처: Hugging Face `daje/korean-tts-training`
   - 수량: 30개 초고음질 WAV 파일 (일상, 감정, 문학, 숫자 낭독)
   - 메타데이터: `metadata.csv` 및 GPT-SoVITS 표준 규격 `train.list` 완비
   - 폴더 바로가기: [data/clean_voice_actors/korean_tts_training_studio/](./data/clean_voice_actors/korean_tts_training_studio/)
2. **표준어 정통 남성 성우 #104** (`speaker_104_male_studio`):
   - 출처: Zeroth-Korean (CC BY 4.0 - 완전 무료)
   - 수량: 64개 발화 (총 629.4초, 약 10.5분 분량)
   - 용도: 묵직하고 중후한 역사 다큐멘터리/메인 서사
   - 폴더 바로가기: [data/clean_voice_actors/speaker_104_male_studio/](./data/clean_voice_actors/speaker_104_male_studio/)
3. **표준어 정통 여성 성우 #105** (`speaker_105_female_studio`):
   - 출처: Zeroth-Korean (CC BY 4.0 - 완전 무료)
   - 수량: 40개 발화 (총 444.2초, 약 7.4분 분량)
   - 용도: 단아하고 맑은 안방마님/여성 낭독
   - 폴더 바로가기: [data/clean_voice_actors/speaker_105_female_studio/](./data/clean_voice_actors/speaker_105_female_studio/)
4. **차분한 남성 나레이터 #126** (`speaker_126_male_narrator`):
   - 출처: Zeroth-Korean (CC BY 4.0 - 완전 무료)
   - 수량: 39개 발화 (총 406.3초, 약 6.8분 분량)
   - 용도: 담담하고 서글픈 비극 서사의 결말부
   - 폴더 바로가기: [data/clean_voice_actors/speaker_126_male_narrator/](./data/clean_voice_actors/speaker_126_male_narrator/)

---

## 🎼 4. 저작권 없는 오픈 소리(오디오/BGM/효과음) 가이드

| 분야 | 추천 플랫폼 / 소스 | 라이선스 | 바로가기 링크 | 주요 소리 및 활용처 |
| :--- | :--- | :---: | :---: | :--- |
| **TTS/보이스** | • Zeroth-Korean (OpenSLR 40)<br>• 한국구비문학대계 (한국학중앙연구원)<br>• KSS Dataset (Korean Single Speaker) | CC BY 4.0<br>공공누리 1유형<br>CC0 | [OpenSLR](https://www.openslr.org/40/)<br>[구비문학대계](https://gubi.aks.ac.kr/) | 스튜디오 성우 원음 및 전국 팔도 구술 야담 원음 |
| **전통 BGM** | • **공유마당** (한국저작권위원회)<br>• **국립국악원** 국악누리 음원<br>• 유튜브 오디오 보관함 (`Cinematic`, `Asian`) | 공공누리 1유형<br>CC0<br>유튜브 무료 | [공유마당](https://gongu.copyright.or.kr/)<br>[국립국악원](https://www.gugak.go.kr/) | 대금, 해금, 가야금 등 한국 전통 국악 및 서정적 배경음악 |
| **효과음 (SFX)** | • **공유마당** 효과음 (짚신, 문 삐걱거림, 다듬이질)<br>• **Freesound.org** (CC0 필터 검색)<br>• **Pixabay Audio** (바람, 비, 귀뚜라미, 발자국) | 공공누리 1유형<br>CC0<br>상업적 무료 | [Freesound](https://freesound.org/)<br>[Pixabay](https://pixabay.com/sound-effects/) | 한옥 생활음, 자연 환경음, 야담 분위기 조성 효과음 |

---

## 💾 5. GitHub 형상 관리 (Git Commit & Push)

- **원격 저장소**: [https://github.com/parkjinsoo8485/notebooklm_slides.git](https://github.com/parkjinsoo8485/notebooklm_slides.git)
- **반영 브랜치**: `main`
- **커밋 내역**:
  - `ad438e2`: *feat: 한국어 실제 육성 및 저작권 무료 오픈 성우 보관소/청음실 구축 & TOP 생성 엔진 완성*
  - `eacedf5`: *docs: 음성 청음실 및 오픈 성우 음원 구축 종합 보고서 추가*
- **특이사항**: 대용량 바이너리(Parquet, 수백 개 WAV)는 `.gitignore`로 안전하게 제외하여 GitHub 100MB 단일 파일 제한을 예방하고, 모든 핵심 소스 코드, 스크립트, 플레이어 HTML, 메타데이터 JSON을 영구 보존 완료.
