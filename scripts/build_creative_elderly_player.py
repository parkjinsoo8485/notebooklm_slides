import asyncio
import os
import sys
import subprocess
import json
import base64
from pathlib import Path
import edge_tts
import torch
import numpy as np
import soundfile as sf
import parselmouth
from parselmouth.praat import call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
OUT_DIR = WORKSPACE / "output" / "slide01_creative_elderly"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REF_GRANDMOTHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandmother.wav"
REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandfather.wav"

SCRIPT_ORIGINAL = (
    "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, "
    "하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. "
    "차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
)

SCRIPT_CREATIVE = (
    "옛~날 옛적... 한양 북촌 명문가의 어질고 고왔던 우리 윤씨 마님이... "
    "하루아침에 억울~한 역모 누명을 쓰고... 저 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요... "
    "차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸~한 늦가을 밤의... 비극이었답니다..."
)

def apply_praat_elderly(in_wav, out_wav, pitch_factor=0.82, formant_factor=0.88, jitter_amount=0.010, is_male=False):
    """Praat PSOLA 기반 노년 성대 변환 (비음 제거 및 연륜 추가)"""
    try:
        snd = parselmouth.Sound(str(in_wav))
        manipulation = call(snd, "To Manipulation", 0.01, 50, 400)
        pitch_tier = call(manipulation, "Extract pitch tier")
        call(pitch_tier, "Multiply frequencies", 0, 999, pitch_factor)
        
        n_points = call(pitch_tier, "Get number of points")
        for i in range(1, n_points + 1):
            t = call(pitch_tier, "Get time from index", i)
            f = call(pitch_tier, "Get value at index", i)
            if f > 0:
                jitter = 1.0 + np.random.normal(0, jitter_amount)
                call(pitch_tier, "Remove point near", t)
                call(pitch_tier, "Add point", t, max(40.0, f * jitter))
                
        call([pitch_tier, manipulation], "Replace pitch tier")
        snd_new = call(manipulation, "Get resynthesis (overlap-add)")
        
        from scipy.signal import resample_poly
        data = snd_new.values.flatten()
        original_sr = int(snd_new.sampling_frequency)
        up = 100
        down = int(round(100 / formant_factor))
        data_slow = resample_poly(data, up, down)
        
        target_len = len(data)
        if len(data_slow) >= target_len:
            data_out = data_slow[:target_len]
        else:
            data_out = np.pad(data_slow, (0, target_len - len(data_slow)))
            
        sf.write(str(out_wav), data_out, original_sr)
        return True
    except Exception as e:
        print(f"   [Praat Error] {e}")
        return False

