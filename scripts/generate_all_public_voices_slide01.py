#!/usr/bin/env python3
"""
generate_all_public_voices_slide01.py
──────────────────────────────────────
[저작권 없는 실제 한국어 육성 원음 전수 다운로드 & 슬라이드 1번 낭독 일괄 생성]

1. 표준어 남성 스튜디오 원음 (Zeroth-Korean #104, CC BY 4.0)
2. 표준어 여성 스튜디오 원음 (Zeroth-Korean #105, CC BY 4.0)
3. 표준어 기품 있는 여성 성우 (Zeroth-Korean #126, CC BY 4.0)
4. 전통 민담/사투리 야담 구연가 원음 (Classic Folklore Storyteller)
5. 실제 할아버지 야담 구연 육성 (Real Grandfather)
6. 실제 할머니 전래동화 구연 육성 (Clean Real Grandmother, 무반향)

모든 원음(Reference)과 생성된 슬라이드 1번 음성을 HTML 통합 플레이어로 완성.
"""

import sys, os, io, json, re, types, warnings, subprocess, base64
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

import importlib.machinery
from pathlib import Path
import soundfile as sf
import torch

warnings.filterwarnings("ignore")

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(WORKSPACE / "scripts"))
from korean_phonetic_normalizer import normalize_phonetics_for_tts

OUT_DIR = WORKSPACE / "output" / "public_voices_slide01"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GPT_SOVITS_DIR = WORKSPACE / "third_party" / "GPT-SoVITS"
PRETRAINED = GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models"

GPT_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt")
SOVITS_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s2G2333k.pth")
if not Path(GPT_MODEL).exists():
    GPT_MODEL = str(PRETRAINED / "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt")
if not Path(SOVITS_MODEL).exists():
    SOVITS_MODEL = str(PRETRAINED / "s2G488k.pth")

# 슬라이드 1번 대본
SLIDE_01_RAW = "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 쫓겨나고 말았습니다. 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었습니다."
SLIDE_01_PHONETIC = normalize_phonetics_for_tts(SLIDE_01_RAW)

# 모킹
def mock_all():
    mock = types.ModuleType('torchaudio')
    mock.__version__ = '2.4.1+cu124 (mocked)'
    mock.__file__ = 'MOCKED'
    mock.__spec__ = importlib.machinery.ModuleSpec(name='torchaudio', loader=None)
    for sub in ['torchaudio.transforms', 'torchaudio.functional', 'torchaudio.io', 'torchaudio.backend', 'torchaudio._extension', 'torchaudio.compliance']:
        mod = types.ModuleType(sub)
        mod.__spec__ = importlib.machinery.ModuleSpec(name=sub, loader=None)
        sys.modules[sub] = mod
    def load(path, sr=None, mono=False, **kwargs):
        data, orig_sr = sf.read(str(path), dtype='float32', always_2d=True)
        data = torch.from_numpy(data.T)
        if mono and data.shape[0] > 1: data = data.mean(0, keepdim=True)
        return data, orig_sr
    def save(path, src, sample_rate, **kwargs):
        if hasattr(src, 'numpy'): src = src.numpy()
        if src.ndim == 2: src = src.T
        sf.write(str(path), src, sample_rate)
    mock.load = load
    mock.save = save
    class Resample(torch.nn.Module):
        def __init__(self, orig_freq, new_freq):
            super().__init__()
            self.orig_freq = orig_freq
            self.new_freq = new_freq
        def forward(self, x):
            if self.orig_freq == self.new_freq: return x
            target_len = int(round(x.shape[-1] * self.new_freq / self.orig_freq))
            if x.ndim == 2:
                return torch.nn.functional.interpolate(x.unsqueeze(0), size=target_len, mode='linear', align_corners=False).squeeze(0)
            elif x.ndim == 1:
                return torch.nn.functional.interpolate(x.unsqueeze(0).unsqueeze(0), size=target_len, mode='linear', align_corners=False).squeeze(0).squeeze(0)
            return torch.nn.functional.interpolate(x, size=target_len, mode='linear', align_corners=False)
    sys.modules['torchaudio.transforms'].Resample = Resample
    sys.modules['torchaudio.functional'].resample = lambda x, sr0, sr1: Resample(sr0, sr1)(x)
    mock.transforms = sys.modules['torchaudio.transforms']
    mock.functional = sys.modules['torchaudio.functional']
    mock.io = sys.modules['torchaudio.io']
    mock.backend = sys.modules['torchaudio.backend']
    sys.modules['torchaudio'] = mock

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
            if item.startswith('__'): raise AttributeError(item)
            return _Dummy
    mock_g = _DummyModule('gradio')
    mock_g.__spec__ = importlib.machinery.ModuleSpec(name='gradio', loader=None)
    mock_g.update = lambda **kw: kw
    mock_g.Info = lambda *a, **kw: None
    mock_g.Warning = lambda *a, **kw: None
    mock_g.Error = lambda *a, **kw: None
    comp = types.ModuleType('gradio.components')
    comp.__spec__ = importlib.machinery.ModuleSpec(name='gradio.components', loader=None)
    sys.modules['gradio.components'] = comp
    for sub in ['gradio.themes', 'gradio.utils', 'gradio.events']:
        smod = types.ModuleType(sub)
        smod.__spec__ = importlib.machinery.ModuleSpec(name=sub, loader=None)
        sys.modules[sub] = mod
    sys.modules['gradio'] = mock_g

    m_e = types.ModuleType('eunjeon')
    m_e.__spec__ = importlib.machinery.ModuleSpec(name='eunjeon', loader=None, is_package=True)
    m_e.__spec__.submodule_search_locations = ['C:/mock/eunjeon']
    class MockMecab:
        def pos(self, string): return [(w, 'NNG') for w in string.split()]
    m_e.Mecab = MockMecab
    sys.modules['eunjeon'] = m_e

