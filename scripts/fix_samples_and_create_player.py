import sys
import io
import os
from pathlib import Path
import soundfile as sf
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FOLDER = Path("c:/My_Project/src/notebooklm_slides/output/korean_storyteller_3to5s_samples")

for wav_file in FOLDER.glob("*.wav"):
    data, sr = sf.read(str(wav_file))
    # Normalize and write as standard 16-bit PCM WAV
    sf.write(str(wav_file), data, sr, subtype='PCM_16')
    print(f"[OK] Converted {wav_file.name} to Standard 16-bit PCM WAV")

# HTML Player 생성
samples = [
    {
        "file": "sample1_storyteller_intro_4.4s.wav",
        "title": "01. 이야기 오프닝 (4.4s)",
        "tone": "따뜻하고 차분한 이야기 시작 톤",
        "text": "자 그럼 오늘도 감동적인 옛날 이야기, 지금 바로 시작합니다."
    },
    {
        "file": "sample2_yadam_drama_4.2s.wav",
        "title": "02. 야담/사극 연기 (4.2s)",
        "tone": "몰입감·긴장감 있는 사극/야담 연기 톤",
        "text": "그 여인을 내놓아라. 그럼 네 빚 문서를 이 자리에서 찢어주마."
    },
    {
        "file": "sample3_classic_folklore_4.8s.wav",
        "title": "03. 고전 설화 낭독 (4.8s)",
        "tone": "깊은 울림의 전통 전래동화/야담 낭독",
        "text": "옛날 옛적 한양에서 그리 멀지 않은 양주 땅 변두리에 만석이라는 농부가 살았습니다."
    },
    {
        "file": "sample4_scholar_journey_3.9s.wav",
        "title": "04. 단아한 나레이션 (3.9s)",
        "tone": "맑고 단아한 성우형 나레이션 톤",
        "text": "한양 땅에서 과거를 보러 가던 이 선비는"
    }
]

html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CosyVoice2 중년 여성 스토리텔러 음성 샘플 4종</title>
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --accent: #58a6ff;
            --accent-green: #2ea043;
            --text-main: #f0f6fc;
            --text-sub: #8b949e;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            max-width: 760px;
            width: 100%;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 8px;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .subtitle {
            color: var(--text-sub);
            font-size: 14px;
            margin-bottom: 28px;
            line-height: 1.6;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 18px;
            transition: transform 0.2s, border-color 0.2s;
        }
        .card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 10px;
        }
        .card-title {
            font-size: 17px;
            font-weight: 600;
            color: var(--accent);
        }
        .card-tag {
            font-size: 12px;
            background: #21262d;
            border: 1px solid var(--border);
            color: #7ee787;
            padding: 3px 8px;
            border-radius: 6px;
        }
        .quote-box {
            background: #0d1117;
            border-left: 3px solid var(--accent);
            padding: 10px 14px;
            border-radius: 4px;
            font-size: 14px;
            color: #c9d1d9;
            margin-bottom: 14px;
            line-height: 1.5;
        }
        audio {
            width: 100%;
            height: 40px;
            border-radius: 8px;
            outline: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ CosyVoice2 한국어 중년 여성 스토리텔러 샘플</h1>
        <div class="subtitle">
            표준 16-bit PCM 24,000Hz WAV로 인코딩 완료되어 모든 브라우저 및 윈도우 미디어 플레이어에서 즉시 원활히 재생됩니다.
        </div>
"""

for s in samples:
    html_content += f"""
        <div class="card">
            <div class="card-header">
                <div class="card-title">{s['title']}</div>
                <div class="card-tag">{s['tone']}</div>
            </div>
            <div class="quote-box">
                "{s['text']}"
            </div>
            <audio controls preload="auto" src="{s['file']}"></audio>
        </div>
    """

html_content += """
    </div>
</body>
</html>
"""

player_path = FOLDER / "player_storyteller.html"
with open(player_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"[OK] Created player: {player_path}")
