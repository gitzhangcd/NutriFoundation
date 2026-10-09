/* WB-EA-P1: separate synthetic-only research annotation workbench. */
const el=id=>document.getElementById(id);
let token='',task='',pack=null,sources=[],current=null,candidates=null,selectedAnchor=null;
const msg=text=>el('message').textContent=text;
async function api(path,options={}){
 const r=await fetch(path,{cache:'no-store',...options,headers:{'X-EA-Token':token,...(options.headers||{})}});
 const data=await r.json().catch(()=>({}));
 if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:'HTTP_'+r.status);
 return data;
}
async function sha(text){
 const d=new TextEncoder().encode(text),h=await crypto.subtle.digest('SHA-256',d);
 return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('');
}
function elem(tag,text,cls=''){
 const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;
}
async function connect(){
 token=el('token').value.trim();
 if(!token){msg('必须输入本地测试 Token');return}
 try{
  const list=await api('/v1/ea/tasks');el('task').replaceChildren();
  for(const t of list.tasks){const o=elem('option',t.task_id+' · '+t.state);o.value=t.task_id;el('task').append(o)}
  msg('认证成功：当前可见 '+list.tasks.length+' 个工程任务');
  if(list.tasks.length)await openTask();
 }catch(e){token='';msg('认证或任务读取失败：'+e.message)}
}
el('connect').onclick=connect;
el('openTask').onclick=()=>openTask().catch(e=>msg('打开任务失败：'+e.message));
async function openTask(){
 task=el('task').value;if(!task){msg('没有授权任务');return}
 current=null;selectedAnchor=null;candidates=null;el('sources').replaceChildren();
 el('groups').replaceChildren();el('readerUnits').replaceChildren();el('candidates').replaceChildren();
 el('evidenceQuote').textContent='尚未选取';el('freeze').disabled=true;el('independent').hidden=true;
 const root='/v1/ea/tasks/'+encodeURIComponent(task);
 pack=await api(root+'/workpack');
 const d=await api(root+'/sources');sources=d.sources;
 el('phase').textContent=pack.state;
 el('taskState').textContent=pack.profile_id+' · '+pack.workflow;
 el('profileName').textContent=pack.profile_id;
 el('profileInfo').textContent=pack.source_type+' · '+pack.required_groups.length+' 组专业字段 · '+d.source_count+' 个授权来源版本';
 for(const s of sources){
  const card=elem('div',undefined,'source-item');
  card.dataset.source=s.source_id;card.dataset.revision=s.revision_id;
  card.append(elem('b',s.title),elem('div',s.source_type+' · '+s.source_id+':'+s.revision_id,'small'),
              elem('div','canonical SHA256 '+s.canonical_document_sha256.slice(0,14)+'…','small'));
  card.onclick=()=>openSource(s).catch(e=>msg('来源读取失败：'+e.message));el('sources').append(card);
 }
 for(const name of pack.required_groups){
  const block=elem('div',undefined,'group');
  block.append(elem('b',name.replaceAll('_',' ')),elem('span','依照当前来源类型专用 Profile 审查，不是 NDS 决策字段。','small'));
  el('groups').append(block);
 }
 if(sources.length)await openSource(sources[0]);
 if(pack.workflow==='HUMAN_INDEPENDENT'){
  el('independent').hidden=false;el('candidateDigest').textContent='严格盲法：禁止读取 Agent 候选';
  el('freeze').disabled=pack.state!=='REGISTERED';
 }else if(pack.state==='CANDIDATE_FROZEN'){
  candidates=await api(root+'/candidates');
  el('candidateDigest').textContent='候选集 SHA '+candidates.content_sha256.slice(0,16)+'…';
  showCandidates();el('freeze').disabled=false;
 }else{
  el('candidateDigest').textContent='当前无可见的冻结候选';
  if(pack.state==='EXPERT_REVIEW_FROZEN'){
   try{const exp=await api(root+'/export');msg('已冻结；Review SHA '+exp.review.content_sha256)}catch(e){}
  }
 }
 if(pack.state!=='EXPERT_REVIEW_FROZEN')msg('已加载 '+d.source_count+' 个授权资料版本 · '+pack.profile_id+' · 合成工程演练');
}
async function openSource(s){
 const root='/v1/ea/tasks/'+encodeURIComponent(task);
 const data=await api(root+'/sources/'+encodeURIComponent(s.source_id)+'/'+encodeURIComponent(s.revision_id));
 if(data.canonical_document_sha256!==s.canonical_document_sha256)throw Error('CANONICAL_SHA_MISMATCH');
 current=data;selectedAnchor=null;el('evidenceQuote').textContent='尚未选取';
 el('docTitle').textContent=data.title;el('docMeta').textContent=data.source_type+' · '+data.source_id+':'+data.revision_id+' · '+data.units.length+' 原文单元 · 合成 fixture';
 el('readerUnits').replaceChildren();
 for(const u of data.units){
  const box=elem('div',undefined,'unit');box.dataset.unit=u.unit_id;
  box.append(elem('div',u.unit_id,'unit-id'),elem('div',u.text,'unit-text'));
  el('readerUnits').append(box);
 }
 for(const x of el('sources').querySelectorAll('.source-item'))
  x.classList.toggle('current',x.dataset.source===s.source_id&&x.dataset.revision===s.revision_id);
}
el('readerUnits').addEventListener('pointerup',async()=>{
 try{
  const s=window.getSelection();if(!s||s.isCollapsed||s.rangeCount!==1||!current)return;
  const r=s.getRangeAt(0),a=r.startContainer,b=r.endContainer;
  if(a!==b||a.nodeType!==Node.TEXT_NODE||!a.parentElement.classList.contains('unit-text'))return;
  const parent=a.parentElement.closest('.unit');
  if(!parent||!el('readerUnits').contains(parent))return;
  const text=String(a.nodeValue),start=r.startOffset,end=r.endOffset,quote=text.slice(start,end);
  if(!quote.trim())return;
  selectedAnchor={source_id:current.source_id,revision_id:current.revision_id,
   canonical_document_sha256:current.canonical_document_sha256,
   unit_id:parent.dataset.unit,start_utf16:start,end_utf16:end,
   source_quote:quote,source_quote_sha256:await sha(quote),pdf_locator:{status:'UNRESOLVED'}};
  el('evidenceQuote').textContent=quote;
  el('anchorStatus').textContent='来源 '+current.source_id+':'+current.revision_id+' / '+parent.dataset.unit+' / '+start+'–'+end+'；提交时将由服务端验证';
  for(const x of el('readerUnits').querySelectorAll('.unit'))x.classList.toggle('selected',x===parent);
 }catch(e){msg('选区不能作为证据：'+e.message)}
});
function showCandidates(){
 el('candidates').replaceChildren();
 for(const c of candidates.items){
  const box=elem('div',undefined,'candidate');box.dataset.candidate=c.candidate_id;
  box.append(elem('h3',c.candidate_id),elem('div',c.target_canonical_object_type+' · '+c.field_group,'small'));
  box.append(elem('blockquote',JSON.stringify(c.candidate_payload,null,2)));
  box.append(elem('p','可追溯原文锚点 '+c.original_anchors.length+' 条 · '+c.source_ref.source_id,'small'));
  const label=elem('label','专家审核结论'),choices=elem('select');choices.className='disposition';
  for(const pair of [['','请选择…'],['ACCEPT','接受'],['MODIFY','修改后接受'],['REJECT','拒绝'],
                    ['NEEDS_MORE_EVIDENCE','需要更多证据'],['IRRELEVANT','无关'],['UNCERTAIN','无法确定']]){
   const option=elem('option',pair[1]);option.value=pair[0];choices.append(option);
  }
  label.append(choices);
  const supportLabel=elem('label','原文是否支持当前候选？');
  const support=elem('select');support.className='source-support';
  for(const pair of [['','请选择证据支持度…'],['SUPPORTED','充分支持'],['PARTIAL','部分支持，需限定'],
                     ['UNSUPPORTED','不支持'],['NOT_VERIFIED','未核实']]){
   const option=elem('option',pair[1]);option.value=pair[0];support.append(option);
  }
  supportLabel.append(support);
  const bind=elem('button','＋ 将当前原文选区绑定到此候选');bind.type='button';
  const linked=elem('span',' 尚未添加专家新引文','small');
  box.reviewAnchors=[];
  bind.onclick=()=>{
   if(!selectedAnchor){msg('请先在左侧结构化原文中选择段落内文字');return}
   if(!box.reviewAnchors.some(a=>a.source_id===selectedAnchor.source_id&&a.revision_id===selectedAnchor.revision_id
      &&a.unit_id===selectedAnchor.unit_id&&a.start_utf16===selectedAnchor.start_utf16
      &&a.end_utf16===selectedAnchor.end_utf16)){
     box.reviewAnchors.push(structuredClone(selectedAnchor));
   }
   linked.textContent=' 已添加 '+box.reviewAnchors.length+' 条专家引文（冻结前由服务端校验）';
  };
  const rl=elem('label','理由（拒绝或修改时必须填写）'),reason=elem('textarea');
  reason.className='reason';reason.placeholder='专家原话及不确定性';rl.append(reason);
  const cl=elem('label','修订后候选 JSON（仅 MODIFY 时填写）'),corr=elem('textarea');
  corr.className='correction';corr.placeholder='{"corrected_statement":"..."}';cl.append(corr);
  box.append(label,supportLabel,bind,linked,rl,cl);el('candidates').append(box);
 }
}
el('freeze').onclick=async()=>{
 if(!task||!pack)return;
 try{
  if(!window.confirm('冻结后不能修改。确认提交当前合成工程专家判断？'))return;
  let body;
  if(pack.workflow==='HUMAN_INDEPENDENT'){
   const value=el('independentStatement').value.trim();if(!value){msg('请先填写独立判断');return}
   const item={statement:value};if(selectedAnchor)item.original_anchors=[selectedAnchor];
   body={items:[item]};
  }else{
   if(!candidates)throw Error('AGENT_CANDIDATES_NOT_FROZEN');
   const items=[];
   for(const box of el('candidates').querySelectorAll('.candidate')){
    const decision=box.querySelector('.disposition').value;
    if(!decision)throw Error('候选 '+box.dataset.candidate+' 尚未判断');
    const support=box.querySelector('.source-support').value;
    if(!support)throw Error('候选 '+box.dataset.candidate+' 尚未评价证据支持度');
    const original=candidates.items.find(c=>c.candidate_id===box.dataset.candidate);
    const entry={candidate_id:box.dataset.candidate,disposition:decision,
                 field_group:original.field_group,source_support_status:support,
                 expert_anchors:box.reviewAnchors,
                 reason:box.querySelector('.reason').value.trim()};
    if(decision==='MODIFY'){
     try{entry.corrected_candidate_payload=JSON.parse(box.querySelector('.correction').value)}
     catch(_){throw Error('MODIFY 需要合法的修订 JSON')}
    }
    items.push(entry);
   }
   body={items,candidate_set_digest:candidates.content_sha256};
  }
  const result=await api('/v1/ea/tasks/'+encodeURIComponent(task)+'/review/freeze',
      {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  el('freeze').disabled=true;el('phase').textContent='EXPERT_REVIEW_FROZEN';
  msg('服务器已冻结不可变复核记录。\nSHA256：'+result.content_sha256+
      '\n状态：NOT_ELIGIBLE_FOR_GOLD / NOT_SCIENTIFIC_CAPTURE');
 }catch(e){msg('冻结失败：'+e.message)}
};
