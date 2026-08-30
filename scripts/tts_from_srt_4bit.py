#!/usr/bin/env python3
"""
tts_from_srt_4bit.py
─────────────────────────────────────────────────────────────────────────────
CosyVoice2 4-Bit (NF4 Quantized) TTS Generator for Slide 001
- Reference Audio: output/cosyvoice2_pristine_samples/sample3_classic_folklore_4.8s.wav
- Subtitle: output/subtitles/slide_001.srt
- 4-Bit NormalFloat Quantization for LLM Backbone (VRAM: ~1.05GB)
- Saves to: output/audio/slide_001.mp3 and creates web player
"""

import sys
import os
import io
import re
import time
import base64
import subprocess
from pathlib import Path
import torch
import torch.nn as nn
import soundfile as sf

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
try:
    from optimize_performance import optimize_system_and_torch
    optimize_system_and_torch(max_cpu_threads=2, lower_priority=True)
except Exception:
    pass

COSYVOICE_DIR = PROJECT_ROOT / "third_party" / "CosyVoice"
MATCHA_DIR = COSYVOICE_DIR / "third_party" / "Matcha-TTS"

sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))

import bitsandbytes as bnb
from hyperpyyaml import load_hyperpyyaml
from cosyvoice.cli.frontend import CosyVoiceFrontEnd
from cosyvoice.cli.model import CosyVoice2Model

SRT_PATH     = PROJECT_ROOT / "output" / "subtitles" / "slide_001.srt"
PROMPT_WAV   = PROJECT_ROOT / "output" / "cosyvoice2_pristine_samples" / "sample3_classic_folklore_4.8s.wav"
PROMPT_TEXT  = "옛날 옛적 한양에서 그리 멀지 않은 양주 땅 변두리에 만석이라는 농부가 살았습니다."

OUT_DIR      = PROJECT_ROOT / "output" / "audio"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_WAV      = OUT_DIR / "slide_001.wav"
OUT_MP3      = OUT_DIR / "slide_001.mp3"
PLAYER_HTML  = PROJECT_ROOT / "output" / "slide_001_cosyvoice2_player.html"

def parse_srt(srt_file):
    with open(srt_file, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content.strip())
    lines = []
    for b in blocks:
        lines_in_block = [line.strip() for line in b.splitlines() if line.strip()]
        if len(lines_in_block) >= 3:
            text = " ".join(lines_in_block[2:])
            lines.append(text)
    return lines

def quantize_module_to_4bit(module, target_classes=(nn.Linear,)):
    for name, child in list(module.named_children()):
        if isinstance(child, target_classes):
            has_bias = child.bias is not None
            new_layer = bnb.nn.Linear4bit(
                child.in_features,
                child.out_features,
                bias=has_bias,
                compute_dtype=torch.float16,
                quant_type="nf4"
            )
            new_layer.weight = bnb.nn.Params4bit(
                child.weight.data,
                requires_grad=False,
                quant_type="nf4"
            )
            if has_bias:
                new_layer.bias = nn.Parameter(child.bias.data, requires_grad=False)
            setattr(module, name, new_layer)
        else:
            quantize_module_to_4bit(child, target_classes)

class CosyVoice2_4Bit_Engine:
    def __init__(self, model_dir):
        print(f"  - [1/3] CosyVoice2 설정 및 프론트엔드 로드...")
        with open(model_dir / "cosyvoice2.yaml", "r") as f:
            configs = load_hyperpyyaml(f, overrides={"qwen_pretrain_path": str(model_dir / "CosyVoice-BlankEN")})
        
        self.sample_rate = configs["sample_rate"]
        self.frontend = CosyVoiceFrontEnd(
            configs["get_tokenizer"],
            configs["feat_extractor"],
            str(model_dir / "campplus.onnx"),
            str(model_dir / "speech_tokenizer_v2.onnx"),
            str(model_dir / "spk2info.pt"),
            configs["allowed_special"]
        )
        
        print(f"  - [2/3] LLM 로드 및 bitsandbytes 4-Bit(NF4) 양자화 적용...")
        llm = configs["llm"]
        llm_dict = torch.load(model_dir / "llm.pt", map_location="cpu")
        llm.load_state_dict(llm_dict)
        del llm_dict
        quantize_module_to_4bit(llm.llm.model.model.layers)
        
        print(f"  - [3/3] Flow Matching & Vocoder 가중치 로드...")
        flow = configs["flow"]
        hift = configs["hift"]
        flow.load_state_dict(torch.load(model_dir / "flow.pt", map_location="cpu"))
        hift.load_state_dict(torch.load(model_dir / "hift.pt", map_location="cpu"))
        
        self.model = CosyVoice2Model(llm, flow, hift, fp16=True)
        if torch.cuda.is_available():
            self.model.llm.to("cuda:0")
            self.model.flow.to("cuda:0")
            self.model.hift.to("cuda:0")
            torch.cuda.empty_cache()
            vram_mb = torch.cuda.memory_allocated() / 1024**2
            print(f"  🚀 4비트 모델 준비 완료! VRAM: {vram_mb:.1f} MB")

    def synthesize_sentence(self, tts_text, prompt_text, prompt_wav):
        prompt_text = self.frontend.text_normalize(prompt_text, split=False, text_frontend=True)
        norm_text = self.frontend.text_normalize(tts_text, split=False, text_frontend=True)
        model_input = self.frontend.frontend_zero_shot(norm_text, prompt_text, str(prompt_wav), self.sample_rate, "")
        chunks = []
        for model_output in self.model.tts(**model_input, stream=False, speed=1.0):
            chunks.append(model_output["tts_speech"])
        if chunks:
            return torch.cat(chunks, dim=1)
        return None

