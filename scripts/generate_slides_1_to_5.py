import asyncio
import json
import os
import subprocess
import sys
import edge_tts
import soundfile as sf
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = "output"
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
SLIDES_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "slides_1_to_5_audio")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp_tts")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SLIDES_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# 4번 [완벽 일체형 + 편안한 리듬 완급 마스터] 공식 스펙
VOICE_NAME = "ko-KR-SunHiNeural"
RATE = "-22%"
PITCH = "-24Hz"
AF_FILTER = (
    "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
    "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
    "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
    "highshelf=f=7500:g=-2.0,"
    "aecho=0.8:0.6:20|35:0.10|0.05,"
    "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
    "volume=1.25"
)

# '~더랬지요' 표현 완전 삭제 & 정통 자연스러운 스토리텔링 문체로 수정한 대본
SLIDES_1_TO_5 = [
    {
        "slide_index": 1,
        "title": "제1막: 버려진 오두막과 충직한 머슴 - 발단",
        "screen_text": "한양 북촌 명문가의 안주인이었던 윤씨 마님, 하루아침에 역모의 누명을 쓰고 쫓겨나다.",
        "voice_script": "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이... 하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 쫓겨나고 말았습니다... 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었습니다."
    },
    {
        "slide_index": 2,
        "title": "제1막: 가문과 재물의 몰락",
        "screen_text": "가문도, 재물도 모두 잃었거늘 이제 이 가련한 목숨 하나 부지해 무엇하겠는가.",
        "voice_script": "살을 에는 비바람이 들이치는 차가운 흙바닥에 주저앉아, 마님은 피눈물을 삼키며 하염없이 흐느꼈습니다... 가문도 재물도 모두 잃었거늘, 이제 이 가련한 목숨 하나 부지해 무엇하겠는가... 백 년을 이어온 명문가의 영화는, 그렇게 한 줌 잿더미가 되어 흩어지고 말았습니다."
    },
    {
        "slide_index": 3,
        "title": "제1막: 냉혹한 세상과 외면",
        "screen_text": "화려했던 비단옷은 흙탕물에 찢기고, 수많은 노비와 친척들은 모두 마님을 외면했습니다.",
        "voice_script": "곱디곱던 비단옷은 흙탕물에 찢기고... 평소 머리를 조아리던 친척과 노비들마저 역적의 집안이라 손가락질하며, 뒤도 돌아보지 않고 뿔뿔이 달아나 버렸습니다..."
    },
    {
        "slide_index": 4,
        "title": "제1막: 유일하게 달려온 충직한 머슴 돌쇠",
        "screen_text": "마님! 소인 돌쇠가 여기 있사옵니다. 결코 마님을 홀로 두지 않을 것입니다.",
        "voice_script": "그때, 어둠을 뚫고 거친 숨을 몰아쉬며 한 사내가 달려왔습니다... 대감댁에서 가장 궂은일을 도맡아 하던, 우직하고 충직한 머슴 돌쇠였습니다..."
    },
    {
        "slide_index": 5,
        "title": "제1막: 눈물의 만류와 충심의 맹세",
        "screen_text": "돌쇠야, 어서 도망치거라. 나와 함께 있다가는 너마저 목숨을 부지하지 못한다.",
        "voice_script": "마님은 피눈물을 흘리며, '돌쇠야 어서 도망치거라, 나와 함께 있다간 너마저 목숨을 잃는다'며, 떨리는 손으로 그를 밀어내려 하였습니다..."
    }
]

async def generate_slide_audio(slide):
    idx = slide["slide_index"]
    script = slide["voice_script"]
    raw_mp3 = os.path.join(TEMP_DIR, f"slide_{idx:03d}_raw.mp3")
    final_mp3 = os.path.join(AUDIO_DIR, f"slide_{idx:03d}.mp3")
    demo_mp3 = os.path.join(SLIDES_OUTPUT_DIR, f"slide_{idx:03d}.mp3")

    # 1. Edge-TTS Single-stream Synthesis
    communicate = edge_tts.Communicate(script, voice=VOICE_NAME, rate=RATE, pitch=PITCH)
    await communicate.save(raw_mp3)

    # 2. FFmpeg Studio Mastering Filter Chain
    cmd = [
        "ffmpeg", "-y", "-i", raw_mp3,
        "-af", AF_FILTER,
        "-ar", "24000", "-b:a", "192k",
        final_mp3
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # Copy to demo folder
    subprocess.run(["ffmpeg", "-y", "-i", final_mp3, "-c", "copy", demo_mp3], capture_output=True, check=True)

    # Audio Metric Analysis
    y, sr = librosa.load(final_mp3, sr=24000)
    duration = len(y) / sr
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=80, fmax=400, sr=sr)
    valid_f0 = f0[~np.isnan(f0)]
    mean_f0 = float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0.0

    print(f"✅ [슬라이드 {idx}] 수정 생성 완료: {final_mp3} (길이: {duration:.2f}초, F0: {mean_f0:.1f}Hz)")
    
    slide_res = slide.copy()
    slide_res["duration"] = f"{duration:.2f}초"
    slide_res["f0"] = f"{mean_f0:.1f} Hz"
    slide_res["filename"] = f"slide_{idx:03d}.mp3"
    return slide_res

