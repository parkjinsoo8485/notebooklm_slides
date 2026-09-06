"""
build_openvoice_elderly.py
edge-tts (한국어 딕션) → OpenVoice V2 ToneColorConverter (노년 음색 이식)
MeloTTS 없이도 동작하는 버전
"""
import asyncio, sys, subprocess, urllib.request, zipfile, json, base64
from pathlib import Path
import edge_tts

if sys.stdout.encoding != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except: pass

WORKSPACE       = Path(r"C:\My_Project\src\notebooklm_slides")
OPENVOICE_DIR   = Path(r"C:\My_Project\src\OpenVoice")
CHECKPOINTS_DIR = OPENVOICE_DIR / "checkpoints_v2" / "checkpoints"
OUT_DIR         = WORKSPACE / "output" / "slide01_openvoice_elderly"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "03_elderly_grandfather_folklore.mp3"

SCRIPT_TEXT = (
    "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, "
    "하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. "
    "차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
)


def download_checkpoints():
    if CHECKPOINTS_DIR.exists() and list(CHECKPOINTS_DIR.rglob("*.pth")):
        print("   [OK] 체크포인트 이미 존재")
        return
    print("   [DL] OpenVoice V2 체크포인트 다운로드 (~200MB)...")
    url = "https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
    zip_path = OPENVOICE_DIR / "checkpoints_v2_0417.zip"
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(OPENVOICE_DIR)
    zip_path.unlink()
    print("   [OK] 체크포인트 다운로드 완료")


