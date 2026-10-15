/* Scientific Source Studio V2 — Demo-faithful UI mounted in Workbench.
 * Old p2_source_studio.* is intentionally untouched.
 * Queue/register use existing /v1/p2/* (synthetic only).
 */
'use strict';
window.p2SourceStudioV2=(()=>{
'use strict';
const ico=(name,cl='')=>`<svg class="ico ${cl}" aria-hidden="true"><use href="#ic-${name}"/></svg>`;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sources=[
{id:'SYN-GUIDE-026',rev:'r3',title:'成人营养管理指南 · 结构化教学示例',year:'2026',journal:'合成指南',kind:'指南/共识',status:'QA_PENDING',rights:'SYNTHETIC_ATTESTED',qa:8,total:12,project:'PRJ-SYN-001',batch:'BATCH-SYN-03',owner:'Curator',roletext:'继续 Unit QA',raw:'a3f2e7c9b4d1e366214f0810f4fceee9bc840afe4a582c2d77e286825b2c9fba',doc:'d9c4b7e2a1f3f3e723a5bf7e6d90c810e8afe5c9b38e719b9c367029da8e3c1b',package:'',clinical:true,sourceType:'SYNTHETIC',outline:'营养管理与随访' },
{id:'SYN-RCT-017',rev:'r1',title:'膳食补充与骨密度变化 · 模拟随机研究',year:'2025',journal:'合成研究',kind:'RCT',status:'RIGHTS_HOLD',rights:'NOT_REVIEWED',qa:0,total:12,project:'PRJ-SYN-002',batch:'BATCH-SYN-02',owner:'Auditor',roletext:'审核模拟用途',raw:'bc39d9a2740b55403e95018401cd21f74506bc7d38fa93ba90ca7b8ee5d0a771',doc:'',package:'',clinical:false,sourceType:'SYNTHETIC'},
{id:'SYN-SR-055',rev:'r2',title:'膳食模式与代谢风险 · 合成系统综述',year:'2024',journal:'合成综述',kind:'系统综述',status:'RIGHTS_ACCEPTED',rights:'SYNTHETIC_ATTESTED',qa:0,total:18,project:'PRJ-SYN-001',batch:'BATCH-SYN-01',owner:'Producer',roletext:'准备结构化',raw:'c9037ae44743cf27645bace1ed0e348ea29bd0f9ce02261ce70da55bf95301ab',doc:'',package:'',clinical:false,sourceType:'SYNTHETIC'},
{id:'SYN-OBS-031',rev:'r1',title:'营养行为与健康变化 · 模拟观察性队列',year:'2023',journal:'合成队列',kind:'观察性研究',status:'QA_HOLD',rights:'SYNTHETIC_ATTESTED',qa:3,total:20,project:'PRJ-SYN-003',batch:'BATCH-SYN-02',owner:'Curator',roletext:'处理 QA 问题',raw:'d516d17cc5d6ee110a6e6a1c9e3aa1f9a43312f52c26b03f854c588b7d958019',doc:'aa2db0019c653ea94c77fbb714a3163d0e129f868628a67260dc7db7ac558721',package:'',clinical:false,sourceType:'SYNTHETIC'},
{id:'SYN-PKG-010',rev:'r4',title:'儿童铁营养资料包 · 虚构规则演示',year:'2023',journal:'内部合成包',kind:'资料包',status:'PACKAGE_FROZEN',rights:'SYNTHETIC_ATTESTED',qa:12,total:12,project:'PRJ-SYN-001',batch:'BATCH-SYN-01',owner:'Reviewer',roletext:'查看冻结包',raw:'e603bf9e42ba3d0806828d351c6e7d721c51d06264bbc61174b7f8f5a0523bd5',doc:'f774f808afe4161f303a2b9c180f7c649f3f0a9bc1783390cb9c2d96f4d00523',package:'0a7ce3204ed147a9f9b9013d2a4bc78eaa0f103b2654edc30d81ee2559fe3321',clinical:false,sourceType:'SYNTHETIC'},
{id:'DEMO-ONLY-006',rev:'v0',title:'演示占位资料 · 不进入实验样本池',year:'—',journal:'DEMO ONLY',kind:'其他',status:'DEMO_ONLY',rights:'NOT_ELIGIBLE',qa:0,total:0,project:'',batch:'',owner:'—',roletext:'只读说明',raw:'',doc:'',package:'',clinical:false,sourceType:'DEMO'}
];
const statuses={RIGHTS_HOLD:{label:'待用途审核',color:'amber',desc:'需独立 Auditor 核查模拟使用权限'},RIGHTS_ACCEPTED:{label:'待结构化',color:'blue',desc:'Producer 可启动模拟结构化处理'},QA_PENDING:{label:'待人工 QA',color:'purple',desc:'Curator 逐 Unit 核验结构化内容'},QA_HOLD:{label:'QA 阻断',color:'red',desc:'必须处理问题并形成新版本'},PACKAGE_FROZEN:{label:'已封存',color:'green',desc:'来源包冻结不代表专家授权或 Gold'},DEMO_ONLY:{label:'只读演示',color:'dark',desc:'不是持久化合成来源'}};
const state={page:'queue',filter:false,selected:'SYN-GUIDE-026',selectedRev:'r3',search:'',kind:'',stage:'',project:'',batch:'',sourceType:'ALL',queuePage:1,perPage:5,readerTab:'bilingual',readerUnit:1,readerAnchor:0,readerIssueTab:'checklist',readerZoom:100,versionTab:'lineage',auditFilter:'',matrixFilter:'',modal:'',wizard:1,form:{title:'',kind:'系统综述',identifier:'',year:'2026',project:'PRJ-SYN-001',batch:'BATCH-SYN-01',note:'',raw:''},showHistorical:false,qaLocal:{},auditEvents:[{date:'2026-10-10 09:20',type:'SOURCE_REGISTERED',actor:'Producer',rev:'r1',description:'登记合成来源与标识信息'},{date:'2026-10-10 09:45',type:'RIGHTS_RECORDED',actor:'Auditor',rev:'r1',description:'合成用途范围审核记录'},{date:'2026-10-11 11:24',type:'CONVERSION_FROZEN',actor:'Producer',rev:'r2',description:'结构化 Unit 与解析追溯冻结'},{date:'2026-10-12 15:05',type:'UNIT_QA_RECORDED',actor:'Curator',rev:'r3',description:'第 1—8 个模拟 Unit QA 留痕'}]};
const units=[
{id:'U-01',type:'观察数据',title:'膳食记录是观察，不自动代表长期习惯',english:'A single 24-hour dietary recall is an observation of reported intake. It does not establish an individual’s habitual diet or a clinical diagnosis.',zh:'一次 24 小时膳食回顾仅观察报告的摄入量，不能直接认定个体的长期膳食习惯或临床诊断。',quote:'A single 24-hour dietary recall is an observation of reported intake.',anchor:{start:0,end:68,verified:true},page:1,section:'Methods / Dietary assessment'},
{id:'U-02',type:'证据适用性',title:'人群适用边界',english:'Evidence generated in a particular population requires independent applicability assessment before being used for a different population, setting, or outcome.',zh:'特定人群产生的科学证据用于其他人群、场景或结局时，需要独立进行适用性评价。',quote:'requires independent applicability assessment',anchor:{start:57,end:101,verified:true},page:2,section:'Methods / Scope'},
{id:'U-03',type:'条件性行动',title:'资料不足时 ASK / DEFER',english:'When the available information does not meet the decision threshold, the appropriate next step may be ASK, DEFER, or NO_CHANGE rather than an unsupported intervention.',zh:'信息不足以满足决策阈值时，合理的下一步可能是询问、推迟或不改变，而非没有依据地实施干预。',quote:'ASK, DEFER, or NO_CHANGE',anchor:{start:109,end:133,verified:true},page:3,section:'Decision / Sufficiency'},
{id:'U-04',type:'纵向监测',title:'监测和重新决策触发条件',english:'A monitoring plan should define what will be observed, the review interval, and explicit triggers for re-decision. Planned actions, execution, and outcomes remain distinct.',zh:'监测计划应规定观察指标、复查间隔和重新决策触发条件；拟议行动、实际执行和结局始终独立记录。',quote:'explicit triggers for re-decision',anchor:{start:81,end:114,verified:true},page:4,section:'Follow-up / Monitoring'}
];
// Bind each synthetic anchor to one exact Unit text occurrence. No PDF position is inferred.
for(const unit of units){const pos=unit.english.indexOf(unit.quote);const unique=pos>=0&&unit.english.indexOf(unit.quote,pos+1)===-1;unit.anchor={start:unique?pos:null,end:unique?pos+unit.quote.length:null,verified:unique};}
const governance=[
['01','Scientific authority / 临床适用','R6 当前规范原件缺失','blocked'],['02','SIS Core 结构不膨胀','静态语义对齐','aligned'],['03','Observation / State / Truth 分离','静态语义对齐','aligned'],['04','双层科学证据 / Applicability','需精确 Adapter 映射','pending'],['05','信息充分性与条件性决策','静态语义对齐','aligned'],['06','Human–Ontology Separation','静态语义对齐','aligned'],['07','Set-valued Reference','静态语义对齐','aligned'],['08','Strict exposure / 反后见之明','运行时测试未完成','pending'],['09','纵向监测 / Re-decision','静态语义对齐','aligned'],['10','临床长程决策 LHDI','R6 原件缺失；待评估','blocked'],['11','Estimand-first Program 路由','静态语义对齐','aligned'],['12','SIS R5 精确来源快照','181565-byte 目标待恢复','blocked'],['13','SIS-MED R6 P0.4 原件','61116-byte 目标待恢复','blocked'],['14','AI Nutri v2.1 ⇄ NDSF','正式版本绑定待补','pending'],['15','物理契约 / 运行时合格性','未执行完整 Non-Regression','pending']
];
let app=null,overlay=null;
let v2DeepLink=null; // exact (id,revision) selected by independent reviewer route; DENY until server confirms

const TYPE_MAP={RANDOMIZED_TRIAL:'RCT',OBSERVATIONAL_STUDY:'观察性研究',SYSTEMATIC_REVIEW_META:'系统综述',GUIDELINE:'指南/共识',CONSENSUS:'专家共识',NARRATIVE_REVIEW:'叙述性综述',CORRECTION_RETRACTION:'更正/撤稿'};
const TYPE_TO_API={'指南/共识':'GUIDELINE','RCT':'RANDOMIZED_TRIAL','系统综述':'SYSTEMATIC_REVIEW_META','观察性研究':'OBSERVATIONAL_STUDY','资料包':'GUIDELINE','其他':'NARRATIVE_REVIEW'};
// Only server projections may be SYNTHETIC/persisted. HiFi fixtures are
// explicitly DEMO, even when their illustrative lifecycle says QA_PENDING.
const DEMO_SEED=sources.map(x=>({...x,sourceType:'DEMO',live:false,
  rights:'NOT_ELIGIBLE',raw:'',doc:'',package:'',project:'',batch:'',qa:0}));
sources.splice(0,sources.length,...DEMO_SEED.map(x=>({...x})));
let liveMeta={role:'manager',session:null,projects:[],batchMap:new Map(),scope:{project:'',batch:''},notice:''};
let sourcesEpoch=0; // invalidates stale async metadata reads across logout/scope changes
function v2Api(path,opts={}){
  const headers={'Accept':'application/json'};
  if(opts.body!==undefined)headers['Content-Type']='application/json';
  const p=liveMeta.session||(typeof auth!=='undefined'?auth:null);
  if(opts.method&&opts.method!=='GET'&&p?.csrf_token)headers['x-csrf-token']=p.csrf_token;
  return fetch(path,{method:opts.method||'GET',body:opts.body?JSON.stringify(opts.body):undefined,
    credentials:'same-origin',cache:'no-store',headers}).then(async r=>{
    const payload=await r.json().catch(()=>({}));
    if(!r.ok)throw new Error(payload.detail?.code||String(payload.detail||r.status));
    return payload;
  });
}
function mapLive(x){
  const rights=(x.rights_status==='APPROVE_SYNTHETIC'||x.rights_status==='SYNTHETIC_RIGHTS_ATTESTED')?'SYNTHETIC_ATTESTED':'NOT_REVIEWED';
  const next={RIGHTS_HOLD:['Auditor','等待独立用途审核'],RIGHTS_ACCEPTED:['Producer','进入结构化转换'],
    QA_PENDING:['Curator','继续 Unit QA'],QA_HOLD:['Curator','查看 QA 阻断'],PACKAGE_FROZEN:['Producer','查看冻结资料包']};
  const n=next[x.status]||['—','查看详情'];
  return {id:x.source_id,rev:x.revision_id,title:x.title,year:'—',journal:'发表信息未核验',
    kind:TYPE_MAP[x.source_type]||x.source_type||'其他',status:x.status,rights,
    qa:x.reviewed_units||0,total:x.unit_count||0,project:'',
    batch:'',owner:n[0],roletext:n[1],
    raw:x.raw_artifact_sha256||'NOT_COMPUTED',doc:x.document_sha256||'',package:x.package_sha256||'',
    clinical:false,sourceType:'SYNTHETIC',live:true,outline:x.identifier||'',identifier:x.identifier||'',
    raw_format:x.raw_format||'MARKDOWN'};
}
async function reloadLive(){
  const epoch=++sourcesEpoch;
  try{
    const p=new URLSearchParams({limit:'100',offset:'0'});
    if(state.project)p.set('project_id',state.project);
    if(state.batch)p.set('batch_id',state.batch);
    const meta=await v2Api('/v1/p2/sources?'+p);
    let rows=meta.sources||[],offset=rows.length;
    while(offset<meta.total&&offset<3000){
      p.set('offset',String(offset));
      const next=await v2Api('/v1/p2/sources?'+p);if(!next.sources?.length)break;
      rows=rows.concat(next.sources);offset=rows.length;
    }
    if(epoch!==sourcesEpoch)return;
    const live=rows.map(mapLive);
    const demos=DEMO_SEED.map(x=>({...x}));
    sources.splice(0,sources.length,...live,...demos);
    if(v2DeepLink){
      const matched=live.some(s=>s.id===v2DeepLink.id&&s.rev===v2DeepLink.rev);
      v2DeepLink.status=matched?'CONFIRMED':'DENIED';
      if(matched){state.selected=v2DeepLink.id;state.selectedRev=v2DeepLink.rev;}
    }else if(live.length&&!live.some(s=>s.id===state.selected&&s.rev===state.selectedRev)){
      state.selected=live[0].id;state.selectedRev=live[0].rev;
    }
    liveMeta.notice=v2DeepLink?.status==='DENIED'?
      'Deep link SourceVersion 不存在或当前角色无权访问；没有选择其他版本替代。':'';
  }catch(err){
    if(epoch!==sourcesEpoch)return;
    // Fail visibly. Never retain a previously loaded source as if fresh.
    liveMeta.notice='P2 后端读取失败，当前只显示 DEMO：'+err.message;
    if(v2DeepLink)v2DeepLink.status='DENIED';
    sources.splice(0,sources.length,...DEMO_SEED.map(x=>({...x})));
    if(!sources.some(x=>x.id===state.selected&&x.rev===state.selectedRev)){
      state.selected=sources[0].id;state.selectedRev=sources[0].rev;
    }
  }
  if(epoch===sourcesEpoch&&app?.isConnected){await readFlow();render();}
}

function tag(text,cls='dark'){return `<span class="tag ${cls}">${esc(text)}</span>`}
function status(s){const v=statuses[s]||statuses.DEMO_ONLY;return tag(v.label,v.color)}
function button(label,action='noop',cls='',iconName='',more=''){return `<button type="button" class="btn ${cls}" data-act="${action}" ${more}>${iconName?ico(iconName,'sm'):''}${label}</button>`}
function toast(message){let el=document.getElementById('p2v2ToastHolder');el.innerHTML=`<div class="toast">${ico('info') } <span>${esc(message)}</span><button type="button" data-act="dismissToast" style="color:white;background:none;border:0;margin-left:9px">×</button></div>`;clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.replaceChildren(),5200)}
function pg(label){state.page=label;state.filter=false;state.modal='';overlay.replaceChildren();window.scrollTo({top:0,behavior:'instant'});render();if(selected()?.live)readFlow()}
function selected(){return sources.find(x=>x.id===state.selected&&x.rev===state.selectedRev)||sources.find(x=>x.id===state.selected)||sources[0]}
function filterSources(){const q=state.search.toLowerCase().trim();return sources.filter(x=>(state.sourceType==='ALL'||x.sourceType===state.sourceType)&&(!q||[x.title,x.id,x.kind,x.journal].some(v=>v.toLowerCase().includes(q)))&&(!state.kind||x.kind===state.kind)&&(!state.stage||x.status===state.stage)&&(!state.project||x.live||x.project===state.project)&&(!state.batch||x.live||x.batch===state.batch))}
function names(){return {queue:['工作队列总览','按状态处理科学来源，先找到材料，再进入操作'],intake:['来源登记与筛选','将身份登记、用途审核与 Project/Batch 使用意图分开管理'],qa:['结构化 QA 阅读器','原文为权威，译文为辅助；证据锚点需要可复核的精确坐标'],audit:['版本谱系与规范审计','核对 SHA、冻结回执、引用历史和当前上游科学规范']}[state.page]}
function header(){const [title,desc]=names();const act=state.page==='qa'?[button('返回工作队列','queue','primary','chevronleft'),button('查看版本谱系','audit','','timeline'),button('规范审计','governance','','shield')]:state.page==='audit'?[button('返回工作队列','queue','primary','chevronleft'),button('记录项目 / 批次引用','openBind','','link'),button('导出模拟审计','exportAudit','','download')]:[button('登记新来源','openRegister','primary','plus'),button('查看版本与引用','audit','','timeline'),button('审计与规范','governance','','shield')];return `<div class="page-head"><div class="grow"><div class="eyebrow">P2 / SCIENTIFIC SOURCE WORKSPACE · V2.1 受控合成流程</div><h1 class="page-title">科学资料处理台</h1><div class="page-desc">${desc} · <span class="page-gloss">V2.1 · 合成来源服务端操作 + 独立 DEMO · 权限分离 · 非真实 PDF/Gold/专家暴露</span></div></div><div class="actions">${act.join('')}</div></div><div class="page-stepper" aria-label="原型分页面">${[['queue','01','工作队列总览'],['intake','02','筛选与来源登记'],['qa','03','QA 阅读与锚点核验'],['audit','04','版本谱系与审计']].map(([id,no,l])=>`<button class="stepitem ${id===state.page?'active':''}" data-page="${id}" ${id===state.page?'aria-current="page"':''}><span class="stepno">${no}</span>${l}</button>`).join('')}</div>`}
function qualRow(iconName,title,sub,txt,color){return `<div class="qual-row">${ico(iconName,'sm')}<div class="tight"><div class="qual-name">${title}</div><div class="qual-sub truncate">${sub}</div></div><div class="right">${tag(txt,color)}</div></div>`}
function selectedDetail(){const s=selected();const isPending=s.status==='RIGHTS_HOLD';const synthetic=s.live===true;const current=!s.live?`DEMO ONLY · 示例阶段：${statuses[s.status].label}`:s.status==='QA_PENDING'?'当前阶段 · 待人工 QA':`当前阶段 · ${statuses[s.status].label}`;return `<section class="card detail"><div class="between"><div class="card-title">${ico('file')} 来源详情</div><span class="mono subtle">${esc(s.id)} / ${esc(s.rev)}</span></div><div class="between" style="margin-top:4px"><div class="detail-title">${esc(s.title)}</div>${tag(s.sourceType==='DEMO'?'演示占位':s.kind,'outline')}</div><div class="small subtle">${esc(s.year)} · ${esc(s.journal)} · ${synthetic?'合成来源':'DEMO ONLY'}</div><div class="status-hero"><div class="bubble">${ico('file','lg')}</div><div><strong>${current}</strong><div class="tiny" style="color:#8f7ba8;margin-top:3px">${esc(statuses[s.status].desc)}。</div></div></div><div class="between"><div class="card-title">${ico('shield')} 来源资格 · 五维状态</div>${ico('info','sm')}</div><div class="qual-list">${qualRow('file','原件完整性','完整性为合成记录检查',synthetic?'已记录':'不可用',synthetic?'green':'dark')}${qualRow('shield','使用授权','不等同真实出版商许可',s.live&&s.rights==='SYNTHETIC_ATTESTED'?'仅合成核准':s.live?'未审核':'DEMO 无资格',s.rights==='SYNTHETIC_ATTESTED'?'green':'amber')}${qualRow('gear','结构化转换','保留 Parser 与 Unit 版本',s.live&&s.doc?'合成结构化已记录':s.live?'未完成':'DEMO 未核验',s.doc?'green':'amber')}${qualRow('list','Unit QA','独立 Curator 的单元核查',(s.live?s.qa+' / '+s.total:'DEMO 未审查'),s.live&&s.qa===s.total&&s.total?'green':'blue')}${qualRow('lock','专家暴露','独立授权，不由来源页面签发','未授权','red')}</div><div class="banner warn">${ico('alert','sm')}资料来源合格、专家参考真值、Gold 资格与专家可见性不能混同。</div><div class="small-title">${ico('link','sm')} 版本与引用</div><dl class="kv"><dt>Raw SHA-256</dt><dd class="codechip" title="${esc(s.raw||'NOT_AVAILABLE')}">${esc(s.raw?`${s.raw.slice(0,14)}…${s.raw.slice(-8)}`:'NOT_AVAILABLE')}</dd><dt>Canonical SHA</dt><dd class="codechip" title="${esc(s.doc||'NOT_CONVERTED')}">${esc(s.doc?`${s.doc.slice(0,14)}…${s.doc.slice(-8)}`:'NOT_CONVERTED')}</dd><dt>Project / Batch</dt><dd>${s.live?'引用详情需从独立 SourceVersion 回执核对':esc(s.project||'DEMO 未绑定')+' / '+esc(s.batch||'—')}</dd><dt>勘误 / 撤稿</dt><dd>${s.status==='QA_HOLD'?'示例 QA 问题待处理':'未声明 · 不等于真实已核查'}</dd></dl><div class="small-title">${ico('stack','sm')} 科学规范与适用边界</div><div class="dep-flow"><span class="dep">SIS R5</span>${ico('chevronright','sm')}<span class="dep purple">Nutrition Foundation v0.1</span>${ico('chevronright','sm')}<span class="dep">AI Nutri v2.1 · 适配待签署</span></div>${s.clinical?`<div style="margin-top:8px">${tag('临床营养附加权威：SIS-MED R6 P0.4','purple')}</div><div class="banner warn" style="margin-top:9px">${ico('alert','sm')}R6 原件未恢复，当前临床条款级符合性 NOT ASSESSED。</div>`:`<div class="small subtle" style="margin-top:7px">一般营养情境不强制引入 SIS-MED；如进入临床营养，需额外满足 R6 P0.4。</div>`}<div class="detail-bottom">${button('打开 QA 阅读器','qa','primary','book')}${button('版本谱系','audit','','timeline')}${button('记录引用','openBind','','link')}</div></section>`}
function rowSource(s){const v=statuses[s.status],n=s.live?s.qa:0,safe=s.live&&s.total?Math.floor(100*n/s.total):0;let op=s.status==='QA_PENDING'?'继续核验':s.status==='RIGHTS_ACCEPTED'?'进入转换':s.status==='QA_HOLD'?'查看阻断':s.status==='RIGHTS_HOLD'?'审核要求':'查看详情';return `<tr class="${s.id===state.selected&&s.rev===state.selectedRev?'selected':''}"><td class="checkcell"><input type="checkbox" title="选择来源 ${esc(s.id)}" data-select-source="${esc(s.id)}" data-rev="${esc(s.rev)}" ${s.id===state.selected&&s.rev===state.selectedRev?'checked':''}/></td><td><button type="button" class="source-name" data-source="${esc(s.id)}" data-rev="${esc(s.rev)}" style="border:0;background:none;text-align:left;padding:0;max-width:255px">${esc(s.title)}</button><div class="source-sub">${esc(s.id)} · ${esc(s.rev)}<br/>${esc(s.kind)} · ${esc(s.year)} · ${esc(s.journal)}</div></td><td>${tag(s.rights==='SYNTHETIC_ATTESTED'?'合成核准':s.rights==='NOT_REVIEWED'?'待审查':'无准入','green'=== (s.rights==='SYNTHETIC_ATTESTED'?'green':'')?'green':(s.rights==='NOT_REVIEWED'?'amber':'dark'))}</td><td>${s.live?status(s.status):tag('DEMO · '+statuses[s.status].label,'dark')}</td><td><div class="nextrole">${ico('users')}<div><b class="small">${esc(s.owner)}</b><div class="rowhint">${esc(s.roletext)}</div></div></div></td><td><div class="qa-meter"><div class="between small"><b class="value">${s.live?n+' / '+s.total:'DEMO ONLY'}</b></div><div class="progress ${s.status==='QA_HOLD'?'danger':''}"><i style="width:${safe}%"></i></div></div></td><td class="tiny subtle">${s.live?'按详情回执核对':esc(s.project||'DEMO')}<br/>${s.live?'非资格授权':esc(s.batch||'—')}</td><td>${button(op,'sourceAction','small','','data-id="'+esc(s.id)+'" data-rev="'+esc(s.rev)+'"')}</td></tr>`}
function filters(){const all=filterSources();const counts=t=>sources.filter(x=>x.status===t&&x.sourceType==='SYNTHETIC').length;return `<div class="queue-top"><div class="between" style="align-items:flex-start"><div><div class="card-title">${ico('list')} 科学资料工作队列</div><div class="card-description">优先从待处理来源开始，按角色和状态进入下一步。</div></div><div class="queue-metrics">${[['RIGHTS_HOLD','待用途审核','amb'],['RIGHTS_ACCEPTED','待结构化','blu'],['QA_PENDING','待人工 QA','pur'],['QA_HOLD','QA 阻断','re'],['PACKAGE_FROZEN','已封存','gr']].map(([id,l,c])=>`<button class="metric ${c} ${state.stage===id?'active':''}" data-stage="${id}">${l}<span class="num value">${String(counts(id)).padStart(2,'0')}</span></button>`).join('')}</div></div><div class="toolbar"><div class="searchwrap">${ico('search')}<input class="input" id="queueSearch" aria-label="搜索资料" placeholder="搜索标题、DOI、PMID 或 Source ID" value="${esc(state.search)}"/></div><select class="select" id="queueKind" aria-label="来源类型"><option value="">全部文献类型</option>${['指南/共识','RCT','系统综述','观察性研究','资料包','其他'].map(x=>`<option ${state.kind===x?'selected':''}>${x}</option>`).join('')}</select><select class="select" id="sourceMode" aria-label="来源数据类型"><option value="ALL" ${state.sourceType==='ALL'?'selected':''}>全部 · 标记类别</option><option value="SYNTHETIC" ${state.sourceType==='SYNTHETIC'?'selected':''}>仅持久化合成</option><option value="DEMO" ${state.sourceType==='DEMO'?'selected':''}>仅虚构 DEMO</option></select></div></div><div class="table-scroll"><table class="table"><thead><tr><th style="width:22px"></th><th>来源 / 版本</th><th>资料资格</th><th>当前阶段</th><th>下一步与角色</th><th>QA 进度</th><th>引用范围</th><th>操作</th></tr></thead><tbody>${all.slice((state.queuePage-1)*state.perPage,state.queuePage*state.perPage).map(rowSource).join('')||`<tr><td colspan="8"><div class="empty-state">${ico('search','xl')}<p>没有匹配的示例来源，请清除过滤条件。</p>${button('清除筛选','clearFilters','small')}</div></td></tr>`}</tbody></table></div><div class="between" style="padding:0 15px 13px"><span class="small subtle">展示 ${Math.min(all.length,state.perPage*(state.queuePage-1)+1)}–${Math.min(all.length,state.perPage*state.queuePage)} / ${all.length} 条 · 仅合成测试记录 / 虚构 DEMO</span><div class="hstack">${button('上一页','prevRows','small','chevronleft',state.queuePage===1?'disabled':'')}${tag('第 '+state.queuePage+' / '+Math.max(1,Math.ceil(all.length/state.perPage))+' 页','outline')}${button('下一页','nextRows','small','chevronright',state.queuePage>=Math.ceil(all.length/state.perPage)?'disabled':'')}</div></div>`}
function scopebar(){return `<div class="card scopebar"><div class="scopebox">${ico('stack','lg')} <span>资料范围</span></div>${button(esc(state.project?state.project+(state.batch?' / '+state.batch:''):'全部来源 · 未筛选')+'　⌄','toggleFilter','light selection')}<span class="scope-desc">只筛选已建立的引用，不改变来源资格或专家权限。</span><div class="filteranchor" style="margin-left:auto">${button('项目 / 批次筛选'+((state.project||state.batch)?' · 已生效':''),'toggleFilter','','filter')}${state.filter?filterMarkup():''}</div>${button('清除','clearFilters','light')}</div>`}
function filterMarkup(){const activeBatches=state.project?(liveMeta.batchMap.get(state.project)||[]):[];return `<div class="filterpop" role="dialog" aria-label="项目批次筛选"><div class="between"><div class="card-title">${ico('filter')} 筛选科学来源</div><button class="btn iconbtn light" data-act="toggleFilter" aria-label="关闭筛选">${ico('close','sm')}</button></div><div class="small subtle" style="margin:9px 0 15px">使用范围仅是来源引用过滤器，绝不构成可见性授权。</div><div class="formgroup"><label class="fieldlabel" for="filterProject">项目 Project</label><select class="select" id="filterProject"><option value="">全部项目</option>${liveMeta.projects.map(x=>`<option value="${esc(x.project_id)}" ${state.project===x.project_id?'selected':''}>${esc(x.name||x.project_id)}</option>`).join('')}</select></div><div class="formgroup"><label class="fieldlabel" for="filterBatch">批次 Batch</label><select class="select" id="filterBatch"><option value="">全部批次</option>${activeBatches.map(x=>`<option value="${esc(x.batch_id)}" ${state.batch===x.batch_id?'selected':''}>${esc(x.label||x.batch_id)}</option>`).join('')}</select></div><div class="formgroup"><label class="fieldlabel">处理阶段</label><div class="chiprow">${[['','全部'],['RIGHTS_HOLD','待审核'],['RIGHTS_ACCEPTED','待结构化'],['QA_PENDING','待 QA'],['QA_HOLD','QA 阻断'],['PACKAGE_FROZEN','已封存']].map(([s,l])=>`<button class="chipbutton ${state.stage===s?'active':''}" data-stage="${s}">${l}</button>`).join('')}</div></div><div class="banner">${ico('info','sm')}所有筛选条件都只影响当前列表。完整审计链和科学规范对照始终不受 Project / Batch 缩小。</div><div class="between" style="margin-top:14px"><span class="small subtle">匹配 ${filterSources().length} 条记录</span><div class="hstack">${button('重置','clearFilters','light')}${button('应用筛选','toggleFilter','primary','check')}</div></div></div>`}
function overviewLower(){return `<div class="bottomgrid"><div class="card"><div class="card-body"><div class="card-title">${ico('gear')} 处理流程与准入边界</div><div class="steps">${['来源登记','用途审核','结构化转换','逐 Unit QA','资料包冻结'].map((l,i)=>`<div class="flowstep"><div class="circle">${i+1}</div><div><b>${l}</b><small>${['IDENTITY','RIGHTS','PARSER','HUMAN QA','FREEZE'][i]}</small></div></div>${i<4?`<span class="arrow">→</span>`:''}`).join('')}</div><div class="mini-warnings"><div><b>ⓘ 冻结 ≠ Gold</b>SourcePackage Frozen 不自动产生专家参考真值。</div><div><b>ⓘ 冻结 ≠ 专家授权</b>Expert Exposure 必须通过独立权限与任务投影。</div><div><b>ⓘ 合成 ≠ 真实来源</b>页面只演示操作，不处理真实 PDF 或私人资料。</div></div></div></div><div class="card"><div class="card-body"><div class="between"><div class="card-title">${ico('file')} 审计与规范</div>${button('查看规范矩阵','governance','small')}</div><div class="checkmini" style="margin-top:16px">${['SOURCE_REGISTERED','RIGHTS_RECORDED','CONVERSION_FROZEN','UNIT_QA_RECORDED','SOURCE_PACKAGE_FROZEN','Normative pin audit'].map(x=>`<div>${ico('circlecheck','sm')}${x}</div>`).join('')}</div><div class="banner warn" style="margin-top:17px">${ico('alert','sm')}临床营养当前权威 SIS-MED R6 P0.4；精确原件缺失，规范验收未通过。</div></div></div></div>`}
function queuePage(){return `${liveMeta.notice?`<div class="banner danger p2v2-live-banner">${ico('alert','sm')}${esc(liveMeta.notice)}</div>`:''}${scopebar()}<div class="workgrid"><div class="card queue-card">${filters()}</div><div class="p2v2-workflow-sidebar">${liveFlowPanel()}${selectedDetail()}</div></div>${overviewLower()}<div class="endcap">视觉参考：WB-P2.1-B / GOV-0.4-P0 · 本 Demo 不更改生产、科研真值、Gold 或专家授权。</div>`}
function formFields(){return `<div class="grid2"><div class="formgroup" style="grid-column:1/-1"><label class="fieldlabel">来源标题 <span class="req">*</span></label><input class="input" id="newTitle" maxlength="130" value="${esc(state.form.title)}" placeholder="示例：营养干预与健康结局 · 虚构研究"/></div><div class="formgroup"><label class="fieldlabel">来源类型</label><select id="newKind" class="select">${['指南/共识','RCT','系统综述','观察性研究','资料包','其他'].map(x=>`<option ${x===state.form.kind?'selected':''}>${x}</option>`).join('')}</select></div><div class="formgroup"><label class="fieldlabel">出版 / 更新年（模拟）</label><input class="input" type="number" id="newYear" min="2000" max="2035" value="${esc(state.form.year)}"/></div><div class="formgroup"><label class="fieldlabel">DOI / PMID（可留空）</label><input class="input" id="newIdentifier" value="${esc(state.form.identifier)}" placeholder="真实编号不会自动确权"/></div><div class="formgroup"><label class="fieldlabel">来源材料性质</label><div class="input" style="background:#f1f6f3;color:#0a7455">SYNTHETIC · 合成演示原件</div></div></div>`}
function intakeRight(){return `<div class="card"><div class="card-head"><div class="card-title">${ico('shield')} 科学来源准入条件</div><div class="card-description">不同性质的资格必须独立满足，不允许在 UI 中互相提升。</div></div><div class="card-body">${qualRow('file','原件身份','来源、出版版本、原件 SHA','待记录','amber')}${qualRow('shield','权限范围','存储 / 机器处理 / 翻译 / 阅读','独立审核','amber')}${qualRow('gear','结构化与稳定锚点','ParserRun、UnitID 与 Exact Quote','待核验','blue')}${qualRow('circlecheck','科学适用性','研究人群、风险与证据边界','未评价','dark')}${qualRow('lock','专家投影与资格','Role / Arm / Phase / Exposure Receipt','禁止访问','red')}<div class="sep"></div><div class="card-title">${ico('timeline')} 权限独立性</div><div class="banner warn" style="margin-top:12px">${ico('alert','sm')}登记 DOI/PDF 不等于获得版权，也不等于该文献适用于营养决策。此 Demo 不允许上传真实论文或患者数据。</div><div class="small-title">GOV-0.4 科学决策边界</div><div class="vstack" style="gap:6px">${tag('SIS R5 · 精确版本需重新绑定','blue')}${tag('NDSF v0.1 · 冻结主规范不改写','green')}${tag('AI Nutri v2.1 · 下游 Adapter 待补','amber')}${tag('SIS-MED R6 P0.4 · 仅临床适用','purple')}</div><div class="banner danger" style="margin-top:14px">${ico('lock','sm')}R6 的完整原件尚未恢复：条款级符合性 NOT ASSESSED，任何页面操作不得提升为 PASS。</div></div></div>`}
function intakePage(){return `<div class="intake-layout"><div><div class="card intake-card"><div class="between"><div><div class="card-title">${ico('plus')} 来源登记 · 合成资料</div><div class="card-description">演示完整登记流程与独立资格审查，不接受真实原始论文。</div></div>${tag('DRAFT ONLY','amber')}</div><div class="tabnav" aria-label="登记步骤"><button class="${state.wizard===1?'active':''}" data-wizard="1">01 来源身份</button><button class="${state.wizard===2?'active':''}" data-wizard="2">02 原始内容</button><button class="${state.wizard===3?'active':''}" data-wizard="3">03 许可与用途</button><button class="${state.wizard===4?'active':''}" data-wizard="4">04 范围确认</button></div><div style="padding-top:20px">${state.wizard===1?`${formFields()}<div class="slide-note">合成 Source ID 在提交时生成；真实 DOI 不会自动确权或建立科学资格。</div>`:state.wizard===2?`<div class="formgroup"><label class="fieldlabel" for="newRawContent">合成 Markdown 原始文本（必填）</label><textarea class="textarea width-full" id="newRawContent" rows="8" maxlength="190000" placeholder="只粘贴自行编写的虚构实验文本，不得输入真实论文全文或患者资料">${esc(state.form.raw||'')}</textarea><div class="small subtle">原文必须由 Producer 明确提供；系统不自动编造正文或来源 SHA。仅限隔离合成工程。</div></div><div class="banner">${ico('info','sm')}真实 PDF / MinerU handoff 需要独立来源系统、版权、原文校验及 Parser provenance。当前不接收真实上传。</div>`:state.wizard===3?`<div class="vstack">${qualRow('lock','保留原件','是否获准在指定存储介质保存','无真实授权','amber')}${qualRow('gear','机器处理','包括 OCR / 解析 / 翻译 / 模型处理','无真实授权','amber')}${qualRow('book','专家阅读','特定角色的逐源访问许可','NO-GO','red')}${qualRow('upload','重新发布','对外传播、论文附录 / 模型训练','NO-GO','red')}</div><div class="banner warn" style="margin-top:16px">${ico('alert','sm')}Demo 内仅使用虚构材料及合成批准状态，不代表现实中的法律许可或真实审核签名。</div>`:`<div class="grid2"><div class="formgroup"><label class="fieldlabel">计划引用项目</label><select class="select" id="newProject">${['PRJ-SYN-001','PRJ-SYN-002','PRJ-SYN-003'].map(x=>`<option ${state.form.project===x?'selected':''}>${x}</option>`).join('')}</select></div><div class="formgroup"><label class="fieldlabel">计划引用批次</label><select class="select" id="newBatch">${['BATCH-SYN-01','BATCH-SYN-02','BATCH-SYN-03'].map(x=>`<option ${state.form.batch===x?'selected':''}>${x}</option>`).join('')}</select></div></div><div class="banner warn">${ico('info','sm')}Project / Batch 仅作为拟引用意图；登记不会自动产生 ScopeBinding，更不赋予专家阅读权限。</div>`}</div><div class="formfooter"><span class="small subtle">步骤 ${state.wizard} / 4 · Producer 提交合成原文写入服务器；其他角色仅预览</span>${button('上一步','wizardPrev','light','chevronleft',state.wizard===1?'disabled':'')}${state.wizard<4?button('下一步','wizardNext','primary','chevronright'):button('提交合成来源','submitRegister','primary','check')}</div></div><div class="card" style="margin-top:14px"><div class="card-head between"><div><div class="card-title">${ico('filter')} 工作队列筛选规则</div><div class="card-description">筛选选项独立于资格审查及用户权限。</div></div>${button('返回工作队列','queue','small','list')}</div><div class="card-body grid3"><div><label class="fieldlabel">来源类型</label><select id="intakeKind" class="select width-full"><option value="">全部类型</option>${['指南/共识','RCT','系统综述','观察性研究','资料包'].map(x=>`<option ${state.kind===x?'selected':''}>${x}</option>`).join('')}</select></div><div><label class="fieldlabel">项目 Project</label><select class="select width-full" id="intakeProject"><option value="">全部项目</option>${['PRJ-SYN-001','PRJ-SYN-002','PRJ-SYN-003'].map(x=>`<option ${state.project===x?'selected':''}>${x}</option>`).join('')}</select></div><div><label class="fieldlabel">批次 Batch</label><select class="select width-full" id="intakeBatch"><option value="">全部批次</option>${['BATCH-SYN-01','BATCH-SYN-02','BATCH-SYN-03'].map(x=>`<option ${state.batch===x?'selected':''}>${x}</option>`).join('')}</select></div></div></div></div>${intakeRight()}</div>`}
function readerUnit(){return units[state.readerUnit]}
function originalParagraph(i){const u=units[i];let text=esc(u.english);const m=u.quote;const pos=u.anchor?.verified?u.anchor.start:-1;if(pos>=0){const start=u.english.slice(0,pos),end=u.english.slice(pos+m.length),color=['','pink','green',''][i]||'';text=esc(start)+`<mark class="mark ${color} ${state.readerUnit===i?'active':''}" data-unit="${i}" title="点击核对 Unit ${esc(u.id)}">${esc(m)}</mark>`+esc(end);}return `<p>${text} <sup class="small" style="color:#267bc3">[${i+1}]</sup></p>${state.readerTab==='bilingual'?`<div class="translation-block">${ico('book','sm')} <b>辅助译文 · 非权威</b><div>${esc(u.zh)}</div></div>`:''}`}
function readerToc(){return `<div class="card reader-left"><div class="side-title">${ico('list')} 来源目录 / Unit 结构</div><div class="tabnav" style="margin:0 0 12px"><button class="active">章节目录</button><button data-act="readerSearch">全文搜索</button></div><div class="toc"><button>${ico('chevronright','sm')} 1. Introduction <span class="more">✓</span></button><button>${ico('chevronright','sm')} 2. Methods <span class="more">2</span></button><button>${ico('chevron','sm')} 3. Scientific claims <span class="more">4</span></button>${units.map((u,i)=>`<button class="indented ${state.readerUnit===i?'active':''}" data-unit="${i}">${esc(u.id)} · ${esc(u.type)} <span class="more">${i+1}</span></button>`).join('')}<button>${ico('chevronright','sm')} 4. Discussion</button><button>${ico('chevronright','sm')} 5. Limitations</button><button>${ico('chevronright','sm')} References</button></div><div class="banner blue" style="margin-top:28px">${ico('info','sm')}此处展示**虚构结构化 Markdown**，不是已验证的真实 PDF / BBox。</div></div>`}
function readerCanvas(){
 const u=readerUnit();
 const mutable=selected().status==='QA_PENDING';
 const tabs=[['bilingual','逐段双语'],['original','仅原文'],['unit','结构化 Unit'],['anchor','锚点核验'],['issue','问题记录']];
 const tabmarkup=tabs.map(([id,l])=>`<button class="${state.readerTab===id?'active':''}" data-readtab="${id}">${l}</button>`).join('');
 let content='';
 if(state.readerTab==='unit'){
   content=units.map((v,i)=>`<div class="unit-card ${i===state.readerUnit?'active':''}" data-unit="${i}"><div class="between"><span class="unit-code">${v.id} · ${v.type}</span>${tag(i===state.readerUnit?'当前选中':'选择','blue')}</div><div class="bold" style="margin-top:8px">${esc(v.title)}</div><p>${esc(v.english)}</p><div class="translation-block">${esc(v.zh)}</div><div class="unit-focus">Original UnitSHA (demo) · Page hint ${v.page} · 非真实 PDF 坐标</div></div>`).join('');
 }else if(state.readerTab==='issue'){
   content=`<div style="padding:20px 0"><h2>QA 问题记录（本地预览）</h2><div class="banner warn">${ico('alert','sm')}问题不会回写到冻结原件或后端。若真实 QA REJECT，需独立新版本修复，不可覆盖原始记录。</div><div class="unit-card"><b>${esc(u.id)} · ${esc(u.title)}</b><p>待确认：目标人群、证据来源及条件范围。</p>${button('添加问题','markIssue','','message')}</div></div>`;
 }else if(state.readerTab==='anchor'){
   content=`<h2>Exact Anchor Inspector</h2><div class="banner">${ico('info','sm')}本原型的锚点与 UnitID 仅对应合成文本。未检验真实 PDF BBox。</div>` + units.map((v,i)=>`<div class="unit-card ${i===state.readerUnit?'active':''}" data-unit="${i}"><div class="hstack"><span class="unit-code">${v.id}</span>${tag('Unit exact quote','blue')}</div><p>${esc(v.quote)}</p><div class="small subtle">源文本：${v.section} · 页提示 ${v.page} · Unit 文本片段匹配</div></div>`).join('');
 }else{
   content=`<h2>3. Nutrition information and decision boundaries</h2><h3>3.1 Scientific evidence & source qualification</h3>`+units.map((v,i)=>originalParagraph(i)).join('');
 }
 return `<div class="card reader-center">
   <div class="tabnav" style="padding-left:13px;margin:0">${tabmarkup}</div>
   <div class="reader-toolbar"><div class="hstack">${button('','readerPrev','small iconbtn','chevronleft')}${tag('Unit '+(state.readerUnit+1)+' / '+units.length,'outline')}${button('','readerNext','small iconbtn','chevronright')}</div><div class="hstack"><span class="small subtle">结构化原文 · Page hint ${u.page}</span>${button('−','zoomOut','small iconbtn')}${tag(state.readerZoom+'%','outline')}${button('+','zoomIn','small iconbtn')}${button('恢复','zoomReset','small')}</div></div>
   <div class="paper-viewport"><div class="paper" style="zoom:${state.readerZoom}%"><div class="paperlabel"><span>SYNTHETIC ORIGINAL EXCERPT · NOT PUBLISHED</span><span>Page hint ${u.page} / 4</span></div>${content}<div class="paperlabel" style="margin-top:24px">演示原文 / 不用于科学结论　·　原文主权 &gt; 辅助翻译</div></div></div>
   <div class="reader-foot"><span class="small subtle">当前 Unit：<b>${esc(u.id)}</b> · ${esc(u.title)}</span><div class="actions">${button('通过本 Unit','passUnit','primary','check',mutable?'':'disabled')}${button('标记问题','markIssue','','alert',mutable?'':'disabled')}${button('保存并下一条','passNext','','chevronright',mutable?'':'disabled')}${button('返回列表','queue','','list')}</div></div>
 </div>`;
}
function qaSide(){const u=readerUnit();const dec=state.qaLocal[u.id];const reviewStatus=dec==='ACCEPT'?'合成通过':dec==='REJECT'?'合成问题':'待核验';return `<div class="card reader-right"><div class="between"><div class="card-title">${ico('file')} ${u.id} / ${units.length}</div>${tag(reviewStatus,dec==='ACCEPT'?'green':dec==='REJECT'?'red':'blue')}</div><div class="detail-title" style="margin-top:12px">${esc(u.title)}</div><div class="hstack" style="margin:9px 0 12px">${tag(u.type,'blue')}${tag('SYNTHETIC_ONLY','dark')}</div><div class="tabnav" style="margin-bottom:12px"><button class="${state.readerIssueTab==='checklist'?'active':''}" data-qatab="checklist">QA 清单</button><button class="${state.readerIssueTab==='anchor'?'active':''}" data-qatab="anchor">锚点 (1)</button><button class="${state.readerIssueTab==='issue'?'active':''}" data-qatab="issue">问题记录</button></div>${state.readerIssueTab==='checklist'?`<div class="qa-check">${['事实与原文是否一致','统计指标、数值与单位是否准确','人群范围和适用时间是否明确','是否发生证据越权 / 结论夸大','是否需要补充不确定性说明'].map((x,i)=>`<div class="qa-check-item">${ico(dec==='ACCEPT'?'circlecheck':'clock','sm')}<span class="grow">${i+1}. ${x}</span>${tag(dec==='ACCEPT'?'示例通过':'待核验',dec==='ACCEPT'?'green':'dark')}</div>`).join('')}</div>`:state.readerIssueTab==='anchor'?`<div class="anchor-item active"> <div class="anchorbadge">A1</div><div class="grow"><b class="small">Exact Quote</b><div class="small" style="margin-top:8px">${esc(u.quote)}</div><div class="tiny subtle" style="margin-top:8px">${esc(u.section)} · Page hint ${u.page}</div></div></div><div class="banner warn">${ico('alert','sm')}已核对的是此 Demo 内的文本片段；不得推断 PDF 页坐标 VERIFIED。</div>`:`<div class="vstack" style="padding:9px 0"><div class="small">${dec==='REJECT'?'当前 Unit 标记了本地 QA 问题。':'当前 Unit 尚无本地 QA 拒绝记录。'}</div>${button('记录一个模拟问题','markIssue','','message')}</div>`}<div class="small-title">${ico('link','sm')} 证据锚点回放</div><div class="anchor-item" data-readtab="anchor"><div class="anchorbadge">A1</div><div class="grow"><div class="small" style="line-height:1.6">“${esc(u.quote)}”</div><div class="tiny subtle" style="margin-top:7px">${esc(u.section)} · Unit ${u.id}</div><div style="margin-top:5px">${tag('合成文本定位','green')}</div></div>${ico('chevronright','sm')}</div><div class="small-title">${ico('message','sm')} 信息充分性与科学决策</div><div class="banner blue">${ico('info','sm')}观察值不能直接代替潜在真值；ASK、DEFER、NO_CHANGE 是合法的条件性行动。</div><div class="small-title">${ico('shield','sm')} Strict-Blind 提醒</div><div class="banner warn">${ico('lock','sm')}Source Curator 的本地 QA 演示不产生 J_preAI、Gold 或对 R0/R2 的 Agent 信息开放。</div></div>`}
// Live-source QA is owned by the independent Curator portal. These four
// hardcoded HiFi units must never be displayed against server SourceVersions.
function serverQAGate(s){
  return '<div class="card" style="padding:35px;max-width:920px">'+
    '<div class="card-title">'+ico('shield')+' 独立 Curator QA · 后端记录只读</div>'+
    '<p class="subtle">已登记合成来源：'+esc(s.id)+' / '+esc(s.rev)+
    '。V2 四个视觉演示 Unit 不属于此版本，不得用来签署、核验或冻结。</p>'+
    '<div class="banner warn">'+ico('alert','sm')+
    ' V2 尚未接入不可变 QA 提交；请独立 Curator 使用原有审核入口。</div>'+
    '<div class="hstack" style="margin-top:20px">'+
    button('打开独立审核入口','openCuratorPortal','primary','book')+
    button('返回工作队列','queue','','chevronleft')+'</div></div>';
}
function qaPage(){if(v2DeepLink&&v2DeepLink.status!=='CONFIRMED')return '<div class="banner danger" role="alert">所指定 SourceVersion 尚未获得服务器验证，不能展示演示 Unit 替代真实材料。</div>';const s=selected();if(s.live)return signedQAPage(s);if(s.id!=='SYN-GUIDE-026'||s.sourceType!=='DEMO'||!['QA_PENDING','QA_HOLD','PACKAGE_FROZEN'].includes(s.status)){return `<div class="card" style="padding:42px;max-width:920px"><div class="card-title">${ico('lock')} 当前来源无法进入 QA 阅读器</div><p class="subtle">${esc(s.id)} · ${esc(statuses[s.status].label)}。只有达到结构化 QA 阶段的合成来源才能展示该阅读界面；真实来源与专家访问仍 NO-GO。</p><div class="banner warn">${ico('alert','sm')}来源登记、用途待核或 Demo 占位不能解锁原文、QA 和专家访问；本原型不会绕过这些门禁。</div><div class="hstack" style="margin-top:20px">${button('选择合成 QA 示例','chooseQASource','primary','book')}${button('返回队列','queue','','chevronleft')}</div></div>`;}return `<div class="banner warn p2v2-live-banner">${ico('alert','sm')}DEMO ONLY · 以下四个 Unit、译文及 Anchor 仅用于视觉预览，非后端来源，也非已签署 QA。</div><div class="card reader-meta"><div class="between grow"><div class="hstack"><span class="card-title">${ico('file')} ${esc(s.title)}</span>${tag(s.id+' / '+s.rev,'outline')}${status(s.status)}</div><div class="hstack">${tag('当前 '+(state.readerUnit+1)+' / '+units.length+' Unit','outline')}${button('返回工作队列','queue','small','chevronleft')}</div></div></div><div class="readergrid">${readerToc()}${readerCanvas()}${qaSide()}</div><div class="reader-metas"><div class="card"><div class="card-title">${ico('file')} 来源版本</div><dl class="kv"><dt>Source ID</dt><dd class="mono">${esc(s.id)}</dd><dt>Revision</dt><dd>${esc(s.rev)}</dd><dt>原件 SHA</dt><dd class="mono">${esc(s.raw?s.raw.slice(0,12)+'…':'NOT_AVAILABLE')}</dd></dl></div><div class="card"><div class="card-title">${ico('search')} 位置信息</div><dl class="kv"><dt>章节</dt><dd>${esc(readerUnit().section)}</dd><dt>Page hint</dt><dd>${readerUnit().page} / 4</dd><dt>PDF BBox</dt><dd>${tag('UNRESOLVED','amber')}</dd></dl></div><div class="card"><div class="card-title">${ico('stack')} 资料使用范围</div><dl class="kv"><dt>项目</dt><dd>${esc(s.project||'—')}</dd><dt>批次</dt><dd>${esc(s.batch||'—')}</dd><dt>专家访问</dt><dd>${tag('DENIED','red')}</dd></dl></div></div>`}
function eventsHtml(){const rows=state.auditEvents.filter(e=>!state.auditFilter||e.type.includes(state.auditFilter));return `<div class="card"><div class="card-head between"><div><div class="card-title">${ico('list')} 审计事件（模拟时间线）</div><div class="card-description">浏览器内的示例事件，不是服务器签名回执。</div></div><div class="hstack"><select class="select" id="auditFilter" aria-label="审计事件类型"><option value="">全部事件</option>${['SOURCE_REGISTERED','RIGHTS_RECORDED','CONVERSION_FROZEN','UNIT_QA_RECORDED','SOURCE_PACKAGE_FROZEN','LOCAL_DEMO_QA'].map(x=>`<option ${state.auditFilter===x?'selected':''}>${x}</option>`).join('')}</select>${button('导出 JSON','exportAudit','small','download')}</div></div><div class="card-body" style="padding-top:4px;overflow:auto"><table class="audit-table"><thead><tr><th>时间</th><th>事件类型</th><th>说明</th><th>执行角色</th><th>版本</th></tr></thead><tbody>${rows.map(e=>`<tr><td class="nowrap">${esc(e.date)}</td><td class="mono">${esc(e.type)}</td><td>${esc(e.description)}</td><td>${esc(e.actor)}</td><td>${esc(e.rev)}</td></tr>`).join('')||'<tr><td colspan="5">暂无匹配事件。</td></tr>'}</tbody></table></div></div>`}
function lineage(){return `<div class="card"><div class="card-head"><div class="card-title">${ico('timeline')} 版本谱系 · Version Lineage</div><div class="card-description">原始材料、Parser 结构化、Unit QA、Package 冻结是不同类型的对象和证据。</div></div><div class="card-body"><div class="lineage">${[['原件登记','r1','Raw Artifact','2026-10-10','file'],['解析结构化','r2','Document IR','2026-10-11','stack'],['Unit QA','r3','Curator QA','2026-10-12','shield'],['资料包冻结','r3','Package · 示例','未放行','database']].map(([l,rev,sub,date,iconName],i)=>`<div class="line-node ${i===3?'active':''}"><div class="node-icon">${ico(iconName,'lg')}</div><div class="node-title">${l}</div><small>${rev} · ${date}</small><span class="codechip">${sub}</span>${i===3?`<div style="margin-top:8px">${tag('仅合成演示','amber')}</div>`:''}</div>${i<3?`<div class="line-arrow">${ico('chevronright','lg')}</div>`:''}`).join('')}</div><div class="banner warn">${ico('alert','sm')}这些阶段是示例模型，而不是声明同一份真实文献已获得版权、全部 Unit QA、正式科研资格或专家读权限。</div></div></div>`}
function referencePanel(){const s=selected();return `<div class="card"><div class="card-head"><div class="card-title">${ico('link')} 版本与引用</div><div class="card-description">不同指纹分别对应不同对象，不能混为单个版本 SHA。</div></div><div class="card-body"><dl class="kv"><dt>Raw Artifact</dt><dd class="codechip" title="${esc(s.raw||'NOT_AVAILABLE')}">${esc(s.raw?s.raw.slice(0,18)+'…'+s.raw.slice(-5):'NOT_AVAILABLE')} <button class="link" data-act="copyRaw" style="border:0;background:none" title="复制 SHA">⧉</button></dd><dt>Canonical Doc</dt><dd class="codechip" title="${esc(s.doc)}">${esc(s.doc?s.doc.slice(0,18)+'…'+s.doc.slice(-5):'NOT_CONVERTED')}</dd><dt>SourcePackage</dt><dd>${tag(s.package?'合成包 SHA 已记录':'未冻结',s.package?'green':'amber')}</dd><dt>关联 Project</dt><dd>${esc(s.project||'未关联')}</dd><dt>关联 Batch</dt><dd>${esc(s.batch||'未关联')}</dd><dt>修订关系</dt><dd>${esc(s.rev)} · 示意版本，不声明已完成勘误核验</dd></dl><div class="small-title">${ico('list','sm')} 引用记录（仅模拟）</div><table class="refs-table"><thead><tr><th>引用用途</th><th>项目 / 批次</th><th>权限状态</th></tr></thead><tbody><tr><td>Source QA 准备</td><td>${esc(s.project||'—')}</td><td>${tag('仅合成','blue')}</td></tr><tr><td>专家研究引用</td><td>—</td><td>${tag('NO_GRANT','red')}</td></tr><tr><td>Gold 参考资格</td><td>—</td><td>${tag('NO_GO','red')}</td></tr></tbody></table><div style="margin-top:13px">${button('记录项目引用（模拟）','openBind','','link')}</div></div></div>`}
function standardsPanel(){return `<div class="card"><div class="card-head between"><div><div class="card-title">${ico('shield')} 规范依赖与适用范围</div><div class="card-description">GOV-0.4-P0 · 静态语义审计，不等于精确合规认证。</div></div>${button('15 项符合性矩阵','matrix','','list')}</div><div class="card-body"><div class="dep-flow"><span class="dep">SIS v0.3.1 R5</span>${ico('chevronright','sm')}<span class="dep purple">Nutrition Foundation v0.1</span>${ico('chevronright','sm')}<span class="dep">AI Nutri v2.1</span></div><div class="banner blue">${ico('info','sm')}AI Nutri v2.1 为下游研究规范，需要版本化 Adapter；它不能替代 SIS 的上游科学权威。</div><div class="small-title">${ico('shield','sm')} 临床营养附加权威</div><div class="resultcard"><h4>SIS-MED v0.3.1 R6 P0.4</h4><p>仅在临床营养场景启用；其规范身份被确认，但完整 R6 原件尚未恢复，因此条款级符合性未评估。</p><div style="margin-top:9px">${tag('R6 SOURCE MISSING','red')}${tag('R6 CONFORMANCE NOT ASSESSED','amber')}</div></div><div class="hstack" style="margin-top:12px"><label class="small" style="color:#637d72"><input type="checkbox" id="historicalToggle" ${state.showHistorical?'checked':''}/> 显示历史版本信息</label></div>${state.showHistorical?`<div class="banner" style="margin-top:10px">${ico('book','sm')}SIS-Med R5-L1 仅可作为历史语义比较，不是当前临床营养规范，不得用于 R6 Conformance。</div>`:''}<div class="small-title">${ico('alert','sm')} 精确来源版本缺口</div><dl class="kv"><dt>SIS R5 pinned</dt><dd class="mono">181,565 B / sha256 3e1da79a…（未恢复）</dd><dt>SIS-MED R6</dt><dd class="mono">61,116 B / sha256 f8513b60…（未恢复）</dd><dt>AI Nutri 绑定</dt><dd>${tag('NDSF Adapter 待签署','amber')}</dd><dt>临床 Profile</dt><dd>${tag('LHDI mapping 待核查','amber')}</dd></dl></div></div>`}
function matrixPanel(){const rows=governance.filter(x=>!state.matrixFilter||x[3]===state.matrixFilter);return `<div class="card"><div class="card-head between"><div><div class="card-title">${ico('list')} GOV-0.4-P0 · 15 轴静态符合性矩阵</div><div class="card-description">完全按照 PR #46 的分级原则：对齐、待适配、版本阻断、未测试。</div></div><select id="matrixFilter" class="select"><option value="">全部发现</option><option value="aligned" ${state.matrixFilter==='aligned'?'selected':''}>静态对齐</option><option value="pending" ${state.matrixFilter==='pending'?'selected':''}>待适配/待测试</option><option value="blocked" ${state.matrixFilter==='blocked'?'selected':''}>精确版本阻断</option></select></div><div class="card-body" style="overflow:auto;padding-top:3px"><table class="matrix-table"><thead><tr><th>审计 ID</th><th>主题</th><th>当前证据</th><th>判定</th></tr></thead><tbody>${rows.map(([id,l,desc,k])=>`<tr><td class="mono">C${id}</td><td class="bold">${l}</td><td>${desc}</td><td>${tag(k==='aligned'?'文本语义对齐':k==='blocked'?'NOT ASSESSED / BLOCK':'待适配或测试',k==='aligned'?'green':k==='blocked'?'red':'amber')}</td></tr>`).join('')}</tbody></table></div></div>`}
function auditPage(){if(v2DeepLink&&v2DeepLink.status!=='CONFIRMED')return '<div class="banner danger" role="alert">指定的 SourceVersion 未经验证；禁止显示其他版本或假审计。</div>';if(selected()?.live)return signedAuditPage(selected());const tabs=[['lineage','版本谱系与审计'],['compare','版本差异对比'],['references','引用记录'],['governance','规范依赖与符合性']];const s=selected();return `${s.live?'<div class="banner warn p2v2-live-banner">后端来源的版本谱系与事件尚未接入此 V2 页面；以下为静态样例，不是服务器审计回执。</div>':''}<div class="card reader-meta" style="margin-bottom:12px"<div class="grow"><div class="hstack"><b class="small">选定来源</b><strong>${esc(s.title)}</strong>${tag(s.id+' / '+s.rev,'outline')}${tag('SYNTHETIC ONLY','green')}</div></div>${button('返回列表','queue','small','chevronleft')}</div><div class="card" style="margin-bottom:13px"><div class="tabnav" style="margin:0;padding:0 8px">${tabs.map(([id,l])=>`<button class="${state.versionTab===id?'active':''}" data-versiontab="${id}">${l}</button>`).join('')}</div></div>${state.versionTab==='lineage'?`<div class="versiongrid"><div>${lineage()}<div style="margin-top:14px">${eventsHtml()}</div></div><div>${referencePanel()}<div style="margin-top:14px">${standardsPanel()}</div></div></div>`:state.versionTab==='compare'?`<div class="versiongrid"><div class="card"><div class="card-head"><div class="card-title">${ico('timeline')} 版本差异 · 模拟变更</div></div><div class="card-body"><div class="grid2"><div class="standard-card"><b>r2 / Canonical IR</b><p class="small subtle">UnitIDs 已固定，Parser lineage 已登记；未声明经过全部人工 QA。</p></div><div class="standard-card"><b>r3 / QA Sidecar</b><p class="small subtle">独立 QA 与问题记录；拒绝项要求新版本，不覆盖原始 Unit。</p></div></div><div class="banner warn" style="margin-top:14px">${ico('alert','sm')}Source revision、Canonical Document revision 和 SourcePackage revision 的身份不同，必须单独溯源。</div></div></div>${referencePanel()}</div>`:state.versionTab==='references'?`<div class="versiongrid">${referencePanel()}<div>${standardsPanel()}</div></div>`:`<div class="versiongrid"><div>${matrixPanel()}</div><div>${standardsPanel()}</div></div>`}`}

/* V2.1-P1: signed synthetic lifecycle uses existing server role gates.
 * D0 /manage=producer|manager; /source-qa=independent curator|auditor. */
const flow={key:'',detail:null,doc:null,original:null,reviews:null,translations:null,audit:null,
  notice:'',busy:false,unit:0,token:0,receipts:[]};
const actorRole=()=>liveMeta.role||liveMeta.session?.role||'';
const sourceKey=x=>x?.live?x.id+':'+x.rev:'';
const sourceUrl=x=>'/v1/p2/sources/'+encodeURIComponent(x.id)+'/'+encodeURIComponent(x.rev);
function flowClear(){++flow.token;flow.key='';flow.detail=flow.doc=flow.original=flow.reviews=
  flow.translations=flow.audit=null;flow.notice='';flow.unit=0;}
async function readFlow(){
  const x=selected(),key=sourceKey(x);
  if(!key){flowClear();return;}
  if(flow.key!==key){flowClear();flow.key=key;}
  const ticket=++flow.token,url=sourceUrl(x);
  try{
    const detail=await v2Api(url);
    if(ticket!==flow.token||sourceKey(selected())!==key)return;
    flow.detail=detail;
    if(actorRole()==='curator'&&['QA_PENDING','QA_HOLD','PACKAGE_FROZEN'].includes(detail.status)){
      const [doc,original,reviews,translations]=await Promise.all([
        v2Api(url+'/document'),v2Api(url+'/original'),v2Api(url+'/reviews'),v2Api(url+'/translations')]);
      if(ticket!==flow.token||sourceKey(selected())!==key)return;
      if(doc.document_sha256!==detail.document_sha256||
        doc.document.raw_artifact_sha256!==original.raw_artifact_sha256||
        original.raw_artifact_sha256!==detail.raw_artifact_sha256)
        throw Error('SOURCE_SHA_OR_DOCUMENT_DRIFT');
      flow.doc=doc;flow.original=original;flow.reviews=reviews;flow.translations=translations;
    }else{flow.doc=flow.original=flow.reviews=flow.translations=null;}
    if(actorRole()==='auditor')flow.audit=await v2Api('/v1/p2/audit');
    if(ticket===flow.token){flow.notice='';if(app?.isConnected)render();}
  }catch(err){
    if(ticket!==flow.token)return;
    flow.notice='P2 服务端读取/版本校验失败：'+err.message;
    // A stale detail snapshot must never authorize a new action after read error.
    flow.detail=flow.audit=flow.doc=flow.original=flow.reviews=flow.translations=null;
    if(app?.isConnected)render();
  }
}
async function flowWrite(action,endpoint,body,ok){
  const x=selected();if(!x?.live||flow.busy){toast('DEMO 不可写入；或有操作正在执行。');return;}
  flow.busy=true;flow.notice='正在向 P2 后端写入…';render();
  try{
    const result=await v2Api(sourceUrl(x)+endpoint,{method:'POST',body});
    flow.receipts.unshift({key:sourceKey(x),action,event:result.event_hash||'',
      at:new Date().toISOString(),server:true});
    flow.receipts=flow.receipts.slice(0,12);
    flow.notice='';await reloadLive();await readFlow();render();
    toast(ok+(result.event_hash?' · Event '+result.event_hash.slice(0,12):''));
    return result;
  }catch(err){flow.notice=action+' 被拒绝：'+err.message;render();toast(flow.notice);}
  finally{flow.busy=false;}
}
function handoff(x){return '<p class="small subtle">在独立 Auditor / Curator 页面以对应账户登录。该操作会明确退出当前管理会话，不会绕过角色隔离。</p>'+
  button('退出当前会话并转到独立审核','v2Handoff','light','shield');}
function liveFlowPanel(){
  const x=selected();if(!x?.live)return '';
  const d=flow.key===sourceKey(x)?flow.detail:null,role=actorRole();
  let h='<section class="card p2v2-lifecycle"><div class="card-head"><div class="card-title">'+ico('gear')+
    ' 来源生命周期 · 后端操作</div><div class="card-description">'+esc(x.id)+' / '+esc(x.rev)+
    ' · 当前角色 '+esc(role)+' · 所有状态均需服务器回执</div></div><div class="card-body">';
  if(flow.notice)h+='<div class="banner danger" role="alert">'+esc(flow.notice)+'</div>';
  if(!d){h+='<p>正在读取 SourceVersion 详情；未校验前不能操作。</p>';}
  else if(x.status==='RIGHTS_HOLD'){
    h+='<div class="banner warn">独立 Auditor 审核用途。合成核准不是真实版权许可。</div>';
    if(d.rights_decision==='HOLD'){
      h+='<div class="banner danger">Auditor 已签署不可变 HOLD；当前修订不得重复批准，需新修订重新审查。</div>';
      if(role==='producer')h+=button('以新修订重新提交合成材料','v2Revise','primary','plus');
    }else if(role==='auditor')h+='<label for="v2Evidence">合成权利审查证据（SYN- 开头）</label>'+
      '<input id="v2Evidence" class="input width-full" maxlength="160" placeholder="SYN-AUDIT-001"/>'+
      '<div class="hstack" style="margin-top:10px">'+button('核准合成用途','v2Approve','primary','check')+
      button('记录独立 HOLD','v2Hold','light','lock')+'</div>';
    else h+=handoff(x);
  }else if(x.status==='RIGHTS_ACCEPTED'){
    h+='<p>合成用途已核准，允许 Producer 发起确定性 Markdown/JATS/HTML 解析。</p>';
    if(role==='producer')h+=button('执行结构化转换','v2Convert','primary','gear');
    else h+='<div class="banner">等待 Producer 转换。</div>';
  }else if(x.status==='QA_PENDING'){
    h+='<div class="banner">独立签署 '+esc(d.reviewed_units)+' / '+esc(d.unit_count)+' Unit；'+
      '未覆盖完整及存在 REJECT 时不可冻结。</div>';
    if(role==='curator')h+=button('进入服务端全文 QA','qa','primary','book');
    else if(role==='producer'){
      h+=button('检查并冻结资料包','v2Freeze','primary','lock',
        d.unit_count&&d.reviewed_units===d.unit_count?'':'disabled');
      h+=handoff(x);
    }else h+=handoff(x);
  }else if(x.status==='QA_HOLD'){
    h+='<div class="banner danger">当前修订已有不可变 QA 拒绝；必须建立新修订，不能覆写 Unit 或继续冻结。</div>';
    if(role==='producer')h+=button('基于当前来源建立返工修订','v2Revise','primary','plus');
    else if(role==='curator')h+=button('查看已签署 QA','qa','light','book');
    else h+=handoff(x);
  }else if(x.status==='PACKAGE_FROZEN'){
    h+='<div class="banner">SourcePackage 冻结：'+esc(d.package_sha256||'未找到回执')+
       ' · 不代表专家授权或 Gold。</div>';
    if(role==='producer'){
      const projects=(liveMeta.projects||[]).filter(y=>y.project_id);
      const chosen=state.bindProject||projects[0]?.project_id||'';
      const batches=liveMeta.batchMap?.get(chosen)||[];
      h+='<div class="grid2"><div><label for="v2BindProject">项目</label><select class="select" id="v2BindProject"><option value="">选择 Project</option>'+
        projects.map(p=>'<option value="'+esc(p.project_id)+'" '+(p.project_id===chosen?'selected':'')+'>'+
          esc(p.name||p.project_id)+'</option>').join('')+'</select></div>'+
        '<div><label for="v2BindBatch">批次</label><select class="select" id="v2BindBatch"><option value="">选择 Batch</option>'+
        batches.map(b=>'<option value="'+esc(b.batch_id)+'">'+esc(b.label||b.batch_id)+'</option>').join('')+
        '</select></div></div>'+button('绑定合成使用范围','v2Bind','light','link');
    }
  }
  if(d)h+='<div class="small-title">服务端身份与资格回读</div><dl class="kv">'+
    '<dt>Rights</dt><dd>'+esc(d.rights_status)+'</dd>'+
    '<dt>Raw SHA</dt><dd class="mono">'+esc(d.raw_artifact_sha256)+'</dd>'+
    '<dt>Canonical SHA</dt><dd class="mono">'+esc(d.document_sha256||'未转换')+'</dd>'+
    '<dt>ParserRun</dt><dd class="mono">'+esc(d.conversion_run_id||'未转换')+'</dd>'+
    '<dt>Package SHA</dt><dd class="mono">'+esc(d.package_sha256||'未冻结')+'</dd>'+
    '<dt>已登记使用范围</dt><dd>'+esc((d.scope_refs||[]).map(r=>r.project_id+' / '+r.batch_id).join('；')||'未绑定')+'</dd></dl>';
  return h+'</div></section>';
}
function signedQAPage(x){
  if(actorRole()!=='curator')return serverQAGate(x);
  if(flow.key!==sourceKey(x)||!flow.doc||!flow.original||!flow.reviews){
    return '<div class="card" style="padding:30px"><b>独立 Curator 正在校验服务器 Original / Document / Reviews</b>'+
      '<div class="banner warn">'+esc(flow.notice||'在完整获取版本一致性证明前禁止 QA。')+'</div>'+
      button('重新读取 Document','v2Read','primary','book')+'</div>';
  }
  const units=flow.doc.document.units||[],ix=Math.max(0,Math.min(flow.unit,units.length-1)),u=units[ix];
  if(!u)return '<div class="banner danger">Document IR 无有效 Unit。</div>';
  const reviewed=flow.reviews.reviews||[],record=reviewed.find(r=>r.unit_id===u.unit_id);
  const translation=flow.translations?.translations?.find(t=>t.unit_id===u.unit_id);
  const canReview=['QA_PENDING','QA_HOLD'].includes(x.status)&&!record;
  const toc=units.map((z,i)=>'<button class="p2v2-unit-nav '+(i===ix?'active':'')+
    '" type="button" data-v2unit="'+i+'">'+esc(z.unit_id)+' · '+esc(z.kind)+
    (reviewed.some(r=>r.unit_id===z.unit_id)?' ✓':' · 待 QA')+'</button>').join('');
  return '<div class="banner warn p2v2-live-banner">服务端 SYNTHETIC_ONLY · 独立 Curator 原文读取。'+
    '不代表真实 PDF 页坐标、临床真实性、Gold 或专家授权。</div>'+
    '<div class="card reader-meta"><b>'+esc(x.title)+'</b> · '+esc(x.id)+' / '+esc(x.rev)+
    ' · '+reviewed.length+' / '+units.length+' Unit 人工签署</div>'+
    '<div class="readergrid p2v2-server-reader">'+
    '<aside class="card reader-left"><b>Canonical Document IR</b><nav class="toc">'+toc+'</nav></aside>'+
    '<section class="card reader-center"><div class="reader-toolbar"><strong>'+esc(u.unit_id)+
    ' · '+esc(u.kind)+'</strong>'+tag(u.pdf_locator_status||'UNRESOLVED','amber')+'</div>'+
      '<div class="paper-viewport"><article class="paper"><div class="paperlabel">SYNTHETIC ORIGINAL · SHA '+
        esc(flow.original.raw_artifact_sha256.slice(0,20))+'</div>'+
        '<h3>只读原文</h3><pre class="p2v2-original">'+esc(flow.original.raw_content)+'</pre>'+
        '<h3>结构化 Unit · 原文 Anchor</h3><p>'+esc(u.text)+'</p>'+
        '<div class="translation-block"><strong>人工辅助译文（非权威）</strong><p>'+
        esc(translation?.translation_zh||'无已保存译文')+'</p></div></article></div></section>'+
    '<aside class="card reader-right"><strong>'+esc(u.unit_id)+' · 独立判断</strong>'+
      '<dl class="kv"><dt>Unit SHA</dt><dd class="mono">'+esc(u.unit_text_sha256)+'</dd>'+
      '<dt>UTF16 Span</dt><dd>[0, '+esc(u.utf16_length)+')</dd>'+
      '<dt>PDF Locator</dt><dd>'+esc(u.pdf_locator_status||'UNRESOLVED')+'</dd></dl>'+
      (record?'<div class="banner">已由 '+esc(record.reviewer)+' 签署 '+esc(record.decision)+
        '，不可重复提交或覆盖。</div>':'<div class="banner warn">尚未提交独立 QA 回执。</div>')+
      (canReview?'<label for="v2ReviewNote">判断与问题备注</label><textarea id="v2ReviewNote" class="textarea width-full" rows="3" maxlength="1200"></textarea>'+
        '<div class="hstack">'+button('ACCEPT · 不可变提交','v2Accept','primary','check')+
        button('REJECT · 返工阻断','v2Reject','light','alert')+'</div>':'')+
      (translation?'':'<label for="v2TranslateText">人工辅助译文</label>'+
        '<textarea id="v2TranslateText" class="textarea width-full" rows="3" maxlength="4000"></textarea>'+
        button('保存辅助译文 Sidecar','v2Translate','light','book'))+'</aside></div>';
}
function signedAuditPage(x){
  const d=flow.key===sourceKey(x)?flow.detail:null;
  const last=flow.receipts.filter(r=>r.key===sourceKey(x));
  const audit=actorRole()==='auditor'?flow.audit:null;
  return '<div class="banner warn p2v2-live-banner">以下 SHA/引用来自服务器；'+
    '无逐项事件查询接口，因此此处不是服务器审计回执的逐项事件明细，也不是静态 Demo 时间线。</div>'+
    '<div class="versiongrid"><section class="card"><div class="card-head"><b>SourceVersion / ParserRun / Package</b></div>'+
    '<div class="card-body"><dl class="kv"><dt>SourceVersion</dt><dd>'+esc(x.id)+' / '+esc(x.rev)+'</dd>'+
    '<dt>Raw SHA</dt><dd class="mono">'+esc(d?.raw_artifact_sha256||'未读取')+'</dd>'+
    '<dt>Doc SHA</dt><dd class="mono">'+esc(d?.document_sha256||'未转换')+'</dd>'+
    '<dt>ParserRun</dt><dd class="mono">'+esc(d?.conversion_run_id||'未转换')+'</dd>'+
    '<dt>QA</dt><dd>'+esc(d?.reviewed_units??'—')+' / '+esc(d?.unit_count??'—')+'</dd>'+
    '<dt>Package SHA</dt><dd class="mono">'+esc(d?.package_sha256||'未冻结')+'</dd></dl>'+
    '<h4>当前浏览器会话服务端写入回执</h4>'+
    (last.length?last.map(r=>'<p class="small">'+esc(r.action)+' · '+esc(r.at)+
      ' · '+esc(r.event||'无事件摘要')+'</p>').join(''):'<p>本会话无写入回执。</p>')+
    '</div></section><section class="card"><div class="card-head"><b>引用与全局审计</b></div>'+
    '<div class="card-body"><div class="small-title">实际 Project / Batch Bindings</div>'+
    ((d?.scope_refs||[]).map(r=>'<p>'+esc(r.project_id)+' / '+esc(r.batch_id)+'</p>').join('')||
      '<p>尚无服务器引用</p>')+
    '<div class="banner warn">引用不等于专家 Grant、Gold、真实版权。</div>'+
    (actorRole()==='auditor'?'<div class="resultcard"><b>Auditor 全局 Hash Chain</b><p>'+
      esc(audit?audit.valid?'VALID':'INVALID':'尚未校验')+' · events '+esc(audit?.events_checked??'—')+
      ' · '+esc(audit?.last_hash||'—')+'</p></div>'+button('重新校验全局审计链','v2Audit','primary','shield'):
      '<p>仅独立 Auditor 能查看全局审计链核验。</p>')+
    '</div></section></div>'+standardsPanel();
}

function render(){if(!app)return;document.querySelectorAll('.side-link').forEach(x=>{x.classList.toggle('active',x.dataset.page==='queue'&&['queue','intake','qa','audit'].includes(state.page)&&x.textContent.trim()==='科学资料')});const page=state.page==='queue'?queuePage():state.page==='intake'?intakePage():state.page==='qa'?qaPage():auditPage();app.innerHTML=header()+page;document.title='NutriFoundation · '+names()[0]+'｜合成资料 V2.1';}
function bindRegister(){state.modal='register';state.wizard=1;state.form={title:'',kind:'系统综述',identifier:'',year:'2026',project:'PRJ-SYN-001',batch:'BATCH-SYN-01',note:'',raw:''};openModal()}
function openModal(){if(state.modal==='register'){overlay.innerHTML=`<div class="modal-backdrop" data-dismiss="yes"><div class="modal" role="dialog" aria-modal="true" aria-label="合成来源登记"><div class="modal-head"><div><div class="modal-title">${ico('plus')} 登记新来源</div><div class="small subtle">与主页面登记流程同步 · 仅 Producer 可登记合成文本并写入服务器</div></div><button class="btn iconbtn light" data-act="closeModal" aria-label="关闭">${ico('close')}</button></div><div class="modal-content"><div class="wizardstep">${['来源身份','原始内容','用途权限','使用范围'].map((l,i)=>`<div class="wstep ${state.wizard===i+1?'active':''}"><i>${i+1}</i>${l}</div>${i<3?'<div class="rule"></div>':''}`).join('')}</div>${state.wizard===1?formFields():state.wizard===2?`<div class="formgroup"><label class="fieldlabel" for="newRawContent">合成 Markdown 原始文本（必填）</label><textarea class="textarea width-full" id="newRawContent" rows="8" maxlength="190000" placeholder="只粘贴自行编写的虚构实验文本，不得输入真实论文全文或患者资料">${esc(state.form.raw||'')}</textarea><div class="small subtle">原文必须由 Producer 明确提供；系统不自动编造正文或来源 SHA。仅限隔离合成工程。</div></div><div class="banner" style="margin-top:12px">真实 PDF 上传和 MinerU 转换保持 NO-GO；本模态框不读取磁盘文件。</div>`:state.wizard===3?`<div class="banner warn">${ico('alert')}使用授权属于独立审查。真实权利无法通过界面勾选自行批准；本流程仅能生成 SYNTHETIC RIGHTS_HOLD。</div><div class="qual-list">${qualRow('shield','存储许可','存储和版权受控','真实未核准','amber')}${qualRow('book','专家阅读','独立任务授权','DENIED','red')}</div>`:`<div class="grid2"><div class="formgroup"><label class="fieldlabel">拟引用项目</label><select id="newProject" class="select">${['PRJ-SYN-001','PRJ-SYN-002','PRJ-SYN-003'].map(x=>`<option ${state.form.project===x?'selected':''}>${x}</option>`).join('')}</select></div><div class="formgroup"><label class="fieldlabel">拟引用批次</label><select id="newBatch" class="select">${['BATCH-SYN-01','BATCH-SYN-02','BATCH-SYN-03'].map(x=>`<option ${state.form.batch===x?'selected':''}>${x}</option>`).join('')}</select></div></div><div class="banner warn">仅用于建立工作队列演示；不会签发任何 SourcePackage、Gold 或 Expert Grant。</div>`}</div><div class="modal-footer"><span class="tiny subtle">步骤 ${state.wizard} / 4</span><div class="hstack">${button('取消','closeModal','light')}${button('上一步','wizardPrevModal','light','chevronleft',state.wizard===1?'disabled':'')}${state.wizard<4?button('下一步','wizardNextModal','primary','chevronright'):button('提交合成来源','submitRegister','primary','check')}</div></div></div></div>`;return}
if(state.modal==='issue'){const u=readerUnit();overlay.innerHTML=`<div class="modal-backdrop" data-dismiss="yes"><div class="modal" style="max-width:560px" role="dialog" aria-modal="true"><div class="modal-head"><div class="modal-title">${ico('message')} 标记模拟 Unit QA 问题</div><button class="btn iconbtn light" data-act="closeModal">${ico('close')}</button></div><div class="modal-content"><div class="banner warn">${ico('alert','sm')}仅改变前端演示状态；真实拒绝决定不可原位覆盖，需冻结审查与新版本处理。</div><div style="margin:14px 0"><b>${esc(u.id)} · ${esc(u.title)}</b></div><label class="fieldlabel">问题类型</label><select class="select width-full" id="issueType"><option>原文 / Unit 不一致</option><option>数值、计量单位或人群不明确</option><option>适用性和不确定性需要补充</option><option>证据锚点不唯一</option></select><label class="fieldlabel" style="margin-top:13px">备注</label><textarea id="issueNote" class="textarea width-full" rows="3" placeholder="说明发现的问题（仅示例）"></textarea></div><div class="modal-footer">${button('取消','closeModal','light')}${button('记录模拟问题','commitIssue','primary','check')}</div></div></div>`;return}
if(state.modal==='bind'){const s=selected();overlay.innerHTML=`<div class="modal-backdrop" data-dismiss="yes"><div class="modal" style="max-width:560px" role="dialog" aria-modal="true"><div class="modal-head"><div class="modal-title">${ico('link')} 建立来源引用 · 预览</div><button class="btn iconbtn light" data-act="closeModal">${ico('close')}</button></div><div class="modal-content"><div class="bold">${esc(s.title)}</div><p class="small subtle">${esc(s.id)} / ${esc(s.rev)}</p><div class="grid2"><div class="formgroup"><label class="fieldlabel">Project</label><select class="select" id="bindProject">${['PRJ-SYN-001','PRJ-SYN-002','PRJ-SYN-003'].map(x=>`<option ${s.project===x?'selected':''}>${x}</option>`).join('')}</select></div><div class="formgroup"><label class="fieldlabel">Batch</label><select class="select" id="bindBatch">${['BATCH-SYN-01','BATCH-SYN-02','BATCH-SYN-03'].map(x=>`<option ${s.batch===x?'selected':''}>${x}</option>`).join('')}</select></div></div><div class="banner warn">${ico('lock','sm')}模拟引用只修改本页状态；不可由此获得 Expert read model、真实版权或 Gold。</div></div><div class="modal-footer">${button('取消','closeModal','light')}${button('保存本地演示引用','commitBind','primary','check')}</div></div></div>`}
}
function captureForm(){const mapping={newTitle:'title',newKind:'kind',newIdentifier:'identifier',newYear:'year',newProject:'project',newBatch:'batch',newRawContent:'raw'};for(const [id,key] of Object.entries(mapping)){let e=document.getElementById(id);if(e)state.form[key]=e.value}}
function action(name,el){const id=el.dataset.id;if(['queue','intake','qa','audit'].includes(name))return pg(name);
switch(name){case 'noop':return;case 'openCuratorPortal':window.open('/source-qa','_blank','noopener');return;case 'notify':return toast('本页面是离线高保真原型，无真实通知服务。');case 'dismissToast':document.getElementById('p2v2ToastHolder').replaceChildren();return;case 'toggleFilter':state.filter=!state.filter;render();return;case 'clearFilters':state.search='';state.kind='';state.stage='';state.project='';state.batch='';state.sourceType='ALL';state.queuePage=1;state.filter=false;render();return;case 'prevRows':state.queuePage=Math.max(1,state.queuePage-1);render();return;case 'nextRows':state.queuePage=Math.min(Math.ceil(filterSources().length/state.perPage),state.queuePage+1);render();return;
case 'openRegister':bindRegister();return;case 'wizardPrev':captureForm();state.wizard=Math.max(1,state.wizard-1);render();return;case 'wizardNext':captureForm();state.wizard=Math.min(4,state.wizard+1);render();return;case 'wizardPrevModal':captureForm();state.wizard=Math.max(1,state.wizard-1);openModal();return;case 'wizardNextModal':captureForm();state.wizard=Math.min(4,state.wizard+1);openModal();return;
case 'submitRegister':captureForm();if(state.form.title.trim().length<4){toast('请先填写至少 4 字的合成来源标题。');if(state.modal==='register'){state.wizard=1;openModal()}else{state.wizard=1;render()}return}let num=String(100+sources.length).padStart(3,'0');const newid='SYN-NEW-'+num;const src={id:newid,rev:'r1',title:state.form.title.trim(),year:state.form.year||'2026',journal:'新增合成登记',kind:state.form.kind||'其他',status:'RIGHTS_HOLD',rights:'NOT_REVIEWED',qa:0,total:0,project:state.form.project,batch:state.form.batch,owner:'Auditor',roletext:'独立审核用途',raw:'NOT_COMPUTED_LOCAL_DEMO',doc:'',package:'',clinical:false,sourceType:'SYNTHETIC'};sources.unshift(src);state.selected=newid;state.queuePage=1;state.search='';state.kind='';state.stage='';state.project='';state.batch='';state.sourceType='ALL';state.modal='';overlay.replaceChildren();state.auditEvents.unshift({date:new Date().toLocaleString('zh-CN',{hour12:false}),type:'SOURCE_REGISTERED',actor:'Local Demo',rev:'r1',description:'已创建 SYNTHETIC RIGHTS_HOLD 的本地演示登记'});pg('queue');toast('合成来源登记已添加到工作队列，状态 RIGHTS_HOLD；无后端写入。');return;
case 'closeModal':state.modal='';overlay.replaceChildren();return;case 'sourceAction':state.selected=id||state.selected;state.selectedRev=el.dataset.rev||state.selectedRev;const s=selected();if(s.live){v2DeepLink=null;state.page=actorRole()==='curator'&&['QA_PENDING','QA_HOLD'].includes(s.status)?'qa':'queue';render();readFlow();return;}if(s.status==='QA_PENDING'){state.readerUnit=0;return pg('qa')}render();toast('DEMO 仅供视觉示例 · '+s.id);return;case 'openBind':state.modal='bind';openModal();return;case 'commitBind':{let a=document.getElementById('bindProject'),b=document.getElementById('bindBatch');if(a&&b){selected().project=a.value;selected().batch=b.value}state.modal='';overlay.replaceChildren();render();toast('已保存浏览器内的合成 Project/Batch 使用范围；不代表专家授权。');return}
case 'chooseQASource':state.selected='SYN-GUIDE-026';state.selectedRev='r3';state.readerUnit=0;render();toast('已切换到合成 QA 来源样例。');return;case 'readerPrev':state.readerUnit=(state.readerUnit+units.length-1)%units.length;render();return;case 'readerNext':state.readerUnit=(state.readerUnit+1)%units.length;render();return;case 'readerSearch':toast('全文检索在正式版本使用 Canonical Unit 索引；本 Demo 请直接选择左侧 Unit。');return;case 'zoomIn':state.readerZoom=Math.min(135,state.readerZoom+10);render();return;case 'zoomOut':state.readerZoom=Math.max(75,state.readerZoom-10);render();return;case 'zoomReset':state.readerZoom=100;render();return;
case 'passUnit':case 'passNext':{if(selected().status!=='QA_PENDING'){toast('该来源不是待 QA 阶段，冻结或阻断版本不可通过此按钮修改。');return}const u=readerUnit();if(state.qaLocal[u.id]==='REJECT'){toast('该 Unit 已在本地标记问题。真实系统需走拒绝处理和新版本，不允许直接覆盖。');return}state.qaLocal[u.id]='ACCEPT';state.auditEvents.unshift({date:new Date().toLocaleString('zh-CN',{hour12:false}),type:'LOCAL_DEMO_QA',actor:'Demo Curator',rev:selected().rev,description:u.id+'：模拟 QA ACCEPT（未签署回执）'});if(name==='passNext')state.readerUnit=(state.readerUnit+1)%units.length;render();toast('已记入本地 QA 预览；非 Curator 真实签署，不影响科学资格。');return}
case 'markIssue':if(selected().status!=='QA_PENDING'){toast('该来源目前不可写入 QA；此界面遵循不可变冻结边界。');return}state.modal='issue';openModal();return;case 'commitIssue':{if(selected().status!=='QA_PENDING'){toast('当前来源不允许新增 QA 记录。');return}const u=readerUnit();state.qaLocal[u.id]='REJECT';state.auditEvents.unshift({date:new Date().toLocaleString('zh-CN',{hour12:false}),type:'LOCAL_DEMO_QA',actor:'Demo Curator',rev:selected().rev,description:u.id+'：模拟 QA 问题；要求独立修订'});state.modal='';overlay.replaceChildren();render();toast('已记录本地模拟问题；当前版本不会被覆盖。');return}
case 'governance':state.versionTab='governance';return pg('audit');case 'matrix':state.versionTab='governance';render();return;case 'copyRaw':navigator.clipboard?.writeText(selected().raw).then(()=>toast('已复制当前合成来源 SHA 示例。')).catch(()=>toast('当前离线环境不允许访问剪贴板。'));return;
case 'exportAudit':{const payload={note:'LOCAL DEMO ONLY / NOT REAL SCIENCE / NOT SIGNED',source_id:selected().id,exported_at:new Date().toISOString(),events:state.auditEvents,standards:{clinical_authority:'SIS-MED v0.3.1 R6 P0.4',r6_conformance:'NOT_ASSESSED_EXACT_SOURCE_MISSING',real_expert:'NO_GO',Gold:'NO_GO'}};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='NutriFoundation_GOV04_Synthetic_Audit_Demo.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);toast('已导出本地模拟审计 JSON，不是系统签署回执。');return}
default:toast('当前操作仅展示界面状态；无真实后端服务。')}
}
document.addEventListener('click',e=>{if(!app?.isConnected)return;const page=e.target.closest('[data-page]');if(page){e.preventDefault();pg(page.dataset.page);return}const source=e.target.closest('[data-source]');if(source){v2DeepLink=null;state.selected=source.dataset.source;state.selectedRev=source.dataset.rev||'';render();readFlow();return}const scope=e.target.closest('[data-stage]');if(scope){state.stage=scope.dataset.stage;state.queuePage=1;render();return}const actual=e.target.closest('[data-v2unit]');if(actual){flow.unit=+actual.dataset.v2unit;render();return}const u=e.target.closest('[data-unit]');if(u){state.readerUnit=+u.dataset.unit;render();return}const rt=e.target.closest('[data-readtab]');if(rt){state.readerTab=rt.dataset.readtab;render();return}const qt=e.target.closest('[data-qatab]');if(qt){state.readerIssueTab=qt.dataset.qatab;render();return}const vt=e.target.closest('[data-versiontab]');if(vt){state.versionTab=vt.dataset.versiontab;render();return}const w=e.target.closest('[data-wizard]');if(w){captureForm();state.wizard=+w.dataset.wizard;render();return}const act=e.target.closest('[data-act]');if(act){e.preventDefault();action(act.dataset.act,act);return}const dismiss=e.target.closest('[data-dismiss]');if(dismiss&&e.target===dismiss){state.modal='';overlay.replaceChildren();return}const sel=e.target.closest('[data-select-source]');if(sel){v2DeepLink=null;state.selected=sel.dataset.selectSource;state.selectedRev=sel.dataset.rev||'';render();readFlow();return}});
document.addEventListener('change',e=>{if(!app?.isConnected)return;const x=e.target;switch(x.id){case 'queueKind':case 'intakeKind':state.kind=x.value;state.queuePage=1;render();break;case 'sourceMode':state.sourceType=x.value;state.queuePage=1;render();break;case 'v2BindProject':state.bindProject=x.value;render();break;case 'filterProject':case 'intakeProject':state.project=x.value;state.batch='';state.queuePage=1;render();reloadLive();break;case 'filterBatch':case 'intakeBatch':state.batch=x.value;state.queuePage=1;render();reloadLive();break;case 'auditFilter':state.auditFilter=x.value;render();break;case 'matrixFilter':state.matrixFilter=x.value;render();break;case 'historicalToggle':state.showHistorical=x.checked;render();break;default:if(/^new(Title|Kind|Year|Project|Batch|Identifier)$/.test(x.id))captureForm();break}});
document.addEventListener('input',e=>{if(!app?.isConnected)return;const t=e.target;if(t.id==='queueSearch'){state.search=t.value;state.queuePage=1;const pos=t.selectionStart;render();const next=document.getElementById('queueSearch');if(next){next.focus();next.setSelectionRange(pos,pos)}}});document.addEventListener('keydown',e=>{if(!app?.isConnected)return;if(e.key==='Escape'){if(state.modal){state.modal='';overlay.replaceChildren()}else if(state.filter){state.filter=false;render()}}});/* notifyBtn omitted in V2 *//* mobileNav omitted in V2 */
window.__p2v2={state,sources,units,governance,go:pg,openRegister:bindRegister};


const _actionBare=action;
action=async function(act,node){
  const x=selected(),role=actorRole();
  if(act==='openRegister'&&role!=='producer'){
    toast('只有 Producer 可登记合成来源。');return;
  }
  if(act==='v2Handoff'){
    if(!x?.live)return toast('仅已登记合成来源可交接独立审核。');
    const uri='/source-qa#/studio-v2?source='+encodeURIComponent(x.id)+
      '&revision='+encodeURIComponent(x.rev);
    if(['curator','auditor'].includes(role)){location.assign(uri);return;}
    if(!window.confirm('该动作会退出当前管理会话，再由独立 Auditor/Curator 登录。确认继续？'))return;
    try{await v2Api('/v1/logout',{method:'POST',body:{}});flowClear();location.assign(uri);}
    catch(err){toast('退出管理会话失败；没有打开独立原文：'+err.message);}
    return;
  }
  if(act==='openCuratorPortal'){
    // Use the exact same explicit sign-out gate as the lifecycle handoff.
    return action('v2Handoff',node);
  }
  if(act==='v2Read'){await readFlow();return;}
  if(act==='v2Approve'||act==='v2Hold'){
    if(!x?.live||role!=='auditor'||x.status!=='RIGHTS_HOLD')return toast('需要独立 Auditor 会话和 RIGHTS_HOLD 状态。');
    const evidence=document.getElementById('v2Evidence')?.value.trim();
    if(!evidence||!/^SYN-[A-Za-z0-9._-]{1,155}$/.test(evidence))
      return toast('必须填写 SYN- 开头的独立审核证据编号。');
    await flowWrite('RIGHTS_RECORDED','/rights',{
      decision:act==='v2Approve'?'APPROVE_SYNTHETIC':'HOLD',
      evidence_ref:evidence,
      uses:['INTERNAL_SOURCE_REVIEW','MACHINE_PROCESSING','RETAIN_ORIGINAL']
    },act==='v2Approve'?'独立 Auditor 已核准合成用途':'独立 Auditor 已记录不可变 HOLD');
    return;
  }
  if(act==='v2Convert'){
    if(!x?.live||role!=='producer'||x.status!=='RIGHTS_ACCEPTED')
      return toast('只有 Producer 能转换已获独立合成核准的来源。');
    await flowWrite('CONVERSION_FROZEN','/convert',{external_payload:null},'结构化 Document IR 与 ParserRun 已保存');
    return;
  }
  if(act==='v2Accept'||act==='v2Reject'){
    if(!x?.live||role!=='curator'||!flow.doc||!flow.original||!flow.reviews||
      !['QA_PENDING','QA_HOLD'].includes(x.status))return toast('需要独立 Curator 和受控原件/IR 的精确匹配。');
    const u=flow.doc.document.units[flow.unit];
    if(!u||flow.reviews.reviews.some(r=>r.unit_id===u.unit_id))
      return toast('该 Unit 已有不可变判断，禁止重写。');
    if(u.utf16_length!==u.text.length)return toast('UTF-16 长度与 Document IR 不一致。');
    const bytes=new TextEncoder().encode(u.text);
    const digest=await crypto.subtle.digest('SHA-256',bytes);
    const sum=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');
    if(sum!==u.unit_text_sha256)return toast('Unit SHA 漂移，禁止提交。');
    const notes=document.getElementById('v2ReviewNote')?.value.trim()||'';
    if(act==='v2Reject'&&!notes)return toast('REJECT 必须说明问题与返工理由。');
    const record=await flowWrite('UNIT_QA_RECORDED','/qa',{
      unit_id:u.unit_id,decision:act==='v2Accept'?'ACCEPT':'REJECT',
      start_utf16:0,end_utf16:u.utf16_length,source_quote:u.text,
      source_quote_sha256:sum,pdf_locator_status:u.pdf_locator_status,
      findings:{ui:'P2_V2_SIGNED_SYNTHETIC_QA',notes:notes.slice(0,1200)}
    },'Curator 不可变 Unit QA 已由服务器确认');
    if(record?.review)flow.unit=Math.min(flow.unit+1,(flow.doc?.document.units||[]).length-1);
    render();return;
  }
  if(act==='v2Translate'){
    if(!x?.live||role!=='curator'||!flow.doc)return toast('辅助译文仅能由独立 Curator 基于 Document IR 保存。');
    const u=flow.doc.document.units[flow.unit],value=document.getElementById('v2TranslateText')?.value.trim();
    if(!u||!value||value.length<2)return toast('先输入明确的人工辅助译文。');
    await flowWrite('AUXILIARY_TRANSLATION_FROZEN','/translations',{
      unit_id:u.unit_id,translation_zh:value,expected_unit_text_sha256:u.unit_text_sha256,
      provenance_ref:'SYN-HUMAN-P2V2-'+crypto.randomUUID().replaceAll('-','').slice(0,12).toUpperCase()
    },'人工辅助译文独立保存（原文保持权威）');
    return;
  }
  if(act==='v2Freeze'){
    const d=flow.detail;
    if(!x?.live||role!=='producer'||x.status!=='QA_PENDING'||!d?.document_sha256||
      !d.unit_count||d.unit_count!==d.reviewed_units)
      return toast('冻结前需要 Producer 身份、全部独立 Unit QA 与精确 Document SHA。');
    await flowWrite('SOURCE_PACKAGE_FROZEN','/freeze',{
      expected_document_sha256:d.document_sha256
    },'资料包已由服务端不可变冻结（非 Gold / 专家授权）');
    return;
  }
  if(act==='v2Bind'){
    const project=document.getElementById('v2BindProject')?.value||'';
    const batch=document.getElementById('v2BindBatch')?.value||'';
    if(!x?.live||role!=='producer'||x.status!=='PACKAGE_FROZEN'||!project||!batch)
      return toast('Producer 仅能给已冻结来源绑定已存在的 Project/Batch。');
    await flowWrite('SOURCE_SCOPE_BOUND','/scope',{
      project_id:project,batch_id:batch
    },'合成来源用途范围已持久化（不会签发 Expert Grant）');
    return;
  }
  if(act==='v2Audit'){
    if(role!=='auditor')return toast('全局 Hash Chain 审计仅独立 Auditor 可查看。');
    try{flow.audit=await v2Api('/v1/p2/audit');render();
      toast(flow.audit.valid?'服务端审计链 VALID':'服务端审计链 INVALID，禁止放行');}
    catch(err){flow.notice='全局 Audit 失败：'+err.message;render();}
    return;
  }
  if(act==='v2Revise'){
    if(!x?.live||role!=='producer'||!(
      x.status==='QA_HOLD'||(x.status==='RIGHTS_HOLD'&&flow.detail?.rights_decision==='HOLD')))
      return toast('只有 QA REJECT 或独立权利 HOLD 的不可变来源可建立新修订。');
    const revisions=sources.filter(s=>s.live&&s.id===x.id).map(s=>/^r[0-9]+$/.test(s.rev)?Number(s.rev.slice(1)):0);
    const newRev='r'+(Math.max(0,...revisions)+1);
    state.modal='register';state.wizard=1;
    state.form={title:x.title,kind:x.kind,identifier:x.identifier||'',year:'',project:'',batch:'',
      note:'',raw:'',parent:{id:x.id,rev:x.rev},newRevision:newRev};
    openModal();return;
  }
  if(act==='openBind'&&x?.live){
    toast('持久化合成引用请使用已冻结来源的服务端 Binding 表单。');return;
  }
  // Never use preview-only local state to impersonate a server QA or audit receipt.
  if(selected()?.live&&['passUnit','passNext','markIssue','commitIssue','commitBind','exportAudit'].includes(act)){
    toast('已登记来源不可通过本地演示按钮核验、引用或导出审计；请进入独立授权工作流。');
    return;
  }
  if(act==='clearFilters'){
    _actionBare(act,node);await reloadLive();return;
  }
  if(act==='submitRegister'){
    captureForm();
    if(state.form.title.trim().length<4){toast('请先填写至少 4 字的合成来源标题。');if(state.modal==='register'){state.wizard=1;openModal()}else{state.wizard=1;render()}return}
    const role=liveMeta.role||liveMeta.session?.role||'';
    if(role!=='producer'){
      toast('当前账户不能登记来源；仅 Producer 能提交合成原文。演示模式不写入服务器。');
      return;
    }
    if(!state.form.raw||!state.form.raw.trim()||state.form.raw.trim().length<20){
      state.wizard=2;
      if(state.modal==='register')openModal();else render();
      toast('请输入至少 20 字的虚构 Markdown 原文；禁止提交真实论文或患者信息。');
      return;
    }
    if(new TextEncoder().encode(state.form.raw).length>190000){
      toast('合成原文超过 V2 限额 190KB。');return;
    }
    if(role==='producer'){
      const capturedAt=new Date().toISOString();
      const parent=state.form.parent||null;
      const sid=parent?.id||('P2-SYN-'+crypto.randomUUID().replaceAll('-','').slice(0,10).toUpperCase());
      const revision=parent?state.form.newRevision:'r1';
      const body={source_id:sid,revision_id:revision,title:state.form.title.trim(),
        source_type:TYPE_TO_API[state.form.kind]||'SYSTEMATIC_REVIEW_META',
        identifier_kind:'SYNTHETIC_ID',identifier:state.form.identifier||('SYN-'+sid.slice(-8)),
        available_at:capturedAt,fetched_at:capturedAt,
        raw_format:'MARKDOWN',
        raw_content:state.form.raw,
        rights_assertion:'SYNTHETIC_FIXTURE',source_family_refs:parent?[parent.id+':'+parent.rev]:[]};
      try{
        await v2Api('/v1/p2/sources',{method:'POST',body});
        state.modal='';if(overlay)overlay.replaceChildren();state.wizard=1;
        // Never retain authored source text after the server has the exact bytes.
        state.form.raw='';state.form.parent=null;state.form.newRevision=null;
        state.selected=sid;state.selectedRev=revision;state.page='queue';state.queuePage=1;
        // A new unbound source cannot appear inside a Project/Batch usage filter.
        state.project='';state.batch='';state.sourceType='SYNTHETIC';state.stage='';state.kind='';state.search='';
        toast('服务端登记 '+sid+' / '+revision+' · RIGHTS_HOLD，需独立审核（旧版本保持不可变）');
        await reloadLive();return;
      }catch(err){toast('登记被拒绝：'+err.message);return;}
    }
  }
  return _actionBare(act,node);
};


  const SVG_ICONS=`<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true"><defs>
<symbol id="ic-home" viewBox="0 0 24 24"><path d="m3 10 9-8 9 8v11H3z"/><path d="M9 21v-8h6v8"/></symbol>
<symbol id="ic-database" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v7c0 2 4 4 9 4s9-2 9-4V5M3 12v7c0 2 4 3 9 3s9-1 9-3v-7"/></symbol>
<symbol id="ic-list" viewBox="0 0 24 24"><path d="M9 5h12M9 12h12M9 19h12"/><path d="M3 5h2M3 12h2M3 19h2"/></symbol>
<symbol id="ic-file" viewBox="0 0 24 24"><path d="M5 2h10l5 5v15H5zM15 2v6h5M8 12h9M8 16h9"/></symbol>
<symbol id="ic-check" viewBox="0 0 24 24"><path d="m4 12 5 5L20 6"/></symbol>
<symbol id="ic-circlecheck" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m7 12 4 4 6-7"/></symbol>
<symbol id="ic-shield" viewBox="0 0 24 24"><path d="M12 2 21 6v7c0 6-4.5 8.2-9 10-4.5-1.8-9-4-9-10V6zM8 12l3 3 5-6"/></symbol>
<symbol id="ic-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 5 5"/></symbol>
<symbol id="ic-filter" viewBox="0 0 24 24"><path d="M3 5h18l-7 8v6l-4 2v-8z"/></symbol>
<symbol id="ic-chevron" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>
<symbol id="ic-chevronleft" viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></symbol>
<symbol id="ic-chevronright" viewBox="0 0 24 24"><path d="m9 5 7 7-7 7"/></symbol>
<symbol id="ic-plus" viewBox="0 0 24 24"><path d="M12 4v16M4 12h16"/></symbol>
<symbol id="ic-close" viewBox="0 0 24 24"><path d="m5 5 14 14M19 5 5 19"/></symbol>
<symbol id="ic-alert" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v7M12 17v1"/></symbol>
<symbol id="ic-copy" viewBox="0 0 24 24"><rect x="8" y="8" width="13" height="13" rx="1"/><path d="M16 8V3H3v13h5"/></symbol>
<symbol id="ic-link" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7 .5l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7-.5l-3 3a5 5 0 0 0 7 7l2-2"/></symbol>
<symbol id="ic-stack" viewBox="0 0 24 24"><path d="m12 2 10 5-10 5L2 7zM2 12l10 5 10-5M2 17l10 5 10-5"/></symbol>
<symbol id="ic-timeline" viewBox="0 0 24 24"><circle cx="5" cy="5" r="2"/><circle cx="19" cy="7" r="2"/><circle cx="10" cy="19" r="2"/><path d="M7 6l10 1M5 7l4 10M18 9l-7 8"/></symbol>
<symbol id="ic-spark" viewBox="0 0 24 24"><path d="m12 2 2 7 7 3-7 2-2 8-3-8-7-2 7-3z"/></symbol>
<symbol id="ic-users" viewBox="0 0 24 24"><circle cx="8" cy="8" r="4"/><path d="M1 22v-3c0-4 3-6 7-6s7 2 7 6v3z"/><path d="M16 4c3 0 5 2 5 5s-2 4-4 4M17 15c4 0 6 2 6 5v2"/></symbol>
<symbol id="ic-bars" viewBox="0 0 24 24"><path d="M3 20V9h4v11M10 20V4h4v16M17 20v-8h4v8M1 22h22"/></symbol>
<symbol id="ic-download" viewBox="0 0 24 24"><path d="M12 2v14m-5-5 5 5 5-5M3 19v3h18v-3"/></symbol>
<symbol id="ic-book" viewBox="0 0 24 24"><path d="M12 5C8 2 4 3 2 4v16c3-1 7-1 10 2 3-3 7-3 10-2V4c-2-1-6-2-10 1v17M12 5v17"/></symbol>
<symbol id="ic-eye" viewBox="0 0 24 24"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></symbol>
<symbol id="ic-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 5v7l5 3"/></symbol>
<symbol id="ic-lock" viewBox="0 0 24 24"><rect x="4" y="10" width="16" height="12" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4"/></symbol>
<symbol id="ic-upload" viewBox="0 0 24 24"><path d="M12 19V3m-5 5 5-5 5 5M4 17v5h16v-5"/></symbol>
<symbol id="ic-message" viewBox="0 0 24 24"><path d="M3 3h18v14H7l-4 4zM7 8h10M7 12h7"/></symbol>
<symbol id="ic-info" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 11v6M12 7v1"/></symbol>
<symbol id="ic-gear" viewBox="0 0 24 24"><path d="M10 2h4l1 3 3 1 3-1 2 4-3 2v3l3 2-2 4-3-1-3 1-1 3h-4l-1-3-3-1-3 1-2-4 3-2v-3L1 9l2-4 3 1 3-1z"/><circle cx="12" cy="12" r="3"/></symbol>
<symbol id="ic-zoom" viewBox="0 0 24 24"><path d="M12 6v12M6 12h12"/></symbol>
</defs></svg>`;

  function ensureChrome(host){
    host.classList.add('p2v2');
    if(!host.querySelector('.p2v2-icons')){
      const wrap=document.createElement('div');
      wrap.className='p2v2-icons';
      wrap.hidden=true;
      wrap.innerHTML=SVG_ICONS;
      host.prepend(wrap);
    }
    let root=host.querySelector('#p2v2App');
    if(!root){
      root=document.createElement('div');
      root.id='p2v2App';
      root.className='content p2v2-app';
      host.append(root);
    }
    let ov=host.querySelector('#p2v2Overlay');
    if(!ov){
      ov=document.createElement('div');
      ov.id='p2v2Overlay';
      host.append(ov);
    }
    if(!host.querySelector('#p2v2ToastHolder')){
      const th=document.createElement('div');
      th.id='p2v2ToastHolder';
      th.setAttribute('role','status');
      th.setAttribute('aria-live','polite');
      host.append(th);
    }
    app=root;overlay=ov;
    return root;
  }

  function renderMount(options={}){
    liveMeta.role=options.role||liveMeta.role||'manager';
    liveMeta.session=options.session||(typeof auth!=='undefined'?auth:null);
    liveMeta.projects=options.projects||liveMeta.projects||[];
    liveMeta.batchMap=options.batchMap||liveMeta.batchMap||new Map();
    liveMeta.scope={project:options.scope?.project||'',batch:options.scope?.batch||''};
    state.project=liveMeta.scope.project;state.batch=liveMeta.scope.batch;
    v2DeepLink=(options.sourceId&&options.revisionId)?{id:options.sourceId,rev:options.revisionId,status:'PENDING'}:null;
    if(v2DeepLink){state.selected=v2DeepLink.id;state.selectedRev=v2DeepLink.rev;}
    if(options.startPage&&['queue','intake','qa','audit'].includes(options.startPage))state.page=options.startPage;
    const host=document.createElement('section');
    host.className='p2v2';
    host.setAttribute('aria-label','科学资料管理 V2');
    ensureChrome(host);
    queueMicrotask(()=>{
      if(!host.isConnected)return;
      ensureChrome(host);
      render();
      reloadLive();
    });
    return host;
  }

  function reset(){
    // No stale source text, original/IR or signed receipt in hidden DOM after
    // independent Curator logout or account switching.
    ++sourcesEpoch;flowClear();flow.busy=false;flow.receipts=[];v2DeepLink=null;
    app?.replaceChildren();overlay?.replaceChildren();
    liveMeta.role='manager';liveMeta.session=null;liveMeta.notice='';
    state.form={title:'',kind:'系统综述',identifier:'',year:'',project:'',batch:'',note:'',raw:''};state.qaLocal={};
    state.page='queue';state.selected=DEMO_SEED[0]?.id||'';state.selectedRev=DEMO_SEED[0]?.rev||'';state.search='';state.stage='';
    state.project='';state.batch='';state.filter=false;state.wizard=1;state.modal='';
    state.versionTab='lineage';sources.splice(0,sources.length,...DEMO_SEED.map(x=>({...x})));
  }

  return {render:renderMount,reload:reloadLive,reset,selectTab:(tab)=>{state.page=tab;if(app)render();}};
})();
