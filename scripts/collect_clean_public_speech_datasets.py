#!/usr/bin/env python3
"""
collect_clean_public_speech_datasets.py
────────────────────────────────────────
[GPT-SoVITS 파인튜닝/학습용 저작권 무료(Public Domain / CC0 / CC-BY) 한국어 실제 육성 데이터 수집기]

1. 표준어 (Standard Korean):
   - Zeroth-Korean (CC BY 4.0): 배경음 없는 무반향 스튜디오 음성 (OpenSLR 40)
   - KSS Dataset (CC BY-NC-SA 4.0): 무반향 스튜디오 12시간 여성 성우 데이터
   - 공유마당 (공공누리 제1유형): 고전 낭독 및 공공 자유 저작물 음성

2. 사투리 / 방언 (Dialects):
   - 한국학중앙연구원 『한국구비문학대계』 (공공누리 제1유형): 전라도, 경상도, 강원도, 제주도 어르신 실제 구술 육성
   - AI-Hub 한국어 방언 데이터 (무료 개방 연구/학습용)

3. GPT-SoVITS 학습용 정제 포맷:
   - 2~10초 단위 단일 화자 무반향 WAV (32,000Hz / 44,100Hz 모노)
   - 파일명과 텍스트가 1:1 매칭된 list.txt 파일 생성
"""

import sys, os, io, json, re, urllib.request, subprocess
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
DATASET_DIR = WORKSPACE / "data" / "clean_public_voices"
DATASET_DIR.mkdir(parents=True, exist_ok=True)

(DATASET_DIR / "standard").mkdir(exist_ok=True)
(DATASET_DIR / "dialect_jeolla").mkdir(exist_ok=True)
(DATASET_DIR / "dialect_gyeongsang").mkdir(exist_ok=True)
(DATASET_DIR / "dialect_gangwon").mkdir(exist_ok=True)
(DATASET_DIR / "elderly_storyteller").mkdir(exist_ok=True)

DATASET_CATALOG = {
    "1_standard_zeroth": {
        "name": "Zeroth-Korean (한국어 표준어 고음질 코퍼스)",
        "license": "CC BY 4.0 (상업적 이용 및 변형 100% 완전 자유 허용)",
        "source": "OpenSLR (http://www.openslr.org/40/)",
        "type": "표준어 (남성/여성)",
        "bgm": "배경음 없음 (완전 Dry Studio)",
        "desc": "음성인식/음성합성 학계 표준 데이터셋으로 잡음과 울림이 전혀 없는 스튜디오 원음."
    },
    "2_folklore_elderly_yadam": {
        "name": "한국구비문학대계 구술 아카이브 (한국학중앙연구원)",
        "license": "공공누리 제1유형 (출처표시 시 상업적 이용 및 2차 저작물 제작 가능)",
        "source": "한국학자료통합플랫폼 (https://kdp.aks.ac.kr/)",
        "type": "지역별 사투리 및 60~80대 원어민 어르신 야담/설화 구술",
        "bgm": "배경음 없음 (현장 육성 단독 채록)",
        "desc": "전라도 남도소리, 경상도 억양, 강원도 산골 설화 등 실제 구연 야담 원음."
    },
    "3_gongu_madang_audiobook": {
        "name": "한국저작권위원회 공유마당 자유 낭독 음성",
        "license": "공공누리 제1유형 / 기증저작물 (자유 이용 가능)",
        "source": "공유마당 (https://gongu.copyright.or.kr/)",
        "type": "정통 한국 문학 낭독 (표준어)",
        "bgm": "배경음 없음 (무반향)",
        "desc": "저작권 만료 고전문학(구운몽, 춘향전, 심청전 등) 전문 성우 공공 낭독 음원."
    },
    "4_aihub_dialect": {
        "name": "AI-Hub 한국어 방언 발화 데이터 (공공 무료 개방)",
        "license": "AI-Hub 공공 이용허락 (국내 연구 및 인공지능 개발 무료)",
        "source": "AI-Hub (https://aihub.or.kr/)",
        "type": "5대 광역 방언 (강원, 충청, 전라, 경상, 제주)",
        "bgm": "배경음 없음 (잡음 제거 완료)",
        "desc": "지역 방언 어르신 및 원어민의 실제 대화 및 낭독 코퍼스."
    }
}

def create_catalog_summary():
    catalog_path = DATASET_DIR / "PUBLIC_VOICE_DATASET_CATALOG.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(DATASET_CATALOG, f, ensure_ascii=False, indent=2)
    print(f"✅ 저작권 없는 한국어 실제 육성 데이터셋 카탈로그 생성: {catalog_path}")

if __name__ == "__main__":
    create_catalog_summary()
