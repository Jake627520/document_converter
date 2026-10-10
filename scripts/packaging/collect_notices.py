"""Collect exact installed dependency notices; fail on incomplete provenance."""
from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
import platform
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import profiles

TOOLS = {"altgraph", "macholib", "packaging", "pyinstaller", "pyinstaller-hooks-contrib", "setuptools"}
LEGAL_SOURCES = {"LICENSE": "LICENSE", "THIRD_PARTY_NOTICES.md": "THIRD_PARTY_NOTICES.md", "LICENSE_AUDIT.md": "docs/LICENSE_AUDIT.md", "PRIVATE_DISTRIBUTION.md": "docs/PRIVATE_DISTRIBUTION.md"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def exact_dependencies(profile):
    expected = {}
    for line in (ROOT / "scripts/packaging" / f"{profile.requirements_stem}.txt").read_text().splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        name, version = entry.split("==")
        expected[normalized(name)] = version
    actual = {normalized(dist.metadata["Name"]): dist.version for dist in metadata.distributions()}
    if actual != expected:
        raise RuntimeError(f"Isolated build dependencies differ from fixed list: expected={expected}, actual={actual}")
    forbidden = profile.forbidden_distributions.intersection(actual)
    if forbidden:
        raise RuntimeError(f"Forbidden release dependencies installed: {sorted(forbidden)}")
    return expected


def check_runtime_provenance():
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Run in a dedicated virtual environment")
    if platform.system() != "Darwin" or platform.machine() != "arm64" or platform.python_version() != "3.12.13":
        raise RuntimeError("This release lock targets CPython 3.12.13 on macOS arm64 only")
    cfg = Path(sys.prefix) / "pyvenv.cfg"
    if "include-system-site-packages = false" not in cfg.read_text().lower():
        raise RuntimeError("System site-packages must be disabled")
    for item in sys.path:
        if "site-packages" in item and not Path(item).resolve().is_relative_to(Path(sys.prefix).resolve()):
            raise RuntimeError(f"External site-packages path: {item}")
    native = ROOT / "scripts/packaging/python-runtime"
    provenance = json.loads((native / "provenance.json").read_text())
    installed_build = Path(sys.base_prefix) / "BUILD"
    if not installed_build.is_file() or installed_build.read_text().strip() != provenance["build"]:
        raise RuntimeError("Python standalone build does not match audited native provenance")
    python_meta = json.loads((native / "PYTHON.json").read_text())
    if python_meta["python_version"] != platform.python_version() or python_meta["target_triple"] != provenance["target_triple"]:
        raise RuntimeError("Python native metadata target mismatch")
    installed_license = Path(sys.base_prefix) / "lib/python3.12/LICENSE.txt"
    if digest(installed_license) != digest(native / "INSTALLED_PYTHON_LICENSE.txt"):
        raise RuntimeError("Installed Python license differs from audited artifact")
    for variants in python_meta["build_info"]["extensions"].values():
        for variant in variants:
            native_links = [link for link in variant["links"] if not link.get("system") and not link.get("framework")]
            for license_path in variant.get("license_paths", []):
                if native_links and not (native / license_path).is_file():
                    raise RuntimeError(f"Missing original native notice: {license_path}")
            if native_links and not variant.get("license_paths") and not variant.get("license_public_domain"):
                raise RuntimeError(f"Unreviewed native component: {native_links}")
    return provenance, python_meta


def collect(destination, profile=None):
    profile = profile or profiles.TEXT
    destination = Path(destination)
    for output, source in LEGAL_SOURCES.items():
        path = ROOT / source
        if not path.is_file() or not path.read_text().strip():
            raise RuntimeError(f"Missing required legal document: {path}")
    provenance, python_meta = check_runtime_provenance()
    expected = exact_dependencies(profile)
    destination.mkdir(parents=True, exist_ok=True)
    for output, source in LEGAL_SOURCES.items():
        shutil.copyfile(ROOT / source, destination / output)
    packages = []
    for dist in sorted(metadata.distributions(), key=lambda d: normalized(d.metadata["Name"])):
        name = normalized(dist.metadata["Name"])
        notices = []
        for item in dist.files or []:
            if re.match(r"(?i)^(license|copying|notice)(?:[._-].*)?$", Path(item).name):
                source = Path(dist.locate_file(item))
                if not source.is_file():
                    raise RuntimeError(f"Missing installed notice: {source}")
                # Preserve nested paths to avoid overwriting vendored license texts.
                relative = Path("third-party") / name / Path(str(item))
                output = destination / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, output)
                notices.append({"path": relative.as_posix(), "sha256": digest(output)})
        if not notices:
            raise RuntimeError(f"No original license/notice in installed wheel: {name}")
        license_name = dist.metadata.get("License-Expression") or dist.metadata.get("License")
        packages.append({"name": name, "version": expected[name], "role": "build-tool" if name in TOOLS else "runtime", "license_metadata": license_name, "license_classifiers": [c for c in dist.metadata.get_all("Classifier", []) if c.startswith("License ::")], "metadata_sha256": hashlib.sha256(dist.read_text("METADATA").encode()).hexdigest(), "record_sha256": hashlib.sha256((dist.read_text("RECORD") or "").encode()).hexdigest(), "notices": notices})
    native = ROOT / "scripts/packaging/python-runtime"
    shutil.copytree(native, destination / "third-party/python-runtime", dirs_exist_ok=True)
    for suffix in ("txt", "lock"):
        name = f"{profile.requirements_stem}.{suffix}"
        shutil.copyfile(ROOT / "scripts/packaging" / name, destination / name)
    notices = [{"path": path.relative_to(destination).as_posix(), "sha256": digest(path)} for path in sorted((destination / "third-party/python-runtime").rglob("*")) if path.is_file()]
    inventory = {"profile": profile.manifest_profile, "target": "macos-arm64", "python": {"version": platform.python_version(), "provenance": provenance, "metadata_licenses": python_meta["licenses"], "notices": notices}, "packages": packages, "legal_documents": [{"path": name, "sha256": digest(destination / name)} for name in LEGAL_SOURCES], "distribution_ready": False, "remaining_review": "Confirm rights owner and authorized recipients, exact frozen native module inventory, signing/notarization and target-machine installation before distribution."}
    (destination / "THIRD_PARTY_INVENTORY.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    return inventory
