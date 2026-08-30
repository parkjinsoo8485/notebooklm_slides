"""
analyze_and_clone_female_voice.py
══════════════════════════════════════════════════════════════════
송림야담 (https://youtu.be/jKatQ6Gd__s) 여성 나레이터 완전 복원

원본 분석 결과:
  - F0 median: 193.7 Hz  (Alto / Mezzo-soprano 여성)
  - F0 range:  130.8 ~ 258.6 Hz
  - Spectral centroid: 1632.4 Hz  (따뜻하고 차분한 중저음)
  - Spectral bandwidth: 1463.2 Hz
  - ZCR: 0.0492 (매우 부드러운 발음)
  - Duration: 15.32s / 48000 Hz stereo

전략:
  1. 원본 F0 기반 Edge-TTS pitch 파라미터 정밀 계산
  2. 7가지 파라미터 조합 생성
  3. FFmpeg 다단계 EQ + Compressor 체인으로 음색 정합
  4. HTML A/B 비교 플레이어 생성
══════════════════════════════════════════════════════════════════
"""

import asyncio
import subprocess
import sys
from pathlib import Path
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR    = WORKSPACE_DIR / "output"
SAMPLES_DIR   = OUTPUT_DIR / "voice_samples" / "songrim_female_v3"
ORIG_MP3      = OUTPUT_DIR / "voice_samples" / "songrim_100pct_replica" / "01_youtube_actual_original.mp3"
VOCALS_WAV    = OUTPUT_DIR / "voice_samples" / "songrim_100pct_replica" / "01_vocals_only.wav"

SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# 원본과 동일한 테스트 문장
EXACT_YT_SENTENCE = (
    "빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 "
    "누군가 찾아와 그리 속삭였습니다. "
    "새벽 장터길 쫓기던 여인을 달구지 안에 숨겨 준 "
    "바로 다음 날이었지요."
)

# ── 원본 분석 결과 (이미 실행 완료) ──
ORIGINAL_ANALYSIS = {
    "f0_median":          193.7,
    "f0_mean":            191.7,
    "f0_min":             130.8,
    "f0_max":             258.6,
    "f0_std":             25.7,
    "spectral_centroid":  1632.4,
    "spectral_bandwidth": 1463.2,
    "zcr":                0.0492,
}

# ══════════════════════════════════════════════════════════════
# FFmpeg EQ 필터 프로파일
# Spectral centroid 1632 Hz → 중저음 따뜻한 여성 음색
# ══════════════════════════════════════════════════════════════
EQ_PROFILES = {
    "warm_narrator": (
        "equalizer=f=180:width_type=o:width=1.0:g=2.0,"
        "equalizer=f=500:width_type=o:width=1.2:g=1.5,"
        "equalizer=f=2500:width_type=o:width=1.0:g=-1.5,"
        "equalizer=f=5000:width_type=o:width=1.2:g=-3.0,"
        "equalizer=f=8000:width_type=o:width=1.0:g=-5.0,"
        "acompressor=threshold=0.2:ratio=3:attack=10:release=150:makeup=1.2,"
        "volume=1.15"
    ),
    "soft_warm": (
        "equalizer=f=150:width_type=o:width=1.1:g=3.0,"
        "equalizer=f=400:width_type=o:width=1.0:g=2.0,"
        "equalizer=f=3000:width_type=o:width=1.2:g=-2.0,"
        "equalizer=f=6000:width_type=o:width=1.0:g=-4.0,"
        "equalizer=f=10000:width_type=o:width=1.0:g=-6.0,"
        "acompressor=threshold=0.18:ratio=2.5:attack=12:release=180:makeup=1.3,"
        "volume=1.2"
    ),
    "broadcast_female": (
        "equalizer=f=100:width_type=o:width=0.8:g=-1.0,"
        "equalizer=f=250:width_type=o:width=1.0:g=1.5,"
        "equalizer=f=800:width_type=o:width=1.2:g=2.0,"
        "equalizer=f=3500:width_type=o:width=1.0:g=-2.5,"
        "equalizer=f=7000:width_type=o:width=1.0:g=-4.5,"
        "acompressor=threshold=0.15:ratio=3:attack=8:release=120:makeup=1.25,"
        "volume=1.18"
    ),
    "yadam_story": (
        "equalizer=f=160:width_type=o:width=1.2:g=2.5,"
        "equalizer=f=450:width_type=o:width=1.1:g=2.0,"
        "equalizer=f=900:width_type=o:width=1.0:g=1.0,"
        "equalizer=f=2800:width_type=o:width=1.2:g=-2.0,"
        "equalizer=f=5500:width_type=o:width=1.0:g=-3.5,"
        "equalizer=f=9000:width_type=o:width=1.0:g=-5.5,"
        "acompressor=threshold=0.12:ratio=2.8:attack=15:release=200:makeup=1.3,"
        "volume=1.2"
    ),
    "no_eq": "volume=1.0",
}

