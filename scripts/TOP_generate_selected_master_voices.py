#!/usr/bin/env python3
"""
generate_selected_master_voices.py
───────────────────────────────────
선택된 2대 공식 마스터 보이스 전용 생성 엔진
1. folklore_storyteller : 전통 야담 구연가 (사투리/판소리 완급 조절)
2. standard_male_104    : 표준어 남성 (중후한 정통 역사 성우)

사용법:
  python scripts/generate_selected_master_voices.py --voice standard_male_104 --slides 1-10
  python scripts/generate_selected_master_voices.py --voice folklore_storyteller --slides all
"""

import sys, os, io, json, re, types, warnings, subprocess, argparse
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

MASTER_DIR = WORKSPACE / "master_voice_standard"
SPEC_FILE = MASTER_DIR / "selected_master_voices.json"

with open(SPEC_FILE, "r", encoding="utf-8") as f:
    SPEC = json.load(f)["voices"]

OUT_AUDIO = WORKSPACE / "output" / "audio"
TEMP_DIR = WORKSPACE / "output" / "temp_tts"
OUT_AUDIO.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

GPT_SOVITS_DIR = WORKSPACE / "third_party" / "GPT-SoVITS"
PRETRAINED = GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models"

GPT_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt")
SOVITS_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s2G2333k.pth")
if not Path(GPT_MODEL).exists():
    GPT_MODEL = str(PRETRAINED / "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt")
if not Path(SOVITS_MODEL).exists():
    SOVITS_MODEL = str(PRETRAINED / "s2G488k.pth")

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

def main():
    parser = argparse.ArgumentParser(description="Generate audios using approved master voices")
    parser.add_argument("--voice", choices=["folklore_storyteller", "standard_male_104"], default="standard_male_104", help="Selected master voice ID")
    parser.add_argument("--slides", default="1", help="Slide range (e.g., '1', '1-5', 'all')")
    args = parser.parse_args()

    vinfo = SPEC[args.voice]
    ref_audio = WORKSPACE / "master_voice_standard" / vinfo["ref_audio"]
    prompt_text = vinfo["prompt_text"]
    dsp_filter = vinfo["dsp_filter"]

    print("=" * 80)
    print(f"🎙️ [선택 마스터 보이스] {vinfo['name']}")
    print(f"   - 레퍼런스: {ref_audio.name}")
    print(f"   - 프롬프트: '{prompt_text}'")
    print(f"   - 대상 슬라이드: {args.slides}")
    print("=" * 80)

    from tools.i18n.i18n import I18nAuto
    i18n = I18nAuto()
    from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language

    change_gpt_weights(gpt_path=GPT_MODEL)
    change_sovits_weights(sovits_path=SOVITS_MODEL)
    ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))

    with open(WORKSPACE / "output" / "slides_data.json", "r", encoding="utf-8") as f:
        slides = json.load(f)

    if args.slides == "all":
        target_indices = [s["slide_index"] for s in slides]
    elif "-" in args.slides:
        start, end = map(int, args.slides.split("-"))
        target_indices = list(range(start, end + 1))
    else:
        target_indices = [int(args.slides)]

    for idx in target_indices:
        slide = next((s for s in slides if s["slide_index"] == idx), None)
        if not slide: continue

        text = slide.get("phonetic_script") or normalize_phonetics_for_tts(slide.get("voice_script", ""))
        print(f"\n[{idx:03d}] 생성 중: {text[:35]}...")

        temp_wav = TEMP_DIR / f"temp_{args.voice}_{idx:03d}.wav"
        final_mp3 = OUT_AUDIO / f"slide_{idx:03d}.mp3"

        gen = get_tts_wav(
            ref_wav_path=str(ref_audio),
            prompt_text=prompt_text,
            prompt_language=ko_lang,
            text=text,
            text_language=ko_lang,
            top_p=0.95,
            temperature=0.85
        )
        results = list(gen)
        if results:
            sr, audio = results[-1]
            sf.write(str(temp_wav), audio, sr)

            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_wav),
                "-af", dsp_filter,
                "-b:a", "320k",
                str(final_mp3)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            if temp_wav.exists(): temp_wav.unlink()
            print(f"[{idx:03d}] ✅ 생성 및 마스터링 완료: {final_mp3.name}")

    print("\n🎉 모든 요청 슬라이드 생성 완료!")

if __name__ == "__main__":
    main()
