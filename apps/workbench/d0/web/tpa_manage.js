/* WB-TPA-P1: safe same-origin synthetic-only management controller.
   All server fields rendered via textContent, never inserted as HTML. */
'use strict';
const $=id=>document.getElementById(id);
let auth=null;
let sourceData=[];
let taskData=[];
let selectedFilter='';
const actorByMode={
 AGENT_PROPOSE_EXPERT_VERIFY:'SYN-EA-EXPERT-A',
 HUMAN_INDEPENDENT:'SYN-EA-EXPERT-B'
};
function el(tag,txt,cls){
 const x=document.createElement(tag);
 if(txt!==undefined)x.textContent=String(txt);
 if(cls)x.className=cls;
 return x;
}
function receipt(value){
 $('receipt').textContent=typeof value==='string'?value:JSON.stringify(value,null,2);
}
function failText(data,status){
 const d=data?.detail;
 return (typeof d==='object'?d.code:d)||data?.error||('HTTP '+status);
}
async function api(path,options={}){
 const headers={'Accept':'application/json'};
 if(options.body!==undefined)headers['Content-Type']='application/json';
 if(options.method && options.method!=='GET' && auth?.csrf_token)
   headers['x-csrf-token']=auth.csrf_token;
 const response=await fetch(path,{credentials:'same-origin',cache:'no-store',...options,headers});
 const data=await response.json().catch(()=>({}));
 if(!response.ok)throw new Error(failText(data,response.status));
 return data;
}
async function signIn(ev){
 ev.preventDefault();
 $('loginError').textContent='';
 const username=$('username').value.trim(),password=$('password').value;
 try{
  const result=await api('/v1/login',{method:'POST',body:JSON.stringify({username,password})});
  $('password').value='';
  if(!['manager','producer'].includes(result.role))throw new Error('当前账号不是研究任务管理角色');
  await loadSession();
 }catch(ex){$('loginError').textContent='登录失败：'+ex.message}
}
function newId(){
 $('taskId').value='TPA-SYN-'+crypto.randomUUID().replaceAll('-','').slice(0,12).toUpperCase();
 $('knowledgeCutoff').value=new Date().toISOString();
}
async function loadSession(){
 let ses;
 try{ses=await api('/v1/session')}catch(e){ses=null}
 if(!ses||!['manager','producer'].includes(ses.role)){
  auth=null;$('loginScreen').hidden=false;$('workspace').hidden=true;
  $('logoutButton').hidden=true;$('userBadge').textContent='未登录';return;
 }
 auth=ses;
 $('loginScreen').hidden=true;$('workspace').hidden=false;$('logoutButton').hidden=false;
 $('userBadge').textContent=ses.username+' · '+ses.role;
 $('roleLabel').textContent=ses.role==='manager'?'管理员：分配与发布':'生产者：创建与准备';
 $('taskForm').hidden=ses.role!=='producer';
 await refresh();
}
async function refresh(){
 const [s,t]=await Promise.all([api('/v1/tpa/sources'),api('/v1/tpa/tasks')]);
 sourceData=s.sources;taskData=t.tasks;
 renderSources();renderOptions();renderTasks();updateStats();
}
function renderSources(){
 $('sourcesList').replaceChildren();
 for(const src of sourceData){
  const card=el('article',undefined,'source-row');
  card.append(el('strong',src.title),el('span',src.source_type,'tag'));
  card.append(el('div',src.source_id+' · '+src.revision_id,'meta'));
  card.append(el('div','版本 SHA：'+src.canonical_document_sha256.slice(0,15)+'…','meta'));
  card.append(el('div','权限：'+src.rights_status,'meta'));
  $('sourcesList').append(card);
 }
}
function renderOptions(){
 const p=$('primarySource').value;
 const extra=$('extraSource').value;
 $('primarySource').replaceChildren();
 $('extraSource').replaceChildren(el('option','不增加'));
 $('extraSource').firstChild.value='';
 for(const src of sourceData){
  const label=src.title+' · '+src.source_id+':'+src.revision_id;
  const k=src.source_id+':'+src.revision_id;
  for(const target of [$('primarySource'),$('extraSource')]){
   const item=el('option',label);item.value=k;target.append(item);
  }
 }
 if(p&&[...$('primarySource').options].some(x=>x.value===p))$('primarySource').value=p;
 if(extra&&[...$('extraSource').options].some(x=>x.value===extra))$('extraSource').value=extra;
 showSourceInfo();
}
function selectedSource(value){
 return sourceData.find(x=>x.source_id+':'+x.revision_id===value);
}
function showSourceInfo(){
 const src=selectedSource($('primarySource').value);
 $('sourceInfo').textContent=src?src.source_type+' · '+src.rights_status+' · 来源版本 '+src.revision_id:'请选择来源';
 $('profileId').value=src?.profile_id||'';
 const ex=$('extraSource');
 if(ex.value===$('primarySource').value)ex.value='';
}
function updateStats(){
 $('countSource').textContent=sourceData.length;
 $('countDraft').textContent=taskData.filter(x=>['DRAFT','VALIDATED','DEFINITION_FROZEN'].includes(x.state)).length;
 $('countReady').textContent=taskData.filter(x=>x.state==='READY_FOR_ASSIGNMENT').length;
 $('countPublished').textContent=taskData.filter(x=>x.state==='PUBLISHED').length;
}
async function createDraft(e){
 e.preventDefault();
 if(auth?.role!=='producer')return;
 const p=selectedSource($('primarySource').value);
 const ex=selectedSource($('extraSource').value);
 if(!p)throw new Error('缺少主来源');
 const refs=[p,...(ex&&ex!==p?[ex]:[])].map(x=>({
  source_id:x.source_id,revision_id:x.revision_id,
  canonical_document_sha256:x.canonical_document_sha256
 }));
 const body={
  task_id:$('taskId').value.trim().toUpperCase(),
  task_kind:'EVIDENCE_ECOSYSTEM_CASE',profile_id:p.profile_id,
  primary_source:{source_id:p.source_id,revision_id:p.revision_id},
  allowed_source_versions:refs,knowledge_cutoff:$('knowledgeCutoff').value.trim(),
  workflow_strategy:$('workflowStrategy').value
 };
 try{
  const qualified=await api('/v1/tpa/source-imports/validate',{method:'POST',body:JSON.stringify({
   import_kind:'EXISTING_SYNTHETIC_SOURCE',source_id:p.source_id,revision_id:p.revision_id,
   canonical_document_sha256:p.canonical_document_sha256
  })});
  const result=await api('/v1/tpa/tasks/drafts',{method:'POST',body:JSON.stringify(body)});
  receipt({source_validation:qualified.status,task_created:result});
  newId();await refresh();
 }catch(ex){receipt('创建失败 / 未发布：'+ex.message)}
}
async function createBatch(){
 if(auth?.role!=='producer'||sourceData.length!==7)return;
 if(!window.confirm('创建七类合成来源的任务草稿；不会自动分配或发布。确认？'))return;
 const serial=crypto.randomUUID().replaceAll('-','').slice(0,10).toUpperCase();
 const workflow=$('workflowStrategy').value;
 const cutoff=$('knowledgeCutoff').value.trim();
 const items=sourceData.map((src,i)=>({
  task_id:'TPA-SYN-BATCH-'+serial+'-'+(i+1),
  task_kind:'EVIDENCE_ECOSYSTEM_CASE',
  primary_source:{source_id:src.source_id,revision_id:src.revision_id},
  allowed_source_versions:[{
   source_id:src.source_id,revision_id:src.revision_id,
   canonical_document_sha256:src.canonical_document_sha256
  }],
  profile_id:src.profile_id,knowledge_cutoff:cutoff,workflow_strategy:workflow
 }));
 try{
  const value=await api('/v1/tpa/batches/drafts',{method:'POST',body:JSON.stringify({
   batch_id:'TPA-BATCH-'+serial,
   idempotency_key:crypto.randomUUID(),items
  })});
  receipt(value);await refresh();
 }catch(e){receipt('批量创建未成功：'+e.message)}
}
async function action(id,kind,mode){
 const path='/v1/tpa/tasks/'+encodeURIComponent(id)+'/'+kind;
 let body;
 if(kind==='assign')body={expert_actor:actorByMode[mode],idempotency_key:crypto.randomUUID()};
 if(kind==='publish')body={idempotency_key:crypto.randomUUID()};
 try{
  const value=await api(path,{method:'POST',...(body?{body:JSON.stringify(body)}:{})});
  receipt(value);await refresh();
 }catch(e){receipt('操作被拒绝：'+e.message)}
}
function renderTasks(){
 $('taskList').replaceChildren();
 const visible=taskData.filter(x=>!selectedFilter||x.state===selectedFilter);
 if(!visible.length){$('taskList').append(el('p','尚无此状态的管理任务。','fine'));return}
 for(const t of visible){
  const card=el('article',undefined,'task-row');
  card.append(el('strong',t.task_id),el('span',t.state,'state'));
  card.append(el('div',t.source_type+' · '+t.profile_id,'meta'));
  card.append(el('div',t.workflow_strategy==='HUMAN_INDEPENDENT'?'独立标注 · 禁止候选':'Agent 复核 · 合成候选','meta'));
  card.append(el('div',t.assigned_expert?'专家：'+t.assigned_expert:'专家：尚未分配','meta'));
  const actions=el('div',undefined,'actions');
  const op=auth?.role==='producer'?{DRAFT:['validate','检查资料与任务'],VALIDATED:['freeze','冻结任务定义'],
    DEFINITION_FROZEN:['prepare','准备工作包']}:{READY_FOR_ASSIGNMENT:['assign','分配合成专家'],ASSIGNED:['publish','授权发布任务']};
  const entry=op[t.state];
  if(entry){
   const button=el('button',entry[1]);button.type='button';
   button.setAttribute('aria-label',t.task_id+' '+entry[1]);
   button.addEventListener('click',()=>action(t.task_id,entry[0],t.workflow_strategy));
   actions.append(button);
  }
  if(auth?.role==='manager'&&['ASSIGNED','PUBLISHED'].includes(t.state)){
   const revoke=el('button','撤销未来访问权限');revoke.type='button';
   revoke.setAttribute('aria-label',t.task_id+' 撤销未来访问权限');
   revoke.className='secondary';
   revoke.onclick=async()=>{
    if(!window.confirm('撤销后不会抹除专家已经看过的资料。确定？'))return;
    await action(t.task_id,'revoke',t.workflow_strategy);
   };
   actions.append(revoke);
  }
  if(t.state==='PUBLISHED'){
   const note=el('small','已授权专家账号查看；本管理端不读取专家原文。','fine');card.append(note);
  }
  if(t.state==='REVOKED'){
   card.append(el('small','已撤销后续访问；历史阅读与投放记录仍保留。','fine'));
  }
  card.append(actions);$('taskList').append(card);
 }
}
async function logout(){
 try{await api('/v1/logout',{method:'POST'})}finally{auth=null;await loadSession();receipt('会话已退出');}
}
document.addEventListener('DOMContentLoaded',()=>{
 $('loginForm').addEventListener('submit',signIn);
 $('logoutButton').addEventListener('click',()=>logout().catch(e=>receipt(e.message)));
 $('reload').addEventListener('click',()=>refresh().catch(e=>receipt(e.message)));
 $('taskForm').addEventListener('submit',e=>createDraft(e).catch(x=>receipt(x.message)));
 $('createBatch').addEventListener('click',()=>createBatch().catch(e=>receipt(e.message)));

 $('primarySource').addEventListener('change',showSourceInfo);
 $('stateFilter').addEventListener('change',e=>{selectedFilter=e.target.value;renderTasks()});
 newId();loadSession().catch(e=>receipt('访问失败：'+e.message));
});
