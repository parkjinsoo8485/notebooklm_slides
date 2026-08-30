#!/usr/bin/env python3
"""
CosyVoice2 SRT -> Studio-Grade Storytelling TTS (Real-Time Progress)
"""

import sys, os, io, re, subprocess, time
from pathlib import Path

for attr in ("stdout", "stderr"):
    s = getattr(sys, attr)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, attr, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

import torch
torch_lib = os.path.join(os.path.dirname(torch.__file__), 'lib')
if os.path.exists(torch_lib):
    os.add_dll_directory(torch_lib)
    os.environ['PATH'] = torch_lib + os.pathsep + os.environ.get('PATH', '')

PROJECT_ROOT  = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
try:
    from optimize_performance import optimize_system_and_torch
    optimize_system_and_torch(max_cpu_threads=2, lower_priority=True)
except Exception:
    pass

COSYVOICE_DIR = PROJECT_ROOT / "third_party" / "CosyVoice"
MATCHA_DIR    = COSYVOICE_DIR / "third_party" / "Matcha-TTS"
sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))

import soundfile as sf
MODEL_DIR    = COSYVOICE_DIR / "pretrained_models" / "CosyVoice2-0.5B"
PROMPT_WAV   = PROJECT_ROOT / "output" / "cosyvoice2_pristine_samples" / "sample3_classic_folklore_4.8s.wav"
PROMPT_TEXT  = "옛날 옛적 한양에서 그리 멀지 않은 양주 땅 변두리에 만석이라는 농부가 살았습니다."
SRT_PATH     = PROJECT_ROOT / "output" / "subtitles" / "slide_001.srt"
OUTPUT_DIR   = PROJECT_ROOT / "output" / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_srt_to_sentences(path):
    text = path.read_text(encoding="utf-8-sig")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or re.match(r"^\d+$", line) or "-->" in line:
            continue
        lines.append(line)
    
    full_text = " ".join(lines)
    sentences = [
        "옛날 옛적 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요.",
        "차가운 달빛조차 서럽게 얼어붙던 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
    ]
    return full_text, sentences

