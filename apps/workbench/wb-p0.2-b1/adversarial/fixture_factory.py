"""Deterministic generated adversarial layouts; no invented scientific observations.

Fixtures intentionally contain synthetic text that is clearly not biomedical evidence.
All generation is reproducible from source and uses a fixed PDF metadata date.
"""
from __future__ import annotations
import hashlib
import io
import json
import zipfile
from pathlib import Path
import fitz

EXACT = "Verified geometry should locate this unique adversarial synthetic quote"
REPEATED = "A duplicated synthetic phrase must never become an exact source coordinate"
LEFT = "The unrelated left column ends with these words"
RIGHT = "The adjacent right column starts with other words"
CELL_A = "The first independent table cell contains text"
CELL_B = "The distant second table cell also contains text"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def make_pdf(kind: str) -> bytes:
    doc = fitz.open()
    if kind == "scanned":
        page = doc.new_page(width=600, height=800)
        # Pixel image of words, no OCR/text layer. Do not pretend recognition.
        tmp=fitz.open(); p=tmp.new_page(width=600,height=800)
        p.insert_text((70,140),EXACT,fontsize=11)
        pix=p.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
        page.insert_image(page.rect,stream=pix.tobytes("png"));tmp.close()
    elif kind == "two_columns_cross_block":
        page=doc.new_page(width=600,height=800)
        page.insert_text((44,140),LEFT,fontsize=10)
        page.insert_text((330,140),RIGHT,fontsize=10)
    elif kind == "table_cell_stitch":
        page=doc.new_page(width=700,height=800)
        page.insert_text((40,150),CELL_A,fontsize=9)
        page.insert_text((400,150),CELL_B,fontsize=9)
    elif kind == "two_columns_valid":
        page=doc.new_page(width=600,height=800)
        page.insert_textbox(fitz.Rect(45,90,290,730),EXACT,fontsize=12)
        page.insert_textbox(fitz.Rect(310,90,550,730),"Additional unrelated text in another column, not evidence",fontsize=11)
    elif kind == "repeated_same_page":
        page=doc.new_page(width=600,height=800)
        page.insert_text((50,120),REPEATED,fontsize=9)
        page.insert_text((50,200),REPEATED,fontsize=9)
    elif kind == "repeated_two_pages":
        page=doc.new_page(width=650,height=850);page.insert_text((45,130),REPEATED,fontsize=9)
        page=doc.new_page(width=650,height=850);page.insert_text((45,130),REPEATED,fontsize=9)
    elif kind == "multi_line":
        page=doc.new_page(width=600,height=800)
        page.insert_textbox(fitz.Rect(100,90,380,600),EXACT,fontsize=12)
    elif kind in {"rotate_0","rotate_90","rotate_180","rotate_270","crop", "crop_rotate_90"}:
        page=doc.new_page(width=600,height=800)
        page.insert_text((100,130),EXACT,fontsize=9)
        if kind.startswith("crop"):
            page.set_cropbox(fitz.Rect(40,50,480,650))
        if kind.startswith("rotate_"):
            page.set_rotation(int(kind.split("_")[1]))
        elif kind == "crop_rotate_90":
            page.set_rotation(90)
    else:
        raise ValueError(kind)
    doc.set_metadata({"title":f"SYNTHETIC_ADVERSARIAL_{kind}","creationDate":"D:20260101000000Z","modDate":"D:20260101000000Z"})
    output=doc.tobytes(garbage=4,deflate=True);doc.close()
    return output


def package(pdf_bytes: bytes, markdown_quote: str, page_hint: int = 1) -> bytes:
    with fitz.open(stream=pdf_bytes,filetype="pdf") as pdf:
        pages=len(pdf)
    md=f"# Synthetic adversarial fixture\n\n<!-- pdf-page: {page_hint} -->\n\n{markdown_quote}\n".encode("utf-8")
    manifest={"package_type":"AnnotationSourcePackage","schema_version":"0.1","source":{"path":"source/original.pdf","sha256":sha(pdf_bytes),"pages":pages,"bytes":len(pdf_bytes)},"reading_document":{"path":"document.md","sha256":sha(md),"profile":"annotation_source_markdown_v1"},"assets":[],"conversion":{"status":"SYNTHETIC_TECHNICAL_FIXTURE_NOT_SCIENTIFIC_EVIDENCE"}}
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("source/original.pdf",pdf_bytes)
        z.writestr("document.md",md)
        z.writestr("conversion_manifest.json",json.dumps(manifest,sort_keys=True))
    return output.getvalue()


def build_browser_fixture(dest: Path) -> dict:
    raw=make_pdf("crop_rotate_90")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(package(raw,EXACT))
    return {"fixture_type":"SYNTHETIC_TECHNICAL_LAYOUT_NOT_SCIENTIFIC_EVIDENCE","profile":"crop_rotate_90","pdf_sha256":sha(raw),"zip_sha256":sha(dest.read_bytes())}


if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    path=root/"fixtures"/"b1_synthetic_crop_rotate_90.AnnotationSourcePackage.v0.1.zip"
    print(json.dumps(build_browser_fixture(path),indent=2))