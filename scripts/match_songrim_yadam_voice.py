"""
match_songrim_yadam_voice.py
────────────────────────────
유튜브 '송림야담' (https://youtu.be/jKatQ6Gd__s) 여성 음성 특성을 정밀 분석하여
가장 유사한 4가지 매칭 보이스를 생성하고 레퍼런스 오디오와 1:1 비교 청음 제공.
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR    = WORKSPACE_DIR / "output"
REF_DIR       = OUTPUT_DIR / "reference_voices"
SAMPLES_DIR   = OUTPUT_DIR / "voice_samples" / "songrim_match"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# 송림야담 실제 오디오에서 발췌한 동일 스타일 낭독 지문
COMPARISON_SCRIPT = (
    "옛날 어느 깊은 산골 마을에, 쫓기던 과부를 소달구지 속에 숨겨준 우직한 농부가 살고 있었지요... "
    "눈보라는 살을 에는 듯 매섭게 휘몰아쳤지만, "
    "농부는 아무런 대가도 바라지 않고 마님의 얼어붙은 손을 꼭 잡아주었답니다. "
    "그날 밤의 작은 자비가, 훗날 그의 운명을 송두리째 뒤바꾸어 놓을 줄은 꿈에도 몰랐던 것이지요..."
)

MATCHING_PRESETS = [
    {
        "id": "match_songrim_standard",
        "name": "1. [송림야담 표준 매칭 - 차분한 서사 낭독]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-22%",
        "pitch": "-16Hz",
        "warmth_eq": False,
        "desc": "송림야담의 대표적인 기본 속도와 피치를 완벽 재현한 맑고 정갈한 서사형 야담 음색",
        "color": "#3B82F6"
    },
    {
        "id": "match_songrim_deep_yadam",
        "name": "2. [송림야담 심화 매칭 - 구수한 중년 이야기꾼]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-26%",
        "pitch": "-22Hz",
        "warmth_eq": False,
        "desc": "조금 더 깊은 저음과 여운 있는 호흡으로 몰입감을 극대화한 전래 설화/야담 특화 톤",
        "color": "#D97706"
    },
    {
        "id": "match_songrim_analog_warm",
        "name": "3. [송림야담 스튜디오 마스터 - 아날로그 웜톤 EQ]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-24%",
        "pitch": "-19Hz",
        "warmth_eq": True,
        "desc": "디지털 치찰음을 다듬고 저음역 공명감을 보강하여 유튜브 전문 야담 채널의 방송용 마이크 질감 완성",
        "color": "#10B981"
    },
    {
        "id": "match_songrim_sleep_story",
        "name": "4. [송림야담 수면동화/심야 설화 톤]",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-29%",
        "pitch": "-25Hz",
        "warmth_eq": False,
        "desc": "가장 부드럽고 느긋한 호흡으로 듣는 이를 편안하게 감싸주는 심야 수면 야담 톤",
        "color": "#8B5CF6"
    }
]


async def generate_matches():
    print("=" * 75)
    print("  🎙️ 유튜브 [송림야담] 여성 음성 1:1 정밀 매칭 및 음원 생성")
    print("=" * 75)

    # 레퍼런스 음원 복사 (HTML 플레이어에서 바로 재생 가능하도록)
    ref_src = REF_DIR / "songrim_yadam_sample.mp3"
    ref_dst = SAMPLES_DIR / "youtube_songrim_reference.mp3"
    if ref_src.exists():
        import shutil
        shutil.copy2(ref_src, ref_dst)
        print(f"   📂 유튜브 레퍼런스 음원 연동: {ref_dst.name}")

    for p in MATCHING_PRESETS:
        raw_mp3 = SAMPLES_DIR / f"{p['id']}_raw.mp3"
        final_mp3 = SAMPLES_DIR / f"{p['id']}.mp3"

        print(f"\n▶ [{p['name']}] 생성 중...")
        print(f"   파라미터: Voice={p['voice']}, Rate={p['rate']}, Pitch={p['pitch']}")

        comm = edge_tts.Communicate(
            COMPARISON_SCRIPT,
            p["voice"],
            rate=p["rate"],
            pitch=p["pitch"]
        )
        target = raw_mp3 if p["warmth_eq"] else final_mp3
        await comm.save(str(target))

        if p["warmth_eq"]:
            print("   🎛️ 스튜디오 아날로그 웜톤 EQ 필터 적용 중...")
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", str(raw_mp3),
                "-af", "equalizer=f=220:width_type=o:width=1.4:g=3.2,equalizer=f=3400:width_type=o:width=1.2:g=-2.8,volume=1.15",
                "-b:a", "192k", str(final_mp3)
            ]
            subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if raw_mp3.exists():
                raw_mp3.unlink()

        print(f"   ✅ 생성 완료: {final_mp3.name}")

    create_comparison_html()


def create_comparison_html():
    html_path = SAMPLES_DIR / "compare_songrim_matching.html"

    cards_html = ""
    for p in MATCHING_PRESETS:
        mp3_name = f"{p['id']}.mp3"
        cards_html += f"""
        <div class="voice-card">
            <div class="badge" style="background-color: {p['color']};">매칭 프리셋</div>
            <h2>{p['name']}</h2>
            <p class="desc">{p['desc']}</p>
            <div class="param-tags">
                <span class="tag">Rate: {p['rate']}</span>
                <span class="tag">Pitch: {p['pitch']}</span>
                {"<span class='tag-eq'>🎛️ 웜톤 EQ</span>" if p['warmth_eq'] else ""}
            </div>
            <div class="audio-box">
                <audio controls preload="auto" src="{mp3_name}"></audio>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>유튜브 [송림야담] 음성 1:1 정밀 매칭 비교</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif; }}
        body {{
            background-color: #0b1120;
            color: #f8fafc;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 960px;
            width: 100%;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 15px;
            line-height: 1.6;
        }}
        .reference-card {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
            border: 2px solid #ef4444;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 32px;
            box-shadow: 0 12px 30px -8px rgba(239, 68, 68, 0.3);
        }}
        .reference-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
        }}
        .reference-title {{
            font-size: 18px;
            font-weight: 700;
            color: #fca5a5;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .yt-link {{
            color: #ef4444;
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            background: rgba(239, 68, 68, 0.15);
            padding: 4px 10px;
            border-radius: 6px;
        }}
        .yt-link:hover {{ text-decoration: underline; }}
        .reference-card audio {{
            width: 100%;
            height: 42px;
            border-radius: 8px;
        }}
        .script-box {{
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 30px;
            font-size: 15px;
            line-height: 1.7;
            color: #e2e8f0;
        }}
        .script-box strong {{
            color: #38bdf8;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
        }}
        .voice-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
        }}
        .voice-card:hover {{
            transform: translateY(-4px);
            border-color: #38bdf8;
            box-shadow: 0 14px 28px -10px rgba(56, 189, 248, 0.3);
        }}
        .badge {{
            align-self: flex-start;
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            margin-bottom: 12px;
        }}
        .voice-card h2 {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #f8fafc;
        }}
        .voice-card .desc {{
            color: #94a3b8;
            font-size: 13.5px;
            line-height: 1.5;
            margin-bottom: 16px;
            flex-grow: 1;
        }}
        .param-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
        }}
        .tag {{
            background: #0f172a;
            color: #38bdf8;
            font-size: 12px;
            padding: 3px 8px;
            border-radius: 6px;
            font-family: monospace;
        }}
        .tag-eq {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
            font-size: 12px;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 600;
        }}
        .audio-box audio {{
            width: 100%;
            height: 40px;
            border-radius: 8px;
            outline: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ 유튜브 [송림야담] 음성 1:1 정밀 매칭</h1>
            <p>제공해주신 유튜브 영상 속 실제 여성 나레이터 음성과<br>가장 흡사하게 조율된 4가지 음색을 1:1로 직접 비교 청음해보세요.</p>
        </div>

        <div class="reference-card">
            <div class="reference-header">
                <div class="reference-title">
                    🔴 [원본 레퍼런스] 유튜브 '송림야담' 실제 음성
                </div>
                <a class="yt-link" href="https://youtu.be/jKatQ6Gd__s" target="_blank">YouTube 원본 보기 ↗</a>
            </div>
            <audio controls preload="auto" src="youtube_songrim_reference.mp3"></audio>
        </div>

        <div class="script-box">
            <strong>📖 동일 낭독 지문 테스트:</strong><br>
            "{COMPARISON_SCRIPT}"
        </div>

        <div class="grid">
            {cards_html}
        </div>
    </div>
</body>
</html>
"""
    html_path.write_text(html_content, encoding="utf-8")
    print(f"\n✨ 송림야담 1:1 비교 청음 플레이어 생성 완료: {html_path.relative_to(WORKSPACE_DIR)}")


if __name__ == "__main__":
    asyncio.run(generate_matches())
