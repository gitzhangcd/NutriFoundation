"""Offline Chromium C1 smoke bridged into actual FastAPI TestClient (no mocked API)."""
from __future__ import annotations
import base64
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from server import BASE, make_app

OUT=BASE/'screenshots';OUT.mkdir(exist_ok=True)
client=TestClient(make_app(Path(tempfile.mkdtemp(prefix='c1_bridge_')),preload_fixture=True))


def call_api(path,method='GET',body=None):
    resp=client.request(method,path,json=body) if method not in ('GET','HEAD') else client.request(method,path)
    try: return {'status':resp.status_code,'data':resp.json()}
    except Exception: return {'status':resp.status_code,'data':{'error':'not-json'}}

FETCH=r"""window.fetch=async (url,opts={})=>{
  const p=typeof url==='string'?url:url.url;
  const body=opts.body?JSON.parse(opts.body):null;
  const response=await window.bridgeApi(p,opts.method||'GET',body);
  return new Response(JSON.stringify(response.data),{status:response.status,headers:{'content-type':'application/json'}});
};"""

SELECT=r"""(quote)=>{
  const para=[...document.querySelectorAll('.unit p')].find(n=>n.textContent.includes(quote));
  if(!para)return 'no paragraph';
  let all='',arr=[],node;const tw=document.createTreeWalker(para,NodeFilter.SHOW_TEXT);
  while((node=tw.nextNode())){arr.push({node,start:all.length,end:all.length+node.textContent.length});all+=node.textContent}
  const i=all.indexOf(quote);if(i<0)return 'not continuous';
  const start=arr.find(x=>x.start<=i&&x.end>i);
  const end=arr.find(x=>x.start<i+quote.length&&x.end>=i+quote.length);
  const r=document.createRange();r.setStart(start.node,i-start.start);r.setEnd(end.node,i+quote.length-end.start);
  const s=window.getSelection();s.removeAllRanges();s.addRange(r);
  return 'selected';
}"""


def run():
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  page=b.new_page(viewport={'width':1850,'height':1120},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.expose_function('bridgeApi',call_api)
  page.evaluate("() => {"+FETCH+"}")
  first_page=client.get('/reader/api/pdf/page/1/png?scale=1.28')
  assert first_page.status_code==200
  uri='data:image/png;base64,'+base64.b64encode(first_page.content).decode()
  page.evaluate("""(uri)=>{const Real=window.Image;window.Image=class extends Real{
    set src(v){super.src=String(v).startsWith('/reader/api/pdf/page/1/png')?uri:v}
    get src(){return super.src}
  }}""",uri)
  html=(BASE/'web/index.html').read_text(encoding='utf-8')
  html=html.replace('<link rel="stylesheet" href="/static/styles.css">','<style>'+(BASE/'web/styles.css').read_text()+'</style>')
  html=html.replace('<link rel="stylesheet" href="/static/c1.css">','<style>'+(BASE/'web/c1.css').read_text()+'</style>')
  html=html.replace('<script src="/static/pdf-reader.js"></script>','<script>'+(BASE/'web/pdf-reader.js').read_text()+'</script>')
  html=html.replace('<script type="module" src="/static/app.js"></script>','<script type="module">'+(BASE/'web/app.js').read_text()+'</script>')
  page.set_content(html,wait_until='load')
  page.wait_for_function("document.querySelector('#sourceStatus')?.textContent?.includes('154')",timeout=20000)
  assert page.locator('#stageList button').count()==5
  assert 'server rev' not in page.locator('#message').inner_text()
  assert page.locator('#pdfPanel').is_hidden()
  page.screenshot(path=str(OUT/'01-integrated-reader-judgment.png'),full_page=True)

  field=page.locator('[data-field="decision_focus"]')
  field.fill('合成示例：先核验资料可用性，不能推断个体治疗建议。')
  page.locator('#saveBtn').click()
  page.wait_for_function("document.querySelector('#saveState')?.textContent?.includes('rev 1')",timeout=10000)
  assert page.evaluate('window.getSelection().toString()')==''
  quote='Three hundred adults with obesity were randomised'
  assert page.evaluate(SELECT,quote)=='selected'
  page.locator('#makeAnchorBtn').click()
  page.wait_for_function("document.querySelector('#anchorCount')?.textContent==='1'",timeout=15000)
  page.locator('#bindField').select_option('decision_focus')
  page.locator('[data-bind]').first.click()
  page.locator('#saveBtn').click()
  page.wait_for_function("document.querySelector('#saveState')?.textContent?.includes('rev 2')",timeout=10000)
  recorded=client.get('/api/tasks/DEMO-R2-PREAI/draft').json()
  assert recorded['payload']['decision_focus'].startswith('合成示例')
  assert len(recorded['bindings']['decision_focus'])==1
  page.screenshot(path=str(OUT/'02-anchor-field-binding.png'),full_page=True)
  page.locator('[data-open-pdf]').first.click()
  page.wait_for_selector('.pdf-highlight',timeout=18000)
  assert page.locator('#pdfEngine').inner_text().find('离线降级')>=0
  assert page.locator('#pdfPage').input_value()=='1'
  page.screenshot(path=str(OUT/'03-pdf-bbox.png'),full_page=True)
  page.locator('.pdf-highlight').first.click()
  page.wait_for_selector('.unit.selected',timeout=12000)
  page.reload() if False else None
  page.locator('#reloadBtn').click()
  page.wait_for_function("document.querySelector('#saveState')?.textContent?.includes('rev 2')",timeout=10000)
  assert page.locator('[data-field="decision_focus"]').input_value().startswith('合成示例')
  assert page.locator('#anchorList').locator('[data-anchor]').count()==1
  page.locator('#taskSelector').select_option('DEMO-R0-NOAI')
  page.wait_for_function("document.querySelector('#saveState')?.textContent?.includes('版本 0')",timeout=8000)
  assert page.locator('[data-field="decision_focus"]').input_value()==''
  assert not errors,errors
  print('PASS_C1_BROWSER_BRIDGE_READER_DRAFT_ANCHOR_BBOX_REPLAY_RELOAD_R0_ISOLATION')
  page.wait_for_timeout(500)
  b.close()

if __name__=='__main__':run()