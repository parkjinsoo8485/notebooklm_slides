"""
05_rvc_convert.py
─────────────────
Edge TTS WAV 파일을 RVC 모델로 음성 변환한다.
GTX 1050 Ti (VRAM 4GB) 최적화:
  - f0_method = "pm"  (가볍고 안정적)
  - 문장 단위 분할 → 순차 변환 (OOM 방지)

단독 실행 (테스트):
    python scripts/05_rvc_convert.py --input output/temp_tts/audio_001.wav --slide 1
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))
try:
    from optimize_performance import optimize_system_and_torch
    optimize_system_and_torch(max_cpu_threads=2, lower_priority=True)
except Exception:
    pass

OUTPUT_DIR    = WORKSPACE_DIR / "output"
AUDIO_DIR     = OUTPUT_DIR / "audio"
TEMP_TTS_DIR  = OUTPUT_DIR / "temp_tts"
MODELS_DIR    = WORKSPACE_DIR / "models" / "rvc"

# ── RVC 기본 설정 (GTX 1050 Ti 최적화) ──────────────────────────
RVC_CONFIG = {
    "device":      "cuda:0",   # GPU 사용 (CPU로 전환 시 "cpu")
    "f0_method":   "pm",       # pm: 빠르고 VRAM 절약 | harvest: 품질↑ 연산↑
    "f0_up_key":   0,          # 동성 변환이므로 피치 이동 없음 (남→남: 0, 여→남: -12)
    "index_rate":  0.75,       # 음색 특징 반영 비율 (0.0~1.0)
    "protect":     0.33,       # 무성음 보호 비율
    "filter_radius": 3,        # 피치 스무딩 반경 (노이즈 감소)
    "resample_sr": 0,          # 출력 샘플레이트 (0=모델 기본값 유지)
    "rms_mix_rate": 0.25,      # 볼륨 포락선 혼합 비율
}


def find_model_files(model_name: str = None):
    """models/rvc/ 및 models/ 에서 .pth + .index 파일 자동 탐색"""
    pth_files = sorted(MODELS_DIR.rglob("*.pth"))
    if not pth_files:
        # models/ 루트도 탐색
        pth_files = sorted((WORKSPACE_DIR / "models").rglob("*.pth"))
    if not pth_files:
        return None, None

    if model_name:
        matched = [p for p in pth_files if model_name.lower() in p.name.lower() or model_name.lower() in p.parent.name.lower()]
        pth = matched[0] if matched else pth_files[0]
    else:
        pth = pth_files[0]

    # 1순위: 동일 디렉터리 내 .index 파일
    parent_indices = sorted(pth.parent.glob("*.index"))
    # 2순위: stem과 일치하는 .index
    stem_indices = sorted(pth.parent.glob(f"*{pth.stem}*.index"))
    
    if stem_indices:
        idx = stem_indices[0]
    elif parent_indices:
        idx = parent_indices[0]
    else:
        all_indices = sorted(MODELS_DIR.rglob("*.index"))
        idx = all_indices[0] if all_indices else None

    return pth, idx



def convert_wav_rvc(
    input_wav:  Path,
    output_wav: Path,
    model_path: Path,
    index_path: Path = None,
    config: dict = None,
) -> bool:
    """
    단일 WAV 파일을 RVC로 변환한다.
    Returns True on success, False on failure.
    """
    cfg = config or RVC_CONFIG

    try:
        from rvc_python.infer import RVCInference
    except ImportError:
        print("❌ rvc-python 미설치: pip install rvc-python --no-deps")
        return False

    # VRAM 부족 시 CPU fallback
    device = cfg["device"]
    try:
        import torch
        if device.startswith("cuda") and not torch.cuda.is_available():
            print("⚠️  CUDA 사용 불가 → CPU 모드로 전환")
            device = "cpu"
    except ImportError:
        device = "cpu"

    try:
        rvc = RVCInference(device=device)
        rvc.load_model(str(model_path))

        rvc.infer_file(
            input_path  = str(input_wav),
            output_path = str(output_wav),
            index_path  = str(index_path) if index_path else "",
            f0_method   = cfg["f0_method"],
            f0_up_key   = cfg["f0_up_key"],
            index_rate  = cfg["index_rate"],
            protect     = cfg["protect"],
            filter_radius   = cfg["filter_radius"],
            resample_sr     = cfg["resample_sr"],
            rms_mix_rate    = cfg["rms_mix_rate"],
        )
        return True

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"⚠️  VRAM 부족 (OOM) → CPU 재시도...")
            try:
                import torch; torch.cuda.empty_cache()
                rvc2 = RVCInference(device="cpu")
                rvc2.load_model(str(model_path))
                rvc2.infer_file(
                    input_path  = str(input_wav),
                    output_path = str(output_wav),
                    index_path  = str(index_path) if index_path else "",
                    f0_method   = cfg["f0_method"],
                    f0_up_key   = cfg["f0_up_key"],
                    index_rate  = cfg["index_rate"],
                )
                return True
            except Exception as e2:
                print(f"❌ CPU 재시도도 실패: {e2}")
                return False
        print(f"❌ RVC 변환 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ RVC 변환 오류: {e}")
        return False


def convert_slide(slide_num: int, model_path: Path, index_path: Path = None) -> bool:
    """슬라이드 번호로 temp_tts WAV → audio 최종 MP3 변환"""
    input_wav  = TEMP_TTS_DIR / f"audio_{slide_num:03d}.wav"
    output_wav = TEMP_TTS_DIR / f"rvc_{slide_num:03d}.wav"
    final_mp3  = AUDIO_DIR    / f"audio_{slide_num:03d}.mp3"

    if not input_wav.exists():
        print(f"  [skip] {input_wav.name} 없음 (Edge TTS 미생성)")
        return False

    t0 = time.time()
    ok = convert_wav_rvc(input_wav, output_wav, model_path, index_path)
    elapsed = time.time() - t0

    if not ok:
        print(f"  [✗] Slide {slide_num:03d} RVC 실패 ({elapsed:.1f}s)")
        return False

    # WAV → MP3 변환 (ffmpeg)
    result = subprocess.run([
        "ffmpeg", "-y", "-i", str(output_wav),
        "-codec:a", "libmp3lame", "-qscale:a", "2",
        str(final_mp3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode == 0:
        print(f"  [✓] Slide {slide_num:03d}: {final_mp3.name} ({elapsed:.1f}s)")
        output_wav.unlink(missing_ok=True)  # 임시 WAV 삭제
        return True
    else:
        print(f"  [✗] Slide {slide_num:03d} MP3 변환 실패")
        return False


def main():
    parser = argparse.ArgumentParser(description="RVC 음성 변환 (단독 실행용)")
    parser.add_argument("--input",   help="변환할 WAV 파일 경로")
    parser.add_argument("--output",  help="출력 WAV 경로")
    parser.add_argument("--slide",   type=int, help="슬라이드 번호 (temp_tts 사용)")
    parser.add_argument("--model",   help=".pth 모델 파일 경로 (없으면 자동 탐색)")
    parser.add_argument("--index",   help=".index 파일 경로 (선택)")
    parser.add_argument("--device",  default=None, help="cuda:0 또는 cpu")
    args = parser.parse_args()

    # 모델 파일 결정
    if args.model:
        model_path = Path(args.model)
        index_path = Path(args.index) if args.index else None
    else:
        model_path, index_path = find_model_files()
        if not model_path:
            print("❌ 모델 파일(.pth)이 없습니다.")
            print(f"   먼저 실행: python scripts/download_rvc_model.py")
            print(f"   또는 .pth 파일을 {MODELS_DIR} 에 복사하세요.")
            sys.exit(1)
        print(f"🎤 모델 자동 탐색: {model_path.name}")
        if index_path:
            print(f"   인덱스: {index_path.name}")

    cfg = dict(RVC_CONFIG)
    if args.device:
        cfg["device"] = args.device

    if args.slide:
        ok = convert_slide(args.slide, model_path, index_path)
        sys.exit(0 if ok else 1)

    elif args.input and args.output:
        ok = convert_wav_rvc(
            Path(args.input), Path(args.output),
            model_path, index_path, cfg
        )
        sys.exit(0 if ok else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