async def main():
    print("🚀 [송림야담] 자연스러운 스토리형 대본으로 슬라이드 1~5번 재생성 시작...")
    results = []
    for s in SLIDES_1_TO_5:
        res = await generate_slide_audio(s)
        results.append(res)
    
    create_slides_player(results)

def create_slides_player(slides):
    cards_html = ""
    for s in slides:
        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <div class="title-box">
                    <span class="badge">슬라이드 {s['slide_index']}</span>
                    <h3>{s['title']}</h3>
                </div>
                <div class="metrics">
                    <span>⏱️ 재생 시간: <strong>{s['duration']}</strong></span>
                    <span>🎵 F0 피치: <strong>{s['f0']}</strong></span>
                </div>
            </div>
            <div class="script-box">
                <div class="script-label">📜 자연스럽게 수정된 스토리형 대본</div>
                <div class="script-content">"{s['voice_script']}"</div>
            </div>
            <div class="player-wrapper">
                <audio controls preload="auto" src="slides_1_to_5_audio/{s['filename']}"></audio>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 슬라이드 1~5번 자연스러운 스토리형 음성 청음실</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #07090e;
            color: #e2e8f0;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 25px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 2.2rem;
            color: #f8fafc;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 1.05rem;
        }}
        .spec-box {{
            background: #0f172a;
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 35px;
        }}
        .spec-box h4 {{
            color: #10b981;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }}
        .spec-box ul {{
            padding-left: 20px;
            color: #cbd5e1;
            font-size: 0.95rem;
        }}
        .spec-box li {{
            margin-bottom: 6px;
        }}
        .card {{
            background: #0d131f;
            border: 2px solid #1e293b;
            border-radius: 14px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .card:hover {{
            transform: translateY(-2px);
            border-color: #10b981;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .title-box {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .badge {{
            font-size: 0.85rem;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 6px;
            background: #10b981;
            color: #fff;
        }}
        .card h3 {{
            font-size: 1.25rem;
            color: #fff;
        }}
        .metrics {{
            display: flex;
            gap: 15px;
            font-size: 0.9rem;
            color: #94a3b8;
            background: rgba(0,0,0,0.3);
            padding: 6px 14px;
            border-radius: 8px;
        }}
        .metrics strong {{
            color: #38bdf8;
        }}
        .script-box {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 18px;
        }}
        .script-label {{
            font-size: 0.8rem;
            color: #10b981;
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .script-content {{
            font-size: 1.05rem;
            color: #f1f5f9;
            line-height: 1.7;
        }}
        .player-wrapper audio {{
            width: 100%;
            height: 48px;
            border-radius: 8px;
            outline: none;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #64748b;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 [송림야담] 슬라이드 1~5번 자연스러운 스토리형 음성 청음실</h1>
            <p>'~였더랬지요' 어색한 어미 완전 삭제 ➔ 깔끔하고 품격 있는 정통 스토리텔링 문체 적용</p>
        </div>

        <div class="spec-box">
            <h4>✨ 수정 및 적용 내역</h4>
            <ul>
                <li><strong>어미 수정</strong>: <code>~였더랬지요</code>, <code>~말았더랬지요</code> ➔ <code>~였습니다</code>, <code>~말았습니다</code>, <code>~흐느꼈습니다</code> 등 매끄러운 서사형 종결어미로 정비</li>
                <li><strong>보이스 & 톤</strong>: ko-KR-SunHiNeural (피치: <code>-24Hz</code>, 템포: <code>-22%</code>)</li>
                <li><strong>스튜디오 DSP</strong>: 190Hz/450Hz 흉성 EQ 부스트 + 3600Hz 치찰음 제어 + 20ms 챔버 앰비언스 리버브</li>
                <li><strong>출력 파일</strong>: <code>output/audio/slide_001.mp3</code> ~ <code>slide_005.mp3</code></li>
            </ul>
        </div>

        {cards_html}

        <div class="footer">
            <p>※ 슬라이드 1~5번 음성 확인 후 전체 120개 슬라이드 일괄 생성 및 비디오 렌더링을 진행할 수 있습니다.</p>
        </div>
    </div>
</body>
</html>
"""
    player_path = "output/slides_1_to_5_player.html"
    with open(player_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Player updated: {player_path}")

if __name__ == "__main__":
    asyncio.run(main())
