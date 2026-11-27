"""A2.5-R1 transport only: lossless target deduplication and deterministic
identity/evidence carrier binding. Scientific choices are reviewer-owned."""
from collections import Counter
from agy_raw_standard_browser import S,canon,require
DIMS=("base_food","entity_grain","food_state","preparation","species_variety","edible_part","composition","regional_scope")
METHOD="Reviewer-authored terms; exact native ID, normalized label/alias equality, whole phrase or all-token conjunction; max 5 records per term."
FIELDS={"dimensions","candidates","negatives","search_results","disposition","local_concept_extension","unresolved_reasons","review_note"}
def table(hits,q):
 rows=[];idx={};groups={}
 require(set(hits)==set(q)==set(S),"QUERY_SYSTEMS")
 for sys in S:
  require(set(hits[sys])==set(q[sys]),"QUERY_HIT_CLOSURE")
  groups[sys]={}
  for term in q[sys]:
   items=hits[sys][term];require(len(items)<=5,"HIT_CAP")
   keys=[]
   for r in items:
    k=tuple(r["target_key"]);require(k[0]==sys,"TARGET_SYSTEM")
    if k not in idx:idx[k]=len(rows)+1;rows.append(r)
    else:require(rows[idx[k]-1]==r,"DUPLICATE_TARGET_DRIFT")
    keys.append(idx[k])
   groups[sys][term]=keys
 return rows,groups
def project(obj,source,q,hits):
 require(isinstance(obj,dict) and set(obj)==FIELDS,"TRANSPORT_FIELDS")
 rows,groups=table(hits,q)
 dims=obj["dimensions"];require(isinstance(dims,dict) and set(dims)==set(DIMS),"DIMENSION_CLOSURE")
 require(isinstance(obj["candidates"],list) and isinstance(obj["negatives"],list),"EDGE_ARRAYS")
 require(isinstance(obj["review_note"],str),"REVIEW_NOTE_TYPE")
 require(isinstance(obj["search_results"],dict) and set(obj["search_results"])==set(S),"SEARCH_RESULTS")
 used=set()
 def refs(x):
  require(isinstance(x,list) and len(set(x))==len(x) and all(type(k) is int and 0<=k<=len(rows) for k in x),"TRANSPORT_EVIDENCE_REF")
  used.update(x)
  return x
 for d in dims.values():
  require(isinstance(d,dict) and set(d)=={"value","state","evidence_refs"},"DIMENSION_FIELDS")
  rr=refs(d["evidence_refs"])
  if d["state"]=="SOURCE_EXPLICIT":require(0 in rr,"EXPLICIT_SOURCE_REF")
  if d["state"]=="EXTERNAL_SUPPORTED":require(any(x>0 for x in rr),"EXTERNAL_REF")
 pp=set();nn=set()
 for kind,keys,seen in [("candidates",{"row","relation","conditions","rationale","evidence_refs","applicability"},pp),("negatives",{"row","conflict_type","rationale","evidence_refs"},nn)]:
  counts=Counter()
  for x in obj[kind]:
   require(isinstance(x,dict) and set(x)==keys,"EDGE_FIELDS")
   i=x["row"];require(type(i) is int and 1<=i<=len(rows) and i not in seen,"EDGE_ROW")
   require(i in refs(x["evidence_refs"]),"EDGE_TARGET_EVIDENCE_REQUIRED")
   seen.add(i);counts[rows[i-1]["target_key"][0]]+=1
  require(all(v<=3 for v in counts.values()),"EDGE_CAP")
 require(not pp&nn,"POS_NEG_CONFLICT")
 # Evidence statements are literal source metadata, not controller-authored
 # semantic conclusions. The reviewer selects all evidence references.
 evidence=[];remap={}
 for i in sorted(used):
  remap[i]=len(evidence)
  if i==0:
   observation=canon({k:source[k] for k in ("source_native_label","native_kind","native_aliases","reference_recipe_ingredient_names","context_note")})
   evidence.append({"artifact_sha256":source["artifact_sha256"],"locator":canon(source["source_locator"]),"observation":observation,"role":"SOURCE_EXPLICIT"})
  else:
   v=rows[i-1]
   evidence.append({"artifact_sha256":v["artifact_sha256"],"locator":v["target_locator"],"observation":canon({k:v[k] for k in ("target_native_label","raw_aliases","raw_definition") if k in v}),"role":"TARGET_EXPLICIT"})
 def rrefs(x):return [remap[i] for i in x]
 nd={k:{"value":v["value"],"state":v["state"],"evidence_refs":rrefs(v["evidence_refs"])} for k,v in dims.items()}
 def edge(v,positive):
  row=rows[v["row"]-1]
  x={k:row[k] for k in ("target_key","target_native_label","target_locator")}
  x.update({k:val for k,val in v.items() if k not in ("row","evidence_refs")})
  x["evidence_refs"]=rrefs(v["evidence_refs"])
  if positive:x.update(direction="SOURCE_RELATION_TO_TARGET",measurement_transfer="HOLD")
  return x
 record={k:source[k] for k in ("review_id","source_ref","source_scope","source_native_label","native_kind")}
 record.update(source_dimensions=nd,evidence=evidence,independent_candidates=[edge(v,True) for v in obj["candidates"]],hard_negatives=[edge(v,False) for v in obj["negatives"]],
  search_attempts=[{"target_system":s,"query_terms":q[s],"search_method":METHOD,"result":obj["search_results"][s]} for s in S],
  case_disposition=obj["disposition"],local_concept_extension=obj["local_concept_extension"],unresolved_reasons=obj["unresolved_reasons"],
  reviewer_minutes=0,review_status="CRITIC_DRAFT",accepted_equivalence=False,mapping_release_authorized=False,scientific_reference_qualified=False,purpose="CURATION_DEV_ONLY")
 return {"records":[record],"review_note":obj["review_note"]}