# ══════════════════════════════════════════════════════════════
# 파라미터 매트릭스
# 원본 F0: 193.7 Hz / SunHiNeural 기본 추정 F0: ~230 Hz
# 필요 보정: -35 ~ -40 Hz
# ══════════════════════════════════════════════════════════════
PARAM_MATRIX = [
    # (이름,           음성,                  rate,    pitch,   eq_profile,         설명)
    ("v1_warm_-35hz",  "ko-KR-SunHiNeural",  "-8%",  "-35Hz", "warm_narrator",    "따뜻한 -35Hz 기준"),
    ("v2_soft_-40hz",  "ko-KR-SunHiNeural",  "-10%", "-40Hz", "soft_warm",        "더 부드럽고 낮음 -40Hz"),
    ("v3_yadam_-38hz", "ko-KR-SunHiNeural",  "-7%",  "-38Hz", "yadam_story",      "야담 감성 -38Hz"),
    ("v4_bcast_-32hz", "ko-KR-SunHiNeural",  "-6%",  "-32Hz", "broadcast_female", "방송용 깔끔 -32Hz"),
    ("v5_deep_-45hz",  "ko-KR-SunHiNeural",  "-12%", "-45Hz", "soft_warm",        "가장 낮고 느림 -45Hz"),
    ("v6_nat_-30hz",   "ko-KR-SunHiNeural",  "-5%",  "-30Hz", "warm_narrator",    "자연스러운 속도 -30Hz"),
    ("v7_noeq_-38hz",  "ko-KR-SunHiNeural",  "-7%",  "-38Hz", "no_eq",            "EQ 없음 (순수 피치만)"),
]


