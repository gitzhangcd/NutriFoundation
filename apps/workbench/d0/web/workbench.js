import {judgmentEvidence,invalidateChangedBindings} from './evidence_status.js';
import {appendNaturalEntry,confirmCanonicalCompleteness,canonicalPaths} from './expert_native.js';
const $=id=>document.getElementById(id);
window.nutriSession=null;
let profile=null,draft=null,model=null,saving=false,viewStage='reader';
let evidenceItems=[],evidenceBindings=[],evidenceItemBindings=[];
let evidenceItemIndex='';
let pdfVerification={};
async function api(path,options={}){const headers={...(options.headers||{})};if(options.method&&options.method!=='GET')headers['X-CSRF-Token']=window.nutriSession?.csrf_token||'';
const r=await fetch(path,{...options,headers,cache:'no-store',credentials:'same-origin'});const data=await r.json().catch(()=>({}));if(!r.ok)throw Error(data.detail?.code||data.detail||`HTTP ${r.status}`);return data;}
function mutation(path,body,method='POST'){return api(path,{method,headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});}
function note(s){$('saveStatus').textContent=s;refreshPresentation();}
function reset(){window.nutriSession=null;model=null;draft=null;profile=null;viewStage='reader';evidenceItems=[];evidenceBindings=[];evidenceItemBindings=[];pdfVerification={};evidenceItemIndex='';for(const id of ['workflowNav','workFooter','evidencePane'])$(id).hidden=true;$('expertPanel').classList.remove('reviewing','evidence-open','focus-mode');$('reviewPane').hidden=true;$('workspace').hidden=true;$('loginPanel').hidden=false;$('logout').hidden=true;$('who').textContent='';$('judgmentForm').replaceChildren();$('candidateForm').replaceChildren();$('units').replaceChildren();$('anchors').replaceChildren();$('receipt').textContent='';$('readiness').replaceChildren();$('status').textContent='等待登录';}
async function enter(session){window.nutriSession=session;$('who').textContent=`${session.username} · 合成测试`;$('logout').hidden=false;$('loginPanel').hidden=true;$('workspace').hidden=false;
for(const [id,role] of [['expertPanel','expert'],['managerPanel','manager'],['producerPanel','producer'],['auditorPanel','auditor']])$(id).hidden=session.role!==role;
$('load').hidden=session.role!=='expert';$('task').parentElement.hidden=session.role!=='expert';$('focusMode').hidden=session.role!=='expert';$('evidenceToggle').hidden=session.role!=='expert';$('workflowNav').hidden=session.role!=='expert';$('workFooter').hidden=session.role!=='expert';
if(session.role==='manager'){renderReadiness(await api('/v1/readiness'));return;}
if(session.role!=='expert')return;
profile=await api('/v1/profile');$('field').replaceChildren();for(const group of profile.field_groups)for(const f of group.fields){const o=document.createElement('option');o.value=f.key;o.textContent=expertFieldTitles[f.key]||f.label;$('field').append(o);}
$('selectionField').replaceChildren(...[...$('field').options].map(o=>o.cloneNode(true)));
const list=await api('/v1/tasks');$('task').replaceChildren();for(const t of list.tasks){const o=document.createElement('option');o.value=t.task_id;o.textContent=`${t.arm} · 合成练习`;$('task').append(o);}if(list.tasks.length)$('load').click();}
$('loginForm').addEventListener('submit',async e=>{e.preventDefault();try{const session=await mutation('/v1/login',{username:$('username').value.trim(),password:$('password').value});$('password').value='';$('loginStatus').textContent='';await enter(session);}catch(e){$('loginStatus').textContent=loginErrors[e.message]||'登录失败，请稍后重试（'+e.message+'）';}});
const loginErrors={UNAUTHENTICATED:'账号或密码不正确，请检查后重试。',RATE_LIMITED:'尝试次数过多，请稍等几分钟再试。',ORIGIN_REQUIRED:'请从分配的访问地址打开工作台。',HOST_NOT_ALLOWED:'请从分配的访问地址打开工作台。'};
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
const fieldShortTitles={
 decision_focus:'关键问题',salient_existing_facts:'已知事实',decision_changing_missing_information:'缺失信息',
 currently_acceptable_actions:'当前行动',conditional_actions:'条件性行动',not_indicated_prohibited_or_unsafe:'不适用/禁止/风险',
 process_action:'下一步',monitoring_needs:'监测随访',uncertainty_notes:'不确定性',rationale_notes:'判断理由'
};
// The case question itself does not need a supporting source.
const sourceOptionalFields=new Set(['decision_focus']);
const phaseTitles={
 PRE_AI:'独立判断阶段（未接触 AI）',HUMAN_DE_NOVO:'独立判断阶段',WAIT_AGENT_FREEZE:'等待候选准备',
 EXPERT_VERIFY:'候选复核阶段',POST_AI_RECONCILE:'AI 后复核阶段'
};
function phaseLabel(phase){if(!phase)return '尚未打开';if(phaseTitles[phase])return phaseTitles[phase];if(phase.endsWith('LOCKED'))return '已冻结（只读）';return phase;}
window.nutriPhaseLabel=phaseLabel;
function afterDraftSaved(before,after){
 evidenceItemBindings=invalidateChangedBindings(evidenceItemBindings,before,after,(data,field,index)=>
   entriesForField(field,data).find(x=>x.index===index)?.text);
 window.nutriReader?.refreshEvidence?.();
}
let conflictPayload=null;
function rememberConflict(submitted){conflictPayload=structuredClone(submitted);}
function applyPayloadToForm(data){
 for(const el of $('judgmentForm').querySelectorAll('[data-key]')){
  const value=get(data,el.dataset.key);el.value=Array.isArray(value)?value.join('\n'):value??'';
 }
}
function formDirty(){return !!(model?.allowed_actions?.includes('draft')&&draft&&$('judgmentForm').querySelector('[data-key]')&&JSON.stringify(payload())!==JSON.stringify(draft.payload));}
const judgmentSections=[
 {title:'这个案例最关键的专业问题是什么？',primary:['decision_focus'],extra:[],hint:'先表达自己的专业判断，无需填写研究术语。'},
 {title:'你作出判断主要依据哪些信息？',primary:['salient_existing_facts'],extra:[],hint:'每行一条依据；选中原文可关联到具体判断。'},
 {title:'还需要知道什么，才能进一步判断？',primary:['decision_changing_missing_information'],extra:[],hint:'优先记录可能改变决策的信息。'},
 {title:'你目前建议怎么做？',primary:['currently_acceptable_actions'],extra:['conditional_actions','process_action','rationale_notes',...['preferred','acceptable','conditional','not_currently_indicated','prohibited','unsafe','unresolved'].map(k=>'reference_set.'+k)],hint:'保留你的原话；条件性行动与完整分类可分别补充。'},
 {title:'什么情况下需要调整或停止？',primary:['not_indicated_prohibited_or_unsafe'],extra:['monitoring_needs','uncertainty_notes'],hint:'分别记录安全边界、监测需求和仍不确定的事项。'}
];
function renderForm(record,editable){
 $('judgmentForm').replaceChildren();
 const fields=new Map(profile.field_groups.flatMap(g=>g.fields).map(f=>[f.key,f]));
 function control(key,primary=false){
  const field=fields.get(key),label=document.createElement('label');
  label.className=primary?'primary-field':'';
  const title=document.createElement('span');title.textContent=expertFieldTitles[key]||field.label;label.append(title);
  const el=document.createElement(field.type.includes('number')||field.type==='nonnegative_integer'?'input':'textarea');
  el.id='f-'+key;el.dataset.key=key;el.dataset.type=field.type;el.disabled=!editable;
  el.setAttribute('aria-label',expertFieldTitles[key]||field.label);
  const value=get(record,key);el.value=Array.isArray(value)?value.join('\n'):value??'';
  if(el.tagName==='TEXTAREA'){el.rows=primary?3:2;el.placeholder=primary?'用自己的专业语言写下判断…':'请按类别补充，每行一项…';}
  else{el.type='number';el.min='0';el.step=field.type==='nonnegative_integer'?'1':'any';}
  el.addEventListener('focus',()=>chooseEvidenceField(key));label.append(el);
  return label;
 }
 judgmentSections.forEach((section,index)=>{
  const div=document.createElement('details');div.className='group';div.open=true;
  const summary=document.createElement('summary'),num=document.createElement('span'),title=document.createElement('span');
  num.className='num';num.textContent=String(index+1).padStart(2,'0');title.textContent=section.title;summary.append(num,title);div.append(summary);
  section.primary.forEach(key=>div.append(control(key,true)));
  const target=document.createElement('button');target.type='button';target.className='field-target';target.dataset.target=section.primary[0];target.textContent='◎ 选此项为引用目标';target.onclick=()=>chooseEvidenceField(target.dataset.target);div.append(target);
  const hint=document.createElement('p');hint.className='field-caption';hint.textContent=section.hint;div.append(hint);
  if(section.extra.length){const extra=document.createElement('details');extra.className='advanced-fields';const st=document.createElement('summary');st.textContent=index===3?'补充行动条件、理由与完整方案分类':'补充监测、随访与不确定性';extra.append(st);section.extra.forEach(key=>extra.append(control(key)));div.append(extra);}
  $('judgmentForm').append(div);
 });
 const meta=document.createElement('details');meta.className='record-fields';const title=document.createElement('summary');title.textContent='工作记录 · 工时与澄清次数';meta.append(title);['active_expert_minutes','clarification_count'].forEach(k=>meta.append(control(k)));$('judgmentForm').append(meta);
 chooseEvidenceField($('field').value);
}
function chooseEvidenceField(key){
 if($('field').value!==key)evidenceItemIndex='';
 $('field').value=key;$('selectionField').value=key;
 for(const button of $('judgmentForm').querySelectorAll('[data-target]'))button.setAttribute('aria-pressed',String(button.dataset.target===key));
 refreshItemOptions();
 window.nutriReader?.updateConfirmation?.();
}
function entriesForField(key, data){
 const value=get(data,key);
 return Array.isArray(value)?value.map((text,i)=>({text,index:i})).filter(x=>String(x.text).trim()):
    typeof value==='string'&&value.trim()?[{text:value,index:0}]:[];
}
function refreshItemOptions(){
 if(!draft||!profile)return;
 const key=$('field').value;
 const data=payload();
 const entries=entriesForField(key,data);
 for(const id of ['evidenceItem','selectionItem']){
   const select=$(id);
   if(!select)continue;
   select.replaceChildren();
   const initial=document.createElement('option');initial.value='';initial.textContent=entries.length?'请选择这段原文要支撑的判断':'这一类还没有判断，请先填写并保存';select.append(initial);
   for(const item of entries){
     const opt=document.createElement('option');opt.value=String(item.index);
     opt.textContent=`第 ${item.index+1} 条 · ${item.text.slice(0,65)}`;select.append(opt);
   }
   if(entries.some(x=>String(x.index)===String(evidenceItemIndex)))select.value=String(evidenceItemIndex);
   else {evidenceItemIndex='';select.value='';}
 }
 if($('evidenceItemNotice'))$('evidenceItemNotice').textContent=
   submissionReadiness().saved?'可选择已保存的具体判断；更改判断后须重新核查绑定。':
   '逐条证据绑定前请先保存当前草稿。';
}
function selectEvidenceItem(field,index,open=false){
 chooseEvidenceField(field);
 evidenceItemIndex=String(index);
 for(const id of ['evidenceItem','selectionItem'])if($(id))$(id).value=evidenceItemIndex;
 if(open){openEvidence();showEvidenceTab('linked');renderEvidenceReview(field,index);}
}
// Selecting text in the reader is the primary way to cite; manual typing stays advanced.
function startCiting(field,index){
 showStage('reader');closeEvidence();selectEvidenceItem(field,index,false);
 const item=entriesForField(field,payload()).find(x=>x.index===index);
 window.nutriReader?.setCiteTarget?.((fieldShortTitles[field]||field)+' 第 '+(index+1)+' 条'+(item?'：'+item.text.slice(0,40):''));
 $('units').focus({preventScroll:true});
}
function renderJudgmentItemRows(){
 const root=$('judgmentItemRows');if(!root||!draft)return;
 root.replaceChildren();
 const data=payload();
 for(const field of profile.field_groups.flatMap(g=>g.fields)){
   if(field.type!=='ordered_string_list'&&field.type!=='nullable_string')continue;
   for(const {text,index} of entriesForField(field.key,data)){
     const row=document.createElement('div');row.className='judgment-item-row';
     const item=document.createElement('div');
     const heading=document.createElement('small');heading.textContent=expertFieldTitles[field.key]||field.label;
     const body=document.createElement('span');body.textContent=text;
     item.append(heading,body);
     const status=itemEvidence(field.key,index,text);
     const links=status.links;
     const state=document.createElement('small');state.className='evidence-state';
     state.textContent=status.stale?`此位置原有 ${status.stale} 条关联：判断已修改或删除，需重新确认`+(links.length?` · 有效证据 ${links.length} 条`:''):links.length?`${links.length} 条证据 · PDF ${links.every(x=>x.pdfVerified)?'本次会话已核验':'本次会话未核验'}`:sourceOptionalFields.has(field.key)?'可选 · 问题本身无需来源':'待补充来源 · 0 条证据';
     item.append(state);
     const cite=document.createElement('button');cite.type='button';cite.className='ghost mini';
     cite.textContent=links.length||status.stale?'核查证据':'关联原文证据';
     cite.onclick=()=>links.length||status.stale?selectEvidenceItem(field.key,index,true):startCiting(field.key,index);
     row.append(item,cite);root.append(row);
   }
 }
 if(!root.children.length){const none=document.createElement('p');none.className='small';none.textContent='还没有单条判断。先填写专业判断，再保存后关联来源证据。';root.append(none);}
}
window.nutriJudgment={
  getBindingTarget:()=>{
    if(!draft || !profile)return null;
    const key=$('field').value;
    const data=payload();
    const entries=entriesForField(key,data);
    const item=entries.find(x=>String(x.index)===String(evidenceItemIndex));
    if(!item)throw Error(entries.length?'请选择这段原文要支撑哪一条判断':'这一类还没有判断，请先填写并保存');
    const state=submissionReadiness();
    if(!state.saved)throw Error('请先保存当前判断，再关联这条证据');
    return {field:key,index:item.index,text:item.text,revision:draft.revision,legacy:false,
            label:(fieldShortTitles[key]||expertFieldTitles[key]||key)+' 第 '+(item.index+1)+' 条'};
  }
};
function payload(){const p=structuredClone(draft.payload);for(const el of $('judgmentForm').querySelectorAll('[data-key]')){let v=el.value;const t=el.dataset.type;if(t==='ordered_string_list')v=v.split('\n').filter(x=>x.trim().length>0);else if(t==='nullable_nonnegative_number')v=v===''?null:Number(v);else if(t==='nonnegative_integer')v=Number(v);else if(t==='nullable_string')v=v.trim()||null;put(p,el.dataset.key,v);}confirmCanonicalCompleteness(profile,p);return p;}
function path(suffix){return `/v1/tasks/${encodeURIComponent($('task').value)}/${suffix}`;}
const dispositionLabels=[['ACCEPT','接受'],['MODIFY','需修改后接受'],['REJECT','拒绝'],['NEEDS_MORE_EVIDENCE','需要更多证据'],['IRRELEVANT','与本案无关'],['UNCERTAIN','不确定']];
function candidates(){const editable=model.allowed_actions.includes('verify')||model.allowed_actions.includes('reconcile');$('candidateForm').replaceChildren();for(const c of model.candidate_set?.items||[]){const box=document.createElement('div');box.className='candidate-card';box.dataset.candidate=c.candidate_ref;const p=document.createElement('p');p.textContent=c.text;box.append(p);const select=document.createElement('select');select.className='disposition';select.setAttribute('aria-label','候选处置');{const o=document.createElement('option');o.value='';o.textContent='请选择处置…';select.append(o);}for(const [d,label] of dispositionLabels){const o=document.createElement('option');o.value=d;o.textContent=label;select.append(o);}select.disabled=!editable;const why=document.createElement('textarea');why.className='rationale';why.placeholder='复核理由';why.disabled=!editable;box.append(select,why);if(model.arm==='R2'){const l=document.createElement('label');l.textContent='是否改变独立判断？';const changed=document.createElement('input');changed.type='checkbox';changed.className='changed';l.prepend(changed);box.append(l);}$('candidateForm').append(box);}}
async function loadJudgment(){try{showStage('reader');note('正在载入');$('receipt').textContent='';model=await api(path('read-model'));$('unexposed').checked=false;const canDraft=model.allowed_actions.includes('draft'),canReconcile=model.allowed_actions.includes('reconcile');
$('saveDraft').hidden=!canDraft;$('freeze').hidden=!canDraft;$('freezeConfirm').hidden=!canDraft;$('submitCandidates').hidden=!model.allowed_actions.some(a=>['verify','reconcile'].includes(a));$('submitCandidates').textContent=model.arm==='R2'?'提交 AI 后复核判断':'提交候选复核';
if(canDraft)draft=await api(path('draft'));else if(model.J_preAI)draft={payload:structuredClone(model.J_preAI.payload),revision:null};else draft=null;
if(model.phase.endsWith('LOCKED')){const records=await api(path('records'));const final=records.records.at(-1);if(final){draft={payload:final.payload.post_ai_judgment||final.payload,revision:null};$('receipt').textContent=JSON.stringify(final,null,2);}}
$('freeze').disabled=!canDraft||!draft||draft.revision<1;if(draft?.payload?.reference_set)renderForm(draft.payload,canDraft||canReconcile);else $('judgmentForm').replaceChildren();$('nativeComposer').hidden=!canDraft;candidates();$('revision').textContent=draft?.revision!=null?`草稿版本 ${draft.revision}`:'只读 / 复核阶段';$('judgmentNote').textContent=canDraft?'每次保存由服务端校验版本；冻结后独立判断不可修改。':canReconcile?'独立判断已冻结；本表单记录新的 AI 后判断，不会覆盖 Pre-AI。':model.arm==='R1'?'本阶段只复核候选摘录，不填写独立判断。':model.phase.endsWith('LOCKED')?'已冻结，只读。':'当前阶段由服务端权限控制。';
$('judgmentTitle').textContent=model.arm==='R1'?'候选复核':'我的独立判断';
$('judgmentItemList').hidden=!draft?.payload?.reference_set;
if(conflictPayload&&canDraft&&draft){applyPayloadToForm(conflictPayload);conflictPayload=null;note(`已载入最新版本 ${draft.revision}，并恢复了你未保存的输入：请核对后再保存。`);}
else note('已载入');}catch(e){note('载入失败：'+e.message);}}
$('load').addEventListener('click',loadJudgment);
document.addEventListener('click',e=>{
 if(!e.target.closest?.('#load')||!formDirty()||conflictPayload)return;
 if(!window.confirm('当前有未保存的修改，重新载入会丢失这些修改。确定继续？')){e.stopPropagation();e.preventDefault();}
},true);
$('saveDraft').onclick=async()=>{if(saving)return;const submitted=payload(),revision=draft.revision,packet=draft.packet_digest;saving=true;$('saveDraft').disabled=true;$('freeze').disabled=true;$('load').disabled=true;try{const result=await mutation(path('draft'),{payload:submitted,expected_revision:revision,packet_digest:packet},'PUT');const previous=draft.payload;draft.payload=submitted;draft.revision=result.revision;if(typeof afterDraftSaved==='function')afterDraftSaved(previous,submitted);$('revision').textContent=`草稿版本 ${draft.revision}`;note(JSON.stringify(payload())===JSON.stringify(submitted)?'已保存':'已保存上一版；当前修改尚未保存');}catch(e){if(e.message==='REVISION_CONFLICT'&&typeof rememberConflict==='function')rememberConflict(submitted);note(e.message==='REVISION_CONFLICT'?'草稿版本冲突：其他窗口已保存新版本。点“打开任务 / 重新载入”会载入最新版本，并恢复你这次的输入供核对。':'保存失败：'+e.message);}finally{saving=false;$('saveDraft').disabled=false;$('load').disabled=false;$('freeze').disabled=draft.revision<1||JSON.stringify(payload())!==JSON.stringify(draft.payload);if(typeof refreshPresentation==='function')refreshPresentation();}};
$('freeze').onclick=async()=>{if(!submissionReadiness().eligible){note('冻结受阻：当前独立判断未保存或尚未填写');return;}if(saving){note('请等待保存完成');return;}if(!$('unexposed').checked){note('请确认未暴露条件后再冻结');return;}try{if(JSON.stringify(payload())!==JSON.stringify(draft.payload)){note('请先保存当前修改，再冻结');return;}const result=await mutation(path('freeze'),{expected_revision:draft.revision,idempotency_key:crypto.randomUUID(),exposure_assertions:Object.fromEntries(['agent_output_seen','other_expert_output_seen','final_reference_seen','hidden_diet_values_seen','meta_audit_labels_seen'].map(k=>[k,false]))});await loadJudgment();$('receipt').textContent=JSON.stringify(result,null,2);showStage('review');note('已冻结 · 合成工程记录');}catch(e){note('冻结失败：'+e.message);}};
$('submitCandidates').onclick=async()=>{try{if([...$('candidateForm').querySelectorAll('.disposition')].some(x=>!x.value)){note('请先为每条候选选择处置');return;}const items=[...$('candidateForm').querySelectorAll('[data-candidate]')].map(box=>({candidate_ref:box.dataset.candidate,expert_disposition:box.querySelector('.disposition').value,rationale:box.querySelector('.rationale').value,...(model.arm==='R2'?{changed_pre_ai_judgment:box.querySelector('.changed').checked,change_type:box.querySelector('.changed').checked?'SYNTHETIC_RECONCILIATION':null,source_refs:['SYN-5-2-PAPER']}:{} )}));const body={items,idempotency_key:crypto.randomUUID()};if(model.arm==='R2')body.post_ai_judgment=payload();const result=await mutation(path(model.arm==='R2'?'reconcile':'verify'),body);await loadJudgment();$('receipt').textContent=JSON.stringify(result,null,2);note('复核提交已锁定 · 合成工程记录');}catch(e){note('提交失败：'+e.message);}};
$('prepare').onclick=async()=>{try{$('producerStatus').textContent=JSON.stringify(await mutation(`/v1/demo/prepare/${$('prepareTask').value}`),null,2);}catch(e){$('producerStatus').textContent='拒绝：'+e.message;}};
$('audit').onclick=async()=>{try{renderAudit(await api(`/v1/tasks/${$('auditTask').value}/audit`));}catch(e){$('auditResult').textContent='无法读取审计链：'+e.message;}};
const gateTitles={IDENTITY_PROVIDER_PRODUCTION_CONFIGURATION:'生产身份认证配置',REAL_EXPERT_CREDENTIALS_QUALIFIED:'真实专家资质核验',
 EXPERT_PRIOR_EXPOSURE_AND_ARM_BINDING:'专家既往暴露与分组绑定',IRB_ETHICS_CONSENT_APPLICABILITY:'伦理审查与知情同意',
 SOURCE_SNAPSHOT_AND_RIGHTS:'来源快照与版权',SOURCE_CASE_VIEW_R3_RECONCILIATION:'来源/病例视图 R3 对齐',
 DEPLOYMENT_SECURITY_AND_PRIVACY:'部署安全与隐私',RESEARCH_SEPARATION_FROM_USABILITY:'科研与可用性测试分离'};