COMMON="Independent source-first developmental reference, not Gold. Use only this case and actual returned raw standard rows. No tools, previous conversations, external search, tested rankings or other context. Preserve source evidence and uncertainty. Unknown is not a contradiction. Do not infer physical composition or nutrient amounts. No accepted equivalence or scientific release. "
def query_prompt(src,rules):
 return COMMON+"Task rules:\n"+canon(rules)+"\nSource:\n"+canon(src)+"\nChoose 1-5 distinct nonempty query terms (max 140 characters) independently for each FoodOn, FDC_SR_Legacy and FNDDS. Same raw browser search: exact ID, normalized equality, whole phrase, all-token match; returns at most 5 records per term. Include relevant variants, specificity and synonyms. Return ONLY JSON {\"queries\":[{\"review_id\":\"copy exact ID\",\"systems\":{\"FoodOn\":[\"term\"],\"FDC_SR_Legacy\":[\"term\"],\"FNDDS\":[\"term\"]}}]}."
TRANSPORT="""
Return ONLY one JSON object with these eight keys, no Markdown or tools:
dimensions: object with keys base_food, entity_grain, food_state, preparation, species_variety, edible_part, composition, regional_scope. Each value is {"value":string or null,"state":enum,"evidence_refs":[integer,...]}. States SOURCE_EXPLICIT, SEMANTIC_INFERENCE, EXTERNAL_SUPPORTED, UNRESOLVED. UNRESOLVED requires null and []; other states require nonempty value and references. SOURCE_EXPLICIT requires evidence 0; EXTERNAL_SUPPORTED requires at least one target reference. Do not infer current state or species absent evidence; reference recipe names are not measured composition.
candidates: array of {"row":positive integer,"relation":enum,"conditions":[string,...],"rationale":string,"applicability":enum,"evidence_refs":[integer,...]}. Relation EXACT, CLOSE, BROADER_TARGET, NARROWER_TARGET, RELATED, CONDITIONAL, AMBIGUOUS, UNRESOLVED. Applicability CONCEPT_CANDIDATE_ONLY, CONDITIONAL_CONCEPT_CANDIDATE, RELATED_ONLY, UNRESOLVED. CONDITIONAL needs nonempty conditions and CONDITIONAL_CONCEPT_CANDIDATE; that applicability always needs conditions. EXACT only same conceptual grain; direction source-to-target. Do not force candidates. At most 3 per standard.
negatives: array of {"row":positive integer,"conflict_type":enum,"rationale":string,"evidence_refs":[integer,...]}. Conflict types EXPLICIT_CONFLICT, GRAIN_OR_ROLE_DIFFERENCE, TARGET_SPECIFIC_CONDITION, COMPOSITION_OR_SPECIES_DIFFERENCE, UNRESOLVED_OTHER. At most 3 per standard, actual difficult negatives only, not all irrelevant hits. Candidate and negative target sets must be disjoint. Missing facts are not explicit conflict.
search_results: object keyed FoodOn, FDC_SR_Legacy, FNDDS, each one of CANDIDATES_FOUND, NO_SUPPORTED_TARGET_IN_REVIEWED_MATERIAL, INSUFFICIENT_SOURCE, SEARCH_INCOMPLETE. No-supported means only bounded searched material, not absence from the knowledge base.
disposition: CANDIDATE_CONCEPT_ONLY, CONDITIONAL_OR_AMBIGUOUS, NO_SUPPORTED_TARGET_IN_REVIEWED_MATERIAL, HOLD_INSUFFICIENT_EVIDENCE. CANDIDATE_CONCEPT_ONLY needs a candidate. Last two require unresolved_reasons and all listed candidates AMBIGUOUS or UNRESOLVED with applicability UNRESOLVED.
local_concept_extension: NOT_PROPOSED or CANDIDATE_FOR_LOCAL_CONCEPT_REVIEW.
unresolved_reasons: array of nonempty strings.
review_note: brief string about actual limitations.
Evidence index 0 is the source record; 1..N are the explicitly indexed raw authority rows. For each candidate/negative include its own row index in evidence_refs. Other source/target evidence may also be selected. The controller copies immutable identities, evidence carriers, actual query terms and fixed HOLD flags; you must supply ALL scientific values, states, relations, rationales, conditions, applicability, dispositions and search outcomes. Use concise rationales; no repeated locator strings in output.
"""
def review_prompt(src,q,hits,rules):
 rows,groups=table(hits,q)
 # Deduplicate repeated rows without dropping any matches, aliases, definitions
 # or exact native identity/locators; retain term-to-row membership.
 tab=[{"row":i+1,**r} for i,r in enumerate(rows)]
 return COMMON+"Task rules:\n"+canon(rules)+"\n"+TRANSPORT+"\nSource evidence 0:\n"+canon(src)+"\nActual queries and result row indices:\n"+canon(groups)+"\nRaw authority rows:\n"+canon(tab)