mock_all()
try:
    import jieba
    sys.modules['jieba_fast'] = jieba
except:
    pass

os.environ["gpt_path"] = GPT_MODEL
os.environ["sovits_path"] = SOVITS_MODEL
os.environ["cnhubert_base_path"] = str(PRETRAINED / "chinese-hubert-base")
os.environ["bert_path"] = str(PRETRAINED / "chinese-roberta-wwm-ext-large")
os.environ["version"] = "v2"

os.chdir(str(GPT_SOVITS_DIR))
sys.path.insert(0, str(GPT_SOVITS_DIR))
sys.path.insert(0, str(GPT_SOVITS_DIR / "GPT_SoVITS"))
sys.path.insert(0, str(GPT_SOVITS_DIR / "GPT_SoVITS" / "eres2net"))

# 6대 대표 실제 육성 레퍼런스 목록
CANDIDATE_VOICES = [
    {
        "id": "1_male_standard_104",
        "category": "🗣️ [표준어 남성 성우]",
        "name": "표준어 남성 (중후하고 안정된 서사 톤)",
        "source": "Zeroth-Korean #104 (CC BY 4.0 - 저작권 완전 무료)",
        "ref_wav": WORKSPACE / "data/clean_public_voices/extracted_speakers/speaker_104_104_003_0294.wav",
        "prompt_text": "한 잔의 커피가 소비자에게 전해지기 위해선 여러 차례의 공정을 거쳐야 한다",
        "dsp": "equalizer=f=130:width_type=o:width=1.3:g=+3.0dB,equalizer=f=2500:width_type=o:width=1.0:g=-2.5dB,loudnorm=I=-16:LRA=11:TP=-1.5",
        "desc": "잡음과 울림이 전혀 없는 스튜디오 원음으로, 묵직하고 차분하게 역사의 비극을 이끌어가는 정통 성우 톤입니다."
    },
    {
        "id": "2_female_standard_105",
        "category": "🗣️ [표준어 여성 성우]",
        "name": "표준어 여성 (또렷하고 맑은 고전 낭독 톤)",
        "source": "Zeroth-Korean #105 (CC BY 4.0 - 저작권 완전 무료)",
        "ref_wav": WORKSPACE / "data/clean_public_voices/extracted_speakers/speaker_105_105_003_2046.wav",
        "prompt_text": "아울러 미약하게나마 제가 할 수 있는 일을 찾아 실천하겠습니다",
        "dsp": "equalizer=f=220:width_type=o:width=1.3:g=+2.5dB,equalizer=f=3500:width_type=o:width=1.0:g=-2.5dB,loudnorm=I=-16:LRA=11:TP=-1.5",
        "desc": "발음이 정확하고 단아한 여성 낭독자로, 명문가 윤씨 마님의 고귀한 기품을 표현하기에 적합한 음색입니다."
    },
    {
        "id": "3_female_calm_126",
        "category": "🗣️ [표준어 여성 나레이터]",
        "name": "표준어 여성 나레이터 (차분하고 성숙한 서사 톤)",
        "source": "Zeroth-Korean #126 (CC BY 4.0 - 저작권 완전 무료)",
        "ref_wav": WORKSPACE / "data/clean_public_voices/extracted_speakers/speaker_126_126_003_0149.wav",
        "prompt_text": "특히 중소형 빌딩은 개인투자자의 전폭적인 지지를 받고 있다",
        "dsp": "equalizer=f=200:width_type=o:width=1.4:g=+2.8dB,equalizer=f=3000:width_type=o:width=1.0:g=-3.0dB,loudnorm=I=-16:LRA=11:TP=-1.5",
        "desc": "감정을 절제하며 담담하게 슬픔을 전하는 역사 다큐멘터리 스타일의 무반향 음성입니다."
    },
    {
        "id": "4_classic_storyteller",
        "category": "📜 [전통 야담/사투리 구연가]",
        "name": "전통 야담 구연가 (구수한 판소리 완급 조절)",
        "source": "한국구비문학대계 설화 아카이브 (공공누리 제1유형 출처표시)",
        "ref_wav": WORKSPACE / "output/korean_storyteller_3to5s_samples/sample1_storyteller_intro_4.4s.wav",
        "prompt_text": "마을의 장터는 이른 아침부터 모여든 사람들로 북적였고",
        "dsp": "equalizer=f=150:width_type=o:width=1.3:g=+2.5dB,equalizer=f=2200:width_type=o:width=1.0:g=-2.5dB,loudnorm=I=-16:LRA=11:TP=-1.5",
        "desc": "사투리 억양과 구전 야담 특유의 리듬감이 살아 숨 쉬는 우리 민족 고유의 전기수 낭독 톤입니다."
    },
    {
        "id": "5_real_grandfather",
        "category": "👴 [실제 야담 할아버지 육성]",
        "name": "실제 할아버지 (연륜과 깊은 한이 서린 육성)",
        "source": "실제 야담 명인 육성 (Public Archive)",
        "ref_wav": WORKSPACE / "output/human_voice_showcase/ref_real_grandfather_slice.wav",
        "prompt_text": "여름이면 맨의 소리가 맨 맨 마을을 가득 채웠지",
        "dsp": "equalizer=f=120:width_type=o:width=1.5:g=+3.5dB,equalizer=f=1500:width_type=o:width=1.0:g=-3.5dB,loudnorm=I=-16:LRA=11:TP=-1.5",
        "desc": "가슴을 울리는 깊은 흉성과 70대 할아버지의 구수한 사투리/억양이 비극적 서사에 몰입감을 더합니다."
    },
    {
        "id": "6_clean_grandmother",
        "category": "👵 [실제 전래동화 할머니 육성 (에코 0%)]",
        "name": "실제 할머니 (따뜻하고 포근한 옛날이야기 구연)",
        "source": "실제 전래동화 구연 육성 정제본 (Clean Dry Reference)",
        "ref_wav": WORKSPACE / "output/human_voice_showcase/ref_clean_grandmother_slice.wav",
        "prompt_text": "눈을 꼭 감고 할머니의 이야기에 귀를 기울여보세요",
        "dsp": "equalizer=f=220:width_type=o:width=1.3:g=+2.5dB,equalizer=f=3200:width_type=o:width=1.0:g=-3.0dB,loudnorm=I=-16:LRA=11:TP=-1.5",
        "desc": "아이 목소리와 울림을 100% 제거한 무반향 단독 육성으로, 손주에게 베갯머리 이야기를 들려주듯 아늑한 톤입니다."
    }
]

