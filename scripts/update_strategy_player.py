#!/usr/bin/env python3
import base64
from pathlib import Path
import soundfile as sf

ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
OUT  = ROOT / "output" / "cosyvoice2_strategy_test"
player_html = ROOT / "output" / "cosyvoice2_strategy_player.html"

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def dur(wav):
    d, sr = sf.read(str(wav))
    return len(d) / sr

ref_clean = ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"

samples = [
    {
        "label": "✨ 04. Korean 경로 수정 후 재생성 (핵심 버그 패치)",
        "meta_extra": "contains_chinese() 우회 + &lt;|ko|&gt; 태그 순서 수정",
        "color": "#f778ba",
        "mp3": OUT / "04_Korean_Fix_테스트.mp3",
        "wav": OUT / "04_Korean_Fix_테스트.wav",
        "text": "안녕하세요, 테스트 음성입니다.",
        "mode": "4-Bit NF4 | Temp=0.3",
        "badge": "버그 수정"
    },
    {
        "label": "03. 보정된 여성 원음(Clean 10.15s) — 버그 수정 전",
        "meta_extra": "한글 영어 경로 처리 (외계음 발생)",
        "color": "#8b949e",
        "mp3": OUT / "03_여성원음_Clean10s_테스트.mp3",
        "wav": OUT / "03_여성원음_Clean10s_테스트.wav",
        "text": "안녕하세요, 테스트 음성입니다.",
        "mode": "4-Bit NF4 | Temp=0.3",
        "badge": None
    },
    {
        "label": "02. 남성 고전설화(sample3) — 버그 수정 전",
        "meta_extra": "한글 영어 경로 처리 (외계음 발생)",
        "color": "#8b949e",
        "mp3": OUT / "02_초단문_4Bit_저온도(0.3).mp3",
        "wav": None,
        "text": "안녕하세요, 테스트 음성입니다.",
        "mode": "4-Bit NF4 | Temp=0.3",
        "badge": None
    },
    {
        "label": "01. 남성 고전설화(sample3) — 버그 수정 전",
        "meta_extra": "한글 영어 경로 처리 (외계음 발생)",
        "color": "#8b949e",
        "mp3": OUT / "01_초단문_FP16_저온도(0.3).mp3",
        "wav": None,
        "text": "안녕하세요, 테스트 음성입니다.",
        "mode": "FP16 | Temp=0.3",
        "badge": None
    },
]

cards = ""
for s in samples:
    if not s["mp3"].exists():
        continue
    d = dur(s["wav"]) if s["wav"] and s["wav"].exists() else 0
    badge_html = f'<span style="background:#238636;color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;margin-left:6px;">{s["badge"]}</span>' if s["badge"] else ""
    cards += f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:15px;">
            <h3 style="margin-top:0;color:{s['color']};font-size:16px;">{s['label']}{badge_html}</h3>
            <p style="font-size:12px;color:#8b949e;margin-bottom:8px;">⚙️ {s['mode']} | {s['meta_extra']}{f' | ⏱️ {d:.1f}초' if d else ''}</p>
            <p style="font-size:14px;color:#c9d1d9;background:#0d1117;padding:10px 14px;border-radius:8px;">"{s['text']}"</p>
            <audio controls style="width:100%;margin-top:10px;" src="data:audio/mp3;base64,{b64(s['mp3'])}"></audio>
        </div>
"""

ref_b64 = b64(ref_clean) if ref_clean.exists() else ""
ref_dur  = dur(ref_clean) if ref_clean.exists() else 0

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>CosyVoice2 한국어 버그 수정 비교 플레이어</title>
    <style>
        body {{ background:#0b0f19; color:#e6edf3; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; padding:30px; }}
        .container {{ max-width:860px; margin:0 auto; }}
    </style>
</head>
<body>
<div class="container">
    <h1 style="color:#58a6ff;font-size:22px;margin-bottom:6px;">🔬 CosyVoice2 외계음 버그 수정 비교 플레이어</h1>
    <p style="color:#8b949e;font-size:13px;margin-bottom:24px;">
        근본 원인: <code>contains_chinese()</code>가 한글을 인식 못해 영어 경로 처리 → <code>&lt;|ko|&gt;</code> 태그가 text_normalize 앞에 붙어 프론트엔드 무력화
    </p>

    <div style="background:#161b22;border:1px solid #d29922;border-radius:12px;padding:18px;margin-bottom:24px;">
        <strong style="color:#d29922;">🎧 레퍼런스 원음 (ref_songrim_clean_10s.wav — BGM 제거 + 완전문장 10.15초)</strong>
        <p style="font-size:13px;color:#94a3b8;margin:8px 0;">재생 시간: {ref_dur:.1f}초</p>
        <p style="font-size:14px;color:#c9d1d9;background:#0d1117;padding:10px 14px;border-radius:8px;">
            "빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."
        </p>
        <audio controls style="width:100%;margin-top:10px;" src="data:audio/wav;base64,{ref_b64}"></audio>
    </div>

    {cards}
</div>
</body>
</html>"""

with open(player_html, "w", encoding="utf-8") as f:
    f.write(html)
print("Player updated!")
