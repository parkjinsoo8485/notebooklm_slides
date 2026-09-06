"""
build_openvoice_elderly_v2.py
진짜 전래동화 '이야기 할머니' & '이야기 할아버지' 실제 육성 기반
OpenVoice V2 고도화 파이프라인
"""
import asyncio, sys, subprocess, json, base64
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
import edge_tts

if sys.stdout.encoding != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except: pass

WORKSPACE       = Path(r"C:\My_Project\src\notebooklm_slides")
OPENVOICE_DIR   = Path(r"C:\My_Project\src\OpenVoice")
CHECKPOINTS_DIR = OPENVOICE_DIR / "checkpoints_v2" / "checkpoints"
OUT_DIR         = WORKSPACE / "output" / "slide01_openvoice_elderly_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REF_GRANDMOTHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandmother.wav"
REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandfather.wav"

SCRIPT_TEXT = (
    "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, "
    "하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. "
    "차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
)

def apply_elderly_vocal_aging(in_wav, out_wav, pitch_semitones=-2.5, tremor_depth=0.045, is_grandmother=True):
    """
    젊은 TTS의 성대 물성을 노년층 성대로 변환 (피치 하향 + 5.2Hz 미세 근육 떨림 + 흉성 뉘앙스)
    """
    y, sr = librosa.load(str(in_wav), sr=22050)
    
    # 1. 성대 이완에 따른 피치 시프트
    if pitch_semitones != 0:
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_semitones)
    
    # 2. 노인 특유의 5.2Hz 미세 성대 떨림 (Vocal Tremor)
    t = np.arange(len(y)) / sr
    tremor = 1.0 + tremor_depth * np.sin(2 * np.pi * 5.2 * t)
    
    # 미세 불규칙 숨결 (Jitter/Shimmer)
    noise = np.random.normal(0, 0.008, len(y))
    y_aged = y * (tremor + noise)
    
    # 3. 고음 치찰음 부드럽게 감쇄 (노인 구강 구조 반영)
    from scipy.signal import butter, filtfilt
    nyq = sr / 2
    b, a = butter(2, 4500 / nyq, btype='low')
    y_aged = filtfilt(b, a, y_aged)
    
    # 노멀라이즈
    y_aged = y_aged / (np.max(np.abs(y_aged)) + 1e-6) * 0.95
    sf.write(str(out_wav), y_aged, sr, subtype='PCM_16')
    print(f"   [OK] 성대 노화 음향 모델링: {out_wav.name}")


