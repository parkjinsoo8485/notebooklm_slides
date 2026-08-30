"""
01_render_slides.py
───────────────────
HTML 템플릿(slide_template.html)을 기반으로 Playwright를 사용하여
1920x1080 고해상도 슬라이드 이미지를 렌더링합니다.
"""

import argparse
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

WORKSPACE_DIR      = Path(__file__).resolve().parent.parent
TEMPLATES_DIR      = WORKSPACE_DIR / "templates"
TEMPLATE_HTML_PATH = TEMPLATES_DIR / "slide_template.html"
OUTPUT_DIR         = WORKSPACE_DIR / "output"
IMAGES_DIR         = OUTPUT_DIR / "images"
SLIDES_DATA_PATH   = OUTPUT_DIR / "slides_data.json"

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


def render_single_slide(page, template_str, slide, out_path):
    slide_idx = slide.get("slide_index", 1)
    chapter_title = slide.get("chapter_title", "조선 설화 야담")
    screen_text = slide.get("slide_screen_text", "").replace("\n", "<br>")
    speaker_tag_html = build_speaker_tag(slide)

    html_content = template_str.replace("{{chapter_title}}", chapter_title)
    html_content = html_content.replace("{{slide_index}}", f"{slide_idx:03d}")
    html_content = html_content.replace("{{speaker_tag}}", speaker_tag_html)
    html_content = html_content.replace("{{slide_screen_text}}", screen_text)

    temp_html = OUTPUT_DIR / f"temp_render_{slide_idx}.html"
    temp_html.write_text(html_content, encoding="utf-8")

    page.goto(temp_html.resolve().as_uri())
    page.wait_for_timeout(100)
    page.screenshot(path=str(out_path), full_page=True)

    if temp_html.exists():
        temp_html.unlink()


def main():
    parser = argparse.ArgumentParser(description="슬라이드 이미지 렌더러")
    parser.add_argument("--slide", type=int, default=None, help="렌더링할 특정 슬라이드 번호")
    parser.add_argument("--limit", type=int, default=None, help="최대 렌더링 개수")
    args = parser.parse_args()

    if not SLIDES_DATA_PATH.exists() or not TEMPLATE_HTML_PATH.exists():
        print("❌ 필요한 템플릿 또는 데이터 파일이 없습니다.")
        return

    slides = json.loads(SLIDES_DATA_PATH.read_text(encoding="utf-8"))
    template_str = TEMPLATE_HTML_PATH.read_text(encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        if args.slide:
            target = [s for s in slides if s.get("slide_index") == args.slide]
            if not target:
                print(f"❌ 슬라이드 {args.slide}를 찾을 수 없습니다.")
                return
            out_img = IMAGES_DIR / f"slide_{args.slide:03d}.png"
            render_single_slide(page, template_str, target[0], out_img)
            print(f"✅ 슬라이드 {args.slide:03d} 렌더링 완료 -> {out_img.name}")
        else:
            print(f"🖼️ 전체 {len(slides)}개 슬라이드 이미지 렌더링 시작...")
            count = 0
            for s in slides:
                idx = s.get("slide_index", count + 1)
                out_img = IMAGES_DIR / f"slide_{idx:03d}.png"
                render_single_slide(page, template_str, s, out_img)
                count += 1
                if count % 10 == 0:
                    print(f"  → {count}/{len(slides)} 완료")
                if args.limit and count >= args.limit:
                    break
            print(f"🎉 모든 슬라이드 이미지 렌더링 완료! ({count}장)")

        browser.close()

if __name__ == "__main__":
    main()
