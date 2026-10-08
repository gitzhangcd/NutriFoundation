"""WB-P0.2-A real-paper source package importer and read-only canonical reader.

Engineering-only: import/parse success never qualifies scientific evidence or Gold.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import os
import re
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import fitz
from pdf_locator import LocatorError, locate_pdf_quote
from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from markdown_it import MarkdownIt
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
DOC_ROOT = BASE / "data"
PROFILE = "AnnotationSourcePackage/0.1"
CANON = "CanonicalDocument-TextProfile/0.1"
SUPPORTED = {"document.md", "source/original.pdf", "conversion_manifest.json"}
MAX_ZIP_SIZE = 30 * 1024 * 1024
MAX_UNPACKED = 80 * 1024 * 1024
MAX_MEMBERS = 80
PAGE_RE = re.compile(r"<!--\s*pdf-page:\s*(\d+)\s*-->")
PAGE_RANGE_RE = re.compile(r"<!--\s*pdf-pages:\s*(\d+)-(\d+)\s*-->")
MD = MarkdownIt("commonmark", {"html": False}).enable("table")


def sha(data: bytes | str) -> str:
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def u16len(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def substring_u16(s: str, start: int, end: int) -> str:
    if start < 0 or end <= start:
        raise ValueError("INVALID_UTF16_RANGE")
    payload = s.encode("utf-16-le")
    try:
        return payload[start * 2 : end * 2].decode("utf-16-le", errors="strict")
    except UnicodeDecodeError as ex:
        raise ValueError("SPLIT_UNICODE_SURROGATE") from ex


def safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name and "\\" not in name and not name.startswith("/") and
                not any(x in ("..", ".") for x in p.parts) and
                (name in SUPPORTED or (name.startswith("assets/") and
                 name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))))


def build_source_package(legacy: Path, pdf: Path, dest: Path) -> dict[str, Any]:
    """Upgrade previous Markdown + figure ZIP; deliberately do not modify source claims."""
    pdf_bytes = pdf.read_bytes()
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("ORIGINAL_NOT_PDF")
    with fitz.open(stream=pdf_bytes, filetype="pdf") as d:
        pages = len(d)
        figure_source_page = next((i + 1 for i, page in enumerate(d) if "Fig 1. Consort diagram." in page.get_text()), None)
    with zipfile.ZipFile(legacy) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        markdowns = [n for n in names if n.endswith(".annotation_source.md")]
        if len(markdowns) != 1:
            raise ValueError("EXPECTED_ONE_LEGACY_MARKDOWN")
        md_bytes = z.read(markdowns[0])
        assets = {"assets/" + n.split("/assets/", 1)[1]: z.read(n)
                  for n in names if "/assets/" in n and n.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))}
    manifest = {
        "package_type": "AnnotationSourcePackage", "schema_version": "0.1",
        "source": {"path": "source/original.pdf", "sha256": sha(pdf_bytes), "pages": pages, "bytes": len(pdf_bytes)},
        "reading_document": {"path": "document.md", "sha256": sha(md_bytes), "profile": "annotation_source_markdown_v1"},
        "assets": [{"path": p, "sha256": sha(blob), "bytes": len(blob),
                     "source_page": figure_source_page if "fig1_" in p else None} for p, blob in sorted(assets.items())],
        "conversion": {"status": "STRUCTURED_NOT_SCIENTIFICALLY_VERIFIED", "description": "Repackaged previously converted Markdown; no new scientific assertions"},
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("conversion_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("document.md", md_bytes)
        z.writestr("source/original.pdf", pdf_bytes)
        for path, blob in assets.items():
            z.writestr(path, blob)
    return manifest


def read_package(payload: bytes) -> dict[str, Any]:
    if len(payload) > MAX_ZIP_SIZE or not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("ZIP_SIZE_OR_FORMAT_INVALID")
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        if len(infos) > MAX_MEMBERS or sum(i.file_size for i in infos) > MAX_UNPACKED:
            raise ValueError("ZIP_LIMIT_EXCEEDED")
        if len({i.filename for i in infos}) != len(infos):
            raise ValueError("DUPLICATE_MEMBERS")
        if any(not safe_member(i.filename) for i in infos):
            raise ValueError("ZIP_INVALID_PATH_OR_CONTENT")
        if not SUPPORTED.issubset({i.filename for i in infos}):
            raise ValueError("MISSING_PDF_OR_MARKDOWN_OR_MANIFEST")
        files = {i.filename: z.read(i.filename) for i in infos}
    mf = json.loads(files["conversion_manifest.json"].decode("utf-8"))
    if mf.get("package_type") != "AnnotationSourcePackage" or mf.get("schema_version") != "0.1":
        raise ValueError("PACKAGE_PROFILE_MISMATCH")
    if files["document.md"].startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF8_BOM_UNSUPPORTED")
    document = files["document.md"].decode("utf-8")
    pdf = files["source/original.pdf"]
    if not pdf.startswith(b"%PDF-"):
        raise ValueError("ORIGINAL_NOT_PDF")
    with fitz.open(stream=pdf, filetype="pdf") as obj:
        pages = len(obj)
    if mf["source"].get("path") != "source/original.pdf" or mf["source"].get("sha256") != sha(pdf) or mf["source"].get("pages") != pages:
        raise ValueError("PDF_MANIFEST_MISMATCH")
    if mf["reading_document"].get("path") != "document.md" or mf["reading_document"].get("sha256") != sha(files["document.md"]):
        raise ValueError("MARKDOWN_MANIFEST_MISMATCH")
    expected = {a["path"]: a["sha256"] for a in mf.get("assets", [])}
    present = {p: sha(b) for p, b in files.items() if p.startswith("assets/")}
    if expected != present:
        raise ValueError("ASSET_MANIFEST_MISMATCH")
    return {"manifest": mf, "markdown": document, "files": files, "pdf_pages": pages}


def canonicalize(md_src: str, manifest: dict[str, Any]) -> dict[str, Any]:
    src_sha = manifest["reading_document"]["sha256"]
    pdf_sha = manifest["source"]["sha256"]
    rev = "r1-" + src_sha[:16]
    doc_id = "DOC-" + pdf_sha[:20]
    lines = md_src.splitlines(keepends=True)
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + u16len(line))
    page_markers = [(i, int(m.group(1))) for i, line in enumerate(lines)
                    if (m := PAGE_RE.search(line))]
    page_ranges = [(i, int(m.group(1)), int(m.group(2))) for i, line in enumerate(lines)
                   if (m := PAGE_RANGE_RE.search(line))]
    for _, a_page, b_page in page_ranges:
        if not (1 <= a_page <= b_page <= manifest["source"]["pages"]):
            raise ValueError("INVALID_PDF_PAGE_RANGE")
    for _, page in page_markers:
        if not (1 <= page <= manifest["source"]["pages"]):
            raise ValueError("INVALID_PDF_PAGE_HINT")
    # Frontmatter is metadata, not an annotatable claim. Preserve byte identity in document hash.
    stripped = list(lines)
    if stripped and stripped[0].strip() == "---":
        for i in range(1, min(80, len(stripped))):
            if stripped[i].strip() == "---":
                for j in range(i + 1):
                    stripped[j] = "\n" if stripped[j].endswith("\n") else ""
                break
    tokens = MD.parse("".join(stripped))
    content_types = {"heading_open": "SECTION", "paragraph_open": "PARAGRAPH", "table_open": "TABLE", "bullet_list_open": "LIST", "ordered_list_open": "LIST", "fence": "CODE", "blockquote_open": "BLOCKQUOTE"}
    units: list[dict[str, Any]] = []
    heading_stack: list[tuple[int, str]] = []
    seen: set[tuple[int, int]] = set()
    for tok in tokens:
        if tok.level != 0 or tok.map is None or tok.type not in content_types:
            continue
        a, b = tok.map
        if (a, b) in seen:
            continue
        seen.add((a, b))
        raw = "".join(lines[a:b]).strip("\n")
        if not raw or PAGE_RE.fullmatch(raw.strip()):
            continue
        typ = content_types[tok.type]
        if typ == "PARAGRAPH" and re.search(r"!\[[^\]]*\]\(assets/", raw):
            typ = "FIGURE"
        elif typ == "PARAGRAPH" and re.match(r"^(?:Fig(?:ure)?\.?\s*\d+|Table\s*\d+)\s*[.:]", raw, re.I):
            typ = "CAPTION"
        current = [p for li, p in page_markers if li <= a]
        page = current[-1] if current else None
        # A range marker indicates uncertain provenance, not an exact page.
        in_range = next(((x, y) for line_idx, x, y in reversed(page_ranges)
                         if line_idx <= a and not any(other > line_idx and other <= a for other, _ in page_markers)), None)
        if in_range:
            page = None
        if typ == "FIGURE":
            match_asset = re.search(r"\((assets/[^)]+)\)", raw)
            if match_asset:
                found_asset = next((e for e in manifest.get("assets", []) if e["path"] == match_asset.group(1)), None)
                if found_asset and found_asset.get("source_page"):
                    page = found_asset["source_page"]
        unit_id = f"U-{len(units) + 1:04d}"
        parent = heading_stack[-1][1] if heading_stack else None
        label = ""
        if typ == "SECTION":
            level = int(tok.tag[1])
            heading_stack = [(l, pid) for l, pid in heading_stack if l < level]
            parent = heading_stack[-1][1] if heading_stack else None
            heading_stack.append((level, unit_id))
            label = raw.lstrip("# ").strip()
        # Render only known local source HTML, with html disabled to avoid source-script execution.
        unit = {
            "unit_id": unit_id, "type": typ, "parent_unit_id": parent,
            "heading": label, "pdf_page_hint": page, "pdf_page_range": list(in_range) if in_range else None,
            "source_line_start": a + 1, "source_line_end": b,
            "source_start_utf16": line_offsets[a], "source_end_utf16": line_offsets[b],
            "raw": raw, "raw_sha256": sha(raw), "html": MD.render(raw),
        }
        units.append(unit)
    if not units:
        raise ValueError("EMPTY_CANONICAL_DOCUMENT")
    return {
        "schema_version": CANON, "document_id": doc_id, "revision": rev,
        "source_pdf_sha256": pdf_sha, "source_markdown_sha256": src_sha,
        "source_pages": manifest["source"]["pages"],
        "source_status": "STRUCTURED_NOT_SCIENTIFICALLY_VERIFIED",
        "title": next((u["heading"] for u in units if u["type"] == "SECTION" and u["raw"].startswith("# ")), "Imported research article"),
        "units": units, "unit_count": len(units),
        "parse_run": {"parser": "markdown-it-py", "adapter": "WB-P0.2-A/0.1", "origin": "ANALYSIS_OF_EXISTING_MARKDOWN", "warnings": ["PDF bbox is a separately verified, append-only locator sidecar; page hints alone are not exact coordinates", "Markdown scientific values have not been revalidated"]},
    }


class AnchorRequest(BaseModel):
    unit_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    start_utf16: int = Field(ge=0)
    end_utf16: int = Field(gt=0)
    expected_revision: str
    expected_source_markdown_sha256: str


class LocatorResolveRequest(BaseModel):
    expected_revision: str
    expected_source_pdf_sha256: str


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = root / "anchors.db"
        with sqlite3.connect(self.db) as con:
            con.execute("CREATE TABLE IF NOT EXISTS anchors (anchor_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, unit_id TEXT NOT NULL, payload TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS pdf_locators (anchor_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, locator_payload TEXT NOT NULL, pdf_sha256 TEXT NOT NULL, canonical_revision TEXT NOT NULL, FOREIGN KEY(anchor_id) REFERENCES anchors(anchor_id))")

    def import_bytes(self, payload: bytes) -> dict:
        result = read_package(payload)
        canonical = canonicalize(result["markdown"], result["manifest"])
        ident = canonical["document_id"]
        workdir = self.root / ident
        if workdir.exists():
            recorded = json.loads((workdir / "canonical.json").read_text())
            if recorded["source_markdown_sha256"] != canonical["source_markdown_sha256"]:
                raise ValueError("SOURCE_DOCUMENT_REVISION_CHANGED_USE_NEW_PACKAGE")
            return recorded
        # Atomic local import; content-addressed documents cannot mutate in place.
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            stage = Path(tmp) / ident
            stage.mkdir()
            for name, blob in result["files"].items():
                dst = stage / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(blob)
            (stage / "canonical.json").write_text(json.dumps(canonical, ensure_ascii=False, indent=2))
            stage.rename(workdir)
        return canonical

    def document(self) -> dict | None:
        for path in sorted(self.root.glob("DOC-*/canonical.json")):
            return json.loads(path.read_text())
        return None

    def path(self, name: str) -> Path:
        doc = self.document()
        if doc is None:
            raise HTTPException(404, "NO_IMPORTED_DOCUMENT")
        return self.root / doc["document_id"] / name

    def anchors(self) -> list[dict]:
        doc = self.document()
        if doc is None:
            return []
        with sqlite3.connect(self.db) as con:
            rows = con.execute("SELECT payload FROM anchors WHERE document_id=? ORDER BY rowid", (doc["document_id"],)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def create_anchor(self, req: AnchorRequest) -> dict:
        doc = self.document()
        if doc is None:
            raise ValueError("NO_IMPORTED_DOCUMENT")
        if req.expected_revision != doc["revision"] or req.expected_source_markdown_sha256 != doc["source_markdown_sha256"]:
            raise ValueError("STALE_REVISION_OR_SOURCE_HASH")
        unit = next((u for u in doc["units"] if u["unit_id"] == req.unit_id), None)
        if unit is None:
            raise ValueError("UNKNOWN_UNIT_ID")
        if req.end_utf16 > u16len(unit["raw"]) or substring_u16(unit["raw"], req.start_utf16, req.end_utf16) != req.quote:
            raise ValueError("QUOTE_RANGE_MISMATCH")
        payload = {
            "anchor_id": "SA-" + sha(f"{doc['revision']}:{unit['unit_id']}:{req.start_utf16}:{req.end_utf16}:{req.quote}")[:20],
            "document_id": doc["document_id"], "source_pdf_sha256": doc["source_pdf_sha256"],
            "source_markdown_sha256": doc["source_markdown_sha256"], "canonical_revision": doc["revision"],
            "unit_id": unit["unit_id"], "unit_raw_sha256": unit["raw_sha256"],
            "start_utf16": req.start_utf16, "end_utf16": req.end_utf16,
            "quote": req.quote, "quote_sha256": sha(req.quote),
            "pdf_page_hint": unit["pdf_page_hint"], "pdf_location_kind": "PAGE_HINT_ONLY_NOT_EXACT_BBOX",
            "created_at": utc(),
        }
        with sqlite3.connect(self.db) as con:
            con.execute("INSERT OR IGNORE INTO anchors (anchor_id,document_id,unit_id,payload) VALUES (?,?,?,?)",
                        (payload["anchor_id"], doc["document_id"], unit["unit_id"], json.dumps(payload, ensure_ascii=False)))
            stored = con.execute("SELECT payload FROM anchors WHERE anchor_id=?", (payload["anchor_id"],)).fetchone()
        return json.loads(stored[0])


    def verified_pdf_path(self) -> Path:
        doc = self.document()
        if doc is None:
            raise ValueError("NO_IMPORTED_DOCUMENT")
        p = self.path("source/original.pdf")
        if sha(p.read_bytes()) != doc["source_pdf_sha256"]:
            raise LocatorError("SOURCE_PDF_SHA_MISMATCH")
        return p

    def get_anchor(self, anchor_id: str) -> dict:
        doc = self.document()
        if doc is None:
            raise ValueError("NO_IMPORTED_DOCUMENT")
        with sqlite3.connect(self.db) as con:
            row = con.execute("SELECT payload FROM anchors WHERE anchor_id=? AND document_id=?", (anchor_id, doc["document_id"])).fetchone()
        if row is None:
            raise ValueError("UNKNOWN_ANCHOR_ID")
        return json.loads(row[0])

    def get_locator(self, anchor_id: str) -> dict | None:
        doc = self.document()
        if doc is None:
            return None
        with sqlite3.connect(self.db) as con:
            row = con.execute("SELECT locator_payload FROM pdf_locators WHERE anchor_id=? AND document_id=?", (anchor_id, doc["document_id"])).fetchone()
        if row:
            self.verified_pdf_path()  # never serve a stale verified locator after source tampering
        return json.loads(row[0]) if row else None

    def resolve_pdf_locator(self, anchor_id: str, req: LocatorResolveRequest) -> dict:
        """Append-only BBox sidecar. Never replace the original SourceAnchor payload."""
        anchor = self.get_anchor(anchor_id)
        doc = self.document()
        if req.expected_revision != doc["revision"] or req.expected_source_pdf_sha256 != doc["source_pdf_sha256"]:
            raise LocatorError("STALE_REVISION_OR_PDF_HASH")
        if anchor["canonical_revision"] != doc["revision"] or anchor["source_pdf_sha256"] != doc["source_pdf_sha256"]:
            raise LocatorError("ANCHOR_SOURCE_IDENTITY_MISMATCH")
        existing = self.get_locator(anchor_id)
        if existing:
            if existing["source_pdf_sha256"] != doc["source_pdf_sha256"] or existing["canonical_revision"] != doc["revision"]:
                raise LocatorError("STORED_LOCATOR_REVISION_MISMATCH")
            return existing
        match = locate_pdf_quote(self.verified_pdf_path(), anchor["quote"],
                                 doc["source_pdf_sha256"], anchor.get("pdf_page_hint"))
        result = {
            "anchor_id": anchor_id, "document_id": doc["document_id"],
            "source_pdf_sha256": doc["source_pdf_sha256"],
            "canonical_revision": doc["revision"],
            "unit_id": anchor["unit_id"], "quote_sha256": anchor["quote_sha256"],
            "pdf_locator": match,
        }
        result["locator_sha256"] = sha(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
        with sqlite3.connect(self.db) as con:
            con.execute("INSERT OR IGNORE INTO pdf_locators (anchor_id, document_id, locator_payload, pdf_sha256, canonical_revision) VALUES (?,?,?,?,?)",
                        (anchor_id, doc["document_id"], json.dumps(result, ensure_ascii=False), doc["source_pdf_sha256"], doc["revision"]))
        recorded = self.get_locator(anchor_id)
        if recorded["locator_sha256"] != result["locator_sha256"]:
            raise LocatorError("LOCATOR_APPEND_ONLY_CONFLICT")
        return recorded


def make_app(root: Path = DOC_ROOT) -> FastAPI:
    store = Store(root)
    app = FastAPI(title="Workbench WB-P0.2-B")

    @app.get("/api/health")
    def health():
        return {"status": "OK", "phase": "WB-P0.2-B", "scientific_status": "NOT_SCIENTIFICALLY_VERIFIED"}

    @app.get("/api/document")
    def document():
        return store.document() or {"status": "NO_IMPORTED_DOCUMENT"}

    @app.get("/api/anchors")
    def anchors():
        return store.anchors()

    @app.post("/api/import")
    async def import_package(file: UploadFile = File(...)):
        try:
            raw = await file.read(MAX_ZIP_SIZE + 1)
            doc = store.import_bytes(raw)
            return {"document_id": doc["document_id"], "units": doc["unit_count"], "revision": doc["revision"], "status": "IMPORTED_NOT_SCIENTIFICALLY_VERIFIED"}
        except (ValueError, UnicodeError, json.JSONDecodeError, KeyError, zipfile.BadZipFile, fitz.FileDataError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/anchors", status_code=201)
    def create_anchor(req: AnchorRequest):
        try:
            return store.create_anchor(req)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/locators/{anchor_id}")
    def get_locator(anchor_id: str):
        try:
            row = store.get_locator(anchor_id)
        except LocatorError as exc:
            raise HTTPException(409, str(exc)) from exc
        if row is None:
            raise HTTPException(404, "NO_VERIFIED_PDF_LOCATOR")
        return row

    @app.post("/api/locators/{anchor_id}/resolve", status_code=200)
    def resolve_locator(anchor_id: str, req: LocatorResolveRequest):
        try:
            return store.resolve_pdf_locator(anchor_id, req)
        except (LocatorError, ValueError) as exc:
            # No best-guess bbox is served on missing/ambiguous evidence.
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/pdf/page/{page_num}/png")
    def render_pdf_page(page_num: int, scale: float = Query(1.35, ge=0.5, le=2.5)):
        try:
            pdf_path = store.verified_pdf_path()
        except LocatorError as exc:
            raise HTTPException(409, str(exc)) from exc
        with fitz.open(pdf_path) as pdf:
            if not 1 <= page_num <= len(pdf):
                raise HTTPException(404, "PAGE_OUT_OF_RANGE")
            page = pdf[page_num-1]
            if page.rotation != 0:
                raise HTTPException(422, "PDF_ROTATION_REQUIRES_TRANSFORM_NOT_SUPPORTED")
            raster = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            png = raster.tobytes("png")
        return Response(content=png, media_type="image/png", headers={"Cache-Control": "private, max-age=0", "X-Content-Type-Options": "nosniff"})

    @app.get("/api/original.pdf")
    def original():
        try:
            p = store.verified_pdf_path()
        except LocatorError as exc:
            raise HTTPException(409, str(exc)) from exc
        return FileResponse(p, media_type="application/pdf", headers={"Cache-Control": "private, max-age=0", "X-Content-Type-Options": "nosniff"})

    @app.get("/assets/{name:path}")
    def asset(name: str):
        if not safe_member("assets/" + name):
            raise HTTPException(404, "INVALID_ASSET_PATH")
        p = store.path("assets/" + name)
        if not p.exists():
            raise HTTPException(404, "ASSET_NOT_FOUND")
        return FileResponse(p, headers={"X-Content-Type-Options": "nosniff"})

    app.mount("/static", StaticFiles(directory=BASE / "web"), name="static")

    @app.get("/")
    def index():
        return FileResponse(BASE / "web" / "index.html")
    return app


app = make_app()


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("package")
    p.add_argument("--legacy", type=Path, required=True)
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("serve")
    s.add_argument("--root", type=Path, default=DOC_ROOT)
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8777)
    args = parser.parse_args()
    if args.cmd == "package":
        manifest = build_source_package(args.legacy, args.pdf, args.out)
        print(json.dumps({"path": str(args.out), "pdf_pages": manifest["source"]["pages"], "assets": len(manifest["assets"]), "pdf_sha256": manifest["source"]["sha256"]}, indent=2))
    else:
        import uvicorn
        uvicorn.run(make_app(args.root), host=args.host, port=args.port)


if __name__ == "__main__":
    main()