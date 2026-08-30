import os
import sys
from pathlib import Path
import fitz  # PyMuPDF

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "output"
STUDIO_DECK_DIR = OUTPUT_DIR / "studio_deck"
STUDIO_IMAGES_DIR = OUTPUT_DIR / "studio_images"

STUDIO_DECK_DIR.mkdir(parents=True, exist_ok=True)
STUDIO_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def convert_pdf_to_images(pdf_path, output_dir):
    print(f"📖 Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"  Total pages in PDF: {total_pages}")
    
    # 300 DPI 렌더링 매트릭스 (1920x1080 이상의 초고화질)
    zoom = 2.5  # 72 * 2.5 = 180 DPI (약 2500x1400 해상도)
    mat = fitz.Matrix(zoom, zoom)
    
    generated_images = []
    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)
        
        out_file = output_dir / f"studio_slide_{page_num + 1:03d}.png"
        pix.save(str(out_file))
        print(f"  [✓] Page {page_num + 1}/{total_pages} -> {out_file.name} ({pix.width}x{pix.height})")
        generated_images.append(out_file)
        
    doc.close()
    print(f"✨ Successfully converted {len(generated_images)} slides to images in: {output_dir}")
    return generated_images

if __name__ == "__main__":
    pdf_files = list(STUDIO_DECK_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in output/studio_deck/")
        sys.exit(1)
        
    convert_pdf_to_images(pdf_files[0], STUDIO_IMAGES_DIR)
