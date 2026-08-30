import argparse
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
TEMP_TTS_DIR = OUTPUT_DIR / "temp_tts"
SLIDES_DATA_PATH = OUTPUT_DIR / "slides_data.json"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_TTS_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# 심야 설화 매칭 마스터 파라미터 (송림야담 심야 톤)
# - Rate : -29%  → 나지막하고 느긋한 호흡의 심야 설화 템포
# - Pitch: -25Hz → 깊은 중저음 톤, 차분하고 부드러운 몰입감
# ──────────────────────────────────────────────────────────────
AUDIOBOOK_VOICE_CONFIG = {
    "voice": "ko-KR-SunHiNeural",
    "rate": "-29%",
    "pitch": "-25Hz",
    "desc": "심야 설화 매칭: SunHi rate -29%, pitch -25Hz"
}


# ──────────────────────────────────────────────────────────────
# 야담 텍스트 튜닝 변환기
#   - 아나운서식 어미 → 이야기꾼 어미
#   - 마침표 → 말줄임표
#   - 강제 호흡 쉼표 삽입
# ──────────────────────────────────────────────────────────────
def apply_yadام_style(text: str) -> str:
    """
    Edge TTS가 야담(이야기꾼) 억양으로 읽도록 텍스트를 튜닝한다.
    1) 아나운서 어미(~했습니다. ~였습니다. 등) → 이야기꾼 어미(~했지요... ~였지요...)
    2) 문장 끝 마침표 → 말줄임표(...) 로 대체 → 말끝을 흐리게
    3) 긴 구(句) 앞에 쉼표 삽입 → 인위적 호흡 파괴
    """

    # ── 1. 아나운서 어미 → 이야기꾼 어미 ─────────────────────────
    yadام_endings = [
        (r'말았습니다', '말았지요'),
        (r'습니다',     '었지요'),
        (r'였습니다',   '였지요'),
        (r'이었습니다', '이었지요'),
        (r'했습니다',   '했지요'),
        (r'입니다',     '이었지요'),
        (r'겠습니다',   '겠지요'),
        (r'됩니다',     '되었지요'),
        (r'있습니다',   '있었지요'),
        (r'없습니다',   '없었지요'),
    ]
    for old, new in yadام_endings:
        text = re.sub(old, new, text)

    # ── 2. 문장 끝 마침표(.) → 말줄임표(...) ──────────────────────
    # 이미 ...가 붙어있으면 그대로, 단순 마침표만 교체
    text = re.sub(r'(?<!\.)\.(?!\.)', '...', text)

    # ── 3. 조사 앞 강제 쉼표로 호흡 파괴 (긴 문장 한정) ─────────────
    # '은/는/이/가/을/를/으로/에서/에게' 앞 공백에 쉼표 삽입
    # 너무 잦으면 어색하므로, 5글자 이상 어절 뒤에만 적용
    def insert_breath_commas(t: str) -> str:
        # 패턴: 4자 이상 어절 뒤 + 공백 + 조사로 시작하는 어절
        pattern = re.compile(
            r'([가-힣]{4,})\s+(은|는|이|가|을|를|도|만|로|으로|에서|에게|보다|처럼|까지|부터)'
        )
        return pattern.sub(r'\1, \2', t)

    text = insert_breath_commas(text)

    return text.strip()


def split_into_clauses_for_subtitles(text):
    """
    말줄임표(...) 및 마침표 단위로 단일행(1줄) 자막 분할
    """
    clean_text = text.replace("...", "...|").replace(". ", ".|")
    parts = clean_text.split("|")
    res = [p.strip() for p in parts if p.strip()]
    return res if res else [text.strip()]


