import asyncio
import subprocess
import os
import sys
import edge_tts
import soundfile as sf
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = "output/storyteller_masters"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TEMP_DIR = "output/storyteller_masters/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 능청스럽고 무게감 있는 완급 조절을 극대화한 명품 여성 스토리텔러 4대 프리셋
STORYTELLER_PRESETS = {
    "master_sly_weight_sunhi": {
        "name": "👑 1. [송림야담 정통 능청·무게감 마스터] (초강력 추천)",
        "voice": "ko-KR-SunHiNeural",
        "badge": "★ 능청 & 무게감 극대화",
        "badge_bg": "#10b981",
        "border": "#10b981",
        "bg": "#092215",
        "desc": "고전 이야기꾼 특유의 능청스러운 운 띄우기('옛날 옛적...')와 급변하는 비극 전개('하루아침에! 억울한 역모의...'), 묵직하게 가라앉는 어미 말끝(-32%)으로 청중을 쥐락펴락하는 완급 조절의 정점",
        "segments": [
            ("옛날 옛적...", "-16%", "-10Hz", "+0%", 0.90),
            ("한양 북촌 명문가의,", "-8%", "-16Hz", "+0%", 0.45),
            ("어질고 고왔던 윤씨 마님이...", "-14%", "-18Hz", "+0%", 0.70),
            ("하루아침에,", "-6%", "-12Hz", "+10%", 0.40),
            ("억울한 역모의 누명을 쓰고...", "-18%", "-22Hz", "-5%", 0.90),
            ("첩첩산중 깊은 산골로,", "-14%", "-20Hz", "+0%", 0.50),
            ("내쫓기고 말았더랬지요...", "-32%", "-26Hz", "+0%", 1.25),
            ("차가운 달빛조차,", "-12%", "-18Hz", "+0%", 0.40),
            ("서럽게 얼어붙던...", "-20%", "-24Hz", "-10%", 0.85),
            ("어느 쓸쓸한 늦가을 밤의 비극이었답니다.", "-34%", "-28Hz", "+0%", 0.90),
        ],
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=4.2,"
            "equalizer=f=420:width_type=o:width=1.3:g=2.2,"
            "equalizer=f=3400:width_type=o:width=1.0:g=-3.8,"
            "highshelf=f=7200:g=-2.5,"
            "aecho=0.8:0.6:22|40:0.12|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.28"
        )
    },
    "master_deep_gravitas_sunhi": {
        "name": "💎 2. [중후한 흉성 그라비타스 마스터 - 묵직한 카리스마]",
        "voice": "ko-KR-SunHiNeural",
        "badge": "묵직한 중저음",
        "badge_bg": "#3b82f6",
        "border": "#3b82f6",
        "bg": "#0f172a",
        "desc": "피치를 -24Hz~-30Hz로 깊게 가라앉혀 40~50대 대형 베테랑 성우의 묵직한 흉성과 신뢰감 있는 카리스마를 부여한 마스터",
        "segments": [
            ("옛날 옛적...", "-20%", "-18Hz", "+0%", 0.95),
            ("한양 북촌 명문가의 어질고 고왔던 윤씨 마님이,", "-12%", "-22Hz", "+0%", 0.65),
            ("하루아침에 억울한 역모의 누명을 쓰고...", "-18%", "-26Hz", "-10%", 0.95),
            ("첩첩산중 깊은 산골로,", "-14%", "-24Hz", "+0%", 0.50),
            ("내쫓기고 말았더랬지요...", "-34%", "-30Hz", "+0%", 1.30),
            ("차가운 달빛조차 서럽게 얼어붙던...", "-16%", "-24Hz", "-10%", 0.80),
            ("어느 쓸쓸한 늦가을 밤의 비극이었답니다.", "-36%", "-32Hz", "+0%", 0.90),
        ],
        "af_filter": (
            "equalizer=f=180:width_type=o:width=1.4:g=4.8,"
            "equalizer=f=380:width_type=o:width=1.2:g=2.5,"
            "equalizer=f=3200:width_type=o:width=1.0:g=-4.2,"
            "aecho=0.8:0.7:24|44:0.12|0.06,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    },
    "master_folklore_jeon-gisu": {
        "name": "📜 3. [구성진 조선 여류 전기수(傳奇叟) 마스터]",
        "voice": "ko-KR-SunHiNeural",
        "badge": "구성진 야담 연기",
        "badge_bg": "#d97706",
        "border": "#d97706",
        "bg": "#1c1407",
        "desc": "마치 사랑방에 둘러앉은 청중들에게 능글맞게 이야기를 들려주듯, 호흡의 끊고 맺음(0.4초~1.2초)과 억양의 높낮이가 가장 다채로운 구연 특화 톤",
        "segments": [
            ("옛날 옛적에...", "-12%", "-8Hz", "+5%", 0.85),
            ("한양 북촌 명문가에,", "-8%", "-14Hz", "+0%", 0.40),
            ("어질고 참으로 고왔던 윤씨 마님이 계셨는데...", "-16%", "-18Hz", "+0%", 0.75),
            ("아, 글쎄... 하루아침에!", "-6%", "-10Hz", "+15%", 0.55),
            ("억울한 역모의 누명을 쓰고 말입니다...", "-18%", "-24Hz", "-10%", 0.95),
            ("첩첩산중 깊은 산골로 내쫓기고 말았더랬지요...", "-30%", "-26Hz", "+0%", 1.20),
            ("차가운 달빛조차 서럽게 얼어붙던...", "-18%", "-20Hz", "-5%", 0.75),
            ("어느 쓸쓸한 늦가을 밤의 비극이었답니다.", "-32%", "-28Hz", "+0%", 0.90),
        ],
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
            "equalizer=f=450:width_type=o:width=1.4:g=1.8,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "aecho=0.8:0.6:20|38:0.10|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    },
    "master_poetic_night": {
        "name": "🌌 4. [심야 비극 서사시 마스터 - 애절한 여운]",
        "voice": "ko-KR-SunHiNeural",
        "badge": "서사적 비장미",
        "badge_bg": "#8b5cf6",
        "border": "#8b5cf6",
        "bg": "#1e1136",
        "desc": "서정적이고 비장한 고전 시 낭송의 호흡을 결합하여, 듣는 내내 눈물이 날 듯한 애절함과 묵직한 몰입감을 선사하는 심야 전용 마스터",
        "segments": [
            ("옛날 옛적...", "-22%", "-16Hz", "+0%", 0.90),
            ("한양 북촌 명문가의 어질고 고왔던 윤씨 마님이,", "-14%", "-20Hz", "+0%", 0.65),
            ("하루아침에 억울한 역모의 누명을 쓰고...", "-20%", "-26Hz", "-15%", 1.00),
            ("첩첩산중 깊은 산골로 내쫓기고 말았더랬지요...", "-34%", "-28Hz", "+0%", 1.30),
            ("차가운 달빛조차 서럽게 얼어붙던...", "-18%", "-22Hz", "-10%", 0.80),
            ("어느 쓸쓸한 늦가을 밤의 비극이었답니다.", "-36%", "-30Hz", "+0%", 0.90),
        ],
        "af_filter": (
            "equalizer=f=185:width_type=o:width=1.5:g=4.0,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-4.2,"
            "lowpass=f=7500,"
            "aecho=0.8:0.6:25|45:0.12|0.05,"
            "compand=attacks=0.04:decays=0.35:points=-80/-80|-24/-22|-12/-11|0/-1:soft-knee=6,"
            "volume=1.22"
        )
    }
}

async def generate_segment(text, voice, rate, pitch, volume, out_path):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, volume=volume)
    await communicate.save(out_path)

