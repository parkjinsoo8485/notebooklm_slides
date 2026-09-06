#!/usr/bin/env python3
"""
generate_slide01_clean_grandmother.py
──────────────────────────────────────
할머니 실제 육성 중 아이 대답 및 배경 소음이 섞이지 않은
순수 무반향(Dry) 구간(ref_clean_grandmother_slice.wav)을 레퍼런스로 사용하여
마이크 에코/하울링이 완전히 제거된 슬라이드 1번 GPT-SoVITS 음원 생성
"""
import sys, os, io, types, warnings, subprocess
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

OUT_DIR = WORKSPACE / "output" / "slide01_creative_elderly"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GPT_SOVITS_DIR = WORKSPACE / "third_party" / "GPT-SoVITS"
PRETRAINED = GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models"

REF_CLEAN_GMA = WORKSPACE / "output" / "human_voice_showcase" / "ref_clean_grandmother_slice.wav"
REF_CLEAN_TEXT = "눈을 꼭 감고 할머니의 이야기에 귀를 기울여보세요"

GPT_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt")
SOVITS_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s2G2333k.pth")
if not Path(GPT_MODEL).exists():
    GPT_MODEL = str(PRETRAINED / "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt")
if not Path(SOVITS_MODEL).exists():
    SOVITS_MODEL = str(PRETRAINED / "s2G488k.pth")

# 슬라이드 1번 문장부호 정밀 보완 및 표준 발음 반영 대본
SLIDE_01_RAW = "옛날 옛적... 한양 북촌 명문가의 어질고 고왔던 윤씨 마님이, 하루아침에 억울한 역모의 누명을 쓰고... 첩첩산중 깊은 산골로 쫓겨나고 말았습니다. 차가운 달빛조차 서럽게 얼어붙던... 어느 쓸쓸한 늦가을 밤의 비극이었습니다."
SLIDE_01_PHONETIC = normalize_phonetics_for_tts(SLIDE_01_RAW)

def mock_all():
    # torchaudio mock
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
        if mono and data.shape[0] > 1:
            data = data.mean(0, keepdim=True)
        return data, orig_sr
    def save(path, src, sample_rate, **kwargs):
        if hasattr(src, 'numpy'):
            src = src.numpy()
        if src.ndim == 2:
            src = src.T
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

    # gradio mock
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
        sys.modules[sub] = smod
    sys.modules['gradio'] = mock_g

    # eunjeon mock
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
    print("=" * 75)
    print("👵 [에코 제거] 실제 할머니 육성 슬라이드 1번 깨끗한 Zero-Shot 합성")
    print(f"📌 레퍼런스: {REF_CLEAN_GMA.name}")
    print(f"📌 프롬프트: '{REF_CLEAN_TEXT}'")
    print(f"📌 발음대본: '{SLIDE_01_PHONETIC}'")
    print("=" * 75)

    from tools.i18n.i18n import I18nAuto
    i18n = I18nAuto()
    from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language
    
    change_gpt_weights(gpt_path=GPT_MODEL)
    change_sovits_weights(sovits_path=SOVITS_MODEL)
    ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))

    raw_wav = OUT_DIR / "gptsovits_clean_grandmother_slide01_raw.wav"
    clean_mp3 = OUT_DIR / "gptsovits_clean_grandmother_slide01_master.mp3"

    gen = get_tts_wav(
        ref_wav_path=str(REF_CLEAN_GMA),
        prompt_text=REF_CLEAN_TEXT,
        prompt_language=ko_lang,
        text=SLIDE_01_PHONETIC,
        text_language=ko_lang,
        top_p=0.95,
        temperature=0.85,
    )
    results = list(gen)
    if not results:
        raise RuntimeError("GPT-SoVITS 생성 실패!")
    
    sr, audio = results[-1]
    sf.write(str(raw_wav), audio, sr)
    print(f"✅ 원본 생성 성공: {raw_wav.name} (sr={sr})")

    # 깨끗한 스튜디오 EQ (마이크 에코/하울링 없는 따뜻한 음색)
    # 중저음 따스함 +2.5dB @220Hz, 거친 고역 치찰음/하울링 완화 -3.0dB @3200Hz, 표준 라우드니스
    CLEAN_DSP = "equalizer=f=220:width_type=o:width=1.3:g=+2.5dB,equalizer=f=3200:width_type=o:width=1.0:g=-3.0dB,highshelf=f=7000:g=-3.0,loudnorm=I=-16:LRA=11:TP=-1.5"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(raw_wav),
        "-af", CLEAN_DSP,
        "-b:a", "320k",
        str(clean_mp3)
    ], check=True)
    print(f"🎉 에코 없는 깨끗한 마스터 완성: {clean_mp3.name}")

    # 또한 slide01_creative_elderly_player.html 에도 즉시 반영되도록 update 스크립트 연결
    # gptsovits_grandmother_master.mp3 파일도 깨끗한 버전으로 덮어쓰기
    target_orig = OUT_DIR / "gptsovits_grandmother_master.mp3"
    import shutil
    shutil.copyfile(clean_mp3, target_orig)
    print(f"💾 청음실용 gptsovits_grandmother_master.mp3 업데이트 완료!")

    subprocess.run([sys.executable, str(WORKSPACE / "scripts" / "update_creative_elderly_player.py")], check=True, cwd=str(WORKSPACE))
    print(f"✨ slide01_creative_elderly_player.html 갱신 완료!")

if __name__ == "__main__":
    main()
