/* Workbench WB-P0.2-B PDF.js adapter with explicit offline raster fallback.
 * The only exact highlight coordinates accepted here are verified server-side
 * PDF_PAGE_BBOX sidecars. Never project a Markdown page hint as exact geometry.
 */
(() => {
  let pdfjs = null, documentHandle = null, mode = 'loading', renderId = 0;
  let currentPage = 1, currentLocator = null, zoom = 1.28;
  const $ = id => document.getElementById(id);

  async function initialize(){
    try {
      // Production installs the exact pinned browser/worker assets locally.
      // No CDN dependency or untrusted runtime script injection.
      pdfjs = await import('/static/vendor/pdfjs/pdf.min.mjs');
      pdfjs.GlobalWorkerOptions.workerSrc = '/static/vendor/pdfjs/pdf.worker.min.mjs';
      documentHandle = await pdfjs.getDocument({url:'/api/original.pdf', useSystemFonts:true}).promise;
      mode = 'pdfjs';
    } catch (err) {
      // Deterministic viewer fallback for offline research environments.
      // Label it accurately: raster pages are NOT PDF.js.
      mode = 'raster-fallback';
      documentHandle = null;
    }
    const label = $('pdfEngine');
    if(label) label.textContent = mode === 'pdfjs' ? 'PDF.js · local pinned module' : '原件页图 · 离线降级（未加载 PDF.js）';
    return mode;
  }

  function drawRectangles(locator){
    const target=$('pdfOverlay');target.replaceChildren();
    if(!locator || locator.pdf_locator?.match_status !== 'VERIFIED_UNIQUE_PDF_TEXT' || locator.pdf_locator.page !== currentPage){
      $('pdfLocatorStatus').textContent='暂无已验证的 PDF_PAGE_BBOX，禁止假定精确位置';
      return;
    }
    // A stale sidecar is never a valid overlay, even if its page coincides.
    if(locator.source_pdf_sha256 !== window.doc?.source_pdf_sha256 ||
       locator.canonical_revision !== window.doc?.revision ||
       !Array.isArray(locator.pdf_locator?.rects)){
      $('pdfLocatorStatus').textContent='原件/文档修订不一致：禁止高亮';
      return;
    }
    const rects=locator.pdf_locator.rects;
    $('pdfLocatorStatus').textContent=`已验证原始 PDF 文字 · 第 ${currentPage} 页 · ${rects.length} 个文本框`;
    for(const rect of rects){
      const [x0,y0,x1,y1]=rect.rect_normalized;
      if (![x0,y0,x1,y1].every(Number.isFinite) || !(0<=x0&&x0<x1&&x1<=1&&0<=y0&&y0<y1&&y1<=1)){
        target.replaceChildren();
        $('pdfLocatorStatus').textContent='坐标无效：拒绝渲染高亮';
        return;
      }
      const el=document.createElement('button');
      el.type='button'; el.className='pdf-highlight';el.setAttribute('aria-label','返回结构化文档中的对应锚点');
      el.style.left=`${100*x0}%`; el.style.top=`${100*y0}%`;
      el.style.width=`${100*(x1-x0)}%`;el.style.height=`${100*(y1-y0)}%`;
      el.title='点击高亮：返回结构化文档中的确切文本锚点';
      el.addEventListener('click',()=>window.replayToStructured?.(locator.anchor_id));
      target.append(el);
    }
  }

  async function showPage(page, locator=null){
    if(!window.doc){return;}
    const generation=++renderId;
    currentPage=Math.max(1,Math.min(window.doc.source_pages,Number(page)||1));
    currentLocator=locator && locator.pdf_locator?.page===currentPage?locator:null;
    $('pdfPage').value=String(currentPage);
    if(mode==='loading')await initialize();
    if(generation!==renderId)return;
    try{
      const stage=$('pdfStage'), canvas=$('pdfCanvas'), img=$('pdfRaster');
      if(mode==='pdfjs'){
        const obj=await documentHandle.getPage(currentPage);
        if(generation!==renderId)return;
        const viewport=obj.getViewport({scale:zoom});
        stage.style.width=`${viewport.width}px`;
        // A renderer with a different page box must NOT reuse PyMuPDF geometry.
        if (currentLocator && (Math.abs(viewport.width/zoom-currentLocator.pdf_locator.page_width)>0.5 ||
            Math.abs(viewport.height/zoom-currentLocator.pdf_locator.page_height)>0.5)) {
          currentLocator=null;
          $('pdfLocatorStatus').textContent='PDF.js 与解析器页面尺寸不一致：拒绝精确高亮';
        }
        canvas.width=Math.floor(viewport.width);canvas.height=Math.floor(viewport.height);
        img.style.display='none';canvas.style.display='block';
        await obj.render({canvasContext:canvas.getContext('2d'),viewport}).promise;
      } else {
        const scale= Math.min(2.5,Math.max(0.5,zoom));
        let image= new Image();
        image.src=`/api/pdf/page/${currentPage}/png?scale=${scale}`;
        await image.decode();
        if(generation!==renderId)return;
        stage.style.width=`${image.naturalWidth}px`;
        img.src=image.src;img.style.display='block';canvas.style.display='none';
      }
      if(generation!==renderId)return;
      drawRectangles(currentLocator);
      if(currentLocator){
        // In both PDF.js and raster mode, the rectangles are overlaid using
        // immutable PDF top-left normalized positions.
        const first=$('pdfOverlay').firstElementChild;
        first?.scrollIntoView({block:'center',inline:'center',behavior:'smooth'});
      }
    }catch(err){
      if(generation===renderId){$('pdfLocatorStatus').textContent=`原件加载失败：${err.message}`;}
    }
  }
  async function reloadDocument(){mode='loading';documentHandle=null;currentLocator=null;await initialize();await showPage(1);}
  function zoomBy(delta){zoom=Math.max(0.65,Math.min(2.25,zoom+delta));$('pdfZoom').textContent=Math.round(zoom*100)+'%';showPage(currentPage,currentLocator);}
  function current(){return {page:currentPage,mode,zoom,locator:currentLocator};}
  window.WBPDF = {initialize,showPage,reloadDocument,zoomBy,current};
})();