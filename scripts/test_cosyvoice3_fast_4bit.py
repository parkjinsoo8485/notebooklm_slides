#!/usr/bin/env python3
"""
Fun-CosyVoice 3.0 고속 4-Bit 양자화 + 한국어 지시문(Instruct) 합성 테스트
────────────────────────────────────────────────────────────────────────────
1. LLM 4-Bit NF4 양자화 적용 (VRAM 3.9GB -> 1.5GB로 축소)
2. CosyVoice 3.0 한국어 공식 지시문 (instruct2 & cross_lingual) 테스트
"""
import sys, os, time, base64, subprocess, io
for attr in ("stdout", "stderr"):
    s = getattr(sys, attr)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, attr, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

from pathlib import Path
import soundfile as sf
import torch
import torch.nn as nn
import bitsandbytes as bnb

PROJECT_ROOT = Path(r"C:\My_Project\src\notebooklm_slides")
COSYVOICE_DIR = PROJECT_ROOT / "third_party" / "CosyVoice"
MATCHA_DIR = COSYVOICE_DIR / "third_party" / "Matcha-TTS"
MODEL_DIR = COSYVOICE_DIR / "pretrained_models" / "Fun-CosyVoice3-0.5B"
OUT_DIR = PROJECT_ROOT / "output" / "cosyvoice3_korean_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))

REF_WAV = PROJECT_ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"
PROMPT_TEXT = "You are a helpful assistant.<|endofprompt|>빈 소달구지 하나로 어린 딸을 키우던 가난한 농부에게 누군가 찾아와 그리 속삭였습니다."

TEST_TEXT = "안녕하세요, 테스트 음성입니다."
SLIDE1_TEXT = "옛날 옛적 한양 북촌 명문가의 어질고 고왔던 윤 씨 마님이, 하루아침에 억울한 누명을 쓰고 깊은 산골로 내쫓기고 말았더렀지요."

from hyperpyyaml import load_hyperpyyaml
from cosyvoice.cli.frontend import CosyVoiceFrontEnd
from cosyvoice.cli.model import CosyVoice3Model

def quantize_module(module, mode="4bit"):
    for name, child in list(module.named_children()):
        if isinstance(child, (nn.Linear,)):
            has_bias = child.bias is not None
            new_layer = bnb.nn.Linear4bit(
                child.in_features, child.out_features, bias=has_bias,
                compute_dtype=torch.float16, quant_type="nf4"
            )
            new_layer.weight = bnb.nn.Params4bit(child.weight.data, requires_grad=False, quant_type="nf4")
            if has_bias:
                new_layer.bias = nn.Parameter(child.bias.data, requires_grad=False)
            setattr(module, name, new_layer)
        else:
            quantize_module(child, mode)

print("=" * 65)
print(" ⚡ Fun-CosyVoice 3.0 고속 4-Bit 한국어 합성 엔진 초기화")
print("=" * 65)

with open(MODEL_DIR / "cosyvoice3.yaml", "r") as f:
    configs = load_hyperpyyaml(f, overrides={"qwen_pretrain_path": str(MODEL_DIR / "CosyVoice-BlankEN")})

frontend = CosyVoiceFrontEnd(
    configs["get_tokenizer"],
    configs["feat_extractor"],
    str(MODEL_DIR / "campplus.onnx"),
    str(MODEL_DIR / "speech_tokenizer_v3.onnx"),
    str(MODEL_DIR / "spk2info.pt"),
    configs["allowed_special"]
)

llm = configs["llm"]
flow = configs["flow"]
hift = configs["hift"]

llm.load_state_dict(torch.load(MODEL_DIR / "llm.pt", map_location="cpu"))
flow.load_state_dict(torch.load(MODEL_DIR / "flow.pt", map_location="cpu"))
hift.load_state_dict(torch.load(MODEL_DIR / "hift.pt", map_location="cpu"))

# LLM에 4-Bit NF4 양자화 적용
print("  - bitsandbytes 4-Bit NF4 양자화 적용 중...")
quantize_module(llm.llm.model.model.layers, mode="4bit")

model = CosyVoice3Model(llm, flow, hift, fp16=True)
if torch.cuda.is_available():
    model.llm.to("cuda:0")
    model.flow.to("cuda:0")
    model.hift.to("cuda:0")
    torch.cuda.empty_cache()
    vram_mb = torch.cuda.memory_allocated() / 1024**2
    print(f"  🚀 모델 준비 완료 (현재 할당 VRAM: {vram_mb:.1f} MB)", flush=True)

# ── 테스트 1: instruct2 한국어 지시 모드 ──
print("\n▶ [테스트 1] instruct2 (한국어 명시 지시)")
instruct_txt = "You are a helpful assistant. 请用韩语表达。<|endofprompt|>"
tts_input = TEST_TEXT

t0 = time.time()
norm_tts = frontend.text_normalize(tts_input, split=False, text_frontend=False)
model_input = frontend.frontend_instruct2(norm_tts, instruct_txt, str(REF_WAV), configs["sample_rate"], "")

chunks1 = []
for out in model.tts(**model_input, stream=False, speed=1.0):
    chunks1.append(out["tts_speech"])

if chunks1:
    audio1 = torch.cat(chunks1, dim=1)
    dur1 = audio1.shape[-1] / configs["sample_rate"]
    elapsed1 = time.time() - t0
    wav1 = OUT_DIR / "03_instruct2_korean_4bit.wav"
    mp31 = OUT_DIR / "03_instruct2_korean_4bit.mp3"
    sf.write(str(wav1), audio1.cpu().numpy().squeeze(), configs["sample_rate"], subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-i", str(wav1), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp31)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✔ 완료: {dur1:.1f}초 (소요: {elapsed1:.1f}초, RTF: {elapsed1/dur1:.2f}x)")

# ── 테스트 2: cross_lingual 한국어 모드 ──
print("\n▶ [테스트 2] cross_lingual (다국어 직접 모드)")
tts_cross = f"You are a helpful assistant.<|endofprompt|>{TEST_TEXT}"
t0 = time.time()
norm_cross = frontend.text_normalize(tts_cross, split=False, text_frontend=False)
model_input_cross = frontend.frontend_cross_lingual(norm_cross, str(REF_WAV), configs["sample_rate"], "")

chunks2 = []
for out in model.tts(**model_input_cross, stream=False, speed=1.0):
    chunks2.append(out["tts_speech"])

if chunks2:
    audio2 = torch.cat(chunks2, dim=1)
    dur2 = audio2.shape[-1] / configs["sample_rate"]
    elapsed2 = time.time() - t0
    wav2 = OUT_DIR / "04_cross_lingual_korean_4bit.wav"
    mp32 = OUT_DIR / "04_cross_lingual_korean_4bit.mp3"
    sf.write(str(wav2), audio2.cpu().numpy().squeeze(), configs["sample_rate"], subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-i", str(wav2), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp32)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✔ 완료: {dur2:.1f}초 (소요: {elapsed2:.1f}초, RTF: {elapsed2/dur2:.2f}x)")

print("\n모든 4-Bit 고속 테스트 완료!")
