const $ = id=>document.getElementById(id);
const SOURCE='SYN-5-2-PAPER';
let doc=null,sourceURL='',currentPage=1,selected=null,selectedUnit=null,pdfjs=null,pdfDoc=null,activeLocator=null;
let translationMap=new Map(),selectedOffsets=null;
function plainMarkdown(raw){
 let text='',offsets=[];
 const skip=new Set();
 for(const match of raw.matchAll(/\*\*|__|^#{1,6}\s+/gm))for(let i=match.index;i<match.index+match[0].length;i++)skip.add(i);
 for(let i=0;i<raw.length;i++){if(!skip.has(i)){offsets.push(i);text+=raw[i];}}
 return {text,offsets};
}
// Structured Markdown TABLE renderer: textContent only, never injected HTML.
// Preserve original raw UTF-16 offsets for per-cell source citation.
function parseSourceTable(raw){
 const lines=raw.split('\n');if(lines.length<2)return null;
 const rows=[];let offset=0;
 for(const line of lines){
   if(!line.trim().startsWith('|'))return null;
   const cells=[];let begin=0,escaped=false;
   for(let i=0;i<=line.length;i++){
     const ch=line[i];
     if(i===line.length || (ch==='|'&&!escaped)){
       const original=line.slice(begin,i),t=original.trim();
       const shift=original.indexOf(t);
       if(t)cells.push({text:t,start:offset+begin+Math.max(0,shift),end:offset+begin+Math.max(0,shift)+t.length});
       begin=i+1;
     }
     if(ch==='\\'&&!escaped)escaped=true;else escaped=false;
   }
   offset+=line.length+1;
   rows.push(cells);
 }
 if(rows.length<3)return null;
 if(!rows[1].length||!rows[1].every(x=>/^:?-{3,}:?$/.test(x.text)))return null;
 const width=rows[0].length;
 if(width<2||rows.some(x=>x.length!==width))return null;
 return [rows[0],...rows.slice(2)];
}
function sourceTableElement(u,rows,onChoose){
 const container=document.createElement('div');container.className='table-scroll';
 const table=document.createElement('table');table.className='scientific-table';
 const caption=document.createElement('caption');caption.textContent='科学资料表格 · 原文值（未经独立核查）';table.append(caption);
 for(let j=0;j<rows.length;j++){
   const region=document.createElement(j===0?'thead':'tbody');
   const tr=document.createElement('tr');
   for(const cell of rows[j]){
     const el=document.createElement(j===0?'th':'td');
     el.textContent=cell.text;el.dataset.rawStart=String(cell.start);el.dataset.rawEnd=String(cell.end);
     if(j===0)el.scope='col';
     el.addEventListener('mouseup',()=>{
       const sel=window.getSelection();
       if(!sel || sel.isCollapsed || !el.contains(sel.anchorNode) || !el.contains(sel.focusNode))return;
       const range=sel.getRangeAt(0);
       if(range.startContainer!==el.firstChild || range.endContainer!==el.firstChild)return;
       const start=cell.start+range.startOffset,end=cell.start+range.endOffset;
       if(u.raw.slice(start,end)===range.toString())onChoose(start,end);
     });
     tr.append(el);
   }
   region.append(tr);table.append(region);
 }
 container.append(table);return container;
}
function togglePDF(open){$('pdfDetails').open=open;$('pdfToggle').setAttribute('aria-expanded',String(open));$('pdfToggle').textContent=open?'返回结构化正文':'核验原始 PDF';}
function scrollUnit(id,smooth=true){togglePDF(false);const el=[...$('units').querySelectorAll('[data-uid]')].find(x=>x.dataset.uid===id);if(el){const container=$('units');container.scrollTo({top:container.scrollTop+el.getBoundingClientRect().top-container.getBoundingClientRect().top-18,behavior:smooth?'smooth':'instant'});for(const button of $('outline').querySelectorAll('button'))button.classList.toggle('active',button.dataset.uid===id);}}
let pdfRenderChain=Promise.resolve();
function identity(){return {'X-CSRF-Token':window.nutriSession?.csrf_token||''}}
function task(){return $('task').value}
function base(){return `/v1/tasks/${encodeURIComponent(task())}/sources/${SOURCE}`}
function show(s){const text=typeof s==='string'?s:JSON.stringify(s,null,2);$('status').textContent=text;$('evidenceFeedback').textContent=text;}
async function call(url,opts={}){const r=await fetch(url,{...opts,headers:{...identity(),...(opts.headers||{})},cache:'no-store'});if(!r.ok){const data=await r.json().catch(()=>({}));throw Error(data.detail?.code||data.detail||`HTTP ${r.status}`)}return r}
async function json(url,opts={}){return (await call(url,opts)).json()}
function escapeToText(el,s){el.textContent=s}
// One queue for initial task load and subsequent source switches prevents
// half-rendered paper/demo DOM from being mixed by concurrent HTTP/PDF tasks.
let readerSequence=Promise.resolve();
function scheduleReading(operation){
 const result=readerSequence.catch(()=>{}).then(operation);
 readerSequence=result;
 return result;
}
async function showSyntheticBilingualExercise(){return scheduleReading(renderSyntheticBilingualExercise);}
async function renderSyntheticBilingualExercise(){
 const p=await json(`/v1/tasks/${encodeURIComponent(task())}/reading-demo`);
 if(p.source_anchor_eligible!==false || p.scientific_capture!==false || p.coverage?.bilingual_units!==p.coverage?.units)
   throw Error('INVALID_SYNTHETIC_READING_SCOPE');
 doc=null;selected=null;selectedUnit=null;selectedOffsets=null;activeLocator=null;
 $('selectionToolbar').hidden=true;$('quote').value='';
 $('pdfDetails').hidden=true;$('pdfToggle').hidden=true;
 $('units').replaceChildren();$('outline').replaceChildren();
 $('readerTitle').textContent='完整双语阅读练习（自编合成）';
 $('sourceTitle').textContent='自编双语模拟科研文章';
 $('readerMeta').textContent='所有数值均为虚构 · 不可建立 SourceAnchor · 不用于真实科学证据';
 $('sourceBadge').textContent=`双语 ${p.coverage.bilingual_units}/${p.coverage.units} 单元 · 无 PDF`;
 $('sourceVersion').textContent='合成练习文档 · '+p.version;
 $('translationVersion').textContent='双语自编 v1 · 非科学译文资格认证';
 $('translationStatus').textContent=`完整合成演练：${p.coverage.bilingual_units}/${p.coverage.units} 双语覆盖 · 不可作为科研引用`;
 $('bilingualToolbar').hidden=false;
 for(const u of p.units){
   const div=document.createElement('div');div.className='unit translated';div.dataset.uid=u.unit_id;
   if(u.type==='SECTION')div.classList.add('section');
   const en=document.createElement('div');en.className='unit-original';
   const zh=document.createElement('div');zh.className='unit-translation';
   const enTable=u.type==='TABLE'?parseSourceTable(u.english):null;
   const zhTable=u.type==='TABLE'?parseSourceTable(u.chinese):null;
   if(enTable)en.append(sourceTableElement({raw:u.english},enTable,()=>{}));
   else en.textContent=u.english;
   if(zhTable)zh.append(sourceTableElement({raw:u.chinese},zhTable,()=>{}));
   else zh.textContent=u.chinese;
   div.append(en,zh);
   if(u.type==='SECTION'){
     const button=document.createElement('button');button.type='button';
     button.dataset.uid=u.unit_id;button.textContent=u.chinese+' / '+u.english;
     button.onclick=()=>scrollUnit(u.unit_id);$('outline').append(button);
   }
   $('units').append(div);
 }
 $('units').dataset.readingMode=$('readerMode').value;
 $('units').scrollTop=0;
 show('正在查看完整双语合成演练。此资料不能引用到正式或合成任务的科学证据链。');
}
async function load(){return scheduleReading(loadDocument);}
async function loadDocument(){try{window.CSS?.highlights?.delete('evidence-source');$('readerSource').hidden=true;selected=null;selectedUnit=null;selectedOffsets=null;doc=null;translationMap.clear();$('bilingualToolbar').hidden=true;$('selectionToolbar').hidden=true;pdfDoc=null;pdfjs=null;sourceURL='';$('units').replaceChildren();$('anchors').replaceChildren();$('outline').replaceChildren();$('translationVersion').textContent='';$('translationStatus').textContent='翻译未就绪';togglePDF(false);window.dispatchEvent(new CustomEvent('nutri-evidence',{detail:{items:[],bindings:[],itemBindings:[]}}));$('pdfCanvas').width=0;$('pdfOverlay').replaceChildren();$('pdfRaster').style.display='none';
 const projection=await json(`/v1/tasks/${task()}/read-model`);$('phase').textContent=projection.phase;
 if(projection.arm==='R1') {$('readerSource').value='paper'; $('readerTitle').textContent='候选证据 · 授权摘录';$('sourceTitle').textContent='R1 候选引用片段';$('readerMeta').textContent='仅限任务许可的候选证据；不提供全文与原始 PDF。';$('sourceVersion').textContent='来源权限：候选摘录';$('translationStatus').textContent='此任务不提供全文译文';$('pdfToggle').hidden=true;$('pdfDetails').hidden=true;$('query').disabled=true;$('searchBtn').disabled=true; $('sourceBadge').textContent='候选引用片段'; if(projection.phase==='EXPERT_VERIFY'){const fragments=await json(base()+'/candidate-spans'); for(const x of fragments.candidate_spans){const div=document.createElement('div');div.className='unit';div.textContent=x.quote; $('units').append(div)}show('R1：仅可见已验证的候选引用片段，不提供整篇原文/PDF');}else{show('R1 门禁：候选尚未冻结，来源不可访问。')}return;}
 $('readerSource').hidden=false;
 $('pdfToggle').hidden=false;$('pdfDetails').hidden=false;$('query').disabled=false;$('searchBtn').disabled=false;
 const src=await json(`/v1/tasks/${task()}/sources`);const d=await json(base()+'/document');doc=d;sourceURL=base();$('readerTitle').textContent=d.title;$('sourceTitle').textContent=d.title;$('readerMeta').textContent='公开论文阅读器练习 · 仅用于合成流程验证 · 英文原文与中文辅助';$('sourceVersion').textContent=`原文版本：${d.revision} · 文档 ${d.document_id}`;$('sourceBadge').textContent=`${d.unit_count} 单元 · PDF ${d.source_pages} 页`;
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
       if(record.translation_status!=='UNVERIFIED_SYNTHETIC' ||
          !['SOURCE_EXCERPT_ONLY','FULL_UNIT'].includes(record.alignment_level))continue;
       if(record.alignment_level==='FULL_UNIT' && record.source_quote!==unit.raw)continue;
       if(!translationMap.has(record.unit_id))translationMap.set(record.unit_id,[]);
       translationMap.get(record.unit_id).push(record);
     }
     const translatedCount=[...translationMap.values()].reduce((n,a)=>n+a.length,0);
     const full=tr.coverage_counts?.fully_translated_units||0;
     $('translationVersion').textContent='译文版本：'+tr.translation_version;
     $('translationStatus').textContent=`译文 ${translatedCount} 处 · 整段 ${full}/${d.unit_count} · 未经科学核查 · ${tr.translation_version}`;
   }
 }catch(e){$('translationStatus').textContent='翻译不可用，仅显示原文';}
 $('bilingualToolbar').hidden=false;for(const u of d.units){
 const records=translationMap.get(u.unit_id)||[];
 const div=document.createElement('div');
 div.className='unit'+(u.type==='SECTION'?' section':'')+(records.length?' translated':'');
 div.dataset.uid=u.unit_id;
 if(u.type==='SECTION'){const button=document.createElement('button');button.type='button';button.dataset.uid=u.unit_id;button.textContent=plainMarkdown(u.raw).text;button.onclick=()=>scrollUnit(u.unit_id);$('outline').append(button);}
 const original=document.createElement('div');original.className='unit-original';const plain=plainMarkdown(u.raw);
 const chooseRange=(start,end)=>{
   selectedUnit=u;selected=u.raw.slice(start,end);selectedOffsets={unit_id:u.unit_id,start,end};
   $('quote').value=selected;$('selectionStatus').textContent='原文精确范围已选取 · 服务端仍需校验';
   $('selectionToolbar').hidden=false;
 };
 const parsed=u.type==='TABLE'?parseSourceTable(u.raw):null;
 if(parsed)original.append(sourceTableElement(u,parsed,chooseRange));
 else original.textContent=plain.text;
 div.append(original);
 original.addEventListener('mouseup',()=>{
   const s=window.getSelection();
   if(s && !s.isCollapsed && original.contains(s.anchorNode) && original.contains(s.focusNode)){
     const range=s.getRangeAt(0);
     if(range.startContainer!==original.firstChild || range.endContainer!==original.firstChild)return;
     const start=plain.offsets[range.startOffset],end=plain.offsets[range.endOffset-1]+1;
     if(!Number.isInteger(start)||!Number.isInteger(end))return;
     selectedUnit=u;selected=u.raw.slice(start,end);
     selectedOffsets={unit_id:u.unit_id,start,end};
     $('quote').value=selected;
     $('selectionStatus').textContent='英文原文选取 · 将由服务端校验精确范围';
     $('selectionToolbar').hidden=false;
   }
 });
 for(const record of records){
   const translated=document.createElement('div');translated.className='unit-translation';
   translated.textContent=(record.alignment_level==='FULL_UNIT'?'中文段落（尚未科学审校）｜':'中文摘录（演练译文）｜')+record.translated_excerpt+
      (record.quality_warnings?.length?' · ⚠ 数字或统计信息待核查':'');
   translated.title='仅原文摘录对齐；译文未经科学审定，不代表全文或精确句子对齐';
   translated.addEventListener('mouseup',()=>{
     const s=window.getSelection();
     if(s && !s.isCollapsed && translated.contains(s.anchorNode) && translated.contains(s.focusNode)){
       selectedUnit=u;selected=record.source_quote;selectedOffsets={unit_id:u.unit_id,start:record.source_start_utf16,end:record.source_end_utf16};$('quote').value=selected;
       $('selectionStatus').textContent='已映射到英文原文摘录 · L1 摘录对齐，非译文精确句子锚点';
       $('selectionToolbar').hidden=false;
     }
   });
   div.append(translated);
 }
 const foot=document.createElement('div');foot.className='unit-footer';const id=document.createElement('span');id.className='unit-id';id.textContent='原文单元 · '+u.unit_id;const cite=document.createElement('button');cite.type='button';cite.className='text-button';cite.textContent='＋ 引用此段';cite.onclick=()=>{selectedUnit=u;selected=u.raw;selectedOffsets={unit_id:u.unit_id,start:0,end:u.raw.length};$('quote').value=selected;$('selectionStatus').textContent='英文整段选取 · 由服务端验证原文范围';$('selectionToolbar').hidden=false;};foot.append(id,cite);if(u.type!=='SECTION')div.append(foot);$('units').append(div);
}
 const sections=[...$('outline').querySelectorAll('button')];if(!sections.length)$('outline').textContent='当前来源没有章节标题';
 const first=sections.find(button=>/abstract/i.test(button.textContent))||sections[0];if(first)scrollUnit(first.dataset.uid,false);
 await listAnchors();show('任务级来源投影已验证；任何原件读取都携带同一任务令牌。');await openPDF();
 if($('readerSource').value==='demo')await renderSyntheticBilingualExercise();
 }catch(e){$('phase').textContent='拒绝访问';show('ACCESS DENIED: '+e.message);$('sourceBadge').textContent='无授权来源';}}
