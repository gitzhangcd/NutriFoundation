"""True Chromium under strict CSP. Real authority on full CI checkout, mock only locally."""
from __future__ import annotations
import base64
import threading
import time
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[4]
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
import app as main

TEST_TOKEN='SYNTHETIC-C2-2-ADMIN-TOKEN-00000'

def build_app():
    if not (ROOT/'runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json').exists():
        # Mark local browser fixture explicitly. GitHub CI MUST use pinned originals.
        main.assess=lambda root:{'source_count':6,'bounded_projection_contract':'PASS',
          'case_projection_binding':{'referenced_case_ref':'D2-NHANES-L-0001:r2','target_workpack_case_ref':'D2-NHANES-L-0001:r3',
           'decision':'BLOCK_REQUIRES_SCIENTIFIC_OWNER_RECONCILIATION'},
          'external_requirements':[{'gate':f'SYNTHETIC-BLOCKER-{i}','requirement':'Test requirement',
                                    'status':'PENDING_INDEPENDENT_EVIDENCE'} for i in range(8)],
          'real_person_ux_pilot':'NO_GO_PENDING','formal_NDS_R1_experiment':'NO_GO_PENDING'}
    return main.make_app(ROOT,TEST_TOKEN)

def main_test():
    server_app=build_app()
    api=TestClient(server_app)
    official=(ROOT/'runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json').exists()
    errors=[]
    service=None
    if official:
        import uvicorn
        service=uvicorn.Server(uvicorn.Config(server_app,host='127.0.0.1',port=8792,log_level='error'))
        t=threading.Thread(target=service.run,daemon=True);t.start()
        for _ in range(100):
            if service.started:break
            time.sleep(.1)
        if not service.started:raise RuntimeError('TEST_SERVER_START_FAILED')
    with sync_playwright() as p:
        binary='/usr/bin/chromium'
        browser=p.chromium.launch(headless=True,executable_path=binary if Path(binary).exists() else None,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':920},device_scale_factor=1)
        page.on('pageerror',lambda exc:errors.append(str(exc)))
        if official:
            # CI exercises real authenticated HTTP + strict CSP, not a fake route.
            page.goto('http://127.0.0.1:8792/',wait_until='load')
        else:
            # Isolated container blocks browser loopback even with route mock.
            # Bridge TestClient without relaxing the production HTTP CSP policy.
            def bridge(url,opts):
                resp=api.request(opts.get('method','GET'),url,headers=opts.get('headers') or {},content=opts.get('body'))
                return {'status':resp.status_code,'body':base64.b64encode(resp.content).decode(),
                        'content_type':resp.headers.get('content-type','application/json')}
            page.expose_function('bridgeApi',bridge)
            markup=(APP/'web/index.html').read_text().replace('<link rel="stylesheet" href="/static/style.css">','').replace('<script src="/static/app.js" defer></script>','')
            page.set_content(markup,wait_until='load')
            page.add_style_tag(content=(APP/'web/style.css').read_text())
            page.evaluate("""window.fetch=async (url,opts={})=>{let x=await window.bridgeApi(String(url),opts);let raw=Uint8Array.from(atob(x.body),c=>c.charCodeAt(0));return new Response(raw,{status:x.status,headers:{'content-type':x.content_type}})}""")
            page.add_script_tag(content=(APP/'web/app.js').read_text())
        assert '准入评估' in page.title() or '真人试测' in page.title()
        assert page.locator('#sourceCount').inner_text()=='—'
        page.locator('#run').click()
        expect(page.locator('#notice')).to_contain_text('请输入本地合成管理员令牌')
        page.locator('#token').fill('BAD-TEST-TOKEN')
        page.locator('#run').click()
        expect(page.locator('#notice')).to_contain_text('401',timeout=8000)
        page.locator('#token').fill(TEST_TOKEN)
        page.locator('#run').click()
        expect(page.locator('#sourceCount')).to_have_text('6',timeout=15000)
        expect(page.locator('.gate-row')).to_have_count(8)
        expect(page.locator('#pilotStatus')).to_have_text('NO GO')
        expect(page.locator('#caseConflict')).to_contain_text('r2 vs D2-NHANES-L-0001:r3')
        assert not errors,errors
        out=APP/'screenshots';out.mkdir(exist_ok=True)
        page.screenshot(path=str(out/'01-real-expert-readiness-NO_GO.png'),full_page=True)
        print('C22_READINESS_CHROMIUM_PASS authority='+('OFFICIAL_PINNED' if official else 'SYNTHETIC_LOCAL')+' no_js_errors=0')
        browser.close()
    if service:service.should_exit=True
if __name__=='__main__':main_test()
