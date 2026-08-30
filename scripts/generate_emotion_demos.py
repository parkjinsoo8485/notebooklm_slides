import asyncio
import os
import subprocess
import sys
import edge_tts
import soundfile as sf
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = "output/emotion_demo_masters"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TEMP_DIR = "output/emotion_demo_masters/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 4대 대표 감정 시연 슬라이드
EMOTION_SAMPLES = [
    {
        "id": "emotion_01_sadness",
        "slide_index": 2,
        "emotion_type": "😭 [슬픔 / 비통과 눈물]",
        "badge": "슬픔 & 비통",
        "badge_bg": "#475569",
        "border": "#64748b",
        "bg": "#0f172a",
        "desc": "낮게 가라앉는 피치(-28Hz)와 처연한 슬로우 템포(-25%), 깊은 흉성 챔버로 가슴 미어지는 슬픔과 눈물의 여운을 극대화",
        "script": "살을 에는 비바람이 들이치는, ... 차가운 흙바닥에 주저앉아, 마님은 피눈물을 삼키며, 하염없이 흐느꼈습니다... 가문도, 재물도 모두 잃었거늘... 이제 이 가련한 목숨 하나 부지해 무엇하겠는가... 백 년을 이어온 명문가의 영화는, 그렇게 한 줌 잿더미가 되어 흩어지고 말았습니다...",
        "tts_rate": "-25%",
        "tts_pitch": "-28Hz",
        "tts_volume": "-5%",
        "af_filter": (
            "adelay=350|350,"
            "equalizer=f=180:width_type=o:width=1.3:g=5.2,"
            "equalizer=f=400:width_type=o:width=1.2:g=2.2,"
            "equalizer=f=3400:width_type=o:width=1.0:g=-4.2,"
            "aecho=0.8:0.7:25|45:0.14|0.07,"
            "compand=attacks=0.04:decays=0.35:points=-80/-80|-24/-22|-12/-12|0/-2:soft-knee=8,"
            "apad=pad_dur=0.6,"
            "volume=1.22"
        )
    },
    {
        "id": "emotion_02_shock",
        "slide_index": 46,
        "emotion_type": "😱 [놀람 / 경악과 충격]",
        "badge": "놀람 & 경악",
        "badge_bg": "#ef4444",
        "border": "#ef4444",
        "bg": "#220d0d",
        "desc": "순간적으로 올라가는 피치(-16Hz)와 빠른 템포(-16%), 짧게 숨을 들이켜는 호흡 쉼표로 밤중에 비밀을 목격한 마님의 경악을 생생하게 연기",
        "script": "잠에서 깬 마님은, 그 광경을 보고 깜짝 놀라며, '돌쇠야, 네가... 어찌 글을 안단 말이냐!'라며, 떨리는 목소리로 물었습니다.",
        "tts_rate": "-16%",
        "tts_pitch": "-16Hz",
        "tts_volume": "+10%",
        "af_filter": (
            "adelay=300|300,"
            "equalizer=f=200:width_type=o:width=1.4:g=3.2,"
            "equalizer=f=2800:width_type=o:width=1.2:g=2.0,"
            "equalizer=f=3800:width_type=o:width=1.0:g=-2.5,"
            "compand=attacks=0.015:decays=0.2:points=-80/-80|-24/-18|-12/-8|0/0:soft-knee=4,"
            "apad=pad_dur=0.4,"
            "volume=1.28"
        )
    },
    {
        "id": "emotion_03_crisis",
        "slide_index": 27,
        "emotion_type": "⚔️ [긴박 / 추격과 위기]",
        "badge": "긴박 & 위기",
        "badge_bg": "#d97706",
        "border": "#d97706",
        "bg": "#1c1407",
        "desc": "조여드는 속도감(-18%)과 단단한 어택 컴프레션으로 턱밑까지 사병들의 횃불이 쫓아온 일촉즉발의 위기감을 전달",
        "script": "사병들의 거친 고함과 횃불이 등 뒤 턱밑까지 바짝 쫓아왔고, ... 얼음장 같은 칼바람 속에 화살이 귓가를 스치며 빗발쳤습니다!",
        "tts_rate": "-18%",
        "tts_pitch": "-20Hz",
        "tts_volume": "+5%",
        "af_filter": (
            "adelay=300|300,"
            "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
            "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.0,"
            "compand=attacks=0.02:decays=0.25:points=-80/-80|-24/-18|-12/-9|0/-1:soft-knee=6,"
            "apad=pad_dur=0.4,"
            "volume=1.25"
        )
    },
    {
        "id": "emotion_04_joy",
        "slide_index": 85,
        "emotion_type": "🎉 [기쁨 / 환희와 감격]",
        "badge": "기쁨 & 환희",
        "badge_bg": "#10b981",
        "border": "#10b981",
        "bg": "#092215",
        "desc": "밝고 온화하게 열리는 피치(-18Hz)와 경쾌한 리듬 템포(-20%), 화사한 고음역대로 10년 만의 억울함 해소와 춤추는 월이댁의 감격을 표현",
        "script": "월이댁은 덩실덩실 춤을 추며, 기쁨의 눈물을 훔쳤고, ... 10년의 서러운 세월이 봄눈 녹듯 환한 환희로 바뀌는 순간이었습니다!",
        "tts_rate": "-20%",
        "tts_pitch": "-18Hz",
        "tts_volume": "+15%",
        "af_filter": (
            "adelay=350|350,"
            "equalizer=f=195:width_type=o:width=1.4:g=3.2,"
            "equalizer=f=450:width_type=o:width=1.3:g=1.5,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-2.5,"
            "highshelf=f=7500:g=1.0,"
            "aecho=0.8:0.5:20|35:0.08|0.04,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-18|-12/-8|0/-1:soft-knee=6,"
            "apad=pad_dur=0.5,"
            "volume=1.28"
        )
    }
]