const statusTitles={PENDING_INDEPENDENT_EVIDENCE:'待独立证据',BLOCK_UPSTREAM_SCIENTIFIC_VERSION_CONFLICT:'阻塞：上游科学版本冲突'};
function renderReadiness(data){
 const head=document.createElement('p');head.className='readiness-head';head.textContent=`真实专家：NO-GO · 正式 NDS-R1：NO-GO · 来源 ${data.source_count} 条`;
 const table=document.createElement('table');table.className='readiness-table';
 const hr=document.createElement('tr');for(const t of ['准入条件','状态'])hr.append(Object.assign(document.createElement('th'),{textContent:t,scope:'col'}));table.append(hr);
 for(const x of data.external_requirements){
  const tr=document.createElement('tr');const gate=document.createElement('td'),status=document.createElement('td');
  gate.textContent=gateTitles[x.gate]||x.gate;const code=document.createElement('small');code.textContent=x.gate;gate.append(code);
  status.textContent=statusTitles[x.status]||x.status;status.className=x.status.startsWith('BLOCK')?'blocked':'pending';const sc=document.createElement('small');sc.textContent=x.status;status.append(sc);
  tr.append(gate,status);table.append(tr);
 }
 $('readiness').replaceChildren(head,table);
}
function renderAudit(data){
 const events=data.events||[];let chainOk=true;
 const list=document.createElement('ol');list.className='audit-timeline';
 events.forEach((ev,i)=>{
  const linked=i===0?ev.previous_hash==='GENESIS':ev.previous_hash===events[i-1].event_hash;chainOk&&=linked;
  const li=document.createElement('li');li.className=linked?'':'broken';
  const title=document.createElement('b');title.textContent=ev.event;
  const meta=document.createElement('small');meta.textContent=`${ev.actor} · ${new Date(ev.created_at).toLocaleString('zh-CN')} · ${linked?'哈希链衔接正常':'⚠ 哈希链断开'}`;
  li.append(title,meta);
  if(ev.details&&ev.details!=='{}'){const d=document.createElement('code');d.textContent=ev.details;li.append(d);}
  list.append(li);
 });
 const summary=document.createElement('p');summary.className=chainOk?'audit-ok':'audit-broken';
 summary.textContent=`${data.task_id} · 共 ${events.length} 个事件 · ${chainOk?'✓ 前后哈希逐条衔接':'⚠ 发现哈希链断开'}（仅检查前端可见的衔接，不替代服务端校验）`;
 const raw=document.createElement('details');const st=document.createElement('summary');st.textContent='查看原始 JSON';const pre=document.createElement('pre');pre.textContent=JSON.stringify(data,null,2);raw.append(st,pre);
 $('auditResult').replaceChildren(summary,list,raw);
}
// P1.1 expert-first presentation only. No change to the scientific 19-field payload.
$('focusMode').onclick=()=>{
 const active=$('expertPanel').classList.toggle('focus-mode');
 $('expertPanel').classList.remove('evidence-open');$('evidencePane').hidden=true;
 $('focusMode').setAttribute('aria-pressed',String(active));
 $('evidenceToggle').hidden=false;
 $('evidenceToggle').setAttribute('aria-expanded','false');
 $('focusMode').textContent=active?'退出专注':'专注阅读';
};
let evidenceReturnFocus=null;
const modalBackground=['#expertPanel > .sidebar','#expertPanel > .reader',
                        '#expertPanel > .judgment','#reviewPane','#workflowNav','#workFooter'];
