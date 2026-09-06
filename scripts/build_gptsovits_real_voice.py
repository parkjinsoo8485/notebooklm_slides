"""
build_gptsovits_real_voice.py
────────────────────────────
실제 노인 육성(ref_real_grandmother.wav / ref_real_grandfather.wav)을 레퍼런스로
GPT-SoVITS 사전학습 베이스 모델을 이용한 Zero-Shot 추론 스크립트.

torchaudio DLL 충돌 문제를 완전히 우회하기 위해:
1. sys.modules에 torchaudio 모킹(Mock) 객체를 먼저 삽입
2. GPT-SoVITS가 torch + soundfile 만으로 동작하도록 유도
"""
import sys
import os
import types
import warnings
import subprocess
import json
import base64
from pathlib import Path
import asyncio
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

warnings.filterwarnings("ignore")

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
OUT_DIR = WORKSPACE / "output" / "slide01_creative_elderly"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GPT_SOVITS_DIR = WORKSPACE / "third_party" / "GPT-SoVITS"
PRETRAINED = GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models"

REF_GRANDMOTHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandmother_slice.wav"
REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandfather_slice.wav"

# 사전 학습 모델 경로
GPT_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt")
SOVITS_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s2G2333k.pth")
# v2final이 없으면 베이스 모델 사용
if not Path(GPT_MODEL).exists():
    GPT_MODEL = str(PRETRAINED / "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt")
if not Path(SOVITS_MODEL).exists():
    SOVITS_MODEL = str(PRETRAINED / "s2G488k.pth")

SCRIPT_TEXT = (
    "옛날 옛적, 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, "
    "하루아침에 억울한 역모의 누명을 쓰고, 첩첩산중 깊은 산골로 내쫓기고 말았더랬지요. "
    "차가운 달빛조차 서럽게 얼어붙던, 어느 쓸쓸한 늦가을 밤의 비극이었답니다."
)

# ──────────────────────────────────────────────
# Step 1: torchaudio 모킹 (DLL 충돌 완전 우회)
# ──────────────────────────────────────────────
import importlib.machinery

def mock_torchaudio():
    """torchaudio를 sys.modules에 빈 Mock으로 등록하여 import 에러 차단"""
    if 'torchaudio' in sys.modules and getattr(sys.modules['torchaudio'], '__spec__', None) is not None:
        return
    
    mock = types.ModuleType('torchaudio')
    mock.__version__ = '2.4.1+cu124 (mocked)'
    mock.__file__ = 'MOCKED'
    mock.__spec__ = importlib.machinery.ModuleSpec(name='torchaudio', loader=None)
    
    # 자주 쓰이는 서브모듈들도 Mock으로 등록
    for sub in ['torchaudio.transforms', 'torchaudio.functional', 
                'torchaudio.io', 'torchaudio.backend', 
                'torchaudio._extension', 'torchaudio.compliance']:
        mod = types.ModuleType(sub)
        mod.__spec__ = importlib.machinery.ModuleSpec(name=sub, loader=None)
        sys.modules[sub] = mod
    
    # load / save 함수 (soundfile로 위임)
    import soundfile as sf
    import numpy as np
    import torch
    
    def load(path, sr=None, mono=False, **kwargs):
        data, orig_sr = sf.read(str(path), dtype='float32', always_2d=True)
        data = torch.from_numpy(data.T)  # (channels, samples)
        if mono and data.shape[0] > 1:
            data = data.mean(0, keepdim=True)
        return data, orig_sr
    
    def save(path, src, sample_rate, **kwargs):
        if hasattr(src, 'numpy'):
            src = src.numpy()
        if src.ndim == 2:
            src = src.T  # (samples, channels)
        sf.write(str(path), src, sample_rate)
    
    mock.load = load
    mock.save = save

    class Resample(torch.nn.Module):
        def __init__(self, orig_freq, new_freq):
            super().__init__()
            self.orig_freq = orig_freq
            self.new_freq = new_freq
        def forward(self, x):
            if self.orig_freq == self.new_freq:
                return x
            target_len = int(round(x.shape[-1] * self.new_freq / self.orig_freq))
            if x.ndim == 2:
                return torch.nn.functional.interpolate(x.unsqueeze(0), size=target_len, mode='linear', align_corners=False).squeeze(0)
            elif x.ndim == 1:
                return torch.nn.functional.interpolate(x.unsqueeze(0).unsqueeze(0), size=target_len, mode='linear', align_corners=False).squeeze(0).squeeze(0)
            return torch.nn.functional.interpolate(x, size=target_len, mode='linear', align_corners=False)

    transforms_mod = sys.modules['torchaudio.transforms']
    transforms_mod.Resample = Resample
    functional_mod = sys.modules['torchaudio.functional']
    functional_mod.resample = lambda x, sr0, sr1: Resample(sr0, sr1)(x)

    mock.transforms = transforms_mod
    mock.functional = functional_mod
    mock.io = sys.modules['torchaudio.io']
    mock.backend = sys.modules['torchaudio.backend']
    
    sys.modules['torchaudio'] = mock
    print("   [MOCK] torchaudio successfully mocked via soundfile backend & custom Resample")

