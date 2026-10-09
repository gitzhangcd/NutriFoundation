/* WB-EA-P1: ORIGINAL D0 single-session, three-column scientific-annotation mode.
 * Authoritative R0/R1/R2 Workbench remains separate and unmodified by this
 * opt-in synthetic evidence flow. No real source or Gold capture enabled.
 */
const $=id=>document.getElementById(id);
let active=false,pack=null,taskId='',sources=[],currentSource=null,candidates=null;
let latestQuote=null,selectionSequence=0,readerModeBefore='immersive';
const msg=s=>$('eaFeedback').textContent=s;
async function api(path,opts={}){
 const method=opts.method||'GET';
 const headers={...(opts.headers||{})};
 if(method!=='GET')headers['X-CSRF-Token']=window.nutriSession?.csrf_token||'';
 const response=await fetch(path,{...opts,headers,cache:'no-store',credentials:'same-origin'});
 const data=await response.json().catch(()=>({}));
 if(!response.ok)throw Error(data.detail?.code||data.detail||'HTTP_'+response.status);
 return data;
}
const path=(tail='')=>'/v1/ea/tasks/'+encodeURIComponent(taskId)+tail;
function node(tag,text,cls=''){
 const out=document.createElement(tag);if(text!==undefined)out.textContent=text;
 if(cls)out.className=cls;return out;
}
async function hashText(v){
 const h=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(v));
 return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('');
}
function resetQuote(){
 latestQuote=null;selectionSequence++;$('eaQuoteStatus').textContent='在左侧原文单元内选中文字，再关联到右侧某一条候选。';
}
async function onQuote(x){
 if(!active||!currentSource)return;
 if(x.document_id!==currentSource.source_id||x.revision_id!==currentSource.revision_id)return;
 const request=++selectionSequence;
 const sum=await hashText(x.source_quote);
 if(request!==selectionSequence||!active)return;
 latestQuote={source_id:currentSource.source_id,revision_id:currentSource.revision_id,
  canonical_document_sha256:currentSource.canonical_document_sha256,
  unit_id:x.unit_id,start_utf16:x.start_utf16,end_utf16:x.end_utf16,
  source_quote:x.source_quote,source_quote_sha256:sum,
  pdf_locator:{status:'UNRESOLVED'}};
 $('eaQuoteStatus').textContent='已选原文 '+currentSource.source_id+':'+currentSource.revision_id+
    ' / '+x.unit_id+'，'+x.source_quote.length+' 字符；绑定后由服务端最终核验。';
}
async function loadSource(s){
 resetQuote();currentSource=null;
 await window.nutriReader.loadEvidenceSource(s);
 currentSource=s;
 $('eaSource').value=s.source_id+':'+s.revision_id;
}
function buildGroups(){
 $('eaGroups').replaceChildren();
 const title=node('p','当前科学来源类型：'+pack.source_type+'，协议：'+pack.profile_id,'small');
 $('eaGroups').append(title);
 const list=node('div',undefined,'ea-profile-groups');
 for(const name of pack.required_groups){
  const item=node('span',name.replaceAll('_',' '),'ea-profile-group');list.append(item);
 }
 $('eaGroups').append(list);
}
function showCandidates(){
 $('eaCandidates').replaceChildren();
 for(const c of candidates.items){
  const box=node('div',undefined,'candidate-card ea-candidate');box.dataset.candidate=c.candidate_id;
  box.reviewAnchors=[];
  box.append(node('h4',c.field_group+' · '+c.target_canonical_object_type));
  box.append(node('p',JSON.stringify(c.candidate_payload),'small'));
  box.append(node('p','候选引用：'+c.original_anchors.length+' 条；原始 Agent/Producer 候选仅供审核','small'));
  const disposition=node('select');disposition.className='ea-disposition';
  for(const [v,t] of [['','选择审核结论'],['ACCEPT','接受'],['MODIFY','修改'],
      ['REJECT','拒绝'],['NEEDS_MORE_EVIDENCE','证据不足'],['IRRELEVANT','不相关'],['UNCERTAIN','不确定']]){
   const option=node('option',t);option.value=v;disposition.append(option);
  }
  const dispositionLabel=node('label','审核结论');dispositionLabel.append(disposition);box.append(dispositionLabel);
  const support=node('select');support.className='ea-support';
  for(const [v,t] of [['','原文支持程度'],['SUPPORTED','支持'],['PARTIAL','部分支持'],
      ['UNSUPPORTED','不支持'],['NOT_VERIFIED','尚未核验']]){
   const opt=node('option',t);opt.value=v;support.append(opt);
  }
  const supportLabel=node('label','证据支持度');supportLabel.append(support);box.append(supportLabel);
  const bind=node('button','＋ 将当前选中原文关联此条候选','ghost mini');bind.type='button';
  const status=node('p','尚未添加专家新引文','small');
  bind.onclick=()=>{
   if(!latestQuote){msg('请先在左侧原文选取文字，或点击引用此段。');return}
   if(!box.reviewAnchors.some(a=>a.source_id===latestQuote.source_id&&
      a.unit_id===latestQuote.unit_id&&a.start_utf16===latestQuote.start_utf16&&
      a.end_utf16===latestQuote.end_utf16)){
    box.reviewAnchors.push(structuredClone(latestQuote));
   }
   status.textContent='已绑定 '+box.reviewAnchors.length+' 条待服务器核验的原文引文';
  };
  box.append(bind,status);
  const reason=node('textarea');reason.className='ea-reason';reason.rows=2;
  reason.placeholder='说明依据、限制、不确定性或拒绝理由';
  const reasonLabel=node('label','专家理由');reasonLabel.append(reason);box.append(reasonLabel);
  const correction=node('textarea');correction.className='ea-correction';correction.rows=2;
  correction.placeholder='仅 MODIFY 需要：{"statement":"修订后原话"}';
  const correctionLabel=node('label','修订候选 JSON（可留空，除非 MODIFY）');
  correctionLabel.append(correction);box.append(correctionLabel);
  $('eaCandidates').append(box);
 }
}
async function openTask(){
 taskId=$('eaTask').value;
 if(!active||!taskId)return;
 latestQuote=null;currentSource=null;candidates=null;
 $('eaFreeze').disabled=true;$('eaReceipt').textContent='';
 pack=await api(path('/workpack'));
 const sourcePack=await api(path('/sources'));sources=sourcePack.sources;
 $('eaProfile').textContent=pack.profile_id+' · '+pack.workflow+' · '+pack.state+
    ' · '+sources.length+' 个获授权来源版本';
 buildGroups();
 $('eaSource').replaceChildren();
 for(const s of sources){
  const option=node('option',s.title+' · '+s.source_id+':'+s.revision_id);
  option.value=s.source_id+':'+s.revision_id;$('eaSource').append(option);
 }
 if(sources.length)await loadSource(sources[0]);
 $('eaCandidates').replaceChildren();$('eaIndependent').hidden=true;
 if(pack.workflow==='HUMAN_INDEPENDENT'){
  $('eaIndependent').hidden=false;
  $('eaFreeze').disabled=pack.state!=='REGISTERED';
  msg('独立标注模式：不返回任何 Agent 候选；引用为合成原文。');
 }else if(pack.state==='CANDIDATE_FROZEN'){
  candidates=await api(path('/candidates'));showCandidates();
  $('eaFreeze').disabled=false;
  msg('候选已冻结 '+candidates.content_sha256.slice(0,16)+'…；逐条复核后提交。');
 }else if(pack.state==='EXPERT_REVIEW_FROZEN'){
  const receipt=await api(path('/export'));$('eaReceipt').textContent=JSON.stringify(receipt,null,2);
  msg('此专家审核已冻结，不能覆盖或重复提交。');
 }else msg('等待 Producer 的冻结候选；不能开始复核。');
}
async function switchMode(){
 if(!$('eaModeBox')||$('eaModeBox').hidden)return;
 active=!active;window.nutriEvidence.active=active;
 document.body.classList.toggle('ea-mode',active);
 $('eaModeBtn').setAttribute('aria-pressed',String(active));
 $('eaModeBtn').textContent=active?'← 返回 NDS-R1 独立决策工作台':'切换到科学证据标注';
 $('eaTaskBox').hidden=!active;$('eaReview').hidden=!active;
 $('expertPanel').classList.remove('reviewing','evidence-open');
 $('reviewPane').hidden=true;$('evidencePane').hidden=true;
 $('judgmentTitle').textContent=active?'科学来源证据审查':'我的独立判断';
 if(active){
  readerModeBefore=$('readerMode').value;
  $('workflowNav').hidden=true;$('workFooter').hidden=true;
  const tasks=await api('/v1/ea/tasks');$('eaTask').replaceChildren();
  for(const t of tasks.tasks){
   const o=node('option',t.task_id+' · '+t.source_type+' · '+t.state);
   o.value=t.task_id;$('eaTask').append(o);
  }
  if(tasks.tasks.length)await openTask();else msg('当前账号没有分配的合成证据审核任务。');
 }else{
  resetQuote();pack=null;taskId='';sources=[];currentSource=null;candidates=null;
  $('readerMode').value=readerModeBefore;
  $('readerMode').dispatchEvent(new Event('change')); // Restore original bilingual presentation state.
  $('load').click(); // The ORIGINAL load path restores R0/R1/R2 and PDF/bilingual reader.
 }
}
async function freeze(){
 if(!active||!pack||!taskId)return;
 if(!$('eaFreeze').disabled && !window.confirm('冻结后不可修改。确认提交此合成证据审核？'))return;
 try{
  let items,expected=null;
  if(pack.workflow==='HUMAN_INDEPENDENT'){
   const text=$('eaStatement').value.trim();
   if(!text){msg('请输入独立判断，允许注明不确定性。');return}
   items=[{statement:text,original_anchors:latestQuote?[latestQuote]:[]}];
  }else{
   if(!candidates)throw Error('AGENT_CANDIDATES_NOT_FROZEN');
   expected=candidates.content_sha256;items=[];
   for(const card of $('eaCandidates').querySelectorAll('.ea-candidate')){
    const decision=card.querySelector('.ea-disposition').value;
    const support=card.querySelector('.ea-support').value;
    const c=candidates.items.find(x=>x.candidate_id===card.dataset.candidate);
    if(!decision||!support)throw Error('请先填写每一条候选的审核结论与支持度');
    const item={candidate_id:c.candidate_id,field_group:c.field_group,
      disposition:decision,source_support_status:support,
      reason:card.querySelector('.ea-reason').value.trim(),
      expert_anchors:card.reviewAnchors};
    if(decision==='MODIFY'){
     try{item.corrected_candidate_payload=JSON.parse(card.querySelector('.ea-correction').value)}
     catch(_){throw Error('修改候选时，必须提供有效 JSON')}
    }
    items.push(item);
   }
  }
  const result=await api(path('/review/freeze'),{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({items,candidate_set_digest:expected})});
  $('eaFreeze').disabled=true;$('eaReceipt').textContent=JSON.stringify(result,null,2);
  msg('审核已冻结：'+result.content_sha256+' · 工程合成，不可晋级 Gold。');
 }catch(e){msg('冻结失败：'+e.message)}
}
function reset(){
 active=false;window.nutriEvidence.active=false;
 document.body.classList.remove('ea-mode');
 $('eaModeBox').hidden=true;$('eaTaskBox').hidden=true;$('eaReview').hidden=true;
 $('eaModeBtn').textContent='切换到科学证据标注';
 $('eaModeBtn').setAttribute('aria-pressed','false');
 taskId='';pack=null;sources=[];currentSource=null;candidates=null;resetQuote();
}
window.nutriEvidence={active:false,api,
 onQuote,readSource:s=>api(path('/sources/'+encodeURIComponent(s.source_id)+'/'+encodeURIComponent(s.revision_id))),
 reset};
window.addEventListener('nutri-session-start',e=>{
 reset();
 if(e.detail.role==='expert')$('eaModeBox').hidden=false;
});
$('eaModeBtn').onclick=()=>switchMode().catch(e=>msg('切换证据模式失败：'+e.message));
$('eaLoad').onclick=()=>openTask().catch(e=>msg('加载失败：'+e.message));
$('eaSource').onchange=()=>{
 const s=sources.find(x=>x.source_id+':'+x.revision_id===$('eaSource').value);
 if(s)loadSource(s).catch(e=>msg('来源拒绝：'+e.message));
};
$('eaFreeze').onclick=freeze;
