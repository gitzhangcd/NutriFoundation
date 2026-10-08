// WB-P0.2-C1: real source reader + synthetic research exercise, durable server-side drafts.
// No Agent candidates and no scientific freeze exposed by this frontend or server.
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const get = (d,path) => path.split('.').reduce((o,k)=>o?.[k],d);
const put = (d,path,v) => {let a=path.split('.');let p=d;while(a.length>1)p=p[a.shift()];p[a[0]]=v};
const state={task:'DEMO-R2-PREAI',stage:0,mode:'structured',doc:null,profile:null,draft:null,anchors:[],activeField:'decision_focus',dirty:false,saving:false,saveTimer:0,selectedUnit:null,changeSeq:0};
window.doc = null;
const status=(message,error=false)=>{const el=$('#message');el.textContent=message;el.classList.toggle('error',error)};
async function api(path,opts={}){const r=await fetch(path,{...opts,headers:{...(opts.body?{'Content-Type':'application/json'}:{}),...opts.headers}});let body=await r.json().catch(()=>({detail:'UNKNOWN_RESPONSE'}));if(!r.ok){const e=new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail));e.status=r.status;throw e}return body}
function currentIdentity(){return {document_id:state.doc.document_id,canonical_revision:state.doc.revision,source_pdf_sha256:state.doc.source_pdf_sha256}}
function getFields(){return state.profile.field_groups.flatMap(g=>g.fields)}
function showSave(label){$('#saveState').textContent=label}
async function load(){
 state.profile=await api('/api/profile');state.doc=await api('/reader/api/document');if(!state.doc.document_id)throw Error('缺少真实论文来源包：请先运行 --demo-source');
 window.doc=state.doc;
 state.anchors=await api('/reader/api/anchors');
 state.draft=await api(`/api/tasks/${state.task}/draft`);
 state.dirty=false;renderDoc();renderStages();renderFields();renderRail();showSave(`服务器版本 ${state.draft.revision} · 已同步`);status('真实公开论文已导入；当前任务与判断均为合成工程数据。')
}
function renderDoc(){const d=$('#documentPanel');let filter=$('#unitSearch').value.trim().toLowerCase();d.innerHTML=state.doc.units.filter(u=>!filter||u.raw.toLowerCase().includes(filter)).map(u=>`<article class="unit" id="unit-${esc(u.unit_id)}" data-unit-id="${esc(u.unit_id)}" data-raw-sha="${esc(u.raw_sha256)}"><div class="technical">${esc(u.unit_id)} · ${esc(u.type)} ${u.pdf_page_hint?' · page hint '+esc(u.pdf_page_hint):''}</div>${u.html.replaceAll('src="assets/','src="/reader/assets/')}</article>`).join('')||'<p>没有匹配的段落。</p>';
 $('#sourceStatus').textContent=`${state.doc.unit_count} units · PDF ${state.doc.source_pages} pages`;
}
function renderStages(){const d=$('#stageList');d.innerHTML=state.profile.field_groups.map((g,i)=>`<button data-stage="${i}" class="${state.stage===i?'active':''}" title="${esc(g.title)}">${String(i+1).padStart(2,'0')}</button>`).join('')}
function editField(f){let value=get(state.draft.payload,f.key), id='field-'+f.key.replace(/[^a-z_]/g,'-');let isNumber=f.type.includes('number')||f.type.includes('integer');let val=Array.isArray(value)?value.join('\n'):value??'';
 return `<div class="field"><label for="${esc(id)}">${esc(f.label)}</label>${isNumber?`<input id="${esc(id)}" type="number" data-field="${esc(f.key)}" data-type="${esc(f.type)}" min="0" step="${f.type==='nonnegative_integer'?'1':'any'}" value="${esc(val)}">`:`<textarea id="${esc(id)}" data-field="${esc(f.key)}" data-type="${esc(f.type)}" rows="${f.type==='nullable_string'?3:4}" placeholder="允许未知或保持空白；不猜测证据未提供的信息">${esc(val)}</textarea>`}<p class="binding-hint">已关联 ${state.draft.bindings[f.key]?.length||0} 条 SourceAnchor · <button type="button" class="btn" data-focus-field="${esc(f.key)}">设为锚点目标</button></p></div>`}
