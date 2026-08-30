"""
06_rvc_pipeline.py
──────────────────
Edge TTS (야담 스타일) → RVC 음성 변환 통합 파이프라인.

워크플로우:
  slides_data.json → apply_yadām_style() → Edge TTS (WAV) → RVC → MP3 + SRT

사용법:
    python scripts/06_rvc_pipeline.py              # 전체 120개 슬라이드
    python scripts/06_rvc_pipeline.py --slide 1    # 슬라이드 1번만 (테스트)
    python scripts/06_rvc_pipeline.py --no-rvc     # RVC 없이 Edge TTS만
    python scripts/06_rvc_pipeline.py --from 10    # 10번부터 재개
"""

import argparse
import asyncio
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR    = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))
try:
    from optimize_performance import optimize_system_and_torch
    optimize_system_and_torch(max_cpu_threads=2, lower_priority=True)
except Exception:
    pass

OUTPUT_DIR       = WORKSPACE_DIR / "output"
AUDIO_DIR        = OUTPUT_DIR / "audio"
SUBTITLES_DIR    = OUTPUT_DIR / "subtitles"
TEMP_TTS_DIR     = OUTPUT_DIR / "temp_tts"
MODELS_DIR       = WORKSPACE_DIR / "models" / "rvc"
SLIDES_DATA_PATH = OUTPUT_DIR / "slides_data.json"

