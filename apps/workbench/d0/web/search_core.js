// Pure helpers for reader search; no DOM access so they can be unit tested in Node.
export const CJK=/[\u3400-\u9fff\uf900-\ufaff]/;
export function normalizeQuery(q){return String(q??'').replace(/\s+/g,' ').trim();}
export function queryProblem(q){
 const n=normalizeQuery(q);
 if(!n)return 'EMPTY';
 return n.length<(CJK.test(n)?2:3)?'TOO_SHORT':'';
}
function escapeRegExp(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}
export function searchPattern(q){return new RegExp(normalizeQuery(q).split(' ').map(escapeRegExp).join('\\s+'),'giu');}
export function matchRanges(text,q){
 const out=[];if(!normalizeQuery(q))return out;
 for(const m of String(text).matchAll(searchPattern(q)))if(m[0])out.push([m.index,m.index+m[0].length]);
 return out;
}
export function snippetParts(text,q,before=40,after=50){
 const flat=String(text).replace(/\s+/g,' ').trim(),hit=matchRanges(flat,q)[0];
 if(!hit)return {before:flat.slice(0,90)+(flat.length>90?'…':''),match:'',after:''};
 const from=Math.max(0,hit[0]-before),to=Math.min(flat.length,hit[1]+after);
 return {before:(from?'…':'')+flat.slice(from,hit[0]),match:flat.slice(hit[0],hit[1]),after:flat.slice(hit[1],to)+(to<flat.length?'…':'')};
}
// units: [{unit_id,type,text}] in document order -> Map(unit_id -> nearest preceding section title)
export function sectionIndex(units){
 const map=new Map();let current='';
 for(const u of units){if(u.type==='SECTION')current=u.text.replace(/\s+/g,' ').trim();map.set(u.unit_id,current);}
 return map;
}
// records: [[unit_id,[text,...]],...] -> unit ids whose translated text matches, in given order
export function translationMatches(records,q){
 const out=[];
 for(const [unit_id,texts] of records)if(texts.some(t=>matchRanges(t,q).length))out.push(unit_id);
 return out;
}
export function searchSummary(total,shown,translationOnly=0){
 if(!total)return '没有找到匹配的原文或译文';
 const head=`共找到 ${total} 处`+(translationOnly?`（其中 ${translationOnly} 处仅在中文译文）`:'');
 return shown<total?`${head}，已列出 ${shown} 处`:head;
}
