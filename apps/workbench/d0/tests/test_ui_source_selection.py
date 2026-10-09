"""Visible markdown text selections must still address exact raw UTF-16 bytes."""
import shutil
import subprocess
from pathlib import Path


def test_presented_source_keeps_original_offsets_after_markdown_and_emoji():
    node = shutil.which('node')
    assert node, 'Node is required for source selection regression'
    reader = (Path(__file__).resolve().parents[1] / 'web/reader.js').read_text()
    mapper = 'function plainMarkdown(raw){' + reader.split('function plainMarkdown(raw){', 1)[1].split('\nfunction togglePDF', 1)[0]
    script = r'''
const assert = require('assert');
MAPPER
const raw = '# Results 😀\n**300 adults** were randomised. Then **300 adults** were assessed.';
const shown = plainMarkdown(raw);
assert.equal(shown.text, 'Results 😀\n300 adults were randomised. Then 300 adults were assessed.');
for (const begin of [shown.text.indexOf('300 adults'), shown.text.lastIndexOf('300 adults')]) {
  const end = begin + '300 adults'.length;
  const startRaw = shown.offsets[begin], endRaw = shown.offsets[end - 1] + 1;
  assert.equal(raw.slice(startRaw, endRaw), '300 adults');
  assert.equal(startRaw, begin === shown.text.indexOf('300 adults') ? raw.indexOf('300 adults') : raw.lastIndexOf('300 adults'));
}
const plain = 'No formatting: 😀 300 adults';
const untouched = plainMarkdown(plain);
assert.equal(untouched.text, plain);
assert.equal(untouched.offsets.length, plain.length);
'''.replace('MAPPER', mapper)
    result = subprocess.run([node, '-e', script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_markdown_scientific_table_preserves_cell_source_ranges():
    node=shutil.which('node')
    assert node, 'Node is required for scientific table test'
    reader=(Path(__file__).resolve().parents[1]/'web/reader.js').read_text()
    parser='function parseSourceTable(raw){'+reader.split('function parseSourceTable(raw){',1)[1].split('\nfunction sourceTableElement',1)[0]
    script=r"""
const assert=require('assert');
MAPPER
const raw='| Outcome | Group A | Group B |\n|:---|---:|---:|\n| Records | 60 | 60 |\n| Mean | 31 | 29 |';
const rows=parseSourceTable(raw);
assert.equal(rows.length,3);
assert.equal(rows[0].length,3);
assert.equal(rows[2][1].text,'31');
for(const row of rows)for(const cell of row)
  assert.equal(raw.slice(cell.start,cell.end),cell.text);
assert.equal(parseSourceTable('a paragraph with | symbols'),null);
""".replace('MAPPER',parser)
    p=subprocess.run([node,'-e',script],capture_output=True,text=True)
    assert p.returncode==0,p.stderr


def _range_helpers():
    reader=(Path(__file__).resolve().parents[1]/'web/reader.js').read_text()
    return 'const ABBREVIATIONS'+reader.split('const ABBREVIATIONS',1)[1].split('\nfunction togglePDF',1)[0]


def test_sentence_range_skips_decimals_and_abbreviations():
    script=r'''
const assert=require('assert');
HELPERS
const raw='Adherence was high. 5:2SH and SBA achieved similar weight-loss at six months (-1.8kg (SD = 3.5) vs -1.7kg; p = 0.7), e.g. in Fig. 2. Next sentence.';
const at=raw.indexOf('similar');
const r=sentenceBounds(raw,at,at+7);
assert.equal(raw.slice(r.start,r.end),'5:2SH and SBA achieved similar weight-loss at six months (-1.8kg (SD = 3.5) vs -1.7kg; p = 0.7), e.g. in Fig. 2.');
const whole=raw.indexOf('Adherence');
assert.equal(raw.slice(...Object.values(sentenceBounds(raw,whole,whole+5))),'Adherence was high.');
const last=raw.indexOf('Next');
assert.equal(raw.slice(...Object.values(sentenceBounds(raw,last,last+4))),'Next sentence.');
'''.replace('HELPERS',_range_helpers())
    p=subprocess.run([shutil.which('node'),'-e',script],capture_output=True,text=True)
    assert p.returncode==0,p.stderr


def test_selection_snaps_to_whole_words_only_when_cut_mid_word():
    script=r'''
const assert=require('assert');
HELPERS
const text='Three hundred adults with obesity were randomised.';
let r=snapToWords(text,0,40);assert.equal(text.slice(r.start,r.end),'Three hundred adults with obesity were randomised');
r=snapToWords(text,text.indexOf('adults'),text.indexOf('adults')+6);assert.equal(text.slice(r.start,r.end),'adults');
r=snapToWords(text,8,15);assert.equal(text.slice(r.start,r.end),'hundred adults');
'''.replace('HELPERS',_range_helpers())
    p=subprocess.run([shutil.which('node'),'-e',script],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
