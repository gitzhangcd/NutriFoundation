"""Offline assisted-review form; source-only uses the separate blank JSON pack.

No network, telemetry or automatic submission. The doctor downloads a decision;
the coordinator imports it through ReviewService's binding and locking checks.
"""
from __future__ import annotations

import json


def assisted_html(projection: dict) -> str:
    if projection.get("mode")!="assisted":
        raise ValueError("Never render machine prefill for source-only review")
    payload=json.dumps(projection,ensure_ascii=False).replace("<","\\u003c").replace("&","\\u0026")
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>证据预填写审查</title><style>
body{font:16px system-ui;margin:24px auto;max-width:1200px;color:#153443;background:#f6f8fa}h1{font-size:24px}
section{background:white;border:1px solid #d8e3e9;border-radius:8px;margin:16px 0;padding:18px}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #d8e3e9;padding:10px;text-align:left;vertical-align:top}
textarea{width:95%;min-height:60px;font:inherit}select,input,button{font:inherit;padding:8px}summary{cursor:pointer}
.warn{color:#8a4000}small{color:#496371}button{background:#0b6373;color:white;border:0;border-radius:5px}
</style><h1>证据预填写审查</h1><p>这是辅助审查。请对照原件确认、修改或保留未解决项。下载记录后交回协调者；本页不会自动提交或晋升。</p>
<p id="identity"></p><p id="source"></p><label>总体决定 <select id="decision"><option value="CONFIRM">确认当前记录</option><option value="REVISE">修改后交回复核</option><option value="UNRESOLVED">存在未解决问题</option><option value="DEFER">暂缓</option></select></label>
<main id="results"></main><button id="save">下载审查记录</button><p id="message" role="status"></p>
<script type="application/json" id="payload">"""+payload+"""</script><script>
const p=JSON.parse(document.getElementById('payload').textContent), edits=[];
document.getElementById('identity').textContent='审查者：'+p.reviewer_id+'；记录：'+p.review_task_id;
document.getElementById('source').textContent='原始来源：'+p.source.source_id+'；来源版本：'+p.source.source_version+'；许可：'+p.source.license+'。本页为派生预填写，保留源内差异。';
if(p.source_file){const link=document.createElement('a');link.textContent='打开完整原件';link.href='./'+encodeURIComponent(p.source_file);link.target='_blank';document.getElementById('source').append(' ',link);}
const anchors=new Map(p.anchors.map(a=>[a.anchor_id,a]));
const labels={study_id:'研究身份',population:'研究人群',analysis_population:'分析样本',exposure:'暴露/膳食模式',comparator:'比较对象',outcome:'结局',time:'随访时间',estimand:'统计目标',model:'分析模型',effect_measure:'效应类型',effect_value:'效应值',effect_unit:'单位',exposure_increment:'评分增量',reference_category:'参照类别',adjustment:'调整因素',base_adjustment:'基础调整因素'};
function node(tag,text,parent){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;parent.appendChild(n);return n;}
for(const r of p.prefill.results){
 const section=node('section',undefined,document.getElementById('results'));node('h2',r.result_id,section);
 for(const issue of r.issues)node('p','待处理问题：'+issue,section).className='warn';
 const table=node('table',undefined,section);const header=node('tr',undefined,table);
 for(const label of ['字段与出处','原记录','审查处理'])node('th',label,header);
 for(const [key,a] of Object.entries(r.fields)){
  const tr=node('tr',undefined,table),left=node('td',undefined,tr),middle=node('td',undefined,tr),right=node('td',undefined,tr);
  node('strong',labels[key]||key,left);const detail=node('details',undefined,left);node('summary','查看原文及表格上下文',detail);
  for(const ref of a.anchor_refs){const bound=anchors.get(ref);if(bound){node('p',bound.exact_text,detail);if(bound.context.kind==='table_cell')node('p','表头：'+JSON.stringify(bound.context.headers)+'；同一行：'+JSON.stringify(bound.context.row_cells)+'；脚注：'+bound.context.footnotes,detail);}}
  const shown=a.source_value===null?(a.reason||a.state):a.source_value;
  node('p',shown.length>220?shown.slice(0,220)+'…（展开出处查看完整原文）':shown,middle);
  const action=node('select',undefined,right);
  for(const [v,t] of [['KEEP','保留/确认原记录'],['CHANGE','修改值'],['UNRESOLVED','标记未解决'],['NOT_REPORTED','原件未报告']]){const o=node('option',t,action);o.value=v;}
  const value=node('textarea',undefined,right);value.value=a.source_value||'';value.setAttribute('aria-label','修改值');value.hidden=true;
  const reason=node('textarea',undefined,right);reason.placeholder='修改或标记原因（必填）';reason.setAttribute('aria-label','处理原因');reason.hidden=true;
  action.onchange=()=>{value.hidden=action.value!=='CHANGE';reason.hidden=action.value==='KEEP';};
  edits.push({path:r.result_id+'/'+key,original:a,action,value,reason});
 }
}
document.getElementById('save').onclick=()=>{
 const patches={},reasons={};let unresolved=false;
 for(const e of edits){const action=e.action.value;if(action==='KEEP')continue;
  if(!e.reason.value.trim()){document.getElementById('message').textContent='请填写每个修改项的原因。';return;}
  reasons[e.path]=e.reason.value.trim();
  if(action==='CHANGE'){if(!e.value.value.trim()||!e.original.anchor_refs.length){document.getElementById('message').textContent='该字段缺少原文锚点，请先标记未解决，由协调者补齐锚点。';return;}patches[e.path]={...e.original,state:'PRESENT',source_value:e.value.value,normalized_value:null,reason:e.reason.value.trim()};}
  else{patches[e.path]={state:action,source_value:null,normalized_value:null,anchor_refs:[],reason:e.reason.value.trim()};unresolved=true;}
 }
 let decision=document.getElementById('decision').value;
 if(Object.keys(patches).length&&decision==='CONFIRM')decision=unresolved?'UNRESOLVED':'REVISE';
 if(decision==='REVISE'&&!Object.keys(patches).length){document.getElementById('message').textContent='选择修改时，请至少修改一个字段。';return;}
 const record={decision_id:'REVIEW-'+crypto.randomUUID(),review_task_id:p.review_task_id,draft_sha256:p.draft_sha256,mode:'assisted',reviewer_id:p.reviewer_id,submitted_at:new Date().toISOString(),patches,reasons,independent_results:[],decision};
 const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=record.decision_id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 document.getElementById('message').textContent='记录已下载，尚未提交；协调者导入后才能锁定。';
};
</script></html>"""
