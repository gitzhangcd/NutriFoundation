/* WB-P1.1-B2: existing EA fixture attestation only, no Agent execution. */
(()=>{
'use strict';
const el=(tag,value,cls)=>{
  const x=document.createElement(tag);
  if(value!==undefined)x.textContent=String(value);
  if(cls)x.className=cls;
  return x;
};
const btn=(label,fn)=>{
  const x=el('button',label,'p11-btn secondary');x.type='button';x.addEventListener('click',fn);return x;
};
const call=(p,opts)=>api(p,opts);
const ROLE=()=>auth?.role;
const TASK=/^TPA-SYN-[A-Z0-9-]{3,50}$/;
let rows=[],total=0,offset=0,selected='',detail=null,inspection=null;
const showError=e=>receipt('B2 未完成：'+e.message);
const routeTask=()=>{
  if(!location.hash.startsWith('#/agent'))return '';
  const raw=location.hash.split('?')[1]||'';
  const t=new URLSearchParams(raw).get('agent_task')||'';
  return TASK.test(t)?t:'';
};
const path=id=>'/v1/tpa/agent-preparations/'+encodeURIComponent(id);
async function refresh(){
  if(!['producer','manager'].includes(ROLE()))return;
  const result=await call('/v1/tpa/agent-preparations?limit=25&offset='+offset);
  rows=result.tasks||[];total=result.total||0;
  if(offset>=total&&offset>0){
    offset=Math.max(0,Math.floor(Math.max(0,total-1)/25)*25);
    return refresh();
  }
  const requested=routeTask();
  if(requested)selected=requested;
  else if(!selected||!rows.some(r=>r.task_id===selected))selected=rows[0]?.task_id||'';
  detail=selected?await call(path(selected)):null;
  inspection=null;
}
async function choose(taskId){
  if(!TASK.test(taskId))throw Error('任务编号不在合成白名单内');
  selected=taskId;inspection=null;
  const url='#/agent?agent_task='+encodeURIComponent(taskId);
  if(location.hash!==url)history.pushState({b2:'task'},'',url);
  detail=await call(path(taskId));renderPage();
}
async function inspect(){
  if(ROLE()!=='producer'||!selected)return;
  const response=await call(path(selected)+'/inspect');
  if(response.fixture_origin!=='SYN-FIXTURE-NOT-AN-LLM'||response.real_agent_executed!==false)
    throw Error('非预置合成候选，拒绝固化 provenance');
  inspection=response;
  receipt({b2_inspection:response.status,source_sha256:response.source_ref.canonical_document_sha256,
    preparation_event_hash:response.preparation_event_hash,real_agent_executed:false});
  renderPage();
}
async function attest(){
  if(!inspection||!selected||ROLE()!=='producer')
    throw Error('必须先完成 Producer 的 EA 固定候选摘要核验');
  const taskId=selected;
  const request={
    contract:'WB-SYNTHETIC-AGENT-PROVENANCE-v0.1',
    expected_preparation_event_hash:inspection.preparation_event_hash,
    expected_candidate_set_digest:inspection.candidate_set_digest
  };
  const idempotency_key=operationKey('b2-fixture-attestation',taskId,request);
  let result;
  try{
    result=await call(path(taskId)+'/attest',{
      method:'POST',body:JSON.stringify({...request,idempotency_key})
    });
  }catch(ex){
    let already;
    try{already=await call(path(taskId))}catch{}
    const proof=already?.attestation;
    if(!proof||proof.status!=='SYNTHETIC_FIXTURE_ATTESTED'||
       proof.candidate_set_digest!==request.expected_candidate_set_digest||
       proof.preparation_event_hash!==request.expected_preparation_event_hash)
       throw ex;
    result={attestation:proof,reconciled_after_uncertain_response:true};
  }
  resolveIntent('b2-fixture-attestation',taskId);
  receipt({b2_attestation:result.attestation.status,
    attestation_sha256:result.attestation.attestation_sha256,
    reconciled_after_uncertain_response:!!result.reconciled_after_uncertain_response,
    real_agent_executed:false,gold_qualification:'NOT_ELIGIBLE'});
  await refresh();renderPage();
}
function pair(parent,label,value){
  parent.append(el('dt',label),el('dd',value||'—'));
}
function render(){
  const page=el('div',undefined,'p11-page');page.id='p11B2AgentPage';
  const heading=el('header',undefined,'p11-heading');
  heading.append(el('h2','Agent 准备 · 固定合成候选来源证明'),
    el('p','只核对原 EA 已冻结的 P1 合成 fixture，不运行 LLM，也不生成科学 Gold'));
  page.append(heading);
  page.append(el('p','Strict-Blind：独立专家模式不进入此任务列表，不能查看任何候选数量、摘要或运行信息。','p11-notice'));
  const stats=el('div',undefined,'p11-source-stats');
  stats.append(el('span','Agent 复核模式任务：'+total),
    el('span','真实模型调用：禁用'),el('span','Gold：NOT_ELIGIBLE'));
  page.append(stats);
  const cols=el('div',undefined,'p11-source-layout');
  const left=el('section',undefined,'p11-panel');
  left.append(el('h3','① 冻结合成工作包'));
  const list=el('div',undefined,'p11-source-rows');list.id='b2AgentTaskRows';
  if(!rows.length)list.append(el('p','当前没有 Agent 复核模式的合成任务。可先在任务中心创建并冻结。','p11-notice'));
  for(const t of rows){
    const item=el('article',undefined,'p11-source-entry');
    if(t.task_id===selected)item.classList.add('selected');
    item.append(el('strong',t.task_id),
      el('p',t.primary_source.source_id+' / '+t.primary_source.revision_id,'p11-meta'),
      el('p','任务状态：'+t.task_state,'p11-meta'),
      el('span',t.preparation_status,'p11-package-status'));
    const chooseButton=btn('查看准备证明',()=>choose(t.task_id).catch(showError));
    chooseButton.setAttribute('aria-pressed',String(t.task_id===selected));
    item.append(chooseButton);list.append(item);
  }
  left.append(list);
  const pager=el('div',undefined,'p11-pagination');
  pager.append(el('span','显示 '+(total?offset+1:0)+'–'+Math.min(offset+rows.length,total)+' / '+total));
  const prev=btn('上一页',()=>{
    offset=Math.max(0,offset-25);selected='';
    refresh().then(renderPage).catch(showError);
  });prev.disabled=offset===0;
  const next=btn('下一页',()=>{
    offset+=25;selected='';refresh().then(renderPage).catch(showError);
  });next.disabled=offset+25>=total;
  pager.append(prev,next);left.append(pager);cols.append(left);
  const right=el('section',undefined,'p11-panel');right.id='b2AgentDetail';
  right.append(el('h3','② 准备核验与不可变回执'));
  if(!selected||!detail){
    right.append(el('p','选择任务后查看冻结准备状态。','p11-notice'));
  }else{
    right.append(el('h4',selected));
    const dl=el('dl',undefined,'p11-source-facts');
    pair(dl,'TPA 状态',detail.task_state);
    pair(dl,'B2 状态',detail.status);
    pair(dl,'来源性质','原 P1 固定合成候选');
    pair(dl,'真实 Agent 执行','否');
    right.append(dl);
    if(detail.attestation){
      const proof=detail.attestation;
      const panel=el('div',undefined,'p11-package-info');panel.id='b2AttestationReceipt';
      panel.append(el('h4','③ 已固化的 provenance'));
      const receiptList=el('dl',undefined,'p11-source-facts');
      pair(receiptList,'回执 SHA-256',proof.attestation_sha256);
      pair(receiptList,'任务定义 SHA-256',proof.task_definition_sha256);
      pair(receiptList,'来源版本',proof.source_ref.source_id+' / '+proof.source_ref.revision_id);
      pair(receiptList,'权威来源 SHA-256',proof.source_ref.canonical_document_sha256);
      pair(receiptList,'P1 准备审计事件 SHA-256',proof.preparation_event_hash);
      pair(receiptList,'执行类型',proof.execution_kind);
      pair(receiptList,'B1 来源引用包',proof.source_package_at_attestation?.package_id||'未登记（允许）');
      if(ROLE()==='producer'&&proof.candidate_set_digest)
        pair(receiptList,'固定候选集合 SHA-256',proof.candidate_set_digest);
      panel.append(receiptList);
      panel.append(el('p','没有候选 payload、原文或专家判断；登记不等于真实模型运行。','p11-notice'));
      right.append(panel);
    }else if(detail.status==='TASK_NOT_PREPARED'){
      right.append(el('p','尚未在原 P1 完成验证、冻结与 prepare；B2 不会替代原状态机。','p11-notice'));
    }else if(ROLE()==='producer'){
      const inspectButton=btn('核验 EA 已冻结合成候选',()=>inspect().catch(showError));
      inspectButton.id='b2InspectAgent';right.append(inspectButton);
      if(inspection){
        const box=el('div',undefined,'p11-package-info');box.id='b2Inspection';
        box.append(el('h4','冻结事实已核对'));
        const provenance=el('dl',undefined,'p11-source-facts');
        pair(provenance,'来源 SHA',inspection.source_ref.canonical_document_sha256);
        pair(provenance,'候选集合 SHA',inspection.candidate_set_digest);
        pair(provenance,'准备审计事件 SHA',inspection.preparation_event_hash);
        box.append(provenance);
        const freeze=btn('固化不可变 B2 provenance',()=>attest().catch(showError));
        freeze.id='b2AttestAgent';box.append(freeze);right.append(box);
      }
    }else{
      right.append(el('p','Manager 只读，无法核验或固化候选证明，也看不到候选摘要与数量。','p11-notice'));
    }
  }
  cols.append(right);page.append(cols);
  page.append(el('p','SYNTHETIC_ENGINEERING_ONLY：真实 Agent、MinerU、真实专家和 Gold 均未放行。','p11-notice'));
  return page;
}
function renderPage(){
  if(!document.body||document.body.dataset.p11View!=='agent')return;
  const view=document.getElementById('p11View');
  if(view)view.replaceChildren(render());
}
window.opsB2Refresh=refresh;
window.opsB2Render=render;
window.opsB2Clear=()=>{
  rows=[];total=0;offset=0;selected='';detail=null;inspection=null;
};
})();
