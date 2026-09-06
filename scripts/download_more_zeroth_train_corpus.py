#!/usr/bin/env python3
"""
download_more_zeroth_train_corpus.py
────────────────────────────────────
Zeroth-Korean 대규모 스튜디오 훈련 원음 코퍼스 (CC BY 4.0) 추가 다운로더
Hugging Face에서 train split (0.parquet, 약 499MB)을 다운로드하고
GPT-SoVITS 훈련 데이터셋으로 일괄 변환하여 저장합니다.
"""

import sys, os, io, urllib.request, time
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
SAVE_PATH = WORKSPACE / "data" / "clean_public_voices" / "zeroth_train_0.parquet"
SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

URL = "https://huggingface.co/api/datasets/kresnik/zeroth_korean/parquet/default/train/0.parquet"

def download():
    print("=" * 80)
    print("📥 Zeroth-Korean Train 대규모 스튜디오 오픈 원음 다운로드 시작")
    print(f"🔗 URL : {URL}")
    print(f"📁 저장 : {SAVE_PATH}")
    print("=" * 80)

    if SAVE_PATH.exists() and SAVE_PATH.stat().st_size > 400 * 1024 * 1024:
        print("✅ 이미 파일이 존재합니다!")
        return

    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(SAVE_PATH, "wb") as out_f:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        t0 = time.time()
        last_log = t0

        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_log > 3.0:
                mb = downloaded / (1024 * 1024)
                pct = (downloaded / total * 100) if total else 0
                speed = mb / (now - t0 + 1e-5)
                print(f"   ⏳ 다운로드 진행 중: {mb:.1f}MB / {total/(1024*1024):.1f}MB ({pct:.1f}%) - {speed:.1f} MB/s")
                last_log = now

    print(f"\n🎉 다운로드 완료! 파일 크기: {SAVE_PATH.stat().st_size / (1024*1024):.1f}MB")

if __name__ == "__main__":
    download()
