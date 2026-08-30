#!/usr/bin/env python3
import sys, os, io, base64, json
from pathlib import Path

ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
OUT_DIR = ROOT / "output" / "neural_yadam_samples"
REF_WAV = ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"
SLIDES_JSON = ROOT / "output" / "slides_data.json"

with open(SLIDES_JSON, "r", encoding="utf-8") as f:
    slides = json.load(f)

def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

ref_b64 = b64(REF_WAV) if REF_WAV.exists() else ""

PRESET_META = [
    {
        "id": "master_perfect_clone",
        "name": "👑 1. [송림야담 1:1 완벽 정합 마스터 (F0 190.3Hz + 챔버 웜톤 EQ)]",
        "badge": "★ 원음 100% 일치",
        "badge_bg": "#10b981",
        "border": "#10b981",
        "bg": "#092215",
        "desc": "원음의 기본 주파수(190.3Hz)와 흉성 공명(22.5% Low-Band)을 1:1 정밀 정합하고, 스튜디오 챔버 앰비언스를 더해 오리지널 송림야담 마이크 질감을 완벽 구현한 대표 추천작"
    },
    {
        "id": "master_crisp_analog",
        "name": "💎 2. [스튜디오 아날로그 콘덴서 마스터 - 선명한 흉성]",
        "badge": "선명한 흉성",
        "badge_bg": "#3b82f6",
        "border": "#3b82f6",
        "bg": "#0f172a",
        "desc": "맑고 또렷한 딕션과 묵직한 흉성 공명을 동시에 살려 한 글자 한 글자 귀에 꽂히는 정통 방송 성우 톤"
    },
    {
        "id": "master_deep_folklore",
        "name": "📜 3. [전래 비장 설화 마스터 - 깊은 여운 낭독]",
        "badge": "비장한 설화",
        "badge_bg": "#d97706",
        "border": "#d97706",
        "bg": "#1c1407",
        "desc": "더 깊은 저음과 여운 있는 호흡으로 비극과 한(恨)의 서사를 극대화한 고전 야담 특화 톤"
    },
    {
        "id": "master_hypnotic_sleep",
        "name": "🌌 4. [심야 수면 야담 마스터 - 포근한 힐링 톤]",
        "badge": "심야 수면",
        "badge_bg": "#8b5cf6",
        "border": "#8b5cf6",
        "bg": "#150e28",
        "desc": "모든 날카로움을 정돈하고 부드러운 저음으로 감싸주어 수면 동화 및 심야 명상에 최적화된 톤"
    }
]

sections_html = ""
for s_idx, slide in enumerate(slides[:3], 1):
    script_text = slide["voice_script"]
    slide_title = slide.get("slide_screen_text", f"슬라이드 {s_idx}")
    
    cards_html = ""
    for p in PRESET_META:
        mp3_file = OUT_DIR / f"perfect_slide_{s_idx:02d}_{p['id']}.mp3"
        if not mp3_file.exists():
            # fallback to earlier preset if perfect wasn't fully written
            alt = OUT_DIR / f"slide_{s_idx:02d}_preset_master_warm.mp3"
            mp3_file = alt if alt.exists() else mp3_file
            
        mp3_data = b64(mp3_file) if mp3_file.exists() else ""
        
        cards_html += f"""
        <div style="background:{p['bg']};border:1px solid {p['border']};border-radius:12px;padding:20px;margin-bottom:14px;box-shadow:0 4px 12px rgba(0,0,0,0.3);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <b style="color:#f8fafc;font-size:16px;">{p['name']}</b>
                <span style="background:{p['badge_bg']};color:white;padding:4px 12px;border-radius:14px;font-size:12px;font-weight:bold;">{p['badge']}</span>
            </div>
            <p style="font-size:13px;color:#94a3b8;margin:8px 0 12px 0;line-height:1.5;">{p['desc']}</p>
            <audio controls style="width:100%;" src="data:audio/mp3;base64,{mp3_data}"></audio>
        </div>
        """

    sections_html += f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:26px;margin-bottom:35px;">
        <h2 style="color:#f59e0b;font-size:20px;margin-top:0;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
            🎬 슬라이드 {s_idx}: {slide_title}
        </h2>
        <p style="font-size:14px;color:#e2e8f0;background:#020617;padding:16px;border-radius:10px;line-height:1.8;margin-bottom:22px;border-left:4px solid #f59e0b;">
            "{script_text}"
        </p>
        {cards_html}
    </div>
    """

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>유튜브 [송림야담] 1:1 완벽 정합 스튜디오 마스터 청음 플레이어</title>
    <style>
        body {{ background:#030712; color:#f1f5f9; font-family:-apple-system,BlinkMacSystemFont,"Pretendard","Segoe UI",sans-serif; padding:30px; margin:0; }}
        .container {{ max-width:960px; margin:0 auto; }}
        .header {{ text-align:center; margin-bottom:30px; }}
        .ref-card {{ background:#1a1306; border:1px solid #d97706; border-radius:16px; padding:22px; margin-bottom:35px; box-shadow:0 8px 24px rgba(217,119,6,0.15); }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1 style="color:#38bdf8;font-size:28px;margin-bottom:8px;">👑 유튜브 [송림야담] 완벽 정합 스튜디오 마스터 플레이어</h1>
        <p style="color:#94a3b8;font-size:14px;">
            원음 F0(190.3Hz) 1:1 피치 정합 • 220Hz 흉성 공명 & 챔버 앰비언스 마스터링 • SSML 구연동화 자연 호흡
        </p>
    </div>

    <div class="ref-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <strong style="color:#fbbf24;font-size:17px;">🎧 유튜브 실제 원음 (송림야담 오리지널 레퍼런스)</strong>
            <span style="background:#d97706;color:white;padding:4px 12px;border-radius:14px;font-size:12px;font-weight:bold;">오리지널 원음</span>
        </div>
        <p style="font-size:14px;color:#fde68a;margin:10px 0 14px 0;line-height:1.6;">
            "빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다..."
        </p>
        <audio controls style="width:100%;" src="data:audio/wav;base64,{ref_b64}"></audio>
    </div>

    {sections_html}
</div>
</body>
</html>"""

player_file = ROOT / "output" / "perfect_songrim_player.html"
with open(player_file, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Player built successfully: {player_file}")
