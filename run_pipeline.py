"""
run_pipeline.py
───────────────
Edge-TTS + RVC 기반 중년 여성 스토리텔러 슬라이드 비디오 제작 파이프라인.

사용법:
  1. 단일 슬라이드 테스트 (1번 슬라이드: 렌더링 -> Edge-TTS -> RVC -> 비디오):
     python run_pipeline.py --slide 1

  2. RVC 모델 지정 및 처음 3개 슬라이드 일괄 제작:
     python run_pipeline.py --limit 3 --model JK_Narrator --merge

  3. 전체 120개 슬라이드 풀 파이프라인 실행:
     python run_pipeline.py --merge

  4. RVC 없이 Edge-TTS 음성만 사용할 때:
     python run_pipeline.py --slide 1 --no-rvc
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

WORKSPACE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR   = WORKSPACE_DIR / "scripts"


def run_command_stream(cmd: list[str]):
    print(f"\n▶ 실행: {' '.join(cmd)}")
    start_time = time.time()
    res = subprocess.run(cmd, text=True)
    elapsed = time.time() - start_time
    if res.returncode != 0:
        print(f"❌ 실패 (소요시간: {elapsed:.1f}초)")
        sys.exit(res.returncode)
    else:
        print(f"✨ 완료 (소요시간: {elapsed:.1f}초)")


def main():
    parser = argparse.ArgumentParser(description="Edge-TTS + RVC 자동 비디오 제작기")
    parser.add_argument("--slide", type=int, default=None, help="특정 슬라이드 번호만 처리")
    parser.add_argument("--limit", type=int, default=None, help="처리할 최대 슬라이드 수")
    parser.add_argument("--rate", type=str, default="-25%", help="말하기 속도 (기본: -25%)")
    parser.add_argument("--pitch", type=str, default="-22Hz", help="Edge-TTS 음조 피치 (기본: -22Hz)")
    parser.add_argument("--model", type=str, default="JK_Narrator", help="RVC 모델 이름 (기본: JK_Narrator)")
    parser.add_argument("--rvc-pitch", type=int, default=0, help="RVC 피치 변경 (반음 단위, 기본: 0)")
    parser.add_argument("--no-rvc", action="store_true", help="RVC 음색 변환을 건너뛰고 Edge-TTS 음성 사용")
    parser.add_argument("--step", type=str, choices=["all", "slides", "tts", "rvc", "video"], default="all", help="실행할 단계")
    parser.add_argument("--merge", action="store_true", help="비디오 세그먼트를 단일 풀타임 비디오로 최종 병합")
    args = parser.parse_args()

    common_args = []
    if args.slide:
        common_args.extend(["--slide", str(args.slide)])
    if args.limit:
        common_args.extend(["--limit", str(args.limit)])

    print("=" * 60)
    print("🎬 [Edge-TTS + RVC 중년 여성 스토리텔러] 비디오 제작 파이프라인 시작")
    print("=" * 60)

    # 1단계: 슬라이드 이미지 렌더링
    if args.step in ["all", "slides"]:
        print("\n[단계 1/4] 🖼️ 슬라이드 이미지 렌더링")
        run_command_stream([sys.executable, str(SCRIPTS_DIR / "01_render_slides.py")] + common_args)

    # 2단계: Edge-TTS 음성 및 SRT 자막 생성
    if args.step in ["all", "tts"]:
        print("\n[단계 2/4] 🎙️ Edge-TTS 기본 음성 및 SRT 자막 생성")
        tts_args = common_args + [f"--rate={args.rate}", f"--pitch={args.pitch}"]
        run_command_stream([sys.executable, str(SCRIPTS_DIR / "02_generate_edge_tts.py")] + tts_args)

    # 3단계: RVC 음색 변환
    if not args.no_rvc and (args.step in ["all", "rvc"]):
        print(f"\n[단계 3/4] 🎭 RVC 음색 변환 ({args.model})")
        rvc_args = common_args + [f"--model={args.model}", f"--pitch={args.rvc_pitch}"]
        run_command_stream([sys.executable, str(SCRIPTS_DIR / "02_b_rvc_changer.py")] + rvc_args)

    # 4단계: 비디오 세그먼트 렌더링
    if args.step in ["all", "video"]:
        print("\n[단계 4/4] 🎬 비디오 세그먼트 렌더링")
        run_command_stream([sys.executable, str(SCRIPTS_DIR / "03_render_video.py")] + common_args)

        # 최종 병합 옵션
        if args.merge:
            print("\n[최종 단계] 🎞️ 전체 세그먼트 결합 및 풀타임 비디오 출력")
            run_command_stream([sys.executable, str(SCRIPTS_DIR / "03_render_video.py"), "--merge"])

    print("\n" + "=" * 60)
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
    print("=" * 60)


if __name__ == "__main__":
    main()
