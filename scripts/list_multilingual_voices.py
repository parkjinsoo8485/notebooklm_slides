import asyncio
import sys
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def main():
    voices = await edge_tts.list_voices()
    multi = [v for v in voices if 'multilingual' in v['ShortName'].lower()]
    print(f"=== edge-tts에 즉시 사용 가능한 Multilingual 모델 (총 {len(multi)}개) ===")
    for v in multi:
        print(f"- {v['ShortName']} ({v['Gender']}, {v['Locale']})")

if __name__ == "__main__":
    asyncio.run(main())