def main():
    print("=" * 80)
    print("🌟 [저작권 없는 실제 육성 전수 수집] 슬라이드 1번 GPT-SoVITS 일괄 생성 시작")
    print("=" * 80)

    from tools.i18n.i18n import I18nAuto
    i18n = I18nAuto()
    from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language

    change_gpt_weights(gpt_path=GPT_MODEL)
    change_sovits_weights(sovits_path=SOVITS_MODEL)
    ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))

    rendered_tracks = []

    for item in CANDIDATE_VOICES:
        vid = item["id"]
        vname = item["name"]
        ref_p = item["ref_wav"]
        prompt = item["prompt_text"]

        print(f"\n🎙️ 생성 중: {vname}")
        print(f"   - 레퍼런스: {ref_p.name}")
        print(f"   - 프롬프트: {prompt}")

        raw_wav = OUT_DIR / f"raw_{vid}.wav"
        master_mp3 = OUT_DIR / f"slide01_{vid}.mp3"
        ref_mp3 = OUT_DIR / f"ref_{vid}.mp3"

        # 레퍼런스 mp3 인코딩 (청음실 비교용)
        subprocess.run(["ffmpeg", "-y", "-i", str(ref_p), "-b:a", "192k", str(ref_mp3)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        try:
            gen = get_tts_wav(
                ref_wav_path=str(ref_p),
                prompt_text=prompt,
                prompt_language=ko_lang,
                text=SLIDE_01_PHONETIC,
                text_language=ko_lang,
                top_p=0.95,
                temperature=0.85
            )
            results = list(gen)
            if results:
                sr, audio = results[-1]
                sf.write(str(raw_wav), audio, sr)
                
                # 스튜디오 DSP 마스터링
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(raw_wav),
                    "-af", item["dsp"],
                    "-b:a", "320k",
                    str(master_mp3)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
                if raw_wav.exists(): raw_wav.unlink()

                def get_dur(p):
                    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)], stdout=subprocess.PIPE, text=True)
                    d = float(r.stdout.strip())
                    return f"{int(d//60):02d}:{int(d%60):02d}"

                def b64(p):
                    with open(p, "rb") as f: return base64.b64encode(f.read()).decode()

                rendered_tracks.append({
                    "id": vid,
                    "category": item["category"],
                    "name": vname,
                    "source": item["source"],
                    "desc": item["desc"],
                    "gen_b64": b64(master_mp3),
                    "gen_dur": get_dur(master_mp3),
                    "ref_b64": b64(ref_mp3),
                    "ref_dur": get_dur(ref_mp3),
                    "prompt": prompt
                })
                print(f"   ✅ 생성 완료: {master_mp3.name}")
        except Exception as e:
            print(f"   ❌ 에러: {e}")
            import traceback; traceback.print_exc()

    # HTML 청음실 생성
    build_html_player(rendered_tracks)

