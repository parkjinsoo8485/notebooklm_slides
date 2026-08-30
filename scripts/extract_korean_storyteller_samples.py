import sys
import io
import torchaudio
import soundfile as sf
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path("c:/My_Project/src/notebooklm_slides")
OUT_DIR = PROJECT_ROOT / "output" / "korean_storyteller_3to5s_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. test_sota_crystal_clean.wav (7.61s -> 3.8s 앞부분 한 문장 깔끔 클립)
# 문장: "마을의 장터는 이른 아침부터 모여든 사람들로 북적였고,"
data, sr = sf.read(str(PROJECT_ROOT / "test_sota_crystal_clean.wav"))
# 0초 ~ 4.2초 (장터 이야기 전반부)
clip1 = data[:int(4.2 * sr)]
sf.write(str(OUT_DIR / "01_storyteller_market_intro.wav"), clip1, sr)

# 2. songrim_clean_voice.wav 에서 3~5초 구간 추출
# 0.0s ~ 4.6s : "그 시절 우리네 어머니들은..." 또는 야담 첫 구절
data2, sr2 = sf.read(str(PROJECT_ROOT / "output/reference_voices/songrim_clean_voice.wav"))
# 24kHz 모노로 변환하여 저장
import torch
import torchaudio.transforms as T

tensor2 = torch.from_numpy(data2).float()
if tensor2.ndim == 1:
    tensor2 = tensor2.unsqueeze(0)
resampler = T.Resample(sr2, 24000)
tensor2_24k = resampler(tensor2)

# 세그먼트 A (0s ~ 4.5s)
clip_a = tensor2_24k[:, :int(4.5 * 24000)]
torchaudio.save(str(OUT_DIR / "02_songrim_yadam_opening_4.5s.wav"), clip_a, 24000)

# 세그먼트 B (5.0s ~ 9.2s -> 4.2초)
clip_b = tensor2_24k[:, int(5.0 * 24000):int(9.2 * 24000)]
torchaudio.save(str(OUT_DIR / "03_songrim_deep_narrative_4.2s.wav"), clip_b, 24000)

# 세그먼트 C (10.0s ~ 14.5s -> 4.5초)
clip_c = tensor2_24k[:, int(10.0 * 24000):int(14.5 * 24000)]
torchaudio.save(str(OUT_DIR / "04_songrim_emotional_flow_4.5s.wav"), clip_c, 24000)

print("Generated all 3~5s clips successfully in:", OUT_DIR)
