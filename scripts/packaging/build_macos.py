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
import profiles
from collect_notices import collect, digest

APP_NAME = "Document Converter"


def render_spec(profile, legal: Path, marker: Path, inventory: Path, root: Path = ROOT, venv: Path | None = None) -> str:
    """Render the PyInstaller spec for one profile; kept separate so it can be checked."""
    venv = venv or Path(sys.prefix).resolve()
    return f'''import json
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata
root = Path({str(root)!r})
venv = Path({str(venv)!r})
datas = [({str(legal)!r}, "legal"), ({str(marker)!r}, ".")]
binaries = []
hiddenimports = {profile.hidden_imports!r}
for package in {profile.collect_all!r}:
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden
for distribution in {profile.copy_metadata!r}:
    datas += copy_metadata(distribution)
a = Analysis([str(root / "scripts/packaging/release_launcher.py")], pathex=[str(root)], binaries=binaries, datas=datas, hiddenimports=hiddenimports, hookspath=[], hooksconfig={{}}, runtime_hooks=[], excludes={profile.excludes!r}, noarchive=False)
forbidden = {profile.forbidden!r}
records = []
for name, source, kind in a.pure + a.binaries + a.datas:
    if any(name == item or name.startswith(item + ".") or name.startswith(item + "/") for item in forbidden):
        raise RuntimeError("Forbidden frozen entry: " + name)
    source_path = Path(source).resolve()
    if "site-packages" in str(source_path) and not source_path.is_relative_to(venv):
        raise RuntimeError("External site-packages entry: " + source)
    records.append({{"name": name, "source": source, "kind": kind}})
Path({str(inventory)!r}).write_text(json.dumps(records, indent=2) + "\\n")
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={APP_NAME!r}, debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=True, target_arch="arm64", codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name={APP_NAME!r})
app = BUNDLE(coll, name={APP_NAME + '.app'!r}, icon=None, bundle_identifier={profile.bundle_identifier!r}, version="0.2.0", info_plist={{"NSHighResolutionCapable": True}})
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/private-release/candidate")
    parser.add_argument("--profile", choices=sorted(profiles.PROFILES), default="text", help="Reviewed release profile to build")
    args = parser.parse_args()
    profile = profiles.get(args.profile)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    staging = output / profile.candidate_name
    if staging.exists():
        raise RuntimeError(f"Choose an empty output directory; existing candidate preserved: {staging}")
    # Missing legal documents or runtime provenance stops before PyInstaller.
    legal = output / "legal-staging"
    collect(legal, profile)
    marker = output / "release-profile"
    marker.mkdir(exist_ok=True)
    (marker / "release_profile.txt").write_text(profile.name + "\n")
    work = output / "pyinstaller-work"
    spec = output / f"{profile.name}-release.spec"
    spec.write_text(render_spec(profile, legal=legal, marker=marker, inventory=output / "FROZEN_INVENTORY.json"))
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
    (staging / "LOCAL-CANDIDATE.txt").write_text(profile.candidate_notice)
    manifest = {"distribution_ready": False, "profile": profile.manifest_profile, "source_sha256": {"document_converter/" + name: digest(ROOT / "document_converter" / name) for name in profile.sources}, "lock_sha256": digest(ROOT / "scripts/packaging" / f"{profile.requirements_stem}.lock"), "files": [{"path": path.relative_to(staging).as_posix(), "sha256": digest(path)} for path in sorted(staging.rglob("*")) if path.is_file() and not path.is_symlink()]}
    (staging / "BUILD_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = output / (staging.name + ".zip")
    subprocess.run(["/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(staging), str(archive)], check=True)
    (output / (archive.name + ".sha256")).write_text(digest(archive) + "  " + archive.name + "\n")
    print(json.dumps({"profile": profile.manifest_profile, "app": str(app), "zip": str(archive), "zip_sha256": digest(archive), "distribution_ready": False}, indent=2))


if __name__ == "__main__":
    main()
