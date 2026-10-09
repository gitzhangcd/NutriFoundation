const $ = id=>document.getElementById(id);
const SOURCE='SYN-5-2-PAPER';
let doc=null,sourceURL='',currentPage=1,selected=null,selectedUnit=null,pdfjs=null,pdfDoc=null,activeLocator=null;
let translationMap=new Map();
function identity(){return {'X-CSRF-Token':window.nutriSession?.csrf_token||''}}
function task(){return $('task').value}
function base(){return `/v1/tasks/${encodeURIComponent(task())}/sources/${SOURCE}`}
function show(s){$('status').textContent=typeof s==='string'?s:JSON.stringify(s,null,2)}
async function call(url,opts={}){const r=await fetch(url,{...opts,headers:{...identity(),...(opts.headers||{})},cache:'no-store'});if(!r.ok){const data=await r.json().catch(()=>({}));throw Error(data.detail?.code||data.detail||`HTTP ${r.status}`)}return r}
async function json(url,opts={}){return (await call(url,opts)).json()}
function escapeToText(el,s){el.textContent=s}
async function load(){try{selected=null;selectedUnit=null;doc=null;translationMap.clear();$('bilingualToolbar').hidden=true;$('selectionToolbar').hidden=true;pdfDoc=null;pdfjs=null;sourceURL='';$('units').replaceChildren();$('anchors').replaceChildren();$('pdfCanvas').width=0;$('pdfOverlay').replaceChildren();$('pdfRaster').style.display='none';
 const projection=await json(`/v1/tasks/${task()}/read-model`);$('phase').textContent=projection.phase;
 if(projection.arm==='R1') { $('sourceBadge').textContent='候选引用片段'; if(projection.phase==='EXPERT_VERIFY'){const fragments=await json(base()+'/candidate-spans'); for(const x of fragments.candidate_spans){const div=document.createElement('div');div.className='unit';div.textContent=x.quote; $('units').append(div)}show('R1：仅可见已验证的候选引用片段，不提供整篇原文/PDF');}else{show('R1 门禁：候选尚未冻结，来源不可访问。')}return;}
 const src=await json(`/v1/tasks/${task()}/sources`);const d=await json(base()+'/document');doc=d;sourceURL=base();$('sourceBadge').textContent=`${d.unit_count} 单元 · PDF ${d.source_pages} 页`;
 // Never use a public static translation manifest: R1 could otherwise read
 // otherwise-forbidden source paragraphs. This task-authorized endpoint returns
 // ONLY exact source-bound, unverified *example excerpts*.
 try{
   const tr=await json(base()+'/translations');
   if(tr.source_document_id===d.document_id &&
      tr.source_revision===d.revision &&
      tr.source_markdown_sha256===d.source_markdown_sha256 &&
      tr.source_pdf_sha256===d.source_pdf_sha256 &&
      tr.scientific_capture===false){
     for(const record of tr.items||[]){
       const unit=d.units.find(x=>x.unit_id===record.unit_id);
       if(!unit || unit.raw_sha256!==record.source_unit_raw_sha256 ||
          unit.raw.slice(record.source_start_utf16,record.source_end_utf16)!==record.source_quote)continue;
       if(!translationMap.has(record.unit_id))translationMap.set(record.unit_id,[]);
       translationMap.get(record.unit_id).push(record);
     }
     $('translationStatus').textContent=`示例译文 ${[...translationMap.values()].reduce((n,a)=>n+a.length,0)} 处 · 未经科学核查`;
   }
 }catch(e){$('translationStatus').textContent='翻译不可用，仅显示原文';}
 $('bilingualToolbar').hidden=false;for(const u of d.units){
 const records=translationMap.get(u.unit_id)||[];
 const div=document.createElement('div');
 div.className='unit'+(u.type==='SECTION'?' section':'')+(records.length?' translated':'');
 div.dataset.uid=u.unit_id;
 const original=document.createElement('div');original.className='unit-original';original.textContent=u.raw;div.append(original);
 original.addEventListener('mouseup',()=>{
   const s=window.getSelection();
   if(s && !s.isCollapsed && original.contains(s.anchorNode) && original.contains(s.focusNode)){
     selectedUnit=u;selected=s.toString();$('quote').value=selected;
     $('selectionStatus').textContent='英文原文选取 · 将由服务端校验精确范围';
     $('selectionToolbar').hidden=false;
   }
 });
 for(const record of records){
   const translated=document.createElement('div');translated.className='unit-translation';
   translated.textContent='中文摘录（演练译文）｜'+record.translated_excerpt;
   translated.title='仅原文摘录对齐；译文未经科学审定，不代表全文或精确句子对齐';
   translated.addEventListener('mouseup',()=>{
     const s=window.getSelection();
     if(s && !s.isCollapsed && translated.contains(s.anchorNode) && translated.contains(s.focusNode)){
       selectedUnit=u;selected=record.source_quote;$('quote').value=selected;
       $('selectionStatus').textContent='已映射到英文原文摘录 · L1 摘录对齐，非译文精确句子锚点';
       $('selectionToolbar').hidden=false;
     }
   });
   div.append(translated);
 }
 $('units').append(div);
}await listAnchors();show('任务级来源投影已验证；任何原件读取都携带同一任务令牌。');await openPDF();}catch(e){$('phase').textContent='拒绝访问';show('ACCESS DENIED: '+e.message);$('sourceBadge').textContent='无授权来源';}}
async function listAnchors(){const r=await json(base()+'/anchors');$('anchors').replaceChildren();for(const a of r.items){const el=document.createElement('div');el.className='anchor';el.textContent=a.quote;const sm=document.createElement('small');sm.textContent=`${a.unit_id} · ${a.anchor_id}`;el.append(sm);el.onclick=()=>openAnchor(a);$('anchors').append(el)}}
async function makeAnchor(){try{if(!doc||!selectedUnit||!selected)throw Error('请先在左侧选中文字');const raw=selectedUnit.raw;const pos=raw.indexOf(selected);if(pos<0)throw Error('选择未在文档单元中精确匹配');const before=raw.slice(0,pos);const start=[...before].reduce((n,c)=>n+(c.codePointAt(0)>0xffff?2:1),0);const end=start+[...selected].reduce((n,c)=>n+(c.codePointAt(0)>0xffff?2:1),0);
const a=await json(base()+'/anchors',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:selectedUnit.unit_id,quote:selected,start_utf16:start,end_utf16:end,expected_revision:doc.revision,expected_source_markdown_sha256:doc.source_markdown_sha256})});await json(base()+'/bind-anchor',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({anchor_id:a.anchor_id,field:$('field').value,expected_document_revision:doc.revision,expected_pdf_sha256:doc.source_pdf_sha256})});await listAnchors();await openAnchor(a);show(`已通过服务端证据验证并绑定到字段 ${$('field').value}。`)}catch(e){show('ANCHOR DENIED: '+e.message)}}
async function openPDF(){try{pdfjs=await import('/static/vendor/pdfjs/pdf.min.mjs');pdfjs.GlobalWorkerOptions.workerSrc='/static/vendor/pdfjs/pdf.worker.min.mjs';pdfDoc=await pdfjs.getDocument({url:base()+'/original.pdf',httpHeaders:identity(),disableRange:true,disableStream:true,useSystemFonts:true}).promise;$('pdfEngine').textContent='PDF.js · authenticated';await showPage(1)}catch(e){pdfjs=null;pdfDoc=null;$('pdfEngine').textContent='授权页图模式';await showPage(1)}}
async function showPage(number){if(!doc)return;currentPage=Math.min(Math.max(number,1),doc.source_pages);$('pdfPage').textContent=`第 ${currentPage} / ${doc.source_pages} 页`;$('pdfOverlay').replaceChildren();const cnv=$('pdfCanvas'),img=$('pdfRaster');if(pdfDoc){img.style.display='none';const page=await pdfDoc.getPage(currentPage),viewport=page.getViewport({scale:1.3});cnv.width=viewport.width;cnv.height=viewport.height;const ctx=cnv.getContext('2d');await page.render({canvas:cnv,canvasContext:ctx,viewport}).promise;}else{cnv.style.display='none';img.style.display='block';const png=await call(base()+`/pages/${currentPage}/png`);const blob=await png.blob();if(img.dataset.objecturl)URL.revokeObjectURL(img.dataset.objecturl);img.dataset.objecturl=URL.createObjectURL(blob);img.src=img.dataset.objecturl;}if(activeLocator&&activeLocator.pdf_locator.page===currentPage)highlight(activeLocator)}
function highlight(loc){if(loc.source_pdf_sha256!==doc?.source_pdf_sha256||loc.canonical_revision!==doc.revision)return;const p=loc.pdf_locator;if(p.match_status!=='VERIFIED_UNIQUE_PDF_TEXT'||p.page!==currentPage)return;for(const v of p.rects){const rect=v.rect_normalized;if(rect.length!==4||rect.some(x=>!Number.isFinite(x)||x<0||x>1)||rect[2]<=rect[0]||rect[3]<=rect[1])continue;const b=document.createElement('button');b.className='pdf-highlight';b.style.left=(rect[0]*100)+'%';b.style.top=(rect[1]*100)+'%';b.style.width=((rect[2]-rect[0])*100)+'%';b.style.height=((rect[3]-rect[1])*100)+'%';b.title='返回已授权结构化正文';b.onclick=()=>{const el=document.querySelector(`[data-uid="${loc.unit_id}"]`);if(el){el.classList.add('selected');el.scrollIntoView({block:'center'})}};$('pdfOverlay').append(b)}$('pdfLocatorStatus').textContent='PDF_PAGE_BBOX/0.2 · 原始 PDF 文字层唯一匹配 · 可反向回放'}
async function openAnchor(a){try{const url=base()+`/anchors/${encodeURIComponent(a.anchor_id)}`;const loc=await json(url+'/resolve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_revision:doc.revision,expected_source_pdf_sha256:doc.source_pdf_sha256})});activeLocator=loc;await showPage(loc.pdf_locator.page);show('已校验原始 PDF 的 SHA-256、引文和文本框。')}catch(e){show('PDF LOCATION UNRESOLVED: '+e.message)}}
function locateTypedQuote(){const q=$('quote').value.trim();if(!doc||q.length<20){show('请先读取任务文档，并输入完整原文引文');return;}const matches=doc.units.filter(u=>u.raw.includes(q));if(matches.length!==1){show('引文在当前授权文档中不存在或不唯一；拒绝猜测定位');return;}selectedUnit=matches[0];selected=q;const el=document.querySelector(`[data-uid="${selectedUnit.unit_id}"]`);if(el){el.classList.add('selected');el.scrollIntoView({block:'center'});}show('已定位输入的准确引文；创建 SourceAnchor 时仍由服务端再次校验。')}
$('readerMode').addEventListener('change',()=>{ $('units').dataset.readingMode=$('readerMode').value; });
$('selectionBind').onclick=()=>{$('makeAnchor').click();};
$('locateQuote').onclick=locateTypedQuote;
$('load').onclick=load;$('makeAnchor').onclick=makeAnchor;$('prev').onclick=()=>showPage(currentPage-1);$('next').onclick=()=>showPage(currentPage+1);
$('candidate').onclick=async()=>{try{const c=await json(`/v1/tasks/${task()}/candidate-set`);show({exposure:'AUTHORIZED',candidate_set_sha:c.candidate_set_sha})}catch(e){show('CANDIDATE DENIED: '+e.message)}};
$('searchBtn').onclick=async()=>{try{const s=await json(base()+'/search?q='+encodeURIComponent($('query').value));$('searchResults').textContent=s.results.map(x=>x.unit_id).join(' · ')||'无匹配'}catch(e){$('searchResults').textContent='SEARCH DENIED'}};

window.nutriReader={load};
