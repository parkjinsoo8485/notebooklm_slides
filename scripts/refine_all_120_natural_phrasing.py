#!/usr/bin/env python3
"""
refine_all_120_natural_phrasing.py
───────────────────────────────────
[송림야담] 전체 120개 슬라이드 띄어 읽기(Phrasing) 초정밀 고도화 엔진
- 주어/조사 뒤의 어색한 쉼표 단절 완전 제거 (예: '마님은, ', '진우는, ' -> '마님은 ', '진우는 ')
- 인용 대사 및 접속 부사 연결 자연화
- 물 흐르듯 유려한 전문 나레이터 완급 조절
- 120개 전편 오디오/자막/slides_data.json/full_story_player.html 일괄 갱신
"""
import sys, os, io, json, re, subprocess, asyncio
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path
import edge_tts

PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from korean_phonetic_normalizer import normalize_phonetics_for_tts

OUTPUT_DIR = PROJECT_ROOT / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
TEMP_DIR = OUTPUT_DIR / "temp_tts"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

SLIDES_DATA_PATH = OUTPUT_DIR / "slides_data.json"

# 현수(Hyunsu) 정통 역사 실록 톤
VOICE = "ko-KR-HyunsuMultilingualNeural"
RATE = "-18%"
DSP_FILTER = (
    "equalizer=f=150:width_type=o:width=1.3:g=3.5,"
    "equalizer=f=350:width_type=o:width=1.2:g=1.8,"
    "equalizer=f=3800:width_type=o:width=1.0:g=-3.0,"
    "aecho=0.8:0.6:18|32:0.07|0.03,"
    "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
    "volume=1.20"
)

def refine_phrasing_for_storyteller(text: str) -> str:
    """문장 띄어 읽기를 성우의 유려한 구어 호흡으로 정밀 다듬기"""
    t = text
    # 1. 인위적 말줄임표/쉼표 결합물 제거
    t = re.sub(r'\s*,\s*\.\.\.\s*', ', ', t)
    t = re.sub(r'\s*\.\.\.\s*', '... ', t)
    t = re.sub(r'\.{4,}', '...', t)
    
    # 2. 주어/보어 조사 뒤의 불필요한 쉼표 단절 제거 (예: '마님은, ' -> '마님은 ', '진우는, ' -> '진우는 ')
    t = re.sub(r'([가-힣]{2,})(은|는|이|가|을|를|의|에|에게|에서|으로|로),\s+', r'\1\2 ', t)
    
    # 3. 따옴표 인용구 전후의 어색한 쉼표 정돈
    t = re.sub(r",\s*['\"]", " '", t)
    t = re.sub(r"['\"],\s*", "' ", t)
    
    # 4. 연속 쉼표/공백 정리
    t = re.sub(r',\s*,+', ',', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def get_audio_duration(file_path: Path) -> float:
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

def generate_srt(text: str, duration: float, srt_path: Path):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        sentences = [text.strip()]
    
    total_chars = sum(len(s) for s in sentences)
    cues = []
    current_time = 0.0
    
    for i, s in enumerate(sentences):
        ratio = len(s) / total_chars if total_chars > 0 else 1.0 / len(sentences)
        dur = duration * ratio
        start_t = current_time
        end_t = start_t + dur if i < len(sentences) - 1 else duration
        current_time = end_t
        
        def format_ts(sec):
            m = int(sec // 60)
            s_val = int(sec % 60)
            ms = int((sec - int(sec)) * 1000)
            return f"00:{m:02d}:{s_val:02d},{ms:03d}"
            
        cues.append(f"{i+1}\n{format_ts(start_t)} --> {format_ts(end_t)}\n{s}\n")
        
    srt_path.write_text("\n".join(cues), encoding="utf-8")

async def process_slide(slide, sem, total_count):
    async with sem:
        idx = int(slide["slide_index"])
        raw_script = slide.get("voice_script", "")
        
        # 1. 띄어 읽기 정밀 고도화 대본 생성
        smooth_script = refine_phrasing_for_storyteller(raw_script)
        # 2. 한국어 표준 연음 정규화 적용
        tts_script = normalize_phonetics_for_tts(smooth_script)
        
        temp_raw = TEMP_DIR / f"raw_slide_{idx:03d}.mp3"
        final_mp3 = AUDIO_DIR / f"slide_{idx:03d}.mp3"
        srt_file = SUBTITLES_DIR / f"slide_{idx:03d}.srt"
        
        try:
            comm = edge_tts.Communicate(tts_script, VOICE, rate=RATE)
            await comm.save(str(temp_raw))
            
            # 스튜디오 DSP 마스터링
            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_raw),
                "-af", DSP_FILTER,
                "-b:a", "320k",
                str(final_mp3)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            if temp_raw.exists():
                temp_raw.unlink()
                
            dur = get_audio_duration(final_mp3)
            slide["audio_duration"] = round(dur, 3)
            slide["audio_path"] = f"output/audio/slide_{idx:03d}.mp3"
            slide["subtitle_path"] = f"output/subtitles/slide_{idx:03d}.srt"
            
            generate_srt(raw_script, dur, srt_file)
            
            print(f"[{idx:03d}/{total_count:03d}] ✅ 띄어 읽기 정밀 합성 완료: {dur:.2f}s")
            return True
        except Exception as e:
            print(f"[{idx:03d}/{total_count:03d}] ❌ 에러: {e}")
            return False

async def main():
    print("=" * 75)
    print("🚀 [송림야담] 전체 120개 슬라이드 띄어 읽기(Phrasing) 초정밀 재합성 시작")
    print(f"🎙️ 보이스: {VOICE} | 속도: {RATE}")
    print("=" * 75)
    
    with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)
        
    total_count = len(slides)
    sem = asyncio.Semaphore(5)
    
    tasks = [process_slide(s, sem, total_count) for s in slides]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    print(f"\n✨ 전체 슬라이드 갱신 완료: {success_count}/{total_count} 성공")
    
    with open(SLIDES_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(slides, f, ensure_ascii=False, indent=2)
    print("💾 slides_data.json 동기화 완료")
    
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "create_full_player.py")], check=True)
    print("🎉 full_story_player.html 통합 플레이어 갱신 완료!")

if __name__ == "__main__":
    asyncio.run(main())
