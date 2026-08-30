#!/usr/bin/env python3
"""
Autonomous Korean TTS Solver — Self-Improving & Self-Verifying Loop
───────────────────────────────────────────────────────────────────
1. 모든 CosyVoice 3.0 포맷에 필수인 `<|endofprompt|>`를 엄격히 준수
2. Whisper STT로 발음 정확도(키워드 일치율) 자동 측정
3. 최고 일치율 전략을 자동 탐색하고 플레이어에 최종 등록
"""
import sys, os, time, io, base64, subprocess
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path
import soundfile as sf
import torch
import whisper
import warnings
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
COSYVOICE_DIR = PROJECT_ROOT / "third_party" / "CosyVoice"
MATCHA_DIR = COSYVOICE_DIR / "third_party" / "Matcha-TTS"
MODEL_DIR = COSYVOICE_DIR / "pretrained_models" / "Fun-CosyVoice3-0.5B"
OUT_DIR = PROJECT_ROOT / "output" / "autonomous_tts_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))

REF_WAV_10S = PROJECT_ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"
PROMPT_TEXT_10S = "빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."

GROUND_TRUTH = "안녕하세요, 테스트 음성입니다."
TARGET_KEYWORDS = ["안녕하세요", "테스트", "음성"]

print("=" * 70)
print(" 🤖 Autonomous Korean TTS Solver 가동")
print(f" 🎯 목표 문장: '{GROUND_TRUTH}'")
print(f" 🎯 필수 키워드: {TARGET_KEYWORDS}")
print("=" * 70)

# 1. Whisper 모델 로드
print("\n[1/3] Whisper STT 모델 로드 중 (base)...")
stt_model = whisper.load_model("base")
print("✔ Whisper STT 준비 완료")

# 2. CosyVoice 3.0 모델 로드
print("\n[2/3] Fun-CosyVoice 3.0 모델 로드 중 (FP16 + Euler-4 가속)...")
from cosyvoice.cli.cosyvoice import AutoModel
cosyvoice = AutoModel(model_dir=str(MODEL_DIR), fp16=True)
cosyvoice.model.flow.n_timesteps = 4
print("✔ CosyVoice 3.0 준비 완료")

# 3. 탐색할 엄격 규격 전략 목록
strategies = [
    # ── 1. cross_lingual 기본 ──
    {
        "id": "CL_01_Official_Prompt",
        "method": "cross_lingual",
        "text": "You are a helpful assistant.<|endofprompt|>안녕하세요, 테스트 음성입니다.",
        "wav": str(REF_WAV_10S),
    },
    # ── 2. cross_lingual 한국어 힌트 ──
    {
        "id": "CL_02_Korean_Hint",
        "method": "cross_lingual",
        "text": "You are a helpful assistant. 한국어 음성입니다.<|endofprompt|>안녕하세요, 테스트 음성입니다.",
        "wav": str(REF_WAV_10S),
    },
    # ── 3. zero_shot 공식 포맷 ──
    {
        "id": "ZS_01_Official_ZeroShot",
        "method": "zero_shot",
        "text": "You are a helpful assistant.<|endofprompt|>안녕하세요, 테스트 음성입니다.",
        "prompt_text": f"You are a helpful assistant.<|endofprompt|>{PROMPT_TEXT_10S}",
        "wav": str(REF_WAV_10S),
    },
    # ── 4. zero_shot 순수 텍스트 ──
    {
        "id": "ZS_02_EndPrompt_Only",
        "method": "zero_shot",
        "text": "<|endofprompt|>안녕하세요, 테스트 음성입니다.",
        "prompt_text": f"<|endofprompt|>{PROMPT_TEXT_10S}",
        "wav": str(REF_WAV_10S),
    },
    # ── 5. instruct2 공식 중국어 지시문 ──
    {
        "id": "INS_01_Official_Instruct",
        "method": "instruct2",
        "text": "안녕하세요, 테스트 음성입니다.",
        "instruct": "You are a helpful assistant. 请用韩语表达。<|endofprompt|>",
        "wav": str(REF_WAV_10S),
    },
    # ── 6. instruct2 한국어 지시문 ──
    {
        "id": "INS_02_Korean_Instruct",
        "method": "instruct2",
        "text": "안녕하세요, 테스트 음성입니다.",
        "instruct": "You are a helpful assistant. 한국어로 또렷하게 발음해주세요.<|endofprompt|>",
        "wav": str(REF_WAV_10S),
    },
    # ── 7. instruct2 영어 지시문 ──
    {
        "id": "INS_03_English_Instruct",
        "method": "instruct2",
        "text": "안녕하세요, 테스트 음성입니다.",
        "instruct": "You are a helpful assistant. Please speak in Korean clearly.<|endofprompt|>",
        "wav": str(REF_WAV_10S),
    },
    # ── 8. zero_shot 슬라이드 1 실전 대본 ──
    {
        "id": "ZS_03_Slide1_Full",
        "method": "zero_shot",
        "text": "You are a helpful assistant.<|endofprompt|>옛날 옛적 한양 북촌 명문가의 어질고 고왔던 윤 씨 마님이, 하루아침에 억울한 누명을 쓰고 깊은 산골로 내쫓기고 말았더랬지요.",
        "prompt_text": f"You are a helpful assistant.<|endofprompt|>{PROMPT_TEXT_10S}",
        "wav": str(REF_WAV_10S),
    }
]

