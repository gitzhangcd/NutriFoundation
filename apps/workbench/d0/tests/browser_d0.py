"""Native Chromium acceptance: real HTTP, PDF.js, role gates and roundtrip.

Default uses disposable local synthetic data. D0_URL + D0_CREDENTIALS can run
against a separately provisioned acceptance instance through an SSH tunnel.
Never point this destructive synthetic workflow test at the user workspace.
"""
from __future__ import annotations
import json
import re
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE=Path(__file__).resolve().parents[1];REPO=BASE.parents[2]
sys.path.insert(0,str(BASE))
from auth import password_hash
from provision import NAMES

SELECT_JS="""([s,a,b])=>{const el=[...document.querySelectorAll('.unit-original')].find(x=>x.textContent.startsWith(s));el.scrollIntoView({block:'center'});const r=document.createRange();r.setStart(el.firstChild,a);r.setEnd(el.firstChild,b);const sel=getSelection();sel.removeAllRanges();sel.addRange(r);window.__selRect=JSON.parse(JSON.stringify(r.getBoundingClientRect()));document.querySelector('#units').dispatchEvent(new Event('pointerup',{bubbles:true}));}"""

CURRENT_HIT_JS="""()=>{const h=CSS.highlights.get('search-current');if(!h)return null;const r=[...h][0].getBoundingClientRect(),u=document.getElementById('units').getBoundingClientRect();return {inUnits:r.top>=u.top&&r.bottom<=u.bottom,inView:r.top>=0&&r.bottom<=innerHeight,text:[...h][0].toString()}}"""

def search_regressions(p,output):
    """Reader search plan P0-P2 on the real paper (R0, 1440x1000)."""
    q=p.locator('#query');hits=p.locator('#searchList .search-hit')
    q.fill('adherence');q.press('Enter')
    expect(p.locator('#searchStatus')).to_contain_text('共找到');assert hits.count()>0
    expect(hits.first.locator('mark')).to_have_text(re.compile('^adherence$',re.I))
    q.fill('');p.locator('#searchBtn').click();expect(p.locator('#searchStatus')).to_have_text('请输入要查找的词。')
    q.fill('effect');p.locator('#searchBtn').click()
    expect(p.locator('#searchStatus')).to_have_text(re.compile(r'^共找到 17 处，已列出 16 处$'))
    expect(p.locator('#searchMore')).to_be_visible();assert hits.count()==16
    box=p.locator('#units').bounding_box();assert box['height']>=190 and box['y']+box['height']<=1000,box
    assert p.locator('#searchList').bounding_box()['height']<=140
    assert p.evaluate("CSS.highlights.get('search-hit').size")>=17
    hits.nth(5).click()
    expect(p.locator('#searchPosition')).to_have_text('6 / 17');expect(hits.nth(5)).to_have_attribute('aria-current','true')
    expect(p.locator('#searchStatus')).to_contain_text('第 6 / 17 处')
    p.wait_for_timeout(700);current=p.evaluate(CURRENT_HIT_JS)
    assert current and current['inUnits'] and current['inView'] and current['text'].lower()=='effect',current
    assert p.evaluate('scrollY')==0
    expect(p.locator('#units .unit.search-current')).to_be_focused()
    output.mkdir(parents=True,exist_ok=True);p.screenshot(path=str(output/'search-current-hit.png'))
    q.press('Enter');expect(p.locator('#searchPosition')).to_have_text('7 / 17')
    q.press('Shift+Enter');expect(p.locator('#searchPosition')).to_have_text('6 / 17')
    for mode in ('chinese','parallel','english','immersive'):
        p.locator(f'[data-mode="{mode}"]').click();p.wait_for_timeout(500)
        current=p.evaluate(CURRENT_HIT_JS);assert current and current['inUnits'],(mode,current)
    p.locator('#searchMore').click();expect(hits).to_have_count(17);expect(p.locator('#searchMore')).to_be_hidden()
    expect(p.locator('#searchStatus')).to_have_text('共找到 17 处')
    p.locator('#searchToggle').click();expect(p.locator('#searchList')).to_be_hidden();expect(p.locator('#searchToggle')).to_have_attribute('aria-expanded','false')
    p.locator('#searchToggle').click();expect(p.locator('#searchList')).to_be_visible()
    p.locator('#searchList').evaluate('e=>{e.scrollTop=e.scrollHeight}');p.locator('#searchBtn').click()
    expect(hits).to_have_count(16);assert p.locator('#searchList').evaluate('e=>e.scrollTop')==0
    q.focus();q.press('ArrowDown');expect(hits.first).to_be_focused();p.keyboard.press('ArrowDown');expect(hits.nth(1)).to_be_focused()
    p.keyboard.press('Escape');expect(p.locator('#searchResults')).to_be_hidden();expect(q).to_be_focused();expect(q).to_have_value('effect')
    assert p.evaluate('[...CSS.highlights.keys()].filter(k=>k.startsWith("search"))')==[]
    q.press('Escape');expect(q).to_have_value('')
    q.fill('weight \n loss');q.press('Enter');expect(p.locator('#searchStatus')).to_contain_text('共找到 22 处')
    expect(p.locator('#searchClear')).to_be_visible();p.locator('#searchClear').click()
    expect(q).to_have_value('');expect(p.locator('#searchResults')).to_be_hidden();expect(q).to_be_focused()
    q.fill('effect');q.press('Enter');expect(hits).to_have_count(16);q.fill('');expect(p.locator('#searchResults')).to_be_hidden()
    q.fill('ab');q.press('Enter');expect(p.locator('#searchStatus')).to_contain_text('英文至少 3 个字母，中文至少 2 个字')
    q.fill('血糖');q.press('Enter');expect(p.locator('#searchStatus')).to_have_text('没有找到匹配的原文或译文')
    expect(p.locator('#searchTips')).to_contain_text('英文原文中不含中文')
    q.fill('随机分配');q.press('Enter');expect(p.locator('#searchStatus')).to_contain_text('仅在中文译文')
    expect(hits.first.locator('.search-source')).to_have_text('中文译文');expect(hits.first.locator('mark')).to_have_text('随机分配')
    expect(hits.first.locator('.search-section')).to_have_text('Methods')
    q.fill('zzzzqx');q.press('Enter');expect(p.locator('#searchTips')).to_contain_text('换同义词')
    p.locator('#searchClear').click()

