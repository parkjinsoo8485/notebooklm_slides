import asyncio
import subprocess
import os
import sys
import edge_tts
import soundfile as sf
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = "output/stream_tempo_masters"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TEMP_DIR = "output/stream_tempo_masters/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 4번 [단일 스트림 일체형]을 완벽한 베이스로 삼고,
# 자연스러운 연속 발화의 결을 100% 살린 채 완급 조절(템포 굴곡 & 구두점 호흡)을 적용한 4대 마스터
STREAM_PRESETS = [
    {
        "id": "stream_tempo_master_optimal",
        "name": "👑 1. [완벽 일체형 + 자연스러운 템포 굴곡 마스터] (초강력 추천)",
        "badge": "★ 일체형 + 완벽 완급",
        "badge_bg": "#10b981",
        "border": "#10b981",
        "bg": "#092215",
        "desc": "4번 단일 스트림의 매끄러운 소리 결을 100% 유지하면서, 문맥 부호(...) 최적화로 '도입부의 아련함 → 역모의 긴장감 → 말끝(~말았더랬지요)의 애절한 감속'을 완벽히 구현한 최고 완성본",
        "text": "옛날 옛적... 한양 북촌 명문가의, 어질고 고왔던 윤씨 마님이... 하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로... 내쫓기고 말았더랬지요... 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의, 비극이었답니다.",
        "rate": "-24%",
        "pitch": "-24Hz",
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
            "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "highshelf=f=7500:g=-2.0,"
            "aecho=0.8:0.6:20|35:0.10|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    },
    {
        "id": "stream_tempo_master_elastic_dsp",
        "name": "💎 2. [완벽 일체형 + 다이내믹 탄성 완급 (Elastic Time)]",
        "badge": "다이내믹 탄성 완급",
        "badge_bg": "#3b82f6",
        "border": "#3b82f6",
        "bg": "#0f172a",
        "desc": "단일 스트림 연속 음원에 가변 타임 스트레칭(WSOLA DSP)을 적용하여, 도입부는 부드럽게 흐르고 위기부와 결말부의 여운을 점진적으로 -30%까지 슬로우다운시킨 입체적 완급",
        "text": "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었답니다.",
        "rate": "-20%",
        "pitch": "-24Hz",
        "use_elastic_stretch": True,
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
            "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "highshelf=f=7500:g=-2.0,"
            "aecho=0.8:0.6:20|35:0.10|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    },
    {
        "id": "stream_tempo_master_deep_breath",
        "name": "📜 3. [완벽 일체형 + 여운 있는 긴 호흡 마스터]",
        "badge": "깊은 여운 호흡",
        "badge_bg": "#d97706",
        "border": "#d97706",
        "bg": "#1c1407",
        "desc": "전체 재생 템포를 -27%로 진중하게 설정하고, 구절 간 쉼표 호흡을 깊게 주어 비극 야담 특유의 무게감과 처연함을 한층 강화한 톤",
        "text": "옛날 옛적... 한양 북촌 명문가의, 어질고 고왔던 윤씨 마님이... 하루아침에, 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로... 내쫓기고 말았더랬지요... 차가운 달빛조차, 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었답니다...",
        "rate": "-27%",
        "pitch": "-24Hz",
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
            "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "highshelf=f=7500:g=-2.0,"
            "aecho=0.8:0.6:20|35:0.10|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    },
    {
        "id": "stream_tempo_master_smooth_rhythm",
        "name": "🌌 4. [완벽 일체형 + 편안한 리듬 완급 마스터]",
        "badge": "편안한 리듬감",
        "badge_bg": "#8b5cf6",
        "border": "#8b5cf6",
        "bg": "#1e1136",
        "desc": "끊김 없이 물 흐르듯 유려하게 흘러가면서도 귓가에 쏙쏙 박히는 정통 방송 성우의 리드미컬한 완급 조절 톤",
        "text": "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이... 하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다.",
        "rate": "-22%",
        "pitch": "-24Hz",
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=3.8,"
            "equalizer=f=450:width_type=o:width=1.5:g=1.8,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "highshelf=f=7500:g=-2.0,"
            "aecho=0.8:0.6:20|35:0.10|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    }
]

def apply_elastic_time_stretch(y, sr):
    # Dynamic time curve: start 1.0 -> middle 0.95 -> ending 0.85 (slowing down smoothly)
    # librosa time_stretch works with a rate float. We segment dynamically:
    n = len(y)
    seg1 = y[:int(n*0.35)] # opening
    seg2 = y[int(n*0.35):int(n*0.70)] # crisis
    seg3 = y[int(n*0.70):] # tragedy climax & ending

    s1 = librosa.effects.time_stretch(seg1, rate=1.03) # slightly brisk opening
    s2 = librosa.effects.time_stretch(seg2, rate=0.96) # weighted middle
    s3 = librosa.effects.time_stretch(seg3, rate=0.88) # slowed down poignant ending
    return np.concatenate([s1, s2, s3])

async def build_stream_masters():
    generated_data = []

    for p in STREAM_PRESETS:
        preset_id = p["id"]
        print(f"--> Generating: {p['name']}")
        sr_target = 24000
        
        raw_mp3 = os.path.join(TEMP_DIR, f"{preset_id}_raw.mp3")
        comm = edge_tts.Communicate(p["text"], voice="ko-KR-SunHiNeural", rate=p["rate"], pitch=p["pitch"])
        await comm.save(raw_mp3)

        y, sr = librosa.load(raw_mp3, sr=sr_target)

        if p.get("use_elastic_stretch"):
            y = apply_elastic_time_stretch(y, sr)

        processed_wav = os.path.join(TEMP_DIR, f"{preset_id}_proc.wav")
        sf.write(processed_wav, y, sr_target)

        # Apply Studio Mastering
        final_mp3 = os.path.join(OUTPUT_DIR, f"{preset_id}.mp3")
        cmd = [
            "ffmpeg", "-y", "-i", processed_wav,
            "-af", p["af_filter"],
            "-ar", "24000", "-b:a", "192k",
            final_mp3
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        y_final, sr = librosa.load(final_mp3, sr=24000)
        duration = len(y_final) / sr
        f0, voiced_flag, voiced_probs = librosa.pyin(y_final, fmin=80, fmax=400, sr=sr)
        valid_f0 = f0[~np.isnan(f0)]
        mean_f0 = float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0.0

        p_info = p.copy()
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
                <audio controls preload="auto" src="stream_tempo_masters/{it['file']}"></audio>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 4번 일체형 연속 발화 베이스 정밀 완급 조절 청음실</title>
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
            <h1>👑 [송림야담] 4번 일체형 연속 발화 베이스 정밀 완급 조절 청음실</h1>
            <p>4번 단일 스트림의 매끄러운 일체감을 100% 유지하면서 스토리텔러 완급(호흡/감속)만 정밀 조율</p>
        </div>

        <div class="benchmark-box">
            <h4>💡 4번 일체형 연속 발화 기반 완급 조절의 핵심</h4>
            <ul>
                <li><strong>완벽한 일체감 100% 보존</strong>: 문장을 분할하지 않고 단일 스트림으로 렌더링하여 성우의 호흡과 소리 결이 끊김 없이 매끄럽게 연결됩니다.</li>
                <li><strong>문맥 구두점(...) 호흡 연출</strong>: <em>"옛날 옛적... 한양 북촌 명문가의, 어질고 고왔던 윤씨 마님이..."</em> 등 자연스러운 쉼표를 통해 성우가 자체적으로 리듬을 타며 완급을 주도록 연출했습니다.</li>
                <li><strong>후반부 서글픈 여운 감속</strong>: 역모로 내쫓기고 비극으로 이어지는 후반부의 말끝을 더욱 부드럽고 여운 있게 마무리합니다.</li>
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
    player_path = "output/stream_tempo_player.html"
    with open(player_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Player updated: {player_path}")

if __name__ == "__main__":
    asyncio.run(build_stream_masters())
