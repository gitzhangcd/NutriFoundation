"""Native pinned PDF.js + FastAPI + Chromium C1 acceptance; fails on raster fallback."""
from __future__ import annotations
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from server import BASE

SELECT = r"""(quote)=>{
 const p=[...document.querySelectorAll('.unit p')].find(n=>n.textContent.includes(quote));if(!p)throw Error('quote missing');
 let all='',arr=[],node;const t=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);
 while((node=t.nextNode())){arr.push({n:node,s:all.length,e:all.length+node.textContent.length});all+=node.textContent}
 const i=all.indexOf(quote),s=arr.find(x=>x.s<=i&&x.e>i),e=arr.find(x=>x.s<i+quote.length&&x.e>=i+quote.length);
 if(i<0||!s||!e)throw Error('missing exact visible quote');
 const r=document.createRange();r.setStart(s.n,i-s.s);r.setEnd(e.n,i+quote.length-e.s);
 window.getSelection().removeAllRanges();window.getSelection().addRange(r);return 'selected';
}"""

def run():
 if not (BASE/'web/vendor/pdfjs/pdf.min.mjs').is_file():
  raise RuntimeError('PINNED_PDFJS_REQUIRED: run bash install_pdfjs.sh')
 socket_=socket.socket();socket_.bind(('127.0.0.1',0));port=socket_.getsockname()[1];socket_.close()
 target=f'http://127.0.0.1:{port}'
 command=[sys.executable,str(BASE/'server.py'),'--demo-source','--root',tempfile.mkdtemp(prefix='c1_native_'), '--port',str(port),'--host','127.0.0.1']
 proc=subprocess.Popen(command,cwd=BASE,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
 try:
  for _ in range(130):
   try:
    if urlopen(target+'/api/health',timeout=.5).status==200:break
   except Exception:time.sleep(.2)
  else:raise RuntimeError('C1_HTTP_SERVER_NOT_READY')
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True)
   page=browser.new_page(viewport={'width':1880,'height':1120},device_scale_factor=1)
   errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(target,wait_until='load')
   page.wait_for_function("document.querySelector('#sourceStatus')?.textContent?.includes('154')",timeout=30000)
   page.locator('[data-field="decision_focus"]').fill('Synthetic paper/decision exercise, not clinical truth')
   page.locator('#saveBtn').click()
   page.wait_for_function("document.querySelector('#saveState')?.textContent?.includes('rev 1')",timeout=10000)
   assert page.evaluate(SELECT,'Three hundred adults with obesity were randomised')=='selected'
   page.locator('#makeAnchorBtn').click()
   page.wait_for_function("document.querySelector('#anchorCount')?.textContent==='1'",timeout=10000)
   page.locator('[data-bind]').first.click()
   page.locator('#saveBtn').click()
   page.wait_for_function("document.querySelector('#saveState')?.textContent?.includes('rev 2')",timeout=10000)
   page.locator('[data-open-pdf]').first.click()
   page.wait_for_function("document.querySelector('#pdfEngine')?.textContent?.startsWith('PDF.js')",timeout=35000)
   page.wait_for_selector('.pdf-highlight',timeout=25000)
   assert page.locator('#pdfCanvas').evaluate('(c)=>c.width>500&&c.height>500')
   bbox=page.locator('.pdf-highlight').first
   assert bbox.evaluate('(e)=>e.getBoundingClientRect().width>50')
   (BASE/'screenshots').mkdir(exist_ok=True)
   page.screenshot(path=str(BASE/'screenshots/04-native-pdfjs-c1.png'),full_page=True)
   bbox.click()
   page.wait_for_selector('.unit.selected',timeout=10000)
   page.locator('#reloadBtn').click()
   page.wait_for_function("document.querySelector('#saveState')?.textContent?.includes('rev 2')",timeout=10000)
   assert page.locator('[data-field="decision_focus"]').input_value().startswith('Synthetic')
   assert len(page.context.request.get(target+'/api/tasks/DEMO-R2-PREAI/draft').json()['bindings']['decision_focus'])==1
   assert not errors,errors
   print('PASS_C1_NATIVE_PDFJS_REAL_PAPER_ANCHOR_FIELD_DURABLE_DRAFT_RELOAD')
   browser.close()
 finally:
  proc.terminate()
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.kill()

if __name__=='__main__':run()