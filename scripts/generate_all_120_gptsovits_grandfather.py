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
import re
import json
import subprocess
from pathlib import Path
import soundfile as sf
import torch

warnings.filterwarnings("ignore")

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(WORKSPACE / "scripts"))
from korean_phonetic_normalizer import normalize_phonetics_for_tts

GPT_SOVITS_DIR = WORKSPACE / "third_party" / "GPT-SoVITS"
PRETRAINED = GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models"

OUT_DIR = WORKSPACE / "output"
AUDIO_DIR = OUT_DIR / "audio"
SUBTITLES_DIR = OUT_DIR / "subtitles"
TEMP_DIR = OUT_DIR / "temp_tts"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

SLIDES_DATA_PATH = OUT_DIR / "slides_data.json"

REF_GRANDFATHER = WORKSPACE / "output" / "human_voice_showcase" / "ref_real_grandfather_slice.wav"
REF_GPA_TEXT = "여름이면 맨의 소리가 맨 맨 마을을 가득 채웠지"

GPT_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt")
SOVITS_MODEL = str(PRETRAINED / "gsv-v2final-pretrained" / "s2G2333k.pth")
if not Path(GPT_MODEL).exists():
    GPT_MODEL = str(PRETRAINED / "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt")
if not Path(SOVITS_MODEL).exists():
    SOVITS_MODEL = str(PRETRAINED / "s2G488k.pth")

# ──────────────────────────────────────────────
# Step 1: torchaudio, gradio, eunjeon 모킹
# ──────────────────────────────────────────────
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

print("=" * 80)
print("👴 [송림야담] 전체 120개 슬라이드 GPT-SoVITS 실제 할아버지 육성 복제 일괄 생성")
print(f"📌 GPT 모델   : {Path(GPT_MODEL).name}")
print(f"📌 SoVITS 모델: {Path(SOVITS_MODEL).name}")
print(f"📌 레퍼런스    : {REF_GRANDFATHER.name}")
print("=" * 80)

from tools.i18n.i18n import I18nAuto
i18n = I18nAuto()
from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, get_tts_wav, dict_language

change_gpt_weights(gpt_path=GPT_MODEL)
change_sovits_weights(sovits_path=SOVITS_MODEL)
ko_lang = next((k for k, v in dict_language.items() if v == "all_ko"), i18n("韩文"))
print("✅ GPT-SoVITS 엔진 및 모델 로드 완료!")

