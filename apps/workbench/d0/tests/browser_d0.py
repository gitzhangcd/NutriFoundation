"""Native Chromium acceptance: real HTTP, PDF.js, role gates and roundtrip.

Default uses disposable local synthetic data. D0_URL + D0_CREDENTIALS can run
against a separately provisioned acceptance instance through an SSH tunnel.
Never point this destructive synthetic workflow test at the user workspace.
"""
from __future__ import annotations
import json
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
        r2.locator('#readerSource').select_option('paper')
        expect(r2.locator('#readerSource')).to_have_attribute('data-ready-source','paper',timeout=30000)
        expect(r2.locator('#units')).to_contain_text('randomised')
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
        r2.locator('#makeAnchor').click();expect(r2.locator('#status')).to_contain_text('已通过服务端证据验证并绑定',timeout=30000)
        expect(r2.locator('.pdf-highlight')).not_to_have_count(0,timeout=30000)
        expect(r2.locator('#pdfLocatorStatus')).to_contain_text('PDF_PAGE_BBOX/0.2')
        output.mkdir(parents=True,exist_ok=True);r2.locator('#evidencePane').evaluate('(el)=>{el.scrollTop=0}');r2.screenshot(path=str(output/'workbench-desktop.png'),full_page=False)
        r2.set_viewport_size({'width':390,'height':844});assert r2.evaluate('document.documentElement.scrollWidth <= window.innerWidth');r2.screenshot(path=str(output/'workbench-mobile.png'),full_page=False)
        r2.set_viewport_size({'width':1440,'height':1000})
        checks.append('anchor_bind_original_pdf_highlight')
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
        r2.locator('.rationale').fill('Synthetic reconciliation for engineering acceptance')
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
        expect(r1.locator('#saveStatus')).to_have_text('复核提交已锁定 · 合成工程记录')
        r1.reload();expect(r1.locator('#receipt')).to_contain_text('R1_verified')
        checks.extend(['R1_candidate_excerpt_only','R1_full_pdf_denied','R1_verification_reload'])
        r0ctx,r0=sign_in('r0');expect(r0.locator('#saveStatus')).to_have_text('已载入')
        assert r0ctx.request.get(url+'/v1/tasks/SYN-R0/candidate-set').status==403
        r0.locator('[id="f-decision_focus"]').fill('Synthetic R0 independent judgment only')
        r0.locator('#saveDraft').click();expect(r0.locator('#saveStatus')).to_have_text('已保存')
        r0.locator('#nextReview').click();r0.locator('#unexposed').check();r0.locator('#freeze').click();expect(r0.locator('#saveStatus')).to_have_text('已冻结 · 合成工程记录')
        r0.reload();expect(r0.locator('[id="f-decision_focus"]')).to_be_disabled()
        checks.extend(['R0_permanent_candidate_denial','R0_freeze_reload_immutable'])
        mgrctx,mgr=sign_in('manager');expect(mgr.locator('#readiness')).to_contain_text('NO-GO')
        expect(mgr.locator('#readiness')).to_contain_text('BLOCK_UPSTREAM_SCIENTIFIC_VERSION_CONFLICT')
        actx,auditor=sign_in('auditor');auditor.locator('#auditTask').select_option('SYN-R2');auditor.locator('#audit').click()
        expect(auditor.locator('#auditResult')).to_contain_text('FREEZE_J_postAI')
        r2.locator('#logout').click();expect(r2.locator('#loginPanel')).to_be_visible()
        assert r2ctx.request.get(url+'/v1/tasks').status==401
        checks.extend(['manager_NO_GO','auditor_integrity_chain','logout_revocation'])
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
