"""Check that every pinned wheel of a profile carries its own license notice.

`collect_notices.py` copies each dependency's notice out of the installed wheel
and fails the build when one carries none. That check can only run on a machine
with the profile installed, and a dependency bump can remove a notice upstream
without changing anything in this repository. This tool answers the same
question from the pinned requirements alone, on any machine with network
access: it finds the exact wheel each locked hash names, reads it without
installing it, and applies the build's own `is_notice` rule.

    python3 scripts/packaging/audit_notices.py --profile pdf

A non-zero exit names each distribution that ships no notice. Re-run it after
changing a pinned version, and record the outcome with the change.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import profiles
from collect_notices import is_notice, normalized

PYPI = "https://pypi.org/pypi/{name}/{version}/json"


def pinned(profile) -> dict[str, dict]:
    """Read one profile's lock file as {distribution: {version, hashes}}."""
    path = Path(__file__).resolve().parent / f"{profile.requirements_stem}.lock"
    entries: dict[str, dict] = {}
    name = None
    for line in path.read_text().splitlines():
        pin = re.match(r"^([A-Za-z0-9._-]+)==([^\s\\]+)", line.strip())
        if pin:
            name = normalized(pin.group(1))
            entries[name] = {"version": pin.group(2), "hashes": set()}
        digest = re.search(r"--hash=sha256:([0-9a-f]{64})", line)
        if digest and name:
            entries[name]["hashes"].add(digest.group(1))
    if not entries:
        raise RuntimeError(f"No pinned distributions in {path}")
    return entries


def wheel_for(name: str, entry: dict) -> dict:
    """The released wheel whose digest the lock file pins."""
    with urllib.request.urlopen(PYPI.format(name=name, version=entry["version"]), timeout=60) as response:
        released = json.load(response)["urls"]
    for artifact in released:
        if artifact["packagetype"] == "bdist_wheel" and artifact["digests"]["sha256"] in entry["hashes"]:
            return artifact
    raise RuntimeError(f"{name}=={entry['version']}: no released wheel matches the locked hash")


def notices_in(url: str) -> list[str]:
    with urllib.request.urlopen(url, timeout=300) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    return [item for item in archive.namelist() if not item.endswith("/") and is_notice(item)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profile", choices=sorted(profiles.PROFILES), default="pdf")
    args = parser.parse_args(argv)
    profile = profiles.PROFILES[args.profile]

    missing = []
    for name, entry in sorted(pinned(profile).items()):
        artifact = wheel_for(name, entry)
        found = notices_in(artifact["url"])
        print(f"{name:30} {entry['version']:12} {len(found):3} notice file(s)")
        if not found:
            missing.append(f"{name}=={entry['version']} ({artifact['filename']})")
    if missing:
        print(f"\n{len(missing)} pinned wheel(s) ship no license notice:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
        print("\nThe build will refuse these. Pin a release that ships its notice.", file=sys.stderr)
        return 1
    print(f"\nEvery pinned wheel of the {args.profile} profile carries its own notice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
