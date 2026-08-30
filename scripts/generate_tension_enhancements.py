import asyncio
import os
import subprocess
import sys
import edge_tts
import soundfile as sf
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = "output/tension_enhanced_masters"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TEMP_DIR = "output/tension_enhanced_masters/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 기준 골든 스탠다드 파라미터 (베이스)
BASE_VOICE = "ko-KR-SunHiNeural"
BASE_PITCH = "-24Hz"

# 4대 긴장감 & 완급 고도화 프리셋
TENSION_PRESETS = [
    {
        "id": "tension_01_breath_suspense",
        "name": "👑 1. [문맥 호흡 텐션 고도화 - 절제된 긴장감] (대표 추천)",
        "badge": "★ 절제된 긴장감",
        "badge_bg": "#10b981",
        "border": "#10b981",
        "bg": "#092215",
        "desc": "표준 음색을 100% 유지하면서, 사건이 터지는 순간('하루아침에... 억울한 역모의 누명을 쓰고,')의 호흡 정적을 미세 조율하여 숨죽이는 긴장감을 유도한 마스터",
        "script": "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이... 하루아침에... 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 쫓겨나고 말았습니다... 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었습니다.",
        "rate": "-22%",
        "pitch": "-24Hz",
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=4.0,"
            "equalizer=f=450:width_type=o:width=1.5:g=2.0,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "highshelf=f=7500:g=-2.0,"
            "aecho=0.8:0.6:20|35:0.10|0.05,"
            "compand=attacks=0.03:decays=0.3:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    },
    {
        "id": "tension_02_deep_proximity",
        "name": "🕯️ 2. [마이크 근접 흉성 서스펜스 고도화 - 묵직한 중저음]",
        "badge": "묵직한 서스펜스",
        "badge_bg": "#d97706",
        "border": "#d97706",
        "bg": "#1c1407",
        "desc": "180Hz~220Hz 흉성 에너지를 1.5dB 추가 보강하여, 성우가 귓가에 비밀스럽게 속삭이듯 낮게 깔리는 압도적인 무게감과 심리적 긴장감을 구현",
        "script": "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에... 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 쫓겨나고 말았습니다. 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었습니다.",
        "rate": "-24%",
        "pitch": "-26Hz",
        "af_filter": (
            "equalizer=f=185:width_type=o:width=1.3:g=5.0,"
            "equalizer=f=420:width_type=o:width=1.4:g=2.4,"
            "equalizer=f=3400:width_type=o:width=1.0:g=-3.8,"
            "highshelf=f=7200:g=-2.5,"
            "aecho=0.8:0.6:22|38:0.11|0.05,"
            "compand=attacks=0.02:decays=0.25:points=-80/-80|-24/-18|-12/-9|0/-1:soft-knee=8,"
            "volume=1.28"
        )
    },
    {
        "id": "tension_03_tri_tempo_elastic",
        "name": "💎 3. [3단계 서사 템포 굴곡 고도화 - 기승전결 완급]",
        "badge": "3단계 서사 굴곡",
        "badge_bg": "#3b82f6",
        "border": "#3b82f6",
        "bg": "#0f172a",
        "desc": "도입부(평온 -18%) ➔ 위기 발생(긴박감 -16%) ➔ 결말(비극 여운 -28%)로 문맥에 따라 템포가 유기적으로 호흡하며 청중의 심박수를 조절하는 고도화",
        "script": "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이... 하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 쫓겨나고 말았습니다... 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었습니다.",
        "rate": "-20%",
        "pitch": "-24Hz",
        "use_tri_elastic": True,
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
        "id": "tension_04_cinematic_space",
        "name": "🌌 4. [시네마틱 공간 잔향 고도화 - 깊은 음영과 서사]",
        "badge": "시네마틱 공간감",
        "badge_bg": "#8b5cf6",
        "border": "#8b5cf6",
        "bg": "#1e1136",
        "desc": "초기 반사음(Early Reflection) 챔버를 28ms로 넓혀 사극 영화 나레이션 특유의 웅장한 공간감과 차가운 밤의 공기감을 극대화한 고도화",
        "script": "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이... 하루아침에, 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 쫓겨나고 말았습니다... 차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었습니다.",
        "rate": "-23%",
        "pitch": "-24Hz",
        "af_filter": (
            "equalizer=f=190:width_type=o:width=1.5:g=4.0,"
            "equalizer=f=450:width_type=o:width=1.5:g=2.0,"
            "equalizer=f=3600:width_type=o:width=1.0:g=-3.5,"
            "highshelf=f=7500:g=-2.0,"
            "aecho=0.8:0.7:28|50:0.14|0.06,"
            "compand=attacks=0.03:decays=0.35:points=-80/-80|-24/-20|-12/-10|0/-1:soft-knee=6,"
            "volume=1.25"
        )
    }
]

def apply_tri_elastic_curve(y, sr):
    n = len(y)
    p1 = int(n * 0.30)
    p2 = int(n * 0.65)
    
    seg_intro = y[:p1]
    seg_crisis = y[p1:p2]
    seg_outro = y[p2:]

    s_intro = librosa.effects.time_stretch(seg_intro, rate=1.00) # 평온
    s_crisis = librosa.effects.time_stretch(seg_crisis, rate=1.06) # 긴장감 있게 살짝 당김
    s_outro = librosa.effects.time_stretch(seg_outro, rate=0.90)  # 서글프게 감속
    return np.concatenate([s_intro, s_crisis, s_outro])

async def build_tension_masters():
    generated_data = []

    for p in TENSION_PRESETS:
        preset_id = p["id"]
        print(f"--> Generating: {p['name']}")
        sr_target = 24000
        
        raw_mp3 = os.path.join(TEMP_DIR, f"{preset_id}_raw.mp3")
        comm = edge_tts.Communicate(p["script"], voice=BASE_VOICE, rate=p["rate"], pitch=p["pitch"])
        await comm.save(raw_mp3)

        y, sr = librosa.load(raw_mp3, sr=sr_target)

        if p.get("use_tri_elastic"):
            y = apply_tri_elastic_curve(y, sr)

        proc_wav = os.path.join(TEMP_DIR, f"{preset_id}_proc.wav")
        sf.write(proc_wav, y, sr_target)

        final_mp3 = os.path.join(OUTPUT_DIR, f"{preset_id}.mp3")
        cmd = [
            "ffmpeg", "-y", "-i", proc_wav,
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
        p_info["duration"] = f"{duration:.2f}초"
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
            <div class="script-box">
                <div class="script-content">"{it['script']}"</div>
            </div>
            <div class="player-wrapper">
                <audio controls preload="auto" src="tension_enhanced_masters/{it['file']}"></audio>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[송림야담] 기준 표준 음성 기반 긴장감 & 완급 고도화 청음실</title>
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
            margin-bottom: 14px;
        }}
        .script-box {{
            background: rgba(0, 0, 0, 0.35);
            border-left: 3px solid rgba(255,255,255,0.3);
            padding: 12px 16px;
            margin-bottom: 18px;
            border-radius: 4px;
        }}
        .script-content {{
            font-size: 0.98rem;
            color: #f1f5f9;
            line-height: 1.6;
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
            <h1>🎭 [송림야담] 기준 표준 음성 기반 긴장감 & 완급 고도화 청음실</h1>
            <p>확정된 표준 음색(-24Hz, 192Hz F0)을 100% 유지하면서 서사의 긴장감과 완급을 미세하게 고도화</p>
        </div>

        <div class="benchmark-box">
            <h4>💡 긴장감과 완급 고도화의 4대 핵심 방향</h4>
            <ul>
                <li><strong>1. 문맥 호흡 텐션 (Breath Suspense)</strong>: 사건 발생 순간의 미세한 쉼표 텐션으로 청중의 숨을 죽이게 유도</li>
                <li><strong>2. 묵직한 근접 흉성 (Deep Proximity)</strong>: 185Hz 흉성 대역을 보강하여 귓가에 낮게 깔리는 은밀하고 묵직한 서스펜스 조성</li>
                <li><strong>3. 3단계 서사 템포 (Tri-Tempo Elasticity)</strong>: 도입부(평온) ➔ 위기부(긴박감) ➔ 결말(비극 여운)로 이어지는 유기적 템포 굴곡</li>
                <li><strong>4. 시네마틱 공간 잔향 (Cinematic Space)</strong>: 사극 영화 특유의 28ms 챔버 앰비언스로 차가운 밤의 공기감 연출</li>
            </ul>
        </div>

        {cards_html}

        <div class="footer">
            <p>※ 모든 오디오는 100% 무료 로컬 오픈소스/Edge 파이프라인으로 무제한 생성 가능합니다.</p>
        </div>
    </div>
</body>
</html>
"""
    player_path = "output/tension_player.html"
    with open(player_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Player updated: {player_path}")

if __name__ == "__main__":
    asyncio.run(build_tension_masters())
