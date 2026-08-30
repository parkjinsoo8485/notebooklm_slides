import asyncio
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
SCRIPTS_DIR = WORKSPACE_DIR / "scripts"
OUTPUT_DIR = WORKSPACE_DIR / "output"
FINAL_VIDEO_PATH = OUTPUT_DIR / "storybook_1hour_final_video.mp4"

def run_step(step_name, cmd_args):
    print(f"\n=======================================================")
    print(f"🚀 [STEP] {step_name}")
    print(f"=======================================================")
    start_t = time.time()
    res = subprocess.run(cmd_args, cwd=str(WORKSPACE_DIR))
    if res.returncode != 0:
        print(f"❌ {step_name} 실패 (Exit code: {res.returncode})")
        sys.exit(res.returncode)
    elapsed = time.time() - start_t
    print(f"✅ {step_name} 완료! (소요시간: {elapsed:.1f}초)")

def main():
    print("🎬 [조선 야담 동화책] 전체 자동화 제작 파이프라인 가동")
    print("-------------------------------------------------------")
    print("1. 슬라이드: 48px 대형 명조 타이포그래피 + 120장 고유 일러스트 렌더링")
    print("2. 오디오/자막: Microsoft Sunhi 0.85x 1인 낭독 + 단일행(1줄) 교체형 SRT")
    print("3. 영상 합성: 무손실 안전 시네마틱 모션 적용 43분 1080p MP4 렌더링")
    print("-------------------------------------------------------")

    # Step 1: 슬라이드 렌더링
    run_step("1단계: 동화책 슬라이드 120장 렌더링", [sys.executable, str(SCRIPTS_DIR / "render_storybook_slides.py")])

    # Step 2: TTS 음성 & 단일행 SRT 생성
    run_step("2단계: Sunhi 1인 낭독 음성 및 단일행 SRT 생성", [sys.executable, str(SCRIPTS_DIR / "04_generate_tts.py")])

    # Step 3: 최종 비디오 렌더링 & Concat 병합
    run_step("3단계: 1080p 시네마틱 최종 비디오 렌더링", [sys.executable, str(SCRIPTS_DIR / "05_render_video.py"), str(FINAL_VIDEO_PATH)])

    print("\n🎉🎉🎉 [축하합니다!] 모든 제작 과정이 100% 성공적으로 완료되었습니다!")
    print(f"👉 최종 완성 영상 경로: {FINAL_VIDEO_PATH}")

if __name__ == "__main__":
    main()
