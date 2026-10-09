// PDF verification is a separate resolver result, never inferred from a binding.
export function judgmentEvidence({field,index,text,savedText,bindings,anchors,pdfStatus={}}){
 const relevant=bindings.filter(b=>b.field===field&&b.item_index===index);
 const links=[];
 for(const binding of relevant){
  const anchor=anchors.find(a=>a.anchor_id===binding.anchor_id);
  if(binding.current_statement_matches&&text===savedText&&anchor)
   links.push({binding,anchor,pdfVerified:pdfStatus[anchor.anchor_id]===true});
 }
 return {links,stale:relevant.length-links.length};
}

// A saved edit must invalidate links before the server listing is refetched;
// otherwise the previous `current_statement_matches` would be shown as current.
export function invalidateChangedBindings(bindings,before,after,itemText){
 return bindings.map(b=>{
  const old=itemText(before,b.field,b.item_index),now=itemText(after,b.field,b.item_index);
  return old===now?b:{...b,current_statement_matches:false};
 });
}
