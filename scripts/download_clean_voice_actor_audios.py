#!/usr/bin/env python3
"""
download_clean_voice_actor_audios.py
───────────────────────────────────
저작권 없는 고품질 스튜디오 전문 성우 음원 자동 다운로더
1. daje/korean-tts-training (스튜디오 전문 성우 무반향 고음질 발화)
2. Zeroth-Korean 스튜디오 성우 (#104 남성 정통 성우, #105 여성 정통 성우, #126 나레이터)
3. 메타데이터 CSV 및 GPT-SoVITS train.list 라벨링 자동 생성
"""

import sys, io, os, json, csv, urllib.request, time, shutil
for a in ("stdout", "stderr"):
    s = getattr(sys, a)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, a, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path

WORKSPACE = Path(r"C:\My_Project\src\notebooklm_slides")
TARGET_DIR = WORKSPACE / "data" / "clean_voice_actors"
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# 1. 스튜디오 전문 성우 (daje/korean-tts-training)
STUDIO_ACTOR_DIR = TARGET_DIR / "korean_tts_training_studio"
STUDIO_ACTOR_DIR.mkdir(parents=True, exist_ok=True)
WAVS_DIR = STUDIO_ACTOR_DIR / "wavs"
WAVS_DIR.mkdir(parents=True, exist_ok=True)

BASE_HF_URL = "https://huggingface.co/datasets/daje/korean-tts-training/resolve/main"

