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
// Synthetic metadata and retry nonce only; no source text, patient data, or model results.
const pendingName='nutriwb_tpa_synthetic_intents_v1';
function readIntents(){
 try {const x=JSON.parse(sessionStorage.getItem(pendingName)||'{}');return x&&typeof x==='object'?x:{}}
 catch {return {}}
}
function saveIntents(x){try{sessionStorage.setItem(pendingName,JSON.stringify(x))}catch{ /* ephemeral fallback */ }}
const volatileIntents={};
function operationKey(action,target,payload){
 const slot=(auth?.username||'unknown')+':'+action+':'+target, signature=JSON.stringify(payload);
 const saved=readIntents(), previous=saved[slot]||volatileIntents[slot];
 if(previous?.signature===signature)return previous.key;
 const value={signature,key:crypto.randomUUID()};
 saved[slot]=value;volatileIntents[slot]=value;saveIntents(saved);
 return value.key;
}
function resolveIntent(action,target){
 const slot=(auth?.username||'unknown')+':'+action+':'+target,saved=readIntents();
 delete saved[slot];delete volatileIntents[slot];saveIntents(saved);
}
function clearIntents(){try{sessionStorage.removeItem(pendingName)}catch{};for(const k of Object.keys(volatileIntents))delete volatileIntents[k]}
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
  auth=null;window.opsClear?.();$('loginScreen').hidden=false;$('workspace').hidden=true;
  $('logoutButton').hidden=true;$('userBadge').textContent='未登录';return;
 }
 if(auth && (auth.username!==ses.username || auth.role!==ses.role)){clearIntents();window.opsClear?.()}
 auth=ses;
 $('loginScreen').hidden=true;$('workspace').hidden=false;$('logoutButton').hidden=false;
 $('userBadge').textContent=ses.username+' · '+ses.role;
 $('roleLabel').textContent=ses.role==='manager'?'管理员：分配与发布':'生产者：创建与准备';
 $('taskForm').hidden=ses.role!=='producer';
 await refresh();
}
async function refresh(){
 if(window.opsA5Enabled){
  const s=await api('/v1/tpa/sources');
  sourceData=s.sources;taskData=[]; // A5 reads *server-paginated* task pages, never a full unfiltered list.
  renderSources();renderOptions();updateStats();
  if(window.opsRefresh)await window.opsRefresh();
  return;
 }
 const [s,t]=await Promise.all([api('/v1/tpa/sources'),api('/v1/tpa/tasks')]);
 sourceData=s.sources;taskData=t.tasks;
 renderSources();renderOptions();renderTasks();updateStats();
 if(window.opsRefresh)await window.opsRefresh();
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
 const ex=$('extraSource');
 if(ex.value===$('primarySource').value)ex.value='';
 const other=selectedSource(ex.value);
 $('sourceInfo').textContent=src?
   '主要来源 '+src.source_id+' / '+src.revision_id+' · '+src.source_type+' · '+src.rights_status+
   ' · SHA-256 '+src.canonical_document_sha256+
   (other?'；补充来源 '+other.source_id+' / '+other.revision_id+' · SHA-256 '+other.canonical_document_sha256:'')
   :'请选择来源';
 $('profileId').value=src?.profile_id||'';
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
  const result=window.opsDraftCreate?await window.opsDraftCreate(body):await api('/v1/tpa/tasks/drafts',{method:'POST',body:JSON.stringify(body)});
  receipt({source_validation:qualified.status,task_created:result});
  window.opsAfterDraft?.(body.task_id);
  newId();await refresh();
 }catch(ex){receipt('创建失败 / 未发布：'+ex.message)}
}
async function createBatch(){
 if(auth?.role!=='producer'||sourceData.length!==7)return;
 if(!window.confirm('这是 P1 旧版七条 Legacy 批量草稿操作，不会放入当前运营项目/批次，也不会发布。继续？'))return;
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
 const expected={validate:'VALIDATED',freeze:'DEFINITION_FROZEN',prepare:'READY_FOR_ASSIGNMENT',
                 assign:'ASSIGNED',publish:'PUBLISHED',revoke:'REVOKED'}[kind];
 const path='/v1/tpa/tasks/'+encodeURIComponent(id)+'/'+kind;
 let body;
 if(kind==='assign'){
  const actor=actorByMode[mode];
  if(!actor){receipt('无效的合成专家工作模式');return}
  body={expert_actor:actor,idempotency_key:operationKey('assign',id,{expert_actor:actor})};
 }
 if(kind==='publish')body={idempotency_key:operationKey('publish',id,{task_id:id})};
 try{
  const value=await api(path,{method:'POST',...(body?{body:JSON.stringify(body)}:{})});
  if(kind==='assign'||kind==='publish')resolveIntent(kind,id);
  receipt(value);window.opsAfterTaskAction?.(id,kind,value);await refresh();
 }catch(e){
  // A lost HTTP response does not prove a failed transaction. Read the server state first.
  try{
   const safe=await api('/v1/tpa/tasks/'+encodeURIComponent(id)+'/management');
   if(safe.state===expected){
    if(kind==='assign'||kind==='publish')resolveIntent(kind,id);
    receipt({task_id:id,state:safe.state,reconciled_after_uncertain_response:true,
             caution:'由服务端任务状态确认；不推断专家已阅读或科学合格'});
    window.opsAfterTaskAction?.(id,kind,safe);await refresh();return;
   }
  }catch{ /* preserve the same request key for a subsequent user-initiated retry */ }
  receipt('操作未确认：'+e.message+'。请刷新服务端状态；重试同一操作会复用原请求键。');
 }
}
window.opsTaskAction=action;
function renderTasks(){
 if(window.opsA5Enabled && window.opsRenderTaskTable){
  window.opsRenderTaskTable($('taskList'),action);
  return;
 }
 $('taskList').replaceChildren();
 const scoped=window.opsVisibleTasks?window.opsVisibleTasks(taskData):taskData;
 const visible=scoped.filter(x=>(!selectedFilter||x.state===selectedFilter)&&(!window.opsPreparingFilter||['DRAFT','VALIDATED','DEFINITION_FROZEN'].includes(x.state)));
 if(!visible.length){$('taskList').append(el('p','尚无此状态的管理任务。','fine'));return}
 for(const t of visible){
  const card=el('article',undefined,'task-row');
  card.append(el('strong',t.task_id),el('span',t.state,'state'));
  card.append(el('div',t.source_type+' · '+t.profile_id,'meta'));
  if(window.opsLegacyTask?.(t.task_id))card.append(el('span','Legacy · 未归属项目/批次','tag'));
  card.append(el('div',t.workflow_strategy==='HUMAN_INDEPENDENT'?'独立标注 · 禁止候选':'Agent 复核 · 合成候选','meta'));
  card.append(el('div',t.assigned_expert?'专家：'+t.assigned_expert:'专家：尚未分配','meta'));
  const actions=el('div',undefined,'actions');
  if(window.opsTaskDetail){
    const inspect=el('button','查看任务详情');inspect.type='button';inspect.className='secondary';
    inspect.addEventListener('click',()=>window.opsTaskDetail(t.task_id));actions.append(inspect);
  }
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
 try{await api('/v1/logout',{method:'POST'})}finally{clearIntents();auth=null;await loadSession();receipt('会话已退出');}
}
document.addEventListener('DOMContentLoaded',()=>{
 $('loginForm').addEventListener('submit',signIn);
 $('logoutButton').addEventListener('click',()=>logout().catch(e=>receipt(e.message)));
 $('reload').addEventListener('click',()=>refresh().catch(e=>receipt(e.message)));
 $('taskForm').addEventListener('submit',e=>createDraft(e).catch(x=>receipt(x.message)));
 $('createBatch').addEventListener('click',()=>createBatch().catch(e=>receipt(e.message)));

 $('primarySource').addEventListener('change',showSourceInfo);
 $('extraSource').addEventListener('change',showSourceInfo);
 $('stateFilter').addEventListener('change',e=>{
  selectedFilter=e.target.value;window.opsPreparingFilter=false;
  if(window.opsA5StateChanged)window.opsA5StateChanged(selectedFilter);
  else renderTasks();
 });
 newId();loadSession().catch(e=>receipt('访问失败：'+e.message));
});