def get_audio_duration_s(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 15.0


async def generate_slide_audio_ssml_master(slide, idx, wav_mode: bool = False):
    idx_num = slide.get("slide_index", idx)
    voice_script = slide.get("voice_script", "")

    if not voice_script:
        voice_script = slide.get("slide_screen_text", "")

    # 야담 스타일 텍스트 변환 적용
    tuned_script = apply_yadام_style(voice_script)

    # wav_mode=True 이면 RVC 입력용 WAV, False 이면 최종 MP3
    ext         = "wav" if wav_mode else "mp3"
    final_audio = (TEMP_TTS_DIR if wav_mode else AUDIO_DIR) / f"audio_{idx_num:03d}.{ext}"
    srt_file    = SUBTITLES_DIR / f"slide_{idx_num:03d}.srt"

    communicate = edge_tts.Communicate(
        tuned_script,
        AUDIOBOOK_VOICE_CONFIG["voice"],
        rate=AUDIOBOOK_VOICE_CONFIG["rate"],
        pitch=AUDIOBOOK_VOICE_CONFIG["pitch"]
    )
    await communicate.save(str(final_audio))

    # 오디오 길이 측정
    total_dur = get_audio_duration_s(final_audio)

    # 단일행(1줄) 교체형 SRT 자막 생성
    clauses = split_into_clauses_for_subtitles(tuned_script)
    total_chars = sum(len(c) for c in clauses)
    srt_cues = []
    current_time_s = 0.0

    for i, clause in enumerate(clauses):
        ratio = len(clause) / total_chars if total_chars > 0 else (1.0 / len(clauses))
        clause_dur = total_dur * ratio
        start_s = current_time_s
        end_s = start_s + clause_dur if i < len(clauses) - 1 else total_dur
        current_time_s = end_s

        s_mins, s_secs = int(start_s // 60), int(start_s % 60)
        s_ms = int((start_s - int(start_s)) * 1000)

        e_mins, e_secs = int(end_s // 60), int(end_s % 60)
        e_ms = int((end_s - int(end_s)) * 1000)

        start_ts = f"00:{s_mins:02d}:{s_secs:02d},{s_ms:03d}"
        end_ts = f"00:{e_mins:02d}:{e_secs:02d},{e_ms:03d}"

        clean_disp = clause.replace("...", "").replace("…", "").strip()
        srt_cues.append(f"{i + 1}\n{start_ts} --> {end_ts}\n{clean_disp}\n")

    with open(srt_file, "w", encoding="utf-8") as sf:
        sf.write("\n".join(srt_cues))

    mode_tag = "WAV(RVC용)" if wav_mode else "MP3"
    print(f"  [✓] Slide {idx_num:03d}: {final_audio.name} ({mode_tag}, {total_dur:.1f}s)")


async def main():
    parser = argparse.ArgumentParser(description="야담 스타일 Edge TTS 생성")
    parser.add_argument("--wav", action="store_true",
                        help="MP3 대신 WAV 출력 (RVC 파이프라인 연동용, temp_tts/ 저장)")
    parser.add_argument("--slide", type=int, default=None,
                        help="단일 슬라이드 번호 처리 (테스트용)")
    args = parser.parse_args()

    if not SLIDES_DATA_PATH.exists():
        print(f"Error: {SLIDES_DATA_PATH} not found.")
        return

    with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)

    if args.slide:
        slides = [s for s in slides if s.get("slide_index") == args.slide]
        if not slides:
            print(f"❌ 슬라이드 {args.slide} 없음.")
            return

    total = len(slides)
    mode_desc = "WAV (RVC 입력용)" if args.wav else "MP3 (최종 오디오)"
    print(f"🎙️ [야담 스타일 v2] {total}개 트랙 생성 시작...")
    print(f"   - Voice : {AUDIOBOOK_VOICE_CONFIG['voice']}")
    print(f"   - Rate  : {AUDIOBOOK_VOICE_CONFIG['rate']}  Pitch: {AUDIOBOOK_VOICE_CONFIG['pitch']}")
    print(f"   - 출력  : {mode_desc}")
    print(f"   - 텍스트: 야담 어미 변환 + 말줄임표 + 호흡 쉼표 자동 적용")
    print()

    for idx, slide in enumerate(slides, start=1):
        await generate_slide_audio_ssml_master(slide, idx, wav_mode=args.wav)

    print(f"\n✨ {total}개 야담 스타일 오디오 및 단일행 SRT 생성 완료!")


if __name__ == "__main__":
    asyncio.run(main())
