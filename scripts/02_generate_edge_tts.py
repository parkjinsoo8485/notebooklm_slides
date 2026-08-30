"""
02_generate_edge_tts.py
────────────────────────
[송림야담 공식 프로덕션 음성 생성기 - 한국어 표준 발음/연음 정밀 적용]
국립국어원 표준 발음법에 따른 연음 규칙(조사 '의' [에], 비음화, 경음화 등)을 적용하여
100% 실제 성우의 자연스러운 발음으로 120개 전체 슬라이드 음성 & 자막을 생성합니다.
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
import edge_tts

# 한국어 발음 정규화 모듈 임포트
from korean_phonetic_normalizer import normalize_phonetics_for_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR    = Path(__file__).resolve().parent.parent
OUTPUT_DIR       = WORKSPACE_DIR / "output"
AUDIO_DIR        = OUTPUT_DIR / "audio"
SUBTITLES_DIR    = OUTPUT_DIR / "subtitles"
TEMP_TTS_DIR     = OUTPUT_DIR / "temp_tts"
SLIDES_DATA_PATH = OUTPUT_DIR / "slides_data.json"

for d in [AUDIO_DIR, SUBTITLES_DIR, TEMP_TTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── 확정된 공식 골든 스탠다드 스펙 ─────────────────────────────
VOICE_NAME = "ko-KR-SunHiNeural"
RATE       = "-22%"
PITCH      = "-24Hz"

AF_FILTER = (
    "adelay=350|350,"
    "equalizer=f=190:width_type=o:width=1.5:g=4.0,"
    "equalizer=f=450:width_type=o:width=1.5:g=2.0,"
    "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
    "highshelf=f=7500:g=-2.0,"
    "aecho=0.8:0.6:20|35:0.10|0.05,"
    "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
    "apad=pad_dur=0.5,"
    "volume=1.25"
)

def clean_and_enhance_script(text: str) -> str:
    """인위적인 어미(~더랬지요 등) 삭제 및 자연스러운 정통 스토리텔링 구어체 변환"""
    replacements = [
        (r'내쫓기고 말았더랬지요', '쫓겨나고 말았습니다'),
        (r'말았더랬지요', '말았습니다'),
        (r'달아나 버렸더랬지요', '달아나 버렸습니다'),
        (r'흐느꼈더랬지요', '흐느꼈습니다'),
        (r'막아냈더랬지요', '막아냈습니다'),
        (r'밝혔더랬지요', '밝혔습니다'),
        (r'돌쇠였더랬지요', '돌쇠였습니다'),
        (r'있었더랬지요', '있었습니다'),
        (r'없었더랬지요', '없었습니다'),
        (r'이었더랬지요', '이었습니다'),
        (r'였더랬지요', '였습니다'),
        (r'했더랬지요', '했습니다'),
        (r'되었더랬지요', '되었습니다'),
        (r'보았더랬지요', '보았습니다'),
        (r'왔더랬지요', '왔습니다'),
        (r'갔더랬지요', '갔습니다'),
        (r'비극이었답니다\.*', '비극이었습니다.'),
        (r'이어졌지요\.*', '이어졌습니다.'),
        (r'놀랐답니다\.*', '놀랐습니다.'),
    ]
    for old, new in replacements:
        text = re.sub(old, new, text)

    # 띄어 읽기 쉼표 보정
    text = re.sub(r'\b다음\s+(제[0-9]+막)', r'다음, \1', text)
    text = re.sub(r'\b(그때)\s+([가-힣])', r'\1, \2', text)
    text = re.sub(r'\b(한편)\s+([가-힣])', r'\1, \2', text)
    text = re.sub(r'\b(하지만)\s+([가-힣])', r'\1, \2', text)
    text = re.sub(r'\b(도성 안)\s+(비밀)', r'\1, \2', text)
    text = re.sub(r'\b(횃불이)\s+(등\s*뒤)', r'\1, \2', text)
    text = re.sub(r'\b(손을)\s+(등\s*뒤)', r'\1, \2', text)
    text = re.sub(r'\b(노파)\s+(월이댁)', r'\1, \2', text)
    text = re.sub(r'\b(들어야\s*할)\s+(결전의)', r'\1, \2', text)
    
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def process_single_slide(slide, sem, total_count):
    idx = slide["slide_index"]
    original_script = slide.get("voice_script") or slide.get("slide_screen_text", "")
    emotion = slide.get("emotion", "")
    
    # 1. 화면 자막용 정제 대본 (정서법 유지: '문밖의', '마님의')
    clean_script = clean_and_enhance_script(original_script)
    slide["voice_script"] = clean_script

    # 2. 상황별 지능형 완급 조절 (Dynamic Situation Pacing)
    # 1) 긴박/추격/위기 상황 -> 조여드는 빠른 템포 (-17%)
    if any(k in emotion for k in ["긴박", "추격", "위기", "대노", "일촉즉발"]) or any(k in clean_script for k in ["사병", "쫓아", "들이닥", "화살이", "칼날", "포졸", "추포"]):
        slide_rate = "-17%"
        slide_pitch = "-22Hz"
    # 2) 슬픔/비통/절망/눈물/애원 상황 -> 깊게 가라앉는 느린 호흡 (-25%)
    elif any(k in emotion for k in ["비통", "슬픔", "눈물", "절망", "애원", "애잔", "추모"]) or any(k in clean_script for k in ["피눈물", "흐느꼈", "잿더미", "홀로 남겨진", "가련한 목숨"]):
        slide_rate = "-25%"
        slide_pitch = "-26Hz"
    # 3) 평균 서사 / 안정적인 스토리텔링 기본 템포 (-22%)
    else:
        slide_rate = "-22%"
        slide_pitch = "-24Hz"

    # 3. TTS 음성 합성 전용 발음 교정 대본 (표준 연음 적용: '문밖에', '마님에', '눈비첸', '산냑초', '살까치')
    phonetic_script = normalize_phonetics_for_tts(clean_script)

    raw_mp3 = TEMP_TTS_DIR / f"slide_{idx:03d}_raw.mp3"
    final_mp3 = AUDIO_DIR / f"slide_{idx:03d}.mp3"
    final_srt = SUBTITLES_DIR / f"slide_{idx:03d}.srt"

    async with sem:
        # Edge-TTS 음성 합성 (상황별 맞춤 템포/피치 적용)
        communicate = edge_tts.Communicate(phonetic_script, voice=VOICE_NAME, rate=slide_rate, pitch=slide_pitch)
        submaker = edge_tts.SubMaker()
        
        with open(raw_mp3, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        # SRT 자막 저장 (화면 표기는 정서법 원문 대본 사용)
        srt_content = submaker.get_srt()
        if not srt_content.strip():
            srt_content = f"1\n00:00:00,000 --> 00:00:10,000\n{clean_script}\n"
        with open(final_srt, "w", encoding="utf-8") as f:
            f.write(srt_content)

        # FFmpeg Studio Mastering DSP 적용
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_mp3),
            "-af", AF_FILTER,
            "-ar", "24000", "-b:a", "192k",
            str(final_mp3)
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await proc.wait()

        # duration 측정
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(final_mp3)
        ]
        probe = await asyncio.create_subprocess_exec(*probe_cmd, stdout=asyncio.subprocess.PIPE, stderr=subprocess.DEVNULL)
        out, _ = await probe.communicate()
        try:
            dur = float(out.decode().strip())
        except Exception:
            dur = 0.0

        slide["audio_path"] = f"output/audio/slide_{idx:03d}.mp3"
        slide["audio_duration"] = dur
        slide["subtitle_path"] = f"output/subtitles/slide_{idx:03d}.srt"

        print(f"[{idx:03d}/{total_count:03d}] ✅ 슬라이드 {idx:03d} 연음 적용 완료 ({dur:.2f}초) | 발음: {phonetic_script[:35]}...")

async def main():
    parser = argparse.ArgumentParser(description="송림야담 120개 슬라이드 전체 연음/표준발음 적용 음성 생성기")
    parser.add_argument("--limit", type=int, default=None, help="생성할 최대 슬라이드 개수")
    parser.add_argument("--concurrency", type=int, default=6, help="동시 생성 작업 수")
    args = parser.parse_args()

    if not SLIDES_DATA_PATH.exists():
        print(f"❌ {SLIDES_DATA_PATH} 파일을 찾을 수 없습니다.")
        return

    with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)

    if args.limit:
        slides = slides[:args.limit]

    total_count = len(slides)
    print(f"🚀 [송림야담] 한국어 표준 발음/연음 규칙(조사 '의' ➔ [에], 문밖의 ➔ [문바께] 등) 적용 전체 생성 시작...")
    print(f"⚙️ 설정: 보이스={VOICE_NAME}, 피치={PITCH}, 템포={RATE}, 동시작업={args.concurrency}")

    start_time = time.time()
    sem = asyncio.Semaphore(args.concurrency)
    tasks = [process_single_slide(s, sem, total_count) for s in slides]
    await asyncio.gather(*tasks)

    with open(SLIDES_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(slides, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print(f"\n🎉 전체 {total_count}개 슬라이드 한국어 표준 연음 음성 생성 완료! (소요시간: {elapsed:.1f}초)")

if __name__ == "__main__":
    asyncio.run(main())
