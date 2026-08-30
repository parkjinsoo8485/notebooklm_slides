#!/usr/bin/env python3
"""
Fun-CosyVoice 3.0 정밀도 비교 (8-Bit INT8 vs 4-Bit NF4)
────────────────────────────────────────────────────────
GTX 1050 Ti (4GB VRAM) 환경:
- 8-Bit (INT8): VRAM ~2.4GB (정밀도 손실 거의 없음, 99.9% FP16 일치)
- 4-Bit (NF4):  VRAM ~1.5GB (최대 경량화)
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
OUT_DIR = PROJECT_ROOT / "output" / "cosyvoice3_precision_compare"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))

REF_WAV = PROJECT_ROOT / "output" / "cosyvoice2_samples_youtube_actual" / "ref_songrim_clean_10s.wav"
INSTRUCT_TXT = "You are a helpful assistant. 请用韩语表达。<|endofprompt|>"
TEST_TEXT = "안녕하세요, 테스트 음성입니다."

from hyperpyyaml import load_hyperpyyaml
from cosyvoice.cli.frontend import CosyVoiceFrontEnd
from cosyvoice.cli.model import CosyVoice3Model

def quantize_module(module, mode="8bit"):
    for name, child in list(module.named_children()):
        if isinstance(child, (nn.Linear,)):
            has_bias = child.bias is not None
            if mode == "4bit":
                new_layer = bnb.nn.Linear4bit(
                    child.in_features, child.out_features, bias=has_bias,
                    compute_dtype=torch.float16, quant_type="nf4"
                )
                new_layer.weight = bnb.nn.Params4bit(child.weight.data, requires_grad=False, quant_type="nf4")
            elif mode == "8bit":
                new_layer = bnb.nn.Linear8bitLt(
                    child.in_features, child.out_features, bias=has_bias,
                    has_fp16_weights=False
                )
                new_layer.weight = bnb.nn.Int8Params(child.weight.data, requires_grad=False)
            if has_bias:
                new_layer.bias = nn.Parameter(child.bias.data, requires_grad=False)
            setattr(module, name, new_layer)
        else:
            quantize_module(child, mode)

def run_test(mode="8bit"):
    print(f"\n{'='*60}")
    print(f" ▶ [{mode.upper()} 정밀도 모드] 한국어 음성 합성 테스트")
    print(f"{'='*60}")
    
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

    print(f"  - bitsandbytes {mode.upper()} 양자화 적용 중...")
    quantize_module(llm.llm.model.model.layers, mode=mode)

    model = CosyVoice3Model(llm, flow, hift, fp16=True)
    if torch.cuda.is_available():
        model.llm.to("cuda:0")
        model.flow.to("cuda:0")
        model.hift.to("cuda:0")
        torch.cuda.empty_cache()
        vram_mb = torch.cuda.memory_allocated() / 1024**2
        print(f"  🚀 모델 준비 완료 (현재 할당 VRAM: {vram_mb:.1f} MB)", flush=True)

    t0 = time.time()
    norm_tts = frontend.text_normalize(TEST_TEXT, split=False, text_frontend=False)
    model_input = frontend.frontend_instruct2(norm_tts, INSTRUCT_TXT, str(REF_WAV), configs["sample_rate"], "")

    chunks = []
    for out in model.tts(**model_input, stream=False, speed=1.0):
        chunks.append(out["tts_speech"])

    if chunks:
        audio = torch.cat(chunks, dim=1)
        dur = audio.shape[-1] / configs["sample_rate"]
        elapsed = time.time() - t0
        wav_path = OUT_DIR / f"cosyvoice3_{mode}_test.wav"
        mp3_path = OUT_DIR / f"cosyvoice3_{mode}_test.mp3"
        sf.write(str(wav_path), audio.cpu().numpy().squeeze(), configs["sample_rate"], subtype="PCM_16")
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_path)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✔ [{mode.upper()} 완료] 길이: {dur:.1f}초 | 소요: {elapsed:.1f}초 | RTF: {elapsed/dur:.2f}x")
        return {"mode": mode, "wav": wav_path, "mp3": mp3_path, "dur": dur, "elapsed": elapsed}
    return None

if __name__ == "__main__":
    r_8bit = run_test("8bit")
