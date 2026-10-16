/* Independent P2 reviewer login. Same-origin D0 cookie and CSRF. */
'use strict';
document.addEventListener('DOMContentLoaded',()=>{
  const at=id=>document.getElementById(id);
  let session=null;
  async function request(path,options={}){
    const headers={'Accept':'application/json'};
    if(options.body!==undefined)headers['Content-Type']='application/json';
    if(options.method&&options.method!=='GET'&&session?.csrf_token)headers['x-csrf-token']=session.csrf_token;
    const res=await fetch(path,{method:options.method||'GET',body:options.body?JSON.stringify(options.body):undefined,
      credentials:'same-origin',cache:'no-store',headers,...(options.headers?{headers:{...headers,...options.headers}}:{})});
    const data=await res.json().catch(()=>({}));
    if(!res.ok)throw new Error(data.detail?.code||String(data.detail||res.status));
    return data;
  }
  function independentV2(){return location.hash.startsWith('#/studio-v2')}
  function portalReference(){
    const q=new URLSearchParams((location.hash.split('?')[1]||''));
    return {sourceId:q.get('source')||'',revisionId:q.get('revision')||''};
  }
  function display(s){
    if(!s||!['curator','auditor'].includes(s.role)){
      session=null;window.p2StudioSession=null;
      window.p2SourceStudio?.reset();window.p2SourceStudioV2?.reset();
      at('p2Login').hidden=false;at('workspace').hidden=true;at('p2Logout').hidden=true;return;
    }
    session=s;window.p2StudioSession=s;
    at('p2Account').textContent=s.username+' · '+s.role;
    at('p2Login').hidden=true;at('workspace').hidden=false;at('p2Logout').hidden=false;
    const v2=independentV2();
    at('p2PortalLegacy').setAttribute('aria-pressed',v2?'false':'true');
    at('p2PortalV2').setAttribute('aria-pressed',v2?'true':'false');
    const host=at('p2PortalMount');
    if(v2){
      const ref=portalReference();
      host.replaceChildren(window.p2SourceStudioV2.render({
        role:s.role,session:s,projects:[],batchMap:new Map(),
        scope:{project:'',batch:''},sourceId:ref.sourceId,revisionId:ref.revisionId,
        startPage:s.role==='curator'?'qa':'queue'
      }));
    }else{
      host.replaceChildren(window.p2SourceStudio.render({
        role:s.role,session:s,projects:[],batchMap:new Map(),scope:{project:'',batch:''}
      }));
      window.p2SourceStudio.selectTab(s.role==='curator'?'qa':'library');
    }
  }
  at('p2PortalLegacy').addEventListener('click',()=>{location.hash='#/studio';});
  at('p2PortalV2').addEventListener('click',()=>{location.hash='#/studio-v2';});
  window.addEventListener('hashchange',()=>{if(session)display(session)});
  at('p2LoginForm').addEventListener('submit',async ev=>{
    ev.preventDefault();at('p2LoginError').textContent='';
    try{
      const data=await request('/v1/login',{method:'POST',body:{username:at('p2Username').value.trim(),
        password:at('p2Password').value}});
      at('p2Password').value='';
      if(!['curator','auditor'].includes(data.role))throw new Error('独立审核页面需要 Curator / Auditor 账户');
      const s=await request('/v1/session');display(s);
    }catch(err){at('p2LoginError').textContent='登录失败：'+err.message;display(null);}
  });
  at('p2Logout').addEventListener('click',async()=>{
    try{await request('/v1/logout',{method:'POST'})}finally{display(null);}
  });
  request('/v1/session').then(display).catch(()=>display(null));
});
