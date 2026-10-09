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