def ux_regressions(sign_in,browser,url,credentials,checks,output):
    """UX review findings (P0/P1/P2) on fresh synthetic R0/R1 tasks."""
    page=browser.new_page();page.goto(url)
    page.locator('#username').fill('r0');page.locator('#password').fill('wrong-password');page.locator('#loginForm button').click()
    expect(page.locator('#loginStatus')).to_have_text('账号或密码不正确，请检查后重试。');page.close()
    r1ctx,r1=sign_in('r1');expect(r1.locator('#saveStatus')).to_have_text('已载入')
    expect(r1.locator('#units .empty-state')).to_contain_text('候选摘录尚未准备好')
    expect(r1.locator('#judgmentTitle')).to_have_text('候选复核')
    expect(r1.locator('#phase')).to_have_text('等待候选准备');r1ctx.close()
    ctx,p=sign_in('r0');expect(p.locator('#saveStatus')).to_have_text('已载入')
    expect(p.locator('#pdfEngine')).to_contain_text('PDF.js',timeout=30000)
    assert p.locator('.skip-links a').count()==3
    expect(p.locator('[data-mode="immersive"]')).to_have_attribute('aria-pressed','true')
    expect(p.locator('#modeHint')).to_contain_text('只有 3 处演练译文')
    search_regressions(p,output)
    # Outline follows reading position.
    p.evaluate("document.getElementById('units').scrollTop=document.getElementById('units').scrollHeight/2");p.wait_for_timeout(300)
    active=p.locator('#outline button.active').first.text_content()
    assert active not in ('Abstract','A randomised controlled trial of the 5:2 diet'),active
    # Paragraph citation hides markdown markers in the preview and does not leave the floating action behind.
    p.evaluate("document.querySelectorAll('.unit-footer .text-button')[0].click()")
    expect(p.locator('#quotePreview')).not_to_contain_text('**');expect(p.locator('#quoteMarkupNote')).to_be_visible()
    expect(p.locator('#selectionToolbar')).to_be_hidden()
    # The drawer replaces the judgment column instead of covering the reader.
    pane=p.locator('#evidencePane').bounding_box();reader=p.locator('.reader').bounding_box()
    assert pane['x']>=reader['x']+reader['width']-1,(pane,reader)
    p.locator('#tabJudgment').hover();p.wait_for_timeout(250)
    assert p.locator('#tabJudgment').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(238, 246, 241)'
    p.locator('#closeEvidence').click()
    # Sentence range does not stop at decimal points.
    p.locator('[data-mode="english"]').click()
    p.evaluate(SELECT_JS,['Adherence to 5:2SH',130,150]);p.locator('#selectionBind').click()
    p.locator('[data-quote-range="sentence"]').click()
    quote=p.locator('#quotePreview').text_content()
    assert quote.startswith('5:2SH and SBA achieved similar weight-loss') and quote.endswith('p = 0.55).'),quote
    p.locator('#closeEvidence').click()
    # Save two judgments, then cite from the item row: reader-first selection with a visible target hint.
    p.locator('[id="f-salient_existing_facts"]').fill('Synthetic fact A\nSynthetic fact B')
    p.locator('#saveDraft').click();expect(p.locator('#saveStatus')).to_have_text('已保存')
    p.locator('#judgmentItemRows .judgment-item-row').filter(has_text='Synthetic fact A').get_by_role('button').click()
    expect(p.locator('#evidencePane')).to_be_hidden();expect(p.locator('#citeTargetHint')).to_contain_text('已知事实 第 1 条')
    p.evaluate(SELECT_JS,['Three hundred adults',0,40])
    expect(p.locator('#selectionToolbar')).to_be_visible()
    toolbar=p.locator('#selectionToolbar').bounding_box();sel=p.evaluate('window.__selRect')
    assert toolbar['y']>=sel['bottom'] or toolbar['y']+toolbar['height']<=sel['top'],(toolbar,sel)
    p.locator('#selectionBind').click()
    expect(p.locator('#quotePreview')).to_have_text('Three hundred adults with obesity were randomised')
    expect(p.locator('#citeTargetHint')).to_be_hidden()
    expect(p.locator('#makeAnchor')).to_have_text('确认关联到「已知事实 第 1 条」')
    p.screenshot(path=str(output/'ux-explicit-target.png'))
    p.locator('#makeAnchor').click();expect(p.locator('#makeAnchor')).to_have_text('已关联 ✓',timeout=30000)
    expect(p.locator('#makeAnchor')).to_be_disabled();expect(p.locator('#evidenceFeedback')).to_have_class(re.compile('success'))
    expect(p.locator('#quoteNext')).to_be_visible();p.locator('#quoteNext').click()
    row=p.locator('#judgmentItemRows .judgment-item-row').filter(has_text='Synthetic fact A')
    expect(row).to_contain_text('1 条证据')
    # P0: a saved edit invalidates the link immediately, without reloading.
    p.locator('[id="f-salient_existing_facts"]').fill('Synthetic fact A edited\nSynthetic fact B')
    p.locator('#saveDraft').click();expect(p.locator('#saveStatus')).to_have_text('已保存')
    row=p.locator('#judgmentItemRows .judgment-item-row').filter(has_text='Synthetic fact A edited')
    expect(row).to_contain_text('需重新确认');expect(row).not_to_contain_text('1 条证据 ·')
    p.locator('#judgmentItemRows').evaluate('el=>el.scrollIntoView({block:"center"})');p.screenshot(path=str(output/'ux-saved-edit-stale.png'))
    p.locator('#nextReview').click()
    expect(p.locator('#reviewAnchors .stale-bindings')).to_contain_text('Three hundred adults with obesity were randomised')
    expect(p.locator('#reviewItemLinks')).to_contain_text('精确到判断条目的证据 0 条')
    expect(p.locator('#nextReview')).to_be_hidden();expect(p.locator('#footerBack')).to_be_visible()
    expect(p.locator('#freezeReason')).to_contain_text('请勾选下面的确认项')
    assert p.locator('#freeze').bounding_box()['y']<1000
    p.locator('#footerBack').click()
    # Demo material is not citable and says so.
    p.locator('#readerSource').select_option('demo');expect(p.locator('#translationStatus')).to_contain_text('16/16',timeout=15000)
    p.evaluate("""()=>{const el=document.querySelectorAll('.unit-original')[3];const r=document.createRange();r.setStart(el.firstChild,0);r.setEnd(el.firstChild,20);getSelection().removeAllRanges();getSelection().addRange(r);document.querySelector('#units').dispatchEvent(new Event('pointerup',{bubbles:true}));}""")
    expect(p.locator('#selectionError')).to_contain_text('不能作为证据引用')
    p.locator('#readerSource').select_option('paper');expect(p.locator('#readerSource')).to_have_attribute('data-ready-source','paper',timeout=30000)
    # Revision conflict keeps the local input after loading the newer server revision.
    other=ctx.new_page();other.goto(url);expect(other.locator('#saveStatus')).to_have_text('已载入',timeout=30000)
    other.locator('[id="f-decision_focus"]').fill('Saved from another window');other.locator('#saveDraft').click()
    expect(other.locator('#saveStatus')).to_have_text('已保存');other.close()
    p.locator('[id="f-decision_focus"]').fill('My unsaved local text');p.locator('#saveDraft').click()
    expect(p.locator('#saveStatus')).to_contain_text('草稿版本冲突')
    p.locator('#load').click();expect(p.locator('#saveStatus')).to_contain_text('恢复了你未保存的输入',timeout=30000)
    expect(p.locator('[id="f-decision_focus"]')).to_have_value('My unsaved local text')
    p.locator('[id="f-decision_focus"]').fill('Synthetic R0 independent judgment only');p.locator('#saveDraft').click()
    expect(p.locator('#saveStatus')).to_have_text('已保存')
    # Mobile keeps task switching and chapter navigation.
    p.set_viewport_size({'width':390,'height':844})
    expect(p.locator('#task')).to_be_visible();expect(p.locator('#outline')).to_be_visible()
    assert p.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    p.screenshot(path=str(output/'ux-mobile-navigation.png'))
    p.locator('#query').fill('effect');p.locator('#query').press('Enter');expect(p.locator('#searchStatus')).to_contain_text('共找到 17 处')
    assert p.locator('#searchList').bounding_box()['height']<=0.31*844
    p.locator('#searchList .search-hit').nth(3).click();p.wait_for_timeout(900)
    current=p.evaluate(CURRENT_HIT_JS);assert current and current['inView'] and current['inUnits'],current
    p.screenshot(path=str(output/'ux-mobile-search-hit.png'));ctx.close()
    checks.extend(['ux_login_message','ux_r1_empty_state','ux_search_enter_snippets','ux_outline_scroll_spy',
      'ux_markdown_free_preview','ux_drawer_beside_reader','ux_light_secondary_hover','ux_sentence_decimal','ux_reader_first_citation',
      'ux_toolbar_not_over_selection','ux_word_snapping','ux_bind_success_state','ux_saved_edit_invalidates_link',
      'ux_stale_binding_quote_listed','ux_freeze_reason_visible','ux_demo_not_citable','ux_conflict_keeps_input','ux_mobile_navigation',
      'search_bounded_list_reader_visible','search_body_and_snippet_highlight','search_total_and_load_more','search_prev_next_counter',
      'search_clear_and_escape','search_cjk_and_translation_hits','search_aria_status_only','search_whitespace_normalised',
      'search_section_labels','search_no_hit_tips','search_modes_keep_current_hit','search_mobile_hit_in_view','search_demo_disabled'])

