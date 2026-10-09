const $=id=>document.getElementById(id);
window.nutriSession=null;
let profile=null,draft=null,model=null,saving=false;
async function api(path,options={}){const headers={...(options.headers||{})};if(options.method&&options.method!=='GET')headers['X-CSRF-Token']=window.nutriSession?.csrf_token||'';
const r=await fetch(path,{...options,headers,cache:'no-store',credentials:'same-origin'});const data=await r.json().catch(()=>({}));if(!r.ok)throw Error(data.detail?.code||data.detail||`HTTP ${r.status}`);return data;}
function mutation(path,body,method='POST'){return api(path,{method,headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});}
function note(s){$('saveStatus').textContent=s;}
function reset(){window.nutriSession=null;$('workspace').hidden=true;$('loginPanel').hidden=false;$('logout').hidden=true;$('who').textContent='';$('judgmentForm').replaceChildren();$('candidateForm').replaceChildren();$('units').replaceChildren();$('anchors').replaceChildren();$('receipt').textContent='';$('readiness').replaceChildren();$('status').textContent='等待登录';}
async function enter(session){window.nutriSession=session;$('who').textContent=`${session.username} · 合成测试`;$('logout').hidden=false;$('loginPanel').hidden=true;$('workspace').hidden=false;
for(const [id,role] of [['expertPanel','expert'],['managerPanel','manager'],['producerPanel','producer'],['auditorPanel','auditor']])$(id).hidden=session.role!==role;
$('load').hidden=session.role!=='expert';$('task').parentElement.hidden=session.role!=='expert';$('focusMode').hidden=session.role!=='expert';$('evidenceToggle').hidden=true;
if(session.role==='manager'){const data=await api('/v1/readiness');const p=document.createElement('p');p.textContent=`真实专家：NO-GO · 正式 NDS-R1：NO-GO · 来源 ${data.source_count} 条`;$('readiness').replaceChildren(p);for(const x of data.external_requirements){const el=document.createElement('p');el.textContent=`${x.gate}: ${x.status}`;$('readiness').append(el)}return;}
if(session.role!=='expert')return;
profile=await api('/v1/profile');$('field').replaceChildren();for(const group of profile.field_groups)for(const f of group.fields){const o=document.createElement('option');o.value=f.key;o.textContent=f.label;$('field').append(o);}
const list=await api('/v1/tasks');$('task').replaceChildren();for(const t of list.tasks){const o=document.createElement('option');o.value=t.task_id;o.textContent=`${t.arm} · 合成练习`;$('task').append(o);}if(list.tasks.length)$('load').click();}
$('loginForm').addEventListener('submit',async e=>{e.preventDefault();try{const session=await mutation('/v1/login',{username:$('username').value.trim(),password:$('password').value});$('password').value='';$('loginStatus').textContent='';await enter(session);}catch(e){$('loginStatus').textContent='登录失败：'+e.message;}});
$('logout').onclick=async()=>{try{await mutation('/v1/logout');reset();}catch(e){note(e.message);}};
function get(obj,key){return key.split('.').reduce((v,k)=>v?.[k],obj);}
function put(obj,key,value){const keys=key.split('.');let v=obj;for(const k of keys.slice(0,-1))v=v[k];v[keys.at(-1)]=value;}
const expertGroupTitles={
 facts:'01 · 这个案例最关键的问题与已知信息',
 missing:'02 · 还需要知道什么，才能进一步判断？',
 actions:'03 · 当前建议、适用条件与安全边界',
 monitoring:'04 · 随访监测与尚不确定的事项',
 review:'05 · 工作记录与提交前检查'
};
const expertFieldTitles={
 decision_focus:'这个案例最关键的专业问题是什么？',
 salient_existing_facts:'你主要依据哪些已知事实？（一行一条）',
 decision_changing_missing_information:'什么信息可能改变你的判断？（一行一条）',
 currently_acceptable_actions:'你目前认为可以采取哪些行动？',
 conditional_actions:'满足哪些条件后才可以采取行动？',
 not_indicated_prohibited_or_unsafe:'哪些行动暂不适用、禁止或存在安全风险？',
 process_action:'下一步具体需要做什么？',
 monitoring_needs:'后续应当监测或随访什么？',
 uncertainty_notes:'哪些地方仍然不确定？也可以说明暂不作答的原因。',
 rationale_notes:'请补充你的专业判断理由'
};
function renderForm(record,editable){
 $('judgmentForm').replaceChildren();
 for(const group of profile.field_groups){
   const div=document.createElement('details');div.className='group';div.open=group.id==='facts';
   const summary=document.createElement('summary');
   summary.textContent=expertGroupTitles[group.id]||group.title;div.append(summary);
   for(const field of group.fields){
     const label=document.createElement('label');label.textContent=expertFieldTitles[field.key]||field.label;
     const el=document.createElement(field.type.includes('number')||field.type==='nonnegative_integer'?'input':'textarea');
     el.id='f-'+field.key;el.dataset.key=field.key;el.dataset.type=field.type;el.disabled=!editable;
     const value=get(record,field.key);el.value=Array.isArray(value)?value.join('\\n'):value??'';
     if(el.tagName==='TEXTAREA')el.rows=2;
     else{el.type='number';el.min='0';el.step=field.type==='nonnegative_integer'?'1':'any';}
     label.append(el);div.append(label);
   }
   $('judgmentForm').append(div);
 }
}
function payload(){const p=structuredClone(draft.payload);for(const el of $('judgmentForm').querySelectorAll('[data-key]')){let v=el.value;const t=el.dataset.type;if(t==='ordered_string_list')v=v.split('\n').map(x=>x.trim()).filter(Boolean);else if(t==='nullable_nonnegative_number')v=v===''?null:Number(v);else if(t==='nonnegative_integer')v=Number(v);else if(t==='nullable_string')v=v.trim()||null;put(p,el.dataset.key,v);}return p;}
function path(suffix){return `/v1/tasks/${encodeURIComponent($('task').value)}/${suffix}`;}
function candidates(){const editable=model.allowed_actions.includes('verify')||model.allowed_actions.includes('reconcile');$('candidateForm').replaceChildren();for(const c of model.candidate_set?.items||[]){const box=document.createElement('div');box.className='candidate-card';box.dataset.candidate=c.candidate_ref;const p=document.createElement('p');p.textContent=c.text;box.append(p);const select=document.createElement('select');select.className='disposition';for(const d of ['UNCERTAIN','ACCEPT','REJECT','MODIFY','IRRELEVANT','NEEDS_MORE_EVIDENCE']){const o=document.createElement('option');o.value=d;o.textContent=d;select.append(o);}select.disabled=!editable;const why=document.createElement('textarea');why.className='rationale';why.placeholder='复核理由';why.disabled=!editable;box.append(select,why);if(model.arm==='R2'){const l=document.createElement('label');l.textContent='是否改变独立判断？';const changed=document.createElement('input');changed.type='checkbox';changed.className='changed';l.prepend(changed);box.append(l);}$('candidateForm').append(box);}}
async function loadJudgment(){try{note('正在载入');$('receipt').textContent='';model=await api(path('read-model'));$('unexposed').checked=false;const canDraft=model.allowed_actions.includes('draft'),canReconcile=model.allowed_actions.includes('reconcile');
$('saveDraft').hidden=!canDraft;$('freeze').hidden=!canDraft;$('freezeConfirm').hidden=!canDraft;$('submitCandidates').hidden=!model.allowed_actions.some(a=>['verify','reconcile'].includes(a));$('submitCandidates').textContent=model.arm==='R2'?'提交 AI 后复核判断':'提交候选复核';
if(canDraft)draft=await api(path('draft'));else if(model.J_preAI)draft={payload:structuredClone(model.J_preAI.payload),revision:null};else draft=null;
if(model.phase.endsWith('LOCKED')){const records=await api(path('records'));const final=records.records.at(-1);if(final){draft={payload:final.payload.post_ai_judgment||final.payload,revision:null};$('receipt').textContent=JSON.stringify(final,null,2);}}
$('freeze').disabled=!canDraft||!draft||draft.revision<1;if(draft?.payload?.reference_set)renderForm(draft.payload,canDraft||canReconcile);else $('judgmentForm').replaceChildren();candidates();$('revision').textContent=draft?.revision!=null?`草稿版本 ${draft.revision}`:'只读 / 复核阶段';$('judgmentNote').textContent=canDraft?'每次保存由服务端校验版本；冻结后独立判断不可修改。':canReconcile?'独立判断已冻结；本表单记录新的 AI 后判断，不会覆盖 Pre-AI。':'当前阶段由服务端权限控制。';note('已载入');}catch(e){note('载入失败：'+e.message);}}
$('load').addEventListener('click',loadJudgment);
$('saveDraft').onclick=async()=>{if(saving)return;const submitted=payload(),revision=draft.revision,packet=draft.packet_digest;saving=true;$('saveDraft').disabled=true;$('freeze').disabled=true;$('load').disabled=true;try{const result=await mutation(path('draft'),{payload:submitted,expected_revision:revision,packet_digest:packet},'PUT');draft.payload=submitted;draft.revision=result.revision;$('revision').textContent=`草稿版本 ${draft.revision}`;note(JSON.stringify(payload())===JSON.stringify(submitted)?'已保存':'已保存上一版；当前修改尚未保存');}catch(e){note(e.message==='REVISION_CONFLICT'?'草稿版本冲突：请重新载入后核对，当前输入尚未保存。':'保存失败：'+e.message);}finally{saving=false;$('saveDraft').disabled=false;$('load').disabled=false;$('freeze').disabled=draft.revision<1||JSON.stringify(payload())!==JSON.stringify(draft.payload);}};
$('freeze').onclick=async()=>{if(saving){note('请等待保存完成');return;}if(!$('unexposed').checked){note('请确认未暴露条件后再冻结');return;}try{if(JSON.stringify(payload())!==JSON.stringify(draft.payload)){note('请先保存当前修改，再冻结');return;}const result=await mutation(path('freeze'),{expected_revision:draft.revision,idempotency_key:crypto.randomUUID(),exposure_assertions:Object.fromEntries(['agent_output_seen','other_expert_output_seen','final_reference_seen','hidden_diet_values_seen','meta_audit_labels_seen'].map(k=>[k,false]))});await loadJudgment();$('receipt').textContent=JSON.stringify(result,null,2);note('已冻结 · 合成工程记录');}catch(e){note('冻结失败：'+e.message);}};
$('submitCandidates').onclick=async()=>{try{const items=[...$('candidateForm').querySelectorAll('[data-candidate]')].map(box=>({candidate_ref:box.dataset.candidate,expert_disposition:box.querySelector('.disposition').value,rationale:box.querySelector('.rationale').value,...(model.arm==='R2'?{changed_pre_ai_judgment:box.querySelector('.changed').checked,change_type:box.querySelector('.changed').checked?'SYNTHETIC_RECONCILIATION':null,source_refs:['SYN-5-2-PAPER']}:{} )}));const body={items,idempotency_key:crypto.randomUUID()};if(model.arm==='R2')body.post_ai_judgment=payload();const result=await mutation(path(model.arm==='R2'?'reconcile':'verify'),body);await loadJudgment();$('receipt').textContent=JSON.stringify(result,null,2);note('复核提交已锁定 · 合成工程记录');}catch(e){note('提交失败：'+e.message);}};
$('prepare').onclick=async()=>{try{$('producerStatus').textContent=JSON.stringify(await mutation(`/v1/demo/prepare/${$('prepareTask').value}`),null,2);}catch(e){$('producerStatus').textContent='拒绝：'+e.message;}};
$('audit').onclick=async()=>{try{$('auditResult').textContent=JSON.stringify(await api(`/v1/tasks/${$('auditTask').value}/audit`),null,2);}catch(e){$('auditResult').textContent=e.message;}};
// P1.1 expert-first presentation only. No change to the scientific 19-field payload.
$('focusMode').onclick=()=>{
 const active=$('expertPanel').classList.toggle('focus-mode');
 $('expertPanel').classList.remove('evidence-open');
 $('focusMode').setAttribute('aria-pressed',String(active));
 $('evidenceToggle').hidden=!active;
 $('evidenceToggle').setAttribute('aria-expanded','false');
 $('focusMode').textContent=active?'退出专注模式':'v0.3 专注模式';
};
$('evidenceToggle').onclick=()=>{
 const opened=$('expertPanel').classList.toggle('evidence-open');
 $('evidenceToggle').setAttribute('aria-expanded',String(opened));
};
api('/v1/session').then(enter).catch(reset);

$('judgmentForm').addEventListener('input',()=>{if(model?.allowed_actions.includes('draft')&&draft){const dirty=JSON.stringify(payload())!==JSON.stringify(draft.payload);$('freeze').disabled=saving||dirty||draft.revision<1;if(dirty&&!saving)note('当前修改尚未保存');}});
