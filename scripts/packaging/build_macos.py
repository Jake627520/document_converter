"""Build an audited local macOS arm64 candidate; never publishes a release."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_notices import collect, digest

APP_NAME = "Document Converter"
EXCLUDES = ["document_converter.pipeline", "document_converter.detector", "document_converter.engines", "document_converter.cli", "fitz", "pymupdf", "docling", "marker", "magic_pdf", "mineru", "torch", "pytest", "httpx", "pip", "setuptools", "tkinter", "uvloop", "httptools", "websockets", "watchfiles"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/private-release/candidate")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    staging = output / "Document-Converter-macos-arm64-local-candidate"
    if staging.exists():
        raise RuntimeError(f"Choose an empty output directory; existing candidate preserved: {staging}")
    # Missing legal documents or runtime provenance stops before PyInstaller.
    legal = output / "legal-staging"
    collect(legal)
    work = output / "pyinstaller-work"
    spec = output / "text-release.spec"
    spec.write_text(f'''import json
from pathlib import Path
root = Path({str(ROOT)!r})
venv = Path({str(Path(sys.prefix).resolve())!r})
a = Analysis([str(root / "scripts/packaging/release_launcher.py")], pathex=[str(root)], binaries=[], datas=[({str(legal)!r}, "legal")], hiddenimports=["uvicorn.logging", "uvicorn.loops.asyncio", "uvicorn.protocols.http.h11_impl", "uvicorn.lifespan.off"], hookspath=[], hooksconfig={{}}, runtime_hooks=[], excludes={EXCLUDES!r}, noarchive=False)
forbidden = {EXCLUDES[:15]!r}
records = []
for name, source, kind in a.pure + a.binaries + a.datas:
    if any(name == item or name.startswith(item + ".") or name.startswith(item + "/") for item in forbidden):
        raise RuntimeError("Forbidden frozen entry: " + name)
    source_path = Path(source).resolve()
    if "site-packages" in str(source_path) and not source_path.is_relative_to(venv):
        raise RuntimeError("External site-packages entry: " + source)
    records.append({{"name": name, "source": source, "kind": kind}})
Path({str(output / "FROZEN_INVENTORY.json")!r}).write_text(json.dumps(records, indent=2) + "\\n")
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={APP_NAME!r}, debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=True, target_arch="arm64", codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name={APP_NAME!r})
app = BUNDLE(coll, name={APP_NAME + '.app'!r}, icon=None, bundle_identifier="local.documentconverter.text", version="0.2.0", info_plist={{"NSHighResolutionCapable": True}})
''')
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    subprocess.run([sys.executable, "-I", "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN", "--distpath", str(output / "app-build"), "--workpath", str(work), str(spec)], cwd=ROOT, env=env, check=True)
    staging.mkdir()
    app = staging / f"{APP_NAME}.app"
    shutil.move(str(output / "app-build" / app.name), app)
    shutil.copytree(legal, staging / "legal")
    frozen = json.loads((output / "FROZEN_INVENTORY.json").read_text())
    (staging / "FROZEN_INVENTORY.json").write_text(json.dumps(frozen, indent=2) + "\n")
    # Original dependency sources and hashes accompany the app and outer ZIP.
    for legal_dir in (staging / "legal", app / "Contents/Resources/legal"):
        shutil.copyfile(output / "FROZEN_INVENTORY.json", legal_dir / "FROZEN_INVENTORY.json")
    subprocess.run(["/usr/bin/codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)
    (staging / "LOCAL-CANDIDATE.txt").write_text("Local test candidate only. Markdown and UTF-8 text to Markdown/HTML.\nApple Silicon macOS only; no PDF/OCR/Office engines or models.\nNo Developer ID signing or notarization; no distribution approval.\nClosing the browser does not stop the app; quit Document Converter in Activity Monitor.\n")
    source_names = ["web_app.py", "web_security.py", "formats.py", "writer.py", "renderer.py", "models.py", "cleaner.py", "__init__.py"]
    manifest = {"distribution_ready": False, "profile": "text-only", "source_sha256": {"document_converter/" + name: digest(ROOT / "document_converter" / name) for name in source_names}, "lock_sha256": digest(ROOT / "scripts/packaging/requirements-macos-arm64.lock"), "files": [{"path": path.relative_to(staging).as_posix(), "sha256": digest(path)} for path in sorted(staging.rglob("*")) if path.is_file() and not path.is_symlink()]}
    (staging / "BUILD_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = output / (staging.name + ".zip")
    subprocess.run(["/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(staging), str(archive)], check=True)
    (output / (archive.name + ".sha256")).write_text(digest(archive) + "  " + archive.name + "\n")
    print(json.dumps({"app": str(app), "zip": str(archive), "zip_sha256": digest(archive), "distribution_ready": False}, indent=2))


if __name__ == "__main__":
    main()
