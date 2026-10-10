#!/bin/sh
# Uses only the dedicated build directory; never copies the project's .venv.
set -eu
PROJECT_ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
BUILD_PYTHON=${BUILD_PYTHON:-"$HOME/.local/bin/python3.12"}
BUILD_UV=${BUILD_UV:-uv}
"$BUILD_UV" venv --python "$BUILD_PYTHON" --no-project --clear "$PROJECT_ROOT/build/private-release/venv"
"$BUILD_UV" pip sync --python "$PROJECT_ROOT/build/private-release/venv/bin/python" --index-url https://pypi.org/simple --require-hashes --only-binary :all: "$PROJECT_ROOT/scripts/packaging/requirements-macos-arm64.lock"
"$PROJECT_ROOT/build/private-release/venv/bin/python" -I "$PROJECT_ROOT/scripts/packaging/build_macos.py" "$@"
