"""
02_b_rvc_changer.py
───────────────────
Edge-TTS로 생성된 오디오를 RVC (Retrieval-based Voice Conversion) 모델로
목표 음색(JK_Narrator 등)으로 변환합니다.
"""

import argparse
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR    = WORKSPACE_DIR / "output"
AUDIO_DIR     = OUTPUT_DIR / "audio"
MODELS_DIR    = WORKSPACE_DIR / "models" / "rvc"

sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))
from rvc_engine import RVCStandaloneInfer


def find_rvc_model(model_name: str = None):
    pth_files = sorted(MODELS_DIR.rglob("*.pth"))
    if not pth_files:
        return None, None

    if model_name:
        matched = [p for p in pth_files if model_name.lower() in p.name.lower() or model_name.lower() in p.parent.name.lower()]
        pth = matched[0] if matched else pth_files[0]
    else:
        # 기본값: JK_Narrator 우선
        jk = [p for p in pth_files if "narrator" in p.parent.name.lower() or "jk" in p.parent.name.lower()]
        pth = jk[0] if jk else pth_files[0]

    parent_indices = sorted(pth.parent.glob("*.index"))
    idx = parent_indices[0] if parent_indices else None
    return pth, idx


def main():
    parser = argparse.ArgumentParser(description="RVC 보이스 체인저")
    parser.add_argument("--slide", type=int, default=None, help="변환할 특정 슬라이드 번호")
    parser.add_argument("--model", type=str, default="JK_Narrator", help="RVC 모델 이름")
    parser.add_argument("--pitch", type=int, default=0, help="RVC 피치 변경 (반음 단위, 기본: 0)")
    parser.add_argument("--index-rate", type=float, default=0.6, help="인덱스 특징 반영 비율 (0.0~1.0)")
    parser.add_argument("--limit", type=int, default=None, help="최대 변환 슬라이드 개수")
    args = parser.parse_args()

    model_path, index_path = find_rvc_model(args.model)
    if not model_path:
        print(f"❌ RVC 모델을 찾을 수 없습니다: {args.model}")
        return

    print(f"🎤 RVC 모델 로드: {model_path.parent.name} ({model_path.name})")
    infer_engine = RVCStandaloneInfer(model_path, index_path)

    if args.slide:
        in_wav = AUDIO_DIR / f"slide_{args.slide:03d}.wav"
        out_wav = AUDIO_DIR / f"slide_{args.slide:03d}.wav"
        out_mp3 = AUDIO_DIR / f"slide_{args.slide:03d}.mp3"
        temp_wav = AUDIO_DIR / f"temp_rvc_{args.slide:03d}.wav"

        if not in_wav.exists():
            print(f"❌ 입력 오디오 파일이 없습니다: {in_wav}")
            return

        print(f"[{args.slide:03d}] 🔄 RVC 음색 변환 중...")
        infer_engine.convert(in_wav, temp_wav, f0_up_key=args.pitch, index_rate=args.index_rate)

        # 변환된 오디오를 최종 MP3 및 WAV로 덮어쓰기
        if temp_wav.exists():
            temp_wav.replace(out_wav)
            cmd = [
                "ffmpeg", "-y", "-i", str(out_wav),
                "-codec:a", "libmp3lame", "-b:a", "192k",
                str(out_mp3)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[{args.slide:03d}] ✅ RVC 변환 및 MP3 갱신 완료 -> {out_mp3.name}")
    else:
        wav_files = sorted(AUDIO_DIR.glob("slide_*.wav"))
        print(f"🚀 총 {len(wav_files)}개 오디오 RVC 변환 시작...")
        count = 0
        for w in wav_files:
            try:
                idx = int(w.stem.split("_")[1])
            except Exception:
                continue

            temp_wav = AUDIO_DIR / f"temp_rvc_{idx:03d}.wav"
            out_mp3 = AUDIO_DIR / f"slide_{idx:03d}.mp3"

            print(f"[{idx:03d}] 🔄 RVC 음색 변환 중...")
            infer_engine.convert(w, temp_wav, f0_up_key=args.pitch, index_rate=args.index_rate)

            if temp_wav.exists():
                temp_wav.replace(w)
                cmd = [
                    "ffmpeg", "-y", "-i", str(w),
                    "-codec:a", "libmp3lame", "-b:a", "192k",
                    str(out_mp3)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            count += 1
            if args.limit and count >= args.limit:
                break
        print(f"🎉 모든 오디오 RVC 변환 완료! ({count}개)")


if __name__ == "__main__":
    main()
