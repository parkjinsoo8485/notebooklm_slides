import json
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
SLIDES_DATA_PATH = OUTPUT_DIR / "slides_data.json"

with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
    slides = json.load(f)

# 캐시 방지 타임스탬프
v_tag = int(time.time())

# 막(Part)별 묶음 처리
parts = {}
for s in slides:
    p_num = s.get("part_number", 1)
    ch_title = s.get("chapter_title", f"제{p_num}막")
    if p_num not in parts:
        parts[p_num] = {"title": ch_title, "slides": []}
    parts[p_num]["slides"].append(s)

total_duration = sum(s.get("audio_duration", 0.0) for s in slides)
total_mins = int(total_duration // 60)
total_secs = int(total_duration % 60)

nav_tabs_html = ""
for p_num, p_data in parts.items():
    nav_tabs_html += f"""
    <button class="tab-btn" onclick="scrollToPart({p_num})">제{p_num}막 ({len(p_data['slides'])}장)</button>
    """

parts_html = ""
for p_num, p_data in parts.items():
    slides_cards = ""
    for s in p_data["slides"]:
        idx = s["slide_index"]
        dur = s.get("audio_duration", 0.0)
        script = s.get("voice_script", "")
        screen_txt = s.get("slide_screen_text", "")
        phonetic = s.get("phonetic_script", "")
        phonetic_box = ""
        if phonetic:
            phonetic_box = f"""
                <div class="script-label" style="margin-top:10px; color:#38bdf8;">🗣️ 표준 연음/발음 적용 낭독문 (TTS 실제 발음)</div>
                <div class="script-content" style="color:#6ee7b7; font-size:13.5px; background:rgba(16,185,129,0.08); padding:8px 12px; border-radius:6px; border-left:3px solid #10b981;">"{phonetic}"</div>
            """
        
        slides_cards += f"""
        <div class="slide-card" id="slide-card-{idx}">
            <div class="card-header">
                <div class="title-row">
                    <span class="badge">슬라이드 {idx:03d}</span>
                    <h4>{screen_txt[:38]}...</h4>
                </div>
                <div class="duration-tag">⏱️ {dur:.1f}s</div>
            </div>
            <div class="script-box">
                <div class="script-label">📜 정서법 원문 대본 (자막용)</div>
                <div class="script-content">"{script}"</div>
                {phonetic_box}
            </div>
            <div class="audio-box">
                <audio id="audio-{idx}" controls preload="none" src="audio/slide_{idx:03d}.mp3?v={v_tag}" onended="onAudioEnded({idx})" onplay="onAudioPlay({idx})"></audio>
            </div>
        </div>
        """

    parts_html += f"""
    <div class="part-section" id="part-{p_num}">
        <div class="part-header">
            <h2>{p_data['title']} <span class="range-text">(슬라이드 {(p_num-1)*20 + 1:03d} ~ {p_num*20:03d})</span></h2>
        </div>
        <div class="grid-container">
            {slides_cards}
        </div>
    </div>
    """

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 전체 120개 슬라이드 한국어 표준 연음 마스터 음성 통합실</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #06080e;
            color: #e2e8f0;
            padding: 30px 20px 80px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1280px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 2.3rem;
            color: #f8fafc;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 1.05rem;
        }}
        .summary-bar {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #10b981;
            border-radius: 14px;
            padding: 20px 30px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-label {{
            font-size: 0.85rem;
            color: #94a3b8;
            margin-bottom: 4px;
        }}
        .stat-value {{
            font-size: 1.45rem;
            font-weight: 700;
            color: #10b981;
        }}
        
        /* 컨트롤 패널 */
        .control-panel {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 16px 24px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            position: sticky;
            top: 15px;
            z-index: 100;
            backdrop-filter: blur(12px);
            background: rgba(15, 23, 42, 0.92);
            box-shadow: 0 10px 25px rgba(0,0,0,0.6);
        }}
        .nav-tabs {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .tab-btn {{
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid #475569;
            padding: 7px 14px;
            border-radius: 6px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .tab-btn:hover {{
            background: #10b981;
            color: #fff;
            border-color: #10b981;
        }}
        .auto-play-box {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.92rem;
            font-weight: 600;
            color: #f1f5f9;
        }}
        .switch {{
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
        }}
        .switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #475569;
            transition: .3s;
            border-radius: 24px;
        }}
        .slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }}
        input:checked + .slider {{
            background-color: #10b981;
        }}
        input:checked + .slider:before {{
            transform: translateX(20px);
        }}

        .part-section {{
            margin-bottom: 50px;
        }}
        .part-header {{
            background: linear-gradient(90deg, #1e293b 0%, rgba(30, 41, 59, 0) 100%);
            border-left: 4px solid #10b981;
            padding: 14px 20px;
            margin-bottom: 22px;
            border-radius: 4px;
        }}
        .part-header h2 {{
            font-size: 1.4rem;
            color: #f1f5f9;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .range-text {{
            font-size: 0.95rem;
            color: #94a3b8;
            font-weight: 400;
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 22px;
        }}
        .slide-card {{
            background: #0d131f;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        .slide-card:hover {{
            transform: translateY(-3px);
            border-color: #10b981;
            box-shadow: 0 12px 28px rgba(0,0,0,0.6);
        }}
        .slide-card.playing {{
            border-color: #38bdf8;
            background: #0c1a2e;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            gap: 10px;
        }}
        .title-row {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .badge {{
            font-size: 0.8rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            background: #10b981;
            color: #fff;
            white-space: nowrap;
        }}
        .card-header h4 {{
            font-size: 0.96rem;
            color: #f1f5f9;
            font-weight: 600;
            line-height: 1.4;
        }}
        .duration-tag {{
            font-size: 0.85rem;
            color: #38bdf8;
            font-weight: 700;
            white-space: nowrap;
        }}
        .script-box {{
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 16px;
            min-height: 90px;
        }}
        .script-label {{
            font-size: 0.75rem;
            color: #10b981;
            margin-bottom: 6px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .script-content {{
            font-size: 0.95rem;
            color: #e2e8f0;
            line-height: 1.6;
        }}
        .audio-box audio {{
            width: 100%;
            height: 42px;
            border-radius: 6px;
            outline: none;
        }}
        .footer {{
            text-align: center;
            margin-top: 60px;
            color: #64748b;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👑 [송림야담] 전체 120개 슬라이드 한국어 표준 연음 마스터 음성 통합실</h1>
            <p>국립국어원 표준 발음법(문밖의 ➔ [문바께], 마님의 ➔ [마니메], 10년 ➔ [심 년]) & [문맥 호흡 텐션] 100% 적용</p>
        </div>

        <div class="summary-bar">
            <div class="stat-item">
                <div class="stat-label">총 슬라이드</div>
                <div class="stat-value">120장</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">총 음성 길이</div>
                <div class="stat-value">{total_mins}분 {total_secs}초</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">발음 규정</div>
                <div class="stat-value">표준 연음 / [에] 발음 100%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">스튜디오 음향</div>
                <div class="stat-value">190Hz 흉성 + 챔버 앰비언스</div>
            </div>
        </div>

        <!-- 컨트롤 패널 -->
        <div class="control-panel">
            <div class="nav-tabs">
                {nav_tabs_html}
            </div>
            <div class="auto-play-box">
                <span>🔄 다음 슬라이드 연속 재생</span>
                <label class="switch">
                    <input type="checkbox" id="autoPlayToggle" checked>
                    <span class="slider"></span>
                </label>
            </div>
        </div>

        {parts_html}

        <div class="footer">
            <p>※ 모든 고음질 음원은 <code>output/audio/</code>에, 완벽 동기화된 SRT 자막은 <code>output/subtitles/</code>에 저장되어 있습니다.</p>
        </div>
    </div>

    <script>
        let currentlyPlayingIdx = null;

        function scrollToPart(partNum) {{
            const el = document.getElementById('part-' + partNum);
            if (el) {{
                const offset = 100;
                const bodyRect = document.body.getBoundingClientRect().top;
                const elementRect = el.getBoundingClientRect().top;
                const elementPosition = elementRect - bodyRect;
                const offsetPosition = elementPosition - offset;
                window.scrollTo({{ top: offsetPosition, behavior: 'smooth' }});
            }}
        }}

        function onAudioPlay(idx) {{
            // 이전 재생 카드 하이라이트 제거
            if (currentlyPlayingIdx !== null && currentlyPlayingIdx !== idx) {{
                const prevCard = document.getElementById('slide-card-' + currentlyPlayingIdx);
                if (prevCard) prevCard.classList.remove('playing');
                const prevAudio = document.getElementById('audio-' + currentlyPlayingIdx);
                if (prevAudio && !prevAudio.paused) prevAudio.pause();
            }}

            currentlyPlayingIdx = idx;
            const currentCard = document.getElementById('slide-card-' + idx);
            if (currentCard) currentCard.classList.add('playing');
        }}

        function onAudioEnded(idx) {{
            const currentCard = document.getElementById('slide-card-' + idx);
            if (currentCard) currentCard.classList.remove('playing');

            const isAuto = document.getElementById('autoPlayToggle').checked;
            if (isAuto && idx < 120) {{
                const nextIdx = idx + 1;
                const nextAudio = document.getElementById('audio-' + nextIdx);
                const nextCard = document.getElementById('slide-card-' + nextIdx);
                if (nextAudio) {{
                    if (nextCard) {{
                        nextCard.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}
                    setTimeout(() => {{
                        nextAudio.play();
                    }}, 400);
                }}
            }}
        }}
    </script>
</body>
</html>
"""

player_path = OUTPUT_DIR / "full_story_player.html"
with open(player_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Enhanced full player created: {player_path}")
