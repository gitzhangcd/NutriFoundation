/* WB-TPA-P1.1-A2: safe management UX layered over the accepted D0 TPA page.
   No real source import, scientific data, rich markup interpolation or role switching. */
'use strict';
(() => {
  const $p = id => document.getElementById(id);
  const e = (tag, text, cls) => {
    const x = document.createElement(tag);
    if (text !== undefined) x.textContent = String(text);
    if (cls) x.className = cls;
    return x;
  };
  const button = (label, fn, variant='secondary') => {
    const x = e('button',label,'p11-btn '+variant);
    x.type='button'; x.addEventListener('click',fn); return x;
  };
  let projects=[], batchMap=new Map(), overview=null, managedTasks=[];
  let project='',batch='',search='',wizardStep=1, active='overview',legacyOnly=false;
  let pageOffset=0,pageTotal=0,pageSize=25,stateScope='',selectedTaskId='',selectedTaskMeta=null;
  let drawerReturnFocus=null;
  // B1 is a *metadata-only* view of trusted synthetic EA source versions.
  let sourcePackages=[],sourceSelection='',packageValidation=null;
  let loadingPromise=null,reloadRequested=false;
  // Explicit opt-in allows the original P1 controller to retain its old fallback routes.
  window.opsA5Enabled=true;
  const routes=['overview','projects','tasks','sources','studio','agent','experts','quality','audit'];
  const labels={overview:'工作总览',projects:'项目与批次',tasks:'任务中心',sources:'科学资料库',studio:'科学资料准备 · P2',agent:'Agent 准备',experts:'专家与分配',quality:'进度与质控',audit:'审计与导出'};
  const metric={preparing:'准备中',ready:'待分配',assigned:'已分配未发布',published:'已发布',revoked:'已撤销',blocked:'历史阻断'};
  // Demo status copy (P1.1-A Management Demo); English enum retained in DOM for acceptance checks.
  const stateLabel={DRAFT:'草稿待核验',VALIDATED:'定义已验证',DEFINITION_FROZEN:'定义已冻结',READY_FOR_ASSIGNMENT:'工作包已准备',ASSIGNED:'已分配待发布',PUBLISHED:'已发布可访问',REVOKED:'后续访问已撤销'};
  const stateClass={DRAFT:'s-draft',VALIDATED:'s-validated',DEFINITION_FROZEN:'s-frozen',READY_FOR_ASSIGNMENT:'s-ready',ASSIGNED:'s-assigned',PUBLISHED:'s-published',REVOKED:'s-revoked'};
  let modeScope='', wizardOpen=false;
  const cutoff = () => new Date().toISOString().slice(0,10);
  const fresh = prefix => `${prefix}${crypto.randomUUID().replaceAll('-','').slice(0,12).toUpperCase()}`;
  const clear = node => node.replaceChildren();
  const role = () => window.auth?.role || auth?.role;
  const notify = msg => { if (typeof receipt==='function') receipt(msg); };
  const catchMessage = err => { notify('未完成操作：'+err.message); window.alert('操作未完成：'+err.message); };
  const apiOps = (path, options) => api(path, options);
  // Scoped navigation remains a UI convenience, never a data entitlement.
  const PROJECT_PATTERN=/^PRJ-SYN-[A-Z0-9-]{3,40}$/;
  const BATCH_PATTERN=/^BATCH-SYN-[A-Z0-9-]{3,40}$/;
  const TASK_PATTERN=/^TPA-SYN-[A-Z0-9-]{3,50}$/;
  const SOURCE_ID_PATTERN=/^[A-Z0-9-]{3,40}$/;
  const SOURCE_REV_PATTERN=/^[A-Za-z0-9._-]{1,32}$/;
  const paramsFor=(p=project,b=batch,t='')=>{
    const query=new URLSearchParams();
    if(p)query.set('project',p);
    if(b)query.set('batch',b);
    if(t&&TASK_PATTERN.test(t))query.set('task',t);
    return query;
  };
  const hashFor=(view,p=project,b=batch,t='')=>{
    const params=paramsFor(p,b,view==='tasks'?t:'');
    if(view==='sources'&&sourceSelection){
      const [sid,revision]=sourceSelection.split(':');
      if(SOURCE_ID_PATTERN.test(sid||'')&&SOURCE_REV_PATTERN.test(revision||'')){
        params.set('source',sid);params.set('revision',revision);
      }
    }
    const query=params.toString();
    return '#/'+view+(query?'?'+query:'');
  };
  function navigate(view,p=project,b=batch){
    if(p&&!PROJECT_PATTERN.test(p))return;
    if(b&&(!BATCH_PATTERN.test(b)||!p))return;
    active=routes.includes(view)?view:'overview';project=p;batch=b;
    const next=hashFor(active,project,batch);
    if(location.hash!==next)location.hash=next;
    // Rendering is immediate; hashchange provides browser back/forward replay.
    render();
  }
  function readRoute(){
    const raw=location.hash.startsWith('#/')?location.hash.slice(2):'';
    const [name,query='']=raw.split('?');
    const params=new URLSearchParams(query);
    let p=params.get('project')||'',b=params.get('batch')||'';
    if(p&&!PROJECT_PATTERN.test(p))p='';
    if(b&&(!BATCH_PATTERN.test(b)||!p))b='';
    const view=routes.includes(name)?name:'overview';
    let task=view==='tasks'?(params.get('task')||''):'';
    if(task&&!TASK_PATTERN.test(task))task='';
    const sid=view==='sources'?(params.get('source')||''):'';
    const revision=view==='sources'?(params.get('revision')||''):'';
    const source=(SOURCE_ID_PATTERN.test(sid)&&SOURCE_REV_PATTERN.test(revision))?
       sid+':'+revision:'';
    if(p&&projects.length&&!projects.some(x=>x.project_id===p)){p='';b='';}
    if(b&&batchMap.size&&!(batchMap.get(p)||[]).some(x=>x.batch_id===b))b='';
    return {view,p,b,task,source};
  }

  function field(label, id, max, placeholder, value='') {
    const wrap=e('label',undefined,'p11-field');
    wrap.append(e('span',label));
    const input=e('input');input.id=id;input.maxLength=max;input.placeholder=placeholder;input.value=value;
    input.required=!label.includes('可选');
    wrap.append(input);return wrap;
  }
  function notice(text){return e('p',text,'p11-notice')}
  function frame(title, subtitle){
    const out=e('div',undefined,'p11-page'); const hdr=e('header',undefined,'p11-heading');
    hdr.append(e('h2',title),e('p',subtitle));out.append(hdr);return out;
  }
  async function loadProjects(){
    const data=await apiOps('/v1/tpa/projects?limit=100&offset=0');
    projects=data.projects || [];
    let offset=projects.length;
    while(offset<data.total&&offset<10000){
      const more=await apiOps('/v1/tpa/projects?limit=100&offset='+offset);
      if(!more.projects?.length)break;
      projects.push(...more.projects); offset+=more.projects.length;
    }
    batchMap=new Map();
    await Promise.all(projects.map(async item=>{
      const b=await apiOps('/v1/tpa/projects/'+encodeURIComponent(item.project_id)+'/batches');
      batchMap.set(item.project_id,b.batches||[]);
    }));
    const r=readRoute();
    project=r.p;batch=r.b;
    if(project&&!projects.some(p=>p.project_id===project)){project='';batch='';}
    if(batch&&!((batchMap.get(project)||[]).some(b=>b.batch_id===batch)))batch='';
  }
  async function fetchViews(){
    const scope=new URLSearchParams();
    if(project)scope.set('project_id',project);
    if(batch)scope.set('batch_id',batch);
    const tasks=new URLSearchParams(scope);
    if(search)tasks.set('q',search);
    const requestedState=!project&&legacyOnly?'LEGACY':stateScope;
    if(requestedState)tasks.set('state',requestedState);
    if(modeScope)tasks.set('workflow_strategy',modeScope);
    tasks.set('limit',String(pageSize));
    tasks.set('offset',String(pageOffset));
    const [v, result]=await Promise.all([
      apiOps('/v1/tpa/overview'+(scope.size?'?'+scope:'')),
      apiOps('/v1/tpa/tasks?'+tasks)
    ]);
    overview=v;managedTasks=result.tasks||[];pageTotal=result.total||0;
    // A state transition may move the selected row off this page. Never invent its status.
    if(pageOffset>=pageTotal&&pageOffset>0){
      pageOffset=Math.max(0,Math.floor(Math.max(0,pageTotal-1)/pageSize)*pageSize);
      return fetchViews();
    }
    if(selectedTaskId){
      const row=managedTasks.find(t=>t.task_id===selectedTaskId);
      if(row)selectedTaskMeta=row;
    }
    // The UI uses only this bounded server page; never silently concatenate to an incomplete 10k sample.
    if($p('countDraft'))$p('countDraft').textContent=String(v.counts.preparing);
    if($p('countReady'))$p('countReady').textContent=String(v.counts.ready);
    if($p('countPublished'))$p('countPublished').textContent=String(v.counts.published);
  }
  function select(id, entries, value, onChange, placeholder){
    const sel=e('select');sel.id=id;sel.className='p11-select';
    const opt=e('option',placeholder);opt.value='';sel.append(opt);
    for(const [k,label] of entries){const o=e('option',label);o.value=k;sel.append(o)}
    sel.value=value;sel.addEventListener('change',ev=>onChange(ev.target.value));return sel;
  }
  async function chooseScope(p,b=''){
    legacyOnly=false;pageOffset=0;navigate(active,p,b);await fetchViews();render();
  }
  function scopes(parent){
    const toolbar=e('div',undefined,'p11-scope');
    toolbar.append(e('span','统计范围：'));
    toolbar.append(select('p11ScopeProject',projects.map(p=>[p.project_id,p.name]),project,
      v=>chooseScope(v).catch(catchMessage),'全部可见项目'));
    if(project){toolbar.append(select('p11ScopeBatch',(batchMap.get(project)||[]).map(b=>[b.batch_id,b.label]),batch,
      v=>chooseScope(project,v).catch(catchMessage),'全部批次'));}
    parent.append(toolbar);
  }
  function countLink(parent,key,val){
    if(key==='blocked'){
      const unavailable=e('div',metric[key],'p11-btn p11-stat p11-unavailable');
      unavailable.append(e('strong',val===null?'未统计':String(val)));
      unavailable.setAttribute('aria-label','历史阻断：未提供可信统计');
      parent.append(unavailable);
      return;
    }
    const b=button(metric[key],()=>{
      navigate('tasks');
      const v={preparing:'PREPARING',ready:'READY_FOR_ASSIGNMENT',assigned:'ASSIGNED',published:'PUBLISHED',revoked:'REVOKED'}[key];
      if(v!==undefined&&$p('stateFilter')){
        $p('stateFilter').value=v;
        $p('stateFilter').dispatchEvent(new Event('change'));
      }
    },'p11-stat');
    b.append(e('strong',val===null?'未统计':String(val)));
    parent.append(b);
  }
  function renderOverview(){
    const c=overview?.counts || {}; const page=frame('工作总览','仅统计服务器已记录的合成工程任务；发布不代表已阅读或完成。');
    scopes(page);
    const stats=e('div',undefined,'p11-stats');
    for(const key of ['preparing','ready','assigned','published','revoked','blocked'])countLink(stats,key,c[key]);
    page.append(stats);
    const cols=e('div',undefined,'p11-grid');
    const todo=e('article',undefined,'p11-panel');todo.append(e('h3','我的待办'));
    if(role()==='producer'){
      todo.append(notice('Producer：负责创建、验证、冻结、准备；不能分配或发布。'));
      todo.append(button('进入任务生产',()=>go('tasks'),'primary'));
      todo.append(e('p',`准备中任务：${c.preparing??0}`,'p11-meta'));
    } else {
      todo.append(notice('Manager：负责合成专家分配、发布及撤销未来访问。'));
      todo.append(button('查看待分配任务',()=>{ $p('stateFilter').value='READY_FOR_ASSIGNMENT';go('tasks');},'primary'));
      todo.append(e('p',`待分配：${c.ready??0} · 待发布：${c.assigned??0}`,'p11-meta'));
    }
    const bounds=e('article',undefined,'p11-panel');bounds.append(e('h3','研究与安全边界'));
    bounds.append(notice('当前阶段只接受虚构合成来源；真实 PDF/MinerU、真实 Agent 和专家试验均未启用。'));
    bounds.append(notice('项目与批次仅为运营分组，不产生新的科学真值、Gold 或实验分组。'));
    bounds.append(notice('历史阻断事件暂无独立可靠统计，因此显示“未统计”，不显示虚假的 0。'));
    cols.append(todo,bounds);page.append(cols);
    page.append(e('p',`未归属 Legacy 合成任务：${c.legacy??0}。历史任务不会自动放入项目。`,'p11-meta'));
    return page;
  }
  function projectCard(item){
    const card=e('article',undefined,'p11-panel p11-project');
    card.append(e('h3',item.name),e('p',item.project_id,'p11-meta'));
    card.append(e('p',`批次 ${item.batch_count} · 任务 ${item.task_count} · ${item.lifecycle}`,'p11-meta'));
    if(item.description)card.append(e('p',item.description,'p11-desc'));
    card.append(button('查看项目与批次',()=>navigate('projects',item.project_id,''),'secondary'));
    return card;
  }
  function renderProjects(){
    const page=frame('项目与批次','管理任务组织关系；不会改变现有科学任务、实验组别或原文访问权限。');
    const head=e('div',undefined,'p11-row');
    head.append(button('全部项目',()=>navigate('projects','',''),'secondary'));
    if(role()==='producer')head.append(button('新建项目',()=>modal('project'),'primary'));
    page.append(head);
    if(!project){
      const cards=e('div',undefined,'p11-grid');
      if(!projects.length)cards.append(notice('还没有合成运营项目。Producer 可创建第一个项目。'));
      for(const p of projects)cards.append(projectCard(p));
      page.append(cards);return page;
    }
    const p=projects.find(x=>x.project_id===project); if(!p)return page;
    page.append(e('h3',p.name),e('p',p.project_id,'p11-meta'));
    const bar=e('div',undefined,'p11-row');
    if(role()==='producer')bar.append(button('在此项目新建批次',()=>modal('batch'),'primary'));
    bar.append(button('查看该项目任务',()=>{batch='';go('tasks')},'secondary'));page.append(bar);
    const cards=e('div',undefined,'p11-grid');
    const batches=batchMap.get(project)||[];
    if(!batches.length)cards.append(notice('该项目还没有批次。'));
    for(const item of batches){
      const card=e('article',undefined,'p11-panel');card.append(e('h3',item.label),e('p',item.batch_id,'p11-meta'));
      card.append(e('p',`${item.task_count} 项任务`,'p11-meta'));
      card.append(button('查看批次任务',()=>navigate('tasks',project,item.batch_id),'secondary'));
      cards.append(card);
    }
    page.append(cards);return page;
  }
  async function loadSourcePackages(){
    const found=await apiOps('/v1/tpa/source-packages?limit=100&offset=0');
    sourcePackages=found.packages||[];
    // B1 accepts at most the seven already-seeded fixtures. Never claim to have
    // inventoried pages we did not read when the registry grows in P2.
    if(found.total>sourcePackages.length){
      notify('来源包注册表当前超出单页范围，后续需服务端分页；此页不是全部包');
    }
    const routeSource=readRoute().source;
    if(routeSource)sourceSelection=routeSource;
    if(sourceSelection&&!sourceData.some(s=>s.source_id+':'+s.revision_id===sourceSelection))
      sourceSelection='';
    if(!sourceSelection&&sourceData.length)
      sourceSelection=sourceData[0].source_id+':'+sourceData[0].revision_id;
  }
  function b1Manifest(src){
    return {schema_version:'WB-SOURCE-PACKAGE-v0.1',
      import_kind:'EXISTING_SYNTHETIC_SOURCE',
      parser_adapter:'SYNTHETIC_FIXTURE_ADAPTER',
      source_id:src.source_id,revision_id:src.revision_id,
      source_type:src.source_type,profile_id:src.profile_id,
      canonical_document_sha256:src.canonical_document_sha256,
      rights_status:src.rights_status,parent_package_id:null};
  }
  const b1PackageId=src=>'SPKG-SYN-'+src.source_id+'-'+src.revision_id.toUpperCase();
  function b1PackageFor(src){
    return sourcePackages.find(p=>p.source_id===src.source_id&&p.revision_id===src.revision_id);
  }
  async function validateB1Source(src){
    const expected=b1Manifest(src);
    const result=await apiOps('/v1/tpa/source-packages/validate',{
      method:'POST',body:JSON.stringify(expected)});
    if(result.normalized_manifest?.canonical_document_sha256!==src.canonical_document_sha256)
      throw Error('服务端来源版本摘要不匹配，禁止登记');
    packageValidation={key:src.source_id+':'+src.revision_id,receipt:result};
    notify({b1_validation:result.status,manifest_sha256:result.manifest_sha256,
      unit_count:result.structure_index?.length,scientific_capture:false});
    render();
  }
  async function registerB1Source(src){
    const key=src.source_id+':'+src.revision_id;
    if(role()!=='producer'||packageValidation?.key!==key)
      throw Error('请先由 Producer 校验准确的合成来源版本');
    const manifest=b1Manifest(src),package_id=b1PackageId(src);
    const intent={...manifest,package_id};
    const idempotency_key=operationKey('source-package',key,intent);
    let registered;
    try{
      registered=await apiOps('/v1/tpa/source-packages',{
        method:'POST',body:JSON.stringify({...intent,idempotency_key})});
    }catch(err){
      let existing=null;
      try{existing=(await apiOps('/v1/tpa/source-packages/'+encodeURIComponent(package_id))).package}catch{}
      const verified=existing&&existing.source_id===src.source_id&&
        existing.revision_id===src.revision_id&&
        existing.canonical_document_sha256===src.canonical_document_sha256&&
        existing.manifest_sha256===packageValidation.receipt.manifest_sha256;
      if(!verified)throw err;
      registered={package:existing,reconciled_after_uncertain_response:true};
    }
    resolveIntent('source-package',key);
    notify({b1_registration:registered.package.status,
      package_id:registered.package.package_id,
      manifest_sha256:registered.package.manifest_sha256,
      reconciled_after_uncertain_response:!!registered.reconciled_after_uncertain_response,
      scientific_capture:false,gold_qualification:'NOT_ELIGIBLE'});
    packageValidation=null;
    await loadSourcePackages();
    render();
  }
  function renderSourceLibrary(){
    const page=frame('科学资料库 · 合成 Source Packages',
      '结构化来源包引用原 EA 已有版本；只管理元数据、来源谱系与校验摘要，不在管理端复制原文。');
    page.id='p11SourcesPage';
    page.append(notice('B1 为合成参考包操作。真实 PDF、MinerU、Markdown/HTML 导入、版权审核和临床资料均未开放。登记包 ≠ 来源科学合格 / Gold。'));
    const stats=e('div',undefined,'p11-source-stats');
    stats.append(e('span',`权威合成来源：${sourceData.length} 个`),
      e('span',`已登记引用包：${sourcePackages.length} 个`),
      e('span','真实来源准入：NO-GO'));
    page.append(stats);
    const columns=e('div',undefined,'p11-source-layout');
    const left=e('section',undefined,'p11-panel');
    left.append(e('h3','① 已存在的来源与版本'));
    const sourceList=e('div',undefined,'p11-source-rows');sourceList.id='b1SourceRows';
    for(const src of sourceData){
      const key=src.source_id+':'+src.revision_id,pkg=b1PackageFor(src);
      const row=e('article',undefined,'p11-source-entry');
      if(key===sourceSelection)row.classList.add('selected');
      row.append(e('strong',src.title),e('p',src.source_id+' / '+src.revision_id+' · '+src.source_type,'p11-meta'));
      row.append(e('span',pkg?'已登记 · 仅合成':'待登记 · 仅合成','p11-package-status'));
      const view=button('查看版本',()=>{
        sourceSelection=key;packageValidation=null;
        const hash=hashFor('sources',project,batch);
        if(location.hash!==hash)history.pushState({p11:'source'},'',hash);
        render();
      });
      view.setAttribute('aria-pressed',key===sourceSelection?'true':'false');
      row.append(view);sourceList.append(row);
    }
    left.append(sourceList);columns.append(left);
    const right=e('section',undefined,'p11-panel');right.id='b1VersionDetail';
    const selected=sourceData.find(src=>src.source_id+':'+src.revision_id===sourceSelection);
    if(!selected){
      right.append(notice('请先选择一份合成来源。'));
    }else{
      const pkg=b1PackageFor(selected);
      right.append(e('h3','② 来源版本与结构包'));
      right.append(e('h4',selected.title));
      const facts=[
        ['Source / Revision',selected.source_id+' / '+selected.revision_id],
        ['来源类型',selected.source_type],['Scientific Profile',selected.profile_id],
        ['可用时间',selected.available_at],['原文权限',selected.rights_status],
        ['文档权威 SHA-256',selected.canonical_document_sha256],
        ['上游谱系','EA_SEEDED_FIXTURE → '+selected.source_id+' / '+selected.revision_id]
      ];
      const grid=e('dl',undefined,'p11-source-facts');
      for(const [label,value] of facts){grid.append(e('dt',label),e('dd',value||'—'))}
      right.append(grid);
      const status=e('div',undefined,'p11-package-info');status.id='b1PackageStatus';
      if(pkg){
        status.append(e('h4','已登记不可变 Source Package'));
        status.append(e('p',pkg.package_id+' · '+pkg.status,'p11-meta'));
        status.append(e('p','包 Manifest SHA-256：'+pkg.manifest_sha256,'p11-meta'));
        status.append(e('p','结构索引 SHA-256：'+pkg.structure_sha256,'p11-meta'));
        status.append(e('p','谱系：'+pkg.lineage.upstream+' → '+pkg.revision_id,'p11-meta'));
        const table=e('table',undefined,'p11-structure-table');
        const heading=e('tr');for(const label of ['序号','位置锚点','类型','UTF-16 长度','文本摘要']){
          const th=e('th',label);th.scope='col';heading.append(th)}
        const thead=e('thead');thead.append(heading);table.append(thead);
        const tbody=e('tbody');
        for(const unit of pkg.structure_index||[]){
          const tr=e('tr');
          for(const value of [unit.ordinal+1,unit.unit_id,unit.element_kind,unit.utf16_length,unit.unit_text_sha256])
            tr.append(e('td',value));
          tbody.append(tr);
        }
        table.append(tbody);
        const scroll=e('div',undefined,'p11-source-structure-scroll');scroll.append(table);status.append(scroll);
        status.append(notice('仅展示定位符、长度和摘要；全文及原文引用仍在原 D0 专家阅读器内，且必须经过任务授权。'));
      }else{
        status.append(notice('此版本尚未登记来源包，但仍是现有 EA 合成来源；B1 不会改变旧任务的可用性。'));
        if(packageValidation?.key===sourceSelection){
          const validated=packageValidation.receipt;
          status.append(e('p','已校验：'+validated.status+' · '+validated.structure_index.length+
            ' 个结构单元 · Manifest SHA '+validated.manifest_sha256,'p11-meta'));
        }
        if(role()==='producer'){
          const actions=e('div',undefined,'p11-row');
          const validate=button('校验结构化来源包',()=>validateB1Source(selected).catch(catchMessage),'secondary');
          validate.id='b1ValidatePackage';actions.append(validate);
          const register=button('登记不可变合成来源包',()=>registerB1Source(selected).catch(catchMessage),'primary');
          register.id='b1RegisterPackage';register.disabled=packageValidation?.key!==sourceSelection;
          actions.append(register);status.append(actions);
        }else status.append(notice('Manager 仅可查看；校验和登记必须由独立 Producer 会话执行。'));
      }
      right.append(status);
      const taskNav=button('前往任务中心选择此版本',()=>{
        navigate('tasks');$p('primarySource').value=selected.source_id+':'+selected.revision_id;
        if(typeof showSourceInfo==='function')showSourceInfo();
      });
      right.append(taskNav);
    }
    columns.append(right);page.append(columns);
    const caution=e('section',undefined,'p11-panel');
    caution.append(e('h3','③ MinerU / HTML / Markdown 上游适配边界'));
    caution.append(notice('规划契约：外部解析 → canonical source units + stable unit IDs → source SHA / structure digest → 版本验证 → 权限及科研来源资格审核。当前 B1 只接受 EA 中已登记的 SYNTHETIC_FIXTURE 引用，不接收上传文件或解析结果。'));
    caution.append(button('打开 P2 科学资料准备预览',()=>navigate('studio'),'secondary'));
    page.append(caution);
    return page;
  }
  function renderPlaceholder(){
    const page=frame(labels[active],'本期 P1.1-A 的功能范围与下一阶段接口。');
    const p=e('article',undefined,'p11-panel');p.append(e('h3','尚未在 P1.1-A 开放完整功能'));
    const lines={sources:'真实来源导入、MinerU 与来源质量审核属于 P2。当前任务生产仅使用七类虚构合成来源。',
      agent:'仅支持 P1 已有的固定合成候选；没有真实模型执行或运行追踪。',
      experts:'正式专家资格、伦理、冲突及跨组盲法资格仍需 P3 审核；目前仅模拟固定测试账号。',
      quality:'完整质量指标与审计导出将在后续阶段建设；本期只展示真实任务状态聚合，Gold 不在此生成。',
      audit:'原 /v1/tpa/audit 只向审计员提供；此管理会话不通过面板绕过独立审计角色授权。'};
    p.append(notice(lines[active]||''));p.append(button('回到任务中心',()=>go('tasks')));page.append(p);return page;
  }
  function renderSelector(){
    const old=$p('p11FormPlacement');if(old)old.remove();
    const form=$p('taskForm');if(!form)return;
    const fieldset=form.querySelector('fieldset');
    const p=e('div',undefined,'p11-form-placement');p.id='p11FormPlacement';
    p.append(e('h3','任务归属 · 必须先选择项目与批次'));
    p.append(select('p11FormProject',projects.map(x=>[x.project_id,x.name]),project,v=>{
      navigate('tasks',v,'');fetchViews().then(render).catch(catchMessage);},'请选择项目'));
    p.append(select('p11FormBatch',(batchMap.get(project)||[]).map(x=>[x.batch_id,x.label]),batch,v=>{navigate('tasks',project,v);fetchViews().then(render).catch(catchMessage);},'请选择批次'));
    fieldset.prepend(p);
  }
  function renderWizard(){
    const box=$p('p11WizardNav');if(!box)return;
    clear(box);
    const words=['① 选择资料','② 定义任务','③ 验证冻结','④ 准备工作包','⑤ 分配发布'];
    for(let i=0;i<5;i++){
      const b=button(words[i],()=>{wizardStep=i+1;renderWizard()},wizardStep===i+1?'primary':'secondary');
      b.classList.add('p11-wizard-step');
      b.setAttribute('aria-current',wizardStep===i+1?'step':'false');
      box.append(b);
    }
    const form=$p('taskForm');if(!form)return;
    const parts=[...form.querySelectorAll('fieldset')];
    parts[0].hidden=wizardStep!==1;parts[1].hidden=wizardStep!==2;parts[2].hidden=wizardStep!==2;
    let info=$p('p11WizardInfo');
    if(!info){info=e('div',undefined,'p11-step-info p11-step-card');info.id='p11WizardInfo';form.after(info);}
    clear(info);
    const current=managedTasks.find(x=>x.task_id===selectedTaskId)||
      (selectedTaskMeta?.task_id===selectedTaskId?selectedTaskMeta:null);
    if(current&&wizardStep>=3){
      info.append(e('h3','当前办理：'+selectedTaskId));
      info.append(e('p','服务端最近已知状态：'+(stateLabel[current.state]||current.state),'p11-meta'));
      info.append(e('p','原始资料仍由获授权专家端读取；此处仅处理任务运营状态。','p11-meta'));
    }
    const nextStep=(n,label)=>button(label,()=>{wizardStep=n;renderWizard()},'primary');
    const send=(kind,label)=>button(label,()=>{
      if(!current||!window.opsTaskAction)return;
      window.opsTaskAction(current.task_id,kind,current.workflow_strategy);
    },'primary');
    if(wizardStep===1){
      info.append(notice('S1：只选择已登记的合成来源及准确版本；不会读取原文或创建 Gold。'));
      if(role()==='producer')info.append(nextStep(2,'下一步：定义任务'));
    }else if(wizardStep===2){
      info.append(notice(role()==='producer'?
        'S2：选择 Project / Batch、模式、Profile、截止时间，再提交合成草稿；不可原位更改冻结定义。':
        'Manager 不具备创建任务权限。请在任务表格选择已准备的任务。'));
    }else if(!current){
      info.append(notice('先从下方任务表选择“继续办理”；未选择任务时不会执行任何状态变更。'));
    }else if(wizardStep===3){
      if(current.state==='DRAFT'&&role()==='producer')info.append(send('validate','S3 · 检查资料与任务'));
      else if(current.state==='VALIDATED'&&role()==='producer')info.append(send('freeze','S3 · 冻结任务定义'));
      else if(['DEFINITION_FROZEN','READY_FOR_ASSIGNMENT','ASSIGNED','PUBLISHED','REVOKED'].includes(current.state))
        info.append(notice('任务定义已冻结，不能原位修改。'));
      else info.append(notice('验证和冻结只允许任务生产者执行；请更换获授权会话。'));
      if(['DEFINITION_FROZEN','READY_FOR_ASSIGNMENT','ASSIGNED','PUBLISHED'].includes(current.state))
        info.append(nextStep(4,'下一步：准备工作包'));
    }else if(wizardStep===4){
      if(current.state==='DEFINITION_FROZEN'&&role()==='producer')
        info.append(send('prepare','S4 · 准备工作包'));
      else if(['READY_FOR_ASSIGNMENT','ASSIGNED','PUBLISHED'].includes(current.state)){
        info.append(notice('工作包已准备：Agent 模式仅为预置合成候选；独立专家模式完全禁止候选暴露。'));
        info.append(nextStep(5,'下一步：分配与发布'));
      }else info.append(notice('此状态不可准备工作包；需先验证并冻结，且由 Producer 执行。'));
    }else{
      if(current.state==='READY_FOR_ASSIGNMENT'&&role()==='manager')
        info.append(send('assign','S5 · 分配匹配模式的合成专家'));
      else if(current.state==='READY_FOR_ASSIGNMENT')
        info.append(notice('工作包已准备；需要独立 Manager 会话才能分配合成专家和发布。'));
      else if(current.state==='ASSIGNED'&&role()==='manager')
        info.append(send('publish','S5 · 授权发布任务'));
      else if(current.state==='PUBLISHED')
        info.append(notice('服务端确认已发布，不代表专家已打开、阅读、理解或完成评审。'));
      else if(current.state==='REVOKED')
        info.append(notice('未来访问已经撤销；既有暴露记录不得删除。'));
      else info.append(notice('需先准备工作包；仅 Manager 能分配和发布。'));
      if(['ASSIGNED','PUBLISHED','REVOKED'].includes(current.state)){
        info.append(button('查看专家交接与版本信息',()=>window.opsTaskDetail(current.task_id)));
      }
    }
  }
  async function reload(){
    if(!auth)return;
    if(loadingPromise){
      // Never silently drop a refresh after a server-committed assignment/publish.
      reloadRequested=true;
      return loadingPromise;
    }
    loadingPromise=(async()=>{
      do {
        reloadRequested=false;
        await loadProjects();await fetchViews();await loadSourcePackages();
        if(active==='agent')await window.opsB2Refresh?.();
        if(active==='experts')await window.opsB3Refresh?.();
        renderSelector();render();
        const deep=readRoute().task;
        if(deep)await window.opsTaskDetail(deep,false);
      }while(reloadRequested&&auth);
    })();
    try {await loadingPromise;}
    finally{loadingPromise=null;}
  }
  function setWizardOpen(open){
    wizardOpen=!!open;
    const panel=$p('p11WizardPanel');
    if(panel)panel.hidden=!wizardOpen;
    document.body.classList.toggle('p11-wizard-open',wizardOpen);
    if(wizardOpen){
      renderSelector();renderWizard();
      $p('p11WizardClose')?.focus();
    }
  }
  function render(){
    active=routes.includes(active)?active:'overview';
    document.body.dataset.p11View=active;
    const separate=active!=='tasks';
    $p('p11View').hidden=!separate;
    $p('p11TaskView').hidden=separate;
    const nav=$p('p11Nav');
    for(const item of nav.querySelectorAll('button[data-p11-route]')){
      // Demo: keep 任务中心 highlighted while browsing nested 项目与批次.
      const onTasksFamily=active==='tasks'||active==='projects';
      const current=(item.dataset.p11Route===active)||(item.dataset.p11Route==='tasks'&&onTasksFamily&&active==='projects');
      item.setAttribute('aria-current',current?'page':'false');
    }
    $p('p11SectionTitle').textContent=labels[active];
    if(active!=='tasks')setWizardOpen(false);
    if(separate){clear($p('p11View'));$p('p11View').append(active==='overview'?renderOverview():active==='projects'?renderProjects():active==='sources'?renderSourceLibrary():active==='studio'&&window.p2SourceStudio?window.p2SourceStudio.render({role:role(),scope:{project,batch},projects,batchMap}):active==='agent'&&window.opsB2Render?window.opsB2Render():active==='experts'&&window.opsB3Render?window.opsB3Render():renderPlaceholder());}
    else{renderTaskToolbar();renderSelector();renderWizard();}
  }
  function go(view){
    navigate(view);
    if(view==='agent')window.opsB2Refresh?.().then(render).catch(catchMessage);
    if(view==='experts')window.opsB3Refresh?.().then(render).catch(catchMessage);
  }
  function projectName(id){
    return projects.find(p=>p.project_id===id)?.name || id;
  }
  function batchName(projectId,batchId){
    return (batchMap.get(projectId)||[]).find(b=>b.batch_id===batchId)?.label || batchId;
  }
  function renderBreadcrumb(){
    const nav=$p('p11Breadcrumb');if(!nav)return;clear(nav);
    const crumbs=[['全部项目','','' ]];
    if(project)crumbs.push([projectName(project),project,'']);
    if(project&&batch)crumbs.push([batchName(project,batch),project,batch]);
    crumbs.push(['任务',project,batch]);
    crumbs.forEach((item,index)=>{
      if(index)nav.append(e('span','›','p11-crumb-sep'));
      const last=index===crumbs.length-1;
      if(last){
        const current=e('span',item[0],'p11-crumb-current');
        current.setAttribute('aria-current','page');
        nav.append(current);
      }else{
        nav.append(button(item[0],()=>{
          if(!item[1]){chooseScope('','').catch(catchMessage);return;}
          chooseScope(item[1],item[2]||'').catch(catchMessage);
        },'p11-crumb'));
      }
    });
  }
  function startNewTask(){
    if(role()!=='producer'){notify('只有 Producer 可以创建任务');return;}
    selectedTaskId='';selectedTaskMeta=null;wizardStep=1;
    setWizardOpen(true);renderWizard();
    $p('primarySource')?.focus();
  }
  function resetTaskFilters(){
    project='';batch='';search='';legacyOnly=false;pageOffset=0;stateScope='';modeScope='';
    if($p('stateFilter'))$p('stateFilter').value='';
    navigate('tasks','','');
    fetchViews().then(()=>{renderTaskToolbar();renderWizard()}).catch(catchMessage);
  }
  function renderTaskToolbar(){
    let bar=$p('p11TaskToolbar');if(!bar)return;clear(bar);
    renderBreadcrumb();
    const shortcut=$p('p11ProjectsShortcut');
    if(shortcut&&!shortcut.dataset.bound){
      shortcut.dataset.bound='1';
      shortcut.addEventListener('click',()=>go('projects'));
    }
    const q=e('label',undefined,'p11-search');q.append(e('span','任务搜索'));
    const input=e('input');input.id='p11TaskSearch';input.placeholder='搜索任务编号，例如 TPA-SYN';input.value=search;
    input.setAttribute('aria-label','搜索任务编号');
    let searchTimer=null;
    input.addEventListener('input',ev=>{
      search=ev.target.value.trim();pageOffset=0;
      if(searchTimer)clearTimeout(searchTimer);
      searchTimer=setTimeout(()=>fetchViews().then(()=>{renderTasks()}).catch(catchMessage),250);
    });q.append(input);bar.append(q);
    const label=e('label');label.append(e('span','项目'));label.append(select('p11TaskProject',projects.map(p=>[p.project_id,p.name]),project,
      v=>chooseScope(v).catch(catchMessage),'全部项目与 Legacy'));bar.append(label);
    const b=e('label');b.append(e('span','批次'));
    b.append(select('p11TaskBatch',project?(batchMap.get(project)||[]).map(x=>[x.batch_id,x.label]):
      projects.flatMap(p=>(batchMap.get(p.project_id)||[]).map(x=>[x.batch_id,x.label])),
      v=>{
        if(!v){chooseScope(project,'').catch(catchMessage);return;}
        if(project){chooseScope(project,v).catch(catchMessage);return;}
        const owner=projects.find(p=>(batchMap.get(p.project_id)||[]).some(x=>x.batch_id===v));
        chooseScope(owner?.project_id||'',v).catch(catchMessage);
      },'全部批次'));bar.append(b);
    // Keep the original #stateFilter node (bound by tpa_manage.js) in Demo toolbar order.
    const stateWrap=$p('stateFilter')?.closest('label');
    if(stateWrap){
      if($p('stateFilter'))$p('stateFilter').value=stateScope||'';
      bar.append(stateWrap);
    }
    const mode=e('label');mode.append(e('span','工作模式'));
    mode.append(select('p11ModeFilter',[
      ['AGENT_PROPOSE_EXPERT_VERIFY','Agent 复核'],
      ['HUMAN_INDEPENDENT','独立标注']
    ],modeScope,v=>{modeScope=v;pageOffset=0;fetchViews().then(()=>{renderTasks()}).catch(catchMessage);},'全部工作模式'));
    bar.append(mode);
    if(!project){
      const legacy=button(legacyOnly?'显示全部任务':'仅显示 Legacy 任务',()=>{
        legacyOnly=!legacyOnly;pageOffset=0;fetchViews().then(()=>{renderTaskToolbar();renderWizard()}).catch(catchMessage);
      },legacyOnly?'primary':'secondary');
      legacy.id='p11LegacyToggle';bar.append(legacy);
    }
    const reset=button('重置',resetTaskFilters,'secondary');reset.id='p11ResetFilters';bar.append(reset);
    const cta=$p('p11NewTaskCta');
    if(cta){
      cta.hidden=role()!=='producer';
      if(!cta.dataset.bound){cta.dataset.bound='1';cta.addEventListener('click',startNewTask);}
    }
    renderTasks();
  }
  const taskOperations={
    DRAFT:['validate','检查资料与任务','producer'],
    VALIDATED:['freeze','冻结任务定义','producer'],
    DEFINITION_FROZEN:['prepare','准备工作包','producer'],
    READY_FOR_ASSIGNMENT:['assign','分配合成专家','manager'],
    ASSIGNED:['publish','授权发布任务','manager']
  };
  const stageFor=state=>({DRAFT:3,VALIDATED:3,DEFINITION_FROZEN:4,
    READY_FOR_ASSIGNMENT:5,ASSIGNED:5,PUBLISHED:5,REVOKED:5})[state]||3;
  function stateChip(state){
    const wrap=e('span',undefined,'p11-state-tag '+(stateClass[state]||''));
    wrap.title=state;
    wrap.append(e('span',stateLabel[state]||state,'p11-state-zh'));
    wrap.append(e('span',state,'p11-state-code'));
    return wrap;
  }
  function continueTask(row){
    selectedTaskId=row.task_id;selectedTaskMeta=row;
    wizardStep=stageFor(row.state);
    setWizardOpen(true);renderWizard();
    $p('p11WizardNav')?.scrollIntoView({block:'nearest'});
  }
  window.opsRenderTaskTable=(container,act)=>{
    clear(container);
    const summary=e('p',`服务端筛选结果：${pageTotal} 项，当前第 ${Math.floor(pageOffset/pageSize)+1} 页；`+
      '发布不代表专家已打开、阅读或提交。','p11-meta');
    container.append(summary);
    const wrap=e('div',undefined,'p11-table-scroll');
    wrap.setAttribute('role','region');wrap.setAttribute('aria-label','可横向滚动的合成任务表格');
    wrap.tabIndex=0;
    const table=e('table',undefined,'p11-task-table');
    const head=e('thead');const header=e('tr');
    const columns=['任务编号','项目 / 批次','来源类型','工作模式','阶段状态','下一步',''];
    for(const title of columns){
      const th=e('th',title);th.scope='col';header.append(th);
    }
    head.append(header);table.append(head);
    const body=e('tbody');
    const rows=managedTasks;
    if(!rows.length){
      const tr=e('tr');const td=e('td','当前范围没有符合条件的合成任务。可重置筛选，或新建合成任务。');
      td.colSpan=columns.length;tr.append(td);body.append(tr);
    }
    for(const task of rows){
      const tr=e('tr',undefined,'task-row');
      const idCell=e('td',undefined,'p11-code');
      idCell.append(e('div',task.task_id));
      idCell.append(e('div','revision · '+(task.task_revision_id||'未记录')+' · '+(task.profile_id||''),'small-muted'));
      tr.append(idCell);
      tr.append(e('td',task.legacy?'Legacy · 未归档':(task.project_id||'—')+' / '+(task.batch_id||'—'),'p11-scope-cell'));
      const src=task.primary_source||{};
      tr.append(e('td',`${task.source_type||'—'} · ${src.source_id||'—'} / ${src.revision_id||'—'}`));
      const mode=e('td');
      mode.append(e('span',task.workflow_strategy==='HUMAN_INDEPENDENT'?'专家独立标注':'Agent 候选复核',
        'strategy '+(task.workflow_strategy==='HUMAN_INDEPENDENT'?'independent':'agent')));
      tr.append(mode);
      const status=e('td');status.append(stateChip(task.state));tr.append(status);
      const next=taskOperations[task.state];
      const nextLabel=next
        ?(role()===next[2]?next[1]:`下一步需 ${next[2]}`)
        :(task.state==='PUBLISHED'?'查看详情 / 必要时撤销':task.state==='REVOKED'?'只读留痕':'查看详情');
      tr.append(e('td',nextLabel,'p11-next-cell'));
      const controls=e('td');const menu=e('div',undefined,'p11-row-actions');
      menu.append(button('查看任务详情',()=>window.opsTaskDetail(task.task_id)));
      menu.append(button('继续办理',()=>continueTask(task)));
      if(next&&role()===next[2]){
        // Producer preparation stays in the Demo wizard; manager assign/publish
        // remain list-first so the modal does not intercept table clicks.
        if(next[2]==='producer'){
          menu.append(button(next[1],()=>{continueTask(task);act(task.task_id,next[0],task.workflow_strategy)},'primary'));
        }else{
          menu.append(button(next[1],()=>{
            selectedTaskId=task.task_id;selectedTaskMeta=task;setWizardOpen(false);
            act(task.task_id,next[0],task.workflow_strategy);
          },'primary'));
        }
      }
      if(role()==='manager'&&['ASSIGNED','PUBLISHED'].includes(task.state)){
        menu.append(button('撤销未来访问权限',()=>{
          if(window.confirm('撤销不会删除已经记录的历史暴露。确定撤销未来访问吗？'))
            act(task.task_id,'revoke',task.workflow_strategy);
        }));
      }
      if(task.state==='PUBLISHED'){
        menu.append(button('专家交接说明',()=>window.opsTaskDetail(task.task_id)));
      }
      controls.append(menu);tr.append(controls);body.append(tr);
    }
    table.append(body);wrap.append(table);container.append(wrap);
    const pager=e('div',undefined,'p11-pagination');
    pager.append(e('span',`显示 ${pageTotal? pageOffset+1:0}–${Math.min(pageOffset+managedTasks.length,pageTotal)} / ${pageTotal}`));
    const previous=button('上一页',()=>{pageOffset=Math.max(0,pageOffset-pageSize);fetchViews().then(()=>{renderTaskToolbar()}).catch(catchMessage)});
    previous.disabled=pageOffset===0;pager.append(previous);
    const next=button('下一页',()=>{pageOffset+=pageSize;fetchViews().then(()=>{renderTaskToolbar()}).catch(catchMessage)});
    next.disabled=pageOffset+pageSize>=pageTotal;pager.append(next);
    container.append(pager);
  };
  window.opsA5StateChanged=value=>{
    stateScope=value;pageOffset=0;fetchViews().then(()=>{renderTasks();renderWizard()}).catch(catchMessage);
  };
  window.opsVisibleTasks = rows => rows.filter(t=>(!project||managedTasks.some(x=>x.task_id===t.task_id))&&(!legacyOnly||managedTasks.some(x=>x.task_id===t.task_id&&x.legacy))&&(!search||t.task_id.toLowerCase().includes(search.toLowerCase())));
  window.opsLegacyTask=taskId=>managedTasks.some(t=>t.task_id===taskId&&t.legacy===true);
  window.opsDraftCreate=async body=>{
    if(!project||!batch)throw Error('请先在“项目与批次”创建或选择项目与批次');
    const intent={...body,project_id:project,batch_id:batch};
    const key=operationKey('draft',body.task_id,intent);
    let result;
    try{
      result=await apiOps('/v1/tpa/tasks/in-batch',{method:'POST',body:JSON.stringify({
        ...intent,idempotency_key:key
      })});
    }catch(err){
      // Do not assume network failure == rollback; confirm by exact server task ID.
      let existing=null;
      try{existing=await apiOps('/v1/tpa/tasks/'+encodeURIComponent(body.task_id)+'/management')}catch{}
      const same=existing&&existing.task_id===body.task_id&&
        existing.placement?.project_id===project&&existing.placement?.batch_id===batch&&
        existing.profile_id===body.profile_id&&existing.knowledge_cutoff===body.knowledge_cutoff&&
        existing.workflow_strategy===body.workflow_strategy&&
        JSON.stringify(existing.primary_source)===JSON.stringify(body.primary_source)&&
        JSON.stringify(existing.allowed_source_versions)===JSON.stringify(body.allowed_source_versions);
      if(!same)throw err; // ID alone never authorizes treating an unrelated task as our transaction.
      result={task:existing,state:existing.state,placement:existing.placement,
              reconciled_after_uncertain_response:true};
    }
    resolveIntent('draft',body.task_id);
    selectedTaskId=body.task_id;selectedTaskMeta={...intent,task_id:body.task_id,state:result.state};
    legacyOnly=false;wizardStep=3;return result;
  };
  window.opsAfterDraft=id=>{selectedTaskId=id;wizardStep=3;setWizardOpen(true);renderWizard()};
  window.opsAfterTaskAction=(id,action,result)=>{
    selectedTaskId=id;
    if(selectedTaskMeta?.task_id===id)selectedTaskMeta.state=result.state;
    if(action==='freeze')wizardStep=4;
    if(action==='prepare')wizardStep=5;
    if(['validate','freeze','prepare'].includes(action))setWizardOpen(true);
    renderWizard();
  };
  window.opsClear=()=>{projects=[];batchMap=new Map();overview=null;managedTasks=[];project='';batch='';search='';wizardStep=1;active='overview';window.opsPreparingFilter=false;legacyOnly=false;pageOffset=0;pageTotal=0;selectedTaskId='';selectedTaskMeta=null;stateScope='';modeScope='';wizardOpen=false;sourcePackages=[];sourceSelection='';packageValidation=null;
    if($p('p11WizardPanel'))$p('p11WizardPanel').hidden=true;
    document.body.classList.remove('p11-wizard-open');
    window.opsB2Clear?.();
    window.opsB3Clear?.();
    if($p('p11View'))clear($p('p11View'));
    if($p('p11Detail')){$p('p11Detail').hidden=true;clear($p('p11Detail'));}
    if($p('p11ModalOverlay')){$p('p11ModalOverlay').hidden=true;clear($p('p11ModalOverlay'));}
    if($p('receipt'))$p('receipt').textContent='仅供合成工程验收。尚无操作。';
  };
  window.opsRefresh=reload;
  function hideDetail(returnFocus=true){
    const box=$p('p11Detail');if(!box)return;
    box.hidden=true;clear(box);
    if(returnFocus&&drawerReturnFocus?.isConnected)drawerReturnFocus.focus();
    if(location.hash!==hashFor('tasks',project,batch))location.hash=hashFor('tasks',project,batch);
  }
  window.opsTaskDetail=async (taskId,recordRoute=true)=>{
    try {
      const detail=await apiOps('/v1/tpa/tasks/'+encodeURIComponent(taskId)+'/management');
      selectedTaskId=detail.task_id;selectedTaskMeta=detail;
      wizardStep=stageFor(detail.state);renderWizard();
      if(recordRoute && TASK_PATTERN.test(taskId)){
        drawerReturnFocus=document.activeElement;
        const h=hashFor('tasks',project,batch,taskId);
        if(location.hash!==h)history.pushState({p11:'task'},'',h);
      }
      const box=$p('p11Detail');clear(box);box.hidden=false;
      box.setAttribute('role','dialog');box.setAttribute('aria-modal','false');
      box.setAttribute('aria-labelledby','p11DetailTitle');box.tabIndex=-1;
      const hdr=e('div',undefined,'p11-drawer-header');
      const title=e('h3','任务详情 · '+detail.task_id);title.id='p11DetailTitle';
      const close=button('关闭详情',()=>hideDetail());
      hdr.append(title,close);box.append(hdr);
      box.append(e('p','运营状态：'+(stateLabel[detail.state]||detail.state),'p11-meta'));
      box.append(e('p','项目 / 批次：'+(detail.placement?detail.placement.project_id+' / '+detail.placement.batch_id:'Legacy · 未归属'),'p11-meta'));
      box.append(e('p','Profile：'+detail.profile_id,'p11-meta'));
      box.append(e('p','工作模式：'+(detail.workflow_strategy==='HUMAN_INDEPENDENT'?'独立专家 · 不允许 Agent 候选':'Agent 候选复核 · 仅合成 fixture'),'p11-meta'));
      box.append(e('p','知识截止（UTC）：'+detail.knowledge_cutoff,'p11-meta'));
      const sourceSection=e('section',undefined,'p11-drawer-section');
      sourceSection.append(e('h4','不可变授权来源版本'));
      for(const v of detail.allowed_source_versions||[]){
        const item=e('div',undefined,'p11-drawer-source');
        item.append(e('strong',v.source_id+' / '+v.revision_id));
        item.append(e('code',v.canonical_document_sha256));
        sourceSection.append(item);
      }
      box.append(sourceSection);
      const next=e('section',undefined,'p11-drawer-section');
      next.append(e('h4','服务端允许的下一步'));
      next.append(e('p',(detail.next_action||'无')+' · 权限与状态以服务器再次核验为准。','p11-meta'));
      const step=taskOperations[detail.state];
      if(step&&role()===step[2]){
        next.append(button(step[1],()=>window.opsTaskAction(detail.task_id,step[0],detail.workflow_strategy),'primary'));
      }
      if(role()==='manager'&&['ASSIGNED','PUBLISHED'].includes(detail.state)){
        next.append(button('撤销未来访问权限',()=>{
          if(window.confirm('撤销不会清除专家已经看过材料的历史记录。确定继续？'))
            window.opsTaskAction(detail.task_id,'revoke',detail.workflow_strategy);
        }));
      }
      box.append(next);
      const handoff=e('section',undefined,'p11-drawer-section p11-handoff');
      handoff.append(e('h4','专家端安全交接'));
      if(detail.state==='PUBLISHED'){
        const alias=detail.workflow_strategy==='HUMAN_INDEPENDENT'?'ea2':'ea1';
        handoff.append(notice('已发布合成任务。请在独立浏览器资料或无痕窗口使用已授权的 '+alias+
          ' 测试账号登录原 D0 专家界面，再在“科学证据任务”中选择该 Task ID。不得复用当前管理端会话。'));
        const link=e('a','打开原 D0 专家入口（另开独立会话）');
        link.href='/';link.target='_blank';link.rel='noopener noreferrer';link.className='p11-btn';
        handoff.append(link);
        handoff.append(e('p','任务编号：'+detail.task_id+' · 仅在服务端授权后可读取对应版本','p11-meta'));
        handoff.append(e('p','已发布 ≠ 已打开 ≠ 已阅读 ≠ 已提交复核。此处没有专家行为证明。','p11-meta'));
      }else if(detail.state==='REVOKED'){
        handoff.append(notice('该任务已撤销未来访问。既有暴露日志保留，不能声称从未被阅读。'));
      }else{
        handoff.append(notice('该任务尚未正式发布给合成专家。不能提前访问原始资料或候选。'));
      }
      box.append(handoff);
      box.append(notice('管理投影不包含原文 units、候选 payload、专家判断或 Gold；scientific_capture=false / NOT_ELIGIBLE。'));
      box.focus();
    }catch(err){catchMessage(err)}
  };

  function modal(type){
    if(role()!=='producer')return;
    const overlay=$p('p11ModalOverlay');clear(overlay);overlay.hidden=false;
    const form=e('form',undefined,'p11-modal');
    const title=type==='project'?'新建合成项目':'新建合成运营批次';
    form.append(e('h3',title),notice('只填写合成运营描述，不要写入患者资料、文献原文或科学答案。'));
    if(type==='project'){
      form.append(field('项目名称','opsName',100,'例如：Evidence QA Sprint'));
      form.append(field('说明（可选）','opsDesc',500,'运营组织描述'));
    }else{
      form.append(field('批次名称','opsName',100,'例如：Calibration Sprint'));
      form.append(field('用途（可选）','opsDesc',500,'仅做运营管理'));
    }
    const row=e('div',undefined,'p11-row');
    row.append(button('取消',()=>{overlay.hidden=true}));
    const submit=e('button','确认创建','p11-btn primary');submit.type='submit';row.append(submit);form.append(row);
    form.addEventListener('submit',async ev=>{
      ev.preventDefault();submit.disabled=true;
      try{
        const name=$p('opsName').value.trim(),description=$p('opsDesc').value.trim();
        let result;
        if(type==='project'){
          result=await apiOps('/v1/tpa/projects',{method:'POST',body:JSON.stringify({
            project_id:fresh('PRJ-SYN-'),name,description,idempotency_key:crypto.randomUUID()})});
          project=result.project_id;batch='';navigate('projects',project,'');
        }else{
          result=await apiOps('/v1/tpa/projects/'+encodeURIComponent(project)+'/batches',{
            method:'POST',body:JSON.stringify({batch_id:fresh('BATCH-SYN-'),label:name,purpose:description,idempotency_key:crypto.randomUUID()})});
          batch=result.batch_id;navigate('projects',project,batch);
        }
        overlay.hidden=true;notify(result);await reload();
      }catch(err){catchMessage(err);submit.disabled=false;}
    });
    overlay.append(form);setTimeout(()=>form.querySelector('input')?.focus(),0);
  }
  document.addEventListener('DOMContentLoaded',()=>{
    const nav=$p('p11Nav');if(!nav)return;
    nav.addEventListener('click',ev=>{
      const item=ev.target.closest('button[data-p11-route]');if(item)go(item.dataset.p11Route);
    });
    $p('p11WizardClose')?.addEventListener('click',()=>setWizardOpen(false));
    document.addEventListener('keydown',ev=>{
      if(ev.key!=='Escape')return;
      if($p('p11ModalOverlay')&&!$p('p11ModalOverlay').hidden)$p('p11ModalOverlay').hidden=true;
      else if(wizardOpen)setWizardOpen(false);
      else if($p('p11Detail')&&!$p('p11Detail').hidden)hideDetail();
    });
    const replayRoute=()=>{
      const r=readRoute();
      const changed=(project!==r.p||batch!==r.b);
      active=r.view;project=r.p;batch=r.b;
      if(r.view==='sources'){
        sourceSelection=r.source || (sourceData.length?sourceData[0].source_id+':'+sourceData[0].revision_id:'');
        packageValidation=null;
      }
      const draw=()=>{
        render();
        const detail=$p('p11Detail');
        if(detail){detail.hidden=true;clear(detail);}
        if(r.task&&auth)window.opsTaskDetail(r.task,false);
      };
      if(changed&&auth){fetchViews().then(draw).catch(catchMessage);}
      else if(r.view==='agent'&&auth){window.opsB2Refresh?.().then(draw).catch(catchMessage);}
      else if(r.view==='experts'&&auth){window.opsB3Refresh?.().then(draw).catch(catchMessage);}
      else draw();
    };
    window.addEventListener('hashchange',replayRoute);
    window.addEventListener('popstate',replayRoute);
    const first=readRoute();active=first.view;project=first.p;batch=first.b;
    if(first.source)sourceSelection=first.source;
    // P1's original loadSession/refresh initiates the first authenticated fetch.
  });
})();