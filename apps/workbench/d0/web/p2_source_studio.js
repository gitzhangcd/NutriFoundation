/* WB-P2 Source Studio / PR #36 aligned.
 * HTML v0.2 visual hierarchy + real SYNTHETIC source-stage API operations.
 * Deliberately NOT real-source/LLM/Gold/expert publication access.
 * Render all user/API text with textContent, never HTML interpolation.
 */
'use strict';
(() => {
  const el=(tag,text,klass)=>{const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=String(text);if(klass)n.className=klass;return n;};
  const append=(node,...items)=>{for(const item of items.flat())if(item)node.append(item);return node;};
  const button=(text,fn,klass='')=>{const n=el('button',text,'p2-btn '+klass);n.type='button';if(fn)n.addEventListener('click',fn);return n;};
  const chip=(text,kind='muted')=>el('span',text,'p2-flag '+kind);
  const alert=(text,kind='warning')=>el('div',text,'p2-banner '+kind);
  const field=(text,control)=>append(el('label',null,'p2-field'),el('span',text),control);
  const textInput=(value='',max=200)=>{const n=el('input');n.value=value;n.maxLength=max;return n;};
  const select=(rows,value,changed)=>{const n=el('select');rows.forEach(([id,label])=>{const o=el('option',label);o.value=id;n.append(o)});n.value=value||'';if(changed)n.addEventListener('change',()=>changed(n.value));return n;};
  const fixtures=[
    {id:'P2-DEMO-RCT-001',v:'r1',title:'Synthetic nutrition intervention trial · evidence extraction illustration',type:'RANDOMIZED_TRIAL',kind:'JATS_XML',stage:'QA_HOLD',rights:'DEMO_NOT_QUALIFIED',project:'',batch:'',units:3,raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO',risk:'Table values await human review'},
    {id:'P2-DEMO-GUIDE-002',v:'r3',title:'Illustrative adult nutrition guideline · structure specimen',type:'GUIDELINE',kind:'HTML',stage:'PACKAGE_DESIGN_PREVIEW',rights:'DEMO_NOT_QUALIFIED',project:'',batch:'',units:6,raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO',risk:'Illustrative package, not a qualified source'},
    {id:'P2-DEMO-META-003',v:'r1',title:'Synthetic systematic review · tables and forest plots',type:'SYSTEMATIC_REVIEW_META',kind:'PDF_HANDOFF',stage:'CONVERSION_REVIEW',rights:'DEMO_NOT_QUALIFIED',project:'',batch:'',units:0,raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO',risk:'Table structure needs manual check'},
    {id:'P2-DEMO-OBS-004',v:'r1',title:'Observational study example · population and exposure mapping',type:'OBSERVATIONAL_STUDY',kind:'PDF_HANDOFF',stage:'RIGHTS_HOLD',rights:'RIGHTS_UNVERIFIED',project:'',batch:'',units:0,raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO',risk:'Rights require independent verification'},
    {id:'P2-DEMO-CORR-005',v:'r2',title:'Correction notice illustration · source family link',type:'CORRECTION_RETRACTION',kind:'HTML',stage:'VERSION_REVIEW',rights:'DEMO_NOT_QUALIFIED',project:'',batch:'',units:2,raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO',risk:'Version lineage unresolved'},
    {id:'P2-DEMO-RCT-006',v:'r1',title:'Structured Markdown example · source quote verification',type:'RANDOMIZED_TRIAL',kind:'MARKDOWN',stage:'QA_HOLD',rights:'DEMO_NOT_QUALIFIED',project:'',batch:'',units:11,raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO',risk:'Evidence anchors are design placeholders'}
  ];
  const demos=[
    {unit_id:'u0001',kind:'PARAGRAPH',text:'Participants were assigned 1:1 to two study arms.',translation:'参与者按 1:1 比例被分配到两个研究组。',pdf_locator_status:'PAGE_HINT_ONLY',issue:'只作示例定位'},
    {unit_id:'u0002',kind:'PARAGRAPH',text:'The primary endpoint was assessed at week 12.',translation:'主要终点在第十二周进行评估。',pdf_locator_status:'UNRESOLVED',issue:'原件页码和坐标未核实'},
    {unit_id:'u0003',kind:'TABLE_CELL',text:'Group A: 20; Group B: 20. Numbers are synthetic.',translation:'A 组：20；B 组：20。仅为虚构数值。',pdf_locator_status:'PAGE_HINT_ONLY',issue:'表格数值和合并单元格须人工核查'}
  ];
  const stages={
    RIGHTS_HOLD:['权限待确认','amber'],RIGHTS_ACCEPTED:['已记录合成用途','teal'],
    QA_PENDING:['人工 QA 待完成','amber'],QA_HOLD:['QA 问题待处理','red'],
    PACKAGE_FROZEN:['合成包已冻结','teal'],CONVERSION_REVIEW:['转换处理中 · 演示','blue'],
    PACKAGE_DESIGN_PREVIEW:['演示封存','teal'],VERSION_REVIEW:['版本关系待核查','blue']
  };
  const governanceMatrix=[
    ['01','Scientific authority / 临床适用','R6 当前规范原件缺失','blocked'],
    ['02','SIS Core 结构不膨胀','静态语义对齐','aligned'],
    ['03','Observation / State / Truth 分离','静态语义对齐','aligned'],
    ['04','双层科学证据 / Applicability','需精确 Adapter 映射','pending'],
    ['05','信息充分性与条件性决策','静态语义对齐','aligned'],
    ['06','Human–Ontology Separation','静态语义对齐','aligned'],
    ['07','Set-valued Reference','静态语义对齐','aligned'],
    ['08','Strict exposure / 反后见之明','运行时测试未完成','pending'],
    ['09','纵向监测 / Re-decision','静态语义对齐','aligned'],
    ['10','临床长程决策 LHDI','R6 原件缺失；待评估','blocked'],
    ['11','Estimand-first Program 路由','静态语义对齐','aligned'],
    ['12','SIS R5 精确来源快照','181565-byte 目标待恢复','blocked'],
    ['13','SIS-MED R6 P0.4 原件','61116-byte 目标待恢复','blocked'],
    ['14','AI Nutri v2.1 ⇄ NDSF','正式版本绑定待补','pending'],
    ['15','物理契约 / 运行时合格性','未执行完整 Non-Regression','pending']
  ];
  const governanceVerdict={aligned:['文本语义对齐','teal'],pending:['待追溯测试','amber'],blocked:['NOT ASSESSED · BLOCK','red']};
  const tabs={library:'工作队列总览',intake:'筛选与来源登记',convert:'结构化处理',qa:'QA 阅读与锚点核验',versions:'版本资料库',audit:'版本谱系与审计'};
  const types={RANDOMIZED_TRIAL:'随机对照试验',OBSERVATIONAL_STUDY:'观察性研究',
    SYSTEMATIC_REVIEW_META:'系统综述',GUIDELINE:'指南 / 共识',CONSENSUS:'专家共识',
    NARRATIVE_REVIEW:'叙述性综述',CORRECTION_RETRACTION:'更正 / 撤稿'};
  let state={tab:'library',selection:'P2-DEMO-RCT-001',search:'',status:'',kindFilter:'',unitIndex:0,highlighted:false,
    display:'bilingual',drawer:false,wizard:false,step:0,notice:'',sourceFilter:'all',liveSources:[],overview:null,
    document:null,original:null,translations:new Map(),reviewed:new Set(),draft:null,scope:{project:'',batch:''},projects:[],
    batches:new Map(),role:'manager',session:null,sourceCount:0,loading:false,intakePreset:null,auditResult:null,
    scopeExpanded:false,versionTab:'lineage',intakeInline:true};
  let root=null;
  const selected=()=>all().find(x=>x.id+':'+x.v===state.selection)||all().find(x=>x.id===state.selection)||all()[0];
  const all=()=>state.liveSources.map(x=>({
    id:x.source_id,v:x.revision_id,title:x.title,type:x.source_type,kind:x.raw_format,
    stage:x.status,rights:x.rights_status,identifier:x.identifier||'',project:'',batch:'',units:x.unit_count||0,
    raw:x.raw_artifact_sha256,canonical:x.document_sha256||'NOT_YET_CONVERTED',
    risk:'独立权利与 Human QA 记录须核查',live:true,doc:x.document_sha256,
    package:x.package_sha256,reviewed:x.reviewed_units||0,source:x
  })).concat(fixtures);
  const principal=()=>state.session||(typeof auth!=='undefined'?auth:null);
  const canSubmit=()=>state.role==='producer';
  const canReview=()=>state.role==='curator';
  const canRights=()=>state.role==='auditor';
  function api(path,opts={}){
    const headers={'Accept':'application/json'};
    if(opts.body!==undefined)headers['Content-Type']='application/json';
    const p=principal();
    if(opts.method&&opts.method!=='GET'&&p?.csrf_token)headers['x-csrf-token']=p.csrf_token;
    return fetch(path,{method:opts.method||'GET',body:opts.body?JSON.stringify(opts.body):undefined,
      credentials:'same-origin',cache:'no-store',headers}).then(async r=>{
      const payload=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(payload.detail?.code||String(payload.detail||r.status));
      return payload;
    });
  }
  async function reload(){
    if(state.loading)return;
    state.loading=true;
    try{
      const p=new URLSearchParams({limit:'100',offset:'0'});
      if(state.scope.project)p.set('project_id',state.scope.project);
      if(state.scope.batch)p.set('batch_id',state.scope.batch);
      const [meta,overview]=await Promise.all([api('/v1/p2/sources?'+p),api('/v1/p2/overview')]);
      let rows=meta.sources||[],offset=rows.length;
      while(offset<meta.total&&offset<3000){
        p.set('offset',String(offset));
        const next=await api('/v1/p2/sources?'+p);if(!next.sources?.length)break;
        rows=rows.concat(next.sources);offset=rows.length;
      }
      state.liveSources=rows;state.overview=overview;state.sourceCount=meta.total;
      if(root?.isConnected)draw();
    }catch(err){state.notice='P2 后台读取失败：'+err.message;if(root?.isConnected)draw()}
    finally{state.loading=false}
  }
  function view(tab){
    if(!Object.prototype.hasOwnProperty.call(tabs,tab))return;
    state.tab=tab;state.notice='';state.drawer=false;draw();
    // This SPA recreates its subtree; restore keyboard focus to the replacement
    // tab rather than leaving focus on a removed DOM button.
    root?.querySelector('.p2-tabs [data-p2-tab="'+tab+'"]')?.focus({preventScroll:true});
  }
  function metaP(text){return el('p',text,'p2-dim')}
  function panel(title,description,css=''){const n=el('section',null,'p2-card '+css);
    if(title)n.append(el('h2',title));if(description)n.append(metaP(description));return n;}
  function nav(){
    const n=el('nav',null,'p2-tabs p2-page-stepper');n.setAttribute('aria-label','科学资料工作台导航');
    const primary=el('div',null,'p2-primary-tabs');
    const secondary=el('div',null,'p2-secondary-tabs');
    // HiFi Demo v1: four numbered workspace pages + two supporting modules.
    const items=[
      ['library','01','工作队列总览',true],['intake','02','筛选与来源登记',true],
      ['qa','03','QA 阅读与锚点核验',true],['audit','04','版本谱系与审计',true],
      ['convert','','转换作业',false],['versions','','版本资料库',false]
    ];
    for(const [key,no,name,isPrimary]of items){
      const b=button('',()=>view(key),'p2-tab '+(isPrimary?'p2-primary-tab p2-stepitem ':'p2-secondary-tab ')+(state.tab===key?'active':''));
      if(no){const badge=el('span',no,'p2-stepno');b.append(badge);}
      b.append(document.createTextNode(name));
      b.dataset.p2Tab=key;
      b.setAttribute('aria-current',state.tab===key?'page':'false');
      (isPrimary?primary:secondary).append(b);
    }
    n.append(primary,secondary);return n;
  }
  function heading(eyebrow,title,description,actions=[]){
    const n=el('div',null,'p2-heading'),left=el('div');
    append(left,el('p',eyebrow,'p2-eyebrow'),el('h1',title),el('p',description,'p2-subtitle'));
    append(n,left,append(el('div',null,'p2-actions'),actions));return n;
  }
  function context(){
    // P2 project/batch scope is an optional SOURCE LIST FILTER against P2
    // immutable usage references, NOT a scientific eligibility or grant control.
    const n=el('section',null,'p2-context p2-context-compact');
    n.setAttribute('aria-label','科学资料项目与批次筛选');
    const project=state.projects.find(x=>x.project_id===state.scope.project);
    const batches=state.scope.project?(state.batches.get(state.scope.project)||[]):[];
    const batch=batches.find(x=>x.batch_id===state.scope.batch);
    const active=!!(state.scope.project||state.scope.batch);
    const head=el('div',null,'p2-scope-head');
    const explanation=el('div',null,'p2-scope-explanation');
    append(explanation,el('strong','资料范围','p2-scope-title'),
      el('span',active?(project?.name||state.scope.project)+(batch?' / '+batch.label:' · 全部批次'):'全部来源 · 未筛选','p2-scope-current'),
      el('small','只筛选已关联的来源版本，不改变资料资格或专家权限。','p2-scope-description'));
    const actions=el('div',null,'p2-scope-actions');
    if(active)actions.append(button('清除',()=>{
      state.scope.project='';state.scope.batch='';state.scopeExpanded=false;
      draw();reload();
    },'outline p2-scope-clear'));
    const toggle=button(state.scopeExpanded?'收起筛选':'按项目 / 批次筛选',()=>{
      state.scopeExpanded=!state.scopeExpanded;draw();
      root?.querySelector('.p2-scope-toggle')?.focus({preventScroll:true});
    },'outline p2-scope-toggle');
    toggle.setAttribute('aria-expanded',state.scopeExpanded?'true':'false');
    toggle.setAttribute('aria-controls','p2ScopeFields');
    actions.append(toggle);head.append(explanation,actions);n.append(head);
    const fields=el('div',null,'p2-scope-fields');fields.id='p2ScopeFields';
    fields.hidden=!state.scopeExpanded;
    const proj=select([['','全部项目']].concat(state.projects.map(x=>[x.project_id,x.name])),
      state.scope.project,v=>{
        state.scope.project=v;state.scope.batch='';draw();reload();
      });
    proj.setAttribute('aria-label','按项目引用筛选来源');
    proj.disabled=!state.projects.length;
    const bat=select([['','全部批次']].concat(batches.map(x=>[x.batch_id,x.label])),
      state.scope.batch,v=>{state.scope.batch=v;draw();reload()});
    bat.setAttribute('aria-label','按批次引用筛选来源');
    bat.disabled=!state.scope.project||!batches.length;
    const first=field('项目 Project',proj),second=field('批次 Batch',bat);
    first.classList.add('p2-scope-field');second.classList.add('p2-scope-field');
    fields.append(first,second);
    fields.append(el('small',state.projects.length?
      '仅显示已有该项目 / 批次引用的来源；未绑定的资料会被过滤，筛选不是授权。':
      '当前没有可选项目。项目与批次在任务中心创建；本页保持全局来源视图。筛选不是授权。','p2-scope-hint'));
    n.append(fields);return n;
  }
  function frame(){
    const n=el('div',null,'p2-studio');
    const meta=el('div',null,'p2-meta-strip');
    const breadcrumb=el('div','工作空间  ›  科学资料处理台  ›  '+(tabs[state.tab]||'工作队列总览'),'p2-breadcrumb');
    const safety=el('span','仅限隔离合成工程 · 未开放真实 PDF、MinerU、Gold 或专家授权','p2-safety-inline');
    meta.append(breadcrumb,safety);n.append(meta,nav());
    // Demo v1: Project/Batch scope sits under the page stepper as a top bar.
    // Never show it on the global audit page (page 04).
    if(state.tab!=='audit'&&document.getElementById('p11Nav'))
      n.append(context());
    if(state.notice)n.append(alert(state.notice,'note'));
    return n;
  }
  function rightsChip(x){
    if(x.rights==='SYNTHETIC_RIGHTS_ATTESTED'||x.rights==='APPROVE_SYNTHETIC'||
      x.stage==='PACKAGE_FROZEN'||x.stage==='QA_PENDING'||x.stage==='RIGHTS_ACCEPTED')
      return chip('合成核准','teal');
    if(x.stage==='RIGHTS_HOLD'||x.rights==='RIGHTS_UNVERIFIED')return chip('待审查','amber');
    if(!x.live)return chip('演示 · 无准入','muted');
    return chip('无准入','muted');
  }
  function scopeText(x){
    const project=x.project||state.scope.project||'';
    const batch=x.batch||state.scope.batch||'';
    if(project||batch)return (project||'未绑定')+' / '+(batch||'—');
    return '未绑定';
  }
  function statBox(value,name,caption){return append(el('div',null,'p2-stat'),el('span',name,'p2-stat-label'),el('strong',value),el('small',caption));}
  function overviewCards(){
    const sources=all();
    return append(el('div',null,'p2-stats'),
      statBox(String(sources.length).padStart(2,'0'),'演示与合成资料总数','演示条目与持久化合成记录分开标识'),
      statBox(String(sources.filter(x=>['RIGHTS_HOLD','VERSION_REVIEW'].includes(x.stage)).length).padStart(2,'0'),'待来源资格核查','未核准禁止进入结构转换'),
      statBox(String(sources.filter(x=>['QA_PENDING','QA_HOLD'].includes(x.stage)).length).padStart(2,'0'),'待人工 QA','数字、表格与原始锚点需核验'),
      statBox(String(sources.filter(x=>['PACKAGE_FROZEN','PACKAGE_DESIGN_PREVIEW'].includes(x.stage)).length).padStart(2,'0'),'已封存（含演示）','不表示真实科研或专家授权'));
  }
  // Presentation-only guidance; P2 rights, QA and grant checks remain server-owned.
  function nextStep(x){
    if(!x.live)return {title:'演示资料 · 不可操作',detail:'虚构条目不构成已登记或合格来源。',button:'查看演示说明'};
    if(x.stage==='RIGHTS_HOLD')return {title:'等待独立用途审核',detail:'Auditor 签署后，Producer 才能结构化。',button:canRights()?'查看并审核':'查看待核要求'};
    if(x.stage==='RIGHTS_ACCEPTED')return {title:'准备结构化转换',detail:'Producer 生成可追溯 ParserRun 与 Document IR。',button:canSubmit()?'进入转换作业':'查看转换条件'};
    if(x.stage==='QA_PENDING')return {title:'继续逐单元 QA',detail:'Curator 核对原文、数值、表格与锚点。',button:canReview()?'继续核验':'查看 QA 进度'};
    if(x.stage==='QA_HOLD')return {title:'存在 QA 阻断',detail:'保留旧 QA；需要新版本修复，不可原位覆盖。',button:canReview()?'查看 QA 问题':'查看阻断原因'};
    if(x.stage==='PACKAGE_FROZEN')return {title:'查看冻结资料包',detail:'仍不形成 Gold 或专家授权。',button:'查看资料包'};
    if(x.stage==='VERSION_REVIEW')return {title:'核对来源版本',detail:'更正、撤稿或原文版本关系待确认。',button:'查看来源详情'};
    return {title:'检查当前处理阶段',detail:'状态不代表真实科研资料已经合格。',button:'查看详情'};
  }
  function openNextStep(x){
    state.selection=x.id+':'+x.v;
    if(x.live&&x.stage==='RIGHTS_ACCEPTED'&&canSubmit()){view('convert');return;}
    if(x.live&&['QA_PENDING','QA_HOLD'].includes(x.stage)&&canReview()){
      state.tab='qa';state.drawer=false;draw();loadSelectedDocument();return;
    }
    if(x.live&&x.stage==='PACKAGE_FROZEN'){view('versions');return;}
    state.drawer=true;draw();
  }

  function qualRow(title,sub,value,kind){
    const row=el('div',null,'p2-qual-row');
    append(row,append(el('div',null,'p2-qual-copy'),el('strong',title,'p2-qual-name'),el('small',sub,'p2-qual-sub')),
      chip(value,kind));
    return row;
  }
  function inlineDetail(){
    const x=selected();if(!x)return el('section','未选择来源','p2-card p2-inline-detail');
    const card=el('section',null,'p2-card p2-inline-detail');
    card.setAttribute('aria-label','来源详情');
    const head=el('div',null,'p2-inline-detail-head');
    append(head,el('strong','来源详情','p2-card-kicker'),el('span',x.id+' / '+x.v,'p2-id'));
    card.append(head,el('h3',x.title),el('p',(types[x.type]||x.type)+' · '+(x.live?'合成来源':'DEMO ONLY'),'p2-dim'));
    const guide=nextStep(x);
    const hero=el('div',null,'p2-status-hero');
    append(hero,el('div',null,'p2-status-bubble'),
      append(el('div'),el('strong','当前阶段 · '+(stages[x.stage]?.[0]||x.stage)),
        el('small',guide.detail,'p2-dim')));
    card.append(hero);
    card.append(el('h4','来源资格 · 五维状态','p2-small-title'));
    const quals=el('div',null,'p2-qual-list');
    const rightsOk=x.rights==='SYNTHETIC_RIGHTS_ATTESTED'||x.stage==='PACKAGE_FROZEN'||x.stage==='QA_PENDING'||x.stage==='RIGHTS_ACCEPTED';
    const structured=!!(x.doc||x.canonical&&x.canonical!=='NOT_YET_CONVERTED'&&x.canonical!=='NOT_COMPUTED_DEMO');
    const qaDone=x.units>0&&(x.reviewed||0)>=x.units&&x.stage==='PACKAGE_FROZEN';
    quals.append(
      qualRow('原件完整性','完整性为合成记录检查',x.live?'已记录':'不可用',x.live?'teal':'muted'),
      qualRow('使用授权','不等同真实出版商许可',rightsOk?'仅合成核准':'待审核',rightsOk?'teal':'amber'),
      qualRow('结构化转换','保留 Parser 与 Unit 版本',structured?'示例完成':'未完成',structured?'teal':'amber'),
      qualRow('Unit QA','独立 Curator 的单元核查',(x.reviewed||0)+' / '+x.units,(qaDone?'teal':'blue')),
      qualRow('专家暴露','独立授权，不由来源页面签发','未授权','red'));
    card.append(quals,alert('资料来源合格、专家参考真值、Gold 资格与专家可见性不能混同。','warning'));
    const facts=el('dl',null,'p2-facts');
    for(const [k,v] of [['Raw SHA-256',x.raw],['Canonical SHA',x.canonical],
      ['Project / Batch',(x.project||state.scope.project||'未绑定')+' / '+(x.batch||state.scope.batch||'—')],
      ['下一步',guide.title]])append(facts,el('dt',k),el('dd',String(v||'—')));
    card.append(el('h4','版本与引用','p2-small-title'),facts);
    const deps=el('div',null,'p2-dep-flow');
    deps.append(chip('SIS R5','blue'),el('span','→','p2-dim'),chip('Nutrition Foundation v0.1','teal'),
      el('span','→','p2-dim'),chip('AI Nutri v2.1 · 适配待签署','amber'));
    card.append(el('h4','科学规范与适用边界','p2-small-title'),deps,
      alert('临床营养当前权威 SIS-MED R6 P0.4；精确原件缺失时条款级符合性 NOT ASSESSED。','warning'));
    const actions=el('div',null,'p2-inline-detail-actions');
    actions.append(
      button('打开 QA 阅读器',()=>{state.tab='qa';state.drawer=false;draw();if(canReview()&&x.live)loadSelectedDocument()},'primary'),
      button('版本谱系',()=>view('audit'),'outline'),
      button('完整工作区',()=>{state.drawer=true;draw()},'outline'));
    card.append(actions);return card;
  }
  function queueSummary(){
    const rows=state.liveSources;
    const groups=[
      ['待用途审核',rows.filter(x=>x.status==='RIGHTS_HOLD').length,'RIGHTS_HOLD','amb'],
      ['待结构化',rows.filter(x=>x.status==='RIGHTS_ACCEPTED').length,'RIGHTS_ACCEPTED','blu'],
      ['待人工 QA',rows.filter(x=>x.status==='QA_PENDING').length,'QA_PENDING','pur'],
      ['QA 阻断',rows.filter(x=>x.status==='QA_HOLD').length,'QA_HOLD','re'],
      ['已封存',rows.filter(x=>x.status==='PACKAGE_FROZEN').length,'PACKAGE_FROZEN','gr']];
    const bar=el('section',null,'p2-queue-summary'),intro=el('div',null,'p2-queue-intro');
    append(intro,el('strong','科学资料工作队列','p2-queue-title'),
      el('span','优先从待处理来源开始，按角色和状态进入下一步。','p2-scope-description'));
    const counts=el('div',null,'p2-queue-counts');
    for(const [label,count,status,tone]of groups){
      const b=button('',()=>{state.status=state.status===status?'':status;draw()},
        'p2-queue-counter p2-metric-'+tone+(state.status===status?' active':''));
      b.append(document.createTextNode(label+' '),el('span',String(count).padStart(2,'0'),'p2-metric-num'));
      b.setAttribute('aria-label','筛选'+label+'的合成来源');
      b.setAttribute('aria-pressed',state.status===status?'true':'false');counts.append(b);
    }
    bar.append(intro,counts);return bar;
  }
  function startIntake(format='MARKDOWN',identifier='SYNTHETIC_ID'){
    state.intakePreset={format,identifier};state.wizard=true;state.step=0;state.draft=null;draw();
  }
  function pipeline(){
    const shell=el('div',null,'p2-flow-shell'),steps=el('div',null,'p2-flow-steps');
    for(const [i,[num,title,desc]] of [
      ['01','来源登记','来源、版本与使用许可'],
      ['02','结构化转换','JATS · HTML · PDF/MinerU'],
      ['03','人工质量核验','原文、数值与 Evidence Anchor'],
      ['04','资料包冻结','不可变 SHA 与审计']
    ].entries()){
      const step=el('div',null,'p2-flow-step'+(i===0?' current':''));
      append(step,el('span',num,'p2-flow-number'),append(el('div'),el('strong',title),el('small',desc)));
      steps.append(step);
    }
    shell.append(steps);
    const grid=el('div',null,'p2-pipeline');
    const left=panel('添加科学资料','选择登记入口，后续统一进入独立资格核验和结构化处理。');
    const actions=el('div',null,'p2-choices');
    for(const [symbol,title,sub,format,identifier] of [
      ['⌕','文献标识符','DOI / PMID / PMCID · 仅元数据','MARKDOWN','DEMO_DOI'],
      ['PDF','本地 PDF','保留原件权限检查；仅隔离 handoff','PDF_HANDOFF','SYNTHETIC_ID'],
      ['</>','XML / HTML','JATS 结构优先，保留解析 lineage','JATS_XML','SYNTHETIC_ID'],
      ['MD','Markdown','结构化稿件须绑定原始资料','MARKDOWN','SYNTHETIC_ID']
    ]){
      const b=button('',()=>startIntake(format,identifier),'p2-choice');
      b.setAttribute('aria-label',title);
      b.append(el('span',symbol,'p2-choice-icon'),append(el('span'),el('strong',title),el('small',sub)));
      actions.append(b);
    }
    left.append(actions,alert('登记不等于授权下载或处理。真实 PDF 上传、在线 DOI 查询及 MinerU 服务尚未开放。','info'));
    grid.append(left);
    const right=panel('准入检查清单','未通过核验的来源不得进入正式专家任务。','p2-gate');
    for(const [i,title,desc] of [
      ['1','来源身份与版本','DOI / PMID / 发布机构 / 勘误撤稿'],
      ['2','使用许可核查','内部存储、机器处理、专家阅读分别核准'],
      ['3','转换结果与原文核验','正文、表格、UTF-16、PDF locator'],
      ['4','不可变版本封存','Raw SHA · Document SHA · Evidence Anchor']
    ]){
      const line=el('div',null,'p2-gate-line');
      append(line,el('span',i,'p2-gate-icon'),append(el('div'),el('strong',title),el('small',desc)));
      right.append(line);
    }
    right.append(alert('🔒 Expert Exposure Gate 保持关闭；资料封存 ≠ 专家授权。'));
    grid.append(right);shell.append(grid);return shell;
  }
  function statFilter(){
    const bar=el('div',null,'p2-status-tabs');
    for(const [id,label] of [['','全部资料'],['RIGHTS_HOLD','来源待核'],['RIGHTS_ACCEPTED','待结构化'],['CONVERSION_REVIEW','转换中'],['QA_PENDING','人工 QA'],['QA_HOLD','QA 阻断'],['PACKAGE_FROZEN','已封存'],['VERSION_REVIEW','版本待核']]){
      const b=button(label,()=>{state.status=id;draw()},'p2-filter-chip'+(state.status===id?' active':''));
      b.setAttribute('aria-pressed',state.status===id?'true':'false');bar.append(b);
    }return bar;
  }
  function sourceList(){
    const wrap=el('section',null,'p2-card p2-source-queue');
    wrap.append(queueSummary());
    const sourceModes=el('div',null,'p2-source-modes');
    const sourceModeLabel=el('span','来源层级','p2-scope-title');
    sourceModes.append(sourceModeLabel);
    for(const [mode,label] of [['all','全部（含演示）'],['registered','已登记合成来源'],['demo','仅界面演示']]){
      const b=button(label,()=>{state.sourceFilter=mode;draw()},'p2-source-mode'+(state.sourceFilter===mode?' active':''));
      b.setAttribute('aria-pressed',state.sourceFilter===mode?'true':'false');
      sourceModes.append(b);
    }
    sourceModes.append(el('small','两类资料严格分离：演示条目没有登记、权利、QA 或专家使用资格。','p2-source-mode-note'));
    wrap.append(sourceModes,statFilter());
    const searchbar=el('div',null,'p2-toolbar');
    const search=textInput(state.search,160);search.placeholder='搜索标题、DOI、PMID 或 Source ID';
    search.setAttribute('aria-label','搜索科学来源');
    search.addEventListener('input',()=>{state.search=search.value;renderTable()});
    const kind=select([['','全部文献类型']].concat(Object.entries(types)),state.kindFilter,
      v=>{state.kindFilter=v;renderTable()});
    const mode=select([['all','全部 · 标记类别'],['registered','仅持久化合成'],['demo','仅虚构 DEMO']],
      state.sourceFilter,v=>{state.sourceFilter=v;renderTable()});
    mode.setAttribute('aria-label','来源数据类型');
    searchbar.append(search,kind,mode,button('刷新真实登记状态',()=>reload(),'outline'));
    wrap.append(searchbar);
    const scroll=el('div',null,'p2-table-wrap'),table=el('table',null,'p2-table p2-queue-table');table.id='p2TableTarget';
    const th=el('thead'),head=el('tr');
    ['','来源 / 版本','资料资格','当前阶段','下一步与角色','QA 进度','引用范围','操作'].forEach(t=>head.append(el('th',t)));
    th.append(head);table.append(th,el('tbody'));scroll.append(table);wrap.append(scroll);
    wrap.append(metaP('已登记记录仅用于隔离合成验证；DEMO 为虚构资料样例。来源冻结 ≠ 真实文献资格 ≠ Gold ≠ 专家访问授权。'));
    renderTableInto(table);return wrap;
  }
  function renderTableInto(table){
    const body=table.querySelector('tbody');body.replaceChildren();
    const rows=all().filter(x=>{
      const f=state.search.trim().toLowerCase();
      return (!f||[x.title,x.id,x.type,x.identifier||''].join(' ').toLowerCase().includes(f))&&
        (!state.status||x.stage===state.status)&&(!state.kindFilter||x.type===state.kindFilter)&&
        (state.sourceFilter==='all'||(state.sourceFilter==='registered'&&x.live)||(state.sourceFilter==='demo'&&!x.live))&&
        (x.live||(!state.scope.project&&!state.scope.batch));
    }).sort((a,b)=>{
      if(a.live!==b.live)return a.live?-1:1;
      const order={QA_HOLD:0,QA_PENDING:1,RIGHTS_HOLD:2,RIGHTS_ACCEPTED:3,VERSION_REVIEW:4,CONVERSION_REVIEW:5,PACKAGE_FROZEN:6,PACKAGE_DESIGN_PREVIEW:7};
      return (order[a.stage]??9)-(order[b.stage]??9)||a.title.localeCompare(b.title);
    });
    for(const x of rows){
      const row=el('tr'),idcell=el('td'),check=el('td',null,'p2-checkcell');
      row.classList.add(x.live?'p2-registered-row':'p2-demo-row');
      const key=x.id+':'+x.v;
      if(state.selection===key||state.selection===x.id)row.classList.add('selected');
      const box=el('input');box.type='checkbox';box.title='选择来源 '+x.id;
      box.checked=state.selection===key||state.selection===x.id;
      box.addEventListener('change',()=>{state.selection=key;state.drawer=false;draw()});
      check.append(box);
      const identity=button(x.title,()=>{state.selection=key;state.drawer=false;draw()},'p2-source-title');
      identity.setAttribute('aria-label','查看来源详情：'+x.title);
      idcell.append(append(el('div',null,'p2-source-identity'),
        el('span',x.kind==='PDF_HANDOFF'?'PDF':x.kind==='JATS_XML'?'XML':x.kind==='MARKDOWN'?'MD':'HTML','p2-filetype'),
        identity),el('div',x.id+' · '+x.v,'p2-id'),
        el('div',(types[x.type]||x.type)+' · 合成','p2-id'));
      const status=stages[x.stage]||[x.stage,'muted'],guide=nextStep(x);
      const rights=el('td');rights.append(rightsChip(x));
      const phase=el('td');phase.append(chip(status[0],status[1]));
      const next=el('td',null,'p2-next-cell');
      next.append(el('strong',guide.title),el('small',guide.detail));
      const qa=el('td',null,'p2-qa-cell');
      const qaFraction=String(x.reviewed||0)+' / '+x.units;
      const qaTrack=el('span',null,'p2-row-progress'),qaFill=el('span',null,'p2-row-progress-fill');
      qaFill.style.width=(100*(x.reviewed||0)/Math.max(x.units,1))+'%';
      qaTrack.append(qaFill);
      qa.append(el('strong',qaFraction),qaTrack);
      const cite=el('td',scopeText(x),'p2-cite-cell');
      const action=el('td');
      action.append(button(guide.button,()=>openNextStep(x),'small'+
        (x.live&&['RIGHTS_ACCEPTED','QA_PENDING'].includes(x.stage)?' primary':'')));
      row.append(check,idcell,rights,phase,next,qa,cite,action);
      ['','来源 / 版本','资料资格','当前阶段','下一步与角色','QA 进度','引用范围','操作'].forEach((name,i)=>{
        row.children[i].dataset.label=name;
      });
      body.append(row);
    }
    if(!rows.length){
      const tr=el('tr'),td=el('td','当前范围没有符合条件的来源版本。可切换来源层级、清除状态筛选或登记合成来源。','p2-dim');
      td.colSpan=8;tr.append(td);body.append(tr);
    }
  }
  function renderTable(){const t=document.getElementById('p2TableTarget');if(t)renderTableInto(t)}
  function library(){
    root.append(heading('P2 / SCIENTIFIC SOURCE WORKSPACE · 高保真交互原型 v1.0','科学资料处理台',
      '按状态处理科学来源，先找到材料，再进入操作 · 只提供合成资料流程演示，不接入真实数据或权限系统。',
      [...(document.getElementById('p11Nav')?[button('B1 合成来源引用 ↗',()=>{window.opsA5OpenB1SourceReferences?.()},'outline')]:[]),
       button('查看版本与引用',()=>view('audit'),'outline'),
       button('审计与规范',()=>{state.versionTab='governance';view('audit')},'outline'),
       button('＋ 登记科学来源',()=>startIntake(),'primary')]));
    const grid=el('div',null,'p2-workgrid');
    const left=el('div',null,'p2-workgrid-main');
    left.append(sourceList());
    grid.append(left,inlineDetail());
    root.append(grid);
    root.append(el('h2','流程指引 · 首次使用时参考','p2-reference-heading'));
    root.append(overviewCards(),pipeline());
  }
  function ensureDraft(){
    return state.draft||(state.draft={
      source_id:'P2-SYN-'+crypto.randomUUID().replaceAll('-','').slice(0,10).toUpperCase(),
      revision_id:'r1',title:'',
      source_type:'SYSTEMATIC_REVIEW_META',identifier_kind:state.intakePreset?.identifier||'SYNTHETIC_ID',
      identifier:'',year:'2026',
      available_at:'2026-01-01T00:00:00Z',fetched_at:'2026-01-02T00:00:00Z',
      raw_format:state.intakePreset?.format||'MARKDOWN',
      raw_content:'# Synthetic scientific paper\n\nThis is illustrative document text for source QA only.\n\n| Group | Value |\n| A | 12.4 |',
      rights_assertion:'SYNTHETIC_FIXTURE',source_family_refs:[],
      project:state.scope.project||'',batch:state.scope.batch||''});
  }
  function intakeInlineForm(){
    const d=ensureDraft();
    const card=el('section',null,'p2-card p2-intake-card');
    const head=el('div',null,'p2-intake-card-head');
    append(head,append(el('div'),el('strong','＋ 来源登记 · 合成资料','p2-card-kicker'),
      el('p','演示完整登记流程与独立资格审查，不接受真实原始论文。','p2-dim')),
      chip('DRAFT ONLY','amber'));
    card.append(head);
    const steps=el('nav',null,'p2-intake-steps');steps.setAttribute('aria-label','登记步骤');
    ['01 来源身份','02 原始内容','03 许可与用途','04 范围确认'].forEach((label,i)=>{
      const b=button(label,()=>{state.step=i;draw()},'p2-intake-step'+(state.step===i?' active':''));
      b.setAttribute('aria-current',state.step===i?'step':'false');
      steps.append(b);
    });
    card.append(steps);
    const form=el('form',null,'p2-wizard-form p2-intake-form');form.addEventListener('submit',ev=>ev.preventDefault());
    function addText(name,key,limit=200,ph=''){
      const n=textInput(d[key]||'',limit);if(ph)n.placeholder=ph;
      n.addEventListener('input',()=>{d[key]=n.value});form.append(field(name,n));return n;
    }
    function addSelect(name,key,choices){form.append(field(name,select(choices,d[key],v=>{d[key]=v})))}
    if(state.step===0){
      const grid=el('div',null,'p2-form-grid');
      const title=textInput(d.title||'',130);title.placeholder='示例：营养干预与健康结局 · 虚构研究';
      title.addEventListener('input',()=>{d.title=title.value});
      grid.append(field('来源标题 *',title));
      grid.append(field('来源类型',select(Object.entries(types),d.source_type,v=>{d.source_type=v})));
      const year=textInput(d.year||'2026',4);year.addEventListener('input',()=>{d.year=year.value});
      grid.append(field('出版 / 更新年（模拟）',year));
      const ident=textInput(d.identifier||'',120);ident.placeholder='真实编号不会自动确权';
      ident.addEventListener('input',()=>{d.identifier=ident.value});
      grid.append(field('DOI / PMID（可留空）',ident));
      const nature=el('div','SYNTHETIC · 合成演示原件','p2-nature-box');
      grid.append(field('来源材料性质',nature));
      form.append(grid,el('p','Source ID 在提交登记时生成；不会形成 DOI 查询、馆藏数据或科学资格。','p2-slide-note'));
    }else if(state.step===1){
      form.append(alert('真实 PDF / MinerU handoff 需要独立来源系统、版权、原文校验及 Parser provenance。当前不接收真实上传。','info'));
      const drop=el('div',null,'p2-filedrop');
      drop.append(el('strong','synthetic_nutrition_source.md'),
        el('small','内置虚构内容 · 用于演示 Parser / Unit 流程','p2-dim'),chip('SYNTHETIC','teal'));
      form.append(field('合成原始材料 / Raw Artifact',drop));
      const raw=el('textarea');raw.rows=7;raw.maxLength=200000;raw.value=d.raw_content;
      raw.addEventListener('input',()=>{d.raw_content=raw.value});
      form.append(field('虚构来源原文（仅合成测试）',raw));
      addSelect('原件格式', 'raw_format',[['MARKDOWN','Markdown'],['JATS_XML','JATS/XML'],['HTML','HTML'],['PDF_HANDOFF','PDF / MinerU handoff']]);
    }else if(state.step===2){
      const list=el('div',null,'p2-rights-checklist');
      for(const [title,sub,value,kind] of [
        ['保留原件','是否获准在指定存储介质保存','无真实授权','amber'],
        ['机器处理','包括 OCR / 解析 / 翻译 / 模型处理','无真实授权','amber'],
        ['专家阅读','特定角色的逐源访问许可','NO-GO','red'],
        ['重新发布','对外传播、论文附录 / 模型训练','NO-GO','red']
      ])list.append(qualRow(title,sub,value,kind));
      form.append(list,alert('Demo 内仅使用虚构材料及合成批准状态，不代表现实中的法律许可或真实审核签名。','warning'));
    }else{
      form.append(alert('Project/Batch 只是合成来源的拟使用范围。仅 Package 冻结后才能单独建立引用；不能直接发布给专家。','info'));
      const projChoices=[['','未选择']].concat(state.projects.map(x=>[x.project_id,x.name]));
      if(!state.projects.length)projChoices.push(['PRJ-SYN-001','PRJ-SYN-001（演示）'],['PRJ-SYN-002','PRJ-SYN-002（演示）']);
      const batches=state.scope.project?(state.batches.get(state.scope.project)||[]):[];
      const batChoices=[['','未选择']].concat(batches.map(x=>[x.batch_id,x.label]));
      if(!batches.length)batChoices.push(['BATCH-SYN-01','BATCH-SYN-01（演示）'],['BATCH-SYN-02','BATCH-SYN-02（演示）']);
      addSelect('计划引用项目','project',projChoices);
      addSelect('计划引用批次','batch',batChoices);
      form.append(metaP('登记后进入 RIGHTS_HOLD；独立 Auditor 须另行签署合成用途。'));
    }
    const actions=el('div',null,'p2-intake-nav');
    actions.append(el('span','步骤 '+(state.step+1)+' / 4','p2-dim'));
    const back=button('← 上一步',()=>{state.step=Math.max(0,state.step-1);draw()},'outline');
    if(state.step===0)back.disabled=true;
    actions.append(back,button(state.step===3?'提交合成来源登记':'下一步 →',async()=>{
      if(state.step<3){state.step++;draw();return;}
      if(!canSubmit()){state.notice='只有 Producer 可以登记合成来源。';draw();return;}
      if((d.title||'').trim().length<4){state.notice='请先填写至少 4 字的合成来源标题。';state.step=0;draw();return;}
      const payload={...d,title:d.title.trim()};
      delete payload.year;delete payload.project;delete payload.batch;
      const saved=await perform(()=>api('/v1/p2/sources',{method:'POST',body:payload}),
        '来源已登记并进入独立用途权利待核查状态');
      if(!saved)return;
      state.tab='library';state.selection=d.source_id+':'+d.revision_id;state.draft=null;
      state.intakePreset=null;state.step=0;state.status='';state.search='';draw();
    },'primary'));
    form.append(actions);card.append(form);return card;
  }
  function intakeSidePanel(){
    const side=el('aside',null,'p2-intake-side');
    const gate=panel('科学来源准入条件','登记不等于授权；以下五维须独立核验。');
    const quals=el('div',null,'p2-qual-list');
    quals.append(
      qualRow('原件身份','DOI / 发布机构 / 勘误','待记录','amber'),
      qualRow('许可范围','存储 / 机器处理 / 阅读','独立审核','amber'),
      qualRow('结构化 / 锚点','Unit 与 Evidence Anchor','待核验','blue'),
      qualRow('科学适用性','GOV-0.4 条款级','未评价','muted'),
      qualRow('专家资格','Exposure Gate','禁止访问','red'));
    gate.append(quals,alert('登记 DOI/PDF 不等于版权或临床决策授权。','warning'));
    const bounds=panel('科学决策边界 · GOV-0.4','当前上游规范快照仅供演示。');
    const deps=el('div',null,'p2-dep-flow');
    deps.append(chip('SIS R5','blue'),chip('Nutrition Foundation v0.1','teal'),
      chip('AI Nutri v2.1','amber'),chip('SIS-MED R6 P0.4','red'));
    bounds.append(deps,alert('R6 完整原件尚未恢复；条款级符合性 NOT ASSESSED。','warning'));
    side.append(gate,bounds);return side;
  }
  function renderIntake(){
    root.append(heading('P2 / SCIENTIFIC SOURCE WORKSPACE · 高保真交互原型 v1.0','科学资料处理台',
      '将身份登记、用途审核与 Project/Batch 使用意图分开管理 · 只提供合成资料流程演示。',
      [button('＋ 登记新来源',()=>startIntake(),'primary'),
       button('查看版本与引用',()=>view('audit'),'outline'),
       button('审计与规范',()=>{state.versionTab='governance';view('audit')},'outline')]));
    const layout=el('div',null,'p2-intake-layout');
    const main=el('div',null,'p2-intake-main');
    main.append(intakeInlineForm());
    const filters=panel('工作队列筛选规则','筛选选项独立于资格审查及用户权限。');
    filters.classList.add('p2-intake-filters');
    const filterRow=el('div',null,'p2-form-grid p2-form-grid-3');
    filterRow.append(
      field('来源类型',select([['','全部类型']].concat(Object.entries(types)),state.kindFilter,v=>{state.kindFilter=v})),
      field('项目 Project',select([['','全部项目']].concat(state.projects.map(x=>[x.project_id,x.name])),
        state.scope.project,v=>{state.scope.project=v;state.scope.batch='';draw();reload()})),
      field('批次 Batch',select([['','全部批次']].concat(
        (state.scope.project?(state.batches.get(state.scope.project)||[]):[]).map(x=>[x.batch_id,x.label])),
        state.scope.batch,v=>{state.scope.batch=v;draw();reload()})));
    filters.append(filterRow,button('返回工作队列',()=>view('library'),'outline'));
    main.append(filters);
    // Auditor still needs a reviewable list of pending synthetic sources.
    if(canRights()||state.liveSources.length){
      const pending=panel('待独立用途审核','Auditor 在此打开详情并签署合成用途；不加载原文。');
      const table=el('table',null,'p2-table p2-intake-table');
      const head=el('tr');
      ['资料名称 / Source ID','来源标识','版权与用途','处理阶段','操作'].forEach(x=>head.append(el('th',x)));
      table.append(append(el('thead'),head));
      const rows=el('tbody');
      for(const x of all().filter(x=>x.live)){
        const row=el('tr'),identity=el('td');
        identity.append(el('strong',x.title),el('div',x.id+' · '+x.v,'p2-id'));
        const status=stages[x.stage]||[x.stage,'muted'];
        const action=button('查看',()=>{state.selection=x.id+':'+x.v;state.drawer=true;draw()},'small');
        row.append(identity,el('td',x.identifier||x.id),el('td',x.rights||'—'),
          append(el('td'),chip(status[0],status[1])),append(el('td'),action));
        rows.append(row);
      }
      table.append(rows);pending.append(append(el('div',null,'p2-table-wrap'),table));
      if(!state.liveSources.length)pending.append(alert('暂无持久化合成来源。演示条目不能直接用于专家任务。','info'));
      main.append(pending);
    }
    layout.append(main,intakeSidePanel());
    root.append(layout);
  }
  function conversion(){
    root.append(heading('P2-B / DOCUMENT CONVERSION','结构化转换作业',
      'PDF/MinerU 是上游适配器；转换后必须存储独立 ParserRun 和稳定单元结构。'));
    const panel1=panel('待处理 / 已处理作业','支持 Markdown、JATS XML 和静态 HTML 的确定性处理；PDF 必须提供独立外部结构化 handoff。');
    const table=el('table',null,'p2-table');const h=el('tr');
    ['来源','解析方式','阶段','单元数','下一步'].forEach(t=>h.append(el('th',t)));
    table.append(append(el('thead'),h));
    const tb=el('tbody');
    for(const x of all()){
      const row=el('tr'),ops=el('td');const status=stages[x.stage]||[x.stage,'muted'];
      if(x.live&&x.stage==='RIGHTS_ACCEPTED'&&canSubmit()){
        ops.append(button('开始结构化转换',async()=>{
          let external_payload=null;
          if(x.kind==='PDF_HANDOFF'){
            const value=window.prompt('输入来自独立 MinerU 处理器的结构化 JSON handoff（本环境仅接受合成示例）');
            if(!value)return;
            try{external_payload=JSON.parse(value)}catch{state.notice='不合法的 JSON handoff';draw();return;}
          }
          await perform(()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/convert',{method:'POST',body:{external_payload}}),
            '转换已提交并冻结结构化文档版本');
        },'small primary'));
      }else ops.append(button('查看版本',()=>{state.selection=x.id+':'+x.v;state.drawer=true;draw()},'small'));
      row.append(append(el('td'),el('strong',x.title),el('div',x.id+' · '+x.v,'p2-id')),el('td',x.kind),append(el('td'),chip(status[0],status[1])),
        el('td',String(x.units)),ops);tb.append(row);
    }
    table.append(tb);panel1.append(append(el('div',null,'p2-table-wrap'),table));root.append(panel1);
    const lower=el('div',null,'p2-two');
    const p1=panel('转换优先级','结构化 JATS/XML → HTML → Markdown → PDF handoff；扫描 PDF 和真实 MinerU 服务仍需外部合格适配器。');
    const p2=panel('Structured Document IR','Unit ID、种类、原文、UTF-16 长度、Unit SHA、页面提示和 Parser lineage。');
    p2.append(alert('PDF page hint ≠ VERIFIED_UNIQUE_PDF_TEXT；本运行时不承认未经人工验证的 BBox。','warning'));
    lower.append(p1,p2);root.append(lower);
  }
  async function loadSelectedDocument(){
    const x=selected();
    state.document=null;state.original=null;state.translations=new Map();state.reviewed=new Set();state.unitIndex=0;
    if(!x?.live||!canReview()){draw();return;}
    try{
      const url='/v1/p2/sources/'+x.id+'/'+x.v;
      const [document,original,reviews,translations]=await Promise.all([
        api(url+'/document'),api(url+'/original'),api(url+'/reviews'),api(url+'/translations')]);
      if(document.document.raw_artifact_sha256!==original.raw_artifact_sha256)
        throw new Error('SOURCE_ARTIFACT_SHA_DRIFT');
      state.document=document;state.original=original;
      state.reviewed=new Set(reviews.reviews.map(x=>x.unit_id));
      state.translations=new Map(translations.translations.map(x=>[x.unit_id,x]));
      draw();
    }catch(err){state.notice='结构化文档/原文/审查记录无法完成独立核验：'+err.message;draw();}
  }
  function setUnitIndex(i){
    const count=qaUnits().length;
    if(!count)return;
    state.unitIndex=((i%count)+count)%count;draw();
    root?.querySelectorAll('.p2-structured-pane .p2-unit')[state.unitIndex]?.scrollIntoView({block:'nearest',inline:'nearest'});
  }
  function qa(){
    root.append(heading('P2 / HUMAN SOURCE QA · 高保真交互原型 v1.0','科学资料处理台',
      '原文为权威，译文为辅助；证据锚点需要可复核的精确坐标 · 只提供合成资料流程演示。',
      [button(state.highlighted?'隐藏锚点对应':'显示锚点对应',()=>{state.highlighted=!state.highlighted;draw()},'outline'),
       button('← 上一单元',()=>setUnitIndex(state.unitIndex-1),'outline'),
        button('下一单元 →',()=>setUnitIndex(state.unitIndex+1),'outline'),
       button('申请封存检查',()=>{state.notice='封存失败或待批准：必须完成独立权利记录、全部 Unit QA、真实定位审查及精确 SHA；本页不签发 Gold/Expert Grant。';draw()},'primary')]));
    const selector=el('div',null,'p2-reader-select');selector.append(chip('SOURCE · SYNTHETIC_ONLY','muted'));
    const opts=all().filter(x=>x.live).map(x=>[x.id+':'+x.v,x.id+' / '+x.v+' · '+x.stage]);
    const chosen=selected();
    selector.append(select([['','选择后端文档']].concat(opts),chosen?.live?chosen.id+':'+chosen.v:'',
      v=>{if(!v)return;state.selection=v;loadSelectedDocument()}));
    const optsMode=[['bilingual','逐段双语'],['original','仅原文'],['translation','辅助译文']];
    const mode=el('div',null,'p2-reading-mode');optsMode.forEach(([id,name])=>mode.append(
      button(name,()=>{state.display=id;draw()},'p2-mode'+(id===state.display?' active':''))));
    selector.append(mode);root.append(selector);
    if(!canReview()&&!canSubmit()){
      root.append(alert('该账号仅可浏览来源元数据。只有经过单独身份配置的 Source Curator 才能加载后端结构化原文并签发 Human QA 记录。','warning'));return;
    }
    const doc=state.document,actual=!!(canReview()&&doc?.document&&state.original?.raw_artifact_sha256===doc.document.raw_artifact_sha256);
    root.append(alert(actual?'当前展示已持久化的合成结构化资料，只有 Source Curator 可提交逐单元 QA。':
      '当前为内置的虚构演示片段。Producer 仅查看界面样例，不代表拥有真实来源全文或 Curator 审核权限。','warning'));
    const context=el('section',null,'p2-reading-context');
    const stageLabel=stages[chosen?.stage]?.[0]||chosen?.stage||'未选择';
    append(context,append(el('div',null,'p2-reading-identity'),
      el('strong',chosen?.live?chosen.title:'未加载受控来源；下方仅显示虚构示例'),
      el('span',(chosen?.id||'DEMO')+' · '+(chosen?.v||'—')+' · '+stageLabel,'p2-id')),
      chip(actual?'原文 SHA 一致 · 合成验证':'不具有真实原件核验资格',actual?'teal':'amber'));
    root.append(context);
    const progressUnits=qaUnits(),progressDone=canReview()&&state.document?.document?state.reviewed.size:0;
    const progress=el('div',null,'p2-qa-progress');
    append(progress,el('strong','核验进度：'+progressDone+' / '+progressUnits.length+' Unit'),
      el('span',canReview()&&state.document?.document?
        '只统计服务端已持久化的独立 QA；缺失或拒绝均阻断冻结。':
        '演示单元不计入真实 QA；仅独立 Curator 能保存审核结果。'));
    const track=el('div',null,'p2-progress-track'),fill=el('span',null,'p2-progress-fill');
    fill.style.width=(100*progressDone/Math.max(progressUnits.length,1))+'%';
    track.append(fill);progress.append(track);root.append(progress);
    const grid=el('div',null,'p2-qa-grid');
    const original=panel('原始资料对照','Source Artifact · Page Hint。');
    const sheet=el('div',null,'p2-pdf-sheet');sheet.dataset.p2ReadSurface='original';
    sheet.append(el('small',actual?'ORIGINAL ARTIFACT · VERIFIED SHA':'SYNTHETIC DOCUMENT EXCERPT'),el('h3','ABSTRACT / METHODS'));
    const units=qaUnits();
    if(actual){
      const originalText=el('pre',null,'p2-original-text');
      const raw=state.original.raw_content||'',target=units[state.unitIndex]?.text||'';
      const index=(state.highlighted&&target)?raw.indexOf(target):-1;
      if(index>=0)originalText.append(document.createTextNode(raw.slice(0,index)),
        el('mark',target,'p2-highlighted-quote'),document.createTextNode(raw.slice(index+target.length)));
      else originalText.textContent=raw;
      sheet.append(originalText);
    }else{
      for(const [i,u]of units.slice(0,3).entries()){
        const p=el('p');
        if(state.highlighted&&i===state.unitIndex)p.append(el('mark',u.text,'p2-highlighted-quote'));
        else p.textContent=u.text;sheet.append(p);
      }
    }
    sheet.append(el('strong',actual?'RAW SOURCE SHA VERIFIED · SYNTHETIC':'DEMO ONLY'));
    original.append(sheet,metaP('原始 PDF 未加载；页面坐标未获独立验证。'));
    grid.append(original);
    const middle=panel('Structured Document IR','稳定 Unit ID · 段落级对照 · 原文 SHA 独立');
    middle.classList.add('p2-structured-pane');middle.dataset.p2ReadSurface='structured';
    for(const [i,u]of units.entries()){
      const item=el('button',null,'p2-unit'+(i===state.unitIndex?' selected':''));
      item.type='button';item.setAttribute('aria-pressed',i===state.unitIndex?'true':'false');
      item.addEventListener('click',()=>setUnitIndex(i));
      item.append(el('span',u.unit_id+' · '+u.kind,'p2-unit-meta'));
      if(actual&&state.reviewed.has(u.unit_id))item.append(chip('已提交 QA','teal'));
      if(state.display!=='translation'){
        const paragraph=el('div',null,'p2-reader-paragraph');
        const text=u.text||'';
        if(state.highlighted&&i===state.unitIndex)paragraph.append(el('mark',text,'p2-highlighted-quote'));
        else paragraph.textContent=text;
        item.append(paragraph);
      }
      if(state.display!=='original'){
        const translation=actual?state.translations.get(u.unit_id)?.translation_zh:u.translation;
        item.append(el('div',translation||'辅助译文尚未生成 · AUXILIARY_ONLY','p2-translation'));
      }
      if(u.kind==='TABLE_CELL')item.append(chip('表格单元格 · 数值需单独核验','amber'));
      middle.append(item);
    }grid.append(middle);
    const right=panel('Evidence Anchor','QA · Source Curator');
    right.classList.add('p2-qa-side');right.dataset.p2ReadSurface='review';
    const u=units[state.unitIndex]||units[0];
    const span=append(el('dl',null,'p2-facts'),
      el('dt','Evidence Unit'),el('dd',u.unit_id+' · '+u.kind),
      el('dt','原文 Quote'),el('dd',u.text),
      el('dt','UTF-16 Span'),el('dd','0 → '+String(u.utf16_length||u.text.length)),
      el('dt','Canonical SHA'),el('dd',actual?doc.document_sha256:'NOT_COMPUTED_DEMO'),
      el('dt','PDF Locator'),el('dd',u.pdf_locator_status||'UNRESOLVED'));
    right.append(chip(actual?(state.reviewed.has(u.unit_id)?'已提交独立 Unit QA':'ORIGINAL_SPAN_CHECK_PENDING'):'DEMO_TEXT_ONLY',
      actual&&state.reviewed.has(u.unit_id)?'teal':'blue'),span);
    right.append(alert('本地段落高亮不等于来自 PDF 的唯一定位。表格及数字、剂量和单位必须独立核验。','warning'));
    if(actual){
      if(canReview()&&!state.translations.has(u.unit_id)){
        const wrap=el('div',null,'p2-translation-entry');
        const area=el('textarea');area.rows=3;area.maxLength=10000;
        area.placeholder='逐段辅助译文 · 不影响原文 SHA / Evidence Anchor';
        wrap.append(field('辅助译文（人工输入 / 独立 Provenance）',area));
        wrap.append(button('保存辅助译文（不作为 Gold）',async()=>{
          const text=area.value.trim();
          if(!text){state.notice='请先填写辅助译文';draw();return;}
          const x=selected();
          const saved=await perform(()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/translations',{
            method:'POST',body:{unit_id:u.unit_id,translation_zh:text,
              provenance_ref:'SYN-HUMAN-UI-CURATOR',
              expected_unit_text_sha256:u.unit_text_sha256}
          }),'辅助译文作为独立、不可变的非权威层保存');
          if(saved){state.translations.set(u.unit_id,saved.translation);draw();}
        },'outline'));
        right.append(wrap);
      }
      const actions=el('div',null,'p2-review-ops');
      if(canReview()&&!state.reviewed.has(u.unit_id)){
        actions.append(button('核查通过 · 冻结此 Unit',()=>submitReview(u,'ACCEPT'),'primary'));
        actions.append(button('标记问题 · 阻断封存',()=>submitReview(u,'REJECT'),'outline'));
      }else right.append(chip('当前会话已记录此单元审查','teal'));
      right.append(actions);
    }else{
      right.append(button('检查封存条件（演示阻断）',()=>{state.notice='封存失败：未提供真实版权/原始文件 SHA，且 PDF 坐标、表格与人工 QA 尚未合格。';draw()},'primary'));
    }
    grid.append(right);root.append(grid);
    root.append(metaP('转换与 QA 不自动生成科研 Gold；真实专家授权必须经 P3 独立 IAM 和 Exposure-Safe Workflow Controller。'));
  }
  function qaUnits(){
    const source=canReview()?state.document?.document?.units:null;
    return Array.isArray(source)&&source.length?source:demos;
  }
  async function submitReview(unit,decision){
    const x=selected();if(!canReview()||!x.live||!state.document||state.reviewPending||state.reviewed.has(unit.unit_id))return;
    // Remove the previous operation's toast *before* the asynchronous request.
    // Otherwise a browser/client can mistake a stale success toast for this
    // unit's successful durable write and submit the next unit too early.
    state.reviewPending=true;
    state.notice='正在持久化此 Unit 的独立 QA 记录…';
    draw();
    try{
      const text=unit.text;
      const bytes=new TextEncoder().encode(text);
      const digest=await crypto.subtle.digest('SHA-256',bytes);
      const quoteSha=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');
      const result=await perform(()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/qa',{method:'POST',body:{
        unit_id:unit.unit_id,decision,start_utf16:0,end_utf16:unit.utf16_length,
        source_quote:text,source_quote_sha256:quoteSha,
        pdf_locator_status:unit.pdf_locator_status,findings:{ui:'HUMAN_QA_SYNTHETIC_ONLY'}}}),
        '独立 QA 记录已持久化，审查结果不可原位修改');
      // Only acknowledge a server-confirmed immutable review. Never use a
      // local Set as evidence of successful QA if the API rejects the write.
      if(result?.review?.unit_id===unit.unit_id)state.reviewed.add(unit.unit_id);
    }finally{state.reviewPending=false;draw();}
  }
  function versions(){
    root.append(heading('P2 / SOURCE VERSION CONTROL · 高保真交互原型 v1.0','科学资料处理台',
      '核对 SHA、冻结回执、引用历史和当前上游科学规范 · 只提供合成资料流程演示。'));
    const p=panel('来源版本与 Source Package','原始 Artifact SHA、Canonical Document SHA 和逐单元 QA 记录分别留痕。');
    const table=el('table',null,'p2-table p2-library-table');
    const head=el('tr');
    ['科学来源','来源类别','资格与处理状态','版本 / SHA','操作'].forEach(t=>head.append(el('th',t)));
    table.append(append(el('thead'),head));
    const tbody=el('tbody');
    for(const x of all()){
      const row=el('tr');row.className='p2-version-row';
      const label=append(el('td'),el('strong',x.title),el('div',x.id,'p2-id'));
      const status=stages[x.stage]||[x.stage,'muted'];
      const proof=append(el('td'),el('div',x.v,'p2-id'),
        el('small',(x.package||x.canonical||'NOT_YET_CONVERTED').slice(0,26)+'…'));
      const actions=el('td');
      if(x.live&&canSubmit()&&x.stage==='QA_PENDING'&&x.doc){
        actions.append(button('检查并冻结',()=>perform(()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/freeze',{
          method:'POST',body:{expected_document_sha256:x.doc}}),'已冻结合成资料包'),'small primary'));
      }
      actions.append(button('详情',()=>{state.selection=x.id+':'+x.v;state.drawer=true;draw()},'small'));
      row.append(label,el('td',types[x.type]||x.type),append(el('td'),chip(status[0],status[1])),proof,actions);
      tbody.append(row);
    }
    table.append(tbody);p.append(append(el('div',null,'p2-table-wrap'),table));root.append(p);
    const rules=panel('资料封存与任务引用的分界',
      '即使合成 Package 已经 QA 冻结，仍不会自动注册原 EA 来源或变更 Task、B2、B3 专家授权。');
    rules.append(alert('SOURCE_PACKAGE_FROZEN（合成）≠ REAL_SOURCE_QUALIFIED ≠ GOLD_QUALIFIED ≠ EXPERT_EXPOSURE_AUTHORIZED。'));
    root.append(rules);
  }
  function matrixPanel(){
    const right=panel('GOV-0.4-P0 · 15 项静态符合性矩阵','对照 Nutrition Foundation / SIS / SIS-MED / AI Nutri 的静态规范轴；页面判定不构成运行时 PASS。');
    const table=el('table',null,'p2-matrix-table');
    const head=el('tr');['索引','主题','当前配置','判定'].forEach(t=>head.append(el('th',t)));
    table.append(append(el('thead'),head));
    const body=el('tbody');
    for(const [idx,topic,config,verdict] of governanceMatrix){
      const tr=el('tr');const v=governanceVerdict[verdict]||[verdict,'muted'];
      tr.append(el('td','C'+idx),el('td',topic),el('td',config),append(el('td'),chip(v[0],v[1])));
      body.append(tr);
    }
    table.append(body);right.append(append(el('div',null,'p2-table-wrap'),table));
    right.append(alert('SIS-MED R6 P0.4 原件缺失：临床条款级符合性 NOT ASSESSED；任何页面操作不得提升为 PASS。','warning'));
    return right;
  }
  function referencePanel(x){
    const card=panel('版本与引用','Raw / Canonical / Package 身份相互独立。');
    const facts=el('dl',null,'p2-facts');
    for(const [k,v] of [
      ['Raw Artifact',x?.raw||'—'],['Canonical Doc',x?.canonical||'—'],
      ['SourcePackage',x?.package||'未冻结'],
      ['关联 Project',x?.project||state.scope.project||'未绑定'],
      ['关联 Batch',x?.batch||state.scope.batch||'—']
    ])append(facts,el('dt',k),el('dd',String(v)));
    card.append(facts);
    if(!x?.package)card.append(chip('未冻结','amber'));
    const cites=panel('引用记录','模拟用途引用；不签发专家授权。');
    const table=el('table',null,'p2-table');
    const head=el('tr');['引用用途','项目 / 批次','权限状态'].forEach(t=>head.append(el('th',t)));
    table.append(append(el('thead'),head));
    const body=el('tbody'),row=el('tr');
    row.append(el('td','合成来源准备'),el('td',scopeText(x||{})),
      append(el('td'),chip('仅合成','blue'),chip('NO_GRANT','red')));
    body.append(row);table.append(body);cites.append(append(el('div',null,'p2-table-wrap'),table));
    cites.append(button('记录项目引用（模拟）',()=>{
      state.notice='已记录浏览器内的合成 Project/Batch 使用意图；不代表专家授权。';draw();
    },'outline'));
    return append(el('div'),card,cites);
  }
  function auditEventsPanel(){
    const card=panel('审计事件（模拟时间线）','事件类型与角色为合成演示；正式链由 Auditor 核验。');
    const tools=el('div',null,'p2-toolbar');
    tools.append(select([['','全部事件'],['SOURCE_REGISTERED','SOURCE_REGISTERED'],
      ['RIGHTS_RECORDED','RIGHTS_RECORDED'],['CONVERSION_FROZEN','CONVERSION_FROZEN'],
      ['UNIT_QA_RECORDED','UNIT_QA_RECORDED'],['SOURCE_PACKAGE_FROZEN','SOURCE_PACKAGE_FROZEN']],'','outline'),
      button('核验审计链',async()=>{
        if(!canRights()){state.notice='只有独立 Auditor 会话可以核验 P2 原始审计链。';draw();return;}
        try{state.auditResult=await api('/v1/p2/audit');state.notice=state.auditResult.valid?
          '审计链通过，仅为合成来源工程验证。':'审计链异常：禁止后续封存。';draw();}
        catch(e){state.notice='审计读取被拒绝：'+e.message;draw();}
      },'outline'));
    card.append(tools);
    const table=el('table',null,'p2-table');
    const head=el('tr');['时间','事件类型','说明','执行角色','版本'].forEach(t=>head.append(el('th',t)));
    table.append(append(el('thead'),head));
    const body=el('tbody');
    for(const [date,type,desc,actor,rev] of [
      ['2026-10-10 09:20','SOURCE_REGISTERED','登记合成来源与标识信息','Producer','r1'],
      ['2026-10-10 09:45','RIGHTS_RECORDED','合成用途范围审核记录','Auditor','r1'],
      ['2026-10-11 11:24','CONVERSION_FROZEN','结构化 Unit 与解析追溯冻结','Producer','r2'],
      ['2026-10-12 15:05','UNIT_QA_RECORDED','模拟 Unit QA 留痕','Curator','r3']
    ]){
      const tr=el('tr');
      tr.append(el('td',date),el('td',type),el('td',desc),el('td',actor),el('td',rev));
      body.append(tr);
    }
    table.append(body);card.append(append(el('div',null,'p2-table-wrap'),table));
    if(state.auditResult)card.append(alert('审计核验：'+(state.auditResult.valid?'VALID':'INVALID')+
      ' · 事件 '+state.auditResult.events_checked+' · 不代表真实科学许可。',
      state.auditResult.valid?'note':'warning'));
    else card.append(alert('仅 Auditor 能读取完整 P2 审计核验结果；Manager 和 Producer 无权通过本页提升权限。','info'));
    return card;
  }
  function audit(){
    root.append(heading('P2 / SCIENTIFIC SOURCE WORKSPACE · 高保真交互原型 v1.0','科学资料处理台',
      '核对 SHA、冻结回执、引用历史和当前上游科学规范；独立 Auditor 核验全局审计链，不受 Project / Batch 筛选影响。',
      [button('返回工作队列',()=>view('library'),'primary'),
       button('记录项目 / 批次引用',()=>{state.drawer=true;draw()},'outline'),
       button('导出模拟审计',()=>{state.notice='已导出浏览器内模拟审计摘要（不代表正式审计凭证）。';draw()},'outline')]));
    const x=selected();
    const identity=el('section',null,'p2-card p2-audit-identity');
    append(identity,append(el('div',null,'grow'),
      el('span','选定来源','p2-dim'),el('strong',x?x.title:'未选择来源'),
      el('span',x?(x.id+' / '+x.v):'—','p2-id')),chip('SYNTHETIC ONLY','teal'),
      button('返回列表',()=>view('library'),'small outline'));
    root.append(identity);
    const tabnav=el('nav',null,'p2-version-tabs');tabnav.setAttribute('aria-label','版本与审计子视图');
    for(const [id,label] of [
      ['lineage','版本谱系与审计'],['compare','版本差异对比'],
      ['references','引用记录'],['governance','规范依赖与符合性']
    ]){
      const b=button(label,()=>{state.versionTab=id;draw()},'p2-version-tab'+(state.versionTab===id?' active':''));
      b.setAttribute('aria-current',state.versionTab===id?'true':'false');
      tabnav.append(b);
    }
    root.append(append(el('section',null,'p2-card p2-version-tabcard'),tabnav));
    const grid=el('div',null,'p2-versiongrid');
    if(state.versionTab==='governance'){
      const side=panel('规范依赖与适用范围','临床营养当前权威为 SIS-MED R6 P0.4；原件缺失时 NOT ASSESSED。');
      side.append(button('打开版本资料库',()=>view('versions'),'outline'));
      grid.append(matrixPanel(),side);
    }else if(state.versionTab==='references'){
      grid.append(referencePanel(x),matrixPanel());
    }else if(state.versionTab==='compare'){
      const left=panel('版本差异 · 模拟变更','Source revision、Canonical Document 与 SourcePackage 身份不同。');
      left.append(append(el('div',null,'p2-two'),
        append(el('div',null,'p2-card'),el('strong','r2 / Canonical IR'),
          el('p','UnitIDs 已固定，Parser lineage 已登记；未声明经过全部人工 QA。','p2-dim')),
        append(el('div',null,'p2-card'),el('strong','r3 / QA Sidecar'),
          el('p','独立 QA 与问题记录；拒绝项要求新版本，不覆盖原始 Unit。','p2-dim'))),
        alert('Source revision、Canonical Document revision 和 SourcePackage revision 的身份不同，必须单独溯源。','warning'));
      grid.append(left,referencePanel(x));
    }else{
      const left=el('div',null,'p2-audit-left');
      const lineageCard=panel('版本谱系','原件 → 解析 → QA → 资料包；演示对象不可作为真实科研证据。');
      const lineage=el('div',null,'p2-lineage');
      for(const [title,sub,code] of [
        ['原件登记','Raw Artifact','SOURCE_REGISTERED'],
        ['解析与结构化','Document SHA','CONVERSION_FROZEN'],
        ['Unit QA','Curator 留痕','UNIT_QA_RECORDED'],
        ['资料包','Package SHA','SOURCE_PACKAGE_FROZEN']
      ]){
        const node=el('div',null,'p2-line-node');
        append(node,el('div',null,'p2-node-icon'),el('strong',title,'p2-node-title'),
          el('small',sub),el('span',code,'p2-id'));
        lineage.append(node);
      }
      lineageCard.append(lineage,alert('各阶段对象仅供合成演示，不可作为真实科研证据。','warning'));
      left.append(lineageCard,auditEventsPanel());
      const right=referencePanel(x);
      const standards=panel('规范依赖与适用范围','GOV-0.4 静态轴；详见「规范依赖与符合性」。');
      standards.append(button('15 项符合性矩阵',()=>{state.versionTab='governance';draw()},'outline'));
      right.append(standards);
      grid.append(left,right);
    }
    root.append(grid);
  }
  function detailDrawer(){
    const x=selected();const layer=el('div',null,'p2-overlay');layer.addEventListener('click',e=>{if(e.target===layer){state.drawer=false;draw()}});
    const card=el('section',null,'p2-drawer');card.setAttribute('role','dialog');card.setAttribute('aria-label','科学来源版本详情');
    const top=el('div',null,'p2-drawer-top');
    append(top,append(el('div'),el('span','SOURCE WORKSPACE / '+x.id,'p2-eyebrow'),el('h2','单篇来源工作区')),button('关闭',()=>{state.drawer=false;draw()},'outline'));
    card.append(top,chip(x.live?'受控合成登记':'演示数据 · 非已登记来源',x.live?'teal':'red'),el('h3',x.title));
    const guide=nextStep(x),flow=el('section',null,'p2-detail-workflow');
    append(flow,el('span','当前阶段 · '+(stages[x.stage]?.[0]||x.stage),'p2-detail-eyebrow'),
      el('strong',guide.title),el('p',guide.detail));
    const steps=el('div',null,'p2-detail-path');
    for(const [name,passed]of [
      ['来源 / 用途',x.live&&x.stage!=='RIGHTS_HOLD'],
      ['结构化',x.live&&['QA_PENDING','QA_HOLD','PACKAGE_FROZEN'].includes(x.stage)],
      ['完整 QA',x.live&&x.stage==='PACKAGE_FROZEN'],
      ['资料包',x.live&&x.stage==='PACKAGE_FROZEN']
    ])steps.append(chip((passed?'✓ ':'○ ')+name,passed?'teal':'muted'));
    flow.append(steps);card.append(flow);
    const guideCards=el('section',null,'p2-source-stage-cards');
    const stageChecks=[
      ['01','来源登记 / 用途',x.live&&x.stage!=='RIGHTS_HOLD','查身份、更正撤稿及独立用途记录'],
      ['02','结构化文档',x.live&&!!x.doc,'Document IR、Parser lineage 与稳定 Unit ID'],
      ['03','人工证据 QA',x.live&&x.stage==='PACKAGE_FROZEN','原文、表格、数值与证据锚点逐单元核验'],
      ['04','不可变资料包',x.live&&x.stage==='PACKAGE_FROZEN','冻结之后仍需独立项目引用及专家授权']
    ];
    for(const [num,label,passed,help] of stageChecks){
      const item=el('div',null,'p2-stage-card'+(passed?' passed':''));
      append(item,el('span',num,'p2-stage-num'),append(el('div'),
        el('strong',label),el('small',help)),chip(passed?'已具备合成记录':'待验证',passed?'teal':'muted'));
      guideCards.append(item);
    }
    card.append(guideCards);
    const jump=el('nav',null,'p2-source-jump');jump.setAttribute('aria-label','单篇来源工作区操作导航');
    jump.append(button('来源登记',()=>{state.drawer=false;view('intake')},'outline'),
      button('结构化处理',()=>{state.drawer=false;view('convert')},'outline'),
      button('人工 QA',()=>{
        state.drawer=false;state.tab='qa';draw();
        if(canReview()&&x.live)loadSelectedDocument();
      },'outline'),
      button('版本与审计',()=>{state.drawer=false;view('audit')},'outline'));
    card.append(jump);
    card.append(el('h3','来源凭据与版本信息','p2-facts-heading'));
    const table=el('dl',null,'p2-facts');
    for(const [name,value]of [
      ['Source / Revision',x.id+' / '+x.v],['文献类型',types[x.type]||x.type],['文件类型',x.kind],
      ['来源资格',x.rights],['工作流状态',stages[x.stage]?.[0]||x.stage],
      ['Raw Artifact SHA-256',x.raw],['Canonical Document SHA-256',x.canonical],
      ['已审单元 / 总单元',(x.reviewed||0)+' / '+x.units],
      ['Source Package SHA-256',x.package||'NOT_FROZEN'],
      ['专家权限','DENIED · NO_GRANT']
    ])append(table,el('dt',name),el('dd',String(value||'—')));
    card.append(table);
    const actions=el('div',null,'p2-drawer-actions');
    if(x.live&&canRights()&&x.stage==='RIGHTS_HOLD'){
      actions.append(button('记录独立合成使用权',()=>perform(()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/rights',{
        method:'POST',body:{decision:'APPROVE_SYNTHETIC',
        uses:['INTERNAL_SOURCE_REVIEW','MACHINE_PROCESSING','RETAIN_ORIGINAL'],
        evidence_ref:'SYN-UI-ATTESTED-ONLY'}}),'合成用途审查记录已签发'),'primary'));
    }
    if(x.live&&canSubmit()&&x.stage==='RIGHTS_ACCEPTED'){
      actions.append(button('前往转换作业',()=>{state.drawer=false;view('convert')},'primary'));
    }
    if(x.live&&canReview()&&['QA_PENDING','QA_HOLD'].includes(x.stage)){
      actions.append(button('打开独立 QA 阅读器',()=>{state.drawer=false;state.tab='qa';loadSelectedDocument()},'primary'));
    }
    if(x.live&&canSubmit()&&x.stage==='PACKAGE_FROZEN'&&state.scope.project&&state.scope.batch){
      actions.append(button('绑定当前项目 / 批次（不授予专家）',()=>perform(
        ()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/scope',{method:'POST',
          body:{project_id:state.scope.project,batch_id:state.scope.batch}}),
        '已建立仅限来源准备的 Project/Batch 引用'),'primary'));
    }
    if(x.live&&!canReview()&&['RIGHTS_HOLD','QA_PENDING','QA_HOLD'].includes(x.stage)){
      actions.append(button('打开独立审核登录 ↗',()=>window.open('/source-qa','_blank','noopener'),'outline'));
    }
    actions.append(button('查看版本与审计',()=>{state.drawer=false;view('audit')},'outline'));
    if(x.live&&canSubmit()&&x.stage==='QA_PENDING'&&x.doc){
      actions.append(button('前往版本资料库冻结',()=>{state.drawer=false;view('versions')},'outline'));
    }
    card.append(actions,alert('Manager 只允许读取来源元数据；P2 与原 B1/EA 的数据不会在此页面自动合并。'));
    layer.append(card);return layer;
  }
  function sourceWizard(){
    const layer=el('div',null,'p2-overlay p2-wizard-layer');layer.addEventListener('click',e=>{if(e.target===layer){state.wizard=false;draw()}});
    const modal=el('section',null,'p2-modal');modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-label','来源登记 · 受控合成准备');
    const top=el('div',null,'p2-modal-head');
    top.append(el('h2','登记科学来源 · 四步向导'),button('关闭',()=>{state.wizard=false;draw()},'outline'));modal.append(top);
    const steps=el('div',null,'p2-steps');
    ['01 来源身份','02 原始内容','03 许可与用途','04 范围确认'].forEach((t,i)=>steps.append(chip(t,i===state.step?'teal':'muted')));
    modal.append(steps);
    const d=ensureDraft();
    if(!d.title)d.title='Synthetic source for internal QA testing';
    if(!d.identifier)d.identifier='SYN-DEMO-REFERENCE-001';
    const form=el('form',null,'p2-wizard-form');form.addEventListener('submit',ev=>ev.preventDefault());
    form.append(alert('P2 合成准备区：不要上传真实 PDF、病人资料或未经许可的论文全文。真实身份与版权必须通过 P2.0 单独审批。','warning'));
    function addText(name,key,limit=200){const n=textInput(d[key]||'',limit);n.addEventListener('input',()=>{d[key]=n.value});form.append(field(name,n));return n;}
    function addSelect(name,key,choices){form.append(field(name,select(choices,d[key],v=>{d[key]=v})))}
    if(state.step===0){
      const options=el('div',null,'p2-kinds');
      for(const [fmt,name]of [['MARKDOWN','Markdown'],['JATS_XML','JATS/XML'],['HTML','HTML'],['PDF_HANDOFF','PDF / MinerU handoff']])
        options.append(button(name,()=>{d.raw_format=fmt;draw()},'p2-kind'+(d.raw_format===fmt?' picked':'')));
      form.append(options);
      addText('资料名称', 'title');addText('Source ID', 'source_id',40);addText('Revision','revision_id',32);
      addSelect('科学来源 Profile / 类型','source_type',Object.entries(types));
      addSelect('文献标识符类型','identifier_kind',[['SYNTHETIC_ID','虚构来源 ID'],['DEMO_DOI','演示 DOI'],['DEMO_PMID','演示 PMID']]);
      addText('标识符','identifier',120);
    }else if(state.step===1){
      form.append(alert('下面保存的文本字节将独立计算 Raw Artifact SHA。PDF_HANDOFF 只接收外部处理结果，暂不运行 MinerU。','info'));
      const raw=el('textarea');raw.rows=9;raw.maxLength=200000;raw.value=d.raw_content;
      raw.addEventListener('input',()=>{d.raw_content=raw.value});form.append(field('虚构来源原文（仅合成测试）',raw));
      addText('来源可用时间（ISO 时区）','available_at',50);addText('获取时间（ISO 时区）','fetched_at',50);
    }else if(state.step===2){
      form.append(panel('使用权核查','来源登记 ≠ 版权批准。独立 Auditor 必须记录精确用途范围和证据引用；真实来源依然 NO-GO。'));
      form.append(chip('RIGHTS_HOLD → SYNTHETIC_RIGHTS_ATTESTED','amber'));
    }else {
      form.append(alert('Project/Batch 只是合成来源的拟使用范围。仅 Package 冻结后才能单独建立引用；不能直接发布给专家。','info'));
      form.append(metaP('Project: '+(state.scope.project||'未选')+'　Batch: '+(state.scope.batch||'未选')));
    }
    const actions=el('div',null,'p2-modal-actions');
    actions.append(button('上一步',()=>{state.step=Math.max(0,state.step-1);draw()},'outline'));
    actions.append(button(state.step===3?'提交合成来源登记':'下一步',async()=>{
      if(state.step<3){state.step++;draw();return;}
      if(!canSubmit()){state.notice='只有 Producer 可以登记合成来源。';state.wizard=false;draw();return;}
      const payload={...d};delete payload.year;delete payload.project;delete payload.batch;
      const saved=await perform(()=>api('/v1/p2/sources',{method:'POST',body:payload}),'来源已登记并进入独立用途权利待核查状态');
      if(!saved)return;
      state.wizard=false;state.tab='library';state.selection=d.source_id+':'+d.revision_id;state.draft=null;state.intakePreset=null;state.status='';state.search='';draw();
    },'primary'));
    form.append(actions);modal.append(form);layer.append(modal);return layer;
  }
  async function perform(action,success){
    try{const result=await action();state.notice=success+'；科研资格和 Gold 仍为 NO-GO。';
      if(state.wizard)state.wizard=false;
      await reload();return result;
    }catch(err){state.notice='操作被拒绝：'+err.message;draw();}
  }
  function draw(){
    if(!root?.isConnected)return;
    // Preserve the user's horizontal navigation position when the SPA swaps
    // its content subtree; otherwise a tapped off-screen tab jumps away.
    const secondaryScroll=root.querySelector('.p2-tabs')?.scrollLeft||0;
    const readerScroll={};
    root.querySelectorAll('[data-p2-read-surface]').forEach(n=>{readerScroll[n.dataset.p2ReadSurface]=n.scrollTop});
    const outer=root.parentElement,component=frame();outer.replaceChild(component,root);root=component;
    const secondary=root.querySelector('.p2-tabs');
    if(secondary)secondary.scrollLeft=secondaryScroll;
    if(state.tab==='library')library();
    else if(state.tab==='intake')renderIntake();
    else if(state.tab==='convert')conversion();
    else if(state.tab==='qa')qa();
    else if(state.tab==='audit')audit();
    else versions();
    root.querySelectorAll('[data-p2-read-surface]').forEach(n=>{
      if(Object.prototype.hasOwnProperty.call(readerScroll,n.dataset.p2ReadSurface))
        n.scrollTop=readerScroll[n.dataset.p2ReadSurface];
    });
    if(state.drawer)root.append(detailDrawer());
    if(state.wizard)root.append(sourceWizard());
  }
  function render(options={}){
    state.role=options.role||state.role;state.session=options.session||principal();
    state.scope={project:options.scope?.project||state.scope.project||'',
                 batch:options.scope?.batch||state.scope.batch||''};
    state.projects=options.projects||state.projects;
    state.batches=options.batchMap||state.batches;
    const outer=el('section',null,'p2-studio-mount');root=frame();outer.append(root);
    queueMicrotask(()=>{if(root?.isConnected){draw();reload()}});
    return outer;
  }
  function reset(){
    state.tab='library';state.selection='P2-DEMO-RCT-001';state.search='';state.status='';
    state.kindFilter='';state.sourceFilter='all';state.unitIndex=0;state.highlighted=false;state.display='bilingual';state.drawer=false;
    state.wizard=false;state.draft=null;state.intakePreset=null;state.auditResult=null;state.document=null;state.original=null;state.translations=new Map();state.notice='';
    state.reviewed=new Set();state.liveSources=[];state.overview=null;state.scopeExpanded=false;state.versionTab='lineage';state.step=0;
  }
  window.p2SourceStudio={render,reload,reset,selectTab:view};
  document.addEventListener('DOMContentLoaded',()=>{
    document.getElementById('logoutButton')?.addEventListener('click',reset);
    document.addEventListener('keydown',event=>{
      if(event.key!=='Escape'||!root?.isConnected)return;
      if(state.wizard||state.drawer){
        event.preventDefault();
        if(state.wizard)state.wizard=false;else state.drawer=false;
        draw();
        root?.querySelector('.p2-tabs [data-p2-tab="'+state.tab+'"]')?.focus({preventScroll:true});
      }
    });
    // The only P2 secondary navigation is now the in-content .p2-tabs.
    // Do not reinstall a competing sidebar handler.
  });
})();