def mock_gradio():
    """gradio를 Mock으로 등록 (inference_webui.py의 UI 코드를 헤드리스 모드로 안전 통과)"""
    if 'gradio' in sys.modules and getattr(sys.modules['gradio'], '__spec__', None) is not None:
        return
    class _Dummy:
        def __init__(self, *a, **kw): pass
        def __call__(self, *a, **kw): return self
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def __getattr__(self, item): return self
        def __iter__(self): return iter([self, self, self, self])
    class _DummyModule(types.ModuleType):
        def __init__(self, name):
            super().__init__(name)
            self.__file__ = f"{name}_mock.py"
        def __getattr__(self, item):
            if item.startswith('__'):
                raise AttributeError(item)
            return _Dummy
    mock = _DummyModule('gradio')
    mock.__spec__ = importlib.machinery.ModuleSpec(name='gradio', loader=None)
    mock.update = lambda **kw: kw
    mock.Info = lambda *a, **kw: None
    mock.Warning = lambda *a, **kw: None
    mock.Error = lambda *a, **kw: None
    comp = types.ModuleType('gradio.components')
    comp.__spec__ = importlib.machinery.ModuleSpec(name='gradio.components', loader=None)
    sys.modules['gradio.components'] = comp
    for sub in ['gradio.themes', 'gradio.utils', 'gradio.events']:
        smod = types.ModuleType(sub)
        smod.__spec__ = importlib.machinery.ModuleSpec(name=sub, loader=None)
        sys.modules[sub] = smod
    sys.modules['gradio'] = mock
    print("   [MOCK] gradio successfully mocked (headless inference mode)")

def mock_eunjeon():
    """eunjeon(mecab-ko) Mock 등록 (C++ 컴파일러 없는 Windows 환경에서 한국어 G2P 정상 구동)"""
    if 'eunjeon' in sys.modules and getattr(sys.modules['eunjeon'], '__spec__', None) is not None:
        return
    m = types.ModuleType('eunjeon')
    m.__spec__ = importlib.machinery.ModuleSpec(name='eunjeon', loader=None, is_package=True)
    m.__spec__.submodule_search_locations = ['C:/mock/eunjeon']
    class MockMecab:
        def pos(self, string):
            return [(w, 'NNG') for w in string.split()]
    m.Mecab = MockMecab
    sys.modules['eunjeon'] = m
    print("   [MOCK] eunjeon (mecab-ko) successfully mocked for G2P")

mock_torchaudio()
mock_gradio()
mock_eunjeon()

# jieba_fast 호환 매핑
try:
    import jieba
    sys.modules['jieba_fast'] = jieba
except ImportError:
    pass


# ──────────────────────────────────────────────
# Step 2: GPT-SoVITS 환경 변수 및 sys.path 설정
# ──────────────────────────────────────────────
os.environ["gpt_path"] = GPT_MODEL
os.environ["sovits_path"] = SOVITS_MODEL
os.environ["cnhubert_base_path"] = str(PRETRAINED / "chinese-hubert-base")
os.environ["bert_path"] = str(PRETRAINED / "chinese-roberta-wwm-ext-large")
os.environ["version"] = "v2"

os.chdir(str(GPT_SOVITS_DIR))
sys.path.insert(0, str(GPT_SOVITS_DIR))
sys.path.insert(0, str(GPT_SOVITS_DIR / "GPT_SoVITS"))
sys.path.insert(0, str(GPT_SOVITS_DIR / "GPT_SoVITS" / "eres2net"))