def to_mp3(wav, mp3):
    subprocess.run(["ffmpeg", "-y", "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

full_text, sentences = parse_srt_to_sentences(SRT_PATH)
print("=" * 68, flush=True)
print(f" 📜 입력 SRT: {SRT_PATH.name}", flush=True)
print(f" 🎙️ 음성 프롬프트: {PROMPT_WAV.name} (고전 설화 목소리)", flush=True)
print(f" 📝 낭독 문장 수: {len(sentences)}개", flush=True)
for i, s in enumerate(sentences, 1):
    print(f"   [{i}] {s}", flush=True)
print("=" * 68, flush=True)

from cosyvoice.cli.cosyvoice import CosyVoice2
vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0
print(f"\n[1/3] CosyVoice2-0.5B 모델 로딩 중... (GPU: {torch.cuda.get_device_name(0)}, VRAM: {vram_gb:.1f}GB)", flush=True)
model = CosyVoice2(str(MODEL_DIR), load_jit=False, load_trt=False, fp16=(vram_gb >= 3.5))
print("      🚀 CUDA 가속 모델 로딩 완료!", flush=True)

sample_rate = model.sample_rate
audio_chunks = []
silence_0_35s = torch.zeros(1, int(sample_rate * 0.35))

print(f"\n[2/3] 문장별 고속 음성 합성 진행 중...", flush=True)
t0 = time.time()

for idx, sent in enumerate(sentences, 1):
    t_chunk_start = time.time()
    tts_input = f"<|ko|>{sent}"
    print(f"\n   ▶ ({idx}/{len(sentences)}) 합성 시작: \"{sent}\"", flush=True)
    
    chunks = []
    for chunk in model.inference_zero_shot(
        tts_text=tts_input,
        prompt_text=PROMPT_TEXT,
        prompt_wav=str(PROMPT_WAV),
        stream=False
    ):
        chunks.append(chunk["tts_speech"])
    
    if chunks:
        sent_audio = torch.cat(chunks, dim=1)
        audio_chunks.append(sent_audio)
        if idx < len(sentences):
            audio_chunks.append(silence_0_35s)
        dur = sent_audio.shape[1] / sample_rate
        print(f"      ✔ 문장 {idx} 완료 (재생: {dur:.1f}초, 소요: {time.time()-t_chunk_start:.1f}초)", flush=True)

final_audio = torch.cat(audio_chunks, dim=1)
total_dur = final_audio.shape[1] / sample_rate
total_elapsed = time.time() - t0
print(f"\n      ✨ 전체 합성 완료! (총 재생: {total_dur:.1f}초, 전체 소요: {total_elapsed:.1f}초, RTF: {total_elapsed/total_dur:.2f}x)", flush=True)

out_wav = OUTPUT_DIR / "slide_001.wav"
out_mp3 = OUTPUT_DIR / "slide_001.mp3"

print(f"\n[3/3] 오디오 파일 저장 중...", flush=True)
sf.write(str(out_wav), final_audio.cpu().numpy().squeeze(), sample_rate, subtype="PCM_16")
to_mp3(out_wav, out_mp3)
print(f"   [WAV] {out_wav}", flush=True)
print(f"   [MP3] {out_mp3} ({out_mp3.stat().st_size / 1024:.1f} KB)", flush=True)

# 웹 플레이어 생성
player_html = PROJECT_ROOT / "output" / "slide_001_player.html"
html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>슬라이드 1번 고전 설화 낭독 음성 (CosyVoice2)</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: "Pretendard", -apple-system, sans-serif; }}
        body {{
            background: #090d16;
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .player-card {{
            background: linear-gradient(145deg, #131b2e, #0f172a);
            border: 1px solid #1f2d4a;
            border-radius: 20px;
            padding: 36px;
            max-width: 680px;
            width: 100%;
            box-shadow: 0 20px 40px -10px rgba(0,0,0,0.7);
        }}
        .badge {{
            display: inline-block;
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 12px;
        }}
        .meta {{
            font-size: 14px;
            color: #94a3b8;
            margin-bottom: 24px;
            line-height: 1.6;
        }}
        .script-box {{
            background: #060911;
            border-left: 4px solid #f59e0b;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 24px;
            font-size: 15px;
            line-height: 1.8;
            color: #e2e8f0;
        }}
        audio {{
            width: 100%;
            height: 48px;
            border-radius: 10px;
            outline: none;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid #1e293b;
            font-size: 13px;
            color: #38bdf8;
        }}
    </style>
</head>
<body>
    <div class="player-card">
        <div class="badge">🎙️ CosyVoice2-0.5B CUDA Accelerated</div>
        <h1>슬라이드 1번 고전 설화 낭독 음성</h1>
        <div class="meta">
            <strong>프롬프트 음성:</strong> sample3_classic_folklore_4.8s (양주 땅 농부 고전 구연톤)<br>
            <strong>입력 자막:</strong> slide_001.srt
        </div>
        <div class="script-box">
            {full_text}
        </div>
        <audio controls autoplay src="audio/slide_001.mp3"></audio>
        <div class="stats">
            <div>⏱ 재생 시간: {total_dur:.1f}초</div>
            <div>⚡ 처리 속도: {total_elapsed:.1f}초 ({total_elapsed/total_dur:.2f}x RTF)</div>
            <div>🎧 24kHz / 192kbps MP3</div>
        </div>
    </div>
</body>
</html>
"""
player_html.write_text(html_content, encoding="utf-8")
print(f"\n🌐 청음 플레이어 생성 완료: {player_html}", flush=True)
print("\n" + "=" * 68, flush=True)
print(" 🎉 슬라이드 1번 음성 변환 완료!", flush=True)
print("=" * 68, flush=True)
