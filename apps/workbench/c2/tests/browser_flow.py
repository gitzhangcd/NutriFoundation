"""Chromium UI smoke through real FastAPI TestClient, synthetic-only."""
from __future__ import annotations
import json,sys,tempfile
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from conftest import fake_authority,ACTORS,screen
from app import make_app

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'screenshots'
OUT.mkdir(exist_ok=True)
app=make_app(Path(tempfile.mkdtemp(prefix='wb_c2_browser_')),test_authority=fake_authority(),actors=ACTORS)
keys={name:key for key,(name,_) in app.state.tokens.items()}
client=TestClient(app)
admin={'X-Workbench-Token':keys['SYN-ADMIN']}
for task,who in [('SYN-R0','SYN-EXPERT-A'),('SYN-R1','SYN-EXPERT-B'),('SYN-R2','SYN-EXPERT-C')]:
    r=client.post(f'/v1/tasks/{task}/qualification',headers=admin,json=screen(who))
    if r.status_code !=200 and r.status_code!=409:raise RuntimeError(r.text)

def bridge_api(path,opts):
    method=opts.get('method','GET')
    headers=opts.get('headers',{})
    raw=opts.get('body')
    r=client.request(method,path,headers=headers,content=raw.encode() if raw else None)
    try:data=r.json()
    except ValueError:data={'error':'not-json'}
    return {'status':r.status_code,'data':data}

FETCH_JS=r"""window.fetch=async (url,opts={})=>{
 const answer=await window.bridgeApi(url,opts);
 return new Response(JSON.stringify(answer.data),{status:answer.status,headers:{'content-type':'application/json'}})
}"""

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1365,'height':900},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
    page.expose_function('bridgeApi',bridge_api)
    page.evaluate('() => {' + FETCH_JS + '}')
    page.set_content((BASE/'web/index.html').read_text(encoding='utf-8'),wait_until='load')
    page.locator('#task').select_option('SYN-R2')
    page.locator('#token').fill(keys['SYN-EXPERT-C'])
    page.locator('#candidate').click()
    page.get_by_text('拒绝访问').wait_for()
    assert 'TASK_NOT_READY' in page.locator('#result').inner_text() or 'R2_PREAI_FREEZE_REQUIRED' in page.locator('#result').inner_text(), page.locator('#result').inner_text()
    page.locator('#load').click()
    page.get_by_text('PRE_AI',exact=True).wait_for()
    value=page.locator('#result').inner_text()
    assert 'candidate_set' not in value and 'scientific_sources' in value
    page.screenshot(path=str(OUT/'01-r2-preai-server-guard.png'),full_page=True)
    page.locator('#task').select_option('SYN-R1')
    page.locator('#token').fill(keys['SYN-EXPERT-B'])
    page.locator('#load').click()
    page.get_by_text('WAIT_AGENT_FREEZE',exact=True).wait_for()
    assert 'candidate_set' not in page.locator('#result').inner_text()
    page.screenshot(path=str(OUT/'02-r1-awaiting-agent.png'),full_page=True)
    page.locator('#task').select_option('SYN-R0')
    page.locator('#token').fill(keys['SYN-EXPERT-A'])
    page.locator('#candidate').click()
    page.get_by_text('拒绝访问').wait_for()
    assert page.locator('#result').inner_text().find('FORBIDDEN')>=0 or page.locator('#result').inner_text().find('TASK_NOT_READY')>=0
    assert not errors,errors
    print('CHROMIUM_C2_SYNTHETIC_POLICY_SMOKE: PASS | R2 PRE-AI guard | R1 hold | R0 never-agent | JS errors=0')
    browser.close()