print(f"\n[3/3] 총 {len(strategies)}개 엄격 규격 전략 순회 탐색 시작...")

results_log = []
winner = None

def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

def evaluate_stt(recognized, ground_truth, keywords):
    rec_clean = recognized.strip()
    kw_hits = sum(1 for kw in keywords if kw in rec_clean)
    kw_score = kw_hits / len(keywords)
    return kw_score, kw_hits

for idx, strat in enumerate(strategies, 1):
    sid = strat["id"]
    method = strat["method"]
    print(f"\n───────────────────────────────────────────────────────")
    print(f" ▶ [{idx}/{len(strategies)}] 시도: {sid} (방법: {method})")
    print(f"   텍스트: {strat['text'][:50]}...")
    
    t0 = time.time()
    chunks = []
    
    try:
        if method == "cross_lingual":
            for out in cosyvoice.inference_cross_lingual(strat["text"], strat["wav"], stream=False, text_frontend=False):
                chunks.append(out["tts_speech"])
        elif method == "zero_shot":
            for out in cosyvoice.inference_zero_shot(strat["text"], strat["prompt_text"], strat["wav"], stream=False, text_frontend=False):
                chunks.append(out["tts_speech"])
        elif method == "instruct2":
            for out in cosyvoice.inference_instruct2(strat["text"], strat["instruct"], strat["wav"], stream=False, text_frontend=False):
                chunks.append(out["tts_speech"])
                
        if not chunks:
            print(f"  ❌ 합성 실패: 0개 청크 출력")
            continue
            
        audio = torch.cat(chunks, dim=1)
        dur = audio.shape[-1] / cosyvoice.sample_rate
        elapsed = time.time() - t0
        
        if dur < 0.5:
            print(f"  ❌ 오디오 길이 너무 짧음 ({dur:.2f}초)")
            continue
            
        wav_path = OUT_DIR / f"{sid}.wav"
        mp3_path = OUT_DIR / f"{sid}.mp3"
        sf.write(str(wav_path), audio.cpu().numpy().squeeze(), cosyvoice.sample_rate, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_path)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                       
        # Whisper STT 검증
        stt_res = stt_model.transcribe(str(wav_path), language="ko")
        rec_text = stt_res["text"].strip()
        score, hits = evaluate_stt(rec_text, GROUND_TRUTH, TARGET_KEYWORDS)
        
        print(f"  ⏱️ 길이: {dur:.1f}초 (소요: {elapsed:.1f}초, RTF: {elapsed/dur:.2f}x)")
        print(f"  🎙️ Whisper STT 인식: '{rec_text}'")
        print(f"  📊 키워드 일치도: {hits}/{len(TARGET_KEYWORDS)} ({score*100:.1f}%)")
        
        entry = {
            "id": sid, "method": method, "dur": dur, "elapsed": elapsed,
            "stt": rec_text, "score": score, "hits": hits, "wav": str(wav_path), "mp3": str(mp3_path)
        }
        results_log.append(entry)
        
        if score >= 0.66:
            print(f"\n🎉 [우수 한국어 후보 발견!] {sid} (일치율: {score*100:.1f}%)")
            if winner is None or score > winner["score"]:
                winner = entry
                
        if score == 1.0:
            print(f"\n🏆 [100% 완벽 일치 달성!] {sid}")
            winner = entry
            
    except Exception as e:
        print(f"  ❌ 예외 발생: {e}")