def ea_integrated_browser(sign_in, checks):
    """Exercise EA in the actual v0.3 D0 layout, then return to NDS R0."""
    context, page = sign_in('r0')
    expect(page.locator('#eaModeBtn')).to_be_visible()
    page.locator('#eaModeBtn').click()
    expect(page.locator('#eaReview')).to_be_visible()
    expect(page.locator('#eaTaskBox')).to_be_visible()
    expect(page.locator('#judgmentPane')).to_be_visible()
    expect(page.locator('#eaProfile')).to_contain_text('WB_EA_RCT_V0_1')
    expect(page.locator('#readerTitle')).to_contain_text('5:2 diet')
    expect(page.locator('#eaTask option')).to_have_count(7)
    expect(page.locator('#eaSource option')).to_have_count(2)
    expect(page.locator('#eaCandidates .ea-candidate')).to_have_count(1)
    checks.append('ea_same_d0_login_layout_and_seven_profiles')

    # Source selection must remain within a server-issued two-version allowlist.
    page.locator('#eaSource').select_option('GUIDE-001:r1')
    expect(page.locator('#readerTitle')).to_contain_text('nutrition guidance')
    expect(page.locator('#sourceVersion')).to_contain_text('GUIDE-001:r1')
    page.locator('#eaSource').select_option('RCT-001:r1')
    expect(page.locator('#readerTitle')).to_contain_text('5:2 diet')
    expect(page.locator('#units')).to_contain_text('fictional 6-month comparison')
    checks.append('ea_switch_2_source_versions_in_original_reader')

    # Reuse original D0 quote-selection behavior and bind to typed candidate.
    page.locator('#units .unit-footer button').last.click()
    expect(page.locator('#eaQuoteStatus')).to_contain_text('已选原文')
    page.locator('#eaCandidates .ea-candidate button').first.click()
    expect(page.locator('#eaCandidates .ea-candidate')).to_contain_text('已绑定 1 条')
    page.locator('#eaCandidates .ea-disposition').select_option('MODIFY')
    page.locator('#eaCandidates .ea-support').select_option('PARTIAL')
    page.locator('#eaCandidates .ea-reason').fill('Synthetic trial only; no real scientific interpretation.')
    page.locator('#eaCandidates .ea-correction').fill('{"training_note":"Not real 5:2 effect data"}')
    page.once('dialog',lambda dialog:dialog.accept())
    page.locator('#eaFreeze').click()
    expect(page.locator('#eaFeedback')).to_contain_text('审核已冻结')
    expect(page.locator('#eaFreeze')).to_be_disabled()
    expect(page.locator('#eaReceipt')).to_contain_text('content_sha256')
    checks.append('ea_original_quote_binding_to_frozen_review')

    # Switching back must restore original NDS R0 profile/reader/PDF path.
    page.locator('#eaModeBtn').click()
    expect(page.locator('#eaReview')).to_be_hidden()
    expect(page.locator('#judgmentForm [data-key]')).to_have_count(19)
    expect(page.locator('#readerTitle')).to_have_text('A randomised controlled trial of the 5:2 diet')
    expect(page.locator('#pdfEngine')).to_contain_text('PDF.js',timeout=30000)
    checks.append('ea_return_to_original_nds_r0_pdf_bilingual_reader')
    context.close()


