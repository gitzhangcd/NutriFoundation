#!/usr/bin/env python3
"""DOC-GOV v1.0 pure-stdlib documentation authority and navigation check.

Checks *local* references, snapshot shapes and byte-exact in-branch Git blob pins.
It cannot approve science, copyright, cloud release, or expert qualification.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
GOV = ROOT / "docs/governance"
REGISTRY = GOV / "DOC-GOV_v1.0_Canonical_Authority_Registry.json"
INVENTORY = GOV / "DOC-GOV_v1.0_Cross_Branch_Inventory.json"
LINK_DOCS = [
    "README.md", "docs/README.md", "docs/CURRENT_BASELINE.md",
    "docs/RESEARCH_WORKFLOW.md", "docs/workbench/README.md",
    "docs/archive/INDEX.md",
    "docs/governance/DOC-GOV_v1.0_Documentation_Convergence_Master.md",
]
CHECKED_OUT = ROOT.resolve()
errors = []

def fail(msg):
    errors.append(msg)

def repo_file(path):
    p = (ROOT / path).resolve()
    if not p.is_relative_to(CHECKED_OUT):
        fail(f"path escapes repository: {path}")
        return None
    if not p.is_file():
        fail(f"missing local file: {path}")
        return None
    return p

def git_blob_sha(content):
    return hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()

def is_sha(v, n):
    return isinstance(v, str) and re.fullmatch(r"[0-9a-f]{" + str(n) + r"}", v) is not None

def check_registry():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema_id") != "nutrifoundation.doc_gov.canonical_authority_registry/1.0":
        fail("unexpected registry schema")
    ids = set()
    for r in data.get("entries", []):
        id_ = r.get("document_id")
        if not id_ or id_ in ids:
            fail(f"invalid/duplicate registry document_id: {id_}")
        ids.add(id_)
        for k in ("authority_domain", "layer", "kind", "status", "release_gate", "note"):
            if not r.get(k):
                fail(f"{id_} missing {k}")
        loc = r.get("locator", {})
        if loc.get("type") == "repository_file":
            if loc.get("available_in_doc_gov_base") is not True:
                fail(f"{id_} marked present but not available in base")
            path = loc.get("path", "")
            p = repo_file(path)
            if p and git_blob_sha(p.read_bytes()) != loc.get("git_blob_sha"):
                fail(f"{id_} in-branch blob pin differs: {path}")
        elif loc.get("type") == "pr_head_file":
            if loc.get("available_in_doc_gov_base") is not False:
                fail(f"{id_} remote PR file wrongly claims present")
            if not is_sha(loc.get("ref_sha"), 40) or not is_sha(loc.get("git_blob_sha"), 40):
                fail(f"{id_} invalid PR SHA")
            if loc.get("ref_sha") not in loc.get("permalink", ""):
                fail(f"{id_} remote link is mutable/missing SHA")
        elif loc.get("type") == "user_provided_attachment_verified_in_session":
            if not is_sha(loc.get("raw_sha256"), 64) or not isinstance(loc.get("raw_bytes"), int):
                fail(f"{id_} invalid raw-byte attestation metadata")
            if loc.get("archived_to_approved_authoritative_store") is not False:
                fail(f"{id_} attachment unexpectedly claims approved canonical archive")
        elif loc.get("type") != "missing_authoritative_file":
            fail(f"{id_} unknown locator type: {loc.get('type')}")
    if len(ids) < 15:
        fail("authority registry unexpectedly small")
    return len(ids)

def check_inventory():
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if data.get("schema_id") != "nutrifoundation.doc_gov.cross_branch_inventory/1.0":
        fail("unexpected inventory schema")
    paths = set()
    for e in data.get("entries", []):
        p = e.get("path")
        if not p or p in paths:
            fail(f"duplicate inventory path: {p}")
        paths.add(p)
        for field in ("gov_blob_sha", "wb_blob_sha"):
            v = e.get(field)
            if v is not None and not is_sha(v, 40):
                fail(f"invalid inventory git blob: {p} {field}")
        exp = "SAME_BYTES" if e.get("gov_blob_sha") and e.get("gov_blob_sha") == e.get("wb_blob_sha") else (
            "DIFFERENT_BYTES" if e.get("gov_blob_sha") and e.get("wb_blob_sha") else (
                "GOV_ONLY" if e.get("gov_blob_sha") else "WB_ONLY"
            )
        )
        if e.get("comparison") != exp:
            fail(f"snapshot discrepancy: {p}")
    if len(paths) != data.get("document_count"):
        fail("inventory count mismatch")
    expected = {"GOV_PR46", "WB_PR48"}
    if {x.get("name") for x in data.get("sources", [])} != expected:
        fail("inventory source set mismatch")
    return len(paths)

def check_links():
    count = 0
    for rel in LINK_DOCS:
        p = repo_file(rel)
        if not p:
            continue
        text = p.read_text(encoding="utf-8")
        # Markdown inline links. Not trying to parse every Markdown extension.
        for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)\n]+)\)", text):
            target = target.strip().split(" ")[0]
            if target.startswith(("https://", "http://", "mailto:", "#")):
                if target.startswith("https://github.com/") and "/blob/" in target:
                    ref = target.split("/blob/", 1)[1].split("/", 1)[0]
                    if not is_sha(ref, 40):
                        fail(f"mutable GitHub blob link: {rel} -> {target}")
                continue
            name = unquote(target.split("#", 1)[0])
            if name and not (p.parent / name).exists():
                fail(f"broken relative link: {rel} -> {target}")
            count += 1
    return count

def main():
    for p in [REGISTRY, INVENTORY]:
        if not p.is_file():
            fail(f"missing machine manifest {p}")
    if errors:
        print("\n".join("FAIL " + x for x in errors))
        return 1
    n = check_registry()
    f = check_inventory()
    l = check_links()
    if errors:
        print("\n".join("FAIL " + x for x in errors))
        return 1
    print(f"PASS DOC-GOV-v1.0: {n} authority entries, {f} audited paths, {l} internal links checked.")
    print("Scope: documentation technical check ONLY; no science/right/Gold/deployment approval.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
