# License and Third-party Review Status

**Document updated:** 2026-10-08
**Repository posture:** intended to remain private during development; actual repository visibility must be checked in GitHub settings.
**Purpose:** record controls present in this repository and identify license questions that still require version-specific verification.

## Current repository controls

- The default dependency list and optional engine groups are declared in `pyproject.toml`. Marker and MinerU are not listed in the default dependency array.
- The adapters invoke Marker/MinerU command-line programs; this repository does not bundle their model weights.
- `.github/workflows/security-audit.yml` contains secret, vulnerability, and package-license checks. These checks apply to the workflow's installed dependency environment and their results must be reviewed for each run.
- The repository's private visibility, if enabled, limits access but does not itself establish that use, copying, or distribution complies with third-party terms.

These are repository configuration observations, not a legal clearance or a guarantee that every runtime dependency or deployment path is compliant.

## Items not verified in this audit

No version-by-version review of current upstream license texts or resolved transitive dependencies was performed for this document update. The following also remain unverified:

1. Exact licenses and notices for the resolved versions of Docling, Marker, MinerU, and all transitive packages.
2. License and use restrictions for model weights, checkpoints, datasets, and any assets downloaded by those tools at runtime.
3. The effect of each engine's process, plugin, network-service, or bundled-distribution deployment model on a particular use case.
4. Whether a future wheel, installer, container, or public repository includes third-party code, model files, or required notices.
5. Whether current CI scans cover every optional extra, platform, and runtime-installed component.

Names such as MIT, Apache-2.0, GPL, AGPL, and CC-BY-NC in earlier project notes are leads for review, not verified statements about every version or artifact. Do not use them as a commercial-use approval.

## Review required before distribution or commercial deployment

- Resolve and record exact package versions for each supported installation profile, including optional extras and transitive dependencies.
- Retrieve and review the license and notice files for those exact package and model artifacts from their upstream sources.
- Review the intended deployment and distribution model, including subprocess/network use and bundled assets.
- Generate and inspect a complete dependency notice report for each profile; inspect CI scan output rather than treating the presence of a workflow as a passing audit.
- Obtain qualified legal review where a distribution or commercial decision depends on license interpretation.

Until those checks are complete, describe the license status as **partially documented; version-specific and deployment-specific review pending**. Keeping the repository private is a visibility choice, not a substitute for license review.
