const $=s=>document.querySelector(s);
const n=$('#notice');
function status(t,failed=false){n.textContent=t;n.className=failed?'notice failure':'notice';}
$('#run').addEventListener('click',async()=>{
  const token=$('#token').value;
  if(!token){status('请输入本地合成管理员令牌。',true);return;}
  status('正在读取权威仓库预检结果…');
  try{
    const response=await fetch('/v1/readiness',{headers:{'X-Workbench-Admin-Token':token},cache:'no-store'});
    if(!response.ok)throw new Error('后端拒绝访问（'+response.status+'）');
    const data=await response.json();
    $('#sourceCount').textContent=String(data.source_count);
    $('#packetStatus').textContent=data.bounded_projection_contract==='PASS'?'一致':'BLOCK';
    $('#pilotStatus').textContent='NO GO';
    $('#gateCount').textContent=data.external_requirements.length+' 个条件';
    const holder=$('#gates');holder.replaceChildren();
    for(const item of data.external_requirements){
      const row=document.createElement('div');row.className='gate-row';
      const badge=document.createElement('span');badge.className='dot';badge.textContent='!';
      const txt=document.createElement('div');const title=document.createElement('strong');title.textContent=item.gate;
      const detail=document.createElement('small');detail.textContent=item.requirement;
      const flag=document.createElement('em');flag.textContent=item.status==='BLOCK_UPSTREAM_SCIENTIFIC_VERSION_CONFLICT'?'科学版本冲突':'待独立审核';
      txt.append(title,detail);row.append(badge,txt,flag);holder.append(row);
    }
    const v=data.case_projection_binding;
    $('#caseConflict').textContent=v.referenced_case_ref+' vs '+v.target_workpack_case_ref+'；'+v.decision;
    status('科学来源限定投影已验证；真人试测仍 NO GO，未生成专家记录。');
  }catch(error){status(error.message,true);}
});
