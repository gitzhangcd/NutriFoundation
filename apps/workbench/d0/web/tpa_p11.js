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
  let loading=false;
  const routes=['overview','projects','tasks','sources','agent','experts','quality','audit'];
  const labels={overview:'工作总览',projects:'项目与批次',tasks:'任务中心',sources:'科学资料库',agent:'Agent 准备',experts:'专家与分配',quality:'进度与质控',audit:'审计与导出'};
  const metric={preparing:'准备中',ready:'待分配',assigned:'已分配未发布',published:'已发布',revoked:'已撤销',blocked:'历史阻断'};
  const stateLabel={DRAFT:'草稿',VALIDATED:'已验证',DEFINITION_FROZEN:'定义已冻结',READY_FOR_ASSIGNMENT:'待分配',ASSIGNED:'已分配',PUBLISHED:'已发布',REVOKED:'已撤销'};
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
  const paramsFor=(p=project,b=batch,t='')=>{
    const query=new URLSearchParams();
    if(p)query.set('project',p);
    if(b)query.set('batch',b);
    if(t&&TASK_PATTERN.test(t))query.set('task',t);
    return query;
  };
  const hashFor=(view,p=project,b=batch,t='')=>{
    const query=paramsFor(p,b,view==='tasks'?t:'').toString();
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
    if(p&&projects.length&&!projects.some(x=>x.project_id===p)){p='';b='';}
    if(b&&batchMap.size&&!(batchMap.get(p)||[]).some(x=>x.batch_id===b))b='';
    return {view,p,b,task};
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
    const args=new URLSearchParams();
    if(project)args.set('project_id',project);
    if(batch)args.set('batch_id',batch);
    const suffix=args.toString()?'?'+args.toString():'';
    const [v, first]=await Promise.all([
      apiOps('/v1/tpa/overview'+suffix),
      apiOps('/v1/tpa/tasks?'+(args.toString()?args.toString()+'&':'')+'limit=100&offset=0')
    ]);
    overview=v;managedTasks=first.tasks||[];
    let offset=managedTasks.length;
    while(offset<first.total&&offset<10000){
      const page=await apiOps('/v1/tpa/tasks?'+(args.toString()?args.toString()+'&':'')+'limit=100&offset='+offset);
      if(!page.tasks?.length)break;
      managedTasks.push(...page.tasks);offset+=page.tasks.length;
    }
    // State authority belongs to server. If a response is incomplete, never call it exhaustive.
  }
  function select(id, entries, value, onChange, placeholder){
    const sel=e('select');sel.id=id;sel.className='p11-select';
    const opt=e('option',placeholder);opt.value='';sel.append(opt);
    for(const [k,label] of entries){const o=e('option',label);o.value=k;sel.append(o)}
    sel.value=value;sel.addEventListener('change',ev=>onChange(ev.target.value));return sel;
  }
  async function chooseScope(p,b=''){
    legacyOnly=false;navigate(active,p,b);await fetchViews();render();
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
      const v={preparing:'',ready:'READY_FOR_ASSIGNMENT',assigned:'ASSIGNED',published:'PUBLISHED',revoked:'REVOKED'}[key];
      if(v!==undefined&&$p('stateFilter')){
        $p('stateFilter').value=v;
        $p('stateFilter').dispatchEvent(new Event('change'));
      }
      if(key==='preparing'){window.opsPreparingFilter=true;renderTasks();}
      render();
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
      b.classList.add('p11-wizard-step');box.append(b);
    }
    const form=$p('taskForm'); if(!form)return;
    const parts=[...form.querySelectorAll('fieldset')];
    parts[0].hidden=wizardStep!==1;parts[1].hidden=wizardStep!==2;parts[2].hidden=wizardStep!==2;
    let info=$p('p11WizardInfo');
    if(!info){info=e('div',undefined,'p11-step-info');info.id='p11WizardInfo';form.after(info);}
    clear(info);
    if(wizardStep===1){
      info.append(notice('选定已登记的合成资料和版本，然后进入定义任务。'));
      info.append(button('下一步：定义任务',()=>{wizardStep=2;renderWizard()},'primary'));
    }else if(wizardStep===2){info.append(notice('确认知识截止、Profile、工作模式后点击“创建合成任务草稿”，系统会以单事务保存任务与运营归属。'));
    }else if(wizardStep===3){info.append(notice('在右侧任务队列使用 Producer 的“检查资料与任务”→“冻结任务定义”，冻结后不能原位改写。'));
    }else if(wizardStep===4){info.append(notice('Producer 在右侧任务队列准备合成候选或独立资料包。专家独立组不接收任何 Agent 候选。'));
    }else{info.append(notice('使用独立 Manager 会话在右侧分配、发布；Producer 不能代行操作。'));
    }
  }
  async function reload(){
    if(loading||!auth)return;
    loading=true;
    try {
      await loadProjects();await fetchViews();renderSelector();render();
      const deep=readRoute().task;
      if(deep)await window.opsTaskDetail(deep,false);
    }
    finally{loading=false;}
  }
  function render(){
    active=routes.includes(active)?active:'overview';
    document.body.dataset.p11View=active;
    const separate=active!=='tasks';
    $p('p11View').hidden=!separate;
    $p('p11TaskView').hidden=separate;
    const nav=$p('p11Nav');
    for(const item of nav.querySelectorAll('button[data-p11-route]')){
      item.setAttribute('aria-current',item.dataset.p11Route===active?'page':'false');
    }
    $p('p11SectionTitle').textContent=labels[active];
    if(separate){clear($p('p11View'));$p('p11View').append(active==='overview'?renderOverview():active==='projects'?renderProjects():renderPlaceholder());}
    else{renderSelector();renderWizard();renderTaskToolbar();}
  }
  function go(view){navigate(view);}
  function renderTaskToolbar(){
    let bar=$p('p11TaskToolbar');if(!bar)return;clear(bar);
    const shortcut=button('项目与批次',()=>go('projects'),'secondary');shortcut.id='p11ProjectsShortcut';bar.append(shortcut);
    const label=e('label');label.append(e('span','项目'));label.append(select('p11TaskProject',projects.map(p=>[p.project_id,p.name]),project,
      v=>chooseScope(v).catch(catchMessage),'全部项目 / Legacy'));bar.append(label);
    if(project){const b=e('label');b.append(e('span','批次'));b.append(select('p11TaskBatch',(batchMap.get(project)||[]).map(x=>[x.batch_id,x.label]),batch,
      v=>chooseScope(project,v).catch(catchMessage),'全部批次'));bar.append(b);}
    const q=e('label');q.append(e('span','任务搜索'));const input=e('input');input.placeholder='合成任务 ID';input.value=search;
    input.addEventListener('input',ev=>{search=ev.target.value.trim();renderTasks();});q.append(input);bar.append(q);
    if(!project){
      const legacy=button(legacyOnly?'显示全部任务':'仅显示 Legacy 任务',()=>{
        legacyOnly=!legacyOnly;renderTaskToolbar();
      },legacyOnly?'primary':'secondary');
      legacy.id='p11LegacyToggle';bar.append(legacy);
    }
    const info=e('p','Legacy 为没有运营批次归属的旧任务，不自动迁移。','p11-meta');bar.append(info);
    renderTasks();
  }
  window.opsVisibleTasks = rows => {
    // Data from server-filtered list; preserve legacy list behavior if scope not selected.
    const allowed = new Set((managedTasks||[]).map(t=>t.task_id));
    const legacyIds=new Set((managedTasks||[]).filter(t=>t.legacy===true).map(t=>t.task_id));
    return rows.filter(t=>(!project||allowed.has(t.task_id))&&(!legacyOnly||legacyIds.has(t.task_id))&&(!search||t.task_id.toLowerCase().includes(search.toLowerCase())));
  };
  window.opsLegacyTask=taskId=>managedTasks.some(t=>t.task_id===taskId&&t.legacy===true);
  window.opsDraftCreate=async body=>{
    if(!project||!batch)throw Error('请先在“项目与批次”创建或选择项目与批次');
    const result=await apiOps('/v1/tpa/tasks/in-batch',{method:'POST',body:JSON.stringify({
      ...body,project_id:project,batch_id:batch,idempotency_key:crypto.randomUUID()
    })});
    legacyOnly=false;wizardStep=3;return result;
  };
  window.opsClear=()=>{projects=[];batchMap=new Map();overview=null;managedTasks=[];project='';batch='';search='';wizardStep=1;active='overview';window.opsPreparingFilter=false;legacyOnly=false;
    if($p('p11View'))clear($p('p11View'));
    if($p('p11Detail')){$p('p11Detail').hidden=true;clear($p('p11Detail'));}
    if($p('p11ModalOverlay')){$p('p11ModalOverlay').hidden=true;clear($p('p11ModalOverlay'));}
    if($p('receipt'))$p('receipt').textContent='仅供合成工程验收。尚无操作。';
  };
  window.opsRefresh=reload;
  window.opsTaskDetail=async (taskId,recordRoute=true)=>{
    try {
      const detail=await apiOps('/v1/tpa/tasks/'+encodeURIComponent(taskId)+'/management');
      if(recordRoute && TASK_PATTERN.test(taskId)){
        const h=hashFor('tasks',project,batch,taskId);
        if(location.hash!==h)history.pushState({p11:'task'},'',h);
      }
      const box=$p('p11Detail');clear(box);box.hidden=false;
      box.append(e('h3','任务详情 · '+detail.task_id),e('p','状态：'+(stateLabel[detail.state]||detail.state),'p11-meta'));
      box.append(e('p','运营归属：'+(detail.placement?detail.placement.project_id+' / '+detail.placement.batch_id:'Legacy'),'p11-meta'));
      box.append(e('p','资料：'+detail.primary_source.source_id+' / '+detail.primary_source.revision_id,'p11-meta'));
      box.append(e('p','Profile：'+detail.profile_id+'；工作模式：'+detail.workflow_strategy,'p11-meta'));
      box.append(e('p','知识截止：'+detail.knowledge_cutoff,'p11-meta'));
      box.append(e('p','后续操作：'+(detail.next_action||'无')+'（须由对应服务端角色授权）','p11-meta'));
      box.append(notice('这是运营元数据。未开放专家原文、候选或 Gold 浏览。'));
      box.append(button('关闭详情',()=>{
        box.hidden=true;clear(box);
        if(location.hash!==hashFor('tasks',project,batch))location.hash=hashFor('tasks',project,batch);
      }));
      box.scrollIntoView({behavior:'smooth',block:'nearest'});
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
    document.addEventListener('keydown',ev=>{
      if(ev.key==='Escape'&&$p('p11ModalOverlay')&&!$p('p11ModalOverlay').hidden)$p('p11ModalOverlay').hidden=true;
    });
    const replayRoute=()=>{
      const r=readRoute();
      const changed=(project!==r.p||batch!==r.b);
      active=r.view;project=r.p;batch=r.b;
      const draw=()=>{
        render();
        const detail=$p('p11Detail');
        if(detail){detail.hidden=true;clear(detail);}
        if(r.task&&auth)window.opsTaskDetail(r.task,false);
      };
      if(changed&&auth){fetchViews().then(draw).catch(catchMessage);}
      else draw();
    };
    window.addEventListener('hashchange',replayRoute);
    window.addEventListener('popstate',replayRoute);
    const first=readRoute();active=first.view;project=first.p;batch=first.b;
    // P1's original loadSession/refresh initiates the first authenticated fetch.
  });
})();