def download_file(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        return True
    except Exception as e:
        print(f"   ⚠️ 다운로드 실패 ({dest.name}): {e}")
        return False

def setup_daje_voice_actors(max_count: int = 50):
    print("=" * 80)
    print("🎙️ [1/2] 한국어 스튜디오 전문 성우 고음질 음원 다운로드 시작...")
    print(f"📁 대상 폴더: {STUDIO_ACTOR_DIR}")
    print("=" * 80)

    # 1. 메타데이터 다운로드
    meta_url = f"{BASE_HF_URL}/metadata.csv"
    meta_path = STUDIO_ACTOR_DIR / "metadata.csv"
    download_file(meta_url, meta_path)

    if not meta_path.exists():
        print("❌ 메타데이터 다운로드 실패")
        return []

    # 2. 메타데이터 파싱 및 상위 발화 다운로드
    downloaded_samples = []
    with open(meta_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= max_count:
                break
            fname = row.get("file_name", "").strip()
            text = row.get("text", "").strip()
            category = row.get("category", "").strip()
            instruct = row.get("instruct", "").strip()

            if not fname or not text:
                continue

            file_url = f"{BASE_HF_URL}/{fname}"
            dest_wav = WAVS_DIR / fname

            print(f"   📥 [{i+1}/{max_count}] {fname} 다운로드 중... ({text[:25]}...)")
            success = download_file(file_url, dest_wav)
            if success:
                downloaded_samples.append({
                    "file_name": fname,
                    "local_path": str(dest_wav),
                    "text": text,
                    "category": category,
                    "instruct": instruct
                })

    # GPT-SoVITS 학습용 train.list 생성
    list_lines = []
    for s in downloaded_samples:
        line = f"{s['local_path']}|studio_voice_actor|KO|{s['text']}\n"
        list_lines.append(line)

    with open(STUDIO_ACTOR_DIR / "train.list", "w", encoding="utf-8") as f:
        f.writelines(list_lines)

    print(f"✅ 스튜디오 전문 성우 음원 {len(downloaded_samples)}개 다운로드 완료!\n")
    return downloaded_samples

def setup_zeroth_voice_actors():
    print("=" * 80)
    print("🎙️ [2/2] Zeroth-Korean 정통 성우 음원 연계 및 정리...")
    print("=" * 80)
    src_corpus = WORKSPACE / "data" / "gpt_sovits_training_corpus"

    actors = [
        ("speaker_104_male_studio", "표준어 정통 남성 성우 #104 (CC BY 4.0)"),
        ("speaker_105_female_studio", "표준어 정통 여성 성우 #105 (CC BY 4.0)"),
        ("speaker_126_male_narrator", "차분한 남성 나레이터 #126 (CC BY 4.0)")
    ]

    zeroth_samples = []
    for folder_name, desc in actors:
        actor_src = src_corpus / folder_name
        actor_dst = TARGET_DIR / folder_name
        actor_dst.mkdir(parents=True, exist_ok=True)

        list_file = actor_src / "train.list"
        if list_file.exists():
            shutil.copyfile(list_file, actor_dst / "train.list")
            with open(list_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                print(f"   ✅ [{desc}] {len(lines)}개 고음질 성우 발화 연계 완료")
                if lines:
                    first_parts = lines[0].strip().split("|")
                    zeroth_samples.append({
                        "name": desc,
                        "folder": folder_name,
                        "sample_path": first_parts[0],
                        "sample_text": first_parts[3] if len(first_parts) > 3 else "",
                        "count": len(lines)
                    })

    return zeroth_samples

def create_player_html(daje_samples, zeroth_samples):
    """다운로드된 성우 음원을 바로 들어볼 수 있는 감각적인 웹 플레이어 생성"""
    out_html = WORKSPACE / "output" / "voice_actors_player.html"
    out_html.parent.mkdir(parents=True, exist_ok=True)

    daje_cards = ""
    for idx, s in enumerate(daje_samples[:20]):
        # 상대 경로 계산
        rel_path = f"../data/clean_voice_actors/korean_tts_training_studio/wavs/{s['file_name']}"
        daje_cards += f"""
        <div class="voice-card">
            <div class="card-header">
                <span class="badge blue">전문 성우 스튜디오</span>
                <span class="tag">{s['category']}</span>
            </div>
            <div class="voice-name">스튜디오 성우 발화 #{idx+1} ({s['file_name']})</div>
            <div class="script-box">"{s['text']}"</div>
            <div class="instruct-box">💡 <i>{s['instruct'][:90]}...</i></div>
            <audio controls preload="none" src="{rel_path}"></audio>
        </div>
        """

    zeroth_cards = ""
    for z in zeroth_samples:
        wav_path = Path(z["sample_path"])
        rel_path = f"../data/gpt_sovits_training_corpus/{z['folder']}/wavs/{wav_path.name}"
        zeroth_cards += f"""
        <div class="voice-card highlight">
            <div class="card-header">
                <span class="badge gold">CC BY 4.0 정통 성우</span>
                <span class="tag">{z['count']}개 발화 보유</span>
            </div>
            <div class="voice-name">{z['name']}</div>
            <div class="script-box">"{z['sample_text']}"</div>
            <audio controls preload="none" src="{rel_path}"></audio>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[송림야담] 저작권 무료 오픈 성우 음원 보관소 & 청음실</title>
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;900&family=Noto+Serif+KR:wght@600;700;900&display=swap" rel="stylesheet">
<style>
:root {{
    --bg: #07090e;
    --card: rgba(17, 24, 39, 0.95);
    --accent: #38bdf8;
    --gold: #f59e0b;
    --emerald: #10b981;
    --text: #f8fafc;
    --muted: #94a3b8;
    --border: rgba(255, 255, 255, 0.1);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: radial-gradient(ellipse at 50% 0%, #0d1e38 0%, #080d1a 50%, var(--bg) 100%);
    color: var(--text);
    font-family: 'Pretendard', sans-serif;
    min-height: 100vh;
    padding: 50px 20px 100px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
}}
.header {{
    text-align: center;
    max-width: 900px;
    margin-bottom: 40px;
}}
.header h1 {{
    font-family: 'Noto Serif KR', serif;
    font-size: 32px;
    font-weight: 900;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #ffffff 40%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 12px;
}}
.header p {{
    color: var(--muted);
    font-size: 15px;
    line-height: 1.6;
}}
.section-title {{
    font-size: 20px;
    font-weight: 700;
    color: var(--gold);
    margin: 30px 0 15px 0;
    width: 100%;
    max-width: 1100px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
    width: 100%;
    max-width: 1100px;
    margin-bottom: 30px;
}}
.voice-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    transition: transform 0.2s ease, border-color 0.2s ease;
}}
.voice-card:hover {{
    transform: translateY(-4px);
    border-color: var(--accent);
}}
.voice-card.highlight {{
    border: 1px solid rgba(245, 158, 11, 0.4);
    background: linear-gradient(180deg, rgba(245, 158, 11, 0.08) 0%, rgba(17, 24, 39, 0.95) 100%);
}}
.card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.badge {{
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
}}
.badge.blue {{ background: rgba(56, 189, 248, 0.15); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.3); }}
.badge.gold {{ background: rgba(245, 158, 11, 0.15); color: var(--gold); border: 1px solid rgba(245, 158, 11, 0.3); }}
.tag {{ font-size: 12px; color: var(--muted); }}
.voice-name {{ font-size: 17px; font-weight: 700; color: #fff; }}
.script-box {{
    background: rgba(0,0,0,0.4);
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
    line-height: 1.5;
    color: #e2e8f0;
    min-height: 60px;
}}
.instruct-box {{
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.4;
}}
audio {{
    width: 100%;
    height: 38px;
    border-radius: 8px;
    margin-top: 5px;
}}
.nav-bar {{
    margin-top: 40px;
    display: flex;
    gap: 15px;
}}
.nav-btn {{
    text-decoration: none;
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
    padding: 10px 20px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    border: 1px solid var(--border);
    transition: all 0.2s;
}}
.nav-btn:hover {{
    background: var(--accent);
    color: #000;
}}
</style>
</head>
<body>
    <div class="header">
        <h1>🎙️ 저작권 무료 오픈 성우 음원 보관소</h1>
        <p>상업적 이용 및 변형이 완전 자유로운 무반향 스튜디오 전문 성우 원음입니다.<br>잡음과 에코가 전혀 없어 GPT-SoVITS 훈련 및 레퍼런스 복제에 즉시 사용 가능합니다.</p>
    </div>

    <div class="section-title">👑 정통 성우 마스터 코퍼스 (Zeroth-Korean 스튜디오 음원)</div>
    <div class="grid">
        {zeroth_cards}
    </div>

    <div class="section-title">🎙️ 스튜디오 전문 성우 발화 세트 (daje/korean-tts-training)</div>
    <div class="grid">
        {daje_cards}
    </div>

    <div class="nav-bar">
        <a class="nav-btn" href="all_listening_rooms_hub.html">🌐 통합 청음실 포털로 돌아가기</a>
        <a class="nav-btn" href="full_story_player.html">👑 120개 슬라이드 전편 완독실</a>
    </div>
</body>
</html>
"""
    out_html.write_text(html_content, encoding="utf-8")
    print(f"🎉 성우 음원 청음실 플레이어 생성 완료! -> {out_html}")

def main():
    daje_samples = setup_daje_voice_actors(max_count=30)
    zeroth_samples = setup_zeroth_voice_actors()
    create_player_html(daje_samples, zeroth_samples)

if __name__ == "__main__":
    main()