async def synthesize_version(name, voice, rate, pitch, eq_profile, desc, text):
    out_final = SAMPLES_DIR / f"{name}.mp3"
    tmp_raw   = SAMPLES_DIR / f"{name}_raw.mp3"

    print(f"  [{name}] {desc}")
    print(f"    voice={voice}  rate={rate}  pitch={pitch}  eq={eq_profile}")

    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await comm.save(str(tmp_raw))

    eq_filter = EQ_PROFILES.get(eq_profile, EQ_PROFILES["warm_narrator"])
    cmd = [
        "ffmpeg", "-y", "-i", str(tmp_raw),
        "-af", eq_filter,
        "-b:a", "192k",
        str(out_final)
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        tmp_raw.unlink(missing_ok=True)
        size_kb = out_final.stat().st_size // 1024
        print(f"    OK -> {out_final.name}  ({size_kb} KB)")
    else:
        print(f"    ERROR: FFmpeg failed")
        out_final = tmp_raw

    return out_final


def create_html_player(versions):
    html_path = SAMPLES_DIR / "compare_female_v3.html"

    cards_html = ""
    colors = ["#10b981","#3b82f6","#f59e0b","#ec4899","#8b5cf6","#06b6d4","#f97316"]

    for i, (name, voice, rate, pitch, eq_profile, desc, out_path) in enumerate(versions):
        c = colors[i % len(colors)]
        cards_html += f"""
        <div class="clone-card" style="border-color:{c}; box-shadow:0 6px 20px -4px {c}33;">
            <div class="card-header">
                <span class="badge" style="background:{c};">{i+1}</span>
                <div class="card-meta">
                    <div class="card-title" style="color:{c};">[v{i+1}] {desc}</div>
                    <div class="card-params">rate: {rate} · pitch: {pitch} · EQ: {eq_profile}</div>
                </div>
            </div>
            <audio controls preload="none" src="{out_path.name}"></audio>
        </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>송림야담 여성 나레이터 복원 비교 v3</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#070c15;--card:#0e1628;--border:#1e2d45;--text:#e8edf5;--muted:#5a7090;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;padding:40px 20px;}}
.container{{max-width:880px;margin:0 auto;}}
h1{{font-family:'Noto Serif KR',serif;font-size:28px;font-weight:700;
    background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    text-align:center;margin-bottom:8px;}}
.subtitle{{color:var(--muted);font-size:13px;text-align:center;margin-bottom:32px;line-height:1.7;}}

/* 분석 박스 */
.analysis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:28px;}}
@media(max-width:600px){{.analysis{{grid-template-columns:repeat(2,1fr);}}}}
.metric{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;text-align:center;}}
.metric-val{{font-size:22px;font-weight:700;color:#60a5fa;}}
.metric-lbl{{font-size:10px;color:var(--muted);margin-top:3px;text-transform:uppercase;letter-spacing:.5px;}}
.metric-sub{{font-size:10px;color:#a78bfa;margin-top:2px;}}

/* 원본 */
.original{{background:linear-gradient(135deg,rgba(239,68,68,.12),var(--card));
           border:2px solid #ef4444;border-radius:16px;padding:22px;margin-bottom:24px;
           box-shadow:0 8px 25px -5px rgba(239,68,68,.25);}}
.section-title{{font-size:15px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px;}}
.script{{background:rgba(0,0,0,.4);border-left:3px solid #ef4444;
         padding:14px 18px;border-radius:0 8px 8px 0;
         font-family:'Noto Serif KR',serif;font-size:14px;line-height:1.9;
         color:#f1f5f9;margin-bottom:14px;}}

/* 클론 카드 */
.section-head{{font-size:16px;font-weight:700;color:#a78bfa;margin-bottom:14px;}}
.clone-card{{background:var(--card);border:1.5px solid var(--border);border-radius:14px;
             padding:18px;margin-bottom:12px;transition:transform .15s;}}
.clone-card:hover{{transform:translateY(-2px);}}
.card-header{{display:flex;align-items:center;gap:12px;margin-bottom:12px;}}
.badge{{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;
        justify-content:center;font-weight:800;font-size:13px;color:#fff;flex-shrink:0;}}
.card-meta{{flex:1;}}
.card-title{{font-weight:700;font-size:13.5px;margin-bottom:3px;}}
.card-params{{font-size:11px;color:var(--muted);font-family:monospace;}}
audio{{width:100%;height:38px;border-radius:8px;}}

/* 가이드 */
.guide{{background:var(--card);border:1px solid var(--border);border-radius:14px;
        padding:20px;margin-top:24px;}}
.guide h3{{font-size:13px;font-weight:700;color:#fbbf24;margin-bottom:10px;}}
.guide li{{font-size:13px;color:var(--muted);line-height:2;list-style:none;}}
.guide li::before{{content:"→ ";color:#60a5fa;}}
.guide li strong{{color:var(--text);}}
</style>
</head>
<body>
<div class="container">
  <h1>🎙️ 송림야담 여성 나레이터 복원 비교 v3</h1>
  <p class="subtitle">원본 F0 분석 기반 · 7가지 파라미터 조합 A/B 테스트<br>
  원본과 가장 동일한 버전을 선택 후 알려주시면 최종 적용합니다</p>

  <div class="analysis">
    <div class="metric">
      <div class="metric-val">193.7</div>
      <div class="metric-lbl">원본 F0 (Hz)</div>
      <div class="metric-sub">Alto / Mezzo</div>
    </div>
    <div class="metric">
      <div class="metric-val">130~259</div>
      <div class="metric-lbl">F0 범위 (Hz)</div>
      <div class="metric-sub">±25.7 변동폭</div>
    </div>
    <div class="metric">
      <div class="metric-val">1632</div>
      <div class="metric-lbl">Spectral Cent.</div>
      <div class="metric-sub">따뜻한 중저음</div>
    </div>
    <div class="metric">
      <div class="metric-val">0.049</div>
      <div class="metric-lbl">ZCR (부드러움)</div>
      <div class="metric-sub">매우 부드러운</div>
    </div>
  </div>

  <div class="original">
    <div class="section-title" style="color:#fca5a5;">🔴 원본: 유튜브 '송림야담' 실제 여성 나레이터 음성</div>
    <div class="script">"{EXACT_YT_SENTENCE}"</div>
    <audio controls preload="auto" src="../songrim_100pct_replica/01_youtube_actual_original.mp3"></audio>
  </div>

  <div class="section-head">🧬 복제 버전 {len(versions)}개 비교</div>
  {cards_html}

  <div class="guide">
    <h3>📋 선택 방법</h3>
    <ul>
      <li>원본 ▶ 재생 후 각 버전과 <strong>A/B 반복 비교</strong></li>
      <li>배경음악 때문에 판단 어려우면 <strong>01_vocals_only.wav</strong> 활용</li>
      <li>가장 비슷한 버전 번호 → <strong>알려주시면 최종 적용</strong>합니다</li>
      <li>pitch + rate + EQ 조합이 핵심 - 미세 조정 가능</li>
    </ul>
  </div>
</div>
</body>
</html>"""

    html_path.write_text(html, encoding="utf-8")
    print(f"\n  HTML 플레이어: {html_path.relative_to(WORKSPACE_DIR)}")
    return html_path


async def main():
    print("=" * 65)
    print("  송림야담 여성 나레이터 100% 복원 - v3")
    print("  원본 F0: 193.7 Hz / Alto-Mezzo / Spectral: 1632 Hz")
    print("=" * 65)

    versions_out = []
    for (name, voice, rate, pitch, eq_profile, desc) in PARAM_MATRIX:
        out_path = await synthesize_version(
            name, voice, rate, pitch, eq_profile, desc, EXACT_YT_SENTENCE
        )
        versions_out.append((name, voice, rate, pitch, eq_profile, desc, out_path))

    create_html_player(versions_out)

    print("\n" + "=" * 65)
    print("  완료! 생성된 파일:")
    for (name, _, _, _, _, desc, path) in versions_out:
        print(f"    {path.name}  ({desc})")
    print("=" * 65)
    print("  -> HTML 파일 열어서 원본과 비교하세요!")


if __name__ == "__main__":
    asyncio.run(main())
