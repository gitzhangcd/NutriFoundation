const $ = id=>document.getElementById(id);
const SOURCE='SYN-5-2-PAPER';
let doc=null,sourceURL='',currentPage=1,selected=null,selectedUnit=null,pdfjs=null,pdfDoc=null,activeLocator=null;
let selectionRect=null,citeTargetLabel='';
let translationMap=new Map(),selectedOffsets=null,originalOffsets=null,selectionAlignment=false,selectionContext='',bindingPending=false,confirmedBinding=null;
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
function sourceTableElement(u,rows,onChoose,title=''){
 const container=document.createElement('div');container.className='table-scroll';
 const table=document.createElement('table');table.className='scientific-table';
 const caption=document.createElement('caption');caption.textContent=(title?title+' · ':'')+'原文值（未经独立核查）';table.append(caption);
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
const ABBREVIATIONS=/(?:\b(?:e\.g|i\.e|vs|et al|Fig|Figs|approx|cf|No|ca|Dr|Mr|Ms|Prof))\.$/;
// A period ends a sentence only when followed by whitespace/end, and is not a
// decimal point (-1.8kg, p = 0.7) or a common scientific abbreviation.
function isSentenceEnd(raw,i){
 const ch=raw[i];if(!/[.!?]/.test(ch))return false;
 if(i+1<raw.length&&!/\s/.test(raw[i+1])&&!/["'”’)\]]/.test(raw[i+1]))return false;
 if(ch==='.'&&ABBREVIATIONS.test(raw.slice(Math.max(0,i-8),i+1)))return false;
 return true;
}
function sentenceBounds(raw,start,end){
 let s=start,e=end;
 while(s>0&&!isSentenceEnd(raw,s-1)&&raw[s-1]!=='\n')s--;
 while(s<raw.length&&/\s/.test(raw[s]))s++;
 if(!(e>0&&isSentenceEnd(raw,e-1))){while(e<raw.length&&!isSentenceEnd(raw,e)&&raw[e]!=='\n')e++;if(e<raw.length&&raw[e]!=='\n')e++;}
 return {start:s,end:Math.max(e,s+1)};
}
// Do not leave half words at the edges of a quote (e.g. "obesity were r").
function snapToWords(text,from,to){
 const word=/[\p{L}\p{N}]/u;let s=from,e=to;
 while(s>0&&word.test(text[s-1])&&word.test(text[s]))s--;
 while(e<text.length&&word.test(text[e-1])&&word.test(text[e]))e++;
 return {start:s,end:e};
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
 doc=null;clearQuoteSelection();activeLocator=null;
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
 $('units').scrollTop=0;$('modeHint').hidden=true;
 show('正在查看完整双语合成演练。此资料不能引用到正式或合成任务的科学证据链。');
}
async function load(){return scheduleReading(loadDocument);}
async function loadDocument(){try{clearQuoteSelection();$('manualQuote').open=false;window.CSS?.highlights?.delete('evidence-source');$('readerSource').hidden=true;selected=null;selectedUnit=null;selectedOffsets=null;doc=null;translationMap.clear();$('bilingualToolbar').hidden=true;$('selectionToolbar').hidden=true;pdfDoc=null;pdfjs=null;sourceURL='';$('units').replaceChildren();$('anchors').replaceChildren();$('outline').replaceChildren();$('translationVersion').textContent='';$('translationStatus').textContent='翻译未就绪';togglePDF(false);window.dispatchEvent(new CustomEvent('nutri-evidence',{detail:{items:[],bindings:[],itemBindings:[]}}));$('pdfCanvas').width=0;$('pdfOverlay').replaceChildren();$('pdfRaster').style.display='none';
 const projection=await json(`/v1/tasks/${task()}/read-model`);$('phase').textContent=window.nutriPhaseLabel?window.nutriPhaseLabel(projection.phase):projection.phase;
 if(projection.arm==='R1') {$('readerSource').value='paper'; $('readerTitle').textContent='候选证据 · 授权摘录';$('sourceTitle').textContent='R1 候选引用片段';$('readerMeta').textContent='仅限任务许可的候选证据；不提供全文与原始 PDF。';$('sourceVersion').textContent='来源权限：候选摘录';$('translationStatus').textContent='此任务不提供全文译文';$('pdfToggle').hidden=true;$('pdfDetails').hidden=true;$('query').disabled=true;$('searchBtn').disabled=true; $('sourceBadge').textContent='候选引用片段'; if(projection.phase==='EXPERT_VERIFY'){const fragments=await json(base()+'/candidate-spans'); for(const x of fragments.candidate_spans){const div=document.createElement('div');div.className='unit';div.textContent=x.quote; $('units').append(div)}show('R1：仅可见已验证的候选引用片段，不提供整篇原文/PDF');}else{show('R1 门禁：候选尚未冻结，来源不可访问。');const empty=document.createElement('div');empty.className='empty-state';empty.textContent='候选摘录尚未准备好。生产方冻结合成候选后，这里会显示需要你复核的原文片段；请稍后点击左侧“打开任务 / 重新载入”。';$('units').append(empty);}return;}
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
 $('bilingualToolbar').hidden=false;let tableTitle='';for(const u of d.units){
 const records=translationMap.get(u.unit_id)||[];
 const div=document.createElement('div');
 div.className='unit'+(u.type==='SECTION'?' section':'')+(records.length?' translated':'');
 div.dataset.uid=u.unit_id;
 if(u.type==='SECTION'){const button=document.createElement('button');button.type='button';button.dataset.uid=u.unit_id;button.textContent=plainMarkdown(u.raw).text;button.onclick=()=>scrollUnit(u.unit_id);$('outline').append(button);}
 const original=document.createElement('div');original.className='unit-original';const plain=plainMarkdown(u.raw);
 const chooseRange=(start,end)=>setQuoteSelection(u,start,end);
 const parsed=u.type==='TABLE'?parseSourceTable(u.raw):null;
 if(u.type==='SECTION'&&/^Table\s+\d+/i.test(plain.text))tableTitle=plain.text;
 if(parsed)original.append(sourceTableElement(u,parsed,chooseRange,tableTitle));
 else original.textContent=plain.text;
 div.append(original);
 for(const record of records){
   const translated=document.createElement('div');translated.className='unit-translation';
   translated.textContent=(record.alignment_level==='FULL_UNIT'?'中文段落（尚未科学审校）｜':'中文摘录（演练译文）｜')+record.translated_excerpt+
      (record.quality_warnings?.length?' · ⚠ 数字或统计信息待核查':'');
   translated.title='仅原文摘录对齐；译文未经科学审定，不代表全文或精确句子对齐';
   div.append(translated);
 }
 const foot=document.createElement('div');foot.className='unit-footer';const id=document.createElement('span');id.className='unit-id';id.textContent='原文单元 · '+u.unit_id;const cite=document.createElement('button');cite.type='button';cite.className='text-button';cite.textContent='＋ 引用此段';cite.onclick=()=>{setQuoteSelection(u,0,u.raw.length);$('selectionToolbar').hidden=true;window.dispatchEvent(new Event('nutri-confirm-quote')); };foot.append(id,cite);if(u.type!=='SECTION')div.append(foot);$('units').append(div);
}
 const sections=[...$('outline').querySelectorAll('button')];if(!sections.length)$('outline').textContent='当前来源没有章节标题';
 const first=sections.find(button=>/abstract/i.test(button.textContent))||sections[0];if(first)scrollUnit(first.dataset.uid,false);
 await listAnchors();updateModeHint();show('原文已载入，可选取文字作为证据。');await openPDF();
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
 if(bindingPending)return;
 $('evidenceFeedback').classList.remove('success');
 try{
  updateConfirmation();if($('makeAnchor').disabled)throw Error('请确认有效引文并保存具体判断');
  bindingPending=true;$('makeAnchor').disabled=true;
  if(!doc||!selectedUnit||!selected)throw Error('请先在左侧选取有明确出处的英文原文');
  if($('quote').value!==selected)throw Error('引文已修改，请重新定位后再关联');
  const target=window.nutriJudgment?.getBindingTarget?.();
  if(!target||target.legacy)throw Error('请先打开专家判断并选择具体目标条目');
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
  $('rangeValidation').textContent='原文范围：服务端已校验';
  $('targetValidation').textContent='判断关联：已关联第 '+(target.index+1)+' 条判断';
  const pdfVerified=await openAnchor(a);
  confirmedBinding={quote:selected,field:target.field,index:target.index,text:target.text,pdfVerified};
  $('quotePdfValidation').textContent='PDF 定位：'+(pdfVerified?'已核验':'待核验');
  const category=exact?`第 ${target.index+1} 条独立判断`:'当前科学字段（尚未关联到具体判断）';
  show(pdfVerified?`已通过服务端证据验证并绑定到${category}；PDF 精确定位已核验。`:
     `已通过服务端证据验证并绑定到${category}；PDF 精确定位尚未验证。请缩小引文并核查 PDF。`);
  $('evidenceFeedback').classList.add('success');
 }catch(e){show('无法创建或绑定证据：'+e.message);}
 finally{bindingPending=false;updateConfirmation();}
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
const begin=selectedUnit.raw.indexOf(q);setQuoteSelection(selectedUnit,begin,begin+q.length);
const el=document.querySelector(`[data-uid="${selectedUnit.unit_id}"]`);if(el){el.classList.add('selected');el.scrollIntoView({block:'center'});}show('已定位输入的准确引文；创建 SourceAnchor 时仍由服务端再次校验。')}
$('readerMode').addEventListener('change',()=>{ $('units').dataset.readingMode=$('readerMode').value;updateModeHint();for(const button of document.querySelectorAll('[data-mode]')){button.classList.toggle('active',button.dataset.mode===$('readerMode').value);button.setAttribute('aria-pressed',String(button.dataset.mode===$('readerMode').value));} });
for(const button of document.querySelectorAll('[data-mode]'))button.onclick=()=>{$('readerMode').value=button.dataset.mode;$('readerMode').dispatchEvent(new Event('change'));};
$('pdfToggle').onclick=()=>togglePDF(!$('pdfDetails').open);
$('pdfDetails').addEventListener('toggle',()=>{$('pdfToggle').setAttribute('aria-expanded',String($('pdfDetails').open));$('pdfToggle').textContent=$('pdfDetails').open?'返回结构化正文':'核验原始 PDF';});
$('dismissSelection').onclick=()=>{clearQuoteSelection();window.getSelection()?.removeAllRanges();};
$('selectionBind').onclick=()=>{window.nutriReader.setCiteTarget('');if(selectedOffsets)scrollUnit(selectedOffsets.unit_id,false);$('selectionToolbar').hidden=true;window.dispatchEvent(new Event('nutri-confirm-quote'));};
$('locateQuote').onclick=locateTypedQuote;
$('load').onclick=load;$('makeAnchor').onclick=makeAnchor;$('prev').onclick=()=>showPage(currentPage-1);$('next').onclick=()=>showPage(currentPage+1);
$('candidate').onclick=async()=>{try{const c=await json(`/v1/tasks/${task()}/candidate-set`);show({exposure:'AUTHORIZED',candidate_set_sha:c.candidate_set_sha})}catch(e){show('CANDIDATE DENIED: '+e.message)}};
function searchSnippet(raw,q){
 const text=plainMarkdown(raw).text.replace(/\s+/g,' '),i=text.toLowerCase().indexOf(q.toLowerCase());
 if(i<0)return text.slice(0,90)+(text.length>90?'…':'');
 const from=Math.max(0,i-40),to=Math.min(text.length,i+q.length+50);
 return (from?'…':'')+text.slice(from,to)+(to<text.length?'…':'');
}
async function runSearch(){
 const q=$('query').value.trim();$('searchResults').replaceChildren();
 if(!doc){$('searchResults').textContent='当前资料不支持搜索，请切换到“真实论文原文”。';return;}
 if(q.length<3){$('searchResults').textContent='请输入至少 3 个字符再搜索。';return;}
 try{const s=await json(base()+'/search?q='+encodeURIComponent(q));
  const count=document.createElement('p');count.className='small';count.textContent=s.results.length?`找到 ${s.results.length} 处：`:'没有匹配的授权原文';$('searchResults').append(count);
  for(const result of s.results){const unit=doc.units.find(u=>u.unit_id===result.unit_id);const button=document.createElement('button');button.type='button';button.className='search-hit';button.textContent=searchSnippet(unit?.raw||result.snippet||'',q);button.title='跳到原文单元 '+result.unit_id;button.onclick=()=>scrollUnit(result.unit_id);$('searchResults').append(button);}
 }catch(e){$('searchResults').textContent='搜索失败：'+e.message;}
}
$('searchBtn').onclick=runSearch;
$('query').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();runSearch();}});

$('readerSource').addEventListener('change',async()=>{
 const picker=$('readerSource');
 const requested=picker.value;
 picker.disabled=true;
 picker.dataset.readySource='';
 $('translationStatus').textContent='正在切换阅读资料…';$('searchResults').replaceChildren();$('query').value='';
 try{
   if(requested==='demo')await showSyntheticBilingualExercise();
   else await load();
   if(picker.value===requested)picker.dataset.readySource=requested;
 }catch(e){$('translationStatus').textContent='阅读资料无法切换：'+e.message;}
 finally{picker.disabled=false;}
});
function updateModeHint(){
 const mode=$('readerMode').value,partial=!!doc&&translationMap.size<doc.units.length;
 $('modeHint').hidden=!(partial&&mode!=='english');
 $('modeHint').textContent=`本论文只有 ${[...translationMap.values()].reduce((n,a)=>n+a.length,0)} 处演练译文，其余段落仅显示英文原文。完整中英对照请切换到“完整双语练习”。`;
}
window.nutriReader={load,updateConfirmation,refreshEvidence:()=>doc?listAnchors().catch(()=>{}):null,setCiteTarget:label=>{citeTargetLabel=label;$('citeTargetHint').hidden=!label;$('citeTargetHint').textContent=label?'正在为「'+label+'」找原文：请在下方原文中选中支撑这条判断的文字。':'';}};

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

function clearQuoteSelection(message=''){
 selected=null;selectedUnit=null;selectedOffsets=null;originalOffsets=null;confirmedBinding=null;
 $('quote').value='';$('selectionToolbar').hidden=true;
 window.CSS?.highlights?.delete('evidence-source');
 $('selectionError').textContent=message;$('selectionError').hidden=!message;
 updateConfirmation();
}
function setQuoteSelection(unit,start,end,alignment=false,context=''){
 if(!unit||!Number.isInteger(start)||!Number.isInteger(end)||end<=start||start<0||end>unit.raw.length){clearQuoteSelection('无法确认原文范围，请重新选择。');return;}
 confirmedBinding=null;selectedUnit=unit;selectedOffsets={unit_id:unit.unit_id,start,end};originalOffsets={...selectedOffsets};
 selectionAlignment=alignment;selectionContext=context;selected=unit.raw.slice(start,end);$('quote').value=selected;
 $('selectionError').hidden=true;$('selectionStatus').textContent=`已选 ${selected.length} 字符`;
 $('rangeValidation').textContent='原文范围：等待服务端校验';$('quotePdfValidation').textContent='PDF 定位：待核验';
 const el=[...$('units').querySelectorAll('[data-uid]')].find(x=>x.dataset.uid===unit.unit_id);
 if(el){highlightSourceRange(el,{...selectedOffsets,start_utf16:start,end_utf16:end,quote:selected});
 const rect=el.getBoundingClientRect(),anchorRect=selectionRect&&selectionRect.height?selectionRect:rect;selectionRect=null;
 toolbarOffset={left:anchorRect.left,below:anchorRect.bottom-rect.top,above:anchorRect.top-rect.top};
 placeToolbar(el);}
 for(const button of document.querySelectorAll('[data-quote-range]'))button.classList.toggle('active',button.dataset.quoteRange==='original');
 updateConfirmation();
}
function updateConfirmation(){
 const valid=!!doc&&!!selectedUnit&&!!selected&&$('quote').value===selected;
 $('quoteEmpty').hidden=valid;$('quoteConfirmation').hidden=!valid;
 if(valid){const shown=plainMarkdown(selected).text;$('quotePreview').textContent=shown;$('quoteMarkupNote').hidden=shown===selected;$('quoteContext').textContent=selectedUnit.raw;
 $('quoteSource').textContent=`${selectedUnit.unit_id} · ${selected.length} 字符 · 英文原文`;
 $('quoteAlignment').hidden=!selectionAlignment;$('quoteTableContext').hidden=!selectionContext;$('quoteTableContext').textContent=selectionContext;
 for(const button of document.querySelectorAll('[data-quote-range]'))button.disabled=selectedUnit.type==='TABLE'&&button.dataset.quoteRange!=='original';}
 let target=null,error='';try{target=window.nutriJudgment?.getBindingTarget?.();}catch(e){error=e.message;}
 $('targetStatement').hidden=!(target&&!target.legacy);
 $('targetStatement').textContent=target&&!target.legacy?'将关联到「'+target.label+'」：'+target.text:'';
 $('evidenceItemNotice').textContent=error||'请核对上方引文和目标判断，再确认关联。';
 const bound=valid&&target&&!target.legacy&&confirmedBinding&&confirmedBinding.quote===selected&&confirmedBinding.field===target.field&&confirmedBinding.index===target.index&&confirmedBinding.text===target.text;
 $('rangeValidation').textContent=bound?'原文范围：服务端已校验':'原文范围：等待服务端校验';
 $('targetValidation').textContent=bound?'判断关联：已关联第 '+(target.index+1)+' 条判断':target&&!target.legacy?'判断关联：已选保存的判断，等待确认':'判断关联：请先填写并保存';
 $('quotePdfValidation').textContent=bound&&confirmedBinding.pdfVerified?'PDF 定位：已核验':'PDF 定位：待核验';
 $('makeAnchor').disabled=bindingPending||!valid||!target||target.legacy||!!bound;
 $('makeAnchor').textContent=bound?'已关联 ✓':target&&!target.legacy?'确认关联到「'+target.label+'」':'确认引文并关联判断';
 $('quoteNext').hidden=!bound;
}
function captureQuoteSelection(){
 const s=window.getSelection();if(!s||s.isCollapsed||!s.rangeCount)return;
 const r=s.getRangeAt(0),element=n=>n.nodeType===1?n:n.parentElement;selectionRect=r.getBoundingClientRect();
 const a=element(r.startContainer),b=element(r.endContainer),units=$('units');
 if(!units.contains(a)&&!units.contains(b))return;
 const left=a.closest('.unit-original,.unit-translation'),right=b.closest('.unit-original,.unit-translation');
 if(!doc){s.removeAllRanges();clearQuoteSelection('当前是双语练习资料，仅供阅读练习，不能作为证据引用。请切换到“真实论文原文”后再选取。');return;}
 if(!left||left!==right){s.removeAllRanges();clearQuoteSelection('这次选区跨越段落，已清除旧引文。请在同一段或单元格内重新选择。');return;}
 const unit=doc.units.find(u=>u.unit_id===left.closest('[data-uid]')?.dataset.uid);if(!unit){clearQuoteSelection('此来源不能引用。');return;}
 if(left.classList.contains('unit-translation')){
  const records=translationMap.get(unit.unit_id)||[],nodes=[...left.parentElement.querySelectorAll('.unit-translation')];
  const record=records[nodes.indexOf(left)];s.removeAllRanges();
  if(record)setQuoteSelection(unit,record.source_start_utf16,record.source_end_utf16,true);else clearQuoteSelection();return;
 }
 const cellA=a.closest('td,th'),cellB=b.closest('td,th');
 if(cellA!==cellB){s.removeAllRanges();clearQuoteSelection('这次选区跨越表格单元格，已清除旧引文。请在一个单元格内重新选择。');return;}
 const region=cellA||left,prefix=r.cloneRange();prefix.selectNodeContents(region);prefix.setEnd(r.startContainer,r.startOffset);
 const from=prefix.toString().length,to=from+r.toString().length;let start,end,context='';
 if(cellA){start=Number(cellA.dataset.rawStart)+from;end=Number(cellA.dataset.rawStart)+to;
 const table=cellA.closest('table'),col=[...cellA.parentElement.children].indexOf(cellA);
 context=[table.caption?.textContent,cellA.parentElement.children[0]?.textContent,table.querySelector('thead tr')?.children[col]?.textContent].filter(Boolean).join(' / ');
 }else{const plain=plainMarkdown(unit.raw);const snapped=snapToWords(plain.text,from,to);start=plain.offsets[snapped.start];end=plain.offsets[snapped.end-1]+1;}
 s.removeAllRanges();setQuoteSelection(unit,start,end,false,context);
}
$('units').addEventListener('pointerup',captureQuoteSelection);
document.addEventListener('keyup',e=>{if(e.key.startsWith('Arrow')||e.key==='Shift'||(e.shiftKey&&['Home','End','PageUp','PageDown'].includes(e.key)))captureQuoteSelection();});
$('quote').addEventListener('input',()=>{if($('quote').value!==selected){selected=null;selectedOffsets=null;originalOffsets=null;$('selectionToolbar').hidden=true;window.CSS?.highlights?.delete('evidence-source');}updateConfirmation();});
let toolbarOffset=null;
// Place the citation action next to, never over, the selected words.
function placeToolbar(el){
 const toolbar=$('selectionToolbar');if(!toolbarOffset)return;
 toolbar.hidden=false;
 const top=el.getBoundingClientRect().top,height=toolbar.offsetHeight||48;
 let y=top+toolbarOffset.below+8;
 if(y+height>window.innerHeight-90)y=top+toolbarOffset.above-height-8;
 toolbar.style.left=Math.max(12,Math.min(toolbarOffset.left,window.innerWidth-(toolbar.offsetWidth||300)-12))+'px';
 toolbar.style.top=Math.max(70,Math.min(y,window.innerHeight-height-12))+'px';
}
$('units').addEventListener('scroll',()=>{
 updateOutlineActive();
 if($('selectionToolbar').hidden||!selectedUnit)return;
 const el=[...$('units').querySelectorAll('[data-uid]')].find(x=>x.dataset.uid===selectedUnit.unit_id);
 if(el)placeToolbar(el);
});
function updateOutlineActive(){
 const container=$('units'),top=container.getBoundingClientRect().top+40;let current=null;
 for(const section of container.querySelectorAll('.unit.section')){if(section.getBoundingClientRect().top<=top)current=section.dataset.uid;else break;}
 if(!current)return;
 for(const button of $('outline').querySelectorAll('button')){
  const active=button.dataset.uid===current;
  if(active&&!button.classList.contains('active'))button.scrollIntoView({block:'nearest'});
  button.classList.toggle('active',active);
 }
}
for(const button of document.querySelectorAll('[data-quote-range]'))button.onclick=()=>{
 if(!selectedUnit||!originalOffsets)return;const unit=selectedUnit,raw=unit.raw,original={...originalOffsets};
 let start=original.start,end=original.end;const mode=button.dataset.quoteRange;
 if(mode==='paragraph'){start=0;end=raw.length;}
 else if(mode==='sentence'){({start,end}=sentenceBounds(raw,start,end));}
 const alignment=selectionAlignment,context=selectionContext;setQuoteSelection(unit,start,end,alignment,context);originalOffsets=original;
 $('selectionToolbar').hidden=true;
 for(const b of document.querySelectorAll('[data-quote-range]'))b.classList.toggle('active',b===button);
 show('引用范围已更新，请核对高亮与引文后确认关联。');
};
