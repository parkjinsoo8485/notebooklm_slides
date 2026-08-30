"""
03_render_video.py
──────────────────
슬라이드 이미지(PNG)와 내레이션 오디오(MP3/WAV), SRT 자막을 결합하여
슬라이드별 개별 비디오 클립 및 전체 풀타임 비디오를 렌더링합니다.
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
IMAGES_DIR    = OUTPUT_DIR / "images"
AUDIO_DIR     = OUTPUT_DIR / "audio"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
SEGMENTS_DIR  = OUTPUT_DIR / "segments"

SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)


def get_audio_duration(file_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 10.0


def render_slide_segment(slide_idx: int, burn_subtitles: bool = True) -> Path:
    img_path = IMAGES_DIR / f"slide_{slide_idx:03d}.png"
    audio_path = AUDIO_DIR / f"slide_{slide_idx:03d}.mp3"
    srt_path = SUBTITLES_DIR / f"slide_{slide_idx:03d}.srt"
    out_mp4 = SEGMENTS_DIR / f"segment_{slide_idx:03d}.mp4"

    if not img_path.exists() or not audio_path.exists():
        print(f"[{slide_idx:03d}] ⚠️ 이미지 또는 오디오 파일이 없어 비디오 렌더링을 건너뜁니다.")
        return None

    dur = get_audio_duration(audio_path)

    # Windows 경로 FFmpeg 자막 필터 이스케이프
    if burn_subtitles and srt_path.exists():
        escaped_srt = str(srt_path.resolve()).replace("\\", "/").replace(":", "\\:")
        # 한글 폰트 및 프리미엄 자막 스타일링
        subtitle_filter = (
            f"subtitles='{escaped_srt}':force_style='"
            f"Fontname=Pretendard,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"BackColour=&H80000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=30,Alignment=2'"
        )
        vf = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p,{subtitle_filter}"
    else:
        vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img_path),
        "-i", str(audio_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{dur:.2f}",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_mp4)
    ]

    print(f"[{slide_idx:03d}] 🎬 비디오 렌더링 중 ({dur:.1f}초)...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print(f"[{slide_idx:03d}] ✅ 비디오 세그먼트 완료 -> {out_mp4.name}")
        return out_mp4
    else:
        print(f"[{slide_idx:03d}] ❌ FFmpeg 렌더링 실패: {res.stderr[-300:]}")
        return None


def merge_all_segments(out_filename: str = "storybook_full_video.mp4"):
    segments = sorted(SEGMENTS_DIR.glob("segment_*.mp4"))
    if not segments:
        print("❌ 병합할 비디오 세그먼트가 없습니다.")
        return

    concat_list = SEGMENTS_DIR / "concat_list.txt"
    lines = [f"file '{p.resolve().as_posix()}'" for p in segments]
    concat_list.write_text("\n".join(lines), encoding="utf-8")

    out_path = OUTPUT_DIR / out_filename
    print(f"🎞️ 총 {len(segments)}개 세그먼트 결합 중 -> {out_path.name}...")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(out_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print(f"🎉 전체 비디오 병합 완성! -> {out_path}")
    else:
        print(f"❌ 병합 실패: {res.stderr[-300:]}")


def main():
    parser = argparse.ArgumentParser(description="슬라이드 비디오 렌더러")
    parser.add_argument("--slide", type=int, default=None, help="렌더링할 특정 슬라이드 번호")
    parser.add_argument("--merge", action="store_true", help="생성된 모든 세그먼트를 단일 비디오로 병합")
    parser.add_argument("--no-subtitles", action="store_true", help="자막 버닝 비활성화")
    parser.add_argument("--limit", type=int, default=None, help="최대 처리 슬라이드 수")
    args = parser.parse_args()

    if args.merge:
        merge_all_segments()
        return

    if args.slide:
        render_slide_segment(args.slide, burn_subtitles=not args.no_subtitles)
    else:
        img_files = sorted(IMAGES_DIR.glob("slide_*.png"))
        print(f"🎬 총 {len(img_files)}개 슬라이드 비디오 렌더링 시작...")
        count = 0
        for img in img_files:
            try:
                idx = int(img.stem.split("_")[1])
            except Exception:
                continue
            render_slide_segment(idx, burn_subtitles=not args.no_subtitles)
            count += 1
            if args.limit and count >= args.limit:
                break
        print(f"🎉 총 {count}개 비디오 세그먼트 생성 완료!")


if __name__ == "__main__":
    main()