function renderFields(){const g=state.profile.field_groups[state.stage];$('#stageBody').innerHTML=`<div class="tiny muted">阶段 ${state.stage+1} / 5 · R0/R2 v0.2 字段映射 · 仅合成草稿</div><h2>${esc(g.title)}</h2><p class="muted tiny">${esc(g.description)}</p>${g.fields.map(editField).join('')}${state.stage===4?'<div class="notice">本阶段只可保存草稿和工程导出；不提供正式冻结、资格绑定或 Agent 解锁。</div>':''}`;$('#revisionText').textContent=`rev ${state.draft.revision}`}
function renderRail(){const choice=$('#bindField');const fields=getFields();choice.innerHTML=fields.map(f=>`<option value="${esc(f.key)}" ${f.key===state.activeField?'selected':''}>${esc(f.label)}</option>`).join('');
 $('#anchorCount').textContent=String(state.anchors.length);$('#anchorList').innerHTML=state.anchors.map(a=>`<div class="c1-anchor" data-anchor="${esc(a.anchor_id)}"><span class="badge">${esc(a.pdf_location_kind)}</span><span class="quote">${esc(a.quote)}</span><div class="tiny muted">${esc(a.unit_id)} · ${esc(a.anchor_id)}</div><div class="actions"><button class="btn" data-bind="${esc(a.anchor_id)}">关联到字段</button><button class="btn" data-open-pdf="${esc(a.anchor_id)}">PDF 定位</button><button class="btn" data-replay="${esc(a.anchor_id)}">返回正文</button></div></div>`).join('')||'<p class="muted" style="padding:15px">请在左侧选取原文句子，创建第一个来源锚点。</p>';
 $('#sourceMeta').textContent=`PDF SHA ${state.doc.source_pdf_sha256.slice(0,15)}… · ${state.doc.revision} · BBox 为独立验证层`}
