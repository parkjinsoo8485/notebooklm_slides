# CosyVoice Korean Text-to-Speech & Zero-Shot Guidelines & Lessons Learned

## 1. Background & Root Cause Analysis (Crucial Lesson)
* **CosyVoice 1.0 & 2.0 (`CosyVoice-300M`, `CosyVoice2-0.5B`)**:
  - **Supported Training Languages**: Chinese (Mandarin), English, Japanese, Cantonese (4 languages ONLY).
  - **Behavior on Korean**: Although Korean characters can be passed into the Qwen/tiktoken tokenizer, the underlying LLM weights were **NEVER trained on Korean speech-text alignments**. Consequently, attempting to synthesize Korean text on CosyVoice 1.0 or 2.0 produces **unavoidable hallucination / alien sounds (외계어)**, regardless of text normalization, temperature scaling, or prompt audio quality.
* **Fun-CosyVoice 3.0 (`Fun-CosyVoice3-0.5B-2512`)**:
  - **Official Korean Support**: Released in Dec 2025 by Alibaba FunAudioLLM. Formally covers **9 languages including Korean (`ko`)**, with large-scale bilingual/multilingual speech alignment.
  - **Mandatory Requirement**: Always use `Fun-CosyVoice3-0.5B` or higher when synthesizing Korean. Never attempt to use `CosyVoice2-0.5B` for Korean.

## 2. Model & API Invocation Rules
1. **Always Consult Official Model Cards First**:
   - Before attempting fine-grained tuning or debugging hallucination in third-party models, verify the exact training dataset language list from the official paper/repo (`README.md`, model card).
2. **Use High-Level AutoModel / CosyVoice3 API**:
   - Do NOT manually hack internal LLM inference loops or inject custom token transformations unless validated against the official `example.py`.
   - In CosyVoice 3.0, use `AutoModel(model_dir='pretrained_models/Fun-CosyVoice3-0.5B')` or `CosyVoice3`.
3. **Korean Text Formatting & Prompt Matching**:
   - Instruct prompt format in CosyVoice 3.0: `"You are a helpful assistant.<|endofprompt|><synthesized_text>"`
   - Prompt Audio: Clean, background-music-free, natural sentence boundaries (3~10 seconds).
   - Never clip mid-syllable or provide mismatched transcripts for zero-shot prompts.

## 3. Hardware & Quantization on GTX 1050 Ti (4GB VRAM)
- Model size is ~0.5B parameters (~1.89GB in FP16 / ~1GB in 4-Bit NF4).
- Keep inference within manageable chunk sizes (15~30 characters per chunk) to avoid VRAM exhaustion and maintain responsive RTF.