for d in [AUDIO_DIR, SUBTITLES_DIR, TEMP_TTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── 심야 설화 매칭 Edge TTS 파라미터 ─────────────────────────────
EDGE_TTS_CONFIG = {
    "voice": "ko-KR-SunHiNeural",
    "rate":  "-29%",
    "pitch": "-25Hz",
}

# ── RVC 설정 (GTX 1050 Ti 최적화) ────────────────────────────────
RVC_CONFIG = {
    "device":        "cuda:0",
    "f0_method":     "pm",
    "f0_up_key":     0,
    "index_rate":    0.75,
    "protect":       0.33,
    "filter_radius": 3,
    "resample_sr":   0,
    "rms_mix_rate":  0.25,
}


# ══════════════════════════════════════════════════════════════════
# 야담 텍스트 튜닝
# ══════════════════════════════════════════════════════════════════
def apply_yadām_style(text: str) -> str:
    """아나운서 어미 → 이야기꾼 어미 + 말줄임표 + 호흡 쉼표"""
    endings = [
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
    for old, new in endings:
        text = re.sub(old, new, text)

    text = re.sub(r'(?<!\.)\.(?!\.)', '...', text)

    pattern = re.compile(
        r'([가-힣]{4,})\s+(은|는|이|가|을|를|도|만|로|으로|에서|에게|보다|처럼|까지|부터)'
    )
    text = pattern.sub(r'\1, \2', text)
    return text.strip()


# ══════════════════════════════════════════════════════════════════
# 자막 생성
# ══════════════════════════════════════════════════════════════════
def split_into_clauses(text: str):
    clean = text.replace("...", "...|").replace(". ", ".|")
    parts = clean.split("|")
    return [p.strip() for p in parts if p.strip()] or [text.strip()]


def get_duration_s(file_path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 15.0


def write_srt(tuned_text: str, audio_path: Path, srt_path: Path):
    total_dur = get_duration_s(audio_path)
    clauses   = split_into_clauses(tuned_text)
    total_ch  = sum(len(c) for c in clauses)
    cues, t   = [], 0.0

    for i, clause in enumerate(clauses):
        ratio  = len(clause) / total_ch if total_ch > 0 else 1.0 / len(clauses)
        dur    = total_dur * ratio
        start  = t
        end    = start + dur if i < len(clauses) - 1 else total_dur
        t      = end

        def ts(s):
            m, sec = int(s // 60), int(s % 60)
            ms = int((s - int(s)) * 1000)
            return f"00:{m:02d}:{sec:02d},{ms:03d}"

        clean = clause.replace("...", "").replace("…", "").strip()
        cues.append(f"{i+1}\n{ts(start)} --> {ts(end)}\n{clean}\n")

    srt_path.write_text("\n".join(cues), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════
# Edge TTS 생성
# ══════════════════════════════════════════════════════════════════
async def generate_edge_tts(text: str, out_wav: Path):
    comm = edge_tts.Communicate(
        text,
        EDGE_TTS_CONFIG["voice"],
        rate  = EDGE_TTS_CONFIG["rate"],
        pitch = EDGE_TTS_CONFIG["pitch"],
    )
    await comm.save(str(out_wav))


# ══════════════════════════════════════════════════════════════════
# RVC 변환
# ══════════════════════════════════════════════════════════════════
def find_rvc_model(model_name: str = None):
    pth_files = sorted(MODELS_DIR.rglob("*.pth"))
    if not pth_files:
        pth_files = sorted((WORKSPACE_DIR / "models").rglob("*.pth"))
    if not pth_files:
        return None, None

    if model_name:
        matched = [p for p in pth_files if model_name.lower() in p.name.lower() or model_name.lower() in p.parent.name.lower()]
        pth = matched[0] if matched else pth_files[0]
    else:
        pth = pth_files[0]

    parent_indices = sorted(pth.parent.glob("*.index"))
    stem_indices = sorted(pth.parent.glob(f"*{pth.stem}*.index"))
    if stem_indices:
        idx = stem_indices[0]
    elif parent_indices:
        idx = parent_indices[0]
    else:
        all_indices = sorted(MODELS_DIR.rglob("*.index"))
        idx = all_indices[0] if all_indices else None

    return pth, idx



def rvc_convert(input_wav: Path, output_wav: Path,
                model_path: Path, index_path: Path = None,
                device: str = "cuda:0") -> bool:
    try:
        from rvc_python.infer import RVCInference
    except ImportError:
        print("❌ rvc-python 미설치. pip install rvc-python --no-deps")
        return False

    try:
        import torch
        if device.startswith("cuda") and not torch.cuda.is_available():
            device = "cpu"
    except ImportError:
        device = "cpu"

    def _run(dev):
        rvc = RVCInference(device=dev)
        rvc.load_model(str(model_path))
        rvc.infer_file(
            input_path   = str(input_wav),
            output_path  = str(output_wav),
            index_path   = str(index_path) if index_path else "",
            f0_method    = RVC_CONFIG["f0_method"],
            f0_up_key    = RVC_CONFIG["f0_up_key"],
            index_rate   = RVC_CONFIG["index_rate"],
            protect      = RVC_CONFIG["protect"],
            filter_radius= RVC_CONFIG["filter_radius"],
            resample_sr  = RVC_CONFIG["resample_sr"],
            rms_mix_rate = RVC_CONFIG["rms_mix_rate"],
        )

    try:
        _run(device)
        return True
    except RuntimeError as e:
        if "out of memory" in str(e).lower() and device != "cpu":
            print("   ⚠️  VRAM OOM → CPU 재시도...")
            try:
                import torch; torch.cuda.empty_cache()
                _run("cpu")
                return True
            except Exception as e2:
                print(f"   ❌ CPU 재시도 실패: {e2}")
        else:
            print(f"   ❌ RVC 오류: {e}")
        return False
    except Exception as e:
        print(f"   ❌ RVC 오류: {e}")
        return False


def wav_to_mp3(wav_path: Path, mp3_path: Path) -> bool:
    r = subprocess.run([
        "ffmpeg", "-y", "-i", str(wav_path),
        "-codec:a", "libmp3lame", "-qscale:a", "2", str(mp3_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


# ══════════════════════════════════════════════════════════════════
# 슬라이드 단위 처리
# ══════════════════════════════════════════════════════════════════
async def process_slide(slide: dict, idx: int,
                        use_rvc: bool,
                        model_path: Path = None,
                        index_path: Path = None) -> bool:
    idx_num      = slide.get("slide_index", idx)
    raw_script   = slide.get("voice_script") or slide.get("slide_screen_text", "")
    tuned_script = apply_yadām_style(raw_script)

    temp_wav  = TEMP_TTS_DIR / f"audio_{idx_num:03d}.wav"
    rvc_wav   = TEMP_TTS_DIR / f"rvc_{idx_num:03d}.wav"
    final_mp3 = AUDIO_DIR    / f"audio_{idx_num:03d}.mp3"
    srt_file  = SUBTITLES_DIR / f"slide_{idx_num:03d}.srt"

    t0 = time.time()

    # 1) Edge TTS → WAV
    try:
        await generate_edge_tts(tuned_script, temp_wav)
    except Exception as e:
        print(f"  [✗] Slide {idx_num:03d} Edge TTS 실패: {e}")
        return False

    if use_rvc and model_path:
        # 2) RVC 변환 WAV → WAV
        ok = rvc_convert(temp_wav, rvc_wav, model_path, index_path)
        if ok:
            # 3) RVC WAV → MP3
            if wav_to_mp3(rvc_wav, final_mp3):
                write_srt(tuned_script, final_mp3, srt_file)
                rvc_wav.unlink(missing_ok=True)
                temp_wav.unlink(missing_ok=True)
                print(f"  [✓] Slide {idx_num:03d} [RVC] ({time.time()-t0:.1f}s)")
                return True
        # RVC 실패 시 Edge TTS 결과로 fallback
        print(f"  [!] Slide {idx_num:03d} RVC 실패 → Edge TTS fallback")
        if wav_to_mp3(temp_wav, final_mp3):
            write_srt(tuned_script, final_mp3, srt_file)
            temp_wav.unlink(missing_ok=True)
            return True
        return False

    else:
        # RVC 없이 Edge TTS MP3만 생성
        if wav_to_mp3(temp_wav, final_mp3):
            write_srt(tuned_script, final_mp3, srt_file)
            temp_wav.unlink(missing_ok=True)
            print(f"  [✓] Slide {idx_num:03d} [TTS Only] ({time.time()-t0:.1f}s)")
            return True
        return False


# ══════════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════════
async def main():
    parser = argparse.ArgumentParser(description="Edge TTS + RVC 통합 파이프라인")
    parser.add_argument("--slide",   type=int, default=None, help="단일 슬라이드 번호 테스트")
    parser.add_argument("--from",    type=int, default=1,    dest="start_from", help="시작 슬라이드 번호")
    parser.add_argument("--no-rvc",  action="store_true", help="RVC 없이 Edge TTS만 실행")
    parser.add_argument("--model",   default=None, help=".pth 경로 (없으면 자동 탐색)")
    parser.add_argument("--index",   default=None, help=".index 경로")
    parser.add_argument("--device",  default="cuda:0", help="cuda:0 또는 cpu")
    args = parser.parse_args()

    # 슬라이드 데이터 로드
    if not SLIDES_DATA_PATH.exists():
        print(f"❌ {SLIDES_DATA_PATH} 없음. 먼저 build_full_120_slides.py 실행.")
        sys.exit(1)
    slides = json.load(open(SLIDES_DATA_PATH, "r", encoding="utf-8"))

    # 슬라이드 필터
    if args.slide:
        slides = [s for s in slides if s.get("slide_index") == args.slide]
        if not slides:
            print(f"❌ 슬라이드 {args.slide} 없음.")
            sys.exit(1)
    else:
        slides = [s for s in slides if s.get("slide_index", 0) >= args.start_from]

    use_rvc = not args.no_rvc
    model_path, index_path = None, None

    if use_rvc:
        if args.model:
            model_path = Path(args.model)
            index_path = Path(args.index) if args.index else None
        else:
            model_path, index_path = find_rvc_model()

        if not model_path:
            print("⚠️  RVC 모델(.pth) 없음 → Edge TTS 전용 모드로 전환")
            print("   모델 다운로드: python scripts/download_rvc_model.py")
            use_rvc = False
        else:
            RVC_CONFIG["device"] = args.device
            print(f"🎤 RVC 모델: {model_path.name}")
            if index_path:
                print(f"   인덱스:  {index_path.name}")
            print(f"   디바이스: {RVC_CONFIG['device']}")
            print(f"   F0 방법:  {RVC_CONFIG['f0_method']}")

    mode_tag = "Edge TTS + RVC" if use_rvc else "Edge TTS Only (야담 스타일)"
    print(f"\n🎙️  [{mode_tag}] {len(slides)}개 슬라이드 처리 시작")
    print(f"   Voice: {EDGE_TTS_CONFIG['voice']}")
    print(f"   Rate : {EDGE_TTS_CONFIG['rate']}  Pitch: {EDGE_TTS_CONFIG['pitch']}")
    print()

    success, failed = 0, []
    for i, slide in enumerate(slides, 1):
        ok = await process_slide(slide, i, use_rvc, model_path, index_path)
        if ok:
            success += 1
        else:
            failed.append(slide.get("slide_index", i))

    print(f"\n{'='*50}")
    print(f"✨ 완료: {success}/{len(slides)} 성공")
    if failed:
        print(f"❌ 실패 슬라이드: {failed}")
    print(f"📁 오디오: {AUDIO_DIR}")
    print(f"📁 자막:   {SUBTITLES_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
