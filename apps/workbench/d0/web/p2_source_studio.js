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
  let tab='library',selection=fixture[0].id,query='',filter='',drawer=false,wizard=false,step=0,kind='DOI / PMID',drafts=[],mode='bilingual',unitIndex=0,globalScope={project:'',batch:''},projects=[],batchMap=new Map(),currentRole='manager',notice='';
  const titles={library:'科学资料库',intake:'来源登记',convert:'转换作业',qa:'人工 QA',versions:'来源与版本'};
  const stages={QA_HOLD:['人工 QA 待处理','amber'],PACKAGE_DESIGN_PREVIEW:['封存样式演示','teal'],RIGHTS_HOLD:['版权资格待核验','red'],CONVERSION_REVIEW:['转换待核对','blue'],DRAFT_RIGHTS_HOLD:['本地待核查草稿','red']};
  let root=null;
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
  function chrome(){const layout=el('div',null,'p2-studio');const actions=[flag('REAL SOURCE / GOLD / EXPERT GRANT · NO-GO','red')];child(layout,heading('Scientific Source Studio','继承 PR #36 管理界面 · 来源准备是独立于专家授权的工作流',actions),banner('这是与现有 D0 同源的 P2 UI 原型。当前来源均为虚构演示；不会上传文件、注册真实文献、生成 SHA 或向 EA/TPA 写入数据。','info'),context(),nav());return layout;}
  function cards(){const stats=el('div',null,'p2-stats');const data=[['4','虚构来源示例'],['2','模拟转换作业'],['2','QA 阻断样例'],['0','正式来源授权']];for(const [v,t]of data){const box=el('div',null,'p2-stat');child(box,el('strong',v),el('span',t));stats.append(box);}return stats;}
  function selected(){return [...fixture,...drafts].find(x=>x.id===selection)||fixture[0];}
  function list(){
    const wrap=el('div',null,'p2-view');wrap.append(cards());
    const toolbar=el('div',null,'p2-toolbar');const search=input('搜索标题 / Source ID / 类型',180);search.value=query;search.setAttribute('aria-label','搜索来源元数据');
    search.addEventListener('input',()=>{query=search.value;renderTable()});
    const status=el('select');for(const [v,t] of [['','全部状态'],['RIGHTS_HOLD','版权待核验'],['CONVERSION_REVIEW','转换待核查'],['QA_HOLD','人工 QA 待处理'],['PACKAGE_DESIGN_PREVIEW','封存样式演示'],['DRAFT_RIGHTS_HOLD','本地待核查']]){const op=el('option',t);op.value=v;status.append(op);}
    status.value=filter;status.addEventListener('change',()=>{filter=status.value;renderTable()});
    toolbar.append(search,status,btn('登记科学来源',()=>{wizard=true;step=0;draw()},'primary'));wrap.append(toolbar);
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
    const tb=el('tbody');const scoped=[...fixture,...drafts].filter(x=>(!globalScope.project||x.project===globalScope.project)&&(!globalScope.batch||x.batch===globalScope.batch));
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
    const wrap=el('div',null,'p2-view');wrap.append(heading('来源登记','采集拟用资料的身份、版本与用途；本原型不执行数据库注册、上传或权利许可判断。',
      [btn('新建来源登记',()=>{wizard=true;step=0;draw()},'primary')]));
    const note=panel('四步来源登记向导','① 输入类型 → ② 文献身份 → ③ 使用权与责任 → ④ Project/Batch 拟使用范围。');note.append(banner('允许查看流程，但创建后只形成浏览器内的虚构待核查草稿。真实 DOI/PDF/患者资料不要输入本演示。','warning'));wrap.append(note);
    const list=panel('浏览器内草稿','刷新页面后消失；没有 HTTP POST、存储或后台任务。');
    list.append(el('p','待核验草稿数量：'+drafts.length,'p2-statline'));list.append(btn('登记一个演示来源',()=>{wizard=true;step=0;draw()}));wrap.append(list);root.append(wrap);
  }
  function conversion(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('结构化转换作业','原始文件与 ParserRun 单独留痕；不将 PDF 转换混入专家标注界面。'));
    const tbl=panel('转换队列 · 虚构示例','所有条目均为设计数据；尚未安装或连接 MinerU / JATS / Markdown Worker。');
    const rows=[['RUN-DEMO-001','PDF / MinerU adapter (mock)','P2-DEMO-RCT-001','人工核验待处理','PDF page hint，尚无唯一 bbox'],['RUN-DEMO-002','JATS adapter (mock)','P2-DEMO-GUIDE-002','结果结构演示','XML 章节及引用关系为示意'],['RUN-DEMO-003','Markdown adapter (mock)','P2-DEMO-META-004','转换待核对','表格脚注与公式待确认']];
    const table=el('table',null,'p2-table');const h=el('tr');['Run','Adapter','Source','Status','风险'].forEach(v=>h.append(el('th',v)));table.append(child(el('thead'),h));
    const body=el('tbody');for(const row of rows){const tr=el('tr');row.forEach(v=>tr.append(el('td',v)));body.append(tr);}table.append(body);tbl.append(child(el('div',null,'p2-table-wrap'),table));
    tbl.append(banner('真实 ParserRun 必须绑定工具版本、参数摘要、输入原始字节 SHA、输出结构摘要、运行日志与人工 QA。UI 不能伪造成功转换。','info'));wrap.append(tbl);
    const bottom=panel('适配器与权威关系','原始 Artifact 为唯一权威；结构化 Markdown/HTML 是辅助表示。PDF BBox 未精确匹配时只能标记 PAGE_HINT_ONLY 或 UNRESOLVED。');wrap.append(bottom);root.append(wrap);
  }
  function quoteNode(record){const node=el('div',null,'p2-reader-paragraph');const before=record.eng.slice(0,record.at[0]);const q=record.eng.slice(record.at[0],record.at[1]);const after=record.eng.slice(record.at[1]);node.append(document.createTextNode(before));node.append(el('mark',q));node.append(document.createTextNode(after));return node;}
  function qa(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('结构化来源 QA 阅读器','原文为权威 · 译文仅辅助 · 精确引用/UTF-16/页码状态独立核查。'));
    if(!isProducer()){const lock=panel('演示身份限制','当前 D0 Manager 没有来源全文访问权。不能因增加 P2 页面而在客户端提升角色。');
      lock.append(banner('Manager 只可查看来源元数据。Source Curator 是 P2.0 待设计的真实身份，不存在于 PR #36 的授权系统中。','warning'));
      wrap.append(lock);root.append(wrap);return;}
    wrap.append(banner('以下是内置虚构文本，不取自任何真实文献或现有 EA 原文；Producer 只能体验 UI 示例，不代表获得正式 Source Curator 权限。','info'));
    const tools=el('div',null,'p2-toolbar');const m=el('select');[['bilingual','逐段双语'],['original','仅原文'],['translation','辅助译文']].forEach(([v,t])=>{const op=el('option',t);op.value=v;m.append(op)});m.value=mode;m.setAttribute('aria-label','阅读显示方式');m.addEventListener('change',()=>{mode=m.value;draw()});
    tools.append(el('strong','SYNTHETIC MOCK READER · NO REAL SOURCE'),m);wrap.append(tools);
    const columns=el('div',null,'p2-qa-grid');
    const original=panel('原始资料定位','PDF 图像与页面坐标尚未接入，左栏仅展示原件占位。');original.append(el('div','PDF / JATS 原件仅作为模拟占位；无真实文件下载或上传。','p2-pdf-preview'));original.append(flag('PAGE HINT ≠ VERIFIED BBOX','amber'));columns.append(original);
    const center=panel('结构化正文','文献转换后按 Unit 展示，双语仅作辅助层。');
    for(const [i,u]of sourceText.entries()){
      const item=el('button',null,'p2-unit'+(i===unitIndex?' selected':''));
      item.type='button';item.setAttribute('aria-pressed',String(i===unitIndex));
      item.addEventListener('click',()=>{unitIndex=i;draw()});item.append(el('span',u.unit+' · '+u.type,'p2-unit-meta'));
      if(mode!=='translation')item.append(quoteNode(u));
      if(mode!=='original')item.append(el('div',u.zh,'p2-translation'));
      center.append(item);
    }columns.append(center);
    const right=panel('Evidence Anchor 核查','选择任意 Unit，查看原文精确引用及定位条件。');const u=sourceText[unitIndex];const q=u.eng.slice(u.at[0],u.at[1]);
    const facts=[['Unit ID',u.unit],['UTF-16',u.at[0]+' — '+u.at[1]],['Quote',q],['Anchor match',u.eng.slice(u.at[0],u.at[1])===q?'仅本地演示文本匹配':'MISMATCH'],['Original SHA','NOT_COMPUTED_DEMO'],['Source Quote SHA','NOT_COMPUTED_DEMO'],['PDF Locator',u.locator],['QA issue',u.issue]];
    const defs=el('dl',null,'p2-facts');for(const [k,v]of facts)child(defs,el('dt',k),el('dd',v));right.append(defs);
    right.append(banner('存在未验证 PDF 坐标/表格数值与缺失 SHA。禁止自动将本示例提升为 VERIFIED_ANCHOR。','warning'));
    right.append(btn('检查封存条件（演示阻断）',()=>{notice='封存失败：来源/许可、原始哈希、表格与 PDF 定位、人工审核均未完成。没有生成新的 Package 或 Grant。';draw()},'primary'));
    columns.append(right);wrap.append(columns);root.append(wrap);
  }
  function versions(){
    const wrap=el('div',null,'p2-view');wrap.append(heading('来源版本与不可变封存','区分 Raw Artifact / Structured IR / Canonical Document / Source Quote 的摘要；封存并不授予 Expert 访问。'));
    const card=panel('版本与谱系 · 设计样例','当前均为虚构来源，不包含实际修订数据或已签发审核证明。');
    for(const x of fixture){const line=el('div',null,'p2-version');child(line,el('strong',x.id+' / '+x.v),el('span',x.revision+' · '+x.right));card.append(line);}
    wrap.append(card);
    const rules=panel('独立资格闸门','来源身份 → 权利范围 → 结构转换 → Human QA → SourcePackage Freeze → TaskSourceBinding。');
    rules.append(banner('SOURCE_PREPARATION_ACCEPTED ≠ EXPERT_EXPOSURE_AUTHORIZED。不能通过本页面创建专家 Grant、Gold 或真实 Agent 证据。','warning'));wrap.append(rules);root.append(wrap);
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
    if(tab==='library')list();else if(tab==='intake')intakePage();else if(tab==='convert')conversion();else if(tab==='qa')qa();else versions();
    if(drawer)root.append(detail());
    if(wizard)root.append(wizardPanel());
  }
  function render(options={}){
    currentRole=options.role||'manager';globalScope={project:options.scope?.project||'',batch:options.scope?.batch||''};
    projects=options.projects||[];batchMap=options.batchMap||new Map();
    root=chrome();const wrapper=el('div',null,'p2-studio-mount');wrapper.append(root);
    // render() returns the mount before it is connected; perform initial draw
    // synchronously without replacing detached nodes.
    if(tab==='library'){root.append(cards());const holder=el('div');root.append(holder);root.removeChild(holder);}
    queueMicrotask(()=>{if(root?.isConnected)draw()});
    return wrapper;
  }
  function reset(){tab='library';selection=fixture[0].id;query='';filter='';drawer=false;wizard=false;drafts=[];notice='';mode='bilingual';unitIndex=0;window.p2DraftForm={};}
  window.p2SourceStudio={render,reset};
  document.addEventListener('DOMContentLoaded',()=>{
    // Same-tab role/session changes must discard locally entered draft metadata.
    document.getElementById('logoutButton')?.addEventListener('click',reset);
  });
})();
