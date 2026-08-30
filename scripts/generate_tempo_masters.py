import asyncio
import subprocess
import os
import sys
import edge_tts
import soundfile as sf
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = "output/tempo_songrim_masters"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TEMP_DIR = "output/tempo_songrim_masters/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 1번 완벽 정합 마스터(SunHi, -24Hz)의 음색과 음향을 100% 그대로 유지하면서
# 문장을 쪼개지 않고 자연스러운 "속도 완급 & 호흡 쉼표"만 매끄럽게 조율한 4대 프리셋
TEMPO_PRESETS = [
    {
        "id": "tempo_master_natural_pacing",
        "name": "👑 1. [송림야담 자연스러운 완급 마스터] (초강력 추천)",
        "badge": "★ 원음 음색 + 자연스러운 완급",
        "badge_bg": "#10b981",
        "border": "#10b981",
        "bg": "#092215",
        "desc": "원음의 묵직한 흉성 음색(-24Hz)을 100% 유지하면서, 문맥의 호흡(0.6초~0.8초)과 말끝 여운 감속만 매끄럽게 살린 가장 자연스러운 완성본",
        "sentences": [
            ("옛날 옛적...", "-18%", "-24Hz", 0.65),
            ("한양 북촌 명문가의 어질고 고왔던 윤씨 마님이,", "-22%", "-24Hz", 0.50),
            ("하루아침에 억울한 역모의 누명을 쓰고...", "-24%", "-24Hz", 0.70),
            ("첩첩산중 깊은 산골로 내쫓기고 말았더랬지요...", "-28%", "-24Hz", 0.85),
            ("차가운 달빛조차 서럽게 얼어붙던...", "-22%", "-24Hz", 0.60),
            ("어느 쓸쓸한 늦가을 밤의 비극이었답니다.", "-28%", "-24Hz", 0.70),
        ],
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
        "id": "tempo_master_dynamic_flow",
        "name": "💎 2. [서사적 기승전결 완급 마스터]",
        "badge": "서사적 완급 조절",
        "badge_bg": "#3b82f6",
        "border": "#3b82f6",
        "bg": "#0f172a",
        "desc": "도입부는 알맞은 속도(-15%)로 편안하게 시작하고, 위기부와 결말부(-28%~-30%)는 차분하게 가라앉히는 자연스러운 스토리텔링 속도 굴곡",
        "sentences": [
            ("옛날 옛적...", "-15%", "-24Hz", 0.60),
            ("한양 북촌 명문가의 어질고 고왔던 윤씨 마님이,", "-20%", "-24Hz", 0.45),
            ("하루아침에 억울한 역모의 누명을 쓰고...", "-25%", "-24Hz", 0.65),
            ("첩첩산중 깊은 산골로 내쫓기고 말았더랬지요...", "-30%", "-24Hz", 0.80),
            ("차가운 달빛조차 서럽게 얼어붙던...", "-20%", "-24Hz", 0.55),
            ("어느 쓸쓸한 늦가을 밤의 비극이었답니다.", "-30%", "-24Hz", 0.70),
        ],
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
        "id": "tempo_master_calm_steady",
        "name": "📜 3. [차분하고 일정한 정통 낭독 완급]",
        "badge": "안정된 정통 낭독",
        "badge_bg": "#d97706",
        "border": "#d97706",
        "bg": "#1c1407",
        "desc": "속도 편차를 줄여(-23%~-26%) 전체적으로 매우 안정되고 고즈넉하게 흘러가는 정통 방송 성우 낭독 스타일",
        "sentences": [
            ("옛날 옛적...", "-23%", "-24Hz", 0.55),
            ("한양 북촌 명문가의 어질고 고왔던 윤씨 마님이,", "-24%", "-24Hz", 0.45),
            ("하루아침에 억울한 역모의 누명을 쓰고...", "-25%", "-24Hz", 0.60),
            ("첩첩산중 깊은 산골로 내쫓기고 말았더랬지요...", "-27%", "-24Hz", 0.75),
            ("차가운 달빛조차 서럽게 얼어붙던...", "-24%", "-24Hz", 0.50),
            ("어느 쓸쓸한 늦가을 밤의 비극이었답니다.", "-27%", "-24Hz", 0.65),
        ],
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
        "id": "tempo_master_single_flow",
        "name": "🌌 4. [원음 1:1 완벽 일체형 연속 발화 (단일 스트림)]",
        "badge": "완벽 일체형",
        "badge_bg": "#8b5cf6",
        "border": "#8b5cf6",
        "bg": "#1e1136",
        "desc": "문장을 분할하지 않고 원문 전체를 단일 스트림(-25%, -24Hz)으로 생성하여 어떠한 끊김도 없는 100% 매끄러운 오리지널 톤",
        "raw_text": "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었답니다",
        "rate": "-25%",
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

async def build_tempo_masters():
    generated_data = []

    for p in TEMPO_PRESETS:
        preset_id = p["id"]
        print(f"--> Generating: {p['name']}")
        sr_target = 24000
        raw_wav = os.path.join(TEMP_DIR, f"{preset_id}_raw.wav")

        if "sentences" in p:
            combined_audio = []
            for s_idx, (text, rate, pitch, pause_sec) in enumerate(p["sentences"]):
                seg_file = os.path.join(TEMP_DIR, f"{preset_id}_s_{s_idx}.mp3")
                comm = edge_tts.Communicate(text, voice="ko-KR-SunHiNeural", rate=rate, pitch=pitch)
                await comm.save(seg_file)

                y_seg, sr = librosa.load(seg_file, sr=sr_target)
                y_trimmed, _ = librosa.effects.trim(y_seg, top_db=32)
                combined_audio.append(y_trimmed)

                pause_samples = int(pause_sec * sr_target)
                silence = np.zeros(pause_samples, dtype=np.float32)
                combined_audio.append(silence)

            full_y = np.concatenate(combined_audio)
            sf.write(raw_wav, full_y, sr_target)
        else:
            comm = edge_tts.Communicate(p["raw_text"], voice="ko-KR-SunHiNeural", rate=p["rate"], pitch=p["pitch"])
            temp_mp3 = os.path.join(TEMP_DIR, f"{preset_id}_single.mp3")
            await comm.save(temp_mp3)
            raw_wav = temp_mp3

        # Apply Studio Mastering
        final_mp3 = os.path.join(OUTPUT_DIR, f"{preset_id}.mp3")
        cmd = [
            "ffmpeg", "-y", "-i", raw_wav,
            "-af", p["af_filter"],
            "-ar", "24000", "-b:a", "192k",
            final_mp3
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        # Audio Analysis
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
                <audio controls preload="auto" src="tempo_songrim_masters/{it['file']}"></audio>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 원음 베이스 자연스러운 속도 완급 조절 청음실</title>
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
            <h1>👑 [송림야담] 원음 베이스 자연스러운 속도 완급 조절 청음실</h1>
            <p>이전의 완벽 정합 음색(-24Hz, 190.3Hz 피치)을 100% 유지하면서 매끄러운 호흡과 속도 완급만 조율</p>
        </div>

        <div class="benchmark-box">
            <h4>💡 이번 조정의 핵심 (어색함 완전 제거)</h4>
            <ul>
                <li><strong>원음 베이스 음색 100% 복원</strong>: 이전 1번 마스터의 깊은 흉성 피치(-24Hz)와 따뜻한 챔버 질감을 완벽하게 유지합니다.</li>
                <li><strong>단어 분절 없는 매끄러운 발음</strong>: 인위적인 피치 꺾임을 없애고 대본 원문 그대로 부드럽게 이어집니다.</li>
                <li><strong>자연스러운 템포 굴곡 (속도 완급만 조율)</strong>: 문장 시작의 알맞은 속도 → 위기부/결말부의 차분한 감속(-28%) 및 적절한 쉼표(0.5s~0.8s)만 섬세하게 반영했습니다.</li>
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
    player_path = "output/tempo_player.html"
    with open(player_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Player updated: {player_path}")

if __name__ == "__main__":
    asyncio.run(build_tempo_masters())
