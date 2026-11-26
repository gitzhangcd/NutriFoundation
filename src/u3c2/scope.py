"""Bounded, traceable FoodOn scope qualification. Not an OWL reasoner."""
import xml.etree.ElementTree as ET
from collections import defaultdict,deque,Counter
B="http://purl.obolibrary.org/obo/"
R="{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
O="{http://www.w3.org/2002/07/owl#}"
S="{http://www.w3.org/2000/01/rdf-schema#}"
def require(v,code):
 if not v:raise ValueError(code)
def parse(path):
 xml=ET.parse(path).getroot()
 v={}
 for e in xml:
  if e.tag!=O+"Class" or not e.get(R+"about"):continue
  iri=e.get(R+"about");require(iri not in v,"DUPLICATE_CLASS")
  v[iri]={"label":e.findtext(S+"label") or "","deprecated":any((a.text or "").casefold()=="true" for a in e.findall(O+"deprecated")),"asserted":set(),"extra":{},"complex_axioms":0}
 for e in xml:
  iri=e.get(R+"about")
  if e.tag!=O+"Class" or iri not in v:continue
  a=v[iri]
  for z in e:
   if z.tag not in (S+"subClassOf",O+"equivalentClass"):continue
   t=z.get(R+"resource")
   if t:
    if z.tag==S+"subClassOf":a["asserted"].add(t)
    else:
     a["extra"][t]="NAMED_EQUIVALENT_CLASS"
     if t in v:v[t]["extra"][iri]="NAMED_EQUIVALENT_CLASS_REVERSE"
    continue
   a["complex_axioms"]+=1
   # A <= (B and C) entails A <= B and A <= C. No reverse inference.
   # Do NOT interpret union members or existential restriction fillers as parents.
   for c in z.findall(O+"Class"):
    for ix in c.findall(O+"intersectionOf"):
     if ix.get(R+"parseType")!="Collection":continue
     for named in ix:
      if named.tag not in (R+"Description",O+"Class"):continue
      t=named.get(R+"about")
      if t and not list(named):a["extra"][t]="NECESSARY_NAMED_INTERSECTION_CONJUNCT"
 return v
def graph(v,augmented):
 ch=defaultdict(dict)
 for i,a in v.items():
  for t in a["asserted"]:ch[t][i]="ASSERTED_NAMED_SUBCLASS"
  if augmented:
   for t,kind in a["extra"].items():
    if i not in ch[t]:ch[t][i]=kind
 return ch
def closure(ch,root):
 # Shortest deterministic witness, child -> root. Cycles handled by visited.
 q=deque([root]);parents={root:None}
 while q:
  t=q.popleft()
  for c,k in sorted(ch[t].items()):
   if c not in parents:parents[c]=(t,k);q.append(c)
 return parents
def witness(anc,i):
 a=[]
 while anc[i] is not None:
  p,k=anc[i];a.append({"child":i,"parent":p,"axiom_kind":k});i=p
 return a
def scope(v,policy,baseline):
 f=policy["foodon"];r=B+f["root"];require(v[r]["label"]==f["baseline_label"],"FOODON_ROOT")
 ga=graph(v,False);gb=graph(v,True)
 asserted=closure(ga,r);aug=closure(gb,r)
 valid=lambda i:i in v and i.startswith(B+"FOODON_") and v[i]["label"] and not v[i]["deprecated"]
 old={i for i in asserted if valid(i)};require(old==baseline,"FOODON_BASELINE_CLOSURE_DRIFT")
 # Negative roots are exclusion or ambiguity conditions, never blanket promotion.
 neg={}
 for x in f["exclusion_roots"]:
  t=B+x["root"];require(v[t]["label"]==x["label"],"NEGATIVE_ROOT_IDENTITY")
  neg[t]=closure(gb,t)
 lanes={}
 for x in f["extension_lanes"]:
  t=B+x["root"];require(v[t]["label"]==x["label"],"LANE_ROOT_IDENTITY")
  lanes[t]=(x["role"],closure(gb,t))
 out={};counts=Counter();lanecount=Counter();excludedoverlap=0
 for i in sorted(v):
  a=v[i];roles=[];proofs=[];bad=[t for t,c in neg.items() if i in c]
  if i in asserted:roles.append("ASSERTED_FOOD_PRODUCT")
  elif i in aug:roles.append("BOUNDED_NECESSARY_FOOD_PRODUCT")
  for t,(role,c) in lanes.items():
   if i in c:roles.append(role);lanecount[role]+=1
  if not valid(i):status="HOLD_NON_FOODON_OR_UNLABELED_OR_DEPRECATED"
  elif bad and roles:status="HOLD_EXCLUSION_BRANCH_OVERLAP"
  elif bad:status="HOLD_NONFOOD_OR_NONIDENTITY_ROLE"
  elif i in old:status="CORE_RETAINED_DEV"
  elif roles:status="EXTENSION_TYPED_RETRIEVAL_ONLY"
  else:status="HOLD_SCOPE_UNRESOLVED"
  if i in old and status!="CORE_RETAINED_DEV":excludedoverlap+=1
  if status in ("CORE_RETAINED_DEV","EXTENSION_TYPED_RETRIEVAL_ONLY"):
   if i in aug:proofs.append({"root":r,"steps":witness(aug,i)})
   for t,(role,c) in lanes.items():
    if i in c:proofs.append({"root":t,"steps":witness(c,i)})
  x={"iri":i,"native_label":a["label"],"deprecated":a["deprecated"],"scope_status":status,"roles":roles,"exclusion_roots":bad,
     "asserted_core_member":i in old,"bounded_product_reachable":i in aug,"witnesses":proofs,
     "locator":"FoodOn.owl#rdf:about="+i,"purpose":"CURATION_DEV","mapping_release_authorized":False}
  out[i]=x;counts[status]+=1
 return out,{"named_classes":len(v),"named_labeled_classes":sum(bool(a["label"]) for a in v.values()),"asserted_root_closure":len(asserted),"asserted_active_core":len(old),
 "bounded_root_closure":len(aug),"bounded_active_root_members":sum(valid(i) for i in aug),"extra_named_axiom_edges":sum(len(a["extra"]) for a in v.values()),"core_negative_overlap":excludedoverlap,
 "scope_status_counts":dict(counts),"lane_memberships_nonexclusive":dict(lanecount),"full_owl_reasoning":False}
