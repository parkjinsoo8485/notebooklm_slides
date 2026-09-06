import whisper
import warnings
warnings.filterwarnings('ignore')

model = whisper.load_model('base')
res = model.transcribe('output/human_voice_showcase/03_elderly_grandfather_folklore.mp3', language='ko')
print("=== 트랙 02 원본 할아버지 육성 내용 (전체 전사) ===")
for seg in res['segments']:
    print(f"[{seg['start']:.1f}s ~ {seg['end']:.1f}s] {seg['text']}")