function openEvidence(){
 if(!$('evidencePane').hidden)return;
 evidenceReturnFocus=document.activeElement;
 $('expertPanel').classList.add('evidence-open');
 $('evidencePane').hidden=false;
 $('evidenceToggle').setAttribute('aria-expanded','true');
 renderEvidenceReview();showEvidenceTab('linked');
 $('closeEvidence').focus();
}
$('evidenceToggle').onclick=()=>{
 if($('evidencePane').hidden)openEvidence();else closeEvidence();
};
// P1.2 explicit human-chosen classification; lossless within the canonical schema.
$('nativeAdd').onclick=()=>{
  try{
    if(!model?.allowed_actions.includes('draft') || !draft)throw Error('JUDGMENT_NOT_EDITABLE');
    const field=$('nativeCategory').value;
    const text=$('nativeStatement').value;
    const before=payload();
    const after=appendNaturalEntry(profile,before,field,text);
    const el=$('judgmentForm').querySelector('[data-key="'+field+'"]');
    if(!el)throw Error('MISSING_CANONICAL_FIELD');
    el.value=after[field].join('\n');
    el.closest('details.group').open=true;let ancestor=el.parentElement;while(ancestor && ancestor!==$('judgmentForm')){if(ancestor.tagName==='DETAILS')ancestor.open=true;ancestor=ancestor.parentElement;}
    el.dispatchEvent(new Event('input',{bubbles:true}));
    $('nativeStatement').value='';
    $('nativeMappingStatus').textContent='已追加原话 · '+canonicalPaths(profile).length+'个科学字段均保留 · 请保存草稿';
  }catch(e){$('nativeMappingStatus').textContent='无法加入：'+e.message;}
};
api('/v1/session').then(enter).catch(reset);

