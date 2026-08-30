import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


WORKSPACE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = WORKSPACE_DIR / "templates"
TEMPLATE_HTML_PATH = TEMPLATES_DIR / "slide_template.html"
OUTPUT_DIR = WORKSPACE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
SLIDES_DATA_PATH = OUTPUT_DIR / "slides_data.json"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def build_speaker_tag(slide):
    char_name = slide.get("character_name", "내레이션")
    theme = slide.get("character_theme", "#d4af37")
    avatar = slide.get("avatar_path", "")
    emotion = slide.get("emotion", "")

    if char_name in ["내레이션", "서술", "해설"] or not avatar:
        return f"""
        <div class="speaker-tag" style="--character-theme: {theme};">
          <div class="speaker-info">
            <span class="speaker-name">{char_name}</span>
            {f'<span class="speaker-emotion">❖ {emotion}</span>' if emotion else ''}
          </div>
        </div>
        """
    
    avatar_full_path = TEMPLATES_DIR / avatar
    # 상대 경로 혹은 파일 URI 생성
    avatar_src = f"assets/{Path(avatar).name}"

    return f"""
    <div class="speaker-tag" style="--character-theme: {theme};">
      <img src="{avatar_src}" alt="{char_name}" class="avatar-img">
      <div class="speaker-info">
        <span class="speaker-name">{char_name}</span>
        {f'<span class="speaker-emotion">❖ {emotion}</span>' if emotion else ''}
      </div>
    </div>
    """

def render_slides():
    if not SLIDES_DATA_PATH.exists():
        print(f"Error: {SLIDES_DATA_PATH} not found.")
        return

    with open(SLIDES_DATA_PATH, "r", encoding="utf-8") as f:
        slides = json.load(f)

    with open(TEMPLATE_HTML_PATH, "r", encoding="utf-8") as f:
        template_raw = f.read()

    total_slides = len(slides)
    print(f"🎬 Starting Playwright Slide Rendering: Total {total_slides} slides...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        for idx, slide in enumerate(slides, start=1):
            idx_num = slide.get("slide_index", idx)
            ch_title = slide.get("chapter_title", "조선 야담")
            screen_text = slide.get("slide_screen_text", "").replace("\n", "<br>")
            theme = slide.get("character_theme", "#d4af37")
            speaker_tag_html = build_speaker_tag(slide)
            counter_str = f"{idx_num:03d} / {total_slides:03d}"

            html_content = template_raw
            html_content = html_content.replace("{{CHARACTER_THEME}}", theme)
            html_content = html_content.replace("{{CHAPTER_TITLE}}", ch_title)
            html_content = html_content.replace("{{SLIDE_COUNTER}}", counter_str)
            html_content = html_content.replace("{{SPEAKER_TAG_HTML}}", speaker_tag_html)
            html_content = html_content.replace("{{SLIDE_SCREEN_TEXT}}", screen_text)

            # 임시 HTML 저장 및 렌더링
            temp_html = TEMPLATES_DIR / f"_temp_slide_{idx_num}.html"
            with open(temp_html, "w", encoding="utf-8") as tf:
                tf.write(html_content)

            page.goto(temp_html.as_uri())
            page.wait_for_load_state("networkidle")

            output_png = IMAGES_DIR / f"slide_{idx_num:03d}.png"
            page.screenshot(path=str(output_png), full_page=False)

            if temp_html.exists():
                temp_html.unlink()

            print(f"  [✓] Rendered: {output_png.name} ({idx_num}/{total_slides})")

        browser.close()

    print(f"\n✨ All {total_slides} slide images rendered successfully in: {IMAGES_DIR}")

if __name__ == "__main__":
    render_slides()
