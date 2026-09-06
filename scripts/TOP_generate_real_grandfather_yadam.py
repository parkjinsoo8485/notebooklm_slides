#!/usr/bin/env python3
"""
TOP_generate_real_grandfather_yadam.py
───────────────────────────────────────
[송림야담 공식 TOP 1] 실제 야담 명인 할아버지 육성 GPT-SoVITS 마스터 생성 엔진
- 가슴을 울리는 깊은 흉성과 70대 할아버지의 구수한 사투리/억양이 비극적 서사에 몰입감을 극대화
- 저작권: 실제 야담 명인 육성 (Public Archive / 자유 이용)
- 레퍼런스: ref_real_grandfather_slice.wav ("여름이면 맨의 소리가 맨 맨 마을을 가득 채웠지")
- 스튜디오 DSP: 120Hz 흉성 보강(+3.5dB), 1500Hz 비음 감쇠(-3.5dB), 방송 표준 -16 LUFS

사용법:
  # 1번 슬라이드 생성:
  python scripts/TOP_generate_real_grandfather_yadam.py --slides 1

  # 특정 범위 (예: 1~10번) 생성:
  python scripts/TOP_generate_real_grandfather_yadam.py --slides 1-10

  # 120개 전편 일괄 생성:
  python scripts/TOP_generate_real_grandfather_yadam.py --slides all
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
OUT_AUDIO.mkdir(parents=True, exist_ok=True)
SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

SLIDES_DATA_PATH = WORKSPACE / "output" / "slides_data.json"

# 공식 할아버지 레퍼런스 및 DSP 스펙
REF_GRANDFATHER = AUDIO_SAMPLES_DIR / "ref_real_grandfather.wav"
if not REF_GRANDFATHER.exists():
    REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandfather_slice.wav"

REF_PROMPT_TEXT = "여름이면 맨의 소리가 맨 맨 마을을 가득 채웠지"
MASTER_DSP = "equalizer=f=120:width_type=o:width=1.5:g=+3.5dB,equalizer=f=1500:width_type=o:width=1.0:g=-3.5dB,loudnorm=I=-16:LRA=11:TP=-1.5"

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
    parser = argparse.ArgumentParser(description="TOP Generate Songrim Yadam with Real Grandfather Voice")
    parser.add_argument("--slides", default="1", help="Target slides: '1', '1-10', or 'all'")
    args = parser.parse_args()

    print("=" * 80)
    print("👴 [TOP] 실제 야담 할아버지 육성 마스터 생성 엔진 가동")
    print(f"📌 레퍼런스 : {REF_GRANDFATHER.name}")
    print(f"📌 프롬프트 : '{REF_PROMPT_TEXT}'")
    print(f"📌 대상슬라이드 : {args.slides}")
    print("=" * 80)

    from tools.i18n.i18n import I18nAuto
    i18n = I18nAuto()
    from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language

    change_gpt_weights(gpt_path=GPT_MODEL)
    change_sovits_weights(sovits_path=SOVITS_MODEL)
    ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))
    print("✅ GPT-SoVITS 할아버지 신경망 로드 완료!\n")

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

        temp_wav = TEMP_DIR / f"raw_gpa_slide_{idx:03d}.wav"
        final_mp3 = OUT_AUDIO / f"slide_{idx:03d}.mp3"
        srt_file = SUBTITLES_DIR / f"slide_{idx:03d}.srt"

        t_s = time.time()
        print(f"[{idx:03d}/{len(slides):03d}] 👴 생성 중 ({len(target_text)}자): {target_text[:32]}...")

        try:
            gen = get_tts_wav(
                ref_wav_path=str(REF_GRANDFATHER),
                prompt_text=REF_PROMPT_TEXT,
                prompt_language=ko_lang,
                text=target_text,
                text_language=ko_lang,
                top_p=0.95,
                temperature=0.85
            )
            results = list(gen)
            if not results:
                raise RuntimeError("GPT-SoVITS 생성 실패")

            sr, audio = results[-1]
            sf.write(str(temp_wav), audio, sr)

            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_wav),
                "-af", MASTER_DSP,
                "-b:a", "320k",
                str(final_mp3)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            if temp_wav.exists(): temp_wav.unlink()

            dur = get_audio_duration(final_mp3)
            slide["audio_duration"] = round(dur, 3)
            slide["audio_path"] = f"output/audio/slide_{idx:03d}.mp3"
            slide["subtitle_path"] = f"output/subtitles/slide_{idx:03d}.srt"
            generate_srt(raw_script, dur, srt_file)

            el = time.time() - t_s
            print(f"[{idx:03d}] ✅ 할아버지 육성 마스터 생성 완료 ({el:.1f}s | 길이: {dur:.1f}s)")

        except Exception as e:
            print(f"[{idx:03d}] ❌ 에러: {e}")
            import traceback; traceback.print_exc()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    with open(SLIDES_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(slides, f, ensure_ascii=False, indent=2)

    total_el = time.time() - t0
    print("\n" + "=" * 80)
    print(f"🎉 모든 요청 슬라이드 생성 완료! (총 소요 시간: {total_el:.1f}s)")
    print("=" * 80)

    # 통합 플레이어 갱신
    subprocess.run([sys.executable, str(WORKSPACE / "scripts" / "create_full_player.py")], check=True, cwd=str(WORKSPACE))
    print("✨ full_story_player.html 갱신 완료!")

if __name__ == "__main__":
    main()
