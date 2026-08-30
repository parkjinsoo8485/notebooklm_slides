import whisper
import warnings
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore')

model = whisper.load_model('base')
res = model.transcribe('test_sota_crystal_clean.wav', language='ko')
print('=== test_sota_crystal_clean.wav ===')
for seg in res['segments']:
    print(f"{seg['start']:.2f}s - {seg['end']:.2f}s ({seg['end']-seg['start']:.2f}s): {seg['text']}")

res2 = model.transcribe('output/reference_voices/songrim_clean_voice.wav', language='ko')
print('\n=== songrim_clean_voice.wav ===')
for seg in res2['segments']:
    print(f"{seg['start']:.2f}s - {seg['end']:.2f}s ({seg['end']-seg['start']:.2f}s): {seg['text']}")
