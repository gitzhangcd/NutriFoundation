// WB-v0.3-P1.2: expert-native view adapter. Does not infer scientific truth.
// All canonical 19 fields remain authoritative and are never silently merged.
export function canonicalPaths(profile) {
  const fields=(profile?.field_groups||[]).flatMap(g=>g.fields||[]);
  const keys=fields.map(f=>f.key);
  if(keys.length!==19 || new Set(keys).size!==19) throw Error('PROFILE_19_FIELD_CONTRACT_MISMATCH');
  return keys;
}
export function getPath(obj,key) {
  return key.split('.').reduce((a,k)=>a?.[k],obj);
}
export function setPath(obj,key,value) {
  const names=key.split('.');
  let target=obj;
  for(const name of names.slice(0,-1)){
    if(!target || !(name in target)) throw Error('CANONICAL_PATH_MISSING');
    target=target[name];
  }
  if(!target || !(names[names.length-1] in target)) throw Error('CANONICAL_PATH_MISSING');
  target[names[names.length-1]]=value;
}
export function confirmCanonicalCompleteness(profile,canonical) {
  const paths=canonicalPaths(profile);
  for(const key of paths) {
    const value=getPath(canonical,key);
    if(value===undefined) throw Error('CANONICAL_FIELD_MISSING:'+key);
  }
  return paths;
}
export function appendNaturalEntry(profile, canonical, field, originalText) {
  const keys=confirmCanonicalCompleteness(profile,canonical);
  if(!keys.includes(field) || !Array.isArray(getPath(canonical,field))) throw Error('NON_LIST_FIELD');
  if(typeof originalText!=='string' || !originalText.trim() || originalText.includes('\n') ||
     originalText.includes('\r') || originalText.length>2000) throw Error('INVALID_EXPERT_ENTRY');
  // Do not normalize, paraphrase, classify, or silently drop expert wording.
  const next=structuredClone(canonical);
  getPath(next,field).push(originalText);
  confirmCanonicalCompleteness(profile,next);
  return next;
}
export function compareUnchangedFields(profile,before,after,allowed) {
  const keys=confirmCanonicalCompleteness(profile,before);
  confirmCanonicalCompleteness(profile,after);
  return keys.every(k=>k===allowed || JSON.stringify(getPath(before,k))===
                       JSON.stringify(getPath(after,k)));
}
