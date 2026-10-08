"""Real HTTP/Chromium and optionally native PDF.js page-level E2E.

CI sets C21_REQUIRE_NATIVE_PDFJS=1; local fallback is reported separately.
"""
from __future__ import annotations
import os, socket, sys, tempfile, threading, time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
import uvicorn

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'tests'))
from app import make_app
from conftest import fake_authority,ACTORS,screen
from fastapi.testclient import TestClient


def run():
    app=make_app(Path(tempfile.mkdtemp(prefix='c21_browser_')),test_authority=fake_authority(),actors=ACTORS)
    client=TestClient(app)
    keys={actor:token for token,(actor,_) in app.state.tokens.items()}
    for task,actor in [('SYN-R0','SYN-EXPERT-A'),('SYN-R1','SYN-EXPERT-B'),('SYN-R2','SYN-EXPERT-C')]:
        r=client.post(f'/v1/tasks/{task}/qualification',json=screen(actor),headers={'X-Workbench-Token':keys['SYN-ADMIN']});assert r.status_code==200,r.text
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    config=uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error',access_log=False)
    server=uvicorn.Server(config)
    worker=threading.Thread(target=server.run,daemon=True);worker.start()
    base=f'http://127.0.0.1:{port}'
    try:
        for _ in range(80):
            try:
                if urlopen(base+'/health',timeout=.5).status==200:break
            except Exception:time.sleep(.15)
        else:raise RuntimeError('HTTP SERVER NOT READY')
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True,executable_path='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1620,'height':950})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base,wait_until='load')
            page.locator('#token').fill(keys['SYN-EXPERT-C'])
            page.locator('#task').select_option('SYN-R2')
            page.locator('#load').click()
            page.wait_for_function("document.querySelector('#sourceBadge')?.textContent?.includes('154')",timeout=40000)
            page.wait_for_function("document.querySelector('#pdfEngine')?.textContent?.includes('PDF.js') || document.querySelector('#pdfEngine')?.textContent?.includes('页图')",timeout=40000)
            if os.getenv('C21_REQUIRE_NATIVE_PDFJS')=='1':
                assert page.locator('#pdfEngine').inner_text().startswith('PDF.js'),page.locator('#status').inner_text()
                assert page.locator('#pdfCanvas').evaluate('(e)=>e.width>500&&e.height>500')
            assert page.locator('.unit').count()==154
            assert page.context.request.get(base+'/v1/tasks/SYN-R2/sources/SYN-5-2-PAPER/original.pdf').status==401
            # Select exact quote from structured reader using DOM Range.
            quote='Three hundred adults with obesity were randomised'
            result=page.evaluate('''(q)=>{const d=[...document.querySelectorAll('.unit')].find(e=>e.textContent.includes(q));let t=d.firstChild,pos=t.textContent.indexOf(q),r=document.createRange();r.setStart(t,pos);r.setEnd(t,pos+q.length);getSelection().removeAllRanges();getSelection().addRange(r);d.dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));return document.querySelector('#quote').value}''',quote)
            assert result==quote,result
            page.locator('#makeAnchor').click()
            page.wait_for_function("document.querySelectorAll('.anchor').length===1",timeout=20000)
            page.wait_for_selector('.pdf-highlight',timeout=20000)
            page.locator('.pdf-highlight').first.click()
            page.wait_for_selector('.unit.selected',timeout=15000)
            out=BASE/'screenshots';out.mkdir(exist_ok=True)
            page.screenshot(path=str(out/'01-task-scoped-anchor-bbox.png'),full_page=True)
            # R1 before candidates must not return documents or even search hits.
            page.locator('#task').select_option('SYN-R1');page.locator('#token').fill(keys['SYN-EXPERT-B']);page.locator('#load').click()
            page.wait_for_function("document.querySelector('#phase')?.textContent==='WAIT_AGENT_FREEZE'",timeout=15000)
            assert page.locator('.unit').count()==0
            page.screenshot(path=str(out/'02-r1-source-hold.png'),full_page=True)
            page.locator('#task').select_option('SYN-R0');page.locator('#token').fill(keys['SYN-EXPERT-A']);page.locator('#load').click()
            page.wait_for_function("document.querySelector('#sourceBadge')?.textContent?.includes('154')",timeout=15000)
            page.locator('#candidate').click()
            page.wait_for_function("document.querySelector('#status')?.textContent?.includes('CANDIDATE DENIED')",timeout=15000)
            assert not errors,errors
            print('C21_SECURE_READER_CHROMIUM PASS; native_pdfjs='+str(bool('PDF.js' in page.locator('#pdfEngine').inner_text())))
            browser.close()
    finally:
        server.should_exit=True;worker.join(timeout=5)

if __name__=='__main__':run()
