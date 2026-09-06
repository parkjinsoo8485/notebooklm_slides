#!/usr/bin/env python3
"""
TOP_generate_folklore_storyteller_yadam.py
──────────────────────────────────────────
[송림야담 공식 TOP] 전통 야담 구연가 (구수한 판소리 완급 조절) GPT-SoVITS 낭독 생성 엔진
- 사투리 억양과 구전 야담 특유의 리듬감이 살아 숨 쉬는 우리 민족 고유의 전기수 낭독 톤
- 저작권: 한국구비문학대계 설화 아카이브 (한국학중앙연구원 - 공공누리 제1유형 출처표시)
- 레퍼런스: ref_folklore_storyteller.wav ("마을의 장터는 이른 아침부터 모여든 사람들로 북적였고")
- 스튜디오 DSP: 150Hz 중저음 리듬감 보강(+2.5dB), 2200Hz 치찰음 완화(-2.5dB), 방송 표준 -16 LUFS

사용법:
  # 1번 슬라이드 생성 (기본값):
  python scripts/TOP_generate_folklore_storyteller_yadam.py
  python scripts/TOP_generate_folklore_storyteller_yadam.py --slides 1

  # 특정 범위 (예: 1~10번) 생성:
  python scripts/TOP_generate_folklore_storyteller_yadam.py --slides 1-10

  # 120개 전편 일괄 생성:
  python scripts/TOP_generate_folklore_storyteller_yadam.py --slides all
"""

import sys, os, io, json, re, types, warnings, subprocess, argparse, time
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
AUDIO_SAMPLES_DIR = MASTER_DIR / "audio_samples"
AUDIO_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

OUT_AUDIO = WORKSPACE / "output" / "audio"
SUBTITLES_DIR = WORKSPACE / "output" / "subtitles"
TEMP_DIR = WORKSPACE / "output" / "temp_tts"
PUBLIC_DIR = WORKSPACE / "output" / "public_voices_slide01"
OUT_AUDIO.mkdir(parents=True, exist_ok=True)
SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

SLIDES_DATA_PATH = WORKSPACE / "output" / "slides_data.json"

# 공식 전통 야담 구연가 레퍼런스 및 DSP 스펙
REF_STORYTELLER = AUDIO_SAMPLES_DIR / "ref_folklore_storyteller.wav"
if not REF_STORYTELLER.exists():
    fallback = WORKSPACE / "output" / "korean_storyteller_3to5s_samples" / "sample1_storyteller_intro_4.4s.wav"
    if fallback.exists():
        import shutil
        shutil.copyfile(fallback, REF_STORYTELLER)

REF_PROMPT_TEXT = "마을의 장터는 이른 아침부터 모여든 사람들로 북적였고"
MASTER_DSP = "equalizer=f=150:width_type=o:width=1.3:g=+2.5dB,equalizer=f=2200:width_type=o:width=1.0:g=-2.5dB,loudnorm=I=-16:LRA=11:TP=-1.5"

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

