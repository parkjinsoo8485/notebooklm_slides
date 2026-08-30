#!/usr/bin/env python3
"""
CosyVoice2 Anti-Hallucination Diagnostic & Strategy Test Suite
─────────────────────────────────────────────────────────────────────────────
Implements User's 4-Point Strategy:
1. 100% Pure Korean Text Normalization (소리 나는 대로, 특수문자 제거)
2. High-Purity Reference Audio (3~5s clean audio with exact transcript)
3. Quantization Comparison (FP16 vs INT8 vs NF4-4bit) + Short Chunk Division
4. Temperature & Sampling Tuning (Low top_k/top_p, temperature scaling)
─────────────────────────────────────────────────────────────────────────────
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

for attr in ("stdout", "stderr"):
    s = getattr(sys, attr)
    if hasattr(s, "buffer") and s.encoding != "utf-8":
        setattr(sys, attr, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))

PROJECT_ROOT  = Path(r"C:\My_Project\src\notebooklm_slides")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
try:
    from optimize_performance import optimize_system_and_torch
    optimize_system_and_torch(max_cpu_threads=2, lower_priority=True)
except Exception:
    pass

COSYVOICE_DIR = PROJECT_ROOT / "third_party" / "CosyVoice"
MATCHA_DIR    = COSYVOICE_DIR / "third_party" / "Matcha-TTS"
sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(MATCHA_DIR))
os.chdir(str(COSYVOICE_DIR))

import bitsandbytes as bnb
from hyperpyyaml import load_hyperpyyaml
from cosyvoice.cli.frontend import CosyVoiceFrontEnd
from cosyvoice.cli.model import CosyVoice2Model

MODEL_DIR     = COSYVOICE_DIR / "pretrained_models" / "CosyVoice2-0.5B"
OUT_DIR       = PROJECT_ROOT / "output" / "cosyvoice2_strategy_test"
OUT_DIR.mkdir(parents=True, exist_ok=True)
HTML_OUT      = PROJECT_ROOT / "output" / "cosyvoice2_strategy_player.html"

# ── 1. 정제된 프롬프트 & 테스트 문장 (순수 한글 소리 표기) ──
PROMPT_WAV    = PROJECT_ROOT / "output" / "cosyvoice2_pristine_samples" / "sample3_classic_folklore_4.8s.wav"
PROMPT_TEXT   = "옛날 옛적 한양에서 그리 멀지 않은 양주 땅 변두리에 만석이라는 농부가 살았습니다."

# Phase 1: 초단문 베이스라인 테스트
SHORT_TEST_TEXT = "안녕하세요, 테스트 음성입니다."

# Phase 2: 슬라이드 1번 대본 순수 한글 소리 정제본 (10~15자 내외 청크)
SLIDE1_CLEAN_CHUNKS = [
    "옛날 옛적,",
    "한양 북촌 명문가의 어질고 고왔던 윤 씨 마님이,",
    "하루아침에 억울한 역모의 누명을 쓰고,",
    "첩첩산중 깊은 산골로 내쫓기고 말았더랬지요.",
    "차가운 달빛조차 서럽게 얼어붙던,",
    "어느 쓸쓸한 늦가을 밤의 비극이었답니다."
]

def quantize_module(module, mode="4bit", target_classes=(nn.Linear,)):
    """Apply INT8 or NF4 quantization to linear layers"""
    for name, child in list(module.named_children()):
        if isinstance(child, target_classes):
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
            quantize_module(child, mode, target_classes)

class ControlledCosyVoiceEngine:
    def __init__(self, mode="fp16", temperature=0.7, top_p=0.8, top_k=25):
        self.mode = mode
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        
        print(f"\n[엔진 초기화] Mode: {mode.upper()} | Temp: {temperature} | Top-P: {top_p} | Top-K: {top_k}", flush=True)
        with open(MODEL_DIR / "cosyvoice2.yaml", "r") as f:
            configs = load_hyperpyyaml(f, overrides={"qwen_pretrain_path": str(MODEL_DIR / "CosyVoice-BlankEN")})
        
        self.sample_rate = configs["sample_rate"]
        self.frontend = CosyVoiceFrontEnd(
            configs["get_tokenizer"],
            configs["feat_extractor"],
            str(MODEL_DIR / "campplus.onnx"),
            str(MODEL_DIR / "speech_tokenizer_v2.onnx"),
            str(MODEL_DIR / "spk2info.pt"),
            configs["allowed_special"]
        )
        
        llm = configs["llm"]
        llm_dict = torch.load(MODEL_DIR / "llm.pt", map_location="cpu")
        llm.load_state_dict(llm_dict)
        del llm_dict
        
        # 커스텀 샘플링 파라미터 주입 (온도 및 Top-K/Top-P 조절)
        def custom_sampling(weighted_scores, decoded_tokens, sampling_k=self.top_k, top_p=self.top_p, temp=self.temperature):
            # 온도 스케일링
            scores = weighted_scores / max(temp, 1e-4)
            # Nucleus / Top-K sampling
            sorted_value, sorted_idx = scores.softmax(dim=0).sort(descending=True, stable=True)
            prob, indices = [], []
            cum_prob = 0.0
            for i in range(len(sorted_idx)):
                if cum_prob < top_p and len(prob) < sampling_k:
                    cum_prob += sorted_value[i]
                    prob.append(sorted_value[i])
                    indices.append(sorted_idx[i])
                else:
                    break
            prob = torch.tensor(prob).to(weighted_scores)
            indices = torch.tensor(indices, dtype=torch.long).to(weighted_scores.device)
            top_ids = indices[prob.multinomial(1, replacement=True)].item()
            return top_ids
            
        llm.sampling = custom_sampling
        
        if mode in ("4bit", "8bit"):
            print(f"  - bitsandbytes {mode} 양자화 적용 중...", flush=True)
            quantize_module(llm.llm.model.model.layers, mode=mode)
            
        flow = configs["flow"]
        hift = configs["hift"]
        flow.load_state_dict(torch.load(MODEL_DIR / "flow.pt", map_location="cpu"))
        hift.load_state_dict(torch.load(MODEL_DIR / "hift.pt", map_location="cpu"))
        
        self.model = CosyVoice2Model(llm, flow, hift, fp16=(mode != "fp32"))
        if torch.cuda.is_available():
            self.model.llm.to("cuda:0")
            self.model.flow.to("cuda:0")
            self.model.hift.to("cuda:0")
            torch.cuda.empty_cache()
            vram_mb = torch.cuda.memory_allocated() / 1024**2
            print(f"  🚀 모델 준비 완료 (현재 할당 VRAM: {vram_mb:.1f} MB)", flush=True)

    def synthesize(self, text, prompt_text, prompt_wav):
        # ── 핵심 수정: text_normalize는 <|ko|> 태그 없이 먼저 수행해야 함 ──
        # <|ko|> 태그가 포함된 채로 text_normalize를 호출하면 'skip frontend'
        # 분기가 활성화되어 한국어 전처리가 통째로 무시됨.
        # 또한 contains_chinese()는 한자만 감지하므로, 한글은 영어 경로로 빠짐.
        # 해결: 한글 텍스트를 먼저 정규화 → 이후 <|ko|> 태그 접두 → 토크나이저 전달
        import re
        from cosyvoice.utils.frontend_utils import contains_chinese

        def normalize_korean(frontend, raw_text):
            """한국어 전용 정규화: contains_chinese() 우회 패치 포함"""
            # 한글(Hangul) 존재 여부를 직접 체크
            has_hangul = bool(re.search(r'[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]', raw_text))
            if has_hangul:
                # contains_chinese를 임시로 패치하여 한국어도 중국어 경로(CJK path)로 처리
                import cosyvoice.utils.frontend_utils as fu
                orig_fn = fu.contains_chinese
                import cosyvoice.cli.frontend as cf_mod
                orig_cf = cf_mod.contains_chinese
                fu.contains_chinese = lambda t: True
                cf_mod.contains_chinese = lambda t: True
                try:
                    result = frontend.text_normalize(raw_text, split=False, text_frontend=True)
                finally:
                    fu.contains_chinese = orig_fn
                    cf_mod.contains_chinese = orig_cf
                return result
            else:
                return frontend.text_normalize(raw_text, split=False, text_frontend=True)

        # 1. 텍스트를 정규화(한국어 경로)
        norm_prompt = normalize_korean(self.frontend, prompt_text)
        norm_tts_body = normalize_korean(self.frontend, text)

        # 2. 정규화 완료된 텍스트에 <|ko|> 태그를 접두
        norm_tts = f"<|ko|>{norm_tts_body}"

        print(f"  [DEBUG] norm_prompt: {repr(norm_prompt)}", flush=True)
        print(f"  [DEBUG] norm_tts:    {repr(norm_tts)}", flush=True)

        model_input = self.frontend.frontend_zero_shot(norm_tts, norm_prompt, str(prompt_wav), self.sample_rate, "")
        chunks = []
        for out in self.model.tts(**model_input, stream=False, speed=1.0):
            chunks.append(out["tts_speech"])
        if chunks:
            return torch.cat(chunks, dim=1)
        return None

def run_test_suite():
    print("=" * 70, flush=True)
    print(" 🛠️ CosyVoice2 외계어 방지 전략 검증 테스트 스위트", flush=True)
    print("=" * 70, flush=True)
    
    results = []
    
    # ── [전략 1 & 4 검증] 1단계: 초단문 베이스라인 테스트 (FP16 vs 4-Bit) ──
    # 온도를 0.3으로 낮춰 결정론적이고 안정적인 발음 유도
    test_cases = [
        {"name": "01_초단문_FP16_저온도(0.3)", "mode": "fp16", "temp": 0.3, "top_p": 0.5, "top_k": 10, "text": SHORT_TEST_TEXT},
        {"name": "02_초단문_4Bit_저온도(0.3)", "mode": "4bit", "temp": 0.3, "top_p": 0.5, "top_k": 10, "text": SHORT_TEST_TEXT},
        {"name": "03_슬라이드1_청크분할_FP16_저온도(0.3)", "mode": "fp16", "temp": 0.3, "top_p": 0.6, "top_k": 15, "chunks": SLIDE1_CLEAN_CHUNKS},
        {"name": "04_슬라이드1_청크분할_4Bit_저온도(0.3)", "mode": "4bit", "temp": 0.3, "top_p": 0.6, "top_k": 15, "chunks": SLIDE1_CLEAN_CHUNKS},
    ]
    
    # 현재는 가장 핵심적인 2가지(초단문 FP16 vs 초단문 4Bit)를 먼저 신속하게 생성하여 비교
    for tc in test_cases[:2]:
        print(f"\n=======================================================", flush=True)
        print(f" ▶ 실행: {tc['name']}", flush=True)
        print(f"   텍스트: \"{tc['text']}\"", flush=True)
        print(f"=======================================================", flush=True)
        
        t0 = time.time()
        engine = ControlledCosyVoiceEngine(
            mode=tc["mode"], temperature=tc["temp"], top_p=tc["top_p"], top_k=tc["top_k"]
        )
        audio = engine.synthesize(tc["text"], PROMPT_TEXT, PROMPT_WAV)
        elapsed = time.time() - t0
        
        if audio is not None:
            wav_path = OUT_DIR / f"{tc['name']}.wav"
            mp3_path = OUT_DIR / f"{tc['name']}.mp3"
            audio_np = audio.cpu().numpy().squeeze()
            sf.write(str(wav_path), audio_np, engine.sample_rate, subtype="PCM_16")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            dur = len(audio_np) / engine.sample_rate
            print(f"   ✔ 생성 완료! 재생길이: {dur:.1f}초 (소요: {elapsed:.1f}초)", flush=True)
            results.append({
                "name": tc["name"],
                "text": tc["text"],
                "dur": dur,
                "elapsed": elapsed,
                "mp3": mp3_path
            })
        else:
            print(f"   ❌ 실패", flush=True)
            
        # 메모리 정리
        del engine
        torch.cuda.empty_cache()
        
    # 결과 비교 HTML 플레이어 생성
    player_items = ""
    for r in results:
        with open(r["mp3"], "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        player_items += f"""
        <div class="card">
            <h3>{r['name']}</h3>
            <p class="meta">⏱️ 재생 시간: {r['dur']:.1f}초 | ⚡ 합성 소요: {r['elapsed']:.1f}초</p>
            <p class="text">"{r['text']}"</p>
            <audio controls src="data:audio/mp3;base64,{b64}"></audio>
        </div>
        """
        
    with open(PROMPT_WAV, "rb") as f:
        prompt_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>CosyVoice2 외계어 방지 전략 검증 플레이어</title>
    <style>
        body {{ background: #0b0f19; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 30px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #58a6ff; font-size: 22px; margin-bottom: 20px; }}
        .ref-box {{ background: #161b22; border: 1px solid #d29922; border-radius: 12px; padding: 18px; margin-bottom: 25px; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; }}
        .card h3 {{ margin-top: 0; color: #7ee787; font-size: 16px; }}
        .meta {{ font-size: 12px; color: #8b949e; margin-bottom: 8px; }}
        .text {{ font-size: 14px; color: #c9d1d9; background: #0d1117; padding: 10px 14px; border-radius: 8px; }}
        audio {{ width: 100%; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ CosyVoice2 외계어 방지 전략 진단 결과</h1>
        <div class="ref-box">
            <strong>🎧 참조 원본 (sample3_classic_folklore_4.8s.wav)</strong>
            <p class="text">"{PROMPT_TEXT}"</p>
            <audio controls src="data:audio/wav;base64,{prompt_b64}"></audio>
        </div>
        {player_items}
    </div>
</body>
</html>"""
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n🌐 플레이어 생성 완료: {HTML_OUT}", flush=True)

if __name__ == "__main__":
    run_test_suite()