def main():
    print("=" * 70, flush=True)
    print(" 🎙️ CosyVoice2 4-Bit (NF4) 음성 합성 시작", flush=True)
    print(f" 📜 자막: {SRT_PATH.name}", flush=True)
    print(f" 🎧 프롬프트: {PROMPT_WAV.name}", flush=True)
    print("=" * 70, flush=True)
    
    srt_lines = parse_srt(SRT_PATH)
    # 문장 단위로 병합
    full_sentence_1 = f"{srt_lines[0]} {srt_lines[1]} {srt_lines[2]}."
    full_sentence_2 = f"{srt_lines[3]} {srt_lines[4]}."
    sentences = [full_sentence_1, full_sentence_2]
    
    for i, s in enumerate(sentences, 1):
        print(f"   [{i}] {s}", flush=True)
    print("=" * 70, flush=True)
    
    model_dir = COSYVOICE_DIR / "pretrained_models" / "CosyVoice2-0.5B"
    engine = CosyVoice2_4Bit_Engine(model_dir)
    
    generated_audios = []
    silence = torch.zeros(1, int(engine.sample_rate * 0.45))
    
    t_start = time.time()
    for idx, sent in enumerate(sentences, 1):
        print(f"\n▶ ({idx}/{len(sentences)}) 합성 중: \"{sent}\"", flush=True)
        tts_input = f"<|ko|>{sent}"
        audio_tensor = engine.synthesize_sentence(tts_input, PROMPT_TEXT, PROMPT_WAV)
        if audio_tensor is not None:
            generated_audios.append(audio_tensor)
            if idx < len(sentences):
                generated_audios.append(silence)
            dur = audio_tensor.shape[1] / engine.sample_rate
            print(f"   ✨ ({idx}/{len(sentences)}) 완료: {dur:.1f}초", flush=True)
        else:
            print(f"   ❌ ({idx}/{len(sentences)}) 실패", flush=True)
            
    if generated_audios:
        final_audio = torch.cat(generated_audios, dim=1).cpu().numpy().squeeze()
        sf.write(str(OUT_WAV), final_audio, engine.sample_rate, subtype="PCM_16")
        
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(OUT_WAV), "-codec:a", "libmp3lame", "-b:a", "192k", str(OUT_MP3)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        total_dur = len(final_audio) / engine.sample_rate
        total_time = time.time() - t_start
        print(f"\n======================================================================", flush=True)
        print(f" 🎉 [성공] CosyVoice2 4-Bit 음성 생성 완료!", flush=True)
        print(f" ⏱️ 총 재생 시간: {total_dur:.1f}초 (소요 시간: {total_time:.1f}초)", flush=True)
        print(f" 📁 MP3: {OUT_MP3}", flush=True)
        print(f"======================================================================", flush=True)
        
        # HTML 플레이어 생성
        with open(OUT_MP3, "rb") as f:
            mp3_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(PROMPT_WAV, "rb") as f:
            prompt_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>CosyVoice2 4-Bit 슬라이드 1번 음성 플레이어</title>
    <style>
        body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; padding: 40px; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 14px; max-width: 650px; width: 100%; padding: 25px; }}
        .badge {{ background: #238636; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; display: inline-block; margin-bottom: 10px; }}
        h2 {{ color: #f0f6fc; margin-bottom: 15px; font-size: 20px; }}
        .box {{ background: #090d13; border: 1px solid #21262d; border-radius: 10px; padding: 15px; margin-bottom: 15px; }}
        .box.main {{ border-left: 4px solid #58a6ff; }}
        .box.ref {{ border-left: 4px solid #d29922; }}
        audio {{ width: 100%; margin-top: 10px; }}
        .txt {{ font-size: 14px; line-height: 1.6; color: #8b949e; font-style: italic; }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">CosyVoice2 4-Bit NF4</span>
        <h2>🎙️ 슬라이드 1번 야담 낭독 음성 (CosyVoice2)</h2>
        <div class="box main">
            <strong>✨ 완성된 음성 ({total_dur:.1f}초)</strong>
            <p class="txt">"{' '.join(sentences)}"</p>
            <audio controls autoplay src="data:audio/mp3;base64,{mp3_b64}"></audio>
        </div>
        <div class="box ref">
            <strong>🎧 참조 프롬프트 (sample3_classic_folklore_4.8s)</strong>
            <p class="txt">"{PROMPT_TEXT}"</p>
            <audio controls src="data:audio/wav;base64,{prompt_b64}"></audio>
        </div>
    </div>
</body>
</html>"""
        with open(PLAYER_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        print(f" 🌐 플레이어 생성 완료: {PLAYER_HTML}", flush=True)

if __name__ == "__main__":
    main()