async function listAnchors(){
 const r=await json(base()+'/anchors'),bindings=await json(base()+'/bindings');
 const itemResult=await json(base()+'/item-bindings');
 $('anchors').replaceChildren();
 for(const a of r.items){
  const el=document.createElement('div');el.className='anchor';el.tabIndex=0;el.setAttribute('role','button');
  const quote=document.createElement('div');quote.textContent=a.quote;el.append(quote);
  const fields=(bindings.items||bindings.bindings||[]).filter(b=>b.anchor_id===a.anchor_id).map(b=>[...$('field').options].find(o=>o.value===b.field)?.textContent||b.field);
  const sm=document.createElement('small');sm.textContent=fields.length?'关联判断：'+fields.join(' · '):'已创建；尚无字段绑定';el.append(sm);
  el.onclick=()=>{togglePDF(true);openAnchor(a)};el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();el.click();}};$('anchors').append(el);
  const unit=[...$('units').querySelectorAll('[data-uid]')].find(x=>x.dataset.uid===a.unit_id);if(unit)unit.classList.add('has-anchor');
 }
 window.dispatchEvent(new CustomEvent('nutri-evidence',{detail:{items:r.items,bindings:bindings.items||bindings.bindings||[],itemBindings:itemResult.items||[]}}));
}
async function sourceHash(text){
 const raw=new TextEncoder().encode(text);
 const buf=await crypto.subtle.digest('SHA-256',raw);
 return [...new Uint8Array(buf)].map(b=>b.toString(16).padStart(2,'0')).join('');
}
async function makeAnchor(){
 try{
  if(!doc||!selectedUnit||!selected)throw Error('请先在左侧选取有明确出处的英文原文');
  if($('quote').value!==selected)throw Error('引文已修改，请重新定位后再关联');
  const target=window.nutriJudgment?.getBindingTarget?.();
  if(!target)throw Error('请先打开专家判断并选择目标条目');
  const raw=selectedUnit.raw;let start,end;
  if(selectedOffsets&&selectedOffsets.unit_id===selectedUnit.unit_id&&raw.slice(selectedOffsets.start,selectedOffsets.end)===selected){
    start=selectedOffsets.start;end=selectedOffsets.end;
  }else{
    if(raw.split(selected).length!==2)throw Error('此引文出现多次，请从原文中精确选取，勿猜测位置');
    start=raw.indexOf(selected);end=start+selected.length;
  }
  if(raw.slice(start,end)!==selected)throw Error('SOURCE_SELECTION_MISMATCH');
  const a=await json(base()+'/anchors',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({unit_id:selectedUnit.unit_id,quote:selected,start_utf16:start,end_utf16:end,
      expected_revision:doc.revision,expected_source_markdown_sha256:doc.source_markdown_sha256})});
  const data={anchor_id:a.anchor_id,field:target.field,
    expected_document_revision:doc.revision,expected_pdf_sha256:doc.source_pdf_sha256};
  let exact=false;
  if(target.legacy){
    await json(base()+'/bind-anchor',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  }else{
    await json(base()+'/bind-anchor-item',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({...data,item_index:target.index,
        item_sha256:await sourceHash(target.text),expected_draft_revision:target.revision})});
    exact=true;
  }
  await listAnchors();
  const pdfVerified=await openAnchor(a);
  const category=exact?`第 ${target.index+1} 条独立判断`:'当前科学字段（尚未关联到具体判断）';
  show(pdfVerified?`已通过服务端证据验证并绑定到${category}；PDF 精确定位已核验。`:
     `已通过服务端证据验证并绑定到${category}；PDF 精确定位尚未验证。请缩小引文并核查 PDF。`);
 }catch(e){show('无法创建或绑定证据：'+e.message);}
}
async function openPDF(){try{pdfjs=await import('/static/vendor/pdfjs/pdf.min.mjs');pdfjs.GlobalWorkerOptions.workerSrc='/static/vendor/pdfjs/pdf.worker.min.mjs';pdfDoc=await pdfjs.getDocument({url:base()+'/original.pdf',httpHeaders:identity(),disableRange:true,disableStream:true,useSystemFonts:true}).promise;$('pdfEngine').textContent='PDF.js · authenticated';await showPage(1)}catch(e){pdfjs=null;pdfDoc=null;$('pdfEngine').textContent='授权页图模式';await showPage(1)}}
async function showPage(number){pdfRenderChain=pdfRenderChain.catch(()=>{}).then(()=>renderPage(number));return pdfRenderChain;}
async function renderPage(number){if(!doc)return;currentPage=Math.min(Math.max(number,1),doc.source_pages);$('pdfPage').textContent=`第 ${currentPage} / ${doc.source_pages} 页`;$('pdfOverlay').replaceChildren();const cnv=$('pdfCanvas'),img=$('pdfRaster');if(pdfDoc){img.style.display='none';const page=await pdfDoc.getPage(currentPage),viewport=page.getViewport({scale:1.3});cnv.width=viewport.width;cnv.height=viewport.height;const ctx=cnv.getContext('2d');await page.render({canvas:cnv,canvasContext:ctx,viewport}).promise;}else{cnv.style.display='none';img.style.display='block';const png=await call(base()+`/pages/${currentPage}/png`);const blob=await png.blob();if(img.dataset.objecturl)URL.revokeObjectURL(img.dataset.objecturl);img.dataset.objecturl=URL.createObjectURL(blob);img.src=img.dataset.objecturl;}if(activeLocator&&activeLocator.pdf_locator.page===currentPage)highlight(activeLocator)}
function highlight(loc){if(loc.source_pdf_sha256!==doc?.source_pdf_sha256||loc.canonical_revision!==doc.revision)return;const p=loc.pdf_locator;if(p.match_status!=='VERIFIED_UNIQUE_PDF_TEXT'||p.page!==currentPage)return;for(const v of p.rects){const rect=v.rect_normalized;if(rect.length!==4||rect.some(x=>!Number.isFinite(x)||x<0||x>1)||rect[2]<=rect[0]||rect[3]<=rect[1])continue;const b=document.createElement('button');b.className='pdf-highlight';b.style.left=(rect[0]*100)+'%';b.style.top=(rect[1]*100)+'%';b.style.width=((rect[2]-rect[0])*100)+'%';b.style.height=((rect[3]-rect[1])*100)+'%';b.title='返回已授权结构化正文';b.onclick=()=>{const el=document.querySelector(`[data-uid="${loc.unit_id}"]`);if(el){el.classList.add('selected');el.scrollIntoView({block:'center'})}};$('pdfOverlay').append(b)}$('pdfLocatorStatus').textContent='PDF_PAGE_BBOX/0.2 · 原始 PDF 文字层唯一匹配 · 可反向回放'}
async function openAnchor(a){try{const url=base()+`/anchors/${encodeURIComponent(a.anchor_id)}`;const loc=await json(url+'/resolve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_revision:doc.revision,expected_source_pdf_sha256:doc.source_pdf_sha256})});activeLocator=loc;await showPage(loc.pdf_locator.page);const verified=loc.pdf_locator.match_status==='VERIFIED_UNIQUE_PDF_TEXT' && $('pdfOverlay').querySelector('.pdf-highlight')!==null;if(!verified)throw Error('PDF_BOUNDING_BOX_NOT_VERIFIED');window.dispatchEvent(new CustomEvent('nutri-pdf-verification',{detail:{anchor_id:a.anchor_id,verified:true}}));show('已校验原始 PDF 的 SHA-256、引文和文本框。');return true;}catch(e){
  window.dispatchEvent(new CustomEvent('nutri-pdf-verification',{detail:{anchor_id:a.anchor_id,verified:false}}));
  const hint=a.pdf_page_hint;
  if(Number.isInteger(hint)&&hint>=1&&hint<=doc.source_pages){
    try{togglePDF(true);await showPage(hint);}catch(_){}
  }else togglePDF(true);
  $('pdfLocatorStatus').textContent='PDF 未能唯一定位原文范围。'+
    (hint?'已打开来源提示页（不构成精确定位证明）。':'可在原始 PDF 中人工查看。')+
    ' 建议缩短引文为可唯一识别的句子或短语，再重新引用。';
  show('原文锚点可独立保存，但 PDF 精确框未验证：'+e.message+
       '。请缩小引文、核查上下文，并在确认前不要视为精确 PDF 证据。');
  return false;
}}
function locateTypedQuote(){const q=$('quote').value.trim();if(!doc||q.length<20){show('请先读取任务文档，并输入完整原文引文');return;}const matches=doc.units.filter(u=>u.raw.includes(q));if(matches.length!==1){show('引文在当前授权文档中不存在或不唯一；拒绝猜测定位');return;}selectedUnit=matches[0];selected=q;
if(selectedUnit.raw.split(q).length!==2){show('引文在原文单元中不唯一：请选中准确原文范围');return;}
const begin=selectedUnit.raw.indexOf(q);selectedOffsets={unit_id:selectedUnit.unit_id,start:begin,end:begin+q.length};
const el=document.querySelector(`[data-uid="${selectedUnit.unit_id}"]`);if(el){el.classList.add('selected');el.scrollIntoView({block:'center'});}show('已定位输入的准确引文；创建 SourceAnchor 时仍由服务端再次校验。')}
$('readerMode').addEventListener('change',()=>{ $('units').dataset.readingMode=$('readerMode').value;for(const button of document.querySelectorAll('[data-mode]')){button.classList.toggle('active',button.dataset.mode===$('readerMode').value);button.setAttribute('aria-pressed',String(button.dataset.mode===$('readerMode').value));} });
for(const button of document.querySelectorAll('[data-mode]'))button.onclick=()=>{$('readerMode').value=button.dataset.mode;$('readerMode').dispatchEvent(new Event('change'));};
$('pdfToggle').onclick=()=>togglePDF(!$('pdfDetails').open);
$('pdfDetails').addEventListener('toggle',()=>{$('pdfToggle').setAttribute('aria-expanded',String($('pdfDetails').open));$('pdfToggle').textContent=$('pdfDetails').open?'返回结构化正文':'核验原始 PDF';});
$('dismissSelection').onclick=()=>{$('selectionToolbar').hidden=true;window.getSelection()?.removeAllRanges();};
$('selectionBind').onclick=()=>{$('makeAnchor').click();};
$('locateQuote').onclick=locateTypedQuote;
$('load').onclick=load;$('makeAnchor').onclick=makeAnchor;$('prev').onclick=()=>showPage(currentPage-1);$('next').onclick=()=>showPage(currentPage+1);
$('candidate').onclick=async()=>{try{const c=await json(`/v1/tasks/${task()}/candidate-set`);show({exposure:'AUTHORIZED',candidate_set_sha:c.candidate_set_sha})}catch(e){show('CANDIDATE DENIED: '+e.message)}};
$('searchBtn').onclick=async()=>{try{const s=await json(base()+'/search?q='+encodeURIComponent($('query').value));$('searchResults').replaceChildren();for(const result of s.results){const button=document.createElement('button');button.type='button';button.className='text-button';button.textContent='跳转：'+result.unit_id;button.onclick=()=>scrollUnit(result.unit_id);$('searchResults').append(button);}if(!s.results.length)$('searchResults').textContent='没有匹配的授权原文'}catch(e){$('searchResults').textContent='SEARCH DENIED'}};

$('readerSource').addEventListener('change',async()=>{
 const picker=$('readerSource');
 const requested=picker.value;
 picker.disabled=true;
 picker.dataset.readySource='';
 $('translationStatus').textContent='正在切换阅读资料…';
 try{
   if(requested==='demo')await showSyntheticBilingualExercise();
   else await load();
   if(picker.value===requested)picker.dataset.readySource=requested;
 }catch(e){$('translationStatus').textContent='阅读资料无法切换：'+e.message;}
 finally{picker.disabled=false;}
});
window.nutriReader={load};

window.addEventListener('nutri-replay-source',async e=>{
 const {anchor,view}=e.detail;if(!doc)return;
 if(view==='pdf'){togglePDF(true);await openAnchor(anchor);return;}
 scrollUnit(anchor.unit_id);
 for(const el of $('units').querySelectorAll('.selected'))el.classList.remove('selected');
 const el=[...$('units').querySelectorAll('[data-uid]')].find(x=>x.dataset.uid===anchor.unit_id);
 if(el){el.classList.add('selected');highlightSourceRange(el,anchor);el.tabIndex=-1;el.focus({preventScroll:true});}
});

function highlightSourceRange(el,anchor){
 if(!window.CSS?.highlights||typeof Highlight==='undefined')return;
 CSS.highlights.delete('evidence-source');
 const unit=doc.units.find(x=>x.unit_id===anchor.unit_id);if(!unit)return;
 const start=anchor.start_utf16,end=anchor.end_utf16;
 if(unit.raw.slice(start,end)!==anchor.quote)return;
 const original=el.querySelector('.unit-original');let node,from,to;
 const cell=[...original.querySelectorAll('[data-raw-start]')].find(c=>Number(c.dataset.rawStart)<=start&&Number(c.dataset.rawEnd)>=end);
 if(cell){node=cell.firstChild;from=start-Number(cell.dataset.rawStart);to=end-Number(cell.dataset.rawStart);}
 else{const plain=plainMarkdown(unit.raw);node=original.firstChild;from=plain.offsets.indexOf(start);to=plain.offsets.indexOf(end-1)+1;}
 if(node?.nodeType!==Node.TEXT_NODE||from<0||to<=from)return;
 const range=document.createRange();range.setStart(node,from);range.setEnd(node,to);
 CSS.highlights.set('evidence-source',new Highlight(range));
}
