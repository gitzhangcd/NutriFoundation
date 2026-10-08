"""True PDF.js integration E2E. Needs vendor assets installed and local HTTP allowed.

Unlike browser_e2e.py (offline raster fallback), this test rejects fallback.
Run after: bash scripts/install_pdfjs.sh
"""
from __future__ import annotations
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'web/vendor/pdfjs/pdf.min.mjs'
if not ASSETS.is_file():
    raise RuntimeError('PDFJS_ASSETS_MISSING: run bash scripts/install_pdfjs.sh')

s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
url=f'http://127.0.0.1:{port}'
cmd=[sys.executable,str(ROOT/'wb_a.py'),'serve','--root',tempfile.mkdtemp(prefix='wb_native_pdfjs_'),
     '--host','127.0.0.1','--port',str(port)]
server=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
try:
    for _ in range(100):
        try:
            if urlopen(url+'/api/health',timeout=0.5).status==200:break
        except Exception: time.sleep(0.2)
    else:raise RuntimeError('SERVER_NOT_READY')
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1900,'height':1100})
        errors=[];page.on('pageerror',lambda x:errors.append(str(x)))
        page.goto(url,wait_until='load')
        page.get_by_role('button',name='导入来源包').click()
        page.locator('#upload').set_input_files(ROOT/'fixtures/5_2_diet.AnnotationSourcePackage.v0.1.zip')
        page.get_by_role('button',name='校验并导入').click()
        page.wait_for_function("document.querySelector('#unitCount')?.textContent==='154'",timeout=20000)
        page.wait_for_function("document.querySelector('#pdfEngine')?.textContent?.startsWith('PDF.js')",timeout=35000)
        page.evaluate("""() => {
          const el=[...document.querySelectorAll('.unit p')].find(x=>x.textContent.includes('Three hundred adults with obesity were randomised'));
          const q='Three hundred adults with obesity were randomised';
          const tw=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n;let items=[];let sum=0;
          while((n=tw.nextNode())){items.push({node:n,begin:sum,end:sum+n.textContent.length});sum+=n.textContent.length}
          const all=items.map(x=>x.node.textContent).join('');const i=all.indexOf(q);
          if(i<0)throw new Error('Quote not visible in document');
          const begin=items.find(x=>x.begin<=i&&x.end>i);
          const end=items.find(x=>x.begin<i+q.length&&x.end>=i+q.length);
          const r=document.createRange();r.setStart(begin.node,i-begin.begin);r.setEnd(end.node,i+q.length-end.begin);
          window.getSelection().removeAllRanges();window.getSelection().addRange(r);
          el.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,clientX:680,clientY:400}));
        }""")
        page.get_by_role('button',name='绑定 SourceAnchor').click()
        page.wait_for_function("document.querySelector('#anchorCount')?.textContent==='1'",timeout=8000)
        page.get_by_role('button',name='定位 PDF ↗').click()
        page.wait_for_selector('.pdf-highlight',timeout=20000)
        assert page.locator('#pdfEngine').inner_text().startswith('PDF.js')
        assert page.locator('#pdfCanvas').evaluate('(el)=>el.width>500 && el.height>500')
        page.screenshot(path=str(ROOT/'screenshots/04-native-pdfjs-bbox.png'))
        page.locator('.pdf-highlight').first.click()
        page.wait_for_selector('.unit.focused',timeout=8000)
        assert not errors,errors
        print('PASS_NATIVE_PDFJS_CANVAS_BBOX_AND_BIDIRECTIONAL_REPLAY')
        browser.close()
finally:
    server.terminate()
    try: server.wait(timeout=5)
    except subprocess.TimeoutExpired:server.kill()