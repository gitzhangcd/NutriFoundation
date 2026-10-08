"""WB-P0.2-B1: adversarial negatives and visible crop/rotation acceptance.

Strict: a real text-layer quote uniquely bound to the immutable PDF may be located;
geometry-incoherent, ambiguous, scanned, and corrupted inputs must fail closed.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import sys
import fitz
import pytest
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'adversarial'))
from fixture_factory import make_pdf, package, sha, EXACT, REPEATED, LEFT, RIGHT, CELL_A, CELL_B
from pdf_locator import locate_pdf_quote, LocatorError
from wb_a import make_app


def locate(tmp_path,kind,quote=EXACT,hint=1):
    pdf=tmp_path/f'{kind}.pdf';pdf.write_bytes(make_pdf(kind))
    return locate_pdf_quote(pdf,quote,sha(pdf.read_bytes()),hint)


@pytest.mark.parametrize('angle', (0,90,180,270))
def test_rotated_page_transformation_uses_visible_page_coordinates(tmp_path,angle):
    layout=locate(tmp_path,'rotate_'+str(angle))
    assert layout['page_rotation']==angle
    assert layout['geometry_basis']=='VISIBLE_CROP_ROTATION_AWARE'
    assert len(layout['rects'])==1
    assert layout['schema_version']=='PDF_PAGE_BBOX/0.2'
    with fitz.open(tmp_path/f'rotate_{angle}.pdf') as doc:
        page=doc[0];pix=page.get_pixmap(matrix=fitz.Matrix(1,1))
        assert abs(layout['page_width']-pix.width)<1
        assert abs(layout['page_height']-pix.height)<1
        assert_text_overlap(pix,layout['rects'])


@pytest.mark.parametrize('kind', ('crop','crop_rotate_90'))
def test_cropped_page_geometry_matches_renderer(tmp_path,kind):
    layout=locate(tmp_path,kind)
    assert layout['page_cropbox'] == [40.0,50.0,480.0,650.0]
    with fitz.open(tmp_path/f'{kind}.pdf') as doc:
        page=doc[0];pix=page.get_pixmap(matrix=fitz.Matrix(1,1))
        assert layout['page_width']==pix.width
        assert layout['page_height']==pix.height
        assert_text_overlap(pix,layout['rects'])


def assert_text_overlap(pix,rects):
    """Boxes must actually overlap the visible black glyph pixels, not just be plausible dimensions."""
    n=pix.n
    total_dark=0
    for item in rects:
        x0,y0,x1,y1=item['rect_pdf_top_left']
        assert x1>x0 and y1>y0
        for y in range(max(0,int(y0)),min(pix.height,int(y1)+1)):
            for x in range(max(0,int(x0)),min(pix.width,int(x1)+1)):
                off=(y*pix.width+x)*n
                rgb=pix.samples[off:off+3]
                if len(rgb)==3 and max(rgb)<160:
                    total_dark+=1
    assert total_dark>45,f'Projected rects miss visible text, dark pixels={total_dark}'


def test_two_columns_unique_quote_remains_locatable(tmp_path):
    location=locate(tmp_path,'two_columns_valid')
    assert location['page']==1
    assert len(location['rects'])>=2


def test_false_flattened_cross_column_match_fails_closed(tmp_path):
    pdf=tmp_path/'cross.pdf';pdf.write_bytes(make_pdf('two_columns_cross_block'))
    phrase=LEFT+' '+RIGHT
    with pytest.raises(LocatorError,match='(?:CROSS_BLOCK_SEQUENCE_NOT_TRUSTWORTHY|NON_CONTIGUOUS_PDF_TEXT_GEOMETRY)'):
        locate_pdf_quote(pdf,phrase,sha(pdf.read_bytes()),1)


def test_false_concatenated_table_cells_refuse_bbox(tmp_path):
    pdf=tmp_path/'cells.pdf';pdf.write_bytes(make_pdf('table_cell_stitch'))
    with pytest.raises(LocatorError,match='(?:NON_CONTIGUOUS_PDF_TEXT_GEOMETRY|CROSS_BLOCK_SEQUENCE_NOT_TRUSTWORTHY)'):
        locate_pdf_quote(pdf,CELL_A+' '+CELL_B,sha(pdf.read_bytes()),1)


@pytest.mark.parametrize('kind',('repeated_same_page','repeated_two_pages'))
def test_repeated_quote_is_never_silently_disambiguated_by_page_hint(tmp_path,kind):
    pdf=tmp_path/f'{kind}.pdf';pdf.write_bytes(make_pdf(kind))
    with pytest.raises(LocatorError,match='AMBIGUOUS_MULTIPLE_PDF_MATCHES'):
        locate_pdf_quote(pdf,REPEATED,sha(pdf.read_bytes()),1)


def test_scanned_image_only_pdf_requires_explicit_ocr_layer_not_guess(tmp_path):
    pdf=tmp_path/'scan.pdf';pdf.write_bytes(make_pdf('scanned'))
    with pytest.raises(LocatorError,match='PDF_QUOTE_NOT_FOUND_NO_EXACT_BBOX'):
        locate_pdf_quote(pdf,EXACT,sha(pdf.read_bytes()),1)


def test_wrong_hint_is_not_substituted_for_true_pdf_page(tmp_path):
    r=locate(tmp_path,'rotate_90',hint=2)
    assert r['page']==1 and r['page_hint_agrees'] is False
    assert r['claimed_page_hint']==2


def test_corrupted_source_is_rejected_before_coordinates(tmp_path):
    pdf=tmp_path/'corp.pdf';pdf.write_bytes(make_pdf('crop_rotate_90'))
    oldsha=sha(pdf.read_bytes())
    with pdf.open('ab') as f: f.write(b'\n% malicious modification')
    with pytest.raises(LocatorError,match='SOURCE_PDF_SHA_MISMATCH'):
        locate_pdf_quote(pdf,EXACT,oldsha,1)


def test_server_rotated_cropped_pdf_png_and_anchor_roundtrip(tmp_path):
    blob=package(make_pdf('crop_rotate_90'),EXACT)
    client=TestClient(make_app(tmp_path/'runtime'))
    response=client.post('/api/import',files={'file':('adversarial.zip',blob,'application/zip')})
    assert response.status_code==200,response.text
    doc=client.get('/api/document').json()
    unit=next(u for u in doc['units'] if EXACT in u['raw'])
    offset=unit['raw'].index(EXACT)
    req={'unit_id':unit['unit_id'],'quote':EXACT,'start_utf16':offset,
         'end_utf16':offset+len(EXACT),'expected_revision':doc['revision'],
         'expected_source_markdown_sha256':doc['source_markdown_sha256']}
    a=client.post('/api/anchors',json=req)
    assert a.status_code==201,a.text
    aid=a.json()['anchor_id']
    l=client.post('/api/locators/'+aid+'/resolve',json={'expected_revision':doc['revision'],
               'expected_source_pdf_sha256':doc['source_pdf_sha256']})
    assert l.status_code==200,l.text
    location=l.json()['pdf_locator']
    assert location['page_rotation']==90 and location['page_width']==600 and location['page_height']==440
    png=client.get('/api/pdf/page/1/png?scale=1')
    assert png.status_code==200 and png.content[:8]==b'\x89PNG\r\n\x1a\n'
    assert client.get('/api/locators/'+aid).json()==l.json()
    assert client.get('/api/anchors').json()[0]['quote']==EXACT


def test_no_scientific_runtime_candidate_exposure(tmp_path):
    client=TestClient(make_app(tmp_path/'runtime'))
    assert client.get('/api/candidates').status_code==404