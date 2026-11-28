"""A2.6-P1 frozen adjudication policy: evaluation projections only, never Gold."""
from copy import deepcopy
from collections import Counter
VERSION="A2.6-P1-SEMANTIC-POLICY-v0.1"
ROUTE="DEVELOPMENT_RAW_PRIMARY_PLUS_CONSERVATIVE_SECONDARY"
OTHER_ROUTE="EXPERT_ADJUDICATION_FIRST"
NEGATIVE_DEMOTIONS={"TARGET_SPECIFIC_CONDITION","UNRESOLVED_OTHER"}
SUPPORT={"EXACT","CLOSE","BROADER_TARGET","NARROWER_TARGET","RELATED","CONDITIONAL"}
DIMS=("base_food","entity_grain","food_state","preparation","species_variety","edible_part","composition","regional_scope")
def need(ok,code):
 if not ok:raise ValueError(code)
def conservative_projection(references):
 """Predetermined evaluation-only sensitivity, not a scientific reference
 schema instance. Preserve reviewed key membership: move uncertain negatives
 to UNRESOLVED candidate placeholders, never count them as supported or as
 unreviewed. Original records remain byte-for-byte unchanged. No new keys.
 Call frozen scorer with sensitivity=True for this secondary projection.
 No assertion that any retained negative is a true scientific error."""
 out=[];counts=Counter()
 for record in references:
  r=deepcopy(record);p=r["independent_candidates"];n=r["hard_negatives"]
  pk={tuple(x["target_key"]) for x in p};nk={tuple(x["target_key"]) for x in n}
  need(len(pk)==len(p) and len(nk)==len(n) and not pk&nk,"EDGE_CLOSURE")
  remain=[]
  for e in n:
   if e["conflict_type"] in NEGATIVE_DEMOTIONS:
    p.append({"target_key":deepcopy(e["target_key"]),"relation":"UNRESOLVED","applicability":"UNRESOLVED"})
    counts[e["conflict_type"]]+=1
   else:remain.append(e)
  r["hard_negatives"]=remain
  pk2={tuple(x["target_key"]) for x in p};nk2={tuple(x["target_key"]) for x in remain}
  need(pk|nk==pk2|nk2 and not pk2&nk2,"REVIEWED_MEMBERSHIP_DRIFT")
  out.append(r)
 return out,dict(counts)