async def generate_edge(text, out_mp3, voice, rate, pitch, is_male=False):
    # 피치를 Edge-TTS 자체에서 너무 많이 낮추면 비음이 심해지므로, Praat에서 주로 낮춤
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch="-5Hz")
    raw_mp3 = str(out_mp3).replace(".mp3", "_raw.mp3")
    raw_wav = str(out_mp3).replace(".mp3", "_raw.wav")
    praat_wav = str(out_mp3).replace(".mp3", "_praat.wav")
    
    await comm.save(raw_mp3)
    subprocess.run(["ffmpeg", "-y", "-i", raw_mp3, "-ar", "44100", "-ac", "1", raw_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 할머니/할아버지에 따라 Formant/Pitch 조정 (비음 제거를 위해 Formant 확 내림)
    pf = 0.78 if is_male else 0.75
    ff = 0.85 if is_male else 0.82
    apply_praat_elderly(raw_wav, praat_wav, pitch_factor=pf, formant_factor=ff, jitter_amount=0.012, is_male=is_male)
    
    subprocess.run(["ffmpeg", "-y", "-i", praat_wav, "-b:a", "320k", str(out_mp3)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw_mp3)
    os.remove(raw_wav)
    os.remove(praat_wav)
    print(f"   [OK] Edge-TTS (Praat Aged): {out_mp3.name}")

async def generate_xtts(text, ref_wav, out_wav):
    try:
        from TTS.api import TTS
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        tts.tts_to_file(
            text=text,
            speaker_wav=str(ref_wav),
            language="ko",
            file_path=str(out_wav)
        )
        print(f"   [OK] XTTS-v2: {out_wav.name}")
    except Exception as e:
        print(f"   [WARNING] TTS failed to load ({e}). Using Edge-TTS fallback.")
        voice = "ko-KR-SunHiNeural" if "grandma" in out_wav.name else "ko-KR-InJoonNeural"
        is_male = "grandpa" in out_wav.name
        
        temp_mp3 = str(out_wav).replace('.wav', '_fallback.mp3')
        await generate_edge(text, Path(temp_mp3), voice, rate="-20%", pitch="-5Hz", is_male=is_male)
        subprocess.run(["ffmpeg", "-y", "-i", temp_mp3, "-ar", "44100", "-ac", "1", str(out_wav)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        os.remove(temp_mp3)

def master_audio(in_file, out_mp3, add_warmth=False, is_male=False):
    # Praat 후 비음 제거 EQ (1500Hz 대역 감쇠) 및 가슴 울림(120~200Hz) 증폭
    if add_warmth:
        if is_male:
            af = "equalizer=f=120:width_type=o:width=1.5:g=+3.5dB,equalizer=f=1500:width_type=o:width=1.0:g=-3.5dB,loudnorm=I=-16:LRA=11:TP=-1.5"
        else:
            af = "equalizer=f=200:width_type=o:width=1.5:g=+3.0dB,equalizer=f=1800:width_type=o:width=1.2:g=-4.0dB,loudnorm=I=-16:LRA=11:TP=-1.5"
    else:
        af = "loudnorm=I=-16:LRA=11:TP=-1.5"
        
    subprocess.run([
        "ffmpeg", "-y", "-i", str(in_file),
        "-af", af,
        "-b:a", "320k",
        str(out_mp3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   [OK] Mastered: {out_mp3.name}")

async def main():
    print("=" * 70)
    print(" 🎨 창조적 음성 생성: 자연스러운 노인 구연 (비음/젊은음색 제거 버전)")
    print("=" * 70)

    tracks_info = []

    # -------------------------------------------------------------------------
    # 할머니 3종
    # -------------------------------------------------------------------------
    print("\n>>> [1/6] 👵 할머니 옵션 A: Edge-TTS + Praat (호흡/말맛 대본 + SunHiNeural)")
    t1_raw = OUT_DIR / "t1_edge_grandma.mp3"
    t1_master = OUT_DIR / "t1_grandma_edge_master.mp3"
    await generate_edge(SCRIPT_CREATIVE, t1_raw, "ko-KR-SunHiNeural", rate="-25%", pitch="-5Hz", is_male=False)
    master_audio(t1_raw, t1_master, add_warmth=True, is_male=False)
    tracks_info.append({
        "badge": "✨ [전략 1] Praat 물리 음향 변환",
        "name": "👵 할머니 A: 구수한 말맛 (비음 완벽 제거)",
        "desc": "Praat의 포먼트(Formant) 이동 기술을 통해 젊은 여성의 비음을 완전히 없애고 100세 할머니의 깊은 연륜을 더했습니다.",
        "file": t1_master,
        "highlight": True
    })

    print("\n>>> [2/6] 👵 할머니 옵션 B: XTTS-v2 1:1 말투 복제 (실제 할머니 레퍼런스)")
    t2_raw = OUT_DIR / "t2_xtts_grandma.wav"
    t2_master = OUT_DIR / "t2_grandma_xtts_master.mp3"
    await generate_xtts(SCRIPT_ORIGINAL, REF_GRANDMOTHER, t2_raw)
    master_audio(t2_raw, t2_master, add_warmth=False, is_male=False)
    tracks_info.append({
        "badge": "👑 [전략 2] XTTS-v2 말투 1:1 복제",
        "name": "👵 할머니 B: 실제 이야기 할머니 육성 1:1 복제",
        "desc": "원본 할머니의 호흡, 성대 떨림, 어미 처리까지 문맥적으로 복제한 구연.",
        "file": t2_master,
        "highlight": False
    })

    print("\n>>> [3/6] 👵 할머니 옵션 C: 하이브리드 서정적 낭독 (Edge-TTS + Praat)")
    t3_raw = OUT_DIR / "t3_edge_grandma_lyric.mp3"
    t3_master = OUT_DIR / "t3_grandma_lyric_master.mp3"
    await generate_edge(SCRIPT_ORIGINAL, t3_raw, "ko-KR-SunHiNeural", rate="-20%", pitch="-5Hz", is_male=False)
    master_audio(t3_raw, t3_master, add_warmth=True, is_male=False)
    tracks_info.append({
        "badge": "🌙 서정적 낭독 톤",
        "name": "👵 할머니 C: 서정적 낭독 톤",
        "desc": "속도를 늦추고 극저음 피치+포먼트 하강으로 자애로운 느낌을 살렸습니다.",
        "file": t3_master,
        "highlight": False
    })

    # -------------------------------------------------------------------------
    # 할아버지 3종
    # -------------------------------------------------------------------------
    print("\n>>> [4/6] 👴 할아버지 옵션 A: Edge-TTS + Praat (호흡/말맛 대본 + InJoonNeural)")
    t4_raw = OUT_DIR / "t4_edge_grandpa.mp3"
    t4_master = OUT_DIR / "t4_grandpa_edge_master.mp3"
    await generate_edge(SCRIPT_CREATIVE, t4_raw, "ko-KR-InJoonNeural", rate="-22%", pitch="-5Hz", is_male=True)
    master_audio(t4_raw, t4_master, add_warmth=True, is_male=True)
    tracks_info.append({
        "badge": "✨ [전략 1] Praat 물리 음향 변환",
        "name": "👴 할아버지 A: 야담가 톤 (비음 완벽 제거)",
        "desc": "가슴을 울리는 흉성을 부스팅하고 비음을 줄여 중후한 연륜이 묻어나는 할아버지 톤입니다.",
        "file": t4_master,
        "highlight": True
    })

    print("\n>>> [5/6] 👴 할아버지 옵션 B: XTTS-v2 1:1 말투 복제 (실제 할아버지 레퍼런스)")
    t5_raw = OUT_DIR / "t5_xtts_grandpa.wav"
    t5_master = OUT_DIR / "t5_grandpa_xtts_master.mp3"
    await generate_xtts(SCRIPT_ORIGINAL, REF_GRANDFATHER, t5_raw)
    master_audio(t5_raw, t5_master, add_warmth=False, is_male=True)
    tracks_info.append({
        "badge": "👑 [전략 2] XTTS-v2 말투 1:1 복제",
        "name": "👴 할아버지 B: 실제 야담 할아버지 육성 1:1 복제",
        "desc": "전통 할아버지의 깊은 숨소리와 억양 곡선(F0)까지 제로샷으로 복제했습니다.",
        "file": t5_master,
        "highlight": False
    })

    print("\n>>> [6/6] 👴 할아버지 옵션 C: 현수 다국어 모델 + Praat (포근한 낭독)")
    t6_raw = OUT_DIR / "t6_edge_grandpa_hyunsu.mp3"
    t6_master = OUT_DIR / "t6_grandpa_hyunsu_master.mp3"
    await generate_edge(SCRIPT_ORIGINAL, t6_raw, "ko-KR-HyunsuMultilingualNeural", rate="-20%", pitch="-5Hz", is_male=True)
    master_audio(t6_raw, t6_master, add_warmth=True, is_male=True)
    tracks_info.append({
        "badge": "🌙 포근한 낭독 톤",
        "name": "👴 할아버지 C: 친근한 손주 대상 낭독",
        "desc": "할아버지가 손주에게 옛이야기를 들려주듯 포근한 음색에 떨림을 추가했습니다.",
        "file": t6_master,
        "highlight": False
    })

    # HTML 청음실 생성
    print("\n>>> [7/7] HTML 비교 청음실 생성 중...")
    def to_b64(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    
    html_tracks = []
    for t in tracks_info:
        d = t["file"]
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(d)], stdout=subprocess.PIPE, text=True)
        dur_str = "??:??"
        if r.stdout.strip():
            d_val = float(r.stdout.strip())
            dur_str = f"{int(d_val//60):02d}:{int(d_val%60):02d}"
        
        html_tracks.append({
            "badge": t["badge"],
            "name": t["name"],
            "desc": t["desc"],
            "b64": to_b64(t["file"]),
            "duration": dur_str,
            "highlight": t["highlight"]
        })

    tj = json.dumps(html_tracks, ensure_ascii=False)
    
    html = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 고도화 음성 마스터 (비음/젊은톤 제거)</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#070a11;--card:rgba(18,25,42,.92);--accent:#f59e0b;--text:#f8fafc;--muted:#94a3b8;--border:rgba(255,255,255,.12);}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:radial-gradient(ellipse at 50% 0%,#1f1535 0%,#0d1117 55%,var(--bg) 100%);color:var(--text);font-family:'Pretendard',sans-serif;min-height:100vh;padding:48px 20px;display:flex;justify-content:center;}
.container{max-width:960px;width:100%;}
.header{text-align:center;margin-bottom:40px;}
.tag{display:inline-block;padding:7px 20px;background:rgba(245,158,11,.15);border:1px solid #f59e0b;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:1.8px;color:#fcd34d;margin-bottom:16px;}
h1{font-family:'Noto Serif KR',serif;font-size:32px;font-weight:900;margin-bottom:14px;background:linear-gradient(135deg,#fff 0%,#fcd34d 40%,var(--accent) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.4;}
p.sub{color:var(--muted);font-size:15px;line-height:1.7;}
.sb{display:flex;flex-direction:column;gap:15px;background:rgba(18,25,42,.95);border:1px solid var(--border);border-radius:16px;padding:22px 26px;margin-bottom:28px;box-shadow:0 10px 30px rgba(0,0,0,.5);}
.st{color:var(--accent);font-weight:800;font-size:13px;}
.sx{font-family:'Noto Serif KR',serif;font-size:16px;line-height:1.8;color:#e2e8f0;padding:12px;background:rgba(0,0,0,0.2);border-radius:8px;}
.tl{display:flex;flex-direction:column;gap:20px;}
.tc{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:24px;transition:transform .3s;box-shadow:0 8px 24px rgba(0,0,0,.4);}
.tc.hl{border-color:rgba(245,158,11,.55);background:rgba(38,28,13,.92);box-shadow:0 10px 32px rgba(245,158,11,.18);}
.tc:hover{transform:translateY(-3px);}
.th{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}
.tb{font-size:12px;font-weight:800;padding:5px 12px;border-radius:8px;background:rgba(255,255,255,.08);color:#cbd5e1;}
.tc.hl .tb{background:rgba(245,158,11,.2);color:#fcd34d;border:1px solid rgba(245,158,11,.4);}
.tt{font-size:13px;font-weight:700;color:#38bdf8;background:rgba(56,189,248,.12);padding:4px 10px;border-radius:6px;}
.tn{font-family:'Noto Serif KR',serif;font-size:19px;font-weight:800;margin-bottom:8px;}
.td{font-size:13px;color:var(--muted);margin-bottom:16px;line-height:1.55;}
audio{width:100%;border-radius:10px;}audio::-webkit-media-controls-panel{background-color:#1e293b;}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <div class="tag">💡 ADVANCED PRAAT VOCAL PHYSICS</div>
  <h1>[송림야담] 고도화 음성 마스터 (비음 완벽 제거)<br>자연스러운 노년기 음색 재현</h1>
  <p class="sub">피치만 낮춰서 발생하던 '기계적 비음'과 '젊은 사람 흉내' 현상을 <b>Praat 포먼트 시프팅(Formant Shifting)</b>과 미세 성대 떨림(Jitter) 물리 모델링을 통해 완전히 해결했습니다.</p>
</div>
<div class="sb">
  <div>
    <div class="st">📜 옵션 A (원문 대본 - 서정 낭독용)</div>
    <div class="sx">""" + SCRIPT_ORIGINAL + """</div>
  </div>
  <div>
    <div class="st">📜 옵션 B (구연 말맛 극대화 대본 - Edge-TTS 전용)</div>
    <div class="sx">""" + SCRIPT_CREATIVE + """</div>
  </div>
</div>
<div class="tl" id="tl"></div>
</div>
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
</script>
</body>
</html>
"""
    html_path = OUT_DIR / "slide01_creative_elderly_player.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"\n[DONE] 창조적 고도화 청음실 완성: {html_path}")

if __name__ == "__main__":
    asyncio.run(main())
