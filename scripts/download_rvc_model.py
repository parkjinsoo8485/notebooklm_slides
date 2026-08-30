"""
download_rvc_model.py
─────────────────────
Hugging Face에서 한국어 나레이션 / 보이스 RVC 공개 모델(.pth + .index)을
models/ 디렉터리로 자동 다운로드 및 구성하는 스크립트.

주요 프리셋:
  - iu (기본): 한국어 여성 맑은 서사형 나레이션 (jantz/IU-RVC_V2-300_Epochs)
  - jungkook: 한국어 남성 차분한 중저음 나레이션 (binant/Jungkook__BTS___RVC_V2_-_1000_Epochs_)
  - iu_1k: 한국어 여성 보이스 1000 epoch (Zonas/RVC2-IU-1K)

사용법:
  python scripts/download_rvc_model.py                      # 기본 한국어 나레이터(IU) 다운로드
  python scripts/download_rvc_model.py --preset jungkook     # 남성 나레이터 다운로드
  python scripts/download_rvc_model.py --preset all          # 추천 모델 전체 다운로드
  python scripts/download_rvc_model.py --model <repo_id>    # 임의의 HuggingFace repo 다운로드
  python scripts/download_rvc_model.py --list                # 사용 가능한 프리셋 및 다운로드된 모델 확인
"""

import argparse
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR    = WORKSPACE_DIR / "models" / "rvc"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ── 추천 한국어 나레이션 / 보이스 계열 공개 모델 프리셋 ─────────────
KOREAN_RVC_PRESETS = {
    "iu": {
        "name": "한국어 여성 나레이션 (IU v2 - 300 Epochs)",
        "repo_id": "jantz/IU-RVC_V2-300_Epochs",
        "description": "오디오북/나레이션에 최적화된 맑고 명료한 한국어 여성 음색",
        "target_dir": "IU_Narrator",
        "files": [
            "IU_v1.0-RVC_v2.pth",
            "added_IVF4383_Flat_nprobe_1_IU_v1.0-RVC_v2_v2.index"
        ]
    },
    "jungkook": {
        "name": "한국어 남성 나레이션 (Jungkook v2 - 1000 Epochs)",
        "repo_id": "binant/Jungkook__BTS___RVC_V2_-_1000_Epochs_",
        "description": "차분하고 안정적인 한국어 남성 음색 (1000 Epochs 고학습 모델)",
        "target_dir": "JK_Narrator",
        "files": [
            "model.pth",
            "model.index"
        ]
    },
    "iu_1k": {
        "name": "한국어 여성 나레이션 (IU 1K Epochs)",
        "repo_id": "Zonas/RVC2-IU-1K",
        "description": "부드럽고 자연스러운 한국어 여성 음색",
        "target_dir": "IU_1K",
        "files": [
            "IU-Zonas.pth",
            "added_IVF1231_Flat_nprobe_1_IU-Zonas_v2.index"
        ]
    }
}

DEFAULT_PRESET = "iu"


