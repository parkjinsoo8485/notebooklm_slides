import sys
import os
import io

for stream_name in ('stdout', 'stderr'):
    stream = getattr(sys, stream_name)
    if hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    elif hasattr(stream, 'buffer'):
        setattr(sys, stream_name, io.TextIOWrapper(stream.buffer, encoding='utf-8', errors='replace'))

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import types
import warnings
import time
from pathlib import Path

warnings.filterwarnings("ignore")

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
GPT_SOVITS_DIR = WORKSPACE / "third_party" / "GPT-SoVITS"
PRETRAINED = GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models"

REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandfather_slice.wav"
ref_gpa_text = "여름이면 맨의 소리가 맨 맨 마을을 가득 채웠지"

GPT_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt")
SOVITS_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s2G2333k.pth")
if not Path(GPT_MODEL).exists():
    GPT_MODEL = str(PRETRAINED / "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt")
if not Path(SOVITS_MODEL).exists():
    SOVITS_MODEL = str(PRETRAINED / "s2G488k.pth")

# 1. torchaudio mocking
import importlib.machinery
def mock_torchaudio():
    if 'torchaudio' in sys.modules and getattr(sys.modules['torchaudio'], '__spec__', None) is not None:
        return
    mock = types.ModuleType('torchaudio')
    mock.__version__ = '2.4.1+cu124 (mocked)'
    mock.__file__ = 'MOCKED'
    mock.__spec__ = importlib.machinery.ModuleSpec(name='torchaudio', loader=None)
    for sub in ['torchaudio.transforms', 'torchaudio.functional', 'torchaudio.io', 'torchaudio.backend', 'torchaudio._extension', 'torchaudio.compliance']:
        mod = types.ModuleType(sub)
        mod.__spec__ = importlib.machinery.ModuleSpec(name=sub, loader=None)
        sys.modules[sub] = mod
    import soundfile as sf
    import torch
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
            if self.orig_freq == self.new_freq:
                return x
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

def mock_gradio():
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
            if item.startswith('__'): raise AttributeError(item)
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

def mock_eunjeon():
    if 'eunjeon' in sys.modules and getattr(sys.modules['eunjeon'], '__spec__', None) is not None:
        return
    m = types.ModuleType('eunjeon')
    m.__spec__ = importlib.machinery.ModuleSpec(name='eunjeon', loader=None, is_package=True)
    m.__spec__.submodule_search_locations = ['C:/mock/eunjeon']
    class MockMecab:
        def pos(self, string): return [(w, 'NNG') for w in string.split()]
    m.Mecab = MockMecab
    sys.modules['eunjeon'] = m

mock_torchaudio()
mock_gradio()
mock_eunjeon()

try:
    import jieba
    sys.modules['jieba_fast'] = jieba
except ImportError:
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

print("Loading GPT-SoVITS inference modules...")
t0 = time.time()
from tools.i18n.i18n import I18nAuto
i18n = I18nAuto()
from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language

change_gpt_weights(gpt_path=GPT_MODEL)
change_sovits_weights(sovits_path=SOVITS_MODEL)
ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))
print(f"Modules loaded in {time.time() - t0:.2f}s")

test_text = "살을 에는 비바람이 들이치는 차가운 흙바닥에 주저앉아, 마님은 피눈물을 삼키며 하염없이 흐느꼈습니다."
print(f"Testing inference with text: {test_text}")
t1 = time.time()
gen = get_tts_wav(
    ref_wav_path=str(REF_GRANDFATHER),
    prompt_text=ref_gpa_text,
    prompt_language=ko_lang,
    text=test_text,
    text_language=ko_lang,
    top_p=1.0,
    temperature=1.0,
)
results = list(gen)
t2 = time.time()
print(f"Inference completed in {t2 - t1:.2f}s!")
if results:
    sr, audio = results[-1]
    import soundfile as sf
    test_out = WORKSPACE / "output" / "temp_tts" / "test_gpa_sample.wav"
    test_out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(test_out), audio, sr)
    print(f"Saved test output to {test_out}, sr={sr}, shape={audio.shape}")
else:
    print("Failed to get audio results!")