async def build_directed_masters():
    generated_data = []

    for preset_id, info in STORYTELLER_PRESETS.items():
        print(f"--> Generating: {info['name']}")
        combined_audio = []
        sr_target = 24000

        for seg_idx, (text, rate, pitch, volume, pause_sec) in enumerate(info["segments"]):
            seg_file = os.path.join(TEMP_DIR, f"{preset_id}_seg_{seg_idx}.mp3")
            await generate_segment(text, info["voice"], rate, pitch, volume, seg_file)
            
            y_seg, sr = librosa.load(seg_file, sr=sr_target)
            y_trimmed, _ = librosa.effects.trim(y_seg, top_db=30)
            combined_audio.append(y_trimmed)

            pause_samples = int(pause_sec * sr_target)
            silence = np.zeros(pause_samples, dtype=np.float32)
            combined_audio.append(silence)

        full_y = np.concatenate(combined_audio)
        raw_concat_path = os.path.join(TEMP_DIR, f"{preset_id}_concat.wav")
        sf.write(raw_concat_path, full_y, sr_target)

        final_mp3 = os.path.join(OUTPUT_DIR, f"{preset_id}.mp3")
        cmd = [
            "ffmpeg", "-y", "-i", raw_concat_path,
            "-af", info["af_filter"],
            "-ar", "24000", "-b:a", "192k",
            final_mp3
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        y_final, sr = librosa.load(final_mp3, sr=24000)
        duration = len(y_final) / sr
        f0, voiced_flag, voiced_probs = librosa.pyin(y_final, fmin=80, fmax=400, sr=sr)
        valid_f0 = f0[~np.isnan(f0)]
        mean_f0 = float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0.0

        p_info = info.copy()
        p_info["file"] = f"{preset_id}.mp3"
        p_info["duration"] = f"{duration:.2f}s"
        p_info["f0"] = f"{mean_f0:.1f} Hz"
        generated_data.append(p_info)
        print(f"Done: {final_mp3} ({duration:.2f}s, {mean_f0:.1f}Hz)")

    create_html_player(generated_data)

def create_html_player(items):
    cards_html = ""
    for idx, it in enumerate(items, 1):
        cards_html += f"""
        <div class="card" style="border: 2px solid {it['border']}; background: {it['bg']};">
            <div class="card-header">
                <div class="title-row">
                    <span class="badge" style="background: {it['badge_bg']};">{it['badge']}</span>
                    <h3>{it['name']}</h3>
                </div>
                <div class="metrics">
                    <span>⏱️ 재생 길이: <strong>{it['duration']}</strong></span>
                    <span>🎵 실측 F0 피치: <strong>{it['f0']}</strong></span>
                </div>
            </div>
            <p class="desc">{it['desc']}</p>
            <div class="player-wrapper">
                <audio controls preload="auto" src="storyteller_masters/{it['file']}"></audio>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 명품 여성 스토리텔러 능청 & 무게감 완급 조절 마스터</title>
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
        .benchmark-box {{
            background: #111827;
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 35px;
        }}
        .benchmark-box h4 {{
            color: #60a5fa;
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
            margin-bottom: 18px;
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
            <h1>🎭 [송림야담] 명품 여성 스토리텔러 능청 & 무게감 완급 조절 마스터</h1>
            <p>이야기꾼의 능청스러운 운 띄우기 + 급변하는 비극 긴장감 + 묵직한 흉성 말끝 슬로우다운(-34%)</p>
        </div>

        <div class="benchmark-box">
            <h4>💡 '능청스러움과 무게감 있는 완급 조절'의 4대 핵심 연출 기법</h4>
            <ul>
                <li><strong>1. 능청스러운 뜸 들이기</strong>: <em>"옛날 옛적..."</em> (0.9초 쉼) 뒤에 <em>"한양 북촌 명문가의..."</em>로 자연스럽게 청중을 끌어당김</li>
                <li><strong>2. 급격한 감정/속도 전환 (조여들기)</strong>: <em>"하루아침에, (0.4초 쉼) 억울한 역모의 누명을 쓰고..."</em>에서 속도와 볼륨을 순간적으로 변화시켜 긴장감 폭발</li>
                <li><strong>3. 묵직하게 가라앉는 어미 감속 (-32% ~ -36%)</strong>: <em>"내쫓기고 말았더랬지요..."</em>의 어미를 서글프고 묵직하게 늘여 전래 설화의 한(恨)을 완성</li>
                <li><strong>4. 1.25초 ~ 1.30초 극적 침묵 (Dramatic Silence)</strong>: 서사가 전환되는 지점에서 성우의 호흡을 깊게 주어 다음 대목의 몰입감 극대화</li>
            </ul>
        </div>

        {cards_html}

        <div class="footer">
            <p>※ 100% 무료 로컬 오픈소스/Edge 파이프라인으로 무제한 생성 가능합니다.</p>
        </div>
    </div>
</body>
</html>
"""
    player_path = "output/storyteller_player.html"
    with open(player_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Player updated: {player_path}")

if __name__ == "__main__":
    asyncio.run(build_directed_masters())
