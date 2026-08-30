import asyncio
import json
import os
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from playwright.async_api import async_playwright

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "output"
STORYBOOK_OUTPUT_DIR = OUTPUT_DIR / "storybook_slides"
SLIDES_JSON_PATH = OUTPUT_DIR / "slides_data.json"
TEMPLATES_DIR = WORKSPACE_DIR / "templates"
TEMPLATE_HTML_PATH = TEMPLATES_DIR / "storybook_template.html"
STUDIO_IMAGES_DIR = OUTPUT_DIR / "studio_images"
IMAGES_DIR = OUTPUT_DIR / "images"
ASSETS_DIR = TEMPLATES_DIR / "assets"


STORYBOOK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def render_storybook_slides():
    if not SLIDES_JSON_PATH.exists():
        print(f"Error: {SLIDES_JSON_PATH} not found.")
        return

    with open(SLIDES_JSON_PATH, "r", encoding="utf-8") as f:
        slides_data = json.load(f)

    with open(TEMPLATE_HTML_PATH, "r", encoding="utf-8") as f:
        template_raw = f.read()

    print(f"총 {len(slides_data)}개 동화책 슬라이드 렌더링 시작...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0
        )
        page = await context.new_page()

        for idx, slide in enumerate(slides_data, 1):
            slide_idx = slide.get("slide_index", idx)
            chapter_title = slide.get("chapter_title", "")
            screen_text = slide.get("slide_screen_text", "")
            character_name = slide.get("character_name", "")
            
            # 텍스트 포맷팅 (100% 순수 서사형 텍스트)
            formatted_text = screen_text.replace("\n", "<br>")


            # 일러스트 이미지 소스 매핑 (120개 슬라이드 1:1 고유 씬 이미지 연동)
            studio_img = STUDIO_IMAGES_DIR / f"slide_{slide_idx:03d}.png"
            images_img = IMAGES_DIR / f"slide_{slide_idx:03d}.png"
            
            if studio_img.exists() and studio_img.stat().st_size > 150000:
                img_src = studio_img.resolve().as_uri()
            elif images_img.exists():
                img_src = images_img.resolve().as_uri()
            else:
                # 캐릭터 아바타 또는 기본 에셋 폴백
                avatar = slide.get("avatar_path", "")
                if avatar and (WORKSPACE_DIR / avatar).exists():
                    img_src = (WORKSPACE_DIR / avatar).resolve().as_uri()
                elif "돌쇠" in character_name:
                    img_src = (ASSETS_DIR / "dolsoe_avatar.jpg").resolve().as_uri()
                elif "마님" in character_name:
                    img_src = (ASSETS_DIR / "lady_yoon_avatar.jpg").resolve().as_uri()
                elif "김판서" in character_name:
                    img_src = (ASSETS_DIR / "gim_panseo_avatar.jpg").resolve().as_uri()
                else:
                    img_src = (STUDIO_IMAGES_DIR / "slide_001.png").resolve().as_uri()


            # HTML 바인딩
            html_content = template_raw.replace("{{IMAGE_SRC}}", img_src)
            html_content = html_content.replace("{{CHAPTER_TITLE}}", chapter_title)
            html_content = html_content.replace("{{STORY_TEXT}}", formatted_text)
            html_content = html_content.replace("{{PAGE_NUMBER}}", f"{slide_idx:03d} / {len(slides_data):03d}")

            temp_html_file = TEMPLATES_DIR / "temp_storybook_render.html"
            with open(temp_html_file, "w", encoding="utf-8") as tf:
                tf.write(html_content)

            await page.goto(temp_html_file.resolve().as_uri(), wait_until="networkidle")
            await page.wait_for_timeout(30)

            out_path = STORYBOOK_OUTPUT_DIR / f"storybook_{slide_idx:03d}.png"
            await page.screenshot(path=str(out_path), full_page=True)
            if slide_idx % 20 == 0 or slide_idx == 1:
                print(f"  [✓] 동화책 슬라이드 렌더링 완료: {out_path.name}")

        await browser.close()
        print(f"\n🎉 전체 {len(slides_data)}장 동화책 스타일 슬라이드 제작 완료 -> {STORYBOOK_OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(render_storybook_slides())