def prepare_reference_clip(ref_mp3, out_wav, start_sec=10, duration=15):
    subprocess.run([
        "ffmpeg", "-y", "-i", str(ref_mp3),
        "-ss", str(start_sec), "-t", str(duration),
        "-ar", "22050", "-ac", "1",
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
        str(out_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   [OK] 레퍼런스 클립: {out_wav.name}")


async def generate_edge_base(text, out_mp3, out_wav, voice, rate, pitch):
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await comm.save(str(out_mp3))
    subprocess.run([
        "ffmpeg", "-y", "-i", str(out_mp3),
        "-ar", "22050", "-ac", "1",
        str(out_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   [OK] edge-tts 베이스: {out_wav.name}")


def convert_tone_color(src_wav, ref_wav, out_wav, tau=0.7):
    import torch
    sys.path.insert(0, str(OPENVOICE_DIR))
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"   [DEV] {device} | tau={tau}")

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
    print(f"   [OK] 음색 변환 완료: {out_wav.name}")


def master_eq(in_wav, out_mp3, mode="grandmother"):
    if mode == "grandfather":
        af = ("equalizer=f=130:width_type=o:width=1.3:g=+4.5dB,"
              "equalizer=f=900:width_type=o:width=1.1:g=+2.5dB,"
              "equalizer=f=3500:width_type=o:width=1.0:g=-3.5dB,"
              "equalizer=f=7000:width_type=o:width=1.2:g=+1.5dB,"
              "compand=attacks=0.08:decays=0.3:points=-80/-80|-28/-22|-12/-8|0/-1.5:soft-knee=6,"
              "volume=1.28")
    else:
        af = ("equalizer=f=200:width_type=o:width=1.4:g=+3.8dB,"
              "equalizer=f=1100:width_type=o:width=1.2:g=+2.2dB,"
              "equalizer=f=3400:width_type=o:width=1.0:g=-3.8dB,"
              "equalizer=f=7200:width_type=o:width=1.2:g=+1.8dB,"
              "compand=attacks=0.08:decays=0.3:points=-80/-80|-28/-22|-12/-8|0/-1.5:soft-knee=6,"
              "volume=1.22")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(in_wav), "-af", af, "-b:a", "320k", str(out_mp3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   [OK] EQ 마스터링: {out_mp3.name}")


async def main():
    print("=" * 65)
    print(" edge-tts + OpenVoice V2 노년 음색 변환 파이프라인")
    print("=" * 65)

    # 0. 체크포인트
    download_checkpoints()

    # 1. 레퍼런스 클립
    ref_wav = OUT_DIR / "ref_elderly.wav"
    prepare_reference_clip(REF_GRANDFATHER, ref_wav)

    # 2. edge-tts 베이스 생성 (3개 프리셋)
    presets = [
        # (이름, 보이스, rate, pitch, tau, mode)
        ("grandmother_warm",  "ko-KR-SunHiNeural",   "-22%", "-10Hz", 0.75, "grandmother"),
        ("grandmother_lyric", "ko-KR-SunHiNeural",   "-18%", "-8Hz",  0.65, "grandmother"),
        ("grandfather",       "ko-KR-HyunsuMultilingualNeural", "-20%", "-6Hz", 0.80, "grandfather"),
    ]

    for name, voice, rate, pitch, tau, mode in presets:
        print(f"\n--- {name} ---")
        mp3_base = OUT_DIR / f"base_{name}.mp3"
        wav_base = OUT_DIR / f"base_{name}.wav"
        wav_conv = OUT_DIR / f"conv_{name}.wav"
        mp3_out  = OUT_DIR / f"slide_001_{name}_master.mp3"

        await generate_edge_base(SCRIPT_TEXT, mp3_base, wav_base, voice, rate, pitch)
        convert_tone_color(wav_base, ref_wav, wav_conv, tau=tau)
        master_eq(wav_conv, mp3_out, mode=mode)

    # 3. HTML
    def to_b64(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    def get_dur(p):
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                            "-of","default=noprint_wrappers=1:nokey=1",str(p)],
                           stdout=subprocess.PIPE, text=True)
        try:
            d = float(r.stdout.strip()); return f"{int(d//60):02d}:{int(d%60):02d}"
        except: return "??:??"

    opt1 = OUT_DIR / "slide_001_grandmother_warm_master.mp3"
    opt2 = OUT_DIR / "slide_001_grandmother_lyric_master.mp3"
    opt3 = OUT_DIR / "slide_001_grandfather_master.mp3"

    tracks = [
        {"badge":"👑 대표 추천: 따뜻한 할머니 구연","name":"👵 [슬라이드 01] OpenVoice V2 | 포근하고 구수한 할머니 전래동화","desc":"edge-tts 한국어 발음 + 실제 노년 성우 음색 벡터(τ=0.75) 이식. 진짜 할머니의 따뜻한 음색.","b64":to_b64(opt1),"duration":get_dur(opt1),"highlight":True},
        {"badge":"✨ 서정적 할머니 낭독 (τ=0.65)","name":"📖 [슬라이드 01] OpenVoice V2 | 서정적이고 자애로운 할머니 낭독","desc":"음색 이식 강도를 조절(τ=0.65)하여 더 자연스럽고 서정적인 노년 여성 낭독 톤.","b64":to_b64(opt2),"duration":get_dur(opt2),"highlight":True},
        {"badge":"👴 중후한 할아버지 구연 (τ=0.80)","name":"👴 [슬라이드 01] OpenVoice V2 | 중후한 할아버지 전래동화","desc":"실제 노년 남성 성우 음색(τ=0.80)을 강하게 이식한 중후하고 연륜 있는 할아버지 톤.","b64":to_b64(opt3),"duration":get_dur(opt3),"highlight":False},
        {"badge":"📻 원본 레퍼런스 육성","name":"👴 [참조] 실제 노년 성우 원본","desc":"OpenVoice V2가 음색 벡터를 추출한 기준 원음.","b64":to_b64(REF_GRANDFATHER),"duration":"02:30","highlight":False},
    ]

    tj = json.dumps(tracks, ensure_ascii=False)
    html = """<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>[송림야담] OpenVoice V2 노년 음색 이식 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#070a11;--card:rgba(18,25,42,.92);--ov:#8b5cf6;--accent:#f59e0b;--text:#f8fafc;--muted:#94a3b8;--border:rgba(255,255,255,.12);}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:radial-gradient(ellipse at 50% 0%,#1f1535 0%,#0d1117 55%,var(--bg) 100%);color:var(--text);font-family:'Pretendard',sans-serif;min-height:100vh;padding:48px 20px;display:flex;justify-content:center;}
.container{max-width:960px;width:100%;}
.header{text-align:center;margin-bottom:40px;}
.tag{display:inline-block;padding:7px 20px;background:rgba(139,92,246,.2);border:1px solid var(--ov);border-radius:999px;font-size:12px;font-weight:800;letter-spacing:1.8px;color:#c4b5fd;margin-bottom:16px;}
h1{font-family:'Noto Serif KR',serif;font-size:30px;font-weight:900;margin-bottom:14px;background:linear-gradient(135deg,#fff 0%,#c4b5fd 40%,var(--accent) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.4;}
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
  <div class="tag">🎙️ EDGE-TTS + OPENVOICE V2 · TONE COLOR CONVERSION</div>
  <h1>[송림야담] OpenVoice V2<br>실제 노년 음색 이식 청음실</h1>
  <p class="sub">실제 노년 성우 원음에서 추출한 <strong>음색 벡터(Tone Color SE)</strong>를<br>edge-tts 한국어 발음에 직접 이식합니다. 진짜 할머니·할아버지 목소리.</p>
</div>
<div class="pipe">
  <div class="ps"><div class="ico">🗣️</div><div class="lbl">edge-tts KR</div><div class="dsc">한국어 발음<br>억양 생성</div></div>
  <div class="arr">→</div>
  <div class="ps"><div class="ico">🎯</div><div class="lbl">OpenVoice V2</div><div class="dsc">노년 음색<br>벡터 이식</div></div>
  <div class="arr">→</div>
  <div class="ps"><div class="ico">🎚️</div><div class="lbl">EQ 마스터링</div><div class="dsc">흉성·숨결<br>아날로그 감성</div></div>
  <div class="arr">→</div>
  <div class="ps"><div class="ico">👵👴</div><div class="lbl">최종 음원</div><div class="dsc">진짜 노년<br>목소리</div></div>
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

    html_path = WORKSPACE / "output" / "slide01_openvoice_elderly_player.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"\n[DONE] 청음실: {html_path}")


if __name__ == "__main__":
    asyncio.run(main())


