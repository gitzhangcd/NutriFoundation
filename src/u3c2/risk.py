"""Conservative multi-dimensional semantic screening, purpose-scoped abstention.
Controlled lexical features are evidence of mentions, not verified taxonomy or composition.
"""
import re,unicodedata
from collections import Counter
def norm(x):return re.sub(r"[\W_]+"," ",unicodedata.normalize("NFKC",str(x)).casefold()).strip()
def find(text,term):
 t=unicodedata.normalize("NFKC",term).casefold();s=unicodedata.normalize("NFKC",text).casefold()
 if re.search(r"[\u3400-\u9fff]",t):return t in s
 # Bound English words; whitespace/hyphen variants normalized.
 return bool(re.search(r"(?<![a-z0-9])"+re.escape(norm(t))+r"(?![a-z0-9])",norm(s)))
def tags(label,table):
 return {k for k,terms in table.items() if any(find(label,t) for t in terms)}
def features(label,grain,p):
 ids=tags(label,p["identity_lexicon"])
 # Disambiguate specific surface forms; no general biological classification.
 if "malabar_spinach" in ids:ids.discard("spinach")
 # Avoid treating chicken egg as an assertion that it contains chicken meat.
 if "egg" in ids and (find(label,"chicken egg") or find(label,"鸡蛋")):ids.discard("chicken")
 process=tags(label,p["process_terms"]);mods=tags(label,p["modifier_terms"]);parts=tags(label,p["component_terms"])
 s=unicodedata.normalize("NFKC",label).casefold()
 if re.match(r"^生(?:鸡|鸭|猪|牛|羊|鱼|虾|蟹|肉|蛋|米)",s) or s.endswith("(生)"):process.add("raw")
 if s.endswith("(熟)") or find(label,"cooked") or find(label,"熟制"):process.add("cooked")
 if find(label,"unprepared"):process.add("unprepared")
 if find(label,"tartare"):process.add("raw_state_inferred_from_dish_name")
 if find(label,"from fresh"):process.discard("fresh");process.add("fresh_input_origin")
 # Negative qualifier phrases are not positive tags.
 if find(label,"unsalted"):mods.discard("salted")
 if find(label,"unsweetened"):mods.discard("sweetened")
 if find(label,"unpeeled"):mods.discard("peeled")
 if find(label,"fat not added") or find(label,"no oil added"):mods.discard("added_oil")
 cooked=bool(process&{"boiled","steamed","fried","roasted","braised","cooked","blanched"})
 state="CONFLICTING_LABEL" if "raw" in process and cooked else "RAW_EXPLICIT" if "raw" in process else "COOKED_EXPLICIT" if cooked else "UNKNOWN"
 # Component/whole difference is only evidence about label and role.
 return {"base_mentions":sorted(ids),"process_mentions":sorted(process),"modifier_mentions":sorted(mods),"component_mentions":sorted(parts),
  "state":state,"native_grain":grain,"feature_origin":"BOUNDED_LEXICAL_MENTION_NOT_TAXONOMY_OR_RECIPE_TRUTH"}
def decide(a,b,p,scope_status=None,legacy_conflict=False):
 """All scientific use denied; navigation retained; semantic shortlist requires
 stronger observable evidence than a model rank. No synthetic exact relation."""
 x=features(a["label"],a["grain"],p);y=features(b["label"],b["grain"],p)
 A=set(x["base_mentions"]);B=set(y["base_mentions"]);P=set(x["process_mentions"]);Q=set(y["process_mentions"])
 M=set(x["modifier_mentions"]);N=set(y["modifier_mentions"]);I=set(x["component_mentions"]);J=set(y["component_mentions"])
 hard=[];unknown=[];role=[];related=[]
 if {x["state"],y["state"]}=={"RAW_EXPLICIT","COOKED_EXPLICIT"}:hard.append("EXPLICIT_RAW_COOKED")
 if "CONFLICTING_LABEL" in (x["state"],y["state"]):unknown.append("LABEL_STATE_INTERNAL_AMBIGUITY")
 for u,v in [("fresh","frozen"),("fresh","dried")]:
  if (u in P and v in Q) or (v in P and u in Q):hard.append("EXPLICIT_"+u.upper()+"_"+v.upper())
 for u,v in [("salted","unsalted"),("sweetened","unsweetened"),("peeled","unpeeled")]:
  if (u in M and v in N) or (v in M and u in N):hard.append("EXPLICIT_"+u.upper()+"_"+v.upper())
 if legacy_conflict:hard.append("UPSTREAM_EXPLICIT_RULE_HOLD")
 # Taxon mismatch only when explicit specific names on both sides.
 if ("spinach" in A and "malabar_spinach" in B) or ("malabar_spinach" in A and "spinach" in B):unknown.append("POTENTIAL_SPECIES_DISTINCTION_REQUIRES_AUTHORITY")
 if J-I or I-J:role.append("COMPONENT_WHOLE_OR_FORM_MISMATCH_CANDIDATE")
 if B-A:unknown.append("TARGET_ADDITIONAL_BASE_MENTION")
 if A-B:unknown.append("SOURCE_BASE_MENTION_NOT_RETAINED")
 if N-M:unknown.append("TARGET_UNDECLARED_MODIFIER")
 if M-N:unknown.append("SOURCE_MODIFIER_NOT_RETAINED")
 if Q-P:unknown.append("TARGET_UNDECLARED_PROCESS")
 if P-Q:unknown.append("SOURCE_PROCESS_NOT_RETAINED")
 if x["state"]!=y["state"] and "UNKNOWN" in (x["state"],y["state"]):unknown.append("ONE_SIDED_STATE_EVIDENCE")
 if scope_status is not None and scope_status!="CORE_RETAINED_DEV":role.append("TARGET_EXTENSION_OR_SCOPE_HOLD")
 # Roles not equivalent: candidate review can compare same grain, or an ingredient
 # reference to a food concept. Other cross-grain routes need explicit review.
 if x["native_grain"]!=y["native_grain"]:
  if not (y["native_grain"]=="ONTOLOGY_FOOD_PRODUCT_CLASS" and (x["native_grain"]=="INGREDIENT_REFERENCE" or norm(a["label"])==norm(b["label"]))):role.append("DIFFERENT_NATIVE_GRAIN")
 exact_surface=bool(norm(a["label"])) and norm(a["label"])==norm(b["label"])
 anchor=bool(A&B) or exact_surface
 if exact_surface:related.append("SAME_NORMALIZED_SURFACE_NOT_IDENTITY")
 if A&B:related.append("SHARED_CONTROLLED_MENTION")
 if hard:status="BLOCK_EXPLICIT_CONFLICT"
 elif role:status="HOLD_ROLE_OR_SCOPE"
 elif unknown:status="HOLD_MISSING_OR_AMBIGUOUS_CONDITION"
 elif not anchor:status="HOLD_NO_OBSERVABLE_IDENTITY_ANCHOR"
 else:status="REVIEW_ELIGIBLE_DEV_ONLY"
 return {"source_dimensions":x,"target_dimensions":y,"explicit_conflicts":sorted(set(hard)),"unresolved_conditions":sorted(set(unknown)),
 "role_conditions":sorted(set(role)),"identity_evidence":related,"disposition":status,
 "concept_review_eligible":status=="REVIEW_ELIGIBLE_DEV_ONLY","concept_equivalence":"HOLD","nutrient_transfer":"HOLD","physical_identity":"HOLD",
 "training":"HOLD","mapping_release":"HOLD","navigation":"CURATION_DEV_ONLY","source_relation_to_target":"UNRESOLVED"}
