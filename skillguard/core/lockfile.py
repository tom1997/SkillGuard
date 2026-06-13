from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skillguard import __version__
from skillguard.core.models import Capability, ScanResult
from skillguard.core.scanner import Scanner

LOCKFILE_NAME = "skillguard.lock"
LOCKFILE_VERSION = 1


@dataclass(frozen=True)
class CapabilityChange:
    kind: str
    access: str
    resource: str
    evidence: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "access": self.access,
            "resource": self.resource,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class VerificationResult:
    target: Path
    lockfile: Path
    added: list[CapabilityChange]
    removed: list[CapabilityChange]
    previous_score: int
    current_score: int
    previous_label: str
    current_label: str
    current_scan: ScanResult

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed or self.previous_score != self.current_score)

    @property
    def has_added_capabilities(self) -> bool:
        return bool(self.added)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": str(self.target),
            "lockfile": str(self.lockfile),
            "changed": self.changed,
            "added_capabilities": [item.to_dict() for item in self.added],
            "removed_capabilities": [item.to_dict() for item in self.removed],
            "previous": {
                "score": self.previous_score,
                "label": self.previous_label.lower(),
            },
            "current": {
                "score": self.current_score,
                "label": self.current_label.lower(),
            },
            "current_scan": self.current_scan.to_dict(),
        }


def default_lockfile_path(target: Path) -> Path:
    return target / LOCKFILE_NAME if target.is_dir() else target.parent / LOCKFILE_NAME


def create_lock(target: Path, lockfile: Path | None = None) -> dict[str, Any]:
    scan = Scanner().scan(target)
    payload = _lock_payload(target, scan)
    path = lockfile or default_lockfile_path(target)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_lock(target: Path, lockfile: Path | None = None) -> VerificationResult:
    path = lockfile or default_lockfile_path(target)
    if not path.exists():
        raise FileNotFoundError(f"Lockfile does not exist: {path}")

    previous = json.loads(path.read_text(encoding="utf-8"))
    current_scan = Scanner().scan(target)
    previous_capabilities = _capability_map(previous.get("capabilities", []))
    current_capabilities = _capability_map(_capabilities_payload(current_scan.capabilities))

    added_keys = sorted(set(current_capabilities) - set(previous_capabilities))
    removed_keys = sorted(set(previous_capabilities) - set(current_capabilities))

    return VerificationResult(
        target=target,
        lockfile=path,
        added=[_change_from_payload(current_capabilities[key]) for key in added_keys],
        removed=[_change_from_payload(previous_capabilities[key]) for key in removed_keys],
        previous_score=int(previous.get("risk", {}).get("score", 0)),
        current_score=current_scan.score,
        previous_label=str(previous.get("risk", {}).get("label", "info")),
        current_label=current_scan.risk_label,
        current_scan=current_scan,
    )


def _lock_payload(target: Path, scan: ScanResult) -> dict[str, Any]:
    return {
        "lockfile_version": LOCKFILE_VERSION,
        "skillguard_version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target": str(target),
        "content_hash": _content_hash(target),
        "risk": {
            "score": scan.score,
            "label": scan.risk_label.lower(),
            "max_severity": scan.max_severity.value,
            "finding_counts": scan.finding_counts(),
        },
        "capabilities": _capabilities_payload(scan.capabilities),
        "required_capabilities": scan.capabilities_summary(),
    }


def _capabilities_payload(capabilities: list[Capability]) -> list[dict[str, Any]]:
    return [
        {
            "kind": capability.kind,
            "access": capability.access,
            "resource": capability.resource,
            "evidence": [evidence.to_dict() for evidence in capability.evidence],
        }
        for capability in sorted(capabilities, key=lambda item: item.key())
    ]


def _capability_map(capabilities: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    mapped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for capability in capabilities:
        key = (
            str(capability.get("kind", "")),
            str(capability.get("access", "")),
            str(capability.get("resource", "")),
        )
        mapped[key] = capability
    return mapped


def _change_from_payload(payload: dict[str, Any]) -> CapabilityChange:
    return CapabilityChange(
        kind=str(payload.get("kind", "")),
        access=str(payload.get("access", "")),
        resource=str(payload.get("resource", "")),
        evidence=list(payload.get("evidence", [])),
    )


def _content_hash(target: Path) -> str:
    root = target.resolve()
    files = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
    digest = hashlib.sha256()
    for path in sorted(files):
        if path.name == LOCKFILE_NAME or _is_ignored(path):
            continue
        relative = path.relative_to(root.parent if root.is_file() else root)
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _is_ignored(path: Path) -> bool:
    ignored = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
    return any(part in ignored for part in path.parts)
