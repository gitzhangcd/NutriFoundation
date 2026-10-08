"""Actual Chromium interactive smoke, deterministic offline FastAPI bridge.

The local browser network is restricted. Playwright intercepts ALL same-origin
requests and forwards them to FastAPI's real TestClient. This tests actual JS,
DOM, canvas/raster viewer and source interactions without faking API responses.
"""
from __future__ import annotations
import tempfile
from pathlib import Path
import base64
import json

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from wb_a import make_app

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'fixtures/5_2_diet.AnnotationSourcePackage.v0.1.zip'
OUT=ROOT/'screenshots';OUT.mkdir(exist_ok=True)
api=TestClient(make_app(Path(tempfile.mkdtemp(prefix='wb_b_e2e_'))))


def call_api(path, method='GET', payload=None):
    if method.upper()=='POST' and path=='/api/import':
        result=api.post(path,files={'file':('source.zip',base64.b64decode(payload['data']),'application/zip')})
    elif method.upper()=='POST':
        result=api.post(path,json=payload)
    else:
        result=api.get(path)
    return {'status':result.status_code,'data':result.json()}

JS_FETCH = r"""
window.fetch = async (url, opts={}) => {
  let payload=null;
  if(opts.body instanceof FormData){
    const f=opts.body.get('file');const ar=new Uint8Array(await f.arrayBuffer());
    const chunks=[];for(let i=0;i<ar.length;i+=8192)chunks.push(String.fromCharCode(...ar.slice(i,i+8192)));
    payload={data:btoa(chunks.join(''))};
  } else if(opts.body) payload=JSON.parse(opts.body);
  let r=await window.bridgeApi(url,opts.method||'GET',payload);
  return new Response(JSON.stringify(r.data),{status:r.status,headers:{'content-type':'application/json'}});
};
"""


def select_phrase(page,phrase):
    return page.evaluate("""(quote) => {
      const match = [...document.querySelectorAll('.unit p')].find(x=>x.textContent.includes(quote));
      if(!match) return 'paragraph missing';
      const nodes=[];let node;const tw=document.createTreeWalker(match,NodeFilter.SHOW_TEXT);
      while((node=tw.nextNode()))nodes.push(node);
      const full=nodes.map(x=>x.textContent).join('');
      const start=full.indexOf(quote);
      if(start<0)return 'span missing';
      let sum=0,first=null,last=null;
      for (const n of nodes) {
        if(!first&&sum+n.length>start) first=[n,start-sum];
        if(!last&&sum+n.length>=start+quote.length) last=[n,start+quote.length-sum];
        sum+=n.length;
      }
      if(!first||!last)return 'range failure';
      const r=document.createRange();r.setStart(first[0],first[1]);r.setEnd(last[0],last[1]);
      const s=window.getSelection();s.removeAllRanges();s.addRange(r);
      match.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,clientX:680,clientY:380}));
      return 'selected';
    }""",phrase)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1860,'height':1080},device_scale_factor=1)
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.expose_function('bridgeApi',call_api)
    assert api.post('/api/import',files={'file':('paper.zip',PACKAGE.read_bytes(),'application/zip')}).status_code==200
    png=api.get('/api/pdf/page/1/png?scale=1.28')
    assert png.content.startswith(b'\x89PNG'),png.status_code
    png_uri='data:image/png;base64,'+base64.b64encode(png.content).decode()
    page.evaluate('() => {'+JS_FETCH+'}')
    page.evaluate("""(uri) => {
      const OriginalImage=window.Image;
      window.Image=class extends OriginalImage {
        set src(value){super.src=(String(value).startsWith('/api/pdf/page/1/png'))?uri:value}
        get src(){return super.src}
      };
    }""",png_uri)
    html=(ROOT/'web'/'index.html').read_text().replace('<script src="/static/pdf-reader.js"></script>',
          '<script>\n'+(ROOT/'web'/'pdf-reader.js').read_text()+'\n</script>')
    page.set_content(html,wait_until='load')
    page.get_by_role('button',name='导入来源包').click()
    page.locator('#upload').set_input_files(PACKAGE)
    page.get_by_role('button',name='校验并导入').click()
    page.wait_for_function("document.querySelector('#unitCount')?.textContent==='154'",timeout=15000)
    page.wait_for_function("document.querySelector('#pdfEngine')?.textContent?.includes('离线降级')",timeout=20000)
    page.screenshot(path=str(OUT/'01-reader-b.png'),full_page=True)
    assert select_phrase(page,'Three hundred adults with obesity were randomised')=='selected'
    page.get_by_role('button',name='绑定 SourceAnchor').click()
    page.wait_for_function("document.querySelector('#anchorCount')?.textContent==='1'",timeout=8000)
    page.get_by_role('button',name='定位 PDF ↗').click()
    page.wait_for_timeout(2000)
    print('PDF DEBUG',page.locator('#pdfLocatorStatus').inner_text(), page.locator('#pdfEngine').inner_text(),page.locator('#toast').inner_text(),page.locator('#pdfOverlay').inner_html()[:100],errors)
    page.wait_for_selector('.pdf-highlight',timeout=9000)
    page.wait_for_function("document.querySelector('#pdfLocatorStatus')?.textContent?.includes('已验证原始 PDF')",timeout=15000)
    source=page.locator('#pdfRaster')
    assert source.evaluate('(x)=>x.naturalWidth')>400
    rects=page.locator('.pdf-highlight')
    assert rects.count()==1
    assert rects.first.evaluate('(el)=>el.getBoundingClientRect().width')>100
    page.screenshot(path=str(OUT/'02-verified-pdf-bbox.png'),full_page=True)
    rects.first.click()
    page.wait_for_function("document.querySelector('#unitCount')?.textContent==='154'",timeout=8000)
    page.wait_for_selector('.unit.focused',timeout=4000)
    assert page.locator('.unit.focused').count()==1
    assert page.evaluate("Boolean(CSS.highlights && CSS.highlights.has('source-anchor'))")
    page.screenshot(path=str(OUT/'03-bidirectional-replay.png'),full_page=True)
    result={'unit_count':page.locator('#unitCount').inner_text(),'anchor_count':page.locator('#anchorCount').inner_text(),
            'pdf_engine':page.locator('#pdfEngine').inner_text(),'pdf_bbox_count':rects.count(),
            'pdf_page':page.locator('#pdfPage').input_value(),'errors':errors}
    print('BROWSER RESULT',result)
    if errors:raise AssertionError('Browser JS errors: '+str(errors))
    browser.close()