# NotebookLM MCP 멀티 계정 연동 가이드

본 문서는 Google NotebookLM을 3개의 계정으로 분리하여 MCP(Model Context Protocol) 서버로 등록하고 활용하는 전체 설정 과정을 정리한 문서입니다.

---

## 1. 개요 및 계정 매핑

Google 계정의 최신 보안 정책(DBSC: Device Bound Session Credentials)을 지원하는 `notebooklm-py` 라이브러리를 기반으로 영구 브라우저 프로필(Persistent Browser Profile)을 생성하여 3개 계정을 등록했습니다.

| MCP 서버 식별자 | 프로필 이름 | 연결된 구글 계정 | 세션 저장 경로 |
| :--- | :--- | :--- | :--- |
| **`notebooklm-1`** | `account1` | `parkjinsoo8485@gmail.com` | `~/.notebooklm/profiles/account1/` |
| **`notebooklm-2`** | `account2` | `jinsoo85@genedu.kr` | `~/.notebooklm/profiles/account2/` |
| **`notebooklm-3`** | `account3` | `lea8485@genedu.kr` | `~/.notebooklm/profiles/account3/` |

---

## 2. 수행한 설정 단계

### 1단계: 필수 라이브러리 및 브라우저 엔진 설치
```powershell
# notebooklm-py 패키지 설치
python -m pip install notebooklm-py

# 브라우저 자동화 엔진(Chromium) 설치
python -m playwright install chromium
```

### 2단계: 3개 독립 프로필 생성
```powershell
python -m notebooklm profile create account1
python -m notebooklm profile create account2
python -m notebooklm profile create account3
```

### 3단계: 계정별 구글 로그인 및 인증 세션 저장
```powershell
# 1번 계정 로그인 (parkjinsoo8485@gmail.com)
python -m notebooklm -p account1 login

# 2번 계정 로그인 (jinsoo85@genedu.kr)
python -m notebooklm -p account2 login

# 3번 계정 로그인 (lea8485@genedu.kr)
python -m notebooklm -p account3 login
```

### 4단계: 글로벌 MCP 설정 등록
- 파일 경로: `C:\Users\user\.gemini\config\mcp_config.json`
- 아래와 같이 3개 계정의 MCP 서버가 등록되었습니다:

```json
{
  "mcpServers": {
    "notebooklm-1": {
      "command": "python",
      "args": [
        "-m",
        "notebooklm",
        "mcp",
        "-p",
        "account1"
      ]
    },
    "notebooklm-2": {
      "command": "python",
      "args": [
        "-m",
        "notebooklm",
        "mcp",
        "-p",
        "account2"
      ]
    },
    "notebooklm-3": {
      "command": "python",
      "args": [
        "-m",
        "notebooklm",
        "mcp",
        "-p",
        "account3"
      ]
    }
  }
}
```

---

## 3. 다른 프로젝트에서의 사용 가능 여부

**👉 네, 다른 어떤 프로젝트/폴더를 열어도 즉시 사용 가능합니다!**

### 이유
- 설정이 특정 프로젝트 폴더가 아닌 **사용자 글로벌 설정(`C:\Users\user\.gemini\config\mcp_config.json`)**에 등록되어 있기 때문입니다.
- 어떤 워크스페이스(프로젝트 폴더)에서 대화하더라도 AI 에이전트는 `notebooklm-1`, `notebooklm-2`, `notebooklm-3`의 모든 도구를 바로 인식하고 실행할 수 있습니다.

---

## 4. 지원되는 주요 도구 목록

3개 계정 모두 아래의 Studio 기능들을 자연어 요청으로 자유롭게 호출할 수 있습니다:

1. **오디오 오버뷰**: `audio_overview_create` (팟캐스트 형식 음성 개요 생성)
2. **슬라이드 자료**: `slide_deck_create` (슬라이드 덱 아웃라인 및 생성)
3. **동영상 개요**: `video_overview_create` (비디오 개요 생성)
4. **마인드맵**: `mind_map_generate`, `mind_map_save` (계층적 마인드맵 생성)
5. **보고서 / 스터디 가이드**: `report_create` (상세 보고서 작성)
6. **플래시카드**: `flashcards_create` (학습용 카드 생성)
7. **퀴즈**: `quiz_create` (출제 및 채점용 퀴즈 생성)
8. **인포그래픽**: `infographic_create` (정보 시각화 자료)
9. **데이터 표**: `data_table_create` (표 데이터 추출)
10. **노트북 및 소스 관리**: 노트북 생성/조회/삭제, URL/PDF/Drive/로컬 파일 소스 추가 및 질문(`notebook_query`)

---

## 5. 실전 사용 예시 (프롬프트 가이드)

채팅창에서 아래와 같이 계정을 지정하여 요청하시면 됩니다:

- *"**1번 계정(parkjinsoo8485)**에 새 노트북 '한국어 교육 자료' 하나 만들어줘."*
- *"**2번 계정(jinsoo85)**의 첫 번째 노트북에 있는 소스를 바탕으로 **퀴즈**와 **슬라이드 덱** 만들어줘."*
- *"**3번 계정(lea8485)**에서 이번 동화 스크립트로 **AI 오디오 오버뷰** 생성해줘."*
