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

ADVANCED_EMOTIONS = [
    {
        "id": "emotion_01_grief_master",
        "slide_index": 2,
        "title": "😭 [비통 / 오열과 절망 극대화 버전]",
        "badge": "비통 & 오열 (극대화)",
        "badge_bg": "#4338ca",
        "border": "#6366f1",
        "bg": "#0c0e27",
        "solution": "해설과 마님의 오열 대사를 분리 합성 + '흑... 아아...' 탄식 호흡 + 비통한 목소리 떨림(Tremolo/Vibrato) DSP 결합",
        "segments": [
            {
                "type": "narration",
                "text": "살을 에는 비바람이 들이치는, ... 차가운 흙바닥에 주저앉아, 마님은 피눈물을 삼키며 하염없이 흐느꼈습니다...",
                "rate": "-24%",
                "pitch": "-26Hz",
                "filter": "equalizer=f=180:g=4.5,compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|0/-1"
            },
            {
                "type": "grief_cry",
                "text": "흑... 가문도... 재물도... 모두 잃었거늘... 아아, 이제 이 가련한 목숨 하나... 부지해 무엇하겠는가...",
                "rate": "-28%",
                "pitch": "-18Hz",
                "filter": "tremolo=f=4.0:d=0.28,equalizer=f=220:g=3.5,equalizer=f=3200:g=-3.0,aecho=0.8:0.7:30|50:0.18|0.09,volume=1.35"
            },
            {
                "type": "narration_end",
                "text": "백 년을 이어온 명문가의 영화는, 그렇게 한 줌 잿더미가 되어 흩어지고 말았습니다...",
                "rate": "-24%",
                "pitch": "-28Hz",
                "filter": "equalizer=f=180:g=4.5,compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|0/-1"
            }
        ]
    },
    {
        "id": "emotion_02_shock_master",
        "slide_index": 46,
        "title": "😱 [경악 / 충격과 공포 극대화 버전]",
        "badge": "경악 & 충격 (극대화)",
        "badge_bg": "#dc2626",
        "border": "#ef4444",
        "bg": "#200a0a",
        "solution": "마님의 급박한 심박수 고음 텐션(+14Hz) + '돌쇠야...?! 네가... 대체 어떻게!' 경악 구어체 엔지니어링 + 순간 정적(0.4초 컷) 극적 연출",
        "segments": [
            {
                "type": "narration",
                "text": "깊은 밤, 잠에서 깬 마님은, 등불 아래 글을 적고 있는 돌쇠를 발견하고... 숨이 턱 막히고 말았습니다.",
                "rate": "-22%",
                "pitch": "-24Hz",
                "filter": "equalizer=f=190:g=4.0"
            },
            {
                "type": "shock_scream",
                "text": "돌쇠야...?! 네가... 대체 어떻게... 글을 쓴단 말이냐...?!",
                "rate": "-12%",
                "pitch": "+14Hz",
                "filter": "equalizer=f=3000:g=3.5,compand=attacks=0.01:decays=0.15:points=-80/-80|-20/-14|0/0,volume=1.45"
            },
            {
                "type": "narration_end",
                "text": "어둠 속에서 마님의 두 눈은, 믿을 수 없다는 듯 한없이 흔들렸습니다.",
                "rate": "-22%",
                "pitch": "-25Hz",
                "filter": "equalizer=f=190:g=4.0"
            }
        ]
    }
]

async def build_advanced_emotions():
    results = []

    for item in ADVANCED_EMOTIONS:
        track_id = item["id"]
        print(f"🎬 Processing: {item['title']}")
        
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

def update_emotion_html(advanced_items):
    cards_html = ""
    for it in advanced_items:
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
                <strong>🛠️ 적용된 감정 극대화 기술:</strong> {it['solution']}
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
    <title>[송림야담] 감정 연기 한계 돌파 - 비통/오열 & 경악/충격 극대화 청음실</title>
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
            border: 1px solid #38bdf8;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 35px;
        }}
        .analysis-box h4 {{
            color: #38bdf8;
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
            background: rgba(56, 189, 248, 0.1);
            border-left: 4px solid #38bdf8;
            padding: 10px 14px;
            margin-bottom: 14px;
            font-size: 0.92rem;
            color: #e0f2fe;
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
            <h1>🎭 [송림야담] 감정 연기 한계 돌파 솔루션 청음실</h1>
            <p>책 읽는 느낌을 탈피한 [대사 분할 다이내믹 피치 + 오열 떨림 DSP + 경악 구어체 엔지니어링]</p>
        </div>

        <div class="analysis-box">
            <h4>💡 기존 TTS의 '책 읽는 느낌' 원인과 극복 솔루션</h4>
            <ul>
                <li><strong>원인</strong>: 단일 문장 일괄 피치/속도 지정 시 신경망이 평이한 뉴스 낭독조로 발화하여 대사의 감정이 실리지 않음.</li>
                <li><strong>해결 1 (다구간 분할 합성)</strong>: 나레이션(차분한 중저음)과 대사(격정적 고음/비통 저음)를 문장 단위로 분할하여 독립 피치로 합성 후 결합.</li>
                <li><strong>해결 2 (구어체 탄식/호흡 엔지니어링)</strong>: <code>'흑...'</code>, <code>'아아,'</code>, <code>'...?!'</code> 등 실제 사람이 울먹이거나 기겁할 때 나오는 구어체 호흡을 신경망에 주입.</li>
                <li><strong>해결 3 (오열 비브라토/트레몰로 DSP)</strong>: 슬픈 대사 구간에 미세한 목소리 떨림(Tremolo/Vibrato) 필터를 걸어 가슴을 쥐어짜는 오열 연출 완성.</li>
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
    print(f"Updated emotion player: {player_path}")

if __name__ == "__main__":
    asyncio.run(build_advanced_emotions())