def run(url,credentials,output):
    errors=[];checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,channel='chromium')
        def sign_in(name):
            context=browser.new_context(viewport={'width':1440,'height':1000})
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url);assert page.title()=='NutriFoundation · Workbench'
            expect(page.locator('#loginPanel')).to_be_visible()
            page.locator('#username').fill(name);page.locator('#password').fill(credentials['accounts'][name]['password'])
            page.locator('#loginForm button').click();expect(page.locator('#workspace')).to_be_visible()
            return context,page
        output.mkdir(parents=True,exist_ok=True)
        ea_integrated_browser(sign_in,checks)
        ux_regressions(sign_in,browser,url,credentials,checks,output)
        r2ctx,r2=sign_in('r2')
        expect(r2.locator('#saveStatus')).to_have_text('已载入')
        # A review click is not a scientific completion receipt.
        expect(r2.locator('#draftProgress')).to_contain_text('0/5')
        r2.locator('#nextReview').click()
        expect(r2.locator('#reviewChecks')).to_contain_text('尚不能冻结')
        expect(r2.locator('#freeze')).to_be_disabled()
        assert r2.locator('#workflowNav .done').count()==0
        r2.locator('#backEdit').click()
        checks.append('empty_unsaved_review_not_submittable')
        # Full bilingual reading UX is self-authored synthetic and not citable.
        r2.locator('#readerSource').select_option('demo')
        expect(r2.locator('#translationStatus')).to_contain_text('16/16 双语覆盖')
        assert r2.locator('.scientific-table').count()==4
        assert r2.locator('#units .unit-translation').count()==16
        expect(r2.locator('#readerMeta')).to_contain_text('不可建立 SourceAnchor')
        expect(r2.locator('#query')).to_be_disabled();expect(r2.locator('#query')).to_have_attribute('placeholder',re.compile('练习资料不支持搜索'))
        r2.locator('#readerSource').select_option('paper')
        expect(r2.locator('#readerSource')).to_have_attribute('data-ready-source','paper',timeout=30000)
        expect(r2.locator('#units')).to_contain_text('randomised');expect(r2.locator('#query')).to_be_enabled()
        expect(r2.locator('#outline button').first).to_have_text('A randomised controlled trial of the 5:2 diet')
        expect(r2.locator('#pdfEngine')).to_contain_text('PDF.js',timeout=30000)
        checks.append('complete_synthetic_bilingual_document_and_tables')
        expect(r2.locator('#pdfEngine')).to_contain_text('PDF.js',timeout=30000)
        assert r2.locator('#judgmentForm [data-key]').count()==19
        expect(r2.locator('#units')).to_contain_text('randomised')
        expect(r2.locator('#bilingualToolbar')).to_be_visible()
        expect(r2.locator('#translationStatus')).to_contain_text('未经科学核查')
        assert r2.locator('.unit-translation').count() >= 1
        for mode in ('parallel', 'english', 'chinese', 'immersive'):
            r2.locator('#readerMode').select_option(mode)
            assert r2.locator('#units').get_attribute('data-reading-mode') == mode
        # Reference interaction: select -> quote confirmation -> range adjustment.
        r2.locator('#readerMode').select_option('english')
        r2.evaluate("""()=>{const el=[...document.querySelectorAll('.unit-original')].find(x=>x.textContent.startsWith('Ratings of interventions'));el.scrollIntoView();const r=document.createRange();r.setStart(el.firstChild,11);r.setEnd(el.firstChild,24);const s=getSelection();s.removeAllRanges();s.addRange(r);document.querySelector('#units').dispatchEvent(new Event('pointerup',{bubbles:true}));}""")
        expect(r2.locator('#selectionBind')).to_have_text('引用所选文字 →')
        r2.locator('#selectionBind').click()
        expect(r2.locator('#quotePreview')).to_have_text('interventions')
        expect(r2.locator('#makeAnchor')).to_be_disabled()
        output.mkdir(parents=True,exist_ok=True)
        r2.screenshot(path=str(output/'reference-quote-confirmation.png'))
        r2.locator('[data-quote-range="sentence"]').click()
        expect(r2.locator('#quotePreview')).to_have_text('Ratings of interventions are presented using median and IQR.')
        r2.locator('[data-quote-range="original"]').click()
        expect(r2.locator('#quotePreview')).to_have_text('interventions')
        # Cross-paragraph selection invalidates the previous citation immediately.
        r2.evaluate("""()=>{const els=[...document.querySelectorAll('.unit-original')];const i=els.findIndex(x=>x.textContent.startsWith('Ratings of interventions'));const r=document.createRange();r.setStart(els[i].firstChild,0);r.setEnd(els[i+1].firstChild,10);getSelection().removeAllRanges();getSelection().addRange(r);document.querySelector('#units').dispatchEvent(new Event('pointerup',{bubbles:true}));}""")
        expect(r2.locator('#makeAnchor')).to_be_disabled()
        expect(r2.locator('#quote')).to_have_value('')
        expect(r2.locator('#selectionError')).to_contain_text('跨越')
        r2.evaluate("""()=>{const cell=document.querySelector('.unit-original td');cell.scrollIntoView();const r=document.createRange();r.selectNodeContents(cell);getSelection().removeAllRanges();getSelection().addRange(r);document.querySelector('#units').dispatchEvent(new Event('pointerup',{bubbles:true}));}""")
        expect(r2.locator('#quoteTableContext')).to_be_visible()
        expect(r2.locator('[data-quote-range="paragraph"]')).to_be_disabled()
        r2.evaluate("""()=>{const cells=document.querySelectorAll('.unit-original td');const r=document.createRange();r.setStart(cells[0].firstChild,0);r.setEnd(cells[1].firstChild,1);getSelection().removeAllRanges();getSelection().addRange(r);document.querySelector('#units').dispatchEvent(new Event('pointerup',{bubbles:true}));}""")
        expect(r2.locator('#selectionError')).to_contain_text('跨越表格单元格')
        expect(r2.locator('#quote')).to_have_value('')
        r2.locator('#closeEvidence').click()
        checks.extend(['reference_selection_confirmation_range_and_invalidation','table_selection_context_and_invalidation'])
        r2.locator('#focusMode').click()
        assert 'focus-mode' in (r2.locator('#expertPanel').get_attribute('class') or '')
        r2.locator('#evidenceToggle').click()
        assert 'evidence-open' in (r2.locator('#expertPanel').get_attribute('class') or '')
        assert r2.evaluate("document.querySelector('.reader').inert") is False
        expect(r2.locator('#evidencePane')).to_have_attribute('aria-modal','false')
        expect(r2.locator('#closeEvidence')).to_be_focused()
        r2.keyboard.press('Escape')
        expect(r2.locator('#evidencePane')).to_be_hidden()
        expect(r2.locator('#evidenceToggle')).to_be_focused()
        r2.locator('#focusMode').click()
        translated=r2.locator('.unit-translation').first
        translated.evaluate('''el => {
            const range=document.createRange();
            range.selectNodeContents(el);
            const sel=window.getSelection();
            sel.removeAllRanges();sel.addRange(range);
            el.dispatchEvent(new Event('pointerup',{bubbles:true}));
        }''')
        expect(r2.locator('#selectionToolbar')).to_be_visible()
        r2.locator('#selectionBind').click()
        expect(r2.locator('#quoteAlignment')).to_be_visible()
        expect(r2.locator('#quotePreview')).not_to_be_empty()
        expect(r2.locator('#makeAnchor')).to_be_disabled()
        r2.locator('#closeEvidence').click()
        r2.locator('#dismissSelection').evaluate('(el)=>el.click()')
        checks.extend(['bilingual_four_modes','expert_focus_layout','translated_excerpt_source_binding'])

        expect(r2.locator('#workflowNav')).to_be_visible()
        assert r2.locator('#outline button').count()>0
        expect(r2.locator('#pdfDetails')).not_to_have_attribute('open','')
        r2.locator('#nativeComposer summary').click()
        expect(r2.locator('#nativeComposer')).to_be_visible()
        r2.locator('#nativeCategory').select_option('salient_existing_facts')
        r2.locator('#nativeStatement').fill('Expert-written synthetic fact with no model inference')
        r2.locator('#nativeAdd').click()
        expect(r2.locator('[id="f-salient_existing_facts"]')).to_have_value('Expert-written synthetic fact with no model inference')
        expect(r2.locator('#nativeMappingStatus')).to_contain_text('19个科学字段')
        expect(r2.locator('#nativeStatement')).to_have_value('')
        checks.append('expert_native_19_field_roundtrip')
        r2.locator('[id="f-decision_focus"]').fill('Synthetic D0 independent judgment only')
        r2.locator('#saveDraft').click();expect(r2.locator('#saveStatus')).to_have_text('已保存')
        r2.reload();expect(r2.locator('#saveStatus')).to_have_text('已载入')
        expect(r2.locator('[id="f-decision_focus"]')).to_have_value('Synthetic D0 independent judgment only')
        expect(r2.locator('[id="f-salient_existing_facts"]')).to_have_value('Expert-written synthetic fact with no model inference')
        # Item-level links require a saved canonical revision, not UI-only field selection.
        r2.locator('#evidenceToggle').click()
        r2.locator('#tabQuote').click()
        r2.locator('#field').select_option('decision_focus')
        r2.locator('#evidenceItem').select_option('0')
        r2.locator('#tabQuote').click()
        r2.locator('#manualQuote').evaluate('(el)=>{el.open=true}')
        r2.locator('#quote').fill('Three hundred adults with obesity were randomised')
        r2.locator('#locateQuote').click()
        r2.locator('#makeAnchor').click()
        expect(r2.locator('#status')).to_contain_text('第 1 条独立判断',timeout=30000)
        item_links=r2ctx.request.get(url+'/v1/tasks/SYN-R2/sources/SYN-5-2-PAPER/item-bindings')
        assert item_links.status==200
        assert any(x['field']=='decision_focus' and x['item_index']==0 and x['current_statement_matches'] for x in item_links.json()['items'])
        r2.locator('#tabLinked').click()
        expect(r2.locator('#evidenceReviewList')).to_contain_text('原文范围：服务端已校验')
        expect(r2.locator('#evidenceReviewList')).to_contain_text('判断关联：当前有效')
        expect(r2.locator('#evidenceReviewList')).to_contain_text('PDF：已核验')
        r2.locator('#evidenceReviewList').get_by_role('button',name='回看原文',exact=True).first.click()
        expect(r2.locator('#evidencePane')).to_be_hidden()
        assert r2.evaluate("CSS.highlights.has('evidence-source')")
        assert r2.evaluate("Array.from(CSS.highlights.get('evidence-source'))[0].toString()")=='Three hundred adults with obesity were randomised'
        r2.locator('[id="f-decision_focus"]').fill('Changed judgment')
        expect(r2.locator('#judgmentItemRows')).to_contain_text('需重新确认')
        r2.locator('#nextReview').click()
        expect(r2.locator('#reviewAnchors')).to_contain_text('旧关联需确认')
        expect(r2.locator('#freeze')).to_be_disabled()
        r2.locator('#backEdit').click()
        r2.locator('[id="f-decision_focus"]').fill('')
        r2.locator('#nextReview').click()
        expect(r2.locator('#reviewAnchors')).to_contain_text('1 条旧关联需确认')
        r2.locator('#backEdit').click()
        r2.locator('[id="f-decision_focus"]').fill('Synthetic D0 independent judgment only')
        r2.locator('#evidenceToggle').click()
        r2.locator('#drawerSubmitReview').click()
        expect(r2.locator('#reviewPane')).to_be_visible()
        expect(r2.locator('#reviewAnchors')).to_contain_text('缺少来源')
        r2.locator('#backEdit').click()
        r2.locator('#evidenceToggle').click()
        checks.extend(['item_level_judgment_evidence_bind','on_demand_nonmodal_review','exact_source_replay','changed_judgment_requires_review','drawer_to_submission_review'])
        r2.locator('#closeEvidence').click()
        expect(r2.locator('#evidencePane')).to_be_hidden()
        assert r2.evaluate("document.querySelector('.reader').inert") is False
        assert r2ctx.request.get(url+'/v1/tasks/SYN-R0/read-model').status==404
        assert r2ctx.request.get(url+'/v1/tasks/SYN-R2/candidate-set').status==403
        checks.extend(['native_pdfjs','19_field_profile','save_reload','cross_task_denial','R2_preAI_candidate_denial'])
        r2.locator('#evidenceToggle').click()
        r2.locator('#tabQuote').click()
        r2.locator('#manualQuote').evaluate('(el)=>{el.open=true}')
        r2.locator('#quote').fill('Three hundred adults with obesity were randomised')
        r2.locator('#locateQuote').click();expect(r2.locator('#status')).to_contain_text('已定位输入的准确引文')
        # A binding target is never preselected: the expert must choose the exact judgment.
        expect(r2.locator('#makeAnchor')).to_be_disabled()
        expect(r2.locator('#evidenceItemNotice')).to_contain_text('请选择这段原文要支撑哪一条判断')
        r2.locator('#evidenceItem').select_option('0')
        expect(r2.locator('#makeAnchor')).to_contain_text('关键问题 第 1 条')
        r2.locator('#makeAnchor').click();expect(r2.locator('#status')).to_contain_text('已通过服务端证据验证并绑定',timeout=30000)
        expect(r2.locator('.pdf-highlight')).not_to_have_count(0,timeout=30000)
        expect(r2.locator('#pdfLocatorStatus')).to_contain_text('PDF_PAGE_BBOX/0.2')
        output.mkdir(parents=True,exist_ok=True);r2.locator('#evidencePane').evaluate('(el)=>{el.scrollTop=0}');r2.screenshot(path=str(output/'workbench-desktop.png'),full_page=False)
        r2.set_viewport_size({'width':390,'height':844});assert r2.evaluate('document.documentElement.scrollWidth <= window.innerWidth');r2.screenshot(path=str(output/'workbench-mobile.png'),full_page=False)
        r2.set_viewport_size({'width':1440,'height':1000})
        checks.extend(['anchor_bind_original_pdf_highlight','explicit_binding_target_required'])
        r2.locator('#closeEvidence').click()
        r2.locator('#nextReview').click()
        expect(r2.locator('#reviewFields')).to_contain_text('Synthetic D0 independent judgment only')
        expect(r2.locator('#reviewChecks')).to_contain_text('已由服务端保存')
        r2.locator('#backEdit').click()
        expect(r2.locator('[id=\"f-decision_focus\"]')).to_have_value('Synthetic D0 independent judgment only')
        r2.locator('#nextReview').click()
        r2.locator('#unexposed').check();r2.locator('#freeze').click()
        expect(r2.locator('#saveStatus')).to_have_text('已冻结 · 合成工程记录')
        expect(r2.locator('#receipt')).to_contain_text('J_preAI')
        prodctx,prod=sign_in('producer');prod.locator('#prepareTask').select_option('SYN-R2');prod.locator('#prepare').click()
        expect(prod.locator('#producerStatus')).to_contain_text('FROZEN_SYNTHETIC_ONLY')
        r2.locator('#load').click();expect(r2.locator('#submitCandidates')).to_be_visible()
        r2.locator('[id="f-decision_focus"]').fill('Synthetic D0 post-AI judgment only')
        r2.locator('.disposition').select_option('ACCEPT');r2.locator('.rationale').fill('Synthetic reconciliation for engineering acceptance')
        r2.locator('.changed').check();r2.locator('#submitCandidates').click()
        expect(r2.locator('#saveStatus')).to_have_text('复核提交已锁定 · 合成工程记录')
        r2.reload();expect(r2.locator('#saveStatus')).to_have_text('已载入')
        expect(r2.locator('[id="f-decision_focus"]')).to_have_value('Synthetic D0 post-AI judgment only')
        expect(r2.locator('[id="f-decision_focus"]')).to_be_disabled()
        checks.append('review_returns_without_losing_canonical_judgment')
        checks.extend(['R2_preAI_freeze','producer_phase_gate','R2_postAI_reconcile_reload_immutable'])
        prod.locator('#prepareTask').select_option('SYN-R1');prod.locator('#prepare').click()
        expect(prod.locator('#producerStatus')).to_contain_text('FROZEN_SYNTHETIC_ONLY')
        r1ctx,r1=sign_in('r1');expect(r1.locator('#saveStatus')).to_have_text('已载入')
        expect(r1.locator('#units')).to_contain_text('Three hundred adults')
        assert r1ctx.request.get(url+'/v1/tasks/SYN-R1/sources/SYN-5-2-PAPER/original.pdf').status==404
        assert r1ctx.request.get(url+'/v1/tasks/SYN-R1/sources/SYN-5-2-PAPER/translations').status==404
        expect(r1.locator('#bilingualToolbar')).to_be_hidden()
        checks.append('R1_bilingual_source_denied')
        r1.locator('.rationale').fill('Synthetic R1 verification only');r1.locator('#submitCandidates').click()
        expect(r1.locator('#saveStatus')).to_have_text('请先为每条候选选择处置')
        r1.locator('.disposition').select_option('ACCEPT');r1.locator('#submitCandidates').click()
        expect(r1.locator('#saveStatus')).to_have_text('复核提交已锁定 · 合成工程记录')
        r1.reload();expect(r1.locator('#receipt')).to_contain_text('R1_verified')
        checks.extend(['R1_candidate_excerpt_only','R1_full_pdf_denied','R1_verification_reload'])
        r0ctx,r0=sign_in('r0');expect(r0.locator('#saveStatus')).to_have_text('已载入')
        assert r0ctx.request.get(url+'/v1/tasks/SYN-R0/candidate-set').status==403
        r0.locator('[id="f-decision_focus"]').fill('Synthetic R0 independent judgment only')
        r0.locator('#saveDraft').click();expect(r0.locator('#saveStatus')).to_have_text('已保存')
        r0.locator('#nextReview').click();r0.locator('#unexposed').check();r0.locator('#freeze').click();expect(r0.locator('#saveStatus')).to_have_text('已冻结 · 合成工程记录')
        expect(r0.locator('#draftProgress')).to_contain_text('已冻结（只读）');expect(r0.locator('#freezeReason')).to_contain_text('已冻结')
        expect(r0.locator('[data-stage="freeze"]')).to_have_class(re.compile('active'))
        r0.reload();expect(r0.locator('[id="f-decision_focus"]')).to_be_disabled()
        checks.extend(['R0_permanent_candidate_denial','R0_freeze_reload_immutable'])
        mgrctx,mgr=sign_in('manager');expect(mgr.locator('#readiness')).to_contain_text('NO-GO')
        expect(mgr.locator('#readiness')).to_contain_text('BLOCK_UPSTREAM_SCIENTIFIC_VERSION_CONFLICT');expect(mgr.locator('#readiness')).to_contain_text('阻塞：上游科学版本冲突')
        actx,auditor=sign_in('auditor');auditor.locator('#auditTask').select_option('SYN-R2');auditor.locator('#audit').click()
        expect(auditor.locator('#auditResult')).to_contain_text('FREEZE_J_postAI');expect(auditor.locator('#auditResult')).to_contain_text('前后哈希逐条衔接')
        r2.locator('#logout').click();expect(r2.locator('#loginPanel')).to_be_visible()
        assert r2ctx.request.get(url+'/v1/tasks').status==401
        checks.extend(['manager_NO_GO','auditor_integrity_chain','logout_revocation','ux_post_freeze_state','ux_readable_manager_auditor'])
        browser.close()
    assert not errors,errors
    result={'status':'PASS','checks':checks,'page_errors':errors,'native_pdfjs':True,'browser':'Chromium',
            'browser_plugin':'NOT_AVAILABLE_REGULAR_PLAYWRIGHT','viewports':['1440x1000','390x844'],
            'scientific_capture':False,'url':url}
    (output/'browser-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

def main():
    os.umask(0o077)
    output=Path(os.environ.get('D0_QA_OUTPUT',str(Path(tempfile.gettempdir())/'nutri-d0-browser-qa')))
    if os.environ.get('D0_URL'):
        run(os.environ['D0_URL'],json.loads(Path(os.environ['D0_CREDENTIALS']).read_text()),output);return
    with tempfile.TemporaryDirectory(prefix='nutri-d0-browser-') as td:
        root=Path(td);accounts={};credentials={'accounts':{}}
        for name,actor,role in NAMES:
            password='Synthetic-Browser-Acceptance-Only-1234'
            accounts[name]={'actor':actor,'role':role,'password_hash':password_hash(password)}
            credentials['accounts'][name]={'password':password}
        p=root/'accounts.json';p.write_text(json.dumps(accounts));p.chmod(0o600)
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        url=f'http://127.0.0.1:{port}'
        with (root/'server.log').open('w') as log:
            proc=subprocess.Popen([sys.executable,str(BASE/'d0_app.py'),'--repo-root',str(REPO),'--root',str(root/'data'),
              '--accounts',str(p),'--auth-db',str(root/'auth.sqlite'),'--origin',url,'--port',str(port),'--allow-synthetic-execution'],stdout=log,stderr=log)
            try:
                for _ in range(80):
                    if proc.poll() is not None:raise RuntimeError((root/'server.log').read_text())
                    try:urllib.request.urlopen(url+'/health',timeout=1);break
                    except OSError:time.sleep(.15)
                else:raise RuntimeError('SERVER_START_TIMEOUT')
                run(url,credentials,output)
            except Exception:
                print('BROWSER_FAILURE_SERVER_DIAGNOSTIC',file=sys.stderr)
                print((root/'server.log').read_text(),file=sys.stderr)
                raise
            finally:proc.terminate();proc.wait(timeout=10)
if __name__=='__main__':main()
