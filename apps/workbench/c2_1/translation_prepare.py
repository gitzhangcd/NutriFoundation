"""Offline synthetic translation-pack preparation. No model or network calls.

The tool reads an explicitly supplied canonical JSON and local translated-unit
mapping, and writes an UNVERIFIED full-unit sidecar. Scientific qualification,
copyright review and external translation service approval are NOT provided.
Do not put restricted sources or translations in a public Git repository.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from translation_contract import SCHEMA, validate

def prepare(doc: dict, translated_by_unit: dict, version: str) -> dict:
    if not isinstance(translated_by_unit, dict): raise ValueError('TRANSLATION_MAP_REQUIRED')
    all_ids = {u['unit_id'] for u in doc['units']}
    if set(translated_by_unit) - all_ids: raise ValueError('UNKNOWN_TRANSLATED_UNIT')
    items=[]
    for unit in doc['units']:
        zh = translated_by_unit.get(unit['unit_id'])
        if zh is None: continue
        source=unit['raw']
        items.append({
            'unit_id':unit['unit_id'],
            'source_unit_raw_sha256':unit['raw_sha256'],
            'source_quote':source,
            'source_start_utf16':0,
            'source_end_utf16':len(source.encode('utf-16-le'))//2,
            'translated_excerpt':zh,
            'alignment_level':'FULL_UNIT',
            'translation_status':'UNVERIFIED_SYNTHETIC',
            'review_receipt_ref':None,
        })
    pack={
        'schema_version':SCHEMA,
        'source_document_id':doc['document_id'],
        'source_revision':doc['revision'],
        'source_markdown_sha256':doc['source_markdown_sha256'],
        'source_pdf_sha256':doc['source_pdf_sha256'],
        'translation_version':version,
        'target_language':'zh-CN',
        'policy':'SYNTHETIC_REVIEW_ONLY',
        'items':items,
    }
    validate(doc,pack)
    return pack

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--document',required=True,help='Private canonical source JSON')
    p.add_argument('--translations',required=True,help='Local JSON mapping unit_id -> translated string')
    p.add_argument('--output',required=True,help='Private destination, never public /static')
    p.add_argument('--version',required=True)
    p.add_argument('--synthetic-only',action='store_true')
    args=p.parse_args()
    if not args.synthetic_only:raise SystemExit('SYNTHETIC_ONLY_REQUIRED')
    doc=json.loads(Path(args.document).read_text(encoding='utf-8'))
    texts=json.loads(Path(args.translations).read_text(encoding='utf-8'))
    pack=prepare(doc,texts,args.version)
    out=Path(args.output)
    if out.exists():raise SystemExit('EXISTING_TRANSLATION_VERSION_REFUSED')
    out.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    out.write_text(json.dumps(pack,ensure_ascii=False,indent=2),encoding='utf-8')
    out.chmod(0o600)
    print('SYNTHETIC_UNVERIFIED_TRANSLATION_PACK_WRITTEN; translation quality NOT certified')

if __name__=='__main__':main()