def get_audio_duration(file_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 15.0

def generate_srt(text: str, duration: float, srt_path: Path):
    sentences = re.split(r'(?<=[.!?…])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        sentences = [text.strip()]
    
    total_chars = sum(len(s) for s in sentences)
    cues = []
    current_time = 0.0
    
    for i, s in enumerate(sentences):
        ratio = len(s) / total_chars if total_chars > 0 else 1.0 / len(sentences)
        dur = duration * ratio
        start_t = current_time
        end_t = start_t + dur if i < len(sentences) - 1 else duration
        current_time = end_t
        
        def format_ts(sec):
            m = int(sec // 60)
            s_val = int(sec % 60)
            ms = int((sec - int(sec)) * 1000)
            return f"00:{m:02d}:{s_val:02d},{ms:03d}"
            
        cues.append(f"{i+1}\n{format_ts(start_t)} --> {format_ts(end_t)}\n{s}\n")
        
    srt_path.write_text("\n".join(cues), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="TOP Generate Songrim Yadam with Folklore Storyteller Voice")
    parser.add_argument("--slides", default="1", help="Target slides: '1', '1-10', or 'all' (default: 1)")
    args = parser.parse_args()

    print("=" * 80)
    print("📜 [TOP] 전통 야담 구연가 (구수한 판소리 완급 조절) 마스터 생성 엔진 가동")
    print(f"⚖️  저작권 : 한국구비문학대계 설화 아카이브 (공공누리 제1유형 출처표시)")
    print(f"📌 레퍼런스 : {REF_STORYTELLER.name}")
    print(f"📌 프롬프트 : '{REF_PROMPT_TEXT}'")
    print(f"📌 대상슬라이드 : {args.slides}")
    print("=" * 80)

    from tools.i18n.i18n import I18nAuto
    i18n = I18nAuto()
    from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language

    change_gpt_weights(gpt_path=GPT_MODEL)
    change_sovits_weights(sovits_path=SOVITS_MODEL)
    ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))
    print("✅ GPT-SoVITS 구연가 신경망 로드 완료!\n")

    with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)

    if args.slides == "all":
        target_indices = [s["slide_index"] for s in slides]
    elif "-" in args.slides:
        start, end = map(int, args.slides.split("-"))
        target_indices = list(range(start, end + 1))
    else:
        target_indices = [int(args.slides)]

    t0 = time.time()
    for idx in target_indices:
        slide = next((s for s in slides if s["slide_index"] == idx), None)
        if not slide: continue

        raw_script = slide.get("voice_script", "")
        target_text = slide.get("phonetic_script") or normalize_phonetics_for_tts(raw_script)

        temp_wav = TEMP_DIR / f"raw_storyteller_slide_{idx:03d}.wav"
        final_mp3 = OUT_AUDIO / f"slide_{idx:03d}_storyteller.mp3"
        srt_file = SUBTITLES_DIR / f"slide_{idx:03d}_storyteller.srt"

        # 1번 슬라이드의 경우 공식 쇼케이스 및 마스터 샘플 경로에도 동시 저장
        sample_master_mp3 = AUDIO_SAMPLES_DIR / "sample_slide01_folklore_storyteller.mp3"
        showcase_mp3 = PUBLIC_DIR / "slide01_4_classic_storyteller.mp3"

        t_s = time.time()
        print(f"🎬 [슬라이드 {idx:03d}] 생성 중... (글자수: {len(target_text)}자)")
        print(f"   - 대본: {raw_script[:45]}...")

        # 1. GPT-SoVITS 추론
        tts_gen = get_tts_wav(
            ref_wav_path=str(REF_STORYTELLER),
            prompt_text=REF_PROMPT_TEXT,
            prompt_language=ko_lang,
            text=target_text,
            text_language=ko_lang,
            how_to_cut=i18n("凑四句一切"),
            top_k=15,
            top_p=1.0,
            temperature=1.0,
            ref_free=False,
            speed=1.0,
            if_freeze=False,
            inp_refs=None
        )

        sr, audio_data = next(tts_gen)
        sf.write(str(temp_wav), audio_data, sr)

        # 2. 고품질 스튜디오 DSP 필터링 및 MP3 인코딩
        cmd = [
            "ffmpeg", "-y", "-i", str(temp_wav),
            "-af", MASTER_DSP,
            "-ar", "44100", "-b:a", "192k",
            str(final_mp3)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 슬라이드 1번 추가 저장 (마스터 샘플 & 쇼케이스)
        if idx == 1:
            import shutil
            shutil.copyfile(str(final_mp3), str(sample_master_mp3))
            shutil.copyfile(str(final_mp3), str(showcase_mp3))
            print(f"   ⭐ [공식 마스터 샘플 동시 갱신] -> {sample_master_mp3.name}")

        # 3. SRT 자막 동기화
        duration = get_audio_duration(final_mp3)
        generate_srt(raw_script, duration, srt_file)

        elapsed = time.time() - t_s
        print(f"   ✨ 완료! 길이: {duration:.1f}초 (소요: {elapsed:.1f}초) -> {final_mp3.name}\n")

    total_elapsed = time.time() - t0
    print("=" * 80)
    print(f"🎉 전통 야담 구연가 생성 작업 완료! (총 소요 시간: {total_elapsed:.1f}초)")
    print(f"📁 결과 오디오 디렉터리: {OUT_AUDIO}")
    if 1 in target_indices:
        print(f"🎧 슬라이드 1번 공식 마스터 음원: {sample_master_mp3}")
    print("=" * 80)

if __name__ == "__main__":
    main()