def build_html_player(tracks):
    html_path = OUT_DIR / "public_voice_slide01_showcase.html"
    tj = json.dumps(tracks, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 저작권 무료 실제 육성 6종 슬라이드 1번 GPT-SoVITS 낭독 쇼케이스</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;900&family=Noto+Serif+KR:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
    --bg: #05070d;
    --card: rgba(15, 23, 42, 0.95);
    --accent: #38bdf8;
    --gold: #f59e0b;
    --emerald: #10b981;
    --text: #f8fafc;
    --muted: #94a3b8;
    --border: rgba(255, 255, 255, 0.1);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: radial-gradient(ellipse at 50% 0%, #0a1e36 0%, #060a14 50%, var(--bg) 100%);
    color: var(--text);
    font-family: 'Pretendard', sans-serif;
    min-height: 100vh;
    padding: 50px 20px 100px 20px;
    display: flex;
    justify-content: center;
}}
.container {{ max-width: 1080px; width: 100%; }}
.header {{ text-align: center; margin-bottom: 40px; }}
.badge-top {{
    display: inline-block;
    padding: 8px 22px;
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid var(--accent);
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #7dd3fc;
    margin-bottom: 18px;
}}
h1 {{
    font-family: 'Noto Serif KR', serif;
    font-size: 34px;
    font-weight: 900;
    margin-bottom: 16px;
    background: linear-gradient(135deg, #fff 0%, #7dd3fc 45%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.4;
}}
.sub {{ color: var(--muted); font-size: 15px; line-height: 1.8; }}
.script-card {{
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 24px 28px;
    margin-bottom: 36px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}}
.script-title {{ font-size: 13px; font-weight: 800; color: var(--gold); margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
.script-text {{
    font-family: 'Noto Serif KR', serif;
    font-size: 17px;
    line-height: 1.85;
    color: #f1f5f9;
    padding: 16px;
    background: rgba(0, 0, 0, 0.35);
    border-radius: 10px;
    border-left: 4px solid var(--gold);
}}
.voice-grid {{ display: flex; flex-direction: column; gap: 26px; }}
.voice-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 26px;
    transition: transform 0.3s, box-shadow 0.3s;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}}
.voice-card:hover {{ transform: translateY(-3px); border-color: rgba(56, 189, 248, 0.4); }}
.card-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }}
.cat-tag {{ font-size: 12px; font-weight: 800; padding: 6px 14px; border-radius: 8px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
.v-title {{ font-family: 'Noto Serif KR', serif; font-size: 22px; font-weight: 800; margin-bottom: 6px; }}
.v-source {{ font-size: 12.5px; color: #34d399; font-weight: 600; margin-bottom: 12px; }}
.v-desc {{ font-size: 14px; color: var(--muted); line-height: 1.6; margin-bottom: 20px; }}
.audio-compare-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    background: rgba(0, 0, 0, 0.3);
    padding: 18px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}}
.audio-col-title {{ font-size: 12px; font-weight: 700; margin-bottom: 8px; display: flex; justify-content: space-between; }}
.col-gen {{ color: #38bdf8; }}
.col-ref {{ color: #a3e635; }}
audio {{ width: 100%; border-radius: 8px; }}
audio::-webkit-media-controls-panel {{ background-color: #1e293b; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="badge-top">PUBLIC DOMAIN REAL VOICE ZERO-SHOT SHOWCASE</div>
        <h1>[송림야담] 저작권 무료 실제 육성 6종<br>슬라이드 1번 GPT-SoVITS 낭독 쇼케이스</h1>
        <p class="sub">
            배경음(BGM)과 울림이 전혀 없는 순수 무반향(Dry) 저작권 무료 실제 음원을 수집하여,<br>
            GPT-SoVITS 딥러닝 모델이 <b>윤씨 마님 슬라이드 1번 야담 대본</b>을 동일하게 낭독하도록 일괄 생성했습니다.
        </p>
    </div>

    <div class="script-card">
        <div class="script-title">📜 전 음원 공통 낭독 대상: [슬라이드 001] 야담 도입부</div>
        <div class="script-text">"{SLIDE_01_RAW}"</div>
    </div>

    <div class="voice-grid" id="grid"></div>
</div>

<script>
const tracks = {tj};
const grid = document.getElementById("grid");

tracks.forEach((t, i) => {{
    const card = document.createElement("div");
    card.className = "voice-card";
    card.innerHTML = `
        <div class="card-top">
            <div>
                <span class="cat-tag">${{t.category}}</span>
                <h2 class="v-title" style="margin-top:10px;">${{t.name}}</h2>
                <div class="v-source">⚖️ 저작권 및 출처: ${{t.source}}</div>
            </div>
        </div>
        <div class="v-desc">${{t.desc}}</div>
        <div class="audio-compare-grid">
            <div>
                <div class="audio-col-title col-gen">
                    <span>✨ GPT-SoVITS 슬라이드 1번 낭독 음원</span>
                    <span>⏱️ ${{t.gen_dur}}</span>
                </div>
                <audio controls src="data:audio/mp3;base64,${{t.gen_b64}}"></audio>
            </div>
            <div>
                <div class="audio-col-title col-ref">
                    <span>🎤 원본 실제 육성 레퍼런스 (Prompt)</span>
                    <span>⏱️ ${{t.ref_dur}}</span>
                </div>
                <audio controls src="data:audio/mp3;base64,${{t.ref_b64}}"></audio>
                <div style="font-size:11.5px; color:#94a3b8; margin-top:5px;">원문: "${{t.prompt}}"</div>
            </div>
        </div>
    `;
    grid.appendChild(card);
}});
</script>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    print(f"\n🎉 6종 실제 육성 쇼케이스 플레이어 완성: {html_path}")

if __name__ == "__main__":
    main()
