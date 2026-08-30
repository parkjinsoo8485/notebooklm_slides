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

REFINED_EMOTIONS = [
    {
        "id": "emotion_01_grief_v2",
        "slide_index": 2,
        "title": "😭 [비통 / 가슴 찢어지는 침잠 독백 마스터]",
        "badge": "비통 & 침잠 (고도화 V2)",
        "badge_bg": "#1e1b4b",
        "border": "#818cf8",
        "bg": "#08091a",
        "solution": "어색한 의성어('흑') 완전 제거! 깊게 가라앉는 처연한 저음(-30Hz)과 가슴이 미어지듯 읊조리는 느린 호흡(-28%) + 180Hz 흉성 챔버로 진정한 한(恨)과 비통함을 구현",
        "segments": [
            {
                "type": "narration_intro",
                "text": "살을 에는 비바람이 들이치는 차가운 흙바닥에 주저앉아, 마님은 피눈물을 삼키며 하염없이 흐느꼈습니다.",
                "rate": "-24%",
                "pitch": "-25Hz",
                "filter": "equalizer=f=185:width_type=o:width=1.4:g=4.5,equalizer=f=450:g=2.0,equalizer=f=3600:g=-3.5,compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|0/-1"
            },
            {
                "type": "madam_grief",
                "text": "가문도, 재물도... 모두 잃어버렸거늘... 이제 이 가련한 목숨 하나 부지하여... 대체 무엇을 하겠는가...",
                "rate": "-28%",         # 깊은 슬픔으로 느려진 읊조림
                "pitch": "-30Hz",        # 낮고 무겁게 침잠하는 마님의 비통 톤
                # 깊은 흉성 + 슬픔의 잔향 챔버
                "filter": "equalizer=f=175:width_type=o:width=1.3:g=5.8,equalizer=f=380:width_type=o:width=1.2:g=2.5,equalizer=f=3200:g=-4.5,aecho=0.8:0.7:25|45:0.16|0.08,compand=attacks=0.04:decays=0.35:points=-80/-80|-24/-22|-12/-10|0/-2:soft-knee=8,volume=1.3"
            },
            {
                "type": "narration_outro",
                "text": "백 년을 이어온 명문가의 영화는, 그렇게 한 줌 잿더미가 되어 흩어지고 말았습니다.",
                "rate": "-24%",
                "pitch": "-26Hz",
                "filter": "equalizer=f=185:width_type=o:width=1.4:g=4.5,equalizer=f=450:g=2.0,equalizer=f=3600:g=-3.5,compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|0/-1"
            }
        ]
    },
    {
        "id": "emotion_02_shock_v2",
        "slide_index": 46,
        "title": "😱 [경악 / 기품 있는 마님의 중후한 충격 마스터]",
        "badge": "경악 & 기품 (고도화 V2)",
        "badge_bg": "#7f1d1d",
        "border": "#f87171",
        "bg": "#180606",
        "solution": "젊은 여자 톤 탈피! 마님 본연의 중후한 흉성 피치(-20Hz) 유지 + 말문이 턱 막히는 순간 정적(0.4초)과 숨죽인 충격 템포(-18%)로 품격 있는 귀부인의 경악을 완성",
        "segments": [
            {
                "type": "narration_intro",
                "text": "깊은 밤, 잠에서 깬 마님은 등불 아래 글을 적고 있는 돌쇠를 발견하고... 숨이 턱 막히고 말았습니다.",
                "rate": "-22%",
                "pitch": "-24Hz",
                "filter": "equalizer=f=190:g=4.0,equalizer=f=450:g=2.0,compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|0/-1"
            },
            {
                "type": "madam_shock",
                "text": "돌쇠야... 네가... 대체 어떻게... 글을 쓴단 말이냐...",
                "rate": "-18%",         # 숨죽이며 짓누르듯 묻는 충격 템포
                "pitch": "-20Hz",        # 마님 고유의 기품 있는 중저음 유지 (고음 피치 제거)
                # 날카롭지 않고 묵직하게 압도하는 충격 컴프레션
                "filter": "equalizer=f=200:width_type=o:width=1.4:g=4.2,equalizer=f=500:g=2.2,equalizer=f=3400:g=-3.0,compand=attacks=0.015:decays=0.2:points=-80/-80|-22/-17|-10/-7|0/0:soft-knee=4,volume=1.35"
            },
            {
                "type": "narration_outro",
                "text": "어둠 속에서 마님의 두 눈은, 믿을 수 없다는 듯 한없이 흔들렸습니다.",
                "rate": "-22%",
                "pitch": "-25Hz",
                "filter": "equalizer=f=190:g=4.0,equalizer=f=450:g=2.0,compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|0/-1"
            }
        ]
    }
]

