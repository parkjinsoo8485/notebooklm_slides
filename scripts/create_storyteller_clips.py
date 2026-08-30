import sys
import io
import torch
import torchaudio
import torchaudio.transforms as T
import soundfile as sf
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path("c:/My_Project/src/notebooklm_slides")
OUT_DIR = PROJECT_ROOT / "output" / "korean_storyteller_3to5s_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. songrim_clean_voice.wav 로드 및 24kHz 변환
src_path = PROJECT_ROOT / "output/reference_voices/songrim_clean_voice.wav"
data, sr = torchaudio.load(str(src_path))
if data.shape[0] > 1:
    data = torch.mean(data, dim=0, keepdim=True)
if sr != 24000:
    data = T.Resample(sr, 24000)(data)
sr = 24000

# Sample 1: "자, 그럼 오늘도 감동적인 옛날 이야기, 지금 바로 시작합니다." (48.0s ~ 54.6s -> 약 4.8초)
# Whisper 확인: 48.0s ~ 54.5s
s1 = data[:, int(48.0 * sr) : int(54.4 * sr)]
torchaudio.save(str(OUT_DIR / "sample1_storyteller_intro_4.4s.wav"), s1, sr)

# Sample 2: "그 여인을 내놓아라. 그럼 네 빚 문서를 이 자리에서 찢어주마." (0.0s ~ 5.9s -> 4.5초)
s2 = data[:, int(0.6 * sr) : int(5.8 * sr)]
torchaudio.save(str(OUT_DIR / "sample2_yadam_drama_4.2s.wav"), s2, sr)

# Sample 3: "옛날 옛적 한양에서 그리 멀지 않은 양주 땅 변두리에 만석이라는 농부가 살았습니다." (54.7s ~ 62.0s -> 약 4.8초 분할)
s3 = data[:, int(54.7 * sr) : int(59.5 * sr)]
torchaudio.save(str(OUT_DIR / "sample3_classic_folklore_4.8s.wav"), s3, sr)

# 2. test_sota_crystal_clean.wav 로드 (선비 이야기 도입)
src2_path = PROJECT_ROOT / "test_sota_crystal_clean.wav"
data2, sr2 = torchaudio.load(str(src2_path))
if data2.shape[0] > 1:
    data2 = torch.mean(data2, dim=0, keepdim=True)
if sr2 != 24000:
    data2 = T.Resample(sr2, 24000)(data2)

# Sample 4: "한양 땅에서 과거를 보러 가던 이 선비는" (0.0s ~ 3.8s)
s4 = data2[:, : int(3.9 * 24000)]
torchaudio.save(str(OUT_DIR / "sample4_scholar_journey_3.9s.wav"), s4, 24000)

print(f"Successfully generated 4 pristine 3~5s storyteller samples in {OUT_DIR}:")
for f in OUT_DIR.glob("*.wav"):
    dur = torchaudio.info(str(f)).num_frames / 24000
    print(f" - {f.name}: {dur:.2f}s (24,000Hz WAV)")
