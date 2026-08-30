#!/usr/bin/env python3
"""
Performance & System Responsiveness Optimizer
- Prevents system freezing/lagging during Heavy AI / TTS / PyTorch execution.
- Optimizes for 4-Core CPU + GTX 1050 Ti (4GB VRAM) environment.
"""

import os
import sys
import gc

def optimize_system_and_torch(max_cpu_threads: int = 2, lower_priority: bool = True):
    """
    1. Sets CPU thread limits for PyTorch, OpenMP, MKL, NumExpr.
    2. Lowers Windows Process Priority to BELOW_NORMAL (prevents mouse/OS lag).
    3. Configures CUDA memory management to prevent memory fragmentation and swapping.
    """
    # ── 1. CPU Thread Limitation (4코어 중 2개만 AI 연산에 할당하여 OS 여유 확보) ──
    threads_str = str(max(1, max_cpu_threads))
    os.environ["OMP_NUM_THREADS"] = threads_str
    os.environ["MKL_NUM_THREADS"] = threads_str
    os.environ["OPENBLAS_NUM_THREADS"] = threads_str
    os.environ["VECLIB_MAXIMUM_THREADS"] = threads_str
    os.environ["NUMEXPR_NUM_THREADS"] = threads_str
    
    # PyTorch CUDA Memory Allocation 설정 (메모리 단편화 방지)
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    try:
        import torch
        torch.set_num_threads(max_cpu_threads)
        if hasattr(torch, "set_num_interop_threads"):
            torch.set_num_interop_threads(max_cpu_threads)
    except Exception:
        pass

    # ── 2. Windows 프로세스 우선순위 조정 (BELOW_NORMAL) ──
    # OS UI, 브라우저, 마우스 입력이 절대 끊기지 않도록 백그라운드 우선순위로 강등
    if lower_priority and sys.platform == "win32":
        try:
            import psutil
            p = psutil.Process(os.getpid())
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        except Exception:
            pass

    # ── 3. GPU VRAM 초기화 및 캐시 정리 ──
    try:
        import torch
        if torch.cuda.is_available():
            gc.collect()
            torch.cuda.empty_cache()
    except Exception:
        pass

if __name__ == "__main__":
    optimize_system_and_torch(max_cpu_threads=2)
    print("[Optimizer] System & PyTorch responsiveness optimization applied.")
