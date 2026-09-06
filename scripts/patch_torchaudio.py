"""
patch_torchaudio.py
torchaudio의 _extension/utils.py에서 _load_lib()가 실패하면
조용히 무시하도록 패치하여, Windows Store Python 환경에서도
torchaudio의 스펙트럼/파형 기능이 작동하게 만드는 1회성 패치 스크립트.
"""
import sys
import os
from pathlib import Path

# torchaudio 설치 경로 탐지
ta_base = None
for p in sys.path:
    cand = Path(p) / "torchaudio"
    if (cand / "_extension").exists():
        ta_base = cand
        break

if ta_base is None:
    import importlib.util
    spec = importlib.util.find_spec("torchaudio")
    if spec:
        ta_base = Path(spec.origin).parent

if ta_base is None:
    print("ERROR: torchaudio not found")
    sys.exit(1)

utils_path = ta_base / "_extension" / "utils.py"
print(f"Patching: {utils_path}")

original = utils_path.read_text(encoding="utf-8")

# 이미 패치되었으면 스킵
if "# [PATCHED] DLL load failure silenced" in original:
    print("Already patched. Skipping.")
else:
    # _load_lib 함수에서 예외를 잡도록 래핑
    old_block = (
        "    torch.ops.load_library(path)\n"
    )
    new_block = (
        "    try:\n"
        "        torch.ops.load_library(path)\n"
        "    except (OSError, FileNotFoundError) as e:\n"
        "        import warnings\n"
        "        warnings.warn(f'[PATCHED] DLL load failure silenced: {e}. Native audio codecs may be unavailable.')\n"
        "        return  # # [PATCHED] DLL load failure silenced\n"
    )
    if old_block in original:
        patched = original.replace(old_block, new_block)
        utils_path.write_text(patched, encoding="utf-8")
        print("SUCCESS: Patched torchaudio/_extension/utils.py")
    else:
        print(f"ERROR: Target block not found. Manual inspection required.")
        print(repr(original[original.find("def _load_lib"):original.find("def _load_lib")+300]))
        sys.exit(1)
