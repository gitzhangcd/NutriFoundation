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