$('judgmentForm').addEventListener('input',()=>{if(model?.allowed_actions.includes('draft')&&draft){const dirty=JSON.stringify(payload())!==JSON.stringify(draft.payload);$('freeze').disabled=saving||dirty||draft.revision<1;if(!saving)note(dirty?'当前修改尚未保存':draft.revision>=1?'已保存':'草稿尚未保存');}});

// P1.3 prototype fidelity: navigation and review are views of authoritative fields.
function submissionReadiness(){
 const canDraft=!!model?.allowed_actions?.includes('draft');
 const hasForm=!!draft&&!!$('judgmentForm').querySelector('[data-key]');
 if(!hasForm)return {canDraft,filled:0,dirty:true,saved:false,eligible:false,reasons:['尚未载入可编辑的判断']};
 const data=payload();
 const filled=judgmentSections.filter(section=>section.primary.some(key=>{
   const val=get(data,key);return Array.isArray(val)?val.some(x=>String(x).trim()):!!String(val??'').trim();
 })).length;
 const dirty=JSON.stringify(data)!==JSON.stringify(draft.payload);
 const saved=Number.isInteger(draft.revision)&&draft.revision>=1&&!dirty&&!saving;
 const reasons=[];
 if(!canDraft)reasons.push('当前任务阶段不允许独立冻结');
 if(filled===0)reasons.push('尚未记录独立判断（0/5）');
 if(!saved)reasons.push(dirty?'有未保存的修改，请先保存草稿':'草稿尚未保存到服务端');
 if(saving)reasons.push('保存操作尚未完成');
 // 5/5 describes coverage, not a scientific claim that every clinical section
 // must be filled; documented uncertainty/abstention remains legitimate.
 return {canDraft,filled,dirty,saved,eligible:canDraft&&filled>0&&saved,reasons};
}
function showStage(stage){
 if(!['reader','judgment','review','freeze'].includes(stage))return;
 if(stage==='freeze' && !submissionReadiness().eligible){
   viewStage='review';
   $('saveStatus').textContent='冻结尚未就绪：请检查草稿保存和判断完整性';
 }else{viewStage=stage==='freeze'?'review':stage;}
 const review=viewStage==='review';
 $('expertPanel').classList.toggle('reviewing',review);
 $('reviewPane').hidden=!review;
 closeEvidence();
 if(review)renderReview();
 if(stage==='judgment'){
   $('judgmentPane').scrollIntoView({block:'nearest'});
   $('judgmentForm').querySelector('textarea:not(:disabled)')?.focus({preventScroll:true});
 }
 if(stage==='freeze'&&submissionReadiness().eligible)$('unexposed').focus({preventScroll:true});
 refreshPresentation();
}
function refreshPresentation(){
 if(!profile||!draft||!$('judgmentForm').querySelector('[data-key]'))return;
 const state=submissionReadiness();
 const frozenNow=!!model?.phase?.endsWith('LOCKED');
 $('draftProgress').textContent=state.canDraft?`已填写 ${state.filled}/5 · ${state.saved?'已保存':'未保存'} · 证据 ${evidenceBindings.length}`:`已填写 ${state.filled}/5 · ${frozenNow?'已冻结（只读）':'只读'} · 证据 ${evidenceBindings.length}`;
 $('nextReview').hidden=viewStage==='review';
 $('footerBack').hidden=viewStage!=='review';
 $('freezeReason').textContent=!state.canDraft?(frozenNow?'✓ 独立判断已冻结，记录不可修改。':''):state.eligible?($('unexposed').checked?'可以冻结：提交后不可修改。':'请勾选下面的确认项后再冻结。'):'暂不能冻结：'+state.reasons.join('；');
 $('freezeReason').classList.toggle('ok',state.eligible||frozenNow);
 $('evidenceCount').textContent=String(evidenceBindings.length);
 $('nextReview').disabled=saving;
 $('nextReview').textContent=model?.allowed_actions.includes('draft')?'核查判断与证据 →':'查看判断与证据 →';
 $('freeze').disabled=!state.eligible || !$('unexposed').checked;
 const stages=['reader','judgment','review','freeze'];
 // Navigation is NOT evidence of stage completion; scientific freeze is
 // the only authoritative completion receipt for the workflow stepper.
 const frozen=!!model?.phase?.endsWith('LOCKED');
 const progress=[frozen,frozen,frozen,frozen];
 for(const step of $('workflowNav').querySelectorAll('[data-stage]')){
   const index=stages.indexOf(step.dataset.stage);
   step.classList.toggle('active',frozen?step.dataset.stage==='freeze':step.dataset.stage===viewStage);
   step.classList.toggle('done',progress[index] && step.dataset.stage!==viewStage);
   step.setAttribute('aria-current',step.dataset.stage===viewStage?'step':'false');
   if(index===3){step.disabled=!state.eligible&&!frozen;step.title=state.eligible?'可进入冻结确认':'需先完成并保存独立判断';}
 }
 refreshItemOptions();
 window.nutriReader?.updateConfirmation?.();
 renderJudgmentItemRows();
 if(!$('evidencePane').hidden)renderEvidenceReview();
 if(viewStage==='review')renderReview();
}
function renderReview(){
 $('reviewFields').replaceChildren();$('reviewChecks').replaceChildren();$('reviewAnchors').replaceChildren();
 if(!profile||!draft||!$('judgmentForm').querySelector('[data-key]')){
  const p=document.createElement('p');p.className='small';p.textContent='当前阶段没有独立判断草稿，请按任务授权复核候选。';$('reviewFields').append(p);return;
 }
 const data=payload();
 const primaryKeys=judgmentSections.flatMap(section=>section.primary);
 const extra=document.createElement('details');extra.className='advanced-fields';const summary=document.createElement('summary');summary.textContent='查看补充判断与完整字段记录';extra.append(summary);
 for(const field of profile.field_groups.flatMap(g=>g.fields)){
  const v=get(data,field.key),empty=Array.isArray(v)?v.length===0:v===null||v==='';
  const block=document.createElement('div');block.className='review-field'+(empty?' empty':'');
  const title=document.createElement('h3');title.textContent=expertFieldTitles[field.key]||field.label;
  const text=document.createElement('p');text.textContent=empty?'尚未填写（不自动推断或补全）':Array.isArray(v)?v.join('\n'):String(v);block.append(title,text);(primaryKeys.includes(field.key)?$('reviewFields'):extra).append(block);
 }
 $('reviewFields').append(extra);
 const dirty=JSON.stringify(data)!==JSON.stringify(draft.payload);
 const ready=submissionReadiness();
 const checks=[ready.saved?'草稿已由服务端保存，当前无未保存修改。':ready.dirty?'当前修改尚未保存，不能冻结。':'草稿版本尚未保存，不能冻结。',
   `五组专业判断已填写 ${ready.filled}/5；未填写的组应明确记录适用性或不确定性。`,
   `原文证据绑定 ${evidenceBindings.length} 条（以服务端绑定记录为准）`,
   ready.eligible?'满足前端最低检查；仍须确认盲法并通过服务端冻结验证。':`尚不能冻结：${ready.reasons.join('；')}`,
   '当前仅限合成练习；真实专家科研采集仍未开放。'];
 for(const text of checks){const p=document.createElement('div');p.className='check-line';p.textContent=text;$('reviewChecks').append(p);}
 $('reviewItemLinks').replaceChildren();
 const current=evidenceItemBindings.filter(b=>{
  const item=entriesForField(b.field,data).find(x=>x.index===b.item_index);
  return item&&itemEvidence(b.field,item.index,item.text).links.some(x=>x.binding===b);
 });
 const stale=evidenceItemBindings.filter(x=>!current.includes(x));
 const itemSummary=document.createElement('p');
 itemSummary.textContent=`精确到判断条目的证据 ${current.length} 条；旧版字段级证据不能自动算作逐条证据。`+
   (stale.length?` ⚠ ${stale.length} 条引用对应的判断已改变，需重新确认。`:'');
 $('reviewItemLinks').append(itemSummary);
 renderEvidenceReview(null,null,$('reviewAnchors'));
}
function closeEvidence(){
 const wasOpen=!$('evidencePane').hidden;
 $('evidencePane').hidden=true;
 $('expertPanel').classList.remove('evidence-open');
 $('evidenceToggle').setAttribute('aria-expanded','false');
 for(const q of modalBackground){const element=document.querySelector(q);if(element)element.inert=false;}
 if(wasOpen){
   const target=evidenceReturnFocus?.isConnected?evidenceReturnFocus:$('evidenceToggle');
   target.focus({preventScroll:true});
 }
 evidenceReturnFocus=null;
}
$('closeEvidence').onclick=closeEvidence;
$('field').addEventListener('change',()=>chooseEvidenceField($('field').value));
$('selectionField').addEventListener('change',()=>chooseEvidenceField($('selectionField').value));
$('drawerSubmitReview').onclick=()=>showStage('review');
$('nextReview').onclick=()=>showStage('review');$('backEdit').onclick=()=>showStage('judgment');$('footerBack').onclick=()=>showStage('judgment');$('quoteNext').onclick=()=>{closeEvidence();$('units').focus({preventScroll:true});};
for(const step of $('workflowNav').querySelectorAll('[data-stage]'))step.onclick=()=>showStage(step.dataset.stage);
$('unexposed').addEventListener('change',refreshPresentation);
$('judgmentForm').addEventListener('input',refreshPresentation);
window.addEventListener('nutri-pdf-verification',e=>{pdfVerification[e.detail.anchor_id]=e.detail.verified;refreshPresentation();});
window.addEventListener('nutri-evidence',e=>{if(!e.detail.items.length)pdfVerification={};evidenceItems=e.detail.items;evidenceBindings=e.detail.bindings;evidenceItemBindings=e.detail.itemBindings||[];refreshPresentation();});
for(const id of ['evidenceItem','selectionItem'])$(id).addEventListener('change',()=>{
  evidenceItemIndex=$(id).value;
  for(const other of ['evidenceItem','selectionItem'])$(other).value=evidenceItemIndex;
  window.nutriReader?.updateConfirmation?.();
});
window.addEventListener('keydown',e=>{
 if($('evidencePane').hidden)return;
 if(e.key==='Escape'){e.preventDefault();closeEvidence();return;}
});
window.addEventListener('beforeunload',e=>{if(model?.allowed_actions.includes('draft')&&draft&&JSON.stringify(payload())!==JSON.stringify(draft.payload)){e.preventDefault();e.returnValue='';}});

