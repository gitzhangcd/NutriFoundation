"""Reader search helpers: query rules, whitespace-tolerant matching and snippets."""
import shutil
import subprocess
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / 'web/search_core.js'


def run_node(body):
    node = shutil.which('node')
    assert node, 'Node is required for reader search tests'
    source = CORE.read_text().replace('export ', '')
    result = subprocess.run([node, '-e', "const assert=require('assert');\n" + source + '\n' + body],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_query_rules_allow_two_character_chinese_and_normalise_whitespace():
    run_node(r'''
assert.equal(normalizeQuery('  weight \n\t loss  '),'weight loss');
assert.equal(queryProblem(''),'EMPTY');
assert.equal(queryProblem('   '),'EMPTY');
assert.equal(queryProblem('ab'),'TOO_SHORT');
assert.equal(queryProblem(' a  b '),'') ;
assert.equal(queryProblem('the'),'');
assert.equal(queryProblem('体'),'TOO_SHORT');
assert.equal(queryProblem('体重'),'');
''')


def test_match_ranges_case_insensitive_and_span_line_breaks():
    run_node(r'''
assert.deepEqual(matchRanges('Effect and effect; EFFECTS',' effect '),[[0,6],[11,17],[19,25]]);
assert.deepEqual(matchRanges('weight\n  loss was weight loss','weight  loss'),[[0,13],[18,29]]);
assert.deepEqual(matchRanges('a (b) [c]*','(b) [c]*'),[[2,10]]);
assert.deepEqual(matchRanges('anything',''),[]);
assert.deepEqual(matchRanges('共三百名肥胖成年人被随机分配','随机分配'),[[10,14]]);
''')


def test_snippet_marks_first_hit_with_context_and_ellipses():
    run_node(r'''
const long='x'.repeat(100)+' the main Effect of diet '+'y'.repeat(100);
const s=snippetParts(long,'effect');
assert.equal(s.match,'Effect');
assert.ok(s.before.startsWith('…')&&s.after.endsWith('…'));
assert.ok(s.before.length<=41&&s.after.length<=51);
const none=snippetParts('short text','zzz');
assert.deepEqual(none,{before:'short text',match:'',after:''});
const flat=snippetParts('a\n\nb effect','effect');
assert.equal(flat.before+flat.match+flat.after,'a b effect');
''')


def test_section_index_translation_matches_and_summary():
    run_node(r'''
const sections=sectionIndex([{unit_id:'U1',type:'SECTION',text:'Abstract'},{unit_id:'U2',type:'PARAGRAPH',text:'x'},
  {unit_id:'U3',type:'SECTION',text:'Methods \n'},{unit_id:'U4',type:'TABLE',text:'y'}]);
assert.equal(sections.get('U2'),'Abstract');assert.equal(sections.get('U4'),'Methods');assert.equal(sections.get('U3'),'Methods');
assert.deepEqual(translationMatches([['U2',['被随机分配']],['U4',['体重下降']]],'体重'),['U4']);
assert.equal(searchSummary(0,0),'没有找到匹配的原文或译文');
assert.equal(searchSummary(17,16),'共找到 17 处，已列出 16 处');
assert.equal(searchSummary(3,3,1),'共找到 3 处（其中 1 处仅在中文译文）');
''')


def test_reader_uses_bounded_results_and_does_not_scroll_page_from_outline():
    web = Path(__file__).resolve().parents[1] / 'web'
    reader, css, html = ((web / n).read_text() for n in ('reader.js', 'style.css', 'index.html'))
    assert "from './search_core.js'" in reader
    assert 'button.scrollIntoView' not in reader.split('function updateOutlineActive', 1)[1].split('\n}', 1)[0]
    assert '.search-list{' in css and 'max-height' in css.split('.search-list{', 1)[1].split('}', 1)[0]
    assert '.reader-scroll{min-height:' in css
    assert '::highlight(search-current)' in css and '::highlight(search-hit)' in css
    assert 'id="searchResults" class="small" hidden' in html and 'role="status"' not in html.split('id="searchResults"', 1)[1].split('id="searchStatus"', 1)[0]
