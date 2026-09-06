# [송림야담] 공식 음성 청음실 & 오픈 성우 음원 구축 종합 보고서

> ### 💡 [필독] 마크다운 문서에서 링크를 여는 방법
> - **현재 에디터(편집 창)에서 열 때**: 키보드의 **`Ctrl` 키를 누른 상태에서 마우스로 링크를 클릭**하세요. (`Ctrl + Click`)
> - **미리보기 창에서 열 때**: `Ctrl + Shift + V` (또는 우측 상단의 미리보기 아이콘)을 눌러 미리보기를 띄우면 **일반 마우스 클릭**으로 바로 열립니다.

---

## 🌐 1. 공식 청음실 & 플레이어 바로가기 (Ctrl + 클릭)

아래 파란색 링크를 **`Ctrl + 클릭`**하시면 해당 웹 플레이어가 즉시 열립니다.

| 청음실 명칭 | 에디터/미리보기 즉시 연결 링크 | 브라우저 직접 연결 전체 경로 |
| :--- | :---: | :---: |
| 🌐 **통합 청음실 포털 허브** *(추천)* | [output/all_listening_rooms_hub.html](output/all_listening_rooms_hub.html) | [file:///c:/My_Project/src/notebooklm_slides/output/all_listening_rooms_hub.html](file:///c:/My_Project/src/notebooklm_slides/output/all_listening_rooms_hub.html) |
| 🎙️ **오픈 성우 음원 보관소 & 청음실** | [output/voice_actors_player.html](output/voice_actors_player.html) | [file:///c:/My_Project/src/notebooklm_slides/output/voice_actors_player.html](file:///c:/My_Project/src/notebooklm_slides/output/voice_actors_player.html) |
| 👑 **120개 슬라이드 전편 완독실** | [output/full_story_player.html](output/full_story_player.html) | [file:///c:/My_Project/src/notebooklm_slides/output/full_story_player.html](file:///c:/My_Project/src/notebooklm_slides/output/full_story_player.html) |
| 🌟 **실제 육성 6종 1번 쇼케이스** | [output/public_voices_slide01/public_voice_slide01_showcase.html](output/public_voices_slide01/public_voice_slide01_showcase.html) | [file:///c:/My_Project/src/notebooklm_slides/output/public_voices_slide01/public_voice_slide01_showcase.html](file:///c:/My_Project/src/notebooklm_slides/output/public_voices_slide01/public_voice_slide01_showcase.html) |
| 👵👴 **에코 제거 노인 육성 청음실** | [output/slide01_creative_elderly/slide01_creative_elderly_player.html](output/slide01_creative_elderly/slide01_creative_elderly_player.html) | [file:///c:/My_Project/src/notebooklm_slides/output/slide01_creative_elderly/slide01_creative_elderly_player.html](file:///c:/My_Project/src/notebooklm_slides/output/slide01_creative_elderly/slide01_creative_elderly_player.html) |
| 📜 **전통 야담 구연가 원음 샘플실** | [output/korean_storyteller_3to5s_samples/player_storyteller.html](output/korean_storyteller_3to5s_samples/player_storyteller.html) | [file:///c:/My_Project/src/notebooklm_slides/output/korean_storyteller_3to5s_samples/player_storyteller.html](file:///c:/My_Project/src/notebooklm_slides/output/korean_storyteller_3to5s_samples/player_storyteller.html) |
| 👵 **Praat PSOLA 노년 음색 연구실** | [output/slide01_praat_grandmother_player.html](output/slide01_praat_grandmother_player.html) | [file:///c:/My_Project/src/notebooklm_slides/output/slide01_praat_grandmother_player.html](file:///c:/My_Project/src/notebooklm_slides/output/slide01_praat_grandmother_player.html) |
| 🎧 **정통 뉴럴 야담 전문 청음실** | [output/neural_yadam_player.html](output/neural_yadam_player.html) | [file:///c:/My_Project/src/notebooklm_slides/output/neural_yadam_player.html](file:///c:/My_Project/src/notebooklm_slides/output/neural_yadam_player.html) |

---

## ⚡ 2. 공식 TOP_ 생성 파이썬 엔진 (Ctrl + 클릭)

### 📜 ① 전통 야담 구연가 마스터 생성 엔진
- **스크립트 파일**: [scripts/TOP_generate_folklore_storyteller_yadam.py](scripts/TOP_generate_folklore_storyteller_yadam.py)  
  *(전체 경로: [file:///c:/My_Project/src/notebooklm_slides/scripts/TOP_generate_folklore_storyteller_yadam.py](file:///c:/My_Project/src/notebooklm_slides/scripts/TOP_generate_folklore_storyteller_yadam.py))*
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
- **스크립트 파일**: [scripts/TOP_generate_real_grandfather_yadam.py](scripts/TOP_generate_real_grandfather_yadam.py)  
  *(전체 경로: [file:///c:/My_Project/src/notebooklm_slides/scripts/TOP_generate_real_grandfather_yadam.py](file:///c:/My_Project/src/notebooklm_slides/scripts/TOP_generate_real_grandfather_yadam.py))*
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
- **스크립트 파일**: [scripts/TOP_generate_selected_master_voices.py](scripts/TOP_generate_selected_master_voices.py)  
  *(전체 경로: [file:///c:/My_Project/src/notebooklm_slides/scripts/TOP_generate_selected_master_voices.py](file:///c:/My_Project/src/notebooklm_slides/scripts/TOP_generate_selected_master_voices.py))*
- **지원 보이스**: `folklore_storyteller` (구연가), `standard_male_104` (정통 성우)
- **실행 명령**:
  ```powershell
  python scripts/TOP_generate_selected_master_voices.py --voice folklore_storyteller --slides 1
  python scripts/TOP_generate_selected_master_voices.py --voice standard_male_104 --slides 1-5
  ```

---

## 🎧 3. 저작권 무료 오픈 성우 & 훈련 코퍼스 폴더 (Ctrl + 클릭)

- **성우 음원 보관 폴더**: [data/clean_voice_actors/](data/clean_voice_actors/)
- **훈련 코퍼스 보관 폴더**: [data/gpt_sovits_training_corpus/](data/gpt_sovits_training_corpus/)
- **공식 마스터 사양서**: [master_voice_standard/selected_master_voices.json](master_voice_standard/selected_master_voices.json)

1. **스튜디오 전문 성우 발화 세트** (`korean_tts_training_studio`):
   - 폴더 열기: [data/clean_voice_actors/korean_tts_training_studio/](data/clean_voice_actors/korean_tts_training_studio/)
   - 수량: 30개 초고음질 WAV 파일 (일상, 감정, 문학, 숫자 낭독)
   - 메타데이터: `metadata.csv` 및 GPT-SoVITS 표준 규격 `train.list` 완비
2. **표준어 정통 남성 성우 #104** (`speaker_104_male_studio`):
   - 폴더 열기: [data/clean_voice_actors/speaker_104_male_studio/](data/clean_voice_actors/speaker_104_male_studio/)
   - 수량: 64개 발화 (총 629.4초, 약 10.5분 분량, CC BY 4.0)
3. **표준어 정통 여성 성우 #105** (`speaker_105_female_studio`):
   - 폴더 열기: [data/clean_voice_actors/speaker_105_female_studio/](data/clean_voice_actors/speaker_105_female_studio/)
   - 수량: 40개 발화 (총 444.2초, 약 7.4분 분량, CC BY 4.0)
4. **차분한 남성 나레이터 #126** (`speaker_126_male_narrator`):
   - 폴더 열기: [data/clean_voice_actors/speaker_126_male_narrator/](data/clean_voice_actors/speaker_126_male_narrator/)
   - 수량: 39개 발화 (총 406.3초, 약 6.8분 분량, CC BY 4.0)

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
- **커밋 해시**: `fd0aecd`
