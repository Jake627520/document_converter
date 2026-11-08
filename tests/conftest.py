import importlib.util
import os
import sys

# Two test modules need what most machines lack, and are left out rather than
# skipped where it is missing, because the CI jobs fail on any skip. The job
# that provides it sets the variable, so there the module is always collected
# and a missing dependency fails instead of vanishing.
collect_ignore = []

# Apple's Vision framework exists only on macOS with PyObjC installed.
if not os.environ.get("REQUIRE_APPLE_VISION") and not (
    sys.platform == "darwin" and importlib.util.find_spec("Vision") is not None
):
    collect_ignore.append("test_apple_vision_macos.py")

# Docling's model pipeline downloads its models on first use.
if not os.environ.get("REQUIRE_DOCLING_MODELS"):
    collect_ignore.append("test_docling_ocr_models.py")
