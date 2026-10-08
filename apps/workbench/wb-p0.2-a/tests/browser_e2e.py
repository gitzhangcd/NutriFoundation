"""Chromium UI smoke with real FastAPI TestClient bridge (no local HTTP access in browser)."""
import base64
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from wb_a import make_app

PACKAGE = Path(__file__).resolve().parents[1] / 'fixtures' / '5_2_diet.AnnotationSourcePackage.v0.1.zip'
OUT = Path(__file__).resolve().parents[1] / 'screenshots'
OUT.mkdir(exist_ok=True)
client=TestClient(make_app(Path(tempfile.mkdtemp(prefix='wb_browser_'))))

def call_api(path, method='GET', payload=None):
    if method=='POST' and path=='/api/import':
        data=base64.b64decode(payload['data'])
        result=client.post(path,files={'file':('source.zip', data,'application/zip')})
    elif method=='POST':
        result=client.post(path,json=payload)
    else:
        result=client.get(path)
    try: body=result.json()
    except Exception: body={'error':'NON_JSON'}
    return {'status':result.status_code, 'data':body}

JS_FETCH = r"""
window.fetch = async (url, opts={}) => {
  let payload=null;
  if(opts.body instanceof FormData){
     const file=opts.body.get('file');
     const arr=new Uint8Array(await file.arrayBuffer());
     const chunks=[];for(let i=0;i<arr.length;i+=8192)chunks.push(String.fromCharCode(...arr.slice(i,i+8192)));
     payload={data:btoa(chunks.join(''))};
  } else if(opts.body) payload=JSON.parse(opts.body);
  const result=await window.bridgeApi(url, opts.method||'GET', payload);
  return new Response(JSON.stringify(result.data), {status:result.status, headers:{'content-type':'application/json'}});
};
"""

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1620,'height':1000},device_scale_factor=1,accept_downloads=True)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.expose_function('bridgeApi',call_api)
    page.evaluate('() => { '+JS_FETCH+'; }')
    page.set_content((Path(__file__).resolve().parents[1]/'web'/'index.html').read_text(),wait_until='load')
    page.get_by_role('button',name='导入来源包').click()
    page.locator('#upload').set_input_files(PACKAGE)
    page.get_by_role('button',name='校验并导入').click()
    page.locator('#unitCount').get_by_text('154').wait_for(timeout=20000)
    page.screenshot(path=str(OUT/'01-structured-reader.png'),full_page=True)
    doc=page.evaluate('doc')
    unit=next(x for x in doc['units'] if 'Three hundred adults with obesity were randomised' in x['raw'])
    page.locator('#unit-'+unit['unit_id']).scroll_into_view_if_needed()
    page.evaluate("""(id) => {
      const el=document.querySelector('#unit-'+id+' p');
      const n=el.firstChild;
      const r=document.createRange();r.setStart(n,0);r.setEnd(n,'Three hundred adults with obesity were randomised'.length);
      const s=window.getSelection();s.removeAllRanges();s.addRange(r);
      el.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,clientX:650,clientY:400}));
    }""",unit['unit_id'])
    page.get_by_role('button',name='绑定 SourceAnchor').click()
    page.locator('#anchorCount').get_by_text('1').wait_for(timeout=10000)
    page.screenshot(path=str(OUT/'02-source-anchor-saved.png'),full_page=True)
    page.get_by_role('button',name='查看原始 PDF ↗').click()
    assert page.locator('body').evaluate('(el)=>el.classList.contains("pdf-mode")')
    assert page.locator('#pdfFrame').get_attribute('src')=='/api/original.pdf#page=1&zoom=100'
    # A second browser session can recover backend state; browser network policy prevents rendering PDF plugin itself.
    assert len(client.get('/api/anchors').json())==1
    assert not errors,errors
    print('BROWSER_BRIDGED_PASS: ZIP upload, 154 units, selection->API anchor, page-level PDF locator, persistence, zero JS exceptions')
    print('SCREENSHOTS:',*[str(x) for x in sorted(OUT.glob('*.png'))])
    browser.close()