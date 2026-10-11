/* B3: synthetic expert roster + original-TPA-backed assignment and handoff UI. */
(()=>{
'use strict';
const node=(tag,value,cls)=>{
 const x=document.createElement(tag);if(value!==undefined)x.textContent=String(value);
 if(cls)x.className=cls;return x;
};
const button=(text,action)=>{
 const b=node('button',text,'p11-btn secondary');b.type='button';b.addEventListener('click',action);return b;
};
const taskRE=/^TPA-SYN-[A-Z0-9-]{3,50}$/;
const endpoint=task=>'/v1/tpa/expert-handoffs/'+encodeURIComponent(task);
let roster=[],items=[],total=0,offset=0,selected='',detail=null;
const report=error=>receipt('B3 未完成：'+error.message);
const readRoute=()=>{
 if(!location.hash.startsWith('#/experts'))return '';
 const id=new URLSearchParams(location.hash.split('?')[1]||'').get('expert_task')||'';
 return taskRE.test(id)?id:'';
};
async function load(){
 if(!['producer','manager'].includes(auth?.role))return;
 const [r,t]=await Promise.all([api('/v1/tpa/expert-roster'),
     api('/v1/tpa/expert-handoffs?limit=25&offset='+offset)]);
 roster=r.experts||[];items=t.tasks||[];total=t.total||0;
 if(offset>=total&&offset>0){
   offset=Math.floor(Math.max(0,total-1)/25)*25;
   return load();
 }
 const linked=readRoute();
 if(linked)selected=linked;
 else if(!selected||!items.some(x=>x.task_id===selected))selected=items[0]?.task_id||'';
 if(!linked&&selected&&location.hash.startsWith('#/experts'))
   history.replaceState({b3:'task'},'','#/experts?expert_task='+encodeURIComponent(selected));
 detail=selected?await api(endpoint(selected)):null;
}
async function choose(id){
 if(!taskRE.test(id))throw Error('不在合成任务编号范围');
 selected=id;
 const url='#/experts?expert_task='+encodeURIComponent(id);
 if(location.hash!==url)history.pushState({b3:'task'},'',url);
 detail=await api(endpoint(id));
 renderPage();
}
async function originalAction(kind){
 if(auth?.role!=='manager'||!detail)return;
 if(!['assign','publish','revoke'].includes(kind))throw Error('不支持此操作');
 const id=selected;
 // Do not issue a second credential, access grant or assignment state machine.
 await window.opsTaskAction(id,kind,detail.workflow_strategy);
 await load();renderPage();
}
async function attest(){
 if(auth?.role!=='manager'||!detail||!detail.can_handoff)return;
 const id=selected;
 const body={
   contract:'WB-SYNTHETIC-EXPERT-HANDOFF-v0.1',
   expected_assignment_event_hash:detail.assignment_event_hash,
   expected_grant_event_hash:detail.grant_event_hash
 };
 const idempotency_key=operationKey('b3-handoff',id,body);
 let proof;
 try{
   proof=await api(endpoint(id)+'/attest',{method:'POST',body:JSON.stringify({...body,idempotency_key})});
 }catch(error){
   let existing=null;
   try{existing=await api(endpoint(id))}catch{}
   const x=existing?.handoff;
   if(!x||x.status!=='SYNTHETIC_HANDOFF_ATTESTED'||
      x.assignment_event_hash!==body.expected_assignment_event_hash||
      x.grant_event_hash!==body.expected_grant_event_hash)throw error;
   proof={handoff:x,reconciled_after_uncertain_response:true};
 }
 resolveIntent('b3-handoff',id);
 receipt({b3_handoff:proof.handoff.status,handoff_sha256:proof.handoff.handoff_sha256,
    reconciled_after_uncertain_response:!!proof.reconciled_after_uncertain_response,
    expert_read_or_completed_inferred:false,gold_qualification:'NOT_ELIGIBLE'});
 await load();renderPage();
}
function pair(root,k,v){root.append(node('dt',k),node('dd',v??'—'));}
function render(){
 const page=node('div',undefined,'p11-page');page.id='p11B3ExpertPage';
 const heading=node('header',undefined,'p11-heading');
 heading.append(node('h2','专家与分配 · 合成安全交接'),
   node('p','固定合成账号，复用原 TPA 发布授权与 EA 专家入口'));
 page.append(heading);
 page.append(node('p','B3 不是正式专家资格、临床伦理许可或真实专家招募。Manager 的 PUBLISHED 不代表专家已打开或完成标注。','p11-notice'));
 const rosterCard=node('section',undefined,'p11-panel');rosterCard.id='b3ExpertRoster';
 rosterCard.append(node('h3','① 合成测试身份名册'));
 const rosterGrid=node('div',undefined,'p11-source-stats');
 for(const item of roster){
   const card=node('span',item.login_hint+' · '+item.actor+' · '+
     (item.mode==='HUMAN_INDEPENDENT'?'独立标注（无候选）':'合成候选复核'));
   rosterGrid.append(card);
 }
 rosterCard.append(rosterGrid);
 rosterCard.append(node('p','仅为固定工程账号，不创建凭据，不赋予真实科研资格。','p11-meta'));
 page.append(rosterCard);
 const columns=node('div',undefined,'p11-source-layout');
 const left=node('section',undefined,'p11-panel');
 left.append(node('h3','② 合成任务队列'));
 const list=node('div',undefined,'p11-source-rows');list.id='b3TaskRows';
 if(!items.length)list.append(node('p','尚无任务，先在任务中心准备合成任务。','p11-notice'));
 for(const task of items){
   const item=node('article',undefined,'p11-source-entry');
   if(task.task_id===selected)item.classList.add('selected');
   item.append(node('strong',task.task_id),
     node('p',task.source_ref.source_id+' / '+task.source_ref.revision_id+' · '+task.state,'p11-meta'),
     node('span',task.assigned_expert||'未分配','p11-package-status'));
   const select=button('查看分配与暴露状态',()=>choose(task.task_id).catch(report));
   select.setAttribute('aria-pressed',String(task.task_id===selected));
   item.append(select);list.append(item);
 }
 left.append(list);
 const pager=node('div',undefined,'p11-pagination');
 pager.append(node('span','显示 '+(total?offset+1:0)+'–'+Math.min(offset+items.length,total)+' / '+total));
 const prev=button('上一页',()=>{
   offset=Math.max(0,offset-25);selected='';load().then(renderPage).catch(report);
 });prev.disabled=offset===0;
 const next=button('下一页',()=>{
   offset+=25;selected='';load().then(renderPage).catch(report);
 });next.disabled=offset+25>=total;
 pager.append(prev,next);left.append(pager);columns.append(left);
 const right=node('section',undefined,'p11-panel');right.id='b3HandoffDetail';
 right.append(node('h3','③ 权威分配闸门 / 交接回执'));
 if(!detail)right.append(node('p','请选择合成任务。','p11-notice'));
 else{
   right.append(node('h4',detail.task_id));
   const facts=node('dl',undefined,'p11-source-facts');
   for(const [name,val] of [
     ['当前任务状态',detail.state],
     ['工作模式',detail.workflow_strategy==='HUMAN_INDEPENDENT'?'专家独立标注':'合成候选复核'],
     ['允许的合成专家',detail.expected_expert_actor],
     ['实际分配',detail.assigned_expert||'未分配'],
     ['原 EA 权威来源版本',detail.source_ref.source_id+' / '+detail.source_ref.revision_id],
     ['来源文档 SHA-256',detail.source_ref.canonical_document_sha256],
     ['原 TPA 分配事件 SHA-256',detail.assignment_event_hash],
     ['原 TPA 授权事件 SHA-256',detail.grant_event_hash],
     ['原 EA 未来访问闸门',detail.expert_gate_state],
     ['真实专家资格','NO-GO']
   ])pair(facts,name,val);
   right.append(facts);
   const actions=node('div',undefined,'p11-row');actions.id='b3HandoffActions';
   if(auth?.role==='manager'&&detail.can_assign){
      const a=button('通过原 TPA 分配合成专家',()=>originalAction('assign').catch(report));a.id='b3Assign';actions.append(a);
   }
   if(auth?.role==='manager'&&detail.can_publish){
      const p=button('通过原 TPA 授权发布',()=>originalAction('publish').catch(report));p.id='b3Publish';actions.append(p);
   }
   if(auth?.role==='manager'&&detail.can_handoff&&!detail.handoff){
      const h=button('固化不可变专家交接回执',()=>attest().catch(report));h.id='b3Attest';actions.append(h);
   }
   if(auth?.role==='manager'&&['PUBLISHED','ASSIGNED'].includes(detail.state)){
      const r=button('撤销未来访问（不删历史）',()=>{
        if(window.confirm('撤销后未来访问被阻止，既有暴露记录不可删除。确定？'))
          originalAction('revoke').catch(report);
      });r.id='b3Revoke';actions.append(r);
   }
   const toTasks=button('返回原任务中心',()=>{
       document.querySelector('[data-p11-route="tasks"]')?.click();
   });actions.append(toTasks);
   right.append(actions);
   const reportCard=node('div',undefined,'p11-package-info');reportCard.id='b3ExposureStatus';
   reportCard.append(node('h4','④ 历史暴露事件 / 访问语义'));
   reportCard.append(node('p','原 TPA 记录的专家访问事件数：'+detail.recorded_exposure_events,'p11-meta'));
   reportCard.append(node('p','最近记录时间：'+(detail.last_recorded_exposure_at||'尚无记录'),'p11-meta'));
   reportCard.append(node('p',detail.state==='REVOKED'?
      '未来访问已撤销；已经发生的历史访问保留，不可抹除。':
      detail.state==='PUBLISHED'?'原权限闸门已发布，仅限匹配账号任务访问。':'尚未发布；原专家入口不可读取任务。','p11-notice'));
   reportCard.append(node('p','暴露事件不是已阅读、已理解或已完成评审的证明。','p11-meta'));
   right.append(reportCard);
   if(detail.handoff){
      const h=node('div',undefined,'p11-package-info');h.id='b3HandoffReceipt';
      h.append(node('h4','不可变合成专家交接证明'));
      const dl=node('dl',undefined,'p11-source-facts');
      pair(dl,'交接 SHA-256',detail.handoff.handoff_sha256);
      pair(dl,'原授权 SHA-256',detail.handoff.grant_event_hash);
      pair(dl,'合成专家',detail.handoff.assigned_expert);
      pair(dl,'验收范围','SYNTHETIC_HANDOFF_ATTESTED');
      h.append(dl);right.append(h);
   }
   if(detail.state==='PUBLISHED'&&!detail.handoff){
      right.append(node('p','可以由 Manager 固化交接回执，但不会新增授权或推断专家已读。','p11-notice'));
   }
   right.append(node('p','专家需要在另一独立会话、使用原 EA 专家账号于原 / 入口选择任务；Manager 不向浏览器发放登录令牌。','p11-notice'));
 }
 columns.append(right);page.append(columns);
 return page;
}
function renderPage(){
 if(document.body?.dataset.p11View!=='experts')return;
 const view=document.getElementById('p11View');
 if(view)view.replaceChildren(render());
}
window.opsB3Refresh=load;
window.opsB3Render=render;
window.opsB3Clear=()=>{roster=[];items=[];total=0;offset=0;selected='';detail=null;};
})();
