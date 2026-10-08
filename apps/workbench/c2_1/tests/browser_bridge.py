"""Local constrained Chromium check: real FastAPI TestClient route bridge.

This checks UI & source gates with genuine API responses but does NOT claim
native PDF.js due lack of local npm assets; remote CI runs browser_secure.py.
"""
from __future__ import annotations
import sys,tempfile
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'tests'))
from app import make_app
from conftest import fake_authority,ACTORS,screen

app=make_app(Path(tempfile.mkdtemp(prefix='wb_c21_bridge_')),test_authority=fake_authority(),actors=ACTORS)
client=TestClient(app)
keys={name:key for key,(name,_) in app.state.tokens.items()}
for task,name in [('SYN-R0','SYN-EXPERT-A'),('SYN-R1','SYN-EXPERT-B'),('SYN-R2','SYN-EXPERT-C')]:
    r=client.post(f'/v1/tasks/{task}/qualification',headers={'X-Workbench-Token':keys['SYN-ADMIN']},json=screen(name))
    assert r.status_code==200,r.text

import base64

def bridge(url, opts):
    path=urlparse(url).path
    if urlparse(url).query:path+='?'+urlparse(url).query
    response=client.request(opts.get('method','GET'),path,headers=opts.get('headers') or {},content=opts.get('body'))
    return {'status':response.status_code,'body':base64.b64encode(response.content).decode(),
            'content_type':response.headers.get('content-type','application/octet-stream')}

FETCH_BRIDGE = r"""window.fetch=async (url,opts={})=>{
  const x=await window.bridgeApi(String(url),opts);
  const raw=Uint8Array.from(atob(x.body),c=>c.charCodeAt(0));
  return new Response(raw,{status:x.status,headers:{'content-type':x.content_type}});
}"""

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1620,'height':950})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.expose_function('bridgeApi',bridge)
    markup=(BASE/'web/index.html').read_text().replace('<script type="module" src="/static/app.js"></script>','').replace('<link rel="stylesheet" href="/static/app.css">','')
    page.set_content(markup,wait_until='load')
    page.add_style_tag(content=(BASE/'web/app.css').read_text())
    page.evaluate(FETCH_BRIDGE)
    page.add_script_tag(content=(BASE/'web/app.js').read_text())
    page.locator('#token').fill(keys['SYN-EXPERT-C'])
    page.locator('#task').select_option('SYN-R2')
    page.locator('#load').click()
    page.wait_for_function("document.querySelector('#sourceBadge')?.textContent?.includes('154')",timeout=20000)
    page.wait_for_function("document.querySelector('#pdfEngine')?.textContent?.includes('页图')",timeout=30000)
    assert page.locator('.unit').count()==154
    quote='Three hundred adults with obesity were randomised'
    r=page.evaluate('''(q)=>{const d=[...document.querySelectorAll('.unit')].find(e=>e.textContent.includes(q));const t=d.firstChild,i=t.textContent.indexOf(q),r=document.createRange();r.setStart(t,i);r.setEnd(t,i+q.length);getSelection().removeAllRanges();getSelection().addRange(r);d.dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));return document.querySelector('#quote').value}''',quote)
    assert r==quote
    page.locator('#makeAnchor').click()
    page.wait_for_function("document.querySelectorAll('.anchor').length===1",timeout=15000)
    page.wait_for_selector('.pdf-highlight',timeout=15000)
    page.locator('.pdf-highlight').first.click()
    page.wait_for_selector('.unit.selected',timeout=15000)
    OUT=BASE/'screenshots';OUT.mkdir(exist_ok=True)
    page.screenshot(path=str(OUT/'01-task-scoped-anchor-bbox-local-raster.png'),full_page=True)
    page.locator('#task').select_option('SYN-R1');page.locator('#token').fill(keys['SYN-EXPERT-B']);page.locator('#load').click()
    page.wait_for_function("document.querySelector('#phase')?.textContent==='WAIT_AGENT_FREEZE'",timeout=20000)
    assert page.locator('.unit').count()==0
    page.screenshot(path=str(OUT/'02-r1-locked-no-source-local.png'),full_page=True)
    page.locator('#task').select_option('SYN-R0');page.locator('#token').fill(keys['SYN-EXPERT-A']);page.locator('#load').click()
    page.wait_for_function("document.querySelector('#sourceBadge')?.textContent?.includes('154')",timeout=20000)
    page.locator('#candidate').click()
    page.wait_for_function("document.querySelector('#status')?.textContent?.includes('CANDIDATE DENIED')",timeout=10000)
    assert not errors,errors
    print('C21_BRIDGED_CHROMIUM PASS | authenticated source, R1 hold, R0 never-Agent, bbox | errors=0')
    browser.close()