function itemEvidence(field,index,text){
 const savedText=entriesForField(field,draft.payload).find(x=>x.index===index)?.text;
 return judgmentEvidence({field,index,text,savedText,bindings:evidenceItemBindings,anchors:evidenceItems,pdfStatus:pdfVerification});
}
function renderEvidenceReview(field=null,index=null,root=$('evidenceReviewList')){
 root.replaceChildren();if(!draft||!profile)return;
 const data=payload();let missing=0,stale=0,pending=0;
 for(const f of profile.field_groups.flatMap(g=>g.fields)){
  if(!['ordered_string_list','nullable_string'].includes(f.type))continue;
  for(const item of entriesForField(f.key,data)){
   const status=itemEvidence(f.key,item.index,item.text);
   if(!status.links.length&&!sourceOptionalFields.has(f.key))missing++;stale+=status.stale;
   pending+=status.links.filter(x=>!x.pdfVerified).length;
   if(field!==null&&(f.key!==field||item.index!==index))continue;
   const card=document.createElement('section');card.className='evidence-review-card';
   const heading=document.createElement('h4');heading.textContent=expertFieldTitles[f.key]||f.label;
   const statement=document.createElement('p');statement.textContent=item.text;card.append(heading,statement);
   const state=document.createElement('p');state.className='small evidence-state';
   state.textContent=status.stale?`${status.stale} 条旧关联需重新确认（此位置的判断已修改或删除）；有效证据 ${status.links.length} 条`:status.links.length?`已关联 ${status.links.length} 条证据`:sourceOptionalFields.has(f.key)?'可选 · 问题本身无需来源':'待补充来源 · 尚无逐条关联的证据';card.append(state);
   for(const {anchor,pdfVerified} of status.links){
    const quote=document.createElement('blockquote');quote.textContent=anchor.quote;
    const label=document.createElement('p');label.className='small';label.textContent=`${anchor.unit_id} · 原文范围：服务端已校验 · 判断关联：当前有效 · PDF：${pdfVerified?'已核验':'本次会话未核验'}`;
    const replay=document.createElement('button');replay.className='ghost mini';replay.textContent='回看原文';
    replay.onclick=()=>{showStage('reader');window.dispatchEvent(new CustomEvent('nutri-replay-source',{detail:{anchor,view:'source'}}));};
    const pdf=document.createElement('button');pdf.className='ghost mini';pdf.textContent='核验 PDF';
    pdf.onclick=()=>{showStage('reader');window.dispatchEvent(new CustomEvent('nutri-replay-source',{detail:{anchor,view:'pdf'}}));};
    card.append(quote,label,replay,pdf);
   }
   const edit=document.createElement('button');edit.className='text-button';edit.textContent=status.links.length?'补充证据关联':'选择原文并关联';
   edit.onclick=()=>startCiting(f.key,item.index);card.append(edit);root.append(card);
  }
 }
 if(!root.children.length){const empty=document.createElement('p');empty.className='small';empty.textContent='还没有可核查的判断。填写并保存判断后，可逐条关联原文。';root.append(empty);}
 if(root===$('reviewAnchors')){
  stale=evidenceItemBindings.filter(b=>{const item=entriesForField(b.field,data).find(x=>x.index===b.item_index);return !item||!itemEvidence(b.field,item.index,item.text).links.some(x=>x.binding===b);}).length;
  const issues=document.createElement('p');issues.className='check-line';issues.textContent=`待核查：${missing} 条判断缺少来源；${stale} 条旧关联需确认；${pending} 条证据 PDF 本次会话未核验。`;root.prepend(issues);}
 renderStaleBindings(root,data);
}

