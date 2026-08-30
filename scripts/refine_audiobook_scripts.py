import json
import re
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "output"
SLIDES_JSON_PATH = OUTPUT_DIR / "slides_data.json"

def engineer_storytelling_script(text):
    """
    [천재대박 연구사님 1번 지침: 문장 부호 엔지니어링 엔진]
    - AI 특유의 랩하듯 읽는 현상 완벽 방지
    - 주어, 부사어 뒤 의도적인 쉼표(,) 배치로 숨고르기
    - 문장 사이 및 극적 여운에 말줄임표(...) 배치하여 깊은 침묵 형성
    """
    t = text.strip()
    t = re.sub(r'[“"”]', '', t)
    t = t.replace("...", " ").replace("…", " ")
    t = re.sub(r'\s+', ' ', t)

    # 1. 문장 분리
    sentences = re.split(r'(?<=[.!?])\s+', t)
    engineered_sentences = []

    for sent in sentences:
        s = sent.strip()
        if not s:
            continue
        s = s.rstrip('.!?')

        # 주어 및 접속사, 부사 뒤 의도적 쉼표 삽입 (호흡 가다듬기)
        # 예: 마님은, 돌쇠는, 그러나, 그때, 어느 날, 깊은 산골에서,
        s = re.sub(r'^(한양 북촌|어느 늦가을 밤|비바람이 들이치는 낡은 흙바닥에|화려했던 비단옷은|그때|돌쇠는|마님은|김판서는|주막 노파는|사병들은|달빛조차|어둠 속에서|눈보라 치는 산길에서|세도가의 횡포에)\s*', r'\1, ', s)
        s = re.sub(r'([가-힣]+)에게도\s+', r'\1에게도, ', s)
        s = re.sub(r'([가-힣]+)지만\s+', r'\1지만, ', s)
        s = re.sub(r'([가-힣]+)었으나\s+', r'\1었으나, ', s)

        # 중복 쉼표 정리
        s = re.sub(r',\s*,', ',', s)
        s = re.sub(r'\s*,\s*', ', ', s)

        # 문장 끝에 말줄임표(...)를 넣어 호흡의 여운과 침묵 형성
        engineered_sentences.append(s + "...")

    # 문장 사이를 '... '로 연결하여 TTS가 한 템포 깊게 쉬어가도록 유도
    full_script = "  ".join(engineered_sentences)
    return full_script

def main():
    if not SLIDES_JSON_PATH.exists():
        print(f"Error: {SLIDES_JSON_PATH} not found.")
        return

    with open(SLIDES_JSON_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)

    for slide in slides:
        v_text = slide.get("voice_script", "")
        if not v_text:
            v_text = slide.get("slide_screen_text", "")
        
        # 화면 자막용 (간결하고 정갈함)
        screen_clean = re.sub(r'[“"”]', '', slide.get("slide_screen_text", "")).strip()
        screen_clean = re.sub(r'\s+', ' ', screen_clean)

        # 음성 대본용 (문장 부호 엔지니어링 적용)
        engineered_voice = engineer_storytelling_script(v_text)

        slide["character_name"] = "내레이션"
        slide["slide_screen_text"] = screen_clean
        slide["voice_script"] = engineered_voice

    with open(SLIDES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(slides, f, ensure_ascii=False, indent=2)

    print(f"✨ 120개 슬라이드 전체 대본 문장 부호 엔지니어링(쉼표/말줄임표) 완료! -> {SLIDES_JSON_PATH}")

if __name__ == "__main__":
    main()
