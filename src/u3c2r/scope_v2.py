"""Pinned RDF/XML syntax audit and exact scope-policy recomputation."""
import pathlib as P,sys,xml.etree.ElementTree as E
from collections import Counter
HERE=P.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"u3c2"))
from scope import parse,scope,closure,graph,B,R,O,S
def require(v,c):
 if not v:raise ValueError(c)
def syntax_check(path):
 root=E.parse(path).getroot();counts=Counter()
 for e in root:
  if e.tag==R+"Description" and any(x.get(R+"resource")=="http://www.w3.org/2002/07/owl#Class" for x in e.findall(R+"type")):counts["unsupported_rdf_description_class"]+=1
  if e.tag==O+"Class" and e.get(R+"about"):
   labels=e.findall(S+"label")
   if e.get(R+"about").startswith(B+"FOODON_"):
    if len(labels)>1:counts["foodon_multiple_labels"]+=1
    if any(x.get("{http://www.w3.org/XML/1998/namespace}lang") not in (None,"en") for x in labels):counts["foodon_non_english_primary_label"]+=1
   for a in e.iter(O+"intersectionOf"):
    if a.get(R+"parseType")!="Collection":counts["unsupported_intersection_serialization"]+=1
    for n in a:
     if n.tag in (R+"Description",O+"Class") and n.get(R+"about") and list(n):counts["unsupported_named_conjunct_with_children"]+=1
     if n.tag==O+"Class" and not n.get(R+"about"):counts["nested_anonymous_conjunct_not_inferred"]+=1
 for k in ("unsupported_rdf_description_class","foodon_multiple_labels","foodon_non_english_primary_label","unsupported_intersection_serialization","unsupported_named_conjunct_with_children"):
  require(counts[k]==0,"OWL_SERIALIZATION_REVIEW_REQUIRED:"+k)
 return dict(counts)
def derive(path,old_policy,policy,baseline):
 syntax=syntax_check(path);v=parse(path);orig,stats=scope(v,old_policy,baseline)
 out={};cnt=Counter();held_probes=[]
 organism=B+"COB_0000022"
 for iri,x in orig.items():
  status=x["scope_status"];role="NONE"
  if x["asserted_core_member"] and organism in x["exclusion_roots"]:
   if set(x["exclusion_roots"])=={organism} and policy["allow_organism_overlap_role_review"]:
    status="DUAL_ROLE_ORGANISM_REVIEW_ONLY";role="ASSERTED_FOOD_PRODUCT_AND_ORGANISM_OVERLAP"
   else:role="MULTIPLE_EXCLUSION_BRANCHES_REVIEW_REQUIRED"
  if iri==policy["scope_review_probe"] and status=="HOLD_SCOPE_UNRESOLVED":role="FOOD_LABEL_SCOPE_REVIEW_REQUIRED"
  out[iri]={"scope_status":status,"review_role":role,"original_scope_status":x["scope_status"],"original_asserted_core_member":x["asserted_core_member"],"native_label":x["native_label"],"iri":iri}
  cnt[status]+=1
 # Additional positive-prefix negative probes: select actual FOODON_ members with
 # non-food/other-role reasons, not prefix-based exclusion.
 for er in old_policy["foodon"]["exclusion_roots"]:
  root=B+er["root"]
  c=closure(graph(v,True),root)
  candidates=sorted(i for i in c if i.startswith(B+"FOODON_") and i in out and out[i]["scope_status"]=="HOLD_NONFOOD_OR_NONIDENTITY_ROLE")
  if candidates:
   i=candidates[0];held_probes.append({"root":root,"iri":i,"label":v[i]["label"],"scope_status":out[i]["scope_status"]})
 return orig,out,{"syntax_audit":syntax,"scope_status_counts":dict(cnt),"core_overlap_organism_role_review":cnt["DUAL_ROLE_ORGANISM_REVIEW_ONLY"],"foodon_prefix_exclusion_probes":held_probes,"old_scope_statistics":stats,"full_owl_reasoning":False}