def format_size(bytes_num: int) -> str:
    """바이트 수를 읽기 쉬운 단위로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.2f} TB"


def download_stream(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    """진행률 표시 스트리밍 다운로드 (HF direct resolve URL)"""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get("content-length", 0))
                print(f"      크기: {format_size(total_size)}")
                downloaded = 0
                start_time = time.time()

                with open(temp_path, "wb") as f:
                    while True:
                        chunk = response.read(1024 * 1024)  # 1MB 버퍼
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        elapsed = max(time.time() - start_time, 0.001)
                        speed = downloaded / elapsed
                        percent = (downloaded / total_size * 100) if total_size > 0 else 0
                        print(
                            f"\r      진행률: [{percent:5.1f}%] {format_size(downloaded)} / {format_size(total_size)} "
                            f"({format_size(int(speed))}/s)",
                            end="",
                            flush=True
                        )

            print()  # 개행
            if temp_path.exists():
                if dest_path.exists():
                    dest_path.unlink()
                temp_path.rename(dest_path)
            return True

        except Exception as e:
            print(f"\n      ⚠️ [시도 {attempt}/{max_retries}] 오류: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            if attempt < max_retries:
                time.sleep(2 * attempt)
            else:
                return False

    return False


def download_repo_files(repo_id: str, target_dir_name: str = None, explicit_files: list = None) -> bool:
    """Hugging Face Hub에서 .pth 및 .index 파일을 감지하여 다운로드"""
    safe_name = target_dir_name or repo_id.replace("/", "__")
    dest_dir = MODELS_DIR / safe_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 모델 다운로드 시작: {repo_id}")
    print(f"   📁 저장 폴더: {dest_dir.relative_to(WORKSPACE_DIR)}")

    target_files = explicit_files
    if not target_files:
        try:
            from huggingface_hub import HfApi
            api = HfApi()
            all_files = list(api.list_repo_files(repo_id))
            target_files = [f for f in all_files if f.lower().endswith((".pth", ".index", ".pt"))]
        except Exception as e:
            print(f"   ℹ️ Repo 파일 목록 조회 실패({e}). 기본 파일 탐색 시도.")
            target_files = []

    if not target_files:
        print(f"   ❌ 대상 .pth/.index 파일을 찾을 수 없습니다: {repo_id}")
        return False

    print(f"   🎯 다운로드 대상 파일 ({len(target_files)}개):")
    for f in target_files:
        print(f"      - {f}")

    success_all = True
    for fname in target_files:
        local_filename = Path(fname).name
        dest_file = dest_dir / local_filename

        if dest_file.exists() and dest_file.stat().st_size > 1024:
            print(f"   ✅ [이미 존재] {local_filename} ({format_size(dest_file.stat().st_size)})")
            continue

        url = f"https://huggingface.co/{repo_id}/resolve/main/{fname}"
        print(f"\n   ⬇️ 다운로드 중: {local_filename}")
        print(f"      URL: {url}")
        ok = download_stream(url, dest_file)
        if not ok:
            success_all = False
            print(f"      ❌ {local_filename} 다운로드 실패")

    # 다운로드 결과 확인
    pth_list = list(dest_dir.rglob("*.pth")) + list(dest_dir.rglob("*.pt"))
    idx_list = list(dest_dir.rglob("*.index"))

    print(f"\n📦 [{safe_name}] 구성 완료:")
    for p in pth_list:
        print(f"   🎵 모델 가중치 (.pth): {p.relative_to(WORKSPACE_DIR)} ({format_size(p.stat().st_size)})")
    for i in idx_list:
        print(f"   🔍 특징 인덱스 (.index): {i.relative_to(WORKSPACE_DIR)} ({format_size(i.stat().st_size)})")

    return success_all


def list_catalog():
    """사용 가능한 프리셋 및 로컬에 이미 다운로드된 모델 현황 출력"""
    print("\n" + "=" * 70)
    print("  📋 Hugging Face 한국어 나레이션 / 보이스 RVC 모델 카탈로그")
    print("=" * 70)

    for key, info in KOREAN_RVC_PRESETS.items():
        print(f"\n🔹 프리셋: [{key}]")
        print(f"   이름 : {info['name']}")
        print(f"   Repo : https://huggingface.co/{info['repo_id']}")
        print(f"   설명 : {info['description']}")
        print(f"   파일 : {', '.join(info['files'])}")

    print("\n" + "-" * 70)
    print("  📂 현재 models/ 디렉터리 내 보유 모델 현황")
    print("-" * 70)
    pth_files = sorted(MODELS_DIR.rglob("*.pth"))
    idx_files = sorted(MODELS_DIR.rglob("*.index"))

    if not pth_files:
        print("   (아직 다운로드된 .pth 모델이 없습니다.)")
    else:
        for p in pth_files:
            paired_idx = [i for i in idx_files if i.parent == p.parent]
            idx_name = paired_idx[0].name if paired_idx else "없음 (가중치 단독 사용 가능)"
            print(f"   🎤 모델: {p.relative_to(WORKSPACE_DIR)} ({format_size(p.stat().st_size)})")
            print(f"      ↳ 인덱스: {idx_name}")

    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Hugging Face 한국어 RVC 나레이션 모델 자동 다운로더")
    parser.add_argument("--preset", default=DEFAULT_PRESET, choices=list(KOREAN_RVC_PRESETS.keys()) + ["all"],
                        help=f"다운로드할 프리셋 선택 (기본값: {DEFAULT_PRESET})")
    parser.add_argument("--model", default=None, help="커스텀 HuggingFace repo_id (예: author/repo)")
    parser.add_argument("--name", default=None, help="커스텀 저장 폴더명")
    parser.add_argument("--list", action="store_true", help="추천 프리셋 및 보유 모델 목록 출력")
    args = parser.parse_args()

    if args.list:
        list_catalog()
        return

    print("=" * 70)
    print("  🎙️ Hugging Face 한국어 나레이션 RVC 모델 자동 다운로더")
    print("=" * 70)

    if args.model:
        download_repo_files(args.model, args.name)
    elif args.preset == "all":
        for k, p in KOREAN_RVC_PRESETS.items():
            download_repo_files(p["repo_id"], p["target_dir"], p["files"])
    else:
        preset_info = KOREAN_RVC_PRESETS[args.preset]
        download_repo_files(preset_info["repo_id"], preset_info["target_dir"], preset_info["files"])

    print("\n✨ 모든 작업이 완료되었습니다!")
    list_catalog()


if __name__ == "__main__":
    main()