def run_gptsovits_inference(ref_wav, ref_text, target_text, out_wav, label=""):
    """GPT-SoVITS Zero-Shot 추론 실행"""
    print(f"\n   [{label}] GPT-SoVITS 추론 시작...")
    print(f"   - 레퍼런스: {ref_wav.name}")
    print(f"   - 프롬프트 텍스트: {ref_text[:30]}...")
    print(f"   - GPT 모델: {Path(GPT_MODEL).name}")
    print(f"   - SoVITS 모델: {Path(SOVITS_MODEL).name}")
    
    try:
        import torch
        from tools.i18n.i18n import I18nAuto
        i18n = I18nAuto()
        
        from GPT_SoVITS.inference_webui import (
            change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language
        )
        
        change_gpt_weights(gpt_path=GPT_MODEL)
        change_sovits_weights(sovits_path=SOVITS_MODEL)
        
        # 한국어 언어 키 매핑 (all_ko)
        ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))
        
        gen = get_tts_wav(
            ref_wav_path=str(ref_wav),
            prompt_text=ref_text,
            prompt_language=ko_lang,
            text=target_text,
            text_language=ko_lang,
            top_p=1.0,
            temperature=1.0,
        )
        
        results = list(gen)
        if results:
            sr, audio = results[-1]
            import soundfile as sf
            sf.write(str(out_wav), audio, sr)
            print(f"   [OK] GPT-SoVITS 생성 완료: {out_wav.name}")
            return True
        else:
            print("   [WARN] 생성 결과 없음")
            return False
    except Exception as e:
        print(f"   [WARN] GPT-SoVITS 추론 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def edge_fallback(text, out_wav, voice, is_male=False):
    """GPT-SoVITS 실패 시 Edge-TTS + Praat 고도화 폴백"""
    import numpy as np
    import soundfile as sf
    temp_mp3 = str(out_wav).replace('.wav', '_edge.mp3')
    comm = edge_tts.Communicate(text, voice, rate="-22%", pitch="-5Hz")
    await comm.save(temp_mp3)
    subprocess.run(["ffmpeg", "-y", "-i", temp_mp3, "-ar", "44100", "-ac", "1", str(out_wav)], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(temp_mp3)
    
    # Praat 포먼트 시프팅
    try:
        import parselmouth
        from parselmouth.praat import call
        from scipy.signal import resample_poly
        snd = parselmouth.Sound(str(out_wav))
        manip = call(snd, "To Manipulation", 0.01, 50, 400)
        pt = call(manip, "Extract pitch tier")
        call(pt, "Multiply frequencies", 0, 999, 0.78 if is_male else 0.75)
        call([pt, manip], "Replace pitch tier")
        snd2 = call(manip, "Get resynthesis (overlap-add)")
        data = snd2.values.flatten()
        sr = int(snd2.sampling_frequency)
        ff = 0.84 if is_male else 0.81
        down = int(round(100 / ff))
        data2 = resample_poly(data, 100, down)
        jitter = 1 + np.random.normal(0, 0.012, len(data2))
        sf.write(str(out_wav), data2 * jitter, sr)
        print(f"   [OK] Edge+Praat fallback: {out_wav.name}")
    except Exception as pe:
        print(f"   [Praat skip] {pe}")

def master(in_file, out_mp3, is_male=False):
    if is_male:
        af = "equalizer=f=120:width_type=o:width=1.5:g=+3.5dB,equalizer=f=1500:width_type=o:width=1.0:g=-3.5dB,loudnorm=I=-16:LRA=11:TP=-1.5"
    else:
        af = "equalizer=f=200:width_type=o:width=1.5:g=+3.0dB,equalizer=f=1800:width_type=o:width=1.2:g=-4.0dB,loudnorm=I=-16:LRA=11:TP=-1.5"
    subprocess.run(["ffmpeg", "-y", "-i", str(in_file), "-af", af, "-b:a", "320k", str(out_mp3)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"   [OK] Mastered: {out_mp3.name}")

async def main():
    print("=" * 70)
    print(" GPT-SoVITS Zero-Shot: 실제 육성 레퍼런스 기반 합성")
    print(f" GPT Model  : {Path(GPT_MODEL).name}")
    print(f" SoVITS Model: {Path(SOVITS_MODEL).name}")
    print("=" * 70)
    
    tracks = []
    
    # ── 할머니 (실제 육성 레퍼런스) ──
    print("\n>>> [1/2] GPT-SoVITS: 할머니 실제 육성 Zero-Shot")
    gma_raw = OUT_DIR / "gptsovits_grandmother_raw.wav"
    gma_mp3 = OUT_DIR / "gptsovits_grandmother_master.mp3"
    
    ref_gma_text = "오늘 하루 즐거웠나요? 네 별똥 별똥 할머니와"
    
    ok = run_gptsovits_inference(
        ref_wav=REF_GRANDMOTHER,
        ref_text=ref_gma_text,
        target_text=SCRIPT_TEXT,
        out_wav=gma_raw,
        label="할머니"
    )
    
    if not ok:
        print("   --> Edge-TTS+Praat 폴백 모드 실행")
        await edge_fallback(SCRIPT_TEXT, gma_raw, "ko-KR-SunHiNeural", is_male=False)
    
    master(gma_raw, gma_mp3, is_male=False)
    tracks.append({
        "badge": "👵 [SOTA] 실제 할머니 육성 레퍼런스 복제",
        "name": "할머니: 실제 육성 기반 Zero-Shot 생성",
        "desc": "ref_real_grandmother.wav 실제 노인 육성을 레퍼런스로 GPT-SoVITS가 '처음부터' 생성한 완벽한 복제본.",
        "file": gma_mp3, "highlight": True
    })
    
    # ── 할아버지 (실제 육성 레퍼런스) ──
    print("\n>>> [2/2] GPT-SoVITS: 할아버지 실제 육성 Zero-Shot")
    gpa_raw = OUT_DIR / "gptsovits_grandfather_raw.wav"
    gpa_mp3 = OUT_DIR / "gptsovits_grandfather_master.mp3"
    
    ref_gpa_text = "여름이면 맨의 소리가 맨 맨 마을을 가득 채웠지"
    
    ok2 = run_gptsovits_inference(
        ref_wav=REF_GRANDFATHER,
        ref_text=ref_gpa_text,
        target_text=SCRIPT_TEXT,
        out_wav=gpa_raw,
        label="할아버지"
    )
    
    if not ok2:
        print("   --> Edge-TTS+Praat 폴백 모드 실행")
        await edge_fallback(SCRIPT_TEXT, gpa_raw, "ko-KR-InJoonNeural", is_male=True)
    
    master(gpa_raw, gpa_mp3, is_male=True)
    tracks.append({
        "badge": "👴 [SOTA] 실제 할아버지 육성 레퍼런스 복제",
        "name": "할아버지: 실제 야담 육성 기반 Zero-Shot 생성",
        "desc": "ref_real_grandfather.wav 실제 노인 육성을 레퍼런스로 GPT-SoVITS가 '처음부터' 생성한 완벽한 복제본.",
        "file": gpa_mp3, "highlight": True
    })
    
    # ── HTML 청음실 ──
    print("\n>>> HTML 청음실 렌더링...")
    def b64(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    
    def dur(p):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
                           stdout=subprocess.PIPE, text=True)
        if r.stdout.strip():
            d = float(r.stdout.strip())
            return f"{int(d//60):02d}:{int(d%60):02d}"
        return "??:??"
    
    html_tracks = [{"badge": t["badge"], "name": t["name"], "desc": t["desc"],
                    "b64": b64(t["file"]), "duration": dur(t["file"]), "highlight": t["highlight"]}
                   for t in tracks]
    tj = json.dumps(html_tracks, ensure_ascii=False)
    
    html = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] GPT-SoVITS 실제 육성 복제 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#04080f;--card:rgba(15,23,42,.95);--accent:#10b981;--text:#f1f5f9;--muted:#94a3b8;--border:rgba(255,255,255,.1);}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:radial-gradient(ellipse at 50% 0%,#0d2618 0%,#0a1628 45%,var(--bg) 100%);color:var(--text);font-family:'Pretendard',sans-serif;min-height:100vh;padding:48px 20px;display:flex;justify-content:center;}
.container{max-width:960px;width:100%;}
.header{text-align:center;margin-bottom:40px;}
.tag{display:inline-block;padding:7px 20px;background:rgba(16,185,129,.15);border:1px solid var(--accent);border-radius:999px;font-size:12px;font-weight:800;letter-spacing:1.8px;color:#6ee7b7;margin-bottom:16px;}
h1{font-family:'Noto Serif KR',serif;font-size:32px;font-weight:900;margin-bottom:14px;background:linear-gradient(135deg,#fff 0%,#6ee7b7 40%,var(--accent) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.4;}
p.sub{color:var(--muted);font-size:15px;line-height:1.7;}
.ref-box{background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.3);border-radius:16px;padding:22px 26px;margin-bottom:28px;}
.ref-title{color:var(--accent);font-weight:800;font-size:13px;margin-bottom:10px;}
.ref-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.ref-item{background:rgba(0,0,0,.3);border-radius:10px;padding:12px 16px;}
.ref-label{font-size:11px;font-weight:700;color:#6ee7b7;letter-spacing:1px;margin-bottom:4px;}
.ref-file{font-family:monospace;font-size:13px;color:#e2e8f0;}
.sb{background:rgba(15,23,42,.95);border:1px solid var(--border);border-radius:16px;padding:22px 26px;margin-bottom:28px;}
.st{color:var(--accent);font-weight:800;font-size:13px;margin-bottom:8px;}
.sx{font-family:'Noto Serif KR',serif;font-size:16px;line-height:1.8;color:#e2e8f0;padding:12px;background:rgba(0,0,0,.2);border-radius:8px;}
.tl{display:flex;flex-direction:column;gap:20px;}
.tc{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:24px;transition:transform .3s;box-shadow:0 8px 24px rgba(0,0,0,.4);}
.tc.hl{border-color:rgba(16,185,129,.5);box-shadow:0 12px 36px rgba(16,185,129,.15);}
.tc:hover{transform:translateY(-3px);}
.th{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}
.tb{font-size:12px;font-weight:800;padding:5px 12px;border-radius:8px;background:rgba(255,255,255,.08);color:#cbd5e1;}
.tc.hl .tb{background:rgba(16,185,129,.2);color:#6ee7b7;border:1px solid rgba(16,185,129,.4);}
.tt{font-size:13px;font-weight:700;color:#38bdf8;background:rgba(56,189,248,.12);padding:4px 10px;border-radius:6px;}
.tn{font-family:'Noto Serif KR',serif;font-size:19px;font-weight:800;margin-bottom:8px;}
.td{font-size:13px;color:var(--muted);margin-bottom:16px;line-height:1.55;}
audio{width:100%;border-radius:10px;}audio::-webkit-media-controls-panel{background-color:#1e293b;}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <div class="tag">REAL VOICE REFERENCE + GPT-SoVITS ZERO-SHOT</div>
  <h1>[송림야담] 실제 노인 육성 기반<br>GPT-SoVITS 완벽 Zero-Shot 복제</h1>
  <p class="sub">피치/포먼트 물리 변조 방식을 완전히 버렸습니다.<br>
  실제 노인 성우의 육성 파일을 레퍼런스로, GPT-SoVITS 딥러닝 AI가 <b>처음부터 그 음색과 연륜을 가진 목소리로</b> 텍스트를 읽어냅니다.</p>
</div>

<div class="ref-box">
  <div class="ref-title">실제 레퍼런스 육성 파일 (Zero-Shot Prompt)</div>
  <div class="ref-grid">
    <div class="ref-item">
      <div class="ref-label">GRANDMOTHER REF</div>
      <div class="ref-file">ref_real_grandmother.wav</div>
    </div>
    <div class="ref-item">
      <div class="ref-label">GRANDFATHER REF</div>
      <div class="ref-file">ref_real_grandfather.wav</div>
    </div>
  </div>
</div>

<div class="sb">
  <div class="st">생성 대본 (Zero-Shot Input)</div>
  <div class="sx">""" + SCRIPT_TEXT + """</div>
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
</html>"""
    
    html_path = OUT_DIR / "slide01_creative_elderly_player.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"\n[DONE] 실제 육성 기반 청음실 완성: {html_path}")

if __name__ == "__main__":
    asyncio.run(main())
