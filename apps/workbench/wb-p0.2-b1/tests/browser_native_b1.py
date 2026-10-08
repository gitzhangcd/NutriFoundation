"""Real Chromium acceptance: PDF.js rotated CropBox, bbox overlay alignment, reverse replay.

This test explicitly fails if pdfjs-dist is not pinned/installed. No fallback can pass.
"""
from __future__ import annotations
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'adversarial'))
from fixture_factory import EXACT,build_browser_fixture

assets=ROOT/'web/vendor/pdfjs/pdf.min.mjs'
if not assets.is_file():
    raise RuntimeError('PDFJS_ASSETS_MISSING_NATIVE_E2E_CANNOT_PASS')
fixture=ROOT/'fixtures/b1_synthetic_crop_rotate_90.AnnotationSourcePackage.v0.1.zip'
manifest=build_browser_fixture(fixture)
s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
url=f'http://127.0.0.1:{port}'
proc=subprocess.Popen([sys.executable,str(ROOT/'wb_a.py'),'serve','--root',tempfile.mkdtemp(prefix='wb_b1_native_'),
                       '--host','127.0.0.1','--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
try:
    for _ in range(100):
        try:
            if urlopen(url+'/api/health',timeout=.6).status==200:break
        except Exception: time.sleep(.2)
    else:raise RuntimeError('SERVER_NOT_READY')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda ex:errors.append(str(ex)))
        page.goto(url,wait_until='load')
        page.get_by_role('button',name='导入来源包').click()
        page.locator('#upload').set_input_files(fixture)
        page.get_by_role('button',name='校验并导入').click()
        page.wait_for_function("window.doc && window.doc.unit_count>=2",timeout=15000)
        page.wait_for_function("document.querySelector('#pdfEngine')?.textContent?.startsWith('PDF.js')",timeout=30000)
        page.evaluate('''(quote)=>{
          const p=[...document.querySelectorAll('.unit p')].find(n=>n.textContent.includes(quote));
          if(!p)throw Error('MISSING_SYNTHETIC_SOURCE_PARAGRAPH');
          const walker=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);let n, text=[];let start=0;
          while((n=walker.nextNode())){text.push({n,s:start,e:start+n.textContent.length});start+=n.textContent.length;}
          const full=text.map(x=>x.n.textContent).join(''),offset=full.indexOf(quote);
          if(offset<0)throw Error('QUOTE_NOT_FOUND_IN_RENDERED_MARKDOWN');
          const a=text.find(x=>x.s<=offset && x.e>offset), b=text.find(x=>x.s<offset+quote.length && x.e>=offset+quote.length);
          const range=document.createRange();range.setStart(a.n,offset-a.s);range.setEnd(b.n,offset+quote.length-b.s);
          window.getSelection().removeAllRanges();window.getSelection().addRange(range);
          p.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,clientX:700,clientY:390}));
        }''',EXACT)
        page.get_by_role('button',name='绑定 SourceAnchor').click()
        page.wait_for_function("document.querySelector('#anchorCount')?.textContent==='1'",timeout=10000)
        page.get_by_role('button',name='定位 PDF ↗').click()
        page.wait_for_selector('.pdf-highlight',timeout=20000)
        assert page.locator('#pdfEngine').inner_text().startswith('PDF.js')
        assert page.locator('#pdfCanvas').evaluate('(x)=>x.width>500 && x.height>300')
        geometry=page.evaluate('''()=>{
          const loc=WBPDF.current().locator;
          const st=document.querySelector('#pdfStage').getBoundingClientRect();
          const box=document.querySelector('.pdf-highlight').getBoundingClientRect();
          const normalized=loc.pdf_locator.rects[0].rect_normalized;
          return {rotation:loc.pdf_locator.page_rotation,page_width:loc.pdf_locator.page_width,
            page_height:loc.pdf_locator.page_height,geometry_basis:loc.pdf_locator.geometry_basis,
            height:st.height,width:st.width,norm:normalized,
            actual_x:(box.left-st.left)/st.width,actual_y:(box.top-st.top)/st.height,
            actual_w:box.width/st.width,actual_h:box.height/st.height};
        }''')
        assert geometry['rotation']==90,geometry
        assert geometry['page_width']==600 and geometry['page_height']==440,geometry
        assert geometry['geometry_basis']=='VISIBLE_CROP_ROTATION_AWARE',geometry
        nx,ny,fx,fy=geometry['norm']
        assert abs(geometry['actual_x']-nx)<0.004 and abs(geometry['actual_y']-ny)<0.004,geometry
        assert abs(geometry['actual_w']-(fx-nx))<0.004 and abs(geometry['actual_h']-(fy-ny))<0.004,geometry
        target=ROOT/'screenshots/05-b1-native-pdfjs-crop-rotate-bbox.png'
        target.parent.mkdir(exist_ok=True)
        page.screenshot(path=str(target),full_page=False)
        page.get_by_role('button',name='返回结构化文档中的对应锚点').first.click()
        page.wait_for_selector('.unit.focused',timeout=10000)
        assert page.locator('.unit.focused').inner_text().find(EXACT)>=0
        assert not errors,errors
        print('PASS_B1_NATIVE_PDFJS_CROP_ROTATION_BBOX_AND_REVERSE_REPLAY')
        print('PASS_B1_PDFJS_OVERLAY_COORDINATES',geometry)
        print('SCREENSHOT',target)
        browser.close()
finally:
    proc.terminate()
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:proc.kill()