# 결과 요약 및 플레이어 업데이트
print("\n" + "=" * 70)
print(" 📊 Autonomous TTS Solver 탐색 결과 요약")
print("=" * 70)

for r in results_log:
    print(f" - [{r['id']}] 일치율: {r['score']*100:.1f}% | STT: '{r['stt']}' | RTF: {r['elapsed']/r['dur']:.2f}x")

# HTML 플레이어 작성
ref_b64 = b64(REF_WAV_10S)
cards = ""

sorted_results = sorted(results_log, key=lambda x: x["score"], reverse=True)

for r in sorted_results:
    is_win = (winner is not None and r["id"] == winner["id"])
    border = "#238636" if is_win else ("#38bdf8" if r["score"] > 0.5 else "#30363d")
    bg = "#0d2818" if is_win else "#161b22"
    badge_text = "🏆 최우수 한국어" if is_win else f"일치율 {r['score']*100:.0f}%"
    badge_bg = "#238636" if r["score"] >= 0.66 else "#8b949e"
    mp3_data = b64(Path(r["mp3"]))
    
    cards += f"""
    <div style="background:{bg};border:1px solid {border};border-radius:12px;padding:20px;margin-bottom:15px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <b style="color:#58a6ff;font-size:16px;">{r['id']} ({r['method']})</b>
            <span style="background:{badge_bg};color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:bold;">{badge_text}</span>
        </div>
        <p style="font-size:12px;color:#8b949e;margin:6px 0;">⏱️ {r['dur']:.1f}초 | ⚡ 소요: {r['elapsed']:.1f}초 (RTF: {r['elapsed']/r['dur']:.2f}x)</p>
        <p style="font-size:14px;color:#c9d1d9;background:#09101d;padding:10px;border-radius:8px;margin:8px 0;">
            <b>🎙️ STT 인식:</b> <span style="color:#7ee787;">"{r['stt']}"</span>
        </p>
        <audio controls style="width:100%;margin-top:8px;" src="data:audio/mp3;base64,{mp3_data}"></audio>
    </div>"""

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Autonomous Korean TTS Solver 결과 리포트</title>
    <style>
        body {{ background:#0b0f19; color:#e6edf3; font-family:-apple-system,sans-serif; padding:30px; }}
        .container {{ max-width:860px; margin:0 auto; }}
        .card {{ background:#161b22; border:1px solid #30363d; border-radius:12px; padding:20px; margin-bottom:15px; }}
        .ref {{ border-color:#d29922; margin-bottom:20px; }}
    </style>
</head>
<body>
<div class="container">
    <h1 style="color:#58a6ff;font-size:24px;margin-bottom:6px;">🤖 Autonomous Korean TTS Solver 리포트</h1>
    <p style="color:#8b949e;font-size:14px;margin-bottom:20px;">
        Whisper STT 기반 자동 발음 검증 및 최고 일치율 전략 자동 선정
    </p>

    <div class="card ref">
        <strong style="color:#d29922;">🎧 레퍼런스 원음 (ref_songrim_clean_10s.wav)</strong>
        <p style="font-size:13px;color:#94a3b8;margin:6px 0;">"{PROMPT_TEXT_10S}"</p>
        <audio controls style="width:100%;margin-top:8px;" src="data:audio/wav;base64,{ref_b64}"></audio>
    </div>

    {cards}
</div>
</body>
</html>"""

player_file = PROJECT_ROOT / "output" / "cosyvoice3_player.html"
with open(player_file, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n🌐 플레이어 최종 업데이트 완료: {player_file}")
