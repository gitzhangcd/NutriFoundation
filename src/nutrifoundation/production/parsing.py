from __future__ import annotations

import hashlib
from xml.etree import ElementTree as ET

from .models import Anchor, ParsedDocument, RawSnapshot, digest


PARSER_VERSION = "jats-table-text-v0.1"


def parse_document(snapshot: RawSnapshot, data: bytes) -> ParsedDocument:
    if hashlib.sha256(data).hexdigest() != snapshot.content_sha256:
        raise ValueError("Parser input hash mismatch")
    anchors = []
    def add(locator, text, context=None):
        anchors.append(Anchor(anchor_id="ANC-"+digest([snapshot.snapshot_id, PARSER_VERSION, locator]),
            snapshot_id=snapshot.snapshot_id, source_sha256=snapshot.content_sha256,
            parser_version=PARSER_VERSION, locator=locator, exact_text=text,
            text_sha256=hashlib.sha256(text.encode()).hexdigest(), context=context or {}))
    if snapshot.format == "TEXT":
        text = data.decode("utf-8")
        offset = 0
        for line in text.splitlines(keepends=True):
            add(f"utf8-text:{offset}:{offset+len(line)}", line)
            offset += len(line)
    elif snapshot.format == "JATS_XML":
        root = ET.fromstring(data)
        # Positional paths remain replayable even when publisher IDs are absent.
        def walk(node, path):
            local = node.tag.rsplit("}", 1)[-1]
            if local in {"p", "article-title", "table-wrap-foot", "caption"}:
                add(path, "".join(node.itertext()), {"kind":local, "publisher_id":node.get("id")})
            if local == "table-wrap":
                caption = " ".join("".join(c.itertext()) for c in node.iter() if c.tag.rsplit("}",1)[-1]=="caption")
                foot = " ".join("".join(c.itertext()) for c in node.iter() if c.tag.rsplit("}",1)[-1]=="table-wrap-foot")
                rows = [r for r in node.iter() if r.tag.rsplit("}",1)[-1]=="tr"]
                headers = [["".join(c.itertext()) for c in r if c.tag.rsplit("}",1)[-1] in {"th","td"}] for r in rows if any(c.tag.rsplit("}",1)[-1]=="th" for c in r)]
                for ri,r in enumerate(rows):
                    cells = [c for c in r if c.tag.rsplit("}",1)[-1] in {"td","th"}]
                    row_text = ["".join(c.itertext()) for c in cells]
                    for ci,c in enumerate(cells):
                        add(f"{path}/table-row:{ri}/cell:{ci}", "".join(c.itertext()),
                            {"kind":"table_cell", "table_id":node.get("id"), "row":ri,"cell":ci,
                             "row_cells":row_text, "headers":headers,"caption":caption,"footnotes":foot,
                             "rowspan":c.get("rowspan","1"),"colspan":c.get("colspan","1"),
                             "column_semantics":"not_inferred"})
            for i,child in enumerate(node):
                walk(child, path+f"/{i}")
        walk(root,"root")
    else:
        raise ValueError("Parser not qualified for this format; raw snapshot retained")
    return ParsedDocument(parsed_id="PARSED-"+digest([snapshot.snapshot_id,PARSER_VERSION]),
        snapshot_id=snapshot.snapshot_id, parser_version=PARSER_VERSION, anchors=tuple(anchors))


def replay_anchor(snapshot: RawSnapshot, data: bytes, anchor: Anchor) -> str:
    parsed = parse_document(snapshot, data)
    found = next((a for a in parsed.anchors if a.anchor_id==anchor.anchor_id),None)
    if found is None or found != anchor:
        raise ValueError("Anchor version/content/context mismatch")
    return found.exact_text