function updateLocal(){state.changeSeq++;state.dirty=true;showSave(`未保存修改 · server rev ${state.draft.revision}`);clearTimeout(state.saveTimer);state.saveTimer=setTimeout(()=>saveDraft().catch(e=>status(e.message,true)),1700)}
function parseInput(el){if(el.dataset.type==='ordered_string_list')return el.value.split('\n').map(s=>s.trim()).filter(Boolean);if(el.dataset.type==='nullable_nonnegative_number')return el.value.trim()?Number(el.value):null;if(el.dataset.type==='nonnegative_integer')return el.value.trim()?Number(el.value):0;return el.value.trim()||null}
function onInput(e){const el=e.target;if(!el.dataset.field)return;const v=parseInput(el);if(typeof v==='number'&&(!Number.isFinite(v)||v<0||el.dataset.type==='nonnegative_integer'&&!Number.isInteger(v))){status('无效的数字输入',true);return}put(state.draft.payload,el.dataset.field,v);state.activeField=el.dataset.field;$('#bindField').value=state.activeField;updateLocal()}
async function saveDraft(){
 if(state.saving)return;
 clearTimeout(state.saveTimer);
 if(!state.dirty)return;
 state.saving=true;const savedSeq=state.changeSeq;showSave('正在保存到服务器…');
 try{
  const body={expected_revision:state.draft.revision,...currentIdentity(),payload:state.draft.payload,bindings:state.draft.bindings};
  const saved=await api(`/api/tasks/${state.task}/draft`,{method:'PUT',body:JSON.stringify(body)});
  if(state.changeSeq===savedSeq){state.draft=saved;state.dirty=false;showSave(`已保存 · server rev ${saved.revision}`)}else{state.draft.revision=saved.revision;state.dirty=true;showSave(`有新修改待保存 · server rev ${saved.revision}`);clearTimeout(state.saveTimer);state.saveTimer=setTimeout(()=>saveDraft().catch(handleError),500)}$('#revisionText').textContent=`rev ${saved.revision}`;
 }catch(e){showSave(e.status===409?'保存冲突 · 点击刷新草稿':'保存失败');status(`保存失败：${e.message}。没有自动覆盖服务器记录。`,true);throw e}finally{state.saving=false}
}
async function createAnchor(){const sel=window.getSelection();const quote=sel?.toString().trim();if(!quote)throw Error('先在结构化正文中选中一句话');const element=sel.anchorNode?.parentElement?.closest('[data-unit-id]');if(!element || !element.contains(sel.focusNode))throw Error('请选择同一个段落中的句子');const unit=state.doc.units.find(x=>x.unit_id===element.dataset.unitId);if(!unit)throw Error('未知 DocumentUnit');const first=unit.raw.indexOf(quote);if(first<0 || unit.raw.indexOf(quote,first+1)!==-1)throw Error('选中文字不能唯一对应 Markdown 原始字符，请选择完整连续句子');
 const anchor=await api('/reader/api/anchors',{method:'POST',body:JSON.stringify({unit_id:unit.unit_id,quote,start_utf16:first,end_utf16:first+quote.length,expected_revision:state.doc.revision,expected_source_markdown_sha256:state.doc.source_markdown_sha256})});
 if(!state.anchors.some(a=>a.anchor_id===anchor.anchor_id))state.anchors.push(anchor);renderRail();status('SourceAnchor 已在后端核实保存。请点击“关联到字段”建立草稿关联。');return anchor;
}
function bind(anchorId){let list=state.draft.bindings[state.activeField]??=[];if(!list.includes(anchorId)){state.draft.bindings[state.activeField]=[...list,anchorId];updateLocal();renderFields()}status(`已关联 ${anchorId} → ${state.activeField}。请保存草稿。`)}
function scrollUnit(a){switchReader('structured');renderDoc();const t=$(`#unit-${a.unit_id}`);if(t){t.classList.add('selected');t.scrollIntoView({block:'center',behavior:'smooth'})}status(`已返回原文：${a.unit_id} · ${a.quote.slice(0,64)}`)}
function switchReader(target){state.mode=target;$('#documentPanel').style.display=target==='structured'?'block':'none';$('#pdfPanel').style.display=target==='pdf'?'block':'none';$('#tabText').classList.toggle('active',target==='structured');$('#tabPdf').classList.toggle('active',target==='pdf');if(target==='pdf')WBPDF.showPage(Number($('#pdfPage').value)||1)}
async function openPDF(anchorId){const a=state.anchors.find(x=>x.anchor_id===anchorId);if(!a)throw Error('找不到 SourceAnchor');let locator;
 try{locator=await api(`/reader/api/locators/${anchorId}`)}catch(e){if(e.status!==404)throw e;locator=await api(`/reader/api/locators/${anchorId}/resolve`,{method:'POST',body:JSON.stringify({expected_revision:state.doc.revision,expected_source_pdf_sha256:state.doc.source_pdf_sha256})})}
 switchReader('pdf');await WBPDF.showPage(locator.pdf_locator.page,locator);status(`PDF 原件文字已验证：第 ${locator.pdf_locator.page} 页。点击黄色高亮回到结构化正文。`)
}
window.replayToStructured=function(anchorId){const a=state.anchors.find(x=>x.anchor_id===anchorId);if(a)scrollUnit(a)};
function download(obj,name){const b=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'});const a=document.createElement('a');a.download=name;a.href=URL.createObjectURL(b);a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500)}
async function switchTask(t){if(state.dirty)await saveDraft();state.task=t;state.stage=0;await load()}
function handleError(e){status(e.message||String(e),true)}
document.addEventListener('input',onInput);
document.addEventListener('focusin',e=>{if(e.target.dataset.field){state.activeField=e.target.dataset.field;$('#bindField').value=state.activeField}});
document.addEventListener('click',e=>{const btn=e.target.closest('button');if(!btn)return;(async()=>{
 if(btn.dataset.stage!==undefined){if(state.dirty)await saveDraft();state.stage=Number(btn.dataset.stage);renderStages();renderFields()}
 else if(btn.dataset.focusField){state.activeField=btn.dataset.focusField;$('#bindField').value=state.activeField;status('目标字段已更新')}
 else if(btn.dataset.bind)bind(btn.dataset.bind);
 else if(btn.dataset.openPdf)await openPDF(btn.dataset.openPdf);
 else if(btn.dataset.replay){let a=state.anchors.find(x=>x.anchor_id===btn.dataset.replay);if(a)scrollUnit(a)}
 else if(btn.id==='makeAnchorBtn')await createAnchor();
 else if(btn.id==='tabText')switchReader('structured');
 else if(btn.id==='tabPdf')switchReader('pdf');
 else if(btn.id==='saveBtn'){await saveDraft();status('服务器已保存当前模拟草稿（不产生任何正式判断快照）。')}
 else if(btn.id==='reloadBtn'){await load();status('从服务器重新载入已保存草稿')}
 else if(btn.id==='exportBtn'){if(state.dirty)await saveDraft();download(await api(`/api/tasks/${state.task}/export`),`C1_SYNTHETIC_${state.task}.json`)}
 else if(btn.id==='nextStage'||btn.id==='prevStage'){if(state.dirty)await saveDraft();state.stage=Math.min(4,Math.max(0,state.stage+(btn.id==='nextStage'?1:-1)));renderStages();renderFields()}
 else if(btn.id==='pdfPrev')await WBPDF.showPage((Number($('#pdfPage').value)||1)-1);
 else if(btn.id==='pdfNext')await WBPDF.showPage((Number($('#pdfPage').value)||1)+1);
 else if(btn.id==='zoomIn')WBPDF.zoomBy(.2);
 else if(btn.id==='zoomOut')WBPDF.zoomBy(-.2);
 else if(btn.id==='backBtn')$('#workspace-link').click();
 })().catch(handleError)});
$('#unitSearch').addEventListener('input',renderDoc);
$('#bindField').addEventListener('change',e=>{state.activeField=e.target.value});
$('#taskSelector').addEventListener('change',e=>switchTask(e.target.value).catch(handleError));
$('#pdfPage').addEventListener('change',e=>WBPDF.showPage(Number(e.target.value)).catch(handleError));
$('#provenance-link').addEventListener('click',()=>{$('#workspace').hidden=true;$('#provenance').hidden=false});
$('#workspace-link').addEventListener('click',()=>{$('#workspace').hidden=false;$('#provenance').hidden=true});
try{await load()}catch(e){handleError(e)}