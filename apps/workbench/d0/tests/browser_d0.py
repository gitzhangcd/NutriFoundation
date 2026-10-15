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
    context, page = sign_in('ea1')
    expect(page.locator('#eaModeBtn')).to_be_visible()
    expect(page.locator('#eaModeBtn')).to_be_disabled()
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

    # No EA actor may acquire NDS R0 source/case information.
    assert context.request.get(page.url.rstrip('/')+'/v1/tasks/SYN-R0/read-model').status==404
    page.locator('#logout').click()
    expect(page.locator('#loginPanel')).to_be_visible()
    context.close()

    # The original separate R0 expert session remains intact and sees no EA.
    nds_context, nds=sign_in('r0')
    expect(nds.locator('#eaModeBtn')).to_be_hidden()
    expect(nds.locator('#judgmentForm [data-key]')).to_have_count(19)
    expect(nds.locator('#readerTitle')).to_have_text('A randomised controlled trial of the 5:2 diet')
    expect(nds.locator('#pdfEngine')).to_contain_text('PDF.js',timeout=30000)
    checks.append('ea_expert_credential_isolation_and_original_nds_r0_pdf_unchanged')
    nds_context.close()



def tpa_management_browser(browser,url,credentials,sign_in,checks,output,errors):
    """Real Chromium sequence through the NEW /manage page and ORIGINAL EA reader."""
    def manager_login(name):
        ctx=browser.new_context(viewport={'width':1440,'height':1000})
        page=ctx.new_page()
        page.on('pageerror',lambda e:errors.append('TPA: '+str(e)))
        page.goto(url+'/manage')
        expect(page.locator('#loginScreen')).to_be_visible()
        page.locator('#username').fill(name)
        page.locator('#password').fill(credentials['accounts'][name]['password'])
        page.locator('#loginForm button').click()
        expect(page.locator('#workspace')).to_be_visible(timeout=30000)
        return ctx,page
    producer_context,p=manager_login('producer')
    # V2-P0: verify the new route does not inherit fixture provenance as
    # authoritative persisted source state. All six internal fixtures are DEMO
    # until independently returned by /v1/p2/sources.
    p.locator('[data-p11-route="studio-v2"]').click()
    expect(p.locator('#p2v2App')).to_be_visible(timeout=15000)
    expect(p.locator('#p2v2App .page-stepper .stepitem')).to_have_count(4)
    expect(p.locator('#p2v2App .queue-metrics')).to_be_visible()
    assert p.evaluate("""() => window.__p2v2.sources.every(s =>
        s.live===true || (s.sourceType==='DEMO' &&
        s.rights==='NOT_ELIGIBLE' && s.qa===0 &&
        !s.raw && !s.doc && !s.package))""")
    assert p.evaluate("""() => window.__p2v2.sources
        .filter(s=>s.live===true).every(s=>s.id.startsWith('P2-SYN-'))""")
    assert p.evaluate("""() => window.__p2v2.sources
        .some(s=>s.sourceType==='DEMO' && s.id==='SYN-GUIDE-026')""")
    p.screenshot(path=str(output/'p2-v2-p0-provenance-queue-1440.png'),full_page=False)
    p.locator('[data-p11-route="studio"]').click()
    # B1: operate the existing seven-authoritative-fixture reference library.
    # B1 remains reachable through the unified Scientific Source primary entry.
    p.locator('[data-p11-route="studio"]').click()
    p.locator('.p2-heading').get_by_role('button',name='B1 合成来源引用 ↗').click()
    expect(p.locator('#b1SourceRows .p11-source-entry')).to_have_count(7)
    expect(p.locator('[data-p11-route="studio"]')).to_have_attribute('aria-current','page')
    assert p.locator('#b1SourcesPage').count()==0  # page is p11SourcesPage, not another app
    assert p.locator('#p11SourcesPage').count()==1
    p.locator('#b1SourceRows .p11-source-entry').filter(has_text='RCT-001').get_by_role('button',name='查看版本').click()
    expect(p.locator('#b1VersionDetail')).to_contain_text('RCT-001')
    expect(p.locator('#b1VersionDetail')).to_contain_text('EA_SEEDED_FIXTURE')
    expect(p.locator('#b1PackageStatus')).to_contain_text('尚未登记')
    p.locator('#b1ValidatePackage').click()
    expect(p.locator('#b1PackageStatus')).to_contain_text('VALIDATED_SYNTHETIC_REFERENCE')
    expect(p.locator('#b1RegisterPackage')).to_be_enabled()
    p.locator('#b1RegisterPackage').click()
    # Receipt distinguishes a genuine backend rejection from a stale client read model.
    try:
        expect(p.locator('#receipt')).to_contain_text('"b1_registration"',timeout=6000)
    except AssertionError:
        raise AssertionError('B1_REGISTER_UI_RECEIPT: '+str(p.locator('#receipt').text_content())+
                             ' ; packages='+str(producer_context.request.get(url+'/v1/tpa/source-packages').json()))
    assert producer_context.request.get(url+'/v1/tpa/source-packages').json()['total']==1
    try:
        expect(p.locator('#b1PackageStatus')).to_contain_text('SPKG-SYN-RCT-001-R1')
    except AssertionError:
        raise AssertionError('B1_STATUS_DESYNC receipt='+str(p.locator('#receipt').text_content())+
            ' detail='+str(p.locator('#b1VersionDetail').text_content())+
            ' list='+str(producer_context.request.get(url+'/v1/tpa/source-packages').json()))
    expect(p.locator('#b1PackageStatus')).to_contain_text('SYNTHETIC_REFERENCE_ONLY')
    expect(p.locator('.p11-structure-table tbody tr')).to_have_count(2)
    assert 'A synthetic randomized trial compares' not in p.locator('#p11SourcesPage').text_content()
    assert 'original_units_exposed' not in p.locator('#p11SourcesPage').text_content()
    p.reload()
    expect(p.locator('#workspace')).to_be_visible(timeout=30000)
    expect(p.locator('#b1PackageStatus')).to_contain_text('SPKG-SYN-RCT-001-R1')
    assert 'source=RCT-001' in p.evaluate('location.hash')
    assert 'revision=r1' in p.evaluate('location.hash')
    p.screenshot(path=str(output/'b1-source-library-synthetic.png'),full_page=True)
    # P2 Source Studio: additive UI-only preview. Existing B1 remains unchanged.
    p.locator('[data-p11-route="studio"]').click()
    expect(p.locator('#p11SectionTitle')).to_have_text('科学资料')
    expect(p.locator('.p2-studio')).to_be_visible(timeout=15000)
    expect(p.locator('#p2TableTarget tbody tr')).to_have_count(6)
    # P2.1-C explicit origin isolation: never imply that fictional Demo rows
    # are qualified, persisted scientific sources.
    source_modes=p.locator('.p2-source-modes')
    expect(source_modes).to_be_visible()
    expect(source_modes).to_contain_text('两类资料严格分离')
    source_modes.get_by_role('button',name='已登记合成来源').click()
    expect(p.locator('#p2TableTarget tbody tr')).to_have_count(1) # empty-state row
    expect(p.locator('#p2TableTarget')).to_contain_text('当前范围没有符合条件的来源版本')
    source_modes.get_by_role('button',name='仅界面演示').click()
    expect(p.locator('#p2TableTarget tbody tr')).to_have_count(6)
    source_modes.get_by_role('button',name='全部（含演示）').click()
    expect(p.locator('#p2TableTarget tbody tr')).to_have_count(6)
    expect(p.locator('.p2-queue-summary')).to_be_visible()
    expect(p.locator('.p2-source-queue')).to_be_visible()
    expect(p.locator('.p2-next-cell')).to_have_count(6)
    assert p.locator('.p2-source-queue').bounding_box()['y'] < p.locator('.p2-flow-steps').bounding_box()['y']
    expect(p.locator('.p2-flow-steps')).to_be_visible()
    expect(p.locator('.p2-flow-step')).to_have_count(4)
    expect(p.locator('.p2-choices .p2-choice')).to_have_count(4)
    expect(p.locator('.p2-stats .p2-stat')).to_have_count(4)
    expect(p.locator('.p2-tabs [data-p2-tab]')).to_have_count(6)
    # High-fidelity v1 information architecture: four primary work areas
    # and two distinct supporting operations, without removing legacy routes.
    expect(p.locator('.p2-primary-tabs [data-p2-tab]')).to_have_count(4)
    expect(p.locator('.p2-secondary-tabs [data-p2-tab]')).to_have_count(2)
    expect(p.locator('.p2-primary-tabs')).to_contain_text('工作队列总览')
    expect(p.locator('.p2-primary-tabs')).to_contain_text('QA 阅读与锚点核验')
    expect(p.locator('.p2-page-stepper')).to_be_visible()
    expect(p.locator('.p2-workgrid')).to_be_visible()
    expect(p.locator('.p2-inline-detail')).to_be_visible()
    expect(p.locator('.p2-qual-list .p2-qual-row')).to_have_count(5)
    expect(p.locator('.p2-heading h1')).to_have_text('科学资料处理台')
    expect(p.locator('.p2-meta-strip')).to_be_visible()
    expect(p.locator('.p2-meta-strip')).to_contain_text('仅限隔离合成工程')
    expect(p.locator('#p2TableTarget thead th')).to_have_count(8)
    expect(p.locator('#p2TableTarget thead')).to_contain_text('资料资格')
    expect(p.locator('#p2TableTarget thead')).to_contain_text('引用范围')
    expect(p.locator('.p2-source-queue .p2-source-title')).to_have_count(6)
    expect(p.locator('.p2-source-queue .p2-row-progress')).to_have_count(6)
    expect(p.locator('.p2-source-queue .p2-checkcell input')).to_have_count(6)
    # Demo v1: Project/Batch scope sits under the page stepper as a top bar.
    expect(p.locator('.p2-studio > .p2-context')).to_have_count(1)
    expect(p.locator('.p2-source-queue .p2-context')).to_have_count(0)
    expect(p.locator('#p2NavGroup')).to_have_count(0)
    expect(p.locator('#p11Nav [data-p11-route="sources"]')).to_be_hidden()
    expect(p.locator('#p11Nav [data-p11-route="studio"]')).to_be_visible()
    expect(p.locator('.p2-tabs [aria-current="page"]')).to_have_count(1)
    # WB-P2.1-A compact Project/Batch usage-reference filter. Scope is not IAM.
    expect(p.locator('.p2-context.p2-context-compact')).to_be_visible()
    expect(p.locator('.p2-scope-current')).to_have_text('全部来源 · 未筛选')
    expect(p.locator('.p2-context')).to_contain_text('不改变资料资格或专家权限')
    expect(p.locator('#p2ScopeFields')).to_be_hidden()
    p.locator('.p2-scope-toggle').click()
    expect(p.locator('#p2ScopeFields')).to_be_visible()
    expect(p.locator('#p2ScopeFields select')).to_have_count(2)
    expect(p.locator('#p2ScopeFields')).to_contain_text('筛选不是授权')
    p.locator('.p2-scope-toggle').click()
    expect(p.locator('#p2ScopeFields')).to_be_hidden()
    # Source-specific responsive kill gates. Local table scrolling is permitted;
    # top-level document and both navigation surfaces must remain bounded.
    # Capture the corrected desktop overview before responsive kill tests,
    # so a narrow-screen regression cannot suppress the visual review asset.
    p.set_viewport_size({'width':1440,'height':1000})
    p.screenshot(path=str(output/'p2-1-v1-revised-source-overview-1440.png'),full_page=False)
    for width,height in [(390,844),(680,900),(740,900),(768,900),(1024,900),(1440,1000)]:
        p.set_viewport_size({'width':width,'height':height})
        expect(p.locator('.p2-tabs')).to_be_visible()
        if width==390:
            p.screenshot(path=str(output/'p2-1-v1-revised-source-overview-390.png'),full_page=False)
            offenders=p.evaluate("""() => [...document.querySelectorAll('*')]
                .filter(e=>e.getBoundingClientRect().width>0 &&
                    (e.getBoundingClientRect().right>innerWidth+1 ||
                     e.getBoundingClientRect().left< -1) &&
                     getComputedStyle(e).position!=='fixed')
                .slice(0,24).map(e=>({tag:e.tagName,cls:e.className?.toString().slice(0,90),
                    w:Math.round(e.getBoundingClientRect().width),
                    l:Math.round(e.getBoundingClientRect().left),
                    r:Math.round(e.getBoundingClientRect().right)}))""")
            print('P2_V1_MOBILE_OVERFLOW_DIAGNOSTIC',offenders)
        assert p.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),width
        if width==390:
            # True phone layout: the source queue becomes readable cards and
            # the engineering header no longer consumes most of the viewport.
            assert p.locator('.tpa-header').evaluate('(e)=>e.getBoundingClientRect().height')<125
            assert p.locator('.p2-source-queue .p2-table tbody tr').first.evaluate(
                '(e)=>getComputedStyle(e).display')=='grid'
            assert p.locator('.p2-source-queue .p2-table thead').evaluate(
                '(e)=>getComputedStyle(e).display')=='none'
        assert p.locator('.p2-context').evaluate('(e)=>e.getBoundingClientRect().height')<120,width
        assert p.evaluate('document.querySelector("#p11Nav").getBoundingClientRect().width <= innerWidth + 1'),width
        if width<=740:
            # Regression: secondary nav formerly broke into per-character columns.
            assert p.evaluate('document.querySelector("#p11Nav").getBoundingClientRect().height < 110'),width
            assert p.evaluate('document.querySelector(".p2-tabs").getBoundingClientRect().height < 90'),width
        if width in (390,680,768,1440):
            p.screenshot(path=str(output/f'p2-1-a-source-overview-{width}.png'),full_page=False)
    expect(p.locator('.p2-pipeline')).to_be_visible()
    # A narrow-screen user can scroll to and activate the last tab without
    # the SPA snapping its horizontal navigation back to the first tab.
    p.set_viewport_size({'width':390,'height':844})
    tabs=p.locator('.p2-tabs')
    tabs.evaluate('(e)=>{e.scrollLeft=e.scrollWidth}')
    assert tabs.evaluate('(e)=>e.scrollLeft')>0
    tabs.locator('[data-p2-tab="audit"]').click()
    expect(tabs.locator('[data-p2-tab="audit"]')).to_have_attribute('aria-current','page')
    assert tabs.evaluate('(e)=>e.scrollLeft')>0
    expect(p.locator('.p2-context')).to_have_count(0)
    expect(p.locator('.p2-heading')).to_contain_text('不受 Project / Batch 筛选影响')
    expect(p.locator('.p2-primary-tabs')).to_contain_text('版本谱系与审计')
    expect(p.locator('.p2-lineage .p2-line-node')).to_have_count(4)
    expect(p.locator('.p2-version-tabs')).to_be_visible()
    p.locator('.p2-version-tabs').get_by_role('button',name='规范依赖与符合性').click()
    expect(p.locator('.p2-matrix-table tbody tr')).to_have_count(15)
    p.screenshot(path=str(output/'p2-1-a-audit-no-irrelevant-scope.png'),full_page=False)
    p.screenshot(path=str(output/'p2-hifi-v1-audit-matrix-390.png'),full_page=False)
    p.set_viewport_size({'width':1440,'height':1000})
    p.locator('.p2-tabs [data-p2-tab="library"]').click()
    # Real keyboard navigation must keep focus after SPA subtree re-render.
    p.locator('.p2-tabs [data-p2-tab="qa"]').focus()
    p.keyboard.press('Enter')
    expect(p.locator('.p2-tabs [data-p2-tab="qa"]')).to_be_focused()
    expect(p.locator('.p2-tabs [aria-current="page"]')).to_have_count(1)
    p.locator('.p2-tabs [data-p2-tab="library"]').click()
    p.screenshot(path=str(output/'p2-html-v02-aligned-overview-desktop.png'),full_page=True)
    p.screenshot(path=str(output/'p2-hifi-v1-workqueue-desktop.png'),full_page=False)
    checks.append('p2_1_a_single_nav_responsive_390_680_740_768_1024_1440_keyboard_focus')
    checks.append('p2_1_a_compact_scope_default_collapsed_audit_global_not_project_scoped')
    p.locator('#p2TableTarget tbody tr').first.get_by_role('button',name='查看演示说明').click()
    expect(p.get_by_role('dialog',name='科学来源版本详情').locator('.p2-detail-workflow')).to_be_visible()
    # P2.1-D single-source workspace: workflow, evidence checkpoints, stage
    # navigation, and original credentials, all gated by existing APIs.
    source_dialog=p.get_by_role('dialog',name='科学来源版本详情')
    expect(source_dialog).to_contain_text('单篇来源工作区')
    expect(source_dialog.locator('.p2-source-stage-cards .p2-stage-card')).to_have_count(4)
    expect(source_dialog.locator('.p2-source-jump button')).to_have_count(4)
    expect(source_dialog).to_contain_text('NOT_COMPUTED_DEMO')
    p.get_by_role('dialog',name='科学来源版本详情').get_by_role('button',name='关闭').click()
    p.locator('.p2-tabs [data-p2-tab="qa"]').click()
    expect(p.locator('.p2-qa-grid')).to_be_visible()
    expect(p.locator('.p2-reading-context')).to_be_visible()
    expect(p.locator('.p2-reading-context')).to_contain_text('不具有真实原件核验资格')
    expect(p.locator('.p2-unit')).to_have_count(3)
    p.locator('.p2-unit').nth(1).click()
    expect(p.locator('.p2-qa-grid')).to_contain_text('UNRESOLVED')
    p.locator('.p2-heading').get_by_role('button',name='显示锚点对应').click()
    expect(p.locator('.p2-qa-grid .p2-unit.selected mark.p2-highlighted-quote')).to_be_visible()
    expect(p.locator('.p2-pdf-sheet mark.p2-highlighted-quote')).to_be_visible()
    p.locator('.p2-qa-grid').get_by_role('button',name='检查封存条件（演示阻断）').click()
    expect(p.locator('.p2-studio')).to_contain_text('封存失败')
    p.locator('.p2-tabs [data-p2-tab="library"]').click()
    p.locator('.p2-heading').get_by_role('button',name='＋ 登记科学来源').click()
    expect(p.get_by_role('dialog',name='来源登记 · 受控合成准备')).to_be_visible()
    p.get_by_role('dialog',name='来源登记 · 受控合成准备').get_by_role('button',name='关闭').click()
    # P2 production-code flow with synthetic sources only: separate human authority.
    p.locator('.p2-heading').get_by_role('button',name='＋ 登记科学来源').click()
    for _ in range(3):
        p.locator('.p2-modal-actions').get_by_role('button',name='下一步').click()
    p.locator('.p2-modal-actions').get_by_role('button',name='提交合成来源登记').click()
    expect(p.locator('.p2-studio')).to_contain_text('来源已登记',timeout=20000)
    info=producer_context.request.get(url+'/v1/p2/sources').json()
    assert info['total']==1,info
    source_id=info['sources'][0]['source_id']
    assert info['sources'][0]['status']=='RIGHTS_HOLD'
    expect(p.locator('#p2TableTarget tbody tr')).to_have_count(7)
    expect(p.locator('#p2TableTarget tbody tr').filter(has_text=source_id).locator('.p2-next-cell')).to_contain_text('等待独立用途审核')
    # Auditor independent session: rights approval, never original units.
    a_ctx=browser.new_context(viewport={'width':1440,'height':900})
    a=a_ctx.new_page();a.on('pageerror',lambda e:errors.append('P2AUDITOR: '+str(e)))
    a.goto(url+'/source-qa')
    expect(a.locator('#p2Login')).to_be_visible()
    a.locator('#p2Username').fill('auditor')
    a.locator('#p2Password').fill(credentials['accounts']['auditor']['password'])
    a.locator('#p2LoginForm button[type="submit"]').click()
    expect(a.locator('#workspace')).to_be_visible(timeout=30000)
    assert a_ctx.request.get(url+'/v1/p2/sources/'+source_id+'/r1/original').status==403
    expect(a.locator('.p2-primary-tabs')).to_contain_text('版本谱系与审计')
    row=a.locator('#p2TableTarget tbody tr').filter(has_text=source_id)
    expect(row).to_be_visible(timeout=20000)
    row.get_by_role('button',name='查看并审核').click()
    a.get_by_role('dialog',name='科学来源版本详情').get_by_role('button',name='记录独立合成使用权').click()
    expect(a.locator('.p2-studio')).to_contain_text('合成用途审查记录已签发',timeout=20000)
    a.screenshot(path=str(output/'p2-rights-review.png'),full_page=True);a_ctx.close()
    # Producer runs deterministic conversion only AFTER auditor approval.
    p.locator('.p2-tabs [data-p2-tab="library"]').click()
    p.locator('.p2-toolbar').get_by_role('button',name='刷新真实登记状态').click()
    expect(p.locator('#p2TableTarget')).to_contain_text('已记录合成用途',timeout=20000)
    ready=p.locator('#p2TableTarget tbody tr').filter(has_text=source_id)
    expect(ready.locator('.p2-next-cell')).to_contain_text('准备结构化转换')
    ready.get_by_role('button',name='进入转换作业').click()
    expect(p.locator('.p2-tabs [data-p2-tab="convert"]')).to_have_attribute('aria-current','page')
    p.locator('.p2-tabs [data-p2-tab="library"]').click()
    p.locator('.p2-tabs [data-p2-tab="convert"]').click()
    expect(p.locator('.p2-table tbody tr').filter(has_text=source_id)).to_have_count(1)
    p.locator('.p2-table tbody tr').filter(has_text=source_id).get_by_role('button',name='开始结构化转换').click()
    expect(p.locator('.p2-studio')).to_contain_text('转换已提交并冻结结构化文档版本',timeout=20000)
    assert producer_context.request.get(url+'/v1/p2/sources/'+source_id+'/r1/original').status==403
    # Curator alone can compare ORIGINAL source to document IR and sign exact spans.
    c_ctx=browser.new_context(viewport={'width':1440,'height':900})
    c=c_ctx.new_page();c.on('pageerror',lambda e:errors.append('P2CURATOR: '+str(e)))
    c.goto(url+'/source-qa')
    c.locator('#p2Username').fill('p2curator')
    c.locator('#p2Password').fill(credentials['accounts']['p2curator']['password'])
    c.locator('#p2LoginForm button[type="submit"]').click()
    expect(c.locator('#workspace')).to_be_visible(timeout=30000)
    expect(c.locator('.p2-reader-select select')).to_be_visible(timeout=20000)
    c.locator('.p2-reader-select select').select_option(source_id+':r1')
    expect(c.locator('.p2-original-text')).to_contain_text('Synthetic scientific paper',timeout=20000)
    unit_count=c.locator('.p2-unit').count()
    assert unit_count>=4
    expect(c.locator('.p2-qa-progress')).to_contain_text('核验进度：0 / '+str(unit_count)+' Unit')
    c.locator('.p2-unit').first.click()
    c.locator('.p2-translation-entry textarea').fill('这是只用于浏览器验收的人工辅助译文。')
    c.get_by_role('button',name='保存辅助译文（不作为 Gold）').click()
    expect(c.locator('.p2-studio')).to_contain_text('辅助译文作为独立、不可变的非权威层保存',timeout=20000)
    assert c_ctx.request.get(url+'/v1/p2/sources/'+source_id+'/r1/translations').json()['count']==1
    for idx in range(unit_count):
        c.locator('.p2-unit').nth(idx).click()
        c.get_by_role('button',name='核查通过 · 冻结此 Unit').click()
        # Verify the newly committed server-side QA count, not a toast left
        # behind by a previous Unit's async write.
        expect(c.locator('.p2-studio')).to_contain_text('独立 QA 记录已持久化',timeout=20000)
        reviews=c_ctx.request.get(url+'/v1/p2/sources/'+source_id+'/r1/reviews').json()
        assert reviews['total']==idx+1,(idx,reviews)
        assert len({r['unit_id'] for r in reviews['reviews']})==idx+1
    assert c_ctx.request.get(url+'/v1/p2/sources/'+source_id+'/r1/reviews').json()['total']==unit_count
    expect(c.locator('.p2-qa-progress')).to_contain_text('核验进度：'+str(unit_count)+' / '+str(unit_count)+' Unit')
    c.screenshot(path=str(output/'p2-curator-raw-structured-qa.png'),full_page=True);c_ctx.close()
    p.locator('.p2-tabs [data-p2-tab="versions"]').click()
    p.locator('.p2-library-table tbody tr').filter(has_text=source_id).get_by_role('button',name='检查并冻结').click()
    expect(p.locator('.p2-studio')).to_contain_text('已冻结合成资料包',timeout=20000)
    assert producer_context.request.get(url+'/v1/p2/sources/'+source_id+'/r1').json()['status']=='PACKAGE_FROZEN'
    checks.append('p2_1_b_list_first_next_step_drawer_and_durable_qa_progress')
    checks.append('p2_1_cd_demo_origin_isolation_source_workflow_qa_context')
    checks.append('p2_1_visual_four_primary_work_areas_eight_column_queue_compact_chrome')
    checks.extend(['p2_html_fidelity_four_stage_four_intake_six_nav_and_six_example_rows','p2_synthetic_source_persisted_intake',
                   'p2_separate_rights_and_no_raw_auditor','p2_curator_original_sha_and_all_units',
                   'p2_immutable_package_freeze_no_expert_grant','p2_auxiliary_translation_has_independent_lineage'])
    p.screenshot(path=str(output/'p2-source-studio-producer-synthetic.png'),full_page=True)
    # V2-P0 exact existing persisted SourceVersion: no browser-local QA or
    # unverified lineage may be attached to the backend source.
    prior=producer_context.request.get(url+'/v1/p2/sources').json()['total']
    p.locator('[data-p11-route="studio-v2"]').click()
    expect(p.locator('#p2v2App')).to_be_visible(timeout=15000)
    expect(p.locator('#p2v2App .table')).to_contain_text(source_id,timeout=15000)
    expect(p.locator('#p2v2App .detail')).to_contain_text(source_id)
    p.locator('#p2v2App [data-page="qa"]').click()
    expect(p.locator('#p2v2App')).to_contain_text('V2 四个视觉演示 Unit 不属于此版本')
    expect(p.locator('#p2v2App .paper-viewport')).to_have_count(0)
    p.locator('#p2v2App [data-page="audit"]').click()
    expect(p.locator('#p2v2App .p2v2-live-banner')).to_contain_text('不是服务器审计回执')
    p.locator('#p2v2App [data-page="queue"]').click()
    p.locator('#p2v2App [data-act="openRegister"]').click()
    expect(p.locator('#p2v2Overlay [role="dialog"]')).to_be_visible()
    p.locator('#p2v2Overlay #newTitle').fill('Synthetic authored source provenance acceptance')
    p.locator('#p2v2Overlay [data-act="wizardNextModal"]').click()
    expect(p.locator('#p2v2Overlay #newRawContent')).to_be_visible()
    p.locator('#p2v2Overlay #newRawContent').fill(
        '# Synthetic authored record\\n\\nThis text was written solely for the synthetic browser check.')
    p.locator('#p2v2Overlay [data-act="wizardNextModal"]').click()
    p.locator('#p2v2Overlay [data-act="wizardNextModal"]').click()
    p.locator('#p2v2Overlay [data-act="submitRegister"]').click()
    expect(p.locator('#p2v2ToastHolder')).to_contain_text('已写入 P2',timeout=20000)
    assert producer_context.request.get(url+'/v1/p2/sources').json()['total']==prior+1
    expect(p.locator('#p2v2App .detail')).to_contain_text('待用途审核')
    checks.append('p2_v2_p0_only_backend_is_persisted_and_producer_raw_required')
    p.screenshot(path=str(output/'p2-v2-p0-persisted-producer-1440.png'),full_page=False)
    # V2.1-P1: complete a NEW source from the V2 UI with separate real
    # synthetic accounts. Legacy P2 coverage above must continue to pass.
    latest=producer_context.request.get(url+'/v1/p2/sources').json()['sources']
    newer=[item for item in latest if item['source_id']!=source_id]
    assert len(newer)==1,newer
    v2_id=newer[0]['source_id']
    expect(p.locator('#p2v2App .p2v2-lifecycle')).to_contain_text('来源生命周期',timeout=20000)
    assert producer_context.request.get(url+'/v1/p2/sources/'+v2_id+'/r1/original').status==403
    # Independent Auditor enters the SAME V2 work surface via /source-qa,
    # preserving the backend role and never using Manager/Producer privileges.
    a2ctx=browser.new_context(viewport={'width':1440,'height':950})
    a2=a2ctx.new_page()
    a2.on('pageerror',lambda e:errors.append('P2V2AUDITOR: '+str(e)))
    a2.goto(url+'/source-qa#/studio-v2?source='+v2_id+'&revision=r1')
    a2.locator('#p2Username').fill('auditor')
    a2.locator('#p2Password').fill(credentials['accounts']['auditor']['password'])
    a2.locator('#p2LoginForm button[type="submit"]').click()
    expect(a2.locator('#p2v2App')).to_be_visible(timeout=20000)
    expect(a2.locator('#v2Evidence')).to_be_visible(timeout=25000)
    assert a2ctx.request.get(url+'/v1/p2/sources/'+v2_id+'/r1/original').status==403
    a2.locator('#v2Evidence').fill('SYN-V2-INDEPENDENT-AUDIT')
    a2.locator('[data-act="v2Approve"]').click()
    expect(a2.locator('#p2v2App .p2v2-lifecycle')).to_contain_text('RIGHTS',timeout=20000)
    assert a2ctx.request.get(url+'/v1/p2/sources/'+v2_id+'/r1').json()['status']=='RIGHTS_ACCEPTED'
    a2.locator('#p2v2App [data-page="audit"]').click()
    expect(a2.locator('#p2v2App')).to_contain_text('Auditor 全局 Hash Chain',timeout=20000)
    expect(a2.locator('#p2v2App')).to_contain_text('VALID')
    a2.screenshot(path=str(output/'p2-v2-p1-auditor-rights-1440.png'),full_page=False)
    a2ctx.close()
    # Producer reads the actual approved revision and converts in V2.
    p.evaluate('window.p2SourceStudioV2.reload()')
    expect(p.locator('#p2v2App [data-act="v2Convert"]')).to_be_visible(timeout=20000)
    p.locator('#p2v2App [data-act="v2Convert"]').click()
    expect(p.locator('#p2v2App .p2v2-lifecycle')).to_contain_text('独立签署',timeout=20000)
    assert producer_context.request.get(url+'/v1/p2/sources/'+v2_id+'/r1').json()['status']=='QA_PENDING'
    # Independent Curator reads original and matching canonical IR in V2;
    # acceptance hashes/UTF-16 spans are calculated, not mock preview state.
    c2ctx=browser.new_context(viewport={'width':1440,'height':950})
    c2=c2ctx.new_page()
    c2.on('pageerror',lambda e:errors.append('P2V2CURATOR: '+str(e)))
    c2.goto(url+'/source-qa#/studio-v2?source='+v2_id+'&revision=r1')
    c2.locator('#p2Username').fill('p2curator')
    c2.locator('#p2Password').fill(credentials['accounts']['p2curator']['password'])
    c2.locator('#p2LoginForm button[type="submit"]').click()
    expect(c2.locator('#p2v2App .p2v2-server-reader')).to_be_visible(timeout=25000)
    expect(c2.locator('#p2v2App .p2v2-original')).to_contain_text('Synthetic authored record')
    actual_units=c2.locator('#p2v2App [data-v2unit]').count()
    assert actual_units>=2,actual_units
    c2.locator('#p2v2App #v2TranslateText').fill('独立 Curator 编写的仅供合成验收的辅助译文。')
    c2.locator('#p2v2App [data-act="v2Translate"]').click()
    expect(c2.locator('#p2v2App .translation-block')).to_contain_text('独立 Curator 编写',timeout=20000)
    for idx in range(actual_units):
        c2.locator('#p2v2App [data-v2unit]').nth(idx).click()
        expect(c2.locator('#p2v2App [data-act="v2Accept"]')).to_be_visible()
        c2.locator('#p2v2App [data-act="v2Accept"]').click()
        expect(c2.locator('#p2v2App .reader-meta')).to_contain_text(str(idx+1)+' / '+str(actual_units),timeout=25000)
        items=c2ctx.request.get(url+'/v1/p2/sources/'+v2_id+'/r1/reviews').json()
        assert items['total']==idx+1,items
    expect(c2.locator('#p2v2App .reader-meta')).to_contain_text(str(actual_units)+' / '+str(actual_units))
    c2.screenshot(path=str(output/'p2-v2-p1-curator-qa-1440.png'),full_page=False)
    c2ctx.close()
    # Producer can now freeze only the exact document SHA; refresh reloads
    # the server state instead of preserving a browser-local success flag.
    p.evaluate('window.p2SourceStudioV2.reload()')
    expect(p.locator('#p2v2App [data-act="v2Freeze"]')).to_be_enabled(timeout=25000)
    p.locator('#p2v2App [data-act="v2Freeze"]').click()
    expect(p.locator('#p2v2App .p2v2-lifecycle')).to_contain_text('SourcePackage 冻结',timeout=25000)
    frozen=producer_context.request.get(url+'/v1/p2/sources/'+v2_id+'/r1').json()
    assert frozen['status']=='PACKAGE_FROZEN' and frozen['package_sha256'],frozen
    assert frozen['expert_exposure_authorized'] is False
    checks.append('p2_v2_1_independent_auditor_producer_curator_qa_translation_freeze_exact_server_roundtrip')
    p.screenshot(path=str(output/'p2-v2-p1-frozen-source-1440.png'),full_page=False)
    p.locator('[data-p11-route="studio"]').click()
    checks.extend(['p2_studio_same_pr36_management_shell','p2_studio_metadata_only_source_preview',
                   'p2_four_step_wizard_synthetic_only_admission','p2_reader_mock_unit_qa_block',
                   'p2_original_b1_source_library_untouched'])
    p.locator('.p2-tabs [data-p2-tab="library"]').click()
    p.locator('.p2-heading').get_by_role('button',name='B1 合成来源引用 ↗').click()
    expect(p.locator('#b1PackageStatus')).to_contain_text('SPKG-SYN-RCT-001-R1')
    checks.extend(['b1_source_version_deeplink_survives_reload',
                   'b1_existing_fixture_validate_before_register',
                   'b1_immutable_package_persist_reload_and_exact_structure_index',
                   'b1_management_never_renders_source_original_text'])
    # P1.1-A: enter a persistent operational project and batch before drafting.
    # P0: V2 is an additional scoped route, not a replacement for original
    # management, B1, or the original scientific-source workbench.
    nav=p.locator('#p11Nav button[data-p11-route]')
    assert nav.count()==9
    assert nav.evaluate_all("(items)=>new Set(items.map(x=>x.dataset.p11Route)).size===9")
    expect(p.locator('#p11Nav [data-p11-route="sources"]')).to_be_hidden()
    expect(p.locator('#p11Nav [data-p11-route="studio"]')).to_be_visible()
    expect(p.locator('#p11Nav [data-p11-route="studio-v2"]')).to_be_visible()
    p.locator('[data-p11-route="tasks"]').click()
    p.locator('#p11ProjectsShortcut').click()
    p.get_by_role('button',name='新建项目').click()
    p.locator('#opsName').fill('Browser Synthetic Program')
    p.locator('#p11ModalOverlay button[type="submit"]').click()
    expect(p.locator('#p11ModalOverlay')).to_be_hidden(timeout=30000)
    p.get_by_role('button',name='在此项目新建批次').click()
    p.locator('#opsName').fill('Browser QA Batch')
    p.locator('#p11ModalOverlay button[type="submit"]').click()
    expect(p.locator('#p11ModalOverlay')).to_be_hidden(timeout=30000)
    assert p.evaluate('location.hash').startswith('#/projects?project=PRJ-SYN-'),p.url
    assert '&batch=BATCH-SYN-' in p.evaluate('location.hash'),p.url
    p.go_back()
    assert 'project=PRJ-SYN-' in p.evaluate('location.hash')
    assert 'batch=' not in p.evaluate('location.hash')
    p.go_forward()
    assert '&batch=BATCH-SYN-' in p.evaluate('location.hash')
    p.reload()
    expect(p.locator('#workspace')).to_be_visible(timeout=30000)
    expect(p.get_by_role('button',name='在此项目新建批次')).to_be_visible()
    p.locator('[data-p11-route="tasks"]').click()
    expect(p.locator('#p11SectionTitle')).to_have_text('任务中心')
    expect(p.locator('#p11NewTaskCta')).to_be_visible()
    p.locator('#p11NewTaskCta').click()
    expect(p.locator('#p11WizardPanel')).to_be_visible()
    expect(p.locator('#p11FormBatch')).not_to_have_value('')
    p.locator('#primarySource').select_option('RCT-001:r1')
    expect(p.locator('#sourceInfo')).to_contain_text('RANDOMIZED_TRIAL')
    expect(p.locator('#sourcesList .source-row')).to_have_count(7)
    p.locator('#primarySource').select_option('RCT-001:r1')
    p.locator('#extraSource').select_option('GUIDE-001:r1')
    expect(p.locator('#sourceInfo')).to_contain_text('SHA-256')
    expect(p.locator('#sourceInfo')).to_contain_text('GUIDE-001 / r1')
    assert len(re.findall(r'(?i)[0-9a-f]{64}',p.locator('#sourceInfo').text_content()))==2
    p.locator('#p11WizardNav .p11-wizard-step').nth(1).click()
    p.locator('#taskId').fill('TPA-SYN-BROWSER-001')
    p.locator('#workflowStrategy').select_option('AGENT_PROPOSE_EXPERT_VERIFY')
    p.locator('#createDraft').click()
    expect(p.locator('#receipt')).to_contain_text('"state": "DRAFT"',timeout=30000)
    expect(p.locator('#p11WizardPanel')).to_be_visible()
    row=p.locator('.task-row').filter(has_text='TPA-SYN-BROWSER-001')
    expect(p.locator('.p11-task-table')).to_be_visible()
    expect(p.locator('#p11WizardNav .p11-wizard-step')).to_have_count(5)
    expect(p.locator('#p11WizardInfo')).to_contain_text('检查资料与任务')
    expect(row).to_contain_text('DRAFT')
    # Demo keeps the five-step wizard open after draft; use in-wizard CTAs
    # because the modal overlay intercepts pointer events on table row buttons.
    p.locator('#p11WizardInfo').get_by_role('button',name=re.compile('检查资料与任务')).click()
    expect(row).to_contain_text('VALIDATED')
    p.locator('#p11WizardInfo').get_by_role('button',name=re.compile('冻结任务定义')).click()
    expect(row).to_contain_text('DEFINITION_FROZEN')
    p.locator('#p11WizardInfo').get_by_role('button',name=re.compile('准备工作包')).click()
    expect(row).to_contain_text('READY_FOR_ASSIGNMENT')
    expect(p.locator('#p11WizardInfo')).to_contain_text('工作包已准备')
    p.locator('#p11WizardClose').click()
    expect(p.locator('#p11WizardPanel')).to_be_hidden()
    # B2: check original EA frozen fixture proof. No true Agent invocation.
    p.locator('[data-p11-route="agent"]').click()
    expect(p.locator('#p11B2AgentPage')).to_be_visible(timeout=30000)
    expect(p.locator('#b2AgentTaskRows')).to_contain_text('TPA-SYN-BROWSER-001')
    expect(p.locator('#b2AgentDetail')).to_contain_text('FIXTURE_NOT_ATTESTED')
    p.locator('#b2InspectAgent').click()
    expect(p.locator('#b2Inspection')).to_contain_text('冻结事实已核对')
    assert 'SYNTHETIC_FIXTURE_NOT_AN_LLM' not in p.locator('#b2Inspection').text_content()
    assert 'A synthetic randomized trial compares' not in p.locator('#p11B2AgentPage').text_content()
    p.locator('#b2AttestAgent').click()
    expect(p.locator('#receipt')).to_contain_text('b2_attestation',timeout=30000)
    expect(p.locator('#b2AttestationReceipt')).to_contain_text('SYNTHETIC_FIXTURE_NOT_AN_LLM')
    expect(p.locator('#b2AttestationReceipt')).to_contain_text('候选集合 SHA-256')
    assert 'agent_task=TPA-SYN-BROWSER-001' in p.evaluate('location.hash')
    p.screenshot(path=str(output/'b2-agent-provenance-synthetic.png'),full_page=True)
    p.reload()
    expect(p.locator('#b2AttestationReceipt')).to_be_visible(timeout=30000)
    expect(p.locator('#b2AttestationReceipt')).to_contain_text('回执 SHA-256')
    checks.extend(['b2_existing_ea_fixture_inspection_without_llm',
                   'b2_immutable_agent_attestation_survives_reload',
                   'b2_origin_and_candidate_digest_producer_only'])
    p.locator('[data-p11-route="tasks"]').click()
    row=p.locator('.task-row').filter(has_text='TPA-SYN-BROWSER-001')
    row.get_by_role('button',name='查看任务详情').click()
    expect(p.locator('#p11Detail')).to_be_visible()
    assert 'task=TPA-SYN-BROWSER-001' in p.evaluate('location.hash')
    p.go_back()
    expect(p.locator('#p11Detail')).to_be_hidden()
    p.go_forward()
    expect(p.locator('#p11Detail')).to_be_visible()
    p.reload()
    expect(p.locator('#p11Detail')).to_be_visible(timeout=30000)
    p.locator('#p11Detail').get_by_role('button',name='关闭详情').click()
    expect(p.locator('#p11Detail')).to_be_hidden()
    p.locator('#p11TaskProject').select_option('')
    expect(p.locator('#p11LegacyToggle')).to_be_visible()
    p.locator('#p11LegacyToggle').click()
    expect(p.locator('.task-row').filter(has_text='TPA-SYN-BROWSER-001')).to_have_count(0)
    p.locator('#p11LegacyToggle').click()
    expect(p.locator('.task-row').filter(has_text='TPA-SYN-BROWSER-001')).to_have_count(1)
    checks.extend(['p11_explicit_legacy_filter_excludes_scoped_tasks',
                   'p11_task_detail_deeplink_back_forward_reload',
                   'p11_full_original_source_revision_digests_visible'])
    checks.extend(['tpa_same_origin_management_login','tpa_seven_synthetic_source_library',
                   'tpa_real_ui_draft_validation_freeze_prepare','tpa_agent_fixture_not_llm',
                   'p11_real_browser_create_project_batch_and_atomic_task',
                   'p11_url_project_batch_scope_backward_forward_reload'])
    manager_context,m=manager_login('manager')
    m.locator('[data-p11-route="studio"]').click()
    m.locator('.p2-heading').get_by_role('button',name='B1 合成来源引用 ↗').click()
    m.locator('#b1SourceRows .p11-source-entry').filter(has_text='RCT-001').get_by_role('button',name='查看版本').click()
    expect(m.locator('#b1PackageStatus')).to_contain_text('SYNTHETIC_REFERENCE_ONLY')
    assert m.locator('#b1ValidatePackage').count()==0
    assert m.locator('#b1RegisterPackage').count()==0
    checks.append('b1_manager_source_package_read_only')
    m.locator('[data-p11-route="studio"]').click()
    expect(m.locator('.p2-studio')).to_be_visible(timeout=15000)
    m.locator('.p2-tabs [data-p2-tab="qa"]').click()
    expect(m.locator('.p2-qa-grid')).to_have_count(0)
    expect(m.locator('.p2-studio')).to_contain_text('该账号仅可浏览来源元数据')
    checks.append('p2_manager_cannot_view_even_synthetic_qa_text')
    m.locator('[data-p11-route="agent"]').click()
    expect(m.locator('#b2AgentTaskRows')).to_contain_text('TPA-SYN-BROWSER-001')
    expect(m.locator('#b2AttestationReceipt')).to_contain_text('SYNTHETIC_FIXTURE_NOT_AN_LLM')
    assert '候选集合 SHA-256' not in m.locator('#b2AgentDetail').text_content()
    assert m.locator('#b2InspectAgent').count()==0
    assert m.locator('#b2AttestAgent').count()==0
    checks.append('b2_manager_read_only_with_candidate_digest_redacted')
    # B3: real browser checks that the only roster identities are fixed synthetic
    # accounts, and pre-publish handoff cannot create a grant.
    m.locator('[data-p11-route="experts"]').click()
    expect(m.locator('#p11B3ExpertPage')).to_be_visible(timeout=30000)
    expect(m.locator('#b3ExpertRoster')).to_contain_text('SYN-EA-EXPERT-A')
    expect(m.locator('#b3ExpertRoster')).to_contain_text('SYN-EA-EXPERT-B')
    expect(m.locator('#b3HandoffDetail')).to_contain_text('TPA-SYN-BROWSER-001')
    expect(m.locator('#b3HandoffDetail')).to_contain_text('READY_FOR_ASSIGNMENT')
    assert m.locator('#b3Attest').count()==0
    assert 'expert_task=TPA-SYN-BROWSER-001' in m.evaluate('location.hash')
    checks.extend(['b3_fixed_synthetic_roster_and_task_version_deeplink',
                   'b3_no_prepublish_handoff_grant'])
    m.locator('[data-p11-route="tasks"]').click()
    row=m.locator('.task-row').filter(has_text='TPA-SYN-BROWSER-001')
    expect(row).to_contain_text('READY_FOR_ASSIGNMENT')
    assert manager_context.request.get(url+'/v1/ea/tasks/TPA-SYN-BROWSER-001/sources/RCT-001/r1').status==403
    row.get_by_role('button',name=re.compile('分配合成专家')).click()
    expect(row).to_contain_text('ASSIGNED')
    # A5: the server commits a publish, but the browser receives a synthetic 502.
    # Client must reconcile via server state; a timeout is NOT proof of rollback.
    def lose_publish_reply(route):
        committed=route.fetch()
        assert committed.status==200
        route.fulfill(status=502,content_type='application/json',
                      body='{"detail":{"code":"SYNTHETIC_LOST_RESPONSE"}}')
    m.route('**/v1/tpa/tasks/TPA-SYN-BROWSER-001/publish',lose_publish_reply,times=1)
    row.get_by_role('button',name=re.compile('授权发布任务')).click()
    try:
        expect(row).to_contain_text('PUBLISHED',timeout=12000)
    except AssertionError:
        state=manager_context.request.get(url+'/v1/tpa/tasks/TPA-SYN-BROWSER-001/management')
        raise AssertionError('UNCONFIRMED_MANAGER_UI_AFTER_LOST_REPLY: server='+
          str(state.status)+'/'+state.text()+' receipt='+str(m.locator('#receipt').text_content())+
          ' browser_row='+str(row.text_content()))
    expect(m.locator('#receipt')).to_contain_text('reconciled_after_uncertain_response')
    assert m.locator('.p11-task-table').count()==1
    row.get_by_role('button',name='查看任务详情').click()
    expect(m.locator('#p11Detail')).to_contain_text('专家端安全交接')
    expect(m.locator('#p11Detail')).to_contain_text('ea1')
    expect(m.locator('#p11Detail')).to_contain_text('已发布 ≠ 已打开')
    assert len(re.findall(r'(?i)[0-9a-f]{64}',m.locator('#p11Detail').text_content()))==2
    m.locator('#p11Detail').get_by_role('button',name='关闭详情').click()
    checks.extend(['tpa_manager_no_original_source_read','tpa_expert_assignment_publish_via_UI',
                   'a5_server_committed_publish_lost_http_reply_reconciled',
                   'a5_published_handoff_safe_and_two_full_source_digests'])
    # B3: same ORIGINAL TPA publication must precede immutable handoff proof.
    m.locator('[data-p11-route="experts"]').click()
    expect(m.locator('#b3HandoffDetail')).to_contain_text('PUBLISHED')
    expect(m.locator('#b3ExposureStatus')).to_contain_text('原 TPA 记录的专家访问事件数：0')
    m.locator('#b3Attest').click()
    expect(m.locator('#receipt')).to_contain_text('b3_handoff',timeout=30000)
    expect(m.locator('#b3HandoffReceipt')).to_contain_text('SYNTHETIC_HANDOFF_ATTESTED')
    assert 'candidate_payload' not in m.locator('#b3HandoffReceipt').text_content()
    m.screenshot(path=str(output/'b3-expert-handoff-synthetic.png'),full_page=True)
    m.reload()
    expect(m.locator('#b3HandoffReceipt')).to_be_visible(timeout=30000)
    expect(m.locator('#b3ExposureStatus')).to_contain_text('专家访问事件数：0')
    checks.extend(['b3_immutable_synthetic_handoff_after_original_grant',
                   'b3_handoff_no_published_equals_read_inference',
                   'b3_manager_reload_persisted_receipt'])
    ea_context,ea=sign_in('ea1')
    expect(ea.locator('#eaTask')).to_contain_text('TPA-SYN-BROWSER-001')
    ea.locator('#eaTask').select_option('TPA-SYN-BROWSER-001')
    ea.locator('#eaLoad').click()
    expect(ea.locator('#eaProfile')).to_contain_text('2 个获授权来源版本')
    expect(ea.locator('#eaCandidates')).to_contain_text('SYNTHETIC')
    ea.locator('#eaSource').select_option('GUIDE-001:r1')
    expect(ea.locator('#units')).to_contain_text('fabricated guideline')
    checks.append('tpa_published_task_delivered_to_original_ea_reader')
    # Access telemetry comes from original EA events, never B3's render step.
    m.locator('[data-p11-route="tasks"]').click()
    m.locator('[data-p11-route="experts"]').click()
    expect(m.locator('#b3ExposureStatus')).not_to_contain_text('专家访问事件数：0')
    expect(m.locator('#b3ExposureStatus')).to_contain_text('暴露事件不是已阅读')
    checks.append('b3_original_ea_exposure_event_count_post_access')
    p.set_viewport_size({'width':1024,'height':768})
    p.evaluate('window.scrollTo(0,0)')
    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    p.screenshot(path=str(output/'p11-management-tablet.png'))
    p.locator('[data-p11-route="tasks"]').focus()
    assert p.evaluate("document.activeElement?.getAttribute('data-p11-route')")=='tasks'
    p.keyboard.press('Enter')
    expect(p.locator('#p11SectionTitle')).to_have_text('任务中心')
    p.locator('#p11ProjectsShortcut').focus()
    p.keyboard.press('Enter')
    expect(p.locator('#p11SectionTitle')).to_have_text('项目与批次')
    p.set_viewport_size({'width':390,'height':844})
    p.evaluate('window.scrollTo(0,0)')
    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    p.screenshot(path=str(output/'tpa-management-mobile.png'))
    p.set_viewport_size({'width':1440,'height':900})
    p.evaluate('window.scrollTo(0,0)')
    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    p.screenshot(path=str(output/'tpa-management-desktop.png'))
    p.evaluate("location.hash='#/tasks?project=%3Cimg%20src=x%20onerror=alert(1)%3E'")
    expect(p.locator('#p11SectionTitle')).to_have_text('任务中心')
    assert p.locator('img[src="x"]').count()==0
    assert p.evaluate("document.querySelector('#p11TaskProject')?.value")==''
    p.locator('#logoutButton').click()
    expect(p.locator('#loginScreen')).to_be_visible()
    assert p.locator('#p11Detail').is_hidden()
    p.locator('#username').fill('manager')
    p.locator('#password').fill(credentials['accounts']['manager']['password'])
    p.locator('#loginForm button').click()
    expect(p.locator('#workspace')).to_be_visible()
    expect(p.locator('#userBadge')).to_contain_text('manager')
    expect(p.locator('#taskForm')).to_be_hidden()
    checks.extend(['tpa_responsive_admin_desktop_mobile',
                   'p11_responsive_tablet_desktop_keyboard_navigation',
                   'p11_hash_allowlist_injection_denied',
                   'p11_same_tab_role_change_clears_private_ui'])
    ea_context.close();manager_context.close();producer_context.close()

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
        tpa_management_browser(browser,url,credentials,sign_in,checks,output,errors)
        browser.close()
    assert not errors,errors
    result={'status':'PASS','checks':checks,'page_errors':errors,'native_pdfjs':True,'browser':'Chromium',
            'browser_plugin':'NOT_AVAILABLE_REGULAR_PLAYWRIGHT','viewports':['1440x1000','1440x900','1024x768','390x844'],
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
