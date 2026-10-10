#!/bin/sh
# Uses only the dedicated build directory; never copies the project's .venv.
# RELEASE_PROFILE selects the reviewed profile: text (default) or pdf.
set -eu
PROJECT_ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
BUILD_PYTHON=${BUILD_PYTHON:-"$HOME/.local/bin/python3.12"}
BUILD_UV=${BUILD_UV:-uv}
RELEASE_PROFILE=${RELEASE_PROFILE:-text}
case "$RELEASE_PROFILE" in
  text) LOCK_STEM=requirements-macos-arm64; VENV_DIR=venv ;;
  pdf) LOCK_STEM=requirements-macos-arm64-pdf; VENV_DIR=venv-pdf ;;
  *) echo "RELEASE_PROFILE must be text or pdf" >&2; exit 2 ;;
esac
"$BUILD_UV" venv --python "$BUILD_PYTHON" --no-project --clear "$PROJECT_ROOT/build/private-release/$VENV_DIR"
"$BUILD_UV" pip sync --python "$PROJECT_ROOT/build/private-release/$VENV_DIR/bin/python" --index-url https://pypi.org/simple --require-hashes --only-binary :all: "$PROJECT_ROOT/scripts/packaging/$LOCK_STEM.lock"
"$PROJECT_ROOT/build/private-release/$VENV_DIR/bin/python" -I "$PROJECT_ROOT/scripts/packaging/build_macos.py" --profile "$RELEASE_PROFILE" "$@"
