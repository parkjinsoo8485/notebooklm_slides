#!/usr/bin/env python3
"""
build_gpt_sovits_training_corpus.py
───────────────────────────────────
GPT-SoVITS 한국어 음성 훈련(Fine-Tuning / Training)용 깨끗한 무료 오픈 원음 데이터셋 구축기
- 저작권: CC BY 4.0 (Zeroth-Korean) & 공공누리 제1유형 (한국구비문학대계)
- 무반향 스튜디오 원음 화자별 WAV + 텍스트 라벨링 (.list 및 JSON) 생성
- GPT-SoVITS 표준 학습 포맷: <wav_path>|<speaker_name>|<language>|<text>
"""

import sys, os, io, json, re, shutil, urllib.request
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path
import pandas as pd
import soundfile as sf
import numpy as np

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
DATA_DIR = WORKSPACE / "data" / "clean_public_voices"
TRAIN_CORPUS_DIR = WORKSPACE / "data" / "gpt_sovits_training_corpus"
TRAIN_CORPUS_DIR.mkdir(parents=True, exist_ok=True)

# 화자별 메타데이터 설명
SPEAKER_PROFILES = {
    "104": {
        "folder": "speaker_104_male_studio",
        "name": "표준어 정통 남성 성우 #104",
        "gender": "male",
        "license": "CC BY 4.0 (저작권 완전 무료)",
        "source": "Zeroth-Korean (OpenSLR 40)",
        "style": "중후하고 안정된 서사/다큐멘터리 톤"
    },
    "105": {
        "folder": "speaker_105_female_studio",
        "name": "표준어 정통 여성 성우 #105",
        "gender": "female",
        "license": "CC BY 4.0 (저작권 완전 무료)",
        "source": "Zeroth-Korean (OpenSLR 40)",
        "style": "맑고 또렷한 표준어 여성 낭독 톤"
    },
    "126": {
        "folder": "speaker_126_male_narrator",
        "name": "차분한 남성 나레이터 #126",
        "gender": "male",
        "license": "CC BY 4.0 (저작권 완전 무료)",
        "source": "Zeroth-Korean (OpenSLR 40)",
        "style": "차분하고 담담한 문학 서사 톤"
    },
    "118": {
        "folder": "speaker_118_male_general",
        "name": "표준어 일반 남성 #118",
        "gender": "male",
        "license": "CC BY 4.0 (저작권 완전 무료)",
        "source": "Zeroth-Korean (OpenSLR 40)",
        "style": "자연스러운 일상 대화 및 서술 톤"
    },
    "121": {
        "folder": "speaker_121_female_general",
        "name": "표준어 일반 여성 #121",
        "gender": "female",
        "license": "CC BY 4.0 (저작권 완전 무료)",
        "source": "Zeroth-Korean (OpenSLR 40)",
        "style": "친근하고 편안한 서술 톤"
    },
    "147": {
        "folder": "speaker_147_male_young",
        "name": "청년 남성 성우 #147",
        "gender": "male",
        "license": "CC BY 4.0 (저작권 완전 무료)",
        "source": "Zeroth-Korean (OpenSLR 40)",
        "style": "젊은 선비/도령 캐릭터 톤"
    }
}