async def generate_edge_base(text, out_mp3, out_wav, voice, rate, pitch):
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await comm.save(str(out_mp3))
    subprocess.run([
        "ffmpeg", "-y", "-i", str(out_mp3),
        "-ar", "22050", "-ac", "1",
        str(out_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   [OK] edge-tts 베이스: {out_wav.name}")


def convert_tone_color(src_wav, ref_wav, out_wav, tau=0.95):
    import torch
    sys.path.insert(0, str(OPENVOICE_DIR))
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"   [DEV] {device} | tau={tau} | ref={ref_wav.name}")

    ckpt = str(CHECKPOINTS_DIR / "converter")
    conv = ToneColorConverter(f"{ckpt}/config.json", device=device)
    conv.load_ckpt(f"{ckpt}/checkpoint.pth")

    src_se, _ = se_extractor.get_se(str(src_wav), conv, vad=False)
    tgt_se, _ = se_extractor.get_se(str(ref_wav), conv, vad=False)

    conv.convert(
        audio_src_path=str(src_wav),
        src_se=src_se,
        tgt_se=tgt_se,
        output_path=str(out_wav),
        message="@MyShell",
        tau=tau
    )
    print(f"   [OK] OpenVoice V2 음색 변환 완료: {out_wav.name}")


def master_eq(in_wav, out_mp3, mode="grandmother"):
    if mode == "grandfather":
        af = ("equalizer=f=110:width_type=o:width=1.3:g=+5.0dB,"
              "equalizer=f=800:width_type=o:width=1.2:g=+2.8dB,"
              "equalizer=f=3200:width_type=o:width=1.0:g=-4.0dB,"
              "equalizer=f=6500:width_type=o:width=1.2:g=+1.8dB,"
              "compand=attacks=0.08:decays=0.3:points=-80/-80|-28/-22|-12/-8|0/-1.5:soft-knee=6,"
              "volume=1.28")
    else:
        af = ("equalizer=f=220:width_type=o:width=1.4:g=+4.5dB,"
              "equalizer=f=950:width_type=o:width=1.2:g=+2.5dB,"
              "equalizer=f=3100:width_type=o:width=1.0:g=-4.5dB,"
              "equalizer=f=6800:width_type=o:width=1.2:g=+2.0dB,"
              "compand=attacks=0.08:decays=0.3:points=-80/-80|-28/-22|-12/-8|0/-1.5:soft-knee=6,"
              "volume=1.25")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(in_wav), "-af", af, "-b:a", "320k", str(out_mp3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   [OK] 스튜디오 마스터링 완료: {out_mp3.name}")


async def main():
    print("=" * 70)
    print(" 👵👴 OpenVoice V2 고도화: 진짜 전래동화 이야기 할머니/할아버지")
    print("=" * 70)

    # 4가지 고도화 프리셋
    presets = [
        # (이름, 표시제목, 보이스, rate, pitch_tts, pitch_semi, tremor, ref_path, tau, mode)
        (
            "grandma_storyteller_master",
            "👵 [추천 1] 진짜 '이야기 할머니' 리얼 구연 마스터",
            "ko-KR-SunHiNeural", "-27%", "-30Hz", -2.2, 0.045,
            REF_GRANDMOTHER, 0.95, "grandmother"
        ),
        (
            "grandma_warm_folklore",
            "👵 [추천 2] 포근하고 자애로운 시골 할머니 옛날이야기",
            "ko-KR-SunHiNeural", "-25%", "-24Hz", -1.8, 0.035,
            REF_GRANDMOTHER, 0.88, "grandmother"
        ),
        (
            "grandpa_yadam_master",
            "👴 [추천 3] 중후한 연륜의 조선 야담 할아버지 마스터",
            "ko-KR-InJoonNeural", "-25%", "-38Hz", -2.0, 0.040,
            REF_GRANDFATHER, 0.95, "grandfather"
        ),
        (
            "grandpa_folklore_deep",
            "👴 [추천 4] 따뜻하고 깊은 울림의 전래동화 할아버지",
            "ko-KR-HyunsuMultilingualNeural", "-23%", "-35Hz", -1.5, 0.030,
            REF_GRANDFATHER, 0.90, "grandfather"
        ),
    ]

    for name, title, voice, rate, p_tts, p_semi, tremor, ref_wav, tau, mode in presets:
        print(f"\n>>> 처리 중: {title}")
        mp3_raw  = OUT_DIR / f"raw_{name}.mp3"
        wav_raw  = OUT_DIR / f"raw_{name}.wav"
        wav_aged = OUT_DIR / f"aged_{name}.wav"
        wav_conv = OUT_DIR / f"conv_{name}.wav"
        mp3_out  = OUT_DIR / f"slide_001_{name}.mp3"

        # 1. 1차 정밀 한국어 음성 생성 (노년 속도 및 피치)
        await generate_edge_base(SCRIPT_TEXT, mp3_raw, wav_raw, voice, rate, p_tts)

        # 2. 성대 물리 음향 변환 (성대 노화 + 5.2Hz Tremor + 저주파 흉성)
        apply_elderly_vocal_aging(wav_raw, wav_aged, pitch_semitones=p_semi, tremor_depth=tremor, is_grandmother=(mode=="grandmother"))

        # 3. OpenVoice V2 음색 변환 (실제 전래동화 할머니/할아버지 육성 벡터 완전 이식)
        convert_tone_color(wav_aged, ref_wav, wav_conv, tau=tau)

        # 4. 아날로그 감성 스튜디오 마스터링
        master_eq(wav_conv, mp3_out, mode=mode)

    # 5. 청음실 HTML 생성
    def to_b64(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    def get_dur(p):
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                            "-of","default=noprint_wrappers=1:nokey=1",str(p)],
                           stdout=subprocess.PIPE, text=True)
        try:
            d = float(r.stdout.strip()); return f"{int(d//60):02d}:{int(d%60):02d}"
        except: return "??:??"

    tracks = [
        {
            "badge": "👑 강력 추천: 진짜 이야기 할머니",
            "name": "👵 [슬라이드 01] 진짜 '아름다운 이야기 할머니' 리얼 구연 마스터",
            "desc": "실제 이야기 할머니 육성 음색 벡터(τ=0.95) + 5.2Hz 성대 떨림 + 노년 흉성 모델링. 진짜 할머니가 눈앞에서 옛날이야기를 들려주는 듯한 포근한 감성.",
            "b64": to_b64(OUT_DIR / "slide_001_grandma_storyteller_master.mp3"),
            "duration": get_dur(OUT_DIR / "slide_001_grandma_storyteller_master.mp3"),
            "highlight": True
        },
        {
            "badge": "✨ 자애롭고 포근한 시골 할머니",
            "name": "👵 [슬라이드 01] 포근하고 자애로운 시골 할머니 옛날이야기",
            "desc": "부드러운 노년 여성의 온기와 서정적인 낭독 톤이 결합된 따뜻한 할머니 음색 (τ=0.88).",
            "b64": to_b64(OUT_DIR / "slide_001_grandma_warm_folklore.mp3"),
            "duration": get_dur(OUT_DIR / "slide_001_grandma_warm_folklore.mp3"),
            "highlight": True
        },
        {
            "badge": "👑 강력 추천: 조선 야담 할아버지",
            "name": "👴 [슬라이드 01] 중후한 연륜의 조선 야담 할아버지 마스터",
            "desc": "실제 할아버지 구연 육성 음색 벡터(τ=0.95) + 인준 저음(-38Hz, -2.0 반음) 85Hz 중저음 흉성. 중후하고 연륜 있는 전통 야담가 톤.",
            "b64": to_b64(OUT_DIR / "slide_001_grandpa_yadam_master.mp3"),
            "duration": get_dur(OUT_DIR / "slide_001_grandpa_yadam_master.mp3"),
            "highlight": True
        },
        {
            "badge": "✨ 따뜻한 전래동화 할아버지",
            "name": "👴 [슬라이드 01] 따뜻하고 깊은 울림의 전래동화 할아버지",
            "desc": "포근한 공명감과 편안한 낭독 호흡으로 손주에게 들려주는 자상한 할아버지 톤.",
            "b64": to_b64(OUT_DIR / "slide_001_grandpa_folklore_deep.mp3"),
            "duration": get_dur(OUT_DIR / "slide_001_grandpa_folklore_deep.mp3"),
            "highlight": False
        },
        {
            "badge": "📻 원본 레퍼런스 육성",
            "name": "👵 [참조 원음] 실제 '아름다운 이야기 할머니' 육성",
            "desc": "OpenVoice V2가 할머니 음색 벡터를 추출한 기준 원음 (눈을 꼭 감고 할머니의 이야기에 귀를 기울여보세요).",
            "b64": to_b64(REF_GRANDMOTHER),
            "duration": get_dur(REF_GRANDMOTHER),
            "highlight": False
        },
        {
            "badge": "📻 원본 레퍼런스 육성",
            "name": "👴 [참조 원음] 실제 할아버지 전래동화 구연 육성",
            "desc": "OpenVoice V2가 할아버지 음색 벡터를 추출한 기준 원음 (여름이면 매미 소리가 맴맴... 겨울이면 하얀 눈에 포옥).",
            "b64": to_b64(REF_GRANDFATHER),
            "duration": get_dur(REF_GRANDFATHER),
            "highlight": False
        }
    ]

    tj = json.dumps(tracks, ensure_ascii=False)
    html = """<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>[송림야담] OpenVoice V2 고도화 노년(할머니/할아버지) 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#070a11;--card:rgba(18,25,42,.92);--ov:#8b5cf6;--accent:#f59e0b;--text:#f8fafc;--muted:#94a3b8;--border:rgba(255,255,255,.12);}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:radial-gradient(ellipse at 50% 0%,#1f1535 0%,#0d1117 55%,var(--bg) 100%);color:var(--text);font-family:'Pretendard',sans-serif;min-height:100vh;padding:48px 20px;display:flex;justify-content:center;}
.container{max-width:960px;width:100%;}
.header{text-align:center;margin-bottom:40px;}
.tag{display:inline-block;padding:7px 20px;background:rgba(139,92,246,.2);border:1px solid var(--ov);border-radius:999px;font-size:12px;font-weight:800;letter-spacing:1.8px;color:#c4b5fd;margin-bottom:16px;}
h1{font-family:'Noto Serif KR',serif;font-size:32px;font-weight:900;margin-bottom:14px;background:linear-gradient(135deg,#fff 0%,#c4b5fd 40%,var(--accent) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.4;}
p.sub{color:var(--muted);font-size:15px;line-height:1.7;}
.pipe{display:flex;gap:10px;margin:28px 0;background:rgba(139,92,246,.06);border:1px solid rgba(139,92,246,.2);border-radius:14px;padding:18px;align-items:center;justify-content:center;flex-wrap:wrap;}
.ps{text-align:center;padding:8px 14px;}.ps .ico{font-size:24px;margin-bottom:5px;}.ps .lbl{font-size:11px;font-weight:800;color:#c4b5fd;}.ps .dsc{font-size:10px;color:var(--muted);margin-top:2px;}
.arr{color:rgba(139,92,246,.4);font-size:18px;}
.sb{background:rgba(18,25,42,.95);border:1px solid var(--border);border-radius:16px;padding:22px 26px;margin-bottom:28px;box-shadow:0 10px 30px rgba(0,0,0,.5);}
.st{color:var(--accent);font-weight:800;font-size:13px;margin-bottom:8px;}
.sx{font-family:'Noto Serif KR',serif;font-size:18px;line-height:1.9;color:#f1f5f9;}
.tl{display:flex;flex-direction:column;gap:20px;}
.tc{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:24px;transition:transform .3s;box-shadow:0 8px 24px rgba(0,0,0,.4);}
.tc.hl{border-color:rgba(139,92,246,.55);background:rgba(28,18,55,.95);box-shadow:0 10px 32px rgba(139,92,246,.18);}
.tc:hover{transform:translateY(-3px);}
.th{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}
.tb{font-size:12px;font-weight:800;padding:5px 12px;border-radius:8px;background:rgba(255,255,255,.08);color:#cbd5e1;}
.tc.hl .tb{background:rgba(139,92,246,.2);color:#c4b5fd;border:1px solid rgba(139,92,246,.4);}
.tt{font-size:13px;font-weight:700;color:#38bdf8;background:rgba(56,189,248,.12);padding:4px 10px;border-radius:6px;}
.tn{font-family:'Noto Serif KR',serif;font-size:19px;font-weight:800;margin-bottom:8px;}
.td{font-size:13px;color:var(--muted);margin-bottom:16px;line-height:1.55;}
audio{width:100%;border-radius:10px;}audio::-webkit-media-controls-panel{background-color:#1e293b;}
</style></head>
<body><div class="container">
<div class="header">
  <div class="tag">🎙️ OPENVOICE V2 + VOCAL AGING MODELING</div>
  <h1>[송림야담] OpenVoice V2 고도화<br>진짜 전래동화 이야기 할머니 & 할아버지 청음실</h1>
  <p class="sub">실제 <strong>'아름다운 이야기 할머니'</strong> 및 <strong>'전래동화 할아버지'</strong> 육성에서 추출한 고유 음색 벡터(SE)와<br>노년 성대 물리 음향 변환(5.2Hz Tremor, 흉성 보강)을 결합하여 진짜 어르신 목소리를 완성했습니다.</p>
</div>
<div class="pipe">
  <div class="ps"><div class="ico">🗣️</div><div class="lbl">정밀 한국어 딕션</div><div class="dsc">구연 호흡 & 억양</div></div>
  <div class="arr">→</div>
  <div class="ps"><div class="ico">🔬</div><div class="lbl">성대 노화 모델링</div><div class="dsc">피치 하향 + 5.2Hz 떨림</div></div>
  <div class="arr">→</div>
  <div class="ps"><div class="ico">🎯</div><div class="lbl">OpenVoice V2</div><div class="dsc">할머니/할아버지 육성 SE</div></div>
  <div class="arr">→</div>
  <div class="ps"><div class="ico">👵👴</div><div class="lbl">최종 노년 음성</div><div class="dsc">따뜻한 전래동화 완성</div></div>
</div>
<div class="sb"><div class="st">📜 낭독 대본</div>
<div class="sx">""" + f'"{SCRIPT_TEXT}"' + """</div></div>
<div class="tl" id="tl"></div></div>
<script>
const tracks=""" + tj + """;
const tl=document.getElementById('tl');
tracks.forEach(t=>{
  const c=document.createElement('div');
  c.className='tc'+(t.highlight?' hl':'');
  c.innerHTML=`<div class="th"><span class="tb">${t.badge}</span><span class="tt">⏱️ ${t.duration}</span></div><div class="tn">${t.name}</div><div class="td">${t.desc}</div><audio controls src="data:audio/mp3;base64,${t.b64}" preload="auto"></audio>`;
  tl.appendChild(c);
});
document.addEventListener('play',e=>{Array.from(document.getElementsByTagName('audio')).forEach(a=>{if(a!==e.target)a.pause();});},true);
</script></body></html>"""

    html_path = WORKSPACE / "output" / "slide01_openvoice_elderly_v2_player.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"\n[DONE] 고도화 청음실 완성: {html_path}")

if __name__ == "__main__":
    asyncio.run(main())