def clean_script_for_tts(text: str) -> str:
    """불필요한 쉼표/말줄임표 파편화를 정리하여 자연스러운 한 호흡 낭독으로 정돈"""
    t = re.sub(r'\s*,\s*\.\.\.\s*', ', ', text)
    t = re.sub(r'\s*\.\.\.\s*', '... ', t)
    t = re.sub(r'\.{3,}', '...', t)
    t = re.sub(r',\s*,+', ',', t)
    t = re.sub(r',\s*$', '.', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

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
            s = int(sec % 60)
            ms = int((sec - int(sec)) * 1000)
            return f"00:{m:02d}:{s:02d},{ms:03d}"
            
        cues.append(f"{i+1}\n{format_ts(start_t)} --> {format_ts(end_t)}\n{s}\n")
        
    srt_path.write_text("\n".join(cues), encoding="utf-8")

# 마스터링 DSP (할아버지 흉성 +3.5dB @120Hz, 거친 고음/비음 감쇠 -3.5dB @1500Hz, 표준음압 -16 LUFS)
MASTER_DSP = "equalizer=f=120:width_type=o:width=1.5:g=+3.5dB,equalizer=f=1500:width_type=o:width=1.0:g=-3.5dB,loudnorm=I=-16:LRA=11:TP=-1.5"

with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
    slides = json.load(f)

total_slides = len(slides)
print(f"🎬 총 {total_slides}개 슬라이드 배치 생성 시작...\n")

start_time_all = time.time()
success_count = 0

for i, slide in enumerate(slides, 1):
    idx = int(slide["slide_index"])
    raw_script = slide.get("voice_script", "")
    target_text = slide.get("phonetic_script") or normalize_phonetics_for_tts(clean_script_for_tts(raw_script))
    
    temp_wav = TEMP_DIR / f"raw_gpa_slide_{idx:03d}.wav"
    final_mp3 = AUDIO_DIR / f"slide_{idx:03d}.mp3"
    srt_file = SUBTITLES_DIR / f"slide_{idx:03d}.srt"

    # --force 가 없고 파일이 존재하면 스킵 (하지만 이번엔 GPT-SoVITS로 전면 전환이므로 force 적용)
    if "--force" not in sys.argv and final_mp3.exists() and False:
        print(f"[{idx:03d}/{total_slides:03d}] ⏩ 스킵: {target_text[:30]}...")
        success_count += 1
        continue
        
    slide["phonetic_script"] = target_text
    
    t_slide_start = time.time()
    print(f"[{idx:03d}/{total_slides:03d}] 👴 경음화/발음규칙 적용 생성 중... ({len(target_text)}자): {target_text[:32]}...")
    
    try:
        gen = get_tts_wav(
            ref_wav_path=str(REF_GRANDFATHER),
            prompt_text=REF_GPA_TEXT,
            prompt_language=ko_lang,
            text=target_text,
            text_language=ko_lang,
            top_p=1.0,
            temperature=1.0,
        )
        results = list(gen)
        if not results:
            raise RuntimeError("GPT-SoVITS generator returned empty results")
        
        sr, audio = results[-1]
        sf.write(str(temp_wav), audio, sr)
        
        # FFmpeg 스튜디오 마스터링 적용
        subprocess.run([
            "ffmpeg", "-y", "-i", str(temp_wav),
            "-af", MASTER_DSP,
            "-b:a", "320k",
            str(final_mp3)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        if temp_wav.exists():
            temp_wav.unlink()
            
        dur = get_audio_duration(final_mp3)
        slide["audio_duration"] = round(dur, 3)
        slide["audio_path"] = f"output/audio/slide_{idx:03d}.mp3"
        slide["subtitle_path"] = f"output/subtitles/slide_{idx:03d}.srt"
        
        generate_srt(raw_script, dur, srt_file)
        
        elapsed = time.time() - t_slide_start
        print(f"[{idx:03d}/{total_slides:03d}] ✅ 생성 성공 ({elapsed:.1f}s | 오디오 길이: {dur:.1f}s)")
        success_count += 1
        
    except Exception as e:
        print(f"[{idx:03d}/{total_slides:03d}] ❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        
    # GPU VRAM 캐시 주기적 정리
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    # 5개마다 진행상황 중간 저장
    if idx % 5 == 0 or idx == total_slides:
        with open(SLIDES_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(slides, f, ensure_ascii=False, indent=2)
        avg_time = (time.time() - start_time_all) / idx
        remain_time = avg_time * (total_slides - idx)
        print(f"   💾 [체크포인트] {idx}/{total_slides} 완료 | 남은 예상 시간: 약 {int(remain_time // 60)}분 {int(remain_time % 60)}초")

# 최종 메타데이터 동기화 저장
with open(SLIDES_DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(slides, f, ensure_ascii=False, indent=2)

total_elapsed = time.time() - start_time_all
print("\n" + "=" * 80)
print(f"🎉 [완료] 전체 120개 슬라이드 할아버지 복제 음성 생성 종료!")
print(f"📊 성공률: {success_count}/{total_slides} (총 소요 시간: {int(total_elapsed // 60)}분 {int(total_elapsed % 60)}초)")
print("=" * 80)

# 통합 플레이어 갱신
print("\n🌐 통합 청음 플레이어(full_story_player.html) 갱신 중...")
subprocess.run([sys.executable, str(WORKSPACE / "scripts" / "create_full_player.py")], check=True, cwd=str(WORKSPACE))
print("✨ full_story_player.html 갱신 완료!")
