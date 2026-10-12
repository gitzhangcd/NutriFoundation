/* WB-P2 Scientific Source Studio UI v0.2 — PR #36 aligned.
 * UI preview only: deliberately NO real upload, API, EA source mutation,
 * scientific Gold, expert grant, model translation, or source import.
 * All displayed documents are fictional synthetic design fixtures.
 */
'use strict';
(() => {
  const el=(tag,txt,cls)=>{const n=document.createElement(tag);if(txt!==undefined&&txt!==null)n.textContent=String(txt);if(cls)n.className=cls;return n;};
  const child=(parent,...items)=>{for(const n of items.flat())if(n)parent.append(n);return parent;};
  const btn=(text,action,cls='')=>{const n=el('button',text,'p2-btn '+cls);n.type='button';n.addEventListener('click',action);return n;};
  const label=(name,input)=>{const wrap=el('label',null,'p2-field');wrap.append(el('span',name),input);return wrap;};
  const input=(placeholder,max=160)=>{const n=el('input');n.placeholder=placeholder;n.maxLength=max;return n;};
  const safeId=s=>String(s||'').replace(/[^A-Za-z0-9_-]/g,'').slice(0,45);
  const fixture=[
    {id:'P2-DEMO-RCT-001',v:'r1',title:'Synthetic nutrition randomized trial — illustrative only',type:'RANDOMIZED_TRIAL',kind:'PDF',parser:'PDF layout mock',stage:'QA_HOLD',risk:'表格数值待人工复核',right:'DEMO_NOT_QUALIFIED',units:14,project:'PRJ-SYN-DEMO-001',batch:'BATCH-SYN-DEMO-001',revision:'Original / r1',raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO'},
    {id:'P2-DEMO-GUIDE-002',v:'r3',title:'Synthetic guideline: nutrition workflow — illustrative only',type:'GUIDELINE',kind:'JATS XML',parser:'JATS adapter mock',stage:'PACKAGE_DESIGN_PREVIEW',risk:'样例状态，不代表权利与科学审核合格',right:'DEMO_NOT_QUALIFIED',units:28,project:'PRJ-SYN-DEMO-001',batch:'BATCH-SYN-DEMO-002',revision:'r1 → r2 → r3',raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO'},
    {id:'P2-DEMO-OBS-003',v:'r1',title:'Synthetic cohort study — illustrative only',type:'OBSERVATIONAL_STUDY',kind:'HTML',parser:'HTML adapter mock',stage:'RIGHTS_HOLD',risk:'使用权不明确',right:'RIGHTS_UNVERIFIED',units:0,project:'',batch:'',revision:'Original / r1',raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO'},
    {id:'P2-DEMO-META-004',v:'r1',title:'Synthetic evidence synthesis — illustrative only',type:'SYSTEMATIC_REVIEW_META',kind:'Markdown',parser:'Markdown adapter mock',stage:'CONVERSION_REVIEW',risk:'表格与脚注结构有待核对',right:'DEMO_NOT_QUALIFIED',units:23,project:'PRJ-SYN-DEMO-002',batch:'',revision:'Original / r1',raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO'}
  ];
  const sourceText=[
    {unit:'u01',type:'PARAGRAPH',eng:'This is fictional trial text prepared only to demonstrate an evidence review interface.',zh:'这是虚构的试验文本，仅用于演示证据审核界面。',at:[5,20],locator:'PAGE_HINT_ONLY',issue:'段落映射未由独立文档解析验证'},
    {unit:'u02',type:'PARAGRAPH',eng:'A synthetic intervention group was compared with a synthetic control group at week twelve.',zh:'在第十二周比较了虚构干预组和虚构对照组。',at:[2,24],locator:'UNRESOLVED',issue:'原件页码和坐标未核实'},
    {unit:'u03',type:'TABLE_CELL',eng:'Demonstration table value: 12.4 units (not research evidence).',zh:'演示表格数值：12.4 单位（并非研究证据）。',at:[26,36],locator:'PAGE_HINT_ONLY',issue:'数值、单位、行列关系必须人工核验'}
  ];
  let tab='overview',selection=fixture[0].id,query='',filter='',drawer=false,wizard=false,step=0,kind='DOI / PMID',drafts=[],mode='bilingual',unitIndex=0,globalScope={project:'',batch:''},projects=[],batchMap=new Map(),currentRole='manager',notice='';
  const titles={overview:'资料总览',intake:'来源登记',convert:'结构化处理',qa:'人工 QA',library:'科学资料库',audit:'审计与版本记录'};
  const stages={QA_HOLD:['人工 QA 待处理','amber'],PACKAGE_DESIGN_PREVIEW:['封存样式演示','teal'],RIGHTS_HOLD:['版权资格待核验','red'],CONVERSION_REVIEW:['转换待核对','blue'],DRAFT_RIGHTS_HOLD:['本地待核查草稿','red']};
  let root=null,onlyFrozen=false,highlighted=false;
  const isProducer=()=>currentRole==='producer';
  const rowButtons=[];
  function heading(title,sub,actions=[]){const bar=el('div',null,'p2-heading');const left=el('div');child(left,el('p','WB-P2 · PR#36 ALIGNED · SYNTHETIC UI PREVIEW','p2-eyebrow'),el('h1',title),el('p',sub,'p2-subtitle'));const right=el('div',null,'p2-actions');child(right,...actions);child(bar,left,right);return bar;}
  function flag(text,variant='muted'){return el('span',text,'p2-flag '+variant);}
  function panel(title,sub){const n=el('section',null,'p2-card');if(title)n.append(el('h3',title));if(sub)n.append(el('p',sub,'p2-dim'));return n;}
  function banner(text,kind='warning'){return el('div',text,'p2-banner '+kind);}
  function noticeBox(){return notice?banner(notice,'note'):null;}
  function context(){const box=el('div',null,'p2-context');box.append(el('span','工作上下文','p2-label'));
    const project=el('select');const batch=el('select');
    child(project,el('option','全部项目'));project.firstChild.value='';
    for(const x of projects){const op=el('option',x.name||x.project_id);op.value=x.project_id;project.append(op);}
    project.value=globalScope.project||'';
    function updateBatches(){batch.replaceChildren();const none=el('option','全部批次');none.value='';batch.append(none);
      const entries=globalScope.project?(batchMap.get(globalScope.project)||[]):[];
      for(const x of entries){const op=el('option',x.label||x.batch_id);op.value=x.batch_id;batch.append(op);}
      batch.value=globalScope.batch||'';
    }
    project.addEventListener('change',()=>{globalScope.project=project.value;globalScope.batch='';updateBatches();draw()});
    batch.addEventListener('change',()=>{globalScope.batch=batch.value;draw()});
    updateBatches();child(box,project,batch,flag('只定义使用范围，不复制 SourceVersion','muted'));return box;}
  function nav(){const bar=el('nav',null,'p2-tabs');bar.setAttribute('aria-label','资料准备模块');for(const [key,title] of Object.entries(titles)){const b=btn(title,()=>{tab=key;drawer=false;draw()},'p2-tab'+(tab===key?' active':''));b.setAttribute('aria-current',tab===key?'page':'false');bar.append(b);}return bar;}
  function chrome(){const layout=el('div',null,'p2-studio');const actions=[flag('REAL SOURCE / GOLD / EXPERT GRANT · NO-GO','red')];child(layout,heading('科学资料准备工作台','独立完成来源登记、结构化转换、人工核验与版本留痕，再由原任务中心建立使用关系',actions),banner('P2 前端交互演示：资料均为虚构示例。不会上传文件、调用 MinerU、计算可信来源 SHA、建立科研证据或开放专家权限。','info'),context(),nav());return layout;}
  function cards(){const stats=el('div',null,'p2-stats');const all=[...fixture,...drafts];const data=[[String(all.length).padStart(2,'0'),'演示资料总数'],[String(all.filter(x=>x.stage==='RIGHTS_HOLD'||x.stage==='DRAFT_RIGHTS_HOLD').length).padStart(2,'0'),'待来源资格核查'],[String(all.filter(x=>x.stage==='QA_HOLD').length).padStart(2,'0'),'待人工 QA'],[String(all.filter(x=>x.stage==='PACKAGE_DESIGN_PREVIEW').length).padStart(2,'0'),'封存样式演示（非授权）']];for(const [v,t]of data){const box=el('div',null,'p2-stat');child(box,el('strong',v),el('span',t));stats.append(box);}return stats;}
  function selected(){return [...fixture,...drafts].find(x=>x.id===selection)||fixture[0];}

  function openWizard(type){
    kind=type;wizard=true;step=0;window.p2DraftForm={};draw();
  }
  function overview(){
    const wrap=el('div',null,'p2-view p2-overview');
    const top=el('div',null,'p2-subheading');
    child(top,el('div','01—04 · 从来源到不可变封存的四步准备流程','p2-eyebrow'),btn('＋ 登记新资料',()=>openWizard('DOI / PMID'),'primary'));
    wrap.append(top);
    const flow=el('div',null,'p2-workflow');
    for(const [i,name,sub,target] of [
      ['01','来源登记','身份、版本与版权','intake'],
      ['02','结构化转换','JATS · PDF · MinerU','convert'],
      ['03','人工质量核验','正文、表格与 Anchor','qa'],
      ['04','资料包冻结','不可变 Hash 与审计','audit']]){
      const b=btn('',()=>{tab=target;draw()},'p2-flow-step');
      child(b,el('span',i,'p2-flow-number'),child(el('span',null,'p2-flow-copy'),el('strong',name),el('small',sub)));
      flow.append(b);
    }
    wrap.append(flow,cards());
    const body=el('div',null,'p2-overview-grid');
    const launch=panel('添加科学资料','按来源类型进入登记，先验证身份与使用权，再进行转换。');
    const modes=el('div',null,'p2-entry-grid');
    for(const [label,desc,k,mark] of [
      ['文献标识符','DOI、PMID、PMCID；先建立来源元数据','DOI / PMID','⌕'],
      ['本地 PDF','记录原始文件及获取许可；本演示不读取内容','PDF','PDF'],
      ['XML / HTML','优先选择可信 JATS / 结构化全文','JATS / HTML','</>'],
      ['Markdown','登记已转换稿件并规划原件关联','Markdown','MD']]){
      const b=btn('',()=>openWizard(k),'p2-entry');
      child(b,el('span',mark,'p2-entry-mark'),child(el('span',null,'p2-entry-copy'),el('strong',label),el('small',desc),el('em','创建来源草稿 →')));
      modes.append(b);
    }
    launch.append(modes,banner('录入的 DOI 或文件不会自动被认定为授权可用。此页面仅创建浏览器内待核查演示草稿。','info'));body.append(launch);
    const gate=panel('准入检查清单','未通过的来源不得转入真实专家任务。');
    for(const [n,title,desc]of [['1','来源身份与版本','DOI / PMID、发布机构、勘误撤稿'],['2','使用许可核查','内部存储、机器处理与专家显示分别核准'],['3','转换与原文核验','段落、数值、表格、UTF-16 与页码'],['4','不可变版本封存','Raw SHA、Document SHA、Anchor 证明']]){
      gate.append(child(el('div',null,'p2-gate-row'),el('span',n,'p2-gate-number'),child(el('div'),el('strong',title),el('small',desc))));
    }
    gate.append(banner('🔒 Expert Exposure Gate：保持关闭','warning'));body.append(gate);wrap.append(body);
    const recent=panel('最近处理的资料','全部为虚构示例，点击详情可查看版本、资格与 QA 状态。');
    recent.append(tableFor([...fixture,...drafts].slice(0,5),'recent'));wrap.append(recent);
    wrap.append(el('p','P2 UI 对照上传 HTML Demo · 内容是内存中的合成示例；不连接真实科学来源。','p2-footnote'));
    root.append(wrap);
  }
  function tableFor(items,layout){
    const wrap=el('div',null,'p2-table-wrap'),t=el('table',null,'p2-table'),head=el('tr');
    const columns=layout==='recent'?['科学资料','来源类型','处理阶段','最近更新','操作']:
      layout==='intake'?['资料名称','来源标识','版权状态','处理阶段','操作']:
      layout==='convert'?['文件','转换方式','转换状态','可核验对象','操作']:
      ['来源资料','来源类别','资格与状态','版本','操作'];
    columns.forEach(h=>head.append(el('th',h)));t.append(child(el('thead'),head));
    const body=el('tbody');
    for(const x of items){const r=el('tr'),s=stages[x.stage]||[x.stage,'muted'];
      const first=el('td');child(first,el('strong',x.title),el('div',x.id+' · '+x.v,'p2-id'));
      r.append(first);
      if(layout==='recent')r.append(el('td',x.type),child(el('td'),flag(s[0],s[1])),el('td','演示记录'));
      else if(layout==='intake')r.append(el('td',x.id),el('td',x.right),child(el('td'),flag(s[0],s[1])));
      else if(layout==='convert')r.append(el('td',x.parser),child(el('td'),flag(s[0],s[1])),el('td','段落 / 表格 / Anchor'));
      else r.append(el('td',x.type),child(el('td'),flag(s[0],s[1])),el('td',x.v));
      r.append(child(el('td'),btn('查看详情',()=>{selection=x.id;drawer=true;draw()},'small')));body.append(r);
    }
    if(!items.length){const tr=el('tr'),td=el('td','无符合条件的演示来源','p2-dim');td.colSpan=5;body.append(child(tr,td));}
    t.append(body);wrap.append(t);return wrap;
  }

  function list(){
    const wrap=el('div',null,'p2-view');wrap.append(cards());
    const toolbar=el('div',null,'p2-toolbar');const search=input('搜索标题 / Source ID / 类型',180);search.value=query;search.setAttribute('aria-label','搜索来源元数据');
    search.addEventListener('input',()=>{query=search.value;renderTable()});
    const status=el('select');for(const [v,t] of [['','全部状态'],['RIGHTS_HOLD','版权待核验'],['CONVERSION_REVIEW','转换待核查'],['QA_HOLD','人工 QA 待处理'],['PACKAGE_DESIGN_PREVIEW','封存样式演示'],['DRAFT_RIGHTS_HOLD','本地待核查']]){const op=el('option',t);op.value=v;status.append(op);}
    status.value=filter;status.addEventListener('change',()=>{filter=status.value;renderTable()});
    toolbar.append(search,status,btn('全部',()=>{onlyFrozen=false;draw()},onlyFrozen?'outline':'primary'),btn('只看已封存',()=>{onlyFrozen=true;draw()},onlyFrozen?'primary':'outline'),btn('登记科学来源',()=>openWizard('DOI / PMID'),'primary'));wrap.append(toolbar);
    const tableCard=panel('科学来源清单','来源版本全局唯一；项目和批次仅为拟使用范围。下列所有文献均为合成展示记录，不属于 EA 已登记来源。');
    const holder=el('div',null,'p2-table-wrap');holder.id='p2TableTarget';tableCard.append(holder);wrap.append(tableCard);
    const lower=el('div',null,'p2-two');
    const a=panel('来源资格与转换','DOI / PDF / JATS / Markdown → 权利核查 → 结构转换 → Evidence Anchor → Human QA。');
    a.append(btn('查看转换作业',()=>{tab='convert';draw()}));
    const b=panel('与 P1.1 的安全交接','P2 可形成待授权 Source Package 和 Task Source Binding 设计，但不会触发 B3 Expert Grant。');
    b.append(btn('查看现有 B1 科学资料库',()=>{window.location.hash='#/sources';},'outline'));
    lower.append(a,b);wrap.append(lower);root.append(wrap);renderTable();
  }
  function renderTable(){const holder=document.getElementById('p2TableTarget');if(!holder)return;holder.replaceChildren();
    const table=el('table',null,'p2-table');const thead=el('thead');const tr=el('tr');
    for(const col of ['资料名称 / 来源版本','资料类型','资格与阶段','项目 / 批次范围','下一步'])tr.append(el('th',col));thead.append(tr);table.append(thead);
    const tb=el('tbody');const scoped=[...fixture,...drafts].filter(x=>(!onlyFrozen||x.stage==='PACKAGE_DESIGN_PREVIEW')&&(!globalScope.project||x.project===globalScope.project)&&(!globalScope.batch||x.batch===globalScope.batch));
    const all=scoped.filter(x=>{const q=query.toLowerCase().trim();return (!q||[x.id,x.title,x.type].join(' ').toLowerCase().includes(q))&&(!filter||x.stage===filter)});
    for(const x of all){const r=el('tr');const first=el('td');child(first,el('strong',x.title),el('div',x.id+' · '+x.v,'p2-id'));const status=stages[x.stage]||[x.stage,'muted'];
      r.append(first,el('td',x.type),child(el('td'),flag(status[0],status[1])),el('td',(x.project||'未绑定')+' / '+(x.batch||'—')));
      const last=el('td');last.append(btn('查看详情',()=>{selection=x.id;drawer=true;draw()},'small'));r.append(last);tb.append(r);}
    if(!all.length){const r=el('tr'),c=el('td','当前筛选下没有资料','p2-dim');c.colSpan=5;r.append(c);tb.append(r);}
    table.append(tb);holder.append(table);
    holder.append(el('p','此处不显示原文及候选答案；当前页面所有真实来源准入均为 NO-GO。','p2-footnote'));
  }
  function detail(){
    const x=selected();const mask=el('div',null,'p2-overlay');mask.addEventListener('click',ev=>{if(ev.target===mask){drawer=false;draw()}});
    const drawerBox=el('section',null,'p2-drawer');drawerBox.setAttribute('role','dialog');drawerBox.setAttribute('aria-label','科学来源版本详情');
    const top=el('div',null,'p2-drawer-top');child(top,el('h2','来源版本详情'),btn('关闭',()=>{drawer=false;draw()},'outline'));drawerBox.append(top);
    drawerBox.append(flag('演示资料 · 不构成真实来源准入','red'));drawerBox.append(el('h3',x.title));
    const items=[['Source ID',x.id],['Revision',x.v],['Type',x.type],['Artifact',x.kind],['Parser / Conversion',x.parser],['Rights',x.right],['Raw byte SHA-256',x.raw],['Canonical document SHA-256',x.canonical],['Project',x.project||'未绑定'],['Batch',x.batch||'未绑定'],['Version lineage',x.revision],['Quality / Hold reason',x.risk]];
    const grid=el('dl',null,'p2-facts');for(const [k,v]of items)child(grid,el('dt',k),el('dd',v));drawerBox.append(grid);
    drawerBox.append(banner('当前样例没有真实来源哈希、版权证明或人工审核签名，因此不得生成 Qualified Source Package。','warning'));
    const actions=el('div',null,'p2-actions');
    child(actions,btn('查看转换示例',()=>{drawer=false;tab='convert';draw()},'outline'),btn('查看 QA 示例',()=>{selection=x.id;drawer=false;tab='qa';draw()},'outline'));
    drawerBox.append(actions);mask.append(drawerBox);return mask;
  }
  function intakePage(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('来源登记与资格核查','先确认是什么、从哪里来、是否允许使用；未经核验不会进入专家阅读器。',
       [btn('＋ 新建来源',()=>openWizard('DOI / PMID'),'primary')]));
    const card=panel('资料接收队列','原始资料默认为待核查；这里展示演示列表，不代表真实来源已登记。');
    card.append(tableFor([...drafts,...fixture],'intake'));wrap.append(card);
    const rule=panel('登记前需明确的三项责任','注册只是草稿，不构成科学来源资格。');
    rule.append(banner('来源版本与身份、存储/机器处理/专家展示许可、撤稿与更正状态，必须分别验证并留痕。','warning'));wrap.append(rule);root.append(wrap);
  }
    function conversion(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('结构化处理任务','转换服务独立于专家标注，ParserRun 必须保留输入版本和运行谱系。',[flag('适配器边界（演示）','blue')]));
    const p=panel('当前转换任务','JATS/XML 优先；PDF/MinerU 由独立转换服务处理，OCR 与表格需额外 QA。');
    p.append(tableFor([...fixture,...drafts].filter(x=>x.stage!=='DRAFT_RIGHTS_HOLD'&&x.stage!=='RIGHTS_HOLD'),'convert'));
    p.append(banner('真实转换必须绑定原始文件 SHA、转换器版本、参数、Job ID、错误日志与原文核验。此演示不会运行 MinerU 或生成文档。','info'));wrap.append(p);
    root.append(wrap);
  }
    function quoteNode(record){const node=el('div',null,'p2-reader-paragraph');const before=record.eng.slice(0,record.at[0]);const q=record.eng.slice(record.at[0],record.at[1]);const after=record.eng.slice(record.at[1]);node.append(document.createTextNode(before));node.append(el('mark',q));node.append(document.createTextNode(after));return node;}
  function qa(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('结构化文档与证据锚点 QA','原始片段 ↔ 结构化结果并排对照；优先核查表格、数值、引用及页码。',[flag('人工核查优先','amber')]));
    if(!isProducer()){
      const lock=panel('演示身份限制','Manager 仅可查看来源元数据，不能因为打开 P2 页面而看到原文或证据 QA。');
      lock.append(banner('Manager 没有来源全文访问权。正式 Source Curator、审核签名和真实资料查看能力尚未实现。','warning'));wrap.append(lock);root.append(wrap);return;
    }
    wrap.append(banner('以下正文完全虚构，不取自 EA 原文。高亮仅演示原文与结构化内容对应，不能生成经过验证的 Anchor。','info'));
    const bar=el('div',null,'p2-toolbar');
    const m=el('select');for(const [v,title]of [['bilingual','原文＋辅助译文'],['original','仅原文'],['translation','仅辅助译文']]){const op=el('option',title);op.value=v;m.append(op);}
    m.value=mode;m.setAttribute('aria-label','阅读显示方式');m.addEventListener('change',()=>{mode=m.value;draw()});
    bar.append(el('strong','SYNTHETIC QA READER'),m,btn(highlighted?'隐藏锚点对应':'显示锚点对应',()=>{highlighted=!highlighted;draw()},'outline'));
    wrap.append(bar);
    const columns=el('div',null,'p2-qa-grid');
    const compare=el('div',null,'p2-qa-compare');
    const original=panel('原件视图 · 原文摘录','模拟原始来源 / 第 4 页（非真实 PDF）');
    const result=panel('结构化文档 IR','段落单元 / 辅助译文不替代原文');
    for(const [i,u]of sourceText.entries()){
      const a=el('button',null,'p2-unit'+(i===unitIndex?' selected':''));
      a.type='button';a.setAttribute('aria-pressed',String(i===unitIndex));a.addEventListener('click',()=>{unitIndex=i;draw()});
      a.append(el('span',u.unit+' · SOURCE','p2-unit-meta'));
      if(mode!=='translation')a.append(highlighted?quoteNode(u):el('p',u.eng,'p2-reader-paragraph'));
      else a.append(el('p','原文隐藏（辅助阅读模式）'));
      original.append(a);
      const b=el('div',null,'p2-structured-unit'+(i===unitIndex?' selected':''));
      b.append(el('span',u.unit+' · '+u.type,'p2-unit-meta'));
      if(mode!=='translation')b.append(highlighted?quoteNode(u):el('p',u.eng,'p2-reader-paragraph'));
      if(mode!=='original')b.append(el('p',u.zh,'p2-translation'));
      result.append(b);
    }
    original.append(flag('PAGE_HINT_ONLY · BBOX 未核准','amber'));compare.append(original,result);columns.append(compare);
    const q=panel('人工 QA 检查','请针对原文证据、数值、单位、结构和授权逐项判断。');
    const u=sourceText[unitIndex];
    for(const [title,value]of [['结构层级','待核验章节和段落关系'],['数值与单位','待核验结果、组别与单位'],['Evidence Anchor',u.unit+' · UTF-16 '+u.at[0]+'–'+u.at[1]],['PDF Locator',u.locator],['来源权限','仅合成演示；无真实许可'],['Original SHA','NOT_COMPUTED_DEMO']]){
      q.append(child(el('div',null,'p2-qa-check'),el('strong',title),el('small',value)));
    }
    q.append(btn('检查封存条件（演示阻断）',()=>{notice='封存失败：来源/许可、原始哈希、表格与 PDF 定位、人工审核均未完成。没有生成新的 Package 或 Grant。';draw()},'primary'));
    q.append(banner('🔒 QA 合格 ≠ 真实专家阅读授权，也不构成 Gold。','warning'));
    columns.append(q);wrap.append(columns);root.append(wrap);
  }
    function versions(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('来源版本与不可变封存','区分 Raw Artifact / Structured IR / Canonical Document / Source Quote 的摘要；封存并不授予 Expert 访问。'));
    const card=panel('版本与谱系 · 设计样例','当前均为虚构来源，不包含实际修订数据或已签发审核证明。');
    for(const x of fixture){const line=el('div',null,'p2-version');child(line,el('strong',x.id+' / '+x.v),el('span',x.revision+' · '+x.right));card.append(line);}
    wrap.append(card);
    const rules=panel('独立资格闸门','来源身份 → 权利范围 → 结构转换 → Human QA → SourcePackage Freeze → TaskSourceBinding。');
    rules.append(banner('SOURCE_PREPARATION_ACCEPTED ≠ EXPERT_EXPOSURE_AUTHORIZED。不能通过本页面创建专家 Grant、Gold 或真实 Agent 证据。','warning'));wrap.append(rules);root.append(wrap);
  }
  function audit(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('审计与版本记录','来源登记、转换、人工 QA 与封存分别留痕；任何历史版本不得覆盖。',[flag('仅为演示事件','muted')]));
    const grid=el('div',null,'p2-two');const log=panel('审计事件流（示意）','真实审计必须绑定 actor、时间、对象、前后状态、request ID 和 hash-chain。');
    for(const [action,info]of [
      ['SOURCE_PACKAGE_FROZEN','示例版本 r3 · 非真实来源冻结'],
      ['QA_ACCEPTED_BY_CURATOR','示例检查：原文、表格、Anchor · 未实际签名'],
      ['STRUCTURE_CONVERSION_COMPLETE','示例 JATS Adapter · Parser/Version/Job ID 未执行'],
      ['SOURCE_RIGHTS_REVIEWED','示例：存储、处理和阅读权限分别评估'],
      ['SOURCE_INTAKE_CREATED','示例来源登记，非真实来源记录']
    ])log.append(child(el('div',null,'p2-timeline-row'),el('strong',action),el('small',info)));
    const lineage=panel('来源版本与谱系','未绑定真实 Publisher、原始 Raw SHA 或转换运行。');
    for(const x of fixture)lineage.append(child(el('div',null,'p2-lineage-row'),el('strong',x.id+' / '+x.v),el('small',x.revision+' · '+x.right)));
    lineage.append(banner('封存不等于 Expert Grant。不能生成真实 Gold、Task Source Binding 或临床使用资格。','warning'));
    grid.append(log,lineage);wrap.append(grid);root.append(wrap);
  }
  function wizardPanel(){
    const layer=el('div',null,'p2-overlay');layer.addEventListener('click',e=>{if(e.target===layer){wizard=false;draw()}});
    const modal=el('section',null,'p2-modal');modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-labelledby','p2ModalTitle');
    const head=el('div',null,'p2-modal-head');child(head,el('div',null,'p2-modal-title'),btn('关闭',()=>{wizard=false;draw()},'outline'));head.firstChild.append(el('h2','来源登记 · 浏览器本地演示'));head.firstChild.firstChild.id='p2ModalTitle';modal.append(head);
    const steps=el('div',null,'p2-steps');for(let i=0;i<4;i++)steps.append(flag((i+1)+' · '+['输入类型','来源身份','权利与用途','项目与批次'][i],i===step?'teal':'muted'));modal.append(steps);
    const form=el('form',null,'p2-wizard-form');let fields=[];const info=el('p','这是本地 UI 演示；不得输入真实隐私数据；没有上传或数据库请求。','p2-dim');form.append(info);
    if(step===0){const opts=el('div',null,'p2-kinds');for(const k of ['DOI / PMID','PDF','JATS / HTML','Markdown']){const b=btn(k,()=>{kind=k;draw()},'p2-kind'+(kind===k?' picked':''));opts.append(b);}form.append(opts);form.append(banner('选 PDF 只表示入口意向；原型不会读取文件内容或调用 MinerU。','info'));}
    if(step===1){const title=input('示例：Synthetic source title',160);title.id='p2DraftTitle';title.value=window.p2DraftForm?.title||'';title.required=true;
      const identifier=input('DEMO-IDENTIFIER',60);identifier.id='p2DraftIdentifier';identifier.value=window.p2DraftForm?.identifier||'';identifier.required=true;
      form.append(label('资料标题（仅填写虚构示例）',title),label('文献标识符（演示字符串）',identifier));
      fields=[title,identifier];}
    if(step===2){form.append(banner('真实来源必须逐项评估版权、保存、机器处理、内部展示及专家可见范围，不能由本页自行确认许可。','warning'));
      const rights=el('textarea');rights.id='p2DraftRights';rights.rows=3;rights.maxLength=280;rights.placeholder='模拟填写拟使用目的（不能提交真实隐私资料）';rights.value=window.p2DraftForm?.rights||'内部来源资格核查（演示）';form.append(label('拟使用权限说明',rights));fields=[rights];}
    if(step===3){form.append(banner('Project / Batch 这里只是任务使用范围的预览，不创建实际绑定或授权。','info'));
      form.append(el('p','当前项目：'+(globalScope.project||'全部项目')+'；当前批次：'+(globalScope.batch||'未选'),'p2-subtitle'));
      const chk=el('input');chk.type='checkbox';chk.id='p2DemoAgree';chk.required=true;
      const check=el('label',null,'p2-check');child(check,chk,el('span','确认只创建浏览器内的虚构待核查记录，不上传真实文献或个人信息'));form.append(check);fields=[chk];}
    const actions=el('div',null,'p2-modal-actions');actions.append(btn('返回',()=>{snapshot();step=Math.max(0,step-1);draw()},'outline'));
    function snapshot(){const d=window.p2DraftForm||{};const t=document.getElementById('p2DraftTitle');const i=document.getElementById('p2DraftIdentifier');const r=document.getElementById('p2DraftRights');if(t)d.title=t.value;if(i)d.identifier=i.value;if(r)d.rights=r.value;window.p2DraftForm=d;}
    actions.append(btn(step===3?'创建本地待核查草稿':'下一步',()=>{
      snapshot();if(step<3){if(fields.some(x=>x.required&&!x.value.trim())){notice='请先填写当前步骤必填信息';draw();return;}step++;draw();return;}
      const chk=document.getElementById('p2DemoAgree');if(!chk?.checked){notice='需要确认此操作仅创建虚构本地草稿';draw();return;}
      if(!isProducer()){notice='只有 Producer 可以创建本地演示草稿；真实 Source Curator 权限未实现';wizard=false;draw();return;}
      const d=window.p2DraftForm||{};
      drafts.unshift({id:'P2-DEMO-LOCAL-'+String(drafts.length+1).padStart(3,'0'),v:'draft',title:d.title||'Fictional local draft',type:kind,kind,parser:'NOT_EXECUTED',stage:'DRAFT_RIGHTS_HOLD',risk:'没有真实身份/权限/来源核查',right:'RIGHTS_UNVERIFIED',units:0,project:globalScope.project,batch:globalScope.batch,revision:'Local in-memory only',raw:'NOT_COMPUTED_DEMO',canonical:'NOT_COMPUTED_DEMO'});
      wizard=false;step=0;window.p2DraftForm={};tab='library';notice='已创建仅存在于当前浏览器内存的待核查演示草稿；没有实际保存、上传或授权。';draw();
    },'primary'));
    form.addEventListener('submit',ev=>ev.preventDefault());form.append(actions);modal.append(form);layer.append(modal);return layer;
  }
  function draw(){
    if(!root||!root.isConnected)return;
    const host=root.parentNode;const next=chrome();host.replaceChild(next,root);root=next;
    const msg=noticeBox();if(msg)root.append(msg);
    if(tab==='overview')overview();else if(tab==='library')list();else if(tab==='intake')intakePage();else if(tab==='convert')conversion();else if(tab==='qa')qa();else audit();
    if(drawer)root.append(detail());
    if(wizard)root.append(wizardPanel());
  }
  function render(options={}){
    currentRole=options.role||'manager';globalScope={project:options.scope?.project||'',batch:options.scope?.batch||''};
    projects=options.projects||[];batchMap=options.batchMap||new Map();
    root=chrome();const wrapper=el('div',null,'p2-studio-mount');wrapper.append(root);
    // render() returns the mount before it is connected; perform initial draw
    // synchronously without replacing detached nodes.
    if(tab==='overview'){root.append(el('div','正在准备科学资料总览…','p2-dim'));}
    queueMicrotask(()=>{if(root?.isConnected)draw()});
    return wrapper;
  }
  function reset(){tab='overview';selection=fixture[0].id;query='';filter='';drawer=false;wizard=false;drafts=[];notice='';mode='bilingual';unitIndex=0;highlighted=false;onlyFrozen=false;window.p2DraftForm={};}
  window.p2SourceStudio={render,reset};
  document.addEventListener('DOMContentLoaded',()=>{
    // Same-tab role/session changes must discard locally entered draft metadata.
    document.getElementById('logoutButton')?.addEventListener('click',reset);
  });
})();
