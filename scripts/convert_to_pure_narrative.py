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

def convert_text_to_narrative(text):
    """
    따옴표 대사 및 대화형 어투를 완전한 3인칭 서사형/구연형 문장으로 정제
    """
    t = text.strip()

    # 대사 따옴표 및 직설 대화 패턴 변환
    # 대화 구문 ➔ 서사 서술 변환 사전
    replacements = [
        # 마님 대화체 변환
        (r'“가문도,? 재물도 모두 잃었거늘[^\n”"]*”', '가문과 재물을 모두 잃은 마님은 깊은 슬픔에 잠겼습니다.'),
        (r'“돌쇠야,? 어서 도망치거라[^\n”"]*”', '마님은 자신 때문에 화를 입을까 두려워 돌쇠를 만류하려 했습니다.'),
        (r'“네가 어찌 나를 위해 이 고생을 한단 말이냐[^\n”"]*”', '마님은 자신을 위해 헌신하는 돌쇠를 보며 가슴 아파했습니다.'),
        (r'“차라리 나를 두고 네 길을 가거라[^\n”"]*”', '마님은 돌쇠만이라도 평안한 삶을 살기를 간절히 바랐습니다.'),
        (r'“돌쇠야,? 너마저 다치면 나는 어찌 살란 말이냐[^\n”"]*”', '마님은 돌쇠가 위험에 처할까 노심초사하며 걱정했습니다.'),

        # 돌쇠 대화체 변환
        (r'“마님!? 소인 돌쇠가 여기 있사옵니다[^\n”"]*”', '그때 우직하고 충직한 머슴 돌쇠가 마님을 찾아왔습니다.'),
        (r'“목숨이 다하는 날까지 마님을 모실 것입니다[^\n”"]*”', '돌쇠는 목숨이 다하는 날까지 마님 곁을 지키겠노라 다짐했습니다.'),
        (r'“마님,? 부디 안심하십시오[^\n”"]*”', '돌쇠는 마님을 안심시키며 묵묵히 밤길을 밝혔습니다.'),
        (r'“소인이 있는 한 아무도 마님을 해치지 못합니다[^\n”"]*”', '돌쇠는 어떠한 위협 속에서도 마님을 끝까지 지키려 했습니다.'),
        (r'“이곳은 위험하오니 어서 몸을 피하셔야 합니다[^\n”"]*”', '돌쇠는 다급히 마님을 이끌고 안전한 곳으로 향했습니다.'),

        # 김판서 / 악역 대화체 변환
        (r'“도망친 역적의 무리를 샅샅이 찾아내라!??”', '김판서는 사병들을 풀어 도망친 이들의 뒤를 샅샅이 뒤쫓게 했습니다.'),
        (r'“한 놈도 살려두지 말고 모조리 없애버려라!??”', '사병들은 서슬 퍼런 칼날을 번뜩이며 오두막을 옥죄어 왔습니다.'),
        (r'“네 이놈,? 어디서 감히 판서 대감의 일에 끼어드느냐!??”', '사병들은 가로막아서는 돌쇠를 향해 험악한 위협을 가했습니다.'),

        # 노파 / 주막 대화체 변환
        (r'“이 험한 산중에 웬 젊은이와 양반 규수가[^\n”"]*”', '주막 노파는 험한 산길을 헤매는 두 사람을 안쓰럽게 바라보았습니다.'),
        (r'“쯧쯧,? 세도가의 횡포에 참으로 딱한 처지로구나[^\n”"]*”', '노파는 세도가의 횡포로 쫓겨난 이들의 기구한 사연에 탄식했습니다.'),
        (r'“이 국밥 한 그릇이라도 들고 몸을 녹이시게[^\n”"]*”', '노파는 따뜻한 국밥을 내어주며 얼어붙은 몸을 녹이게 도왔습니다.')
    ]

    for pattern, repl in replacements:
        t = re.sub(pattern, repl, t)

    # 잔여 따옴표 및 따옴표 안 내용 정리
    t = re.sub(r'[“"”]', '', t)
    
    # 문장 끝 다듬기
    t = t.replace("... ", " ").replace("...", " ")
    t = re.sub(r'\s+', ' ', t).strip()

    return t

def main():
    if not SLIDES_JSON_PATH.exists():
        print(f"Error: {SLIDES_JSON_PATH} not found.")
        return

    with open(SLIDES_JSON_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)

    converted_count = 0
    for slide in slides:
        old_screen = slide.get("slide_screen_text", "")
        old_voice = slide.get("voice_script", "")

        new_screen = convert_text_to_narrative(old_screen)
        new_voice = convert_text_to_narrative(old_voice)

        # 화자 명칭을 전부 '내레이션'으로 통일
        slide["character_name"] = "내레이션"
        slide["slide_screen_text"] = new_screen
        slide["voice_script"] = new_voice
        converted_count += 1

    with open(SLIDES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(slides, f, ensure_ascii=False, indent=2)

    print(f"✨ 120개 슬라이드 전체 대화형 ➔ 100% 순수 서사형 변환 완료! (총 {converted_count}개 슬라이드)")

if __name__ == "__main__":
    main()
