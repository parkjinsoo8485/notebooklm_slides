"""
patch_torchaudio_full.py
torchaudio의 _extension/__init__.py 전체를 패치하여
DLL 로드 실패 시 조용히 무시하고 계속 진행하도록 만드는 스크립트.
Windows Store Python 환경의 DLL 경로 문제 해결용.
"""
import sys
from pathlib import Path

ta_base = None
for p in sys.path:
    cand = Path(p) / "torchaudio"
    if (cand / "_extension").exists():
        ta_base = cand
        break

if ta_base is None:
    import importlib.util
    spec = importlib.util.find_spec("torchaudio")
    if spec and spec.origin:
        ta_base = Path(spec.origin).parent

if ta_base is None:
    print("ERROR: torchaudio not found in sys.path")
    sys.exit(1)

ext_init = ta_base / "_extension" / "__init__.py"
print(f"Patching: {ext_init}")

original = ext_init.read_text(encoding="utf-8")

if "# [FULLY_PATCHED]" in original:
    print("Already fully patched. Skipping.")
    sys.exit(0)

# 전체 교체: DLL 로드 블록을 try-except로 감쌈
old_block = """if _IS_TORCHAUDIO_EXT_AVAILABLE:
    _load_lib("libtorchaudio")

    import torchaudio.lib._torchaudio  # noqa

    _check_cuda_version()
    _IS_RIR_AVAILABLE = torchaudio.lib._torchaudio.is_rir_available()
    _IS_ALIGN_AVAILABLE = torchaudio.lib._torchaudio.is_align_available()"""

new_block = """if _IS_TORCHAUDIO_EXT_AVAILABLE:
    try:  # [FULLY_PATCHED] Windows Store Python DLL fix
        _load_lib("libtorchaudio")
        import torchaudio.lib._torchaudio  # noqa
        _check_cuda_version()
        _IS_RIR_AVAILABLE = torchaudio.lib._torchaudio.is_rir_available()
        _IS_ALIGN_AVAILABLE = torchaudio.lib._torchaudio.is_align_available()
    except (OSError, ImportError) as _e:
        import warnings
        warnings.warn(f"[FULLY_PATCHED] torchaudio native ext load failed (DLL missing): {_e}. Native audio codecs unavailable, but core ops should work.")"""

if old_block in original:
    patched = original.replace(old_block, new_block)
    ext_init.write_text(patched, encoding="utf-8")
    print("SUCCESS: Fully patched torchaudio/_extension/__init__.py")
else:
    print("ERROR: Target block not found. Printing relevant section:")
    start = original.find("_IS_TORCHAUDIO_EXT_AVAILABLE")
    print(repr(original[start:start+600]))
    sys.exit(1)
