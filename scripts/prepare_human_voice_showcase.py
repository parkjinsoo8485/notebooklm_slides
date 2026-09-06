import os, sys, subprocess
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

OUT_DIR = Path(r"C:\My_Project\src\notebooklm_slides\output\human_voice_showcase")
OUT_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR = Path(r"C:\My_Project\src\notebooklm_slides\references")

print("🎙️ 1. 기존 보유 레퍼런스 음원 처리 중...")
if (REF_DIR / "narrator_ref.wav").exists():
    out_mp3 = OUT_DIR / "01_korean_historical_narrator.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(REF_DIR / "narrator_ref.wav"),
        "-t", "90", "-b:a", "192k", str(out_mp3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   ✅ [01] 고전 야담 전문 나레이터 (약 1분 10초) 준비 완료")

# 유튜브 공공/오픈 낭독 영상에서 구간 추출
clips = [
    {
        "id": "82pnjKTLWms",
        "name": "02_authentic_yadam_storyteller.mp3",
        "title": "구수한 조선 야담 전문 이야기꾼 (실제 육성 낭독)",
        "start": "60",
        "duration": "150"
    },
    {
        "id": "FHN7gh1JKGE",
        "name": "03_elderly_grandfather_folklore.mp3",
        "title": "따뜻하고 깊이 있는 할아버지 전래동화 구연 (실제 육성)",
        "start": "30",
        "duration": "150"
    }
]

for c in clips:
    mp3_path = OUT_DIR / c["name"]
    if mp3_path.exists() and mp3_path.stat().st_size > 100000:
        print(f"   ✅ [{c['name']}] 이미 다운로드 완료됨")
        continue
        
    print(f"⬇️ 다운로드 및 추출 중: {c['title']}...")
    raw_audio = OUT_DIR / f"temp_{c['id']}.webm"
    try:
        # yt-dlp 오디오 다운로드
        subprocess.run([
            sys.executable, "-m", "yt_dlp",
            "-f", "ba",
            "-o", str(raw_audio),
            f"https://www.youtube.com/watch?v={c['id']}"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        
        if raw_audio.exists():
            subprocess.run([
                "ffmpeg", "-y", "-i", str(raw_audio),
                "-ss", c["start"], "-t", c["duration"],
                "-b:a", "192k", str(mp3_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            raw_audio.unlink(missing_ok=True)
            print(f"   ✅ {c['name']} 추출 완료 ({c['duration']}초)")
    except Exception as e:
        print(f"   ⚠️ 다운로드 예외 ({c['id']}): {e}")

print("✨ 음원 준비 완료!")
