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
  const tabs={library:'资料总览',intake:'来源登记',convert:'转换作业',qa:'人工 QA',versions:'来源与版本'};
  const types={RANDOMIZED_TRIAL:'随机对照试验',OBSERVATIONAL_STUDY:'观察性研究',
    SYSTEMATIC_REVIEW_META:'系统综述',GUIDELINE:'指南 / 共识',CONSENSUS:'专家共识',
    NARRATIVE_REVIEW:'叙述性综述',CORRECTION_RETRACTION:'更正 / 撤稿'};
  let state={tab:'library',selection:'P2-DEMO-RCT-001',search:'',status:'',kindFilter:'',unitIndex:0,
    display:'bilingual',drawer:false,wizard:false,step:0,notice:'',liveSources:[],overview:null,
    document:null,original:null,translations:new Map(),reviewed:new Set(),draft:null,scope:{project:'',batch:''},projects:[],
    batches:new Map(),role:'manager',session:null,sourceCount:0,loading:false};
  let root=null;
  const selected=()=>all().find(x=>x.id+':'+x.v===state.selection)||all().find(x=>x.id===state.selection)||all()[0];
  const all=()=>state.liveSources.map(x=>({
    id:x.source_id,v:x.revision_id,title:x.title,type:x.source_type,kind:x.raw_format,
    stage:x.status,rights:x.rights_status,project:'',batch:'',units:x.unit_count||0,
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
  function view(tab){state.tab=tab;state.notice='';state.drawer=false;draw();}
  function metaP(text){return el('p',text,'p2-dim')}
  function panel(title,description,css=''){const n=el('section',null,'p2-card '+css);
    if(title)n.append(el('h2',title));if(description)n.append(metaP(description));return n;}
  function nav(){
    const n=el('nav',null,'p2-tabs');n.setAttribute('aria-label','科学资料库二级导航');
    for(const [key,name]of Object.entries(tabs)){
      const b=button(name,()=>view(key),'p2-tab '+(state.tab===key?'active':''));b.setAttribute('aria-current',state.tab===key?'page':'false');n.append(b);
    }return n;
  }
  function heading(eyebrow,title,description,actions=[]){
    const n=el('div',null,'p2-heading'),left=el('div');
    append(left,el('p',eyebrow,'p2-eyebrow'),el('h1',title),el('p',description,'p2-subtitle'));
    append(n,left,append(el('div',null,'p2-actions'),actions));return n;
  }
  function context(){
    const n=el('div',null,'p2-context');
    n.append(el('span','使用范围 · Project / Batch','p2-label'));
    const proj=select([['','全部项目']].concat(state.projects.map(x=>[x.project_id,x.name])),
      state.scope.project,v=>{state.scope.project=v;state.scope.batch='';draw();reload()});
    const batches=state.scope.project?(state.batches.get(state.scope.project)||[]):[];
    const bat=select([['','全部批次']].concat(batches.map(x=>[x.batch_id,x.label])),
      state.scope.batch,v=>{state.scope.batch=v;reload()});
    n.append(proj,bat,chip('精确版本引用，不复制原始来源'));return n;
  }
  function frame(){
    const n=el('div',null,'p2-studio');
    const breadcrumb=el('div','工作空间  ›  科学资料库  ›  '+(tabs[state.tab]||'资料总览'),'p2-breadcrumb');
    n.append(breadcrumb,alert('架构安全边界：当前仅使用合成测试来源与受控结构化记录。真实 PDF、外部来源资格、Gold、正式专家授权及真实部署仍为 NO-GO。','info'));
    n.append(context(),nav());
    for(const b of document.querySelectorAll("#p2NavGroup [data-p2-tab]"))
      b.setAttribute("aria-current",b.dataset.p2Tab===state.tab?"page":"false");
    if(state.notice)n.append(alert(state.notice,'note'));
    return n;
  }
  function statBox(value,name){return append(el('div',null,'p2-stat'),el('strong',value),el('span',name));}
  function overviewCards(){
    const summary=state.overview||{};
    return append(el('div',null,'p2-stats'),
      statBox(String((summary.total||0)+fixtures.length).padStart(2,'0'),'演示与已登记来源'),
      statBox(String(summary.rights_hold||0).padStart(2,'0'),'独立权限待确认'),
      statBox(String(summary.qa_pending||0).padStart(2,'0'),'结构化与人工 QA'),
      statBox(String(summary.packages_frozen||0).padStart(2,'0'),'已冻结合成来源包'));
  }
  function pipeline(){
    const grid=el('div',null,'p2-pipeline');
    const left=panel('资料准备流水线','先准备、再验证、最后形成待任务引用的资料包。');
    const phase=el('div',null,'p2-phases');
    ['01 来源登记','02 资格审查','03 结构转换','04 人工 QA','05 资料封存'].forEach((name,i)=>{
      if(i)phase.append(el('span','›','p2-phase-arrow'));
      phase.append(el('span',name,'p2-phase '+(i===0?'on':'')));
    });left.append(phase);
    const actions=el('div',null,'p2-choices');
    for(const [symbol,title,sub,target]of [
      ['＋','登记新文献','DOI / PMID、PDF、JATS、HTML、Markdown','intake'],
      ['⇄','查看转换作业','解析器 lineage、结构识别与错误','convert'],
      ['⌗','检查 Evidence Anchors','原文对照、UTF-16 与定位质量','qa']
    ]){
      actions.append(button('',()=>view(target),'p2-choice'));
      const b=actions.lastChild;b.append(el('span',symbol,'p2-choice-icon'),el('strong',title),el('small',sub));
    }
    left.append(actions);grid.append(left);
    const right=panel('独立的科学准入闸门','QA 合格不代表获得真实科研及专家权限。','p2-gate');
    for(const [i,title,desc]of [['✓','Source Qualification','版本身份、使用权与修订状态'],['⌗','Human Document QA','文本、表格、数值与 Anchor 校验'],['▣','Immutable Source Package','精确版本、不可变记录、Canonical SHA']]){
      const line=el('div',null,'p2-gate-line');append(line,el('span',i,'p2-gate-icon'),append(el('div'),el('strong',title),el('small',desc)));right.append(line);
    }
    right.append(alert('来源资格封存 ≠ Task 已发布 ≠ 专家访问授权。P3 身份与暴露授权为 NO-GO。'));grid.append(right);
    return grid;
  }
  function statFilter(){
    const bar=el('div',null,'p2-status-tabs');
    for(const [id,label] of [['','全部资料'],['RIGHTS_HOLD','来源待核'],['CONVERSION_REVIEW','转换中'],['QA_PENDING','人工 QA'],['PACKAGE_FROZEN','已封存'],['VERSION_REVIEW','版本待核']]){
      const b=button(label,()=>{state.status=id;draw()},'p2-filter-chip'+(state.status===id?' active':''));bar.append(b);
    }return bar;
  }
  function sourceList(){
    const wrap=panel('科学来源列表','以版本 SHA 和列表优先模式展示；项目/批次是引用范围，来源版本由全局权威管理。');
    const right=button('查看来源版本谱系 ↗',()=>view('versions'),'outline');
    wrap.insertBefore(right,wrap.children[1]||null);
    wrap.append(statFilter());
    const searchbar=el('div',null,'p2-toolbar');
    const search=textInput(state.search,160);search.placeholder='搜索标题、DOI、PMID 或 Source ID';
    search.setAttribute('aria-label','搜索科学来源');search.addEventListener('input',()=>{state.search=search.value;renderTable()});
    const kind=select([['','全部文献类型']].concat(Object.entries(types)),state.kindFilter,
      v=>{state.kindFilter=v;renderTable()});
    searchbar.append(search,kind,button('刷新真实登记状态',()=>reload(),'outline'));
    wrap.append(searchbar);
    const scroll=el('div',null,'p2-table-wrap'),table=el('table',null,'p2-table');table.id='p2TableTarget';
    const th=el('thead'),head=el('tr');['来源 / 版本','文献类别','来源资格','结构化与 QA','Project / Batch','操作'].forEach(t=>head.append(el('th',t)));
    th.append(head);table.append(th,el('tbody'));scroll.append(table);wrap.append(scroll);
    wrap.append(metaP('演示记录与真实合成阶段记录已分开标识；不显示受控原始正文，也不提供专家 Candidate 访问。'));
    renderTableInto(table);return wrap;
  }
  function renderTableInto(table){
    const body=table.querySelector('tbody');body.replaceChildren();
    const src=all().filter(x=>{
      const f=state.search.trim().toLowerCase();
      return (!f||[x.title,x.id,x.type].join(' ').toLowerCase().includes(f))&&
        (!state.status||x.stage===state.status)&&(!state.kindFilter||x.type===state.kindFilter)&&
        (x.live||(!state.scope.project&&!state.scope.batch));
    });
    for(const x of src){
      const r=el('tr'),idcell=el('td'),title=el('strong',x.title),info=el('div',x.id+' · '+x.v,'p2-id');
      idcell.append(title,info,chip(x.live?'持久化合成记录':'演示条目','muted'));
      const status=stages[x.stage]||[x.stage,'muted'];
      const qa=el('td');qa.append(chip(status[0],status[1]),el('small',String(x.reviewed||0)+'/'+x.units+' anchors · '+x.risk));
      const rights=el('td');rights.append(chip(x.rights,'muted'));
      const action=el('td');action.append(button('查看详情 →',()=>{state.selection=x.id+':'+x.v;state.drawer=true;draw()},'small'));
      r.append(idcell,el('td',types[x.type]||x.type),rights,qa,
        el('td',x.live?(state.scope.project||'全局资料')+' / '+(state.scope.batch||'—'):(x.project||'未绑定')+' / '+(x.batch||'—')),action);
      body.append(r);
    }
    if(!src.length){const row=el('tr'),cell=el('td','当前筛选没有符合条件的来源版本。','p2-dim');cell.colSpan=6;row.append(cell);body.append(row);}
  }
  function renderTable(){const t=document.getElementById('p2TableTarget');if(t)renderTableInto(t)}
  function library(){
    root.append(heading('02 / SOURCE OPERATIONS','科学资料库',
      '真实科学资料的准备入口：先核对来源和权限，再进行结构转换、证据定位与人工验收。',
      [button('查看转换队列',()=>view('convert'),'outline'),button('＋ 登记科学来源',()=>{state.wizard=true;state.step=0;state.draft=null;draw()},'primary')]));
    root.append(overviewCards(),pipeline(),sourceList());
  }
  function renderIntake(){
    root.append(heading('P2-A / SOURCE INTAKE','来源登记',
      '分阶段填写来源身份与用途，所有写入都先进入独立合成待核查状态。',
      [button('＋ 新建来源登记',()=>{state.wizard=true;state.step=0;state.draft=null;draw()},'primary')]));
    const panel1=panel('来源登记队列','当前 P2 的合成来源登记是持久化操作，原稿、SHA 与审计存在独立数据库，绝不写入 EA。');
    const statuses=all().filter(x=>x.live);
    if(!statuses.length)panel1.append(alert('尚未有持久化合成来源。请先创建一个合成文献，不要输入真实患者资料或未经许可的全文。','info'));
    for(const x of statuses){const row=el('div',null,'p2-version');
      row.append(el('strong',x.id+' / '+x.v),chip(stages[x.stage]?.[0]||x.stage,stages[x.stage]?.[1]||'muted'),
        button('查看',()=>{state.selection=x.id+':'+x.v;state.drawer=true;draw()},'small'));panel1.append(row);}
    root.append(panel1);
    const help=panel('登记与版权审查的分工','Producer 负责建立来源待审核记录；Auditor 在独立会话记录合成使用权；Source Curator 核查结构化结果。');
    help.append(alert('真实 DOI、PDF、机器处理版权和公共传播资格不会通过一个勾选框自动获得授权。','warning'));
    help.append(button('打开独立审查入口',()=>window.open('/source-qa','_blank','noopener'),'outline'));
    root.append(help);
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
      row.append(el('td',x.title),el('td',x.kind),append(el('td'),chip(status[0],status[1])),
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
  function qa(){
    root.append(heading('P2-C/D / HUMAN SOURCE QA','结构化资料 QA 阅读器',
      '原文为权威，结构化正文负责阅读与定位；译文仅为辅助，不参与原始证据 SHA。',
      [button('下一个待检查单元',()=>{const units=qaUnits();state.unitIndex=(state.unitIndex+1)%units.length;draw()},'outline'),
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
    const grid=el('div',null,'p2-qa-grid');
    const original=panel('原始资料对照','Source Artifact · Page Hint。');
    const sheet=el('div',null,'p2-pdf-sheet');
    sheet.append(el('small',actual?'ORIGINAL ARTIFACT · VERIFIED SHA':'SYNTHETIC DOCUMENT EXCERPT'),el('h3','ABSTRACT / METHODS'));
    const units=qaUnits();
    if(actual){
      const originalText=el('pre',state.original.raw_content,'p2-original-text');
      sheet.append(originalText);
    }else{
      for(const u of units.slice(0,3))sheet.append(el('p',u.text));
    }
    sheet.append(el('strong',actual?'RAW SOURCE SHA VERIFIED · SYNTHETIC':'DEMO ONLY'));
    original.append(sheet,metaP('原始 PDF 未加载；页面坐标未获独立验证。'));
    grid.append(original);
    const middle=panel('Structured Document IR','稳定 Unit ID · 段落级对照 · 原文 SHA 独立');
    for(const [i,u]of units.entries()){
      const item=el('button',null,'p2-unit'+(i===state.unitIndex?' selected':''));
      item.type='button';item.setAttribute('aria-pressed',i===state.unitIndex?'true':'false');
      item.addEventListener('click',()=>{state.unitIndex=i;draw()});
      item.append(el('span',u.unit_id+' · '+u.kind,'p2-unit-meta'));
      if(state.display!=='translation'){
        const paragraph=el('div',null,'p2-reader-paragraph');
        const text=u.text||'';const a=text.length>40?Math.min(18,text.length-1):0;
        if(a){paragraph.append(document.createTextNode(text.slice(0,a)),el('mark',text.slice(a,Math.min(a+25,text.length))),document.createTextNode(text.slice(Math.min(a+25,text.length))));}
        else paragraph.append(document.createTextNode(text));
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
    const u=units[state.unitIndex]||units[0];
    const span=append(el('dl',null,'p2-facts'),
      el('dt','Evidence Unit'),el('dd',u.unit_id+' · '+u.kind),
      el('dt','原文 Quote'),el('dd',u.text),
      el('dt','UTF-16 Span'),el('dd','0 → '+String(u.utf16_length||u.text.length)),
      el('dt','Canonical SHA'),el('dd',actual?doc.document_sha256:'NOT_COMPUTED_DEMO'),
      el('dt','PDF Locator'),el('dd',u.pdf_locator_status||'UNRESOLVED'));
    right.append(chip(actual?'ORIGINAL_SPAN_CHECK_PENDING':'DEMO_TEXT_ONLY','blue'),span);
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
    const x=selected();if(!canReview()||!x.live||!state.document)return;
    const text=unit.text;
    const bytes=new TextEncoder().encode(text);
    const digest=await crypto.subtle.digest('SHA-256',bytes);
    const quoteSha=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');
    await perform(()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/qa',{method:'POST',body:{
      unit_id:unit.unit_id,decision,start_utf16:0,end_utf16:unit.utf16_length,
      source_quote:text,source_quote_sha256:quoteSha,
      pdf_locator_status:unit.pdf_locator_status,findings:{ui:'HUMAN_QA_SYNTHETIC_ONLY'}}}),
      '独立 QA 记录已持久化，审查结果不可原位修改');
    state.reviewed.add(unit.unit_id);
  }
  function versions(){
    root.append(heading('P2-D/E / SOURCE VERSION CONTROL','来源版本与封存记录',
      '全局 SourceVersion 保留独立权威；项目与批次只能引用经过合成质量审核的精确包。'));
    const p=panel('Source Package 与 lineage','原始字节 SHA、Canonical Document SHA、人工 QA 记录摘要分别计算。');
    for(const x of all()){
      const row=el('div',null,'p2-version');
      row.append(el('strong',x.id+' / '+x.v),chip(stages[x.stage]?.[0]||x.stage,
        stages[x.stage]?.[1]||'muted'),el('span',(x.package||x.canonical||'未转换').slice(0,28)+'…','p2-id'));
      if(x.live&&canSubmit()&&x.stage==='QA_PENDING'&&x.doc){
        row.append(button('检查并冻结',()=>perform(()=>api('/v1/p2/sources/'+x.id+'/'+x.v+'/freeze',{
          method:'POST',body:{expected_document_sha256:x.doc}}),'已冻结合成资料包'),'small primary'));
      }
      row.append(button('详情',()=>{state.selection=x.id+':'+x.v;state.drawer=true;draw()},'small'));
      p.append(row);
    }root.append(p);
    const rules=panel('资料封存与任务引用的分界','即使合成 Package QA 完整并被冻结，仍不会向原 EA 注册真实资料，不会改变 TPA Task、B2 或 B3 Expert Grants。');
    rules.append(alert('SOURCE_PACKAGE_FROZEN（合成）≠ REAL_SOURCE_QUALIFIED ≠ GOLD_QUALIFIED ≠ EXPERT_EXPOSURE_AUTHORIZED。'));
    root.append(rules);
  }
  function detailDrawer(){
    const x=selected();const layer=el('div',null,'p2-overlay');layer.addEventListener('click',e=>{if(e.target===layer){state.drawer=false;draw()}});
    const card=el('section',null,'p2-drawer');card.setAttribute('role','dialog');card.setAttribute('aria-label','科学来源版本详情');
    const top=el('div',null,'p2-drawer-top');
    append(top,el('h2','来源详情 · '+x.id),button('关闭',()=>{state.drawer=false;draw()},'outline'));
    card.append(top,chip(x.live?'受控合成登记':'演示数据 · 非已登记来源',x.live?'teal':'red'),el('h3',x.title));
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
    actions.append(button('查看版本管理',()=>{state.drawer=false;view('versions')},'outline'));
    card.append(actions,alert('Manager 只允许读取来源元数据；P2 与原 B1/EA 的数据不会在此页面自动合并。'));
    layer.append(card);return layer;
  }
  function sourceWizard(){
    const layer=el('div',null,'p2-overlay p2-wizard-layer');layer.addEventListener('click',e=>{if(e.target===layer){state.wizard=false;draw()}});
    const modal=el('section',null,'p2-modal');modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-label','来源登记 · 受控合成准备');
    const top=el('div',null,'p2-modal-head');
    top.append(el('h2','登记科学来源 · 四步向导'),button('关闭',()=>{state.wizard=false;draw()},'outline'));modal.append(top);
    const steps=el('div',null,'p2-steps');
    ['01 来源类型','02 原始内容','03 权限说明','04 范围确认'].forEach((t,i)=>steps.append(chip(t,i===state.step?'teal':'muted')));
    modal.append(steps);
    const d=state.draft||(state.draft={
      source_id:'P2-SYN-'+crypto.randomUUID().replaceAll('-','').slice(0,10).toUpperCase(),
      revision_id:'r1',title:'Synthetic source for internal QA testing',
      source_type:'RANDOMIZED_TRIAL',identifier_kind:'SYNTHETIC_ID',
      identifier:'SYN-DEMO-REFERENCE-001',
      available_at:'2026-01-01T00:00:00Z',fetched_at:'2026-01-02T00:00:00Z',
      raw_format:'MARKDOWN',
      raw_content:'# Synthetic scientific paper\n\nThis is illustrative document text for source QA only.\n\n| Group | Value |\n| A | 12.4 |',
      rights_assertion:'SYNTHETIC_FIXTURE',source_family_refs:[]});
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
      const saved=await perform(()=>api('/v1/p2/sources',{method:'POST',body:d}),'来源已登记并进入独立用途权利待核查状态');
      if(!saved)return;
      state.wizard=false;state.tab='library';state.selection=d.source_id+':'+d.revision_id;state.draft=null;draw();
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
    const outer=root.parentElement,component=frame();outer.replaceChild(component,root);root=component;
    if(state.tab==='library')library();
    else if(state.tab==='intake')renderIntake();
    else if(state.tab==='convert')conversion();
    else if(state.tab==='qa')qa();
    else versions();
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
    state.kindFilter='';state.unitIndex=0;state.display='bilingual';state.drawer=false;
    state.wizard=false;state.draft=null;state.document=null;state.original=null;state.translations=new Map();state.notice='';
    state.reviewed=new Set();state.liveSources=[];state.overview=null;
  }
  window.p2SourceStudio={render,reload,reset,selectTab:view};
  document.addEventListener('DOMContentLoaded',()=>{
    document.getElementById('logoutButton')?.addEventListener('click',reset);
    document.getElementById('p2NavGroup')?.addEventListener('click',event=>{
      const target=event.target.closest('[data-p2-tab]');if(!target)return;
      state.tab=target.dataset.p2Tab;
      if(!location.hash.startsWith('#/studio'))location.hash='#/studio';
      else draw();
    });
  });
})();
