import os
import sys
import json
import subprocess
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "output"
STORYBOOK_DIR = OUTPUT_DIR / "storybook_slides"
STUDIO_IMAGES_DIR = OUTPUT_DIR / "studio_images"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
TEMP_SEGMENTS_DIR = OUTPUT_DIR / "segments"
DEFAULT_FINAL_VIDEO_PATH = OUTPUT_DIR / "full_story_1hour_video.mp4"
SLIDES_DATA_PATH = OUTPUT_DIR / "slides_data.json"

TEMP_SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)

def find_slide_image(idx_num):
    candidates = [
        STORYBOOK_DIR / f"storybook_{idx_num:03d}.png",
        IMAGES_DIR / f"slide_{idx_num:03d}.png",
        STUDIO_IMAGES_DIR / f"slide_{idx_num:03d}.png",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def find_audio_file(idx_num):
    candidates = [
        AUDIO_DIR / f"audio_{idx_num:03d}.mp3",
        AUDIO_DIR / f"slide_{idx_num:03d}.mp3",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def get_audio_duration(audio_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 5.0

AMBIENCE_PATH = WORKSPACE_DIR / "templates" / "assets" / "night_ambience_bed.mp3"

def render_segment(img_path, audio_path, out_seg_path, duration, idx_num=1):
    # duration에 0.6초 여유를 두어 음성과 여운이 자연스럽게 넘어가도록 함
    total_duration = duration + 0.6
    fps = 25
    total_frames = int(total_duration * fps)

    # 100% 안전하고 편안한 미세 호흡 모션 (1.00x ~ 1.025x)
    motion_type = idx_num % 4

    if motion_type == 0:
        v_filter = f"scale=1920:1080,zoompan=z='min(zoom+0.0001,1.025)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"
    elif motion_type == 1:
        v_filter = f"scale=1920:1080,zoompan=z='if(lte(zoom,1.0),1.025,max(1.0005,zoom-0.0001))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"
    elif motion_type == 2:
        v_filter = f"scale=1920:1080,zoompan=z='min(zoom+0.00008,1.02)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih*0.4/zoom)':s=1920x1080:fps={fps}"
    else:
        v_filter = f"scale=1920:1080,zoompan=z='min(zoom+0.00006,1.015)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"

    # 오디오 믹싱: 음성 100% + 배경 앰비언스 -26dB 마스킹 믹싱
    if AMBIENCE_PATH.exists():
        filter_complex = (
            f"[0:v]{v_filter}[v]; "
            f"[1:a]volume=1.0[voice]; "
            f"[2:a]volume=-26dB,aloop=loop=-1:size=2e+09[bg]; "
            f"[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-i", str(audio_path),
            "-i", str(AMBIENCE_PATH),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{total_duration:.2f}",
            str(out_seg_path)
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{v_filter}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{total_duration:.2f}",
            str(out_seg_path)
        ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)





def main():
    if not SLIDES_DATA_PATH.exists():
        print(f"Error: {SLIDES_DATA_PATH} not found.")
        return

    with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)

    total = len(slides)
    segment_files = []
    print(f"🎥 Rendering Video Segments for {total} slides...")

    for idx, slide in enumerate(slides, start=1):
        idx_num = slide.get("slide_index", idx)
        img_file = find_slide_image(idx_num)
        audio_file = find_audio_file(idx_num)
        seg_file = TEMP_SEGMENTS_DIR / f"seg_{idx_num:03d}.mp4"

        if not img_file or not audio_file:
            print(f"  [!] Skipping slide {idx_num}: Missing image ({img_file}) or audio ({audio_file}).")
            continue

        duration = get_audio_duration(audio_file)
        print(f"  Rendering Segment {idx_num:03d}/{total:03d} (Duration: {duration:.1f}s, Image: {img_file.name}, Motion: {idx_num % 4})...")
        render_segment(img_file, audio_file, seg_file, duration, idx_num)
        segment_files.append(seg_file)


    if not segment_files:
        print("Error: No segments created.")
        return

    print("\n🔗 Merging segments into final MP4...")
    concat_list_path = TEMP_SEGMENTS_DIR / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for seg in segment_files:
            escaped_path = str(seg.resolve()).replace("\\", "/")
            f.write(f"file '{escaped_path}'\n")

    final_video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FINAL_VIDEO_PATH

    merge_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(final_video_path)
    ]

    subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"\n🎉 Final Video Created Successfully!")
    print(f"👉 Path: {final_video_path}")


if __name__ == "__main__":
    main()
