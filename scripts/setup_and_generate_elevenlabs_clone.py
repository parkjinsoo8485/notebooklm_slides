"""
setup_and_generate_elevenlabs_clone.py
──────────────────────────────────────
ElevenLabs API를 통해 원본 음성(01_youtube_actual_original.mp3)을
자동으로 Voice Lab에 1:1 클론으로 등록하고, 즉시 테스트 음원을 생성하는 자동화 스크립트.
"""

import argparse
import json
import os
import sys
import mimetypes
from pathlib import Path
import urllib.request
import urllib.error

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR    = WORKSPACE_DIR / "output"
SAMPLES_DIR   = OUTPUT_DIR / "voice_samples" / "elevenlabs_clones"
REF_MP3       = OUTPUT_DIR / "voice_samples" / "songrim_100pct_replica" / "01_youtube_actual_original.mp3"

SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def create_multipart_data(fields: dict, files: dict, boundary: str) -> bytes:
    """Multipart/form-data 인코더"""
    body = bytearray()
    
    # 텍스트 필드
    for name, value in fields.items():
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode('utf-8'))
        body.extend(f'{value}\r\n'.encode('utf-8'))
        
    # 파일 필드
    for name, filepath in files.items():
        filename = Path(filepath).name
        mime_type = mimetypes.guess_type(filename)[0] or 'audio/mpeg'
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(f'Content-Type: {mime_type}\r\n\r\n'.encode('utf-8'))
        with open(filepath, 'rb') as f:
            body.extend(f.read())
        body.extend(b'\r\n')
        
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    return bytes(body)


def auto_create_voice_clone(api_key: str, ref_audio_path: Path, voice_name: str = "Songrim_Yadam_Narrator") -> str:
    """ElevenLabs Voice Lab에 15초 원본 음성을 업로드하여 Voice Clone 자동 생성"""
    print(f"\n1. ElevenLabs Voice Lab에 원본 음성 업로드 및 클론 생성 중...")
    print(f"   - 음원 파일: {ref_audio_path.name}")
    print(f"   - 보이스 이름: {voice_name}")
    
    url = "https://api.elevenlabs.io/v1/voices/add"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    fields = {
        "name": voice_name,
        "description": "송림야담 100% 원본 복제 조선 서사 여성 나레이터"
    }
    files = {
        "files": str(ref_audio_path)
    }
    
    data = create_multipart_data(fields, files, boundary)
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            voice_id = res_json.get("voice_id")
            print(f"   ✅ 보이스 클론 등록 성공! Voice ID: {voice_id}")
            return voice_id
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', errors='replace')
        print(f"❌ ElevenLabs Voice Clone 생성 실패 ({e.code}): {err}")
        return None
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def synthesize(api_key: str, voice_id: str, text: str, output_path: Path) -> bool:
    """ElevenLabs Multilingual v2로 한국어 음성 생성"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.80,
            "style": 0.15,
            "use_speaker_boost": True
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"❌ 음성 합성 오류: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="ElevenLabs Automated Voice Clone & Synthesize")
    parser.add_argument("--api-key", type=str, default=os.getenv("ELEVENLABS_API_KEY"), help="ElevenLabs API Key")
    parser.add_argument("--voice-id", type=str, default=None, help="기존 Voice ID가 있는 경우 입력")
    args = parser.parse_args()

    print("=" * 75)
    print("  🚀 ElevenLabs 원본 음성 자동 1:1 보이스 클로닝 & 생성 파이프라인")
    print("=" * 75)

    api_key = args.api_key
    if not api_key:
        print("\n🔑 ElevenLabs API Key를 입력해주세요:")
        api_key = input("API Key: ").strip()

    if not api_key:
        print("❌ API Key가 입력되지 않았습니다.")
        return

    # 1. Voice ID 확보 (자동 클론 생성 또는 기존 ID 사용)
    voice_id = args.voice_id
    if not voice_id:
        voice_id = auto_create_voice_clone(api_key, REF_MP3)
        if not voice_id:
            return

    # 2. 테스트 음원 2종 생성 (1번 원본 벤치마크, 2번 슬라이드 1번 대본)
    samples = [
        {
            "id": "eleven_clone_benchmark",
            "name": "원본 동일 대본 복제",
            "text": "빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다. 새벽 장터길 쫓기던 여인을 달구지 안에 숨겨 준 바로 다음 날이었지요."
        },
        {
            "id": "eleven_clone_slide1",
            "name": "1번 슬라이드 본문 대본",
            "text": "소박맞아 쫓겨난 윤씨 마님은 눈보라 치는 산길을 헤매며 깊은 절망에 빠졌습니다. 그때, 어둠 속에서 묵묵히 마님의 뒤를 따르는 우직한 그림자가 있었습니다."
        }
    ]

    print("\n2. 한국어 100% 클론 음성 생성 중 (Eleven Multilingual v2)...")
    for s in samples:
        out_mp3 = SAMPLES_DIR / f"{s['id']}.mp3"
        print(f"   ▶ [{s['name']}] 합성 중...")
        success = synthesize(api_key, voice_id, s['text'], out_mp3)
        if success:
            print(f"      ✅ 생성 완료: {out_mp3.name}")

    print("\n" + "=" * 75)
    print("  ✨ ElevenLabs 100% 클로닝 및 테스트 음원 생성 완료!")
    print("=" * 75)
    print(f"  📂 생성 폴더: {SAMPLES_DIR}")
    print(f"  🔑 등록된 Voice ID: {voice_id}")


if __name__ == "__main__":
    main()