async def build_emotion_demos():
    generated_data = []

    for item in EMOTION_SAMPLES:
        preset_id = item["id"]
        print(f"--> Generating: {item['emotion_type']}")
        sr_target = 24000
        
        raw_mp3 = os.path.join(TEMP_DIR, f"{preset_id}_raw.mp3")
        final_mp3 = os.path.join(OUTPUT_DIR, f"{preset_id}.mp3")

        # 1. Edge-TTS with Emotion Parameters
        comm = edge_tts.Communicate(
            item["script"],
            voice="ko-KR-SunHiNeural",
            rate=item["tts_rate"],
            pitch=item["tts_pitch"],
            volume=item["tts_volume"]
        )
        await comm.save(raw_mp3)

        # 2. FFmpeg Emotion DSP Filter Chain
        cmd = [
            "ffmpeg", "-y", "-i", raw_mp3,
            "-af", item["af_filter"],
            "-ar", "24000", "-b:a", "192k",
            final_mp3
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        y_final, sr = librosa.load(final_mp3, sr=24000)
        duration = len(y_final) / sr
        f0, voiced_flag, voiced_probs = librosa.pyin(y_final, fmin=80, fmax=400, sr=sr)
        valid_f0 = f0[~np.isnan(f0)]
        mean_f0 = float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0.0

        p_info = item.copy()
        p_info["file"] = f"{preset_id}.mp3"
        p_info["duration"] = f"{duration:.2f}초"
        p_info["f0"] = f"{mean_f0:.1f} Hz"
        generated_data.append(p_info)
        print(f"Done: {final_mp3} ({duration:.2f}s, {mean_f0:.1f}Hz)")

    create_html_player(generated_data)

def create_html_player(items):
    cards_html = ""
    for it in items:
        cards_html += f"""
        <div class="card" style="border: 2px solid {it['border']}; background: {it['bg']};">
            <div class="card-header">
                <div class="title-row">
                    <span class="badge" style="background: {it['badge_bg']};">{it['badge']}</span>
                    <h3>{it['emotion_type']} (슬라이드 {it['slide_index']})</h3>
                </div>
                <div class="metrics">
                    <span>⏱️ 재생 길이: <strong>{it['duration']}</strong></span>
                    <span>🎵 실측 F0 피치: <strong>{it['f0']}</strong></span>
                </div>
            </div>
            <p class="desc">{it['desc']}</p>
            <div class="script-box">
                <div class="script-content">"{it['script']}"</div>
            </div>
            <div class="player-wrapper">
                <audio controls preload="auto" src="emotion_demo_masters/{it['file']}"></audio>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 4대 감정(슬픔/놀람/긴박/기쁨) 다이내믹 연기 청음실</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #06080e;
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
        .benchmark-box {{
            background: #0f172a;
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 35px;
        }}
        .benchmark-box h4 {{
            color: #10b981;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }}
        .benchmark-box ul {{
            padding-left: 20px;
            color: #cbd5e1;
            font-size: 0.95rem;
        }}
        .benchmark-box li {{
            margin-bottom: 6px;
        }}
        .card {{
            border-radius: 14px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 14px 30px rgba(0,0,0,0.7);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .title-row {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .badge {{
            font-size: 0.8rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            color: #fff;
        }}
        .card h3 {{
            font-size: 1.3rem;
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
        .desc {{
            color: #cbd5e1;
            font-size: 0.98rem;
            margin-bottom: 14px;
        }}
        .script-box {{
            background: rgba(0, 0, 0, 0.4);
            border-left: 3px solid rgba(255,255,255,0.3);
            padding: 14px 18px;
            margin-bottom: 18px;
            border-radius: 4px;
        }}
        .script-content {{
            font-size: 1rem;
            color: #f1f5f9;
            line-height: 1.65;
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
            <h1>🎭 [송림야담] 4대 감정(슬픔/놀람/긴박/기쁨) 다이내믹 연기 청음실</h1>
            <p>슬라이드 문맥에 따른 실시간 감정선(Emotional Dynamics: 피치, 템포, 볼륨, 흉성 EQ) 제어</p>
        </div>

        <div class="benchmark-box">
            <h4>💡 감정(Emotion)별 4대 음향 연출 원리</h4>
            <ul>
                <li><strong>😭 슬픔 / 비통 (피치 -28Hz, 템포 -25%)</strong>: 목소리를 깊게 가라앉히고 처연한 쉼표로 눈물의 호흡을 전달</li>
                <li><strong>😱 놀람 / 경악 (피치 -16Hz, 템포 -16%)</strong>: 순간적인 고음 텐션과 짧은 정적으로 뜻밖의 비밀을 본 충격을 표현</li>
                <li><strong>⚔️ 긴박 / 위기 (피치 -20Hz, 템포 -18%)</strong>: 단단하고 빠른 어택 컴프레션으로 턱밑까지 쫓아온 사병들의 일촉즉발 위기감 전달</li>
                <li><strong>🎉 기쁨 / 환희 (피치 -18Hz, 템포 -20%)</strong>: 밝고 화사한 톤과 볼륨(+1.5dB)으로 10년 만의 감격과 춤추는 월이댁의 기쁨을 표현</li>
            </ul>
        </div>

        {cards_html}

        <div class="footer">
            <p>※ 확인 후 전체 120개 슬라이드에 감정별 맞춤 파라미터를 100% 일괄 연동하여 확장할 수 있습니다.</p>
        </div>
    </div>
</body>
</html>
"""
    player_path = "output/emotion_player.html"
    with open(player_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Emotion player updated: {player_path}")

if __name__ == "__main__":
    asyncio.run(build_emotion_demos())