function staleBindings(data){
 return evidenceItemBindings.filter(b=>{const item=entriesForField(b.field,data).find(x=>x.index===b.item_index);return !item||!itemEvidence(b.field,item.index,item.text).links.some(x=>x.binding===b);});
}
function renderStaleBindings(root,data){
 const stale=staleBindings(data);if(!stale.length)return;
 const box=document.createElement('section');box.className='stale-bindings';
 const h=document.createElement('h4');h.textContent=`失效的旧关联（${stale.length}）`;box.append(h);
 const p=document.createElement('p');p.className='small';p.textContent='下面的引文原本支撑的判断已被修改或删除。审计记录保留不可删除；如仍需要，请对当前判断重新选取原文并关联。';box.append(p);
 for(const b of stale){
  const anchor=evidenceItems.find(a=>a.anchor_id===b.anchor_id);
  const row=document.createElement('div');row.className='stale-row';
  const meta=document.createElement('small');meta.textContent=`原关联：${fieldShortTitles[b.field]||b.field} 第 ${b.item_index+1} 条（草稿版本 ${b.draft_revision}）`;
  const quote=document.createElement('blockquote');quote.textContent=anchor?anchor.quote:'（原引文不可用）';
  row.append(meta,quote);box.append(row);
 }
 root.append(box);
}
function showEvidenceTab(tab){
 $('evidenceReviewList').hidden=tab!=='linked';$('quoteComposer').hidden=tab!=='quote';
 $('drawerSubmitReview').hidden=tab!=='linked';
 $('evidenceDialogTitle').textContent=tab==='quote'?'引文确认':'判断与证据核查';
 $('tabQuote').classList.toggle('active',tab==='quote');$('tabLinked').classList.toggle('active',tab==='linked');
 if(tab==='quote'){$('quoteComposer').open=true;window.nutriReader?.updateConfirmation?.();}
}
$('tabQuote').onclick=()=>showEvidenceTab('quote');$('tabLinked').onclick=()=>showEvidenceTab('linked');
$('tabJudgment').onclick=()=>showStage('judgment');
window.addEventListener('nutri-confirm-quote',()=>{openEvidence();showEvidenceTab('quote');});