async def build_refined_emotions():
    results = []

    for item in REFINED_EMOTIONS:
        track_id = item["id"]
        print(f"🎬 Processing Refined V2: {item['title']}")
        
        seg_audios = []
        sr = 24000

        for idx, seg in enumerate(item["segments"]):
            seg_raw = os.path.join(TEMP_DIR, f"{track_id}_seg_{idx}_raw.mp3")
            seg_filt = os.path.join(TEMP_DIR, f"{track_id}_seg_{idx}_filt.wav")

            comm = edge_tts.Communicate(
                seg["text"],
                voice="ko-KR-SunHiNeural",
                rate=seg["rate"],
                pitch=seg["pitch"],
                volume="+10%"
            )
            await comm.save(seg_raw)

            # Apply segment filter
            filt = seg["filter"]
            cmd = ["ffmpeg", "-y", "-i", seg_raw, "-af", filt, "-ar", str(sr), seg_filt]
            subprocess.run(cmd, capture_output=True, check=True)
            
            y, _ = librosa.load(seg_filt, sr=sr)
            seg_audios.append(y)

        # Concatenate with silence pauses
        leading_silence = np.zeros(int(sr * 0.35))
        pause_between = np.zeros(int(sr * 0.45))
        trailing_silence = np.zeros(int(sr * 0.50))

        full_chain = [leading_silence]
        for i, y_seg in enumerate(seg_audios):
            full_chain.append(y_seg)
            if i < len(seg_audios) - 1:
                full_chain.append(pause_between)
        full_chain.append(trailing_silence)

        final_y = np.concatenate(full_chain)
        final_wav = os.path.join(TEMP_DIR, f"{track_id}_merged.wav")
        sf.write(final_wav, final_y, sr)

        final_mp3 = os.path.join(OUTPUT_DIR, f"{track_id}.mp3")
        # Master final mp3
        cmd = [
            "ffmpeg", "-y", "-i", final_wav,
            "-af", "volume=1.2",
            "-ar", "24000", "-b:a", "192k",
            final_mp3
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        dur = len(final_y) / sr
        f0, _, _ = librosa.pyin(final_y, fmin=80, fmax=400, sr=sr)
        valid_f0 = f0[~np.isnan(f0)]
        mean_f0 = float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0.0

        res_item = item.copy()
        res_item["file"] = f"{track_id}.mp3"
        res_item["duration"] = f"{dur:.2f}초"
        res_item["f0"] = f"{mean_f0:.1f} Hz"
        results.append(res_item)
        print(f"✅ Generated: {final_mp3} ({dur:.2f}s, {mean_f0:.1f}Hz)")

    update_emotion_html(results)

def update_emotion_html(refined_items):
    cards_html = ""
    for it in refined_items:
        full_text = " ".join([s["text"] for s in it["segments"]])
        cards_html += f"""
        <div class="card" style="border: 2px solid {it['border']}; background: {it['bg']};">
            <div class="card-header">
                <div class="title-row">
                    <span class="badge" style="background: {it['badge_bg']};">{it['badge']}</span>
                    <h3>{it['title']}</h3>
                </div>
                <div class="metrics">
                    <span>⏱️ 재생 길이: <strong>{it['duration']}</strong></span>
                    <span>🎵 실측 F0: <strong>{it['f0']}</strong></span>
                </div>
            </div>
            <div class="solution-box">
                <strong>🛠️ V2 핵심 보완점:</strong> {it['solution']}
            </div>
            <div class="script-box">
                <div class="script-content">"{full_text}"</div>
            </div>
            <div class="player-wrapper">
                <audio controls preload="auto" src="emotion_demo_masters/{it['file']}?v={np.random.randint(1000,9999)}"></audio>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 마님 품격 연기 V2 - 비통 침잠 & 중후한 경악 청음실</title>
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
        }}
        .header p {{
            color: #94a3b8;
            font-size: 1.05rem;
        }}
        .analysis-box {{
            background: #0f172a;
            border: 1px solid #818cf8;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 35px;
        }}
        .analysis-box h4 {{
            color: #818cf8;
            margin-bottom: 12px;
            font-size: 1.15rem;
        }}
        .analysis-box ul {{
            padding-left: 20px;
            color: #cbd5e1;
            font-size: 0.95rem;
        }}
        .analysis-box li {{
            margin-bottom: 8px;
        }}
        .card {{
            border-radius: 14px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
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
            font-size: 0.85rem;
            font-weight: 700;
            padding: 5px 12px;
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
        .solution-box {{
            background: rgba(129, 140, 248, 0.1);
            border-left: 4px solid #818cf8;
            padding: 10px 14px;
            margin-bottom: 14px;
            font-size: 0.92rem;
            color: #e0e7ff;
            border-radius: 0 6px 6px 0;
        }}
        .script-box {{
            background: rgba(0, 0, 0, 0.4);
            border-left: 3px solid rgba(255,255,255,0.3);
            padding: 14px 18px;
            margin-bottom: 18px;
            border-radius: 4px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 [송림야담] 마님 품격 연기 V2 청음실</h1>
            <p>어색한 의성어 완전 배제 + 마님 본연의 기품 있는 중후한 흉성 유지</p>
        </div>

        <div class="analysis-box">
            <h4>💡 V2 핵심 피드백 반영 사항</h4>
            <ul>
                <li><strong>1. '돌쇠야' 젊은 여자 목소리 해결</strong>: 피치를 높이지 않고 마님 고유의 묵직한 중저음(-20Hz)을 유지하며, 숨이 턱 막히는 순간 정적(0.4초)과 무거운 호흡으로 귀부인의 경악을 연기.</li>
                <li><strong>2. '가문도 재물도' 어색한 책 읽기 해결</strong>: Edge-TTS가 엉뚱하게 발음하던 의성어(<code>흑...</code>)를 완전히 제거하고, 낮게 읊조리는 침잠 톤(-30Hz, 템포 -28%)과 깊은 흉성 챔버로 가슴 미어지는 한(恨)을 사실적으로 구현.</li>
            </ul>
        </div>

        {cards_html}

    </div>
</body>
</html>
"""
    player_path = "output/emotion_player.html"
    with open(player_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated emotion player V2: {player_path}")

if __name__ == "__main__":
    asyncio.run(build_refined_emotions())