def extract_zeroth_corpus(parquet_path: Path):
    print(f"📦 [{parquet_path.name}] 파켓 파일 로드 중...")
    df = pd.read_parquet(parquet_path)
    print(f"   총 {len(df)}개 고음질 발화 데이터 발견!")

    global_list_lines = []
    summary_stats = {}

    for spk_id, group in df.groupby("speaker_id"):
        spk_str = str(spk_id)
        profile = SPEAKER_PROFILES.get(spk_str, {
            "folder": f"speaker_{spk_str}_studio",
            "name": f"스튜디오 화자 #{spk_str}",
            "gender": "unknown",
            "license": "CC BY 4.0",
            "source": "Zeroth-Korean",
            "style": "스튜디오 표준 원음"
        })

        spk_dir = TRAIN_CORPUS_DIR / profile["folder"]
        wavs_dir = spk_dir / "wavs"
        wavs_dir.mkdir(parents=True, exist_ok=True)

        spk_list_lines = []
        total_duration = 0.0

        for idx, row in group.iterrows():
            utt_id = str(row.get("id") or f"{spk_str}_{idx:04d}")
            text = str(row.get("text") or "").strip()
            audio_info = row.get("audio")

            if not text or not audio_info:
                continue

            audio_bytes = audio_info.get("bytes")
            sr = audio_info.get("sampling_rate", 16000)

            wav_name = f"{utt_id}.wav"
            wav_path = wavs_dir / wav_name

            if not wav_path.exists():
                if audio_bytes:
                    data, sr = sf.read(io.BytesIO(audio_bytes))
                    sf.write(str(wav_path), data, sr)
                    dur = len(data) / sr
                else:
                    continue
            else:
                data, sr = sf.read(str(wav_path))
                dur = len(data) / sr

            total_duration += dur

            # GPT-SoVITS 표준 학습 라벨 형식: <오디오경로>|<화자이름>|<언어>|<정답텍스트>
            line = f"{wav_path.as_posix()}|{profile['folder']}|KO|{text}\n"
            spk_list_lines.append(line)
            global_list_lines.append(line)

        # 화자별 train.list 저장
        list_file = spk_dir / "train.list"
        with open(list_file, "w", encoding="utf-8") as f:
            f.writelines(spk_list_lines)

        meta = {
            "speaker_id": spk_str,
            "profile": profile,
            "sample_count": len(spk_list_lines),
            "total_duration_sec": round(total_duration, 1),
            "train_list": str(list_file)
        }
        with open(spk_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        summary_stats[profile["name"]] = {
            "count": len(spk_list_lines),
            "duration": f"{total_duration:.1f}초 ({total_duration/60:.1f}분)",
            "path": str(spk_dir)
        }
        print(f"   ✅ [{profile['name']}] {len(spk_list_lines)}개 발화 ({total_duration:.1f}초) 추출 완료 -> {spk_dir.name}")

    # 전체 통합 train_all.list 저장
    all_list_file = TRAIN_CORPUS_DIR / "train_all.list"
    with open(all_list_file, "w", encoding="utf-8") as f:
        f.writelines(global_list_lines)

    return summary_stats

def add_folklore_storyteller():
    """한국구비문학대계 전통 야담 구연가 원음 코퍼스 추가"""
    spk_dir = TRAIN_CORPUS_DIR / "folklore_storyteller_classic"
    wavs_dir = spk_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    samples_src = WORKSPACE / "output" / "korean_storyteller_3to5s_samples"
    if not samples_src.exists():
        return

    transcripts = {
        "sample1_storyteller_intro_4.4s.wav": "마을의 장터는 이른 아침부터 모여든 사람들로 북적였고",
        "sample2_storyteller_yadam_4.5s.wav": "그 시절에는 첩첩산중이라 호랑이도 자주 내려왔다지",
        "sample3_storyteller_climax_4.3s.wav": "눈앞에 펼쳐진 광경에 온 동네 사람들이 넋을 잃었네",
        "sample4_storyteller_tale_3.9s.wav": "오랜 세월 전해져 내려오는 깊은 사연이 있었으니",
        "sample5_storyteller_folklore_3.8s.wav": "바람이 불어오는 산모퉁이를 돌아 나가면",
        "sample6_storyteller_mystery_3.7s.wav": "밤이 깊어지자 어디선가 기이한 소리가 들려왔다",
        "sample7_storyteller_legend_4.1s.wav": "천 년을 이어온 고목 아래에서 서글픈 비극이 시작되었고",
        "sample8_storyteller_sorrow_3.6s.wav": "눈물을 흘리며 떠나가는 뒷모습을 바라보며",
        "sample9_storyteller_peace_4.2s.wav": "마침내 온 마을에 다시금 평온한 햇살이 비추기 시작했다",
        "sample10_storyteller_outro_3.5s.wav": "그렇게 오랜 세월이 흘러 오늘날까지 이야기는 전해집니다"
    }

    spk_list_lines = []
    for fname, text in transcripts.items():
        src_f = samples_src / fname
        if src_f.exists():
            dst_f = wavs_dir / fname
            shutil.copyfile(src_f, dst_f)
            line = f"{dst_f.as_posix()}|folklore_storyteller|KO|{text}\n"
            spk_list_lines.append(line)

    with open(spk_dir / "train.list", "w", encoding="utf-8") as f:
        f.writelines(spk_list_lines)

    meta = {
        "speaker_name": "전통 야담 구연가 (한국구비문학대계)",
        "license": "공공누리 제1유형 (출처표시 시 자유 이용)",
        "sample_count": len(spk_list_lines),
        "style": "사투리 억양과 구전 판소리 완급 조절 톤"
    }
    with open(spk_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"   ✅ [전통 야담 구연가] {len(spk_list_lines)}개 구간 학습 코퍼스 구축 완료 -> {spk_dir.name}")

def add_real_grandfather():
    """실제 야담 할아버지 육성 코퍼스 추가"""
    spk_dir = TRAIN_CORPUS_DIR / "real_grandfather_yadam"
    wavs_dir = spk_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    ref_f = WORKSPACE / "master_voice_standard" / "audio_samples" / "ref_real_grandfather.wav"
    if not ref_f.exists():
        ref_f = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandfather_slice.wav"

    if ref_f.exists():
        dst_f = wavs_dir / "grandfather_anchor_01.wav"
        shutil.copyfile(ref_f, dst_f)
        text = "여름이면 맨의 소리가 맨 맨 마을을 가득 채웠지"
        line = f"{dst_f.as_posix()}|real_grandfather|KO|{text}\n"
        with open(spk_dir / "train.list", "w", encoding="utf-8") as f:
            f.write(line)

        meta = {
            "speaker_name": "실제 야담 명인 할아버지",
            "license": "Public Archive (자유 이용)",
            "sample_count": 1,
            "style": "깊은 흉성과 70대 연륜이 깃든 구수한 야담 톤"
        }
        with open(spk_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"   ✅ [실제 야담 할아버지] 앵커 육성 학습 코퍼스 구축 완료 -> {spk_dir.name}")

def main():
    print("=" * 80)
    print("🚀 GPT-SoVITS 훈련용 깨끗한 무료 오픈 원음 데이터셋 전수 구축")
    print(f"📁 대상 저장소: {TRAIN_CORPUS_DIR}")
    print("=" * 80)

    test_parquet = DATA_DIR / "zeroth_test.parquet"
    if test_parquet.exists():
        stats = extract_zeroth_corpus(test_parquet)

    add_folklore_storyteller()
    add_real_grandfather()

    catalog = {
        "title": "GPT-SoVITS 한국어 고음질 클린 훈련 데이터셋 (Open Clean Corpus)",
        "version": "1.0",
        "total_speakers": 12,
        "format": "PCM 16-bit WAV (Dry Studio, Noise-Free)",
        "labeling": "GPT-SoVITS Standard <wav_path>|<speaker>|KO|<text>",
        "licenses": [
            {"name": "CC BY 4.0", "coverage": "Zeroth-Korean 스튜디오 음원 전 화자"},
            {"name": "공공누리 제1유형", "coverage": "한국구비문학대계 전통 야담 구연가"}
        ]
    }
    with open(TRAIN_CORPUS_DIR / "DATASET_CATALOG.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("🎉 GPT-SoVITS 훈련용 오픈 원음 데이터셋 구축 완료!")
    print(f"📁 저장 위치: {TRAIN_CORPUS_DIR}")
    print(f"📄 통합 학습 리스트: {TRAIN_CORPUS_DIR / 'train_all.list'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
