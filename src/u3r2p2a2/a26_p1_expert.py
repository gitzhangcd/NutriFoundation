"""A2.6-P1 expert task envelope/queue validation, not a truth validator.
Pure functions. No actual data, model, expert dispatch, file import, or Gold."""
from a26_p1_semantic_policy import DIMS,need,SUPPORT
from collections import Counter
from jsonschema import Draft202012Validator
import json,re
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def expected_items(queue):
 out={}
 for x in queue["dimensions"]:
  k=("source_dimensions",x["dimension"]);need(k not in out and k[1] in DIMS,"QUEUE_DIMENSION");out[k]=x
 need({k[1] for k in out}==set(DIMS),"QUEUE_EIGHT_DIMENSIONS")
 for x in queue["edges"]:
  field=x["field"];i=x["zero_based_index"]
  need(field in ("independent_candidates","hard_negatives") and type(i) is int and i>=0,"QUEUE_EDGE_KEY")
  k=(field,str(i));need(k not in out,"QUEUE_DUP_ITEM");out[k]=x
 for field in ("independent_candidates","hard_negatives"):
  ix=sorted(int(k[1]) for k in out if k[0]==field);need(ix==list(range(len(ix))),"QUEUE_EDGE_INDEX_CLOSURE")
 return out
def validate_phase_a_freeze(receipt,task,expert_id):
 # Receipt authenticity, source/evidence truth, actual isolation and
 # qualification require separate operator review; this checks contract only.
 need(receipt["version"]=="A2.6-P1-EXPERT-PHASE-A-FREEZE-v0.1" and receipt["status"]=="SOURCE_ONLY_REVIEW_FROZEN" and receipt["task_id"]==task["task_id"],"PHASE_A_SCOPE")
 need(receipt["reviewer_id"]==expert_id and receipt["source_packet_sha256"]==task["source_packet_sha256"] and receipt["input_hashes"]==task["phase_a"]["allowed_inputs"],"PHASE_A_PIN")
 need(receipt["completed_cases"]==32 and receipt["rank_access"] is False and receipt["agy_reference_access"] is False and receipt["prior_risk_label_access"] is False and receipt["scientific_release_authorized"] is False,"PHASE_A_BOUNDARY")
 need(isinstance(receipt["signed_attestation"],str) and receipt["signed_attestation"].strip(),"PHASE_A_ATTESTATION")
 need(set(receipt["output_file_hashes"])=={"SourceOnlyReviewRecords.jsonl","PhaseAExecutionManifest.json"} and all(isinstance(h,str) and re.fullmatch(r"[a-f0-9]{64}",h) for h in receipt["output_file_hashes"].values()),"PHASE_A_OUTPUT_PINS")
def validate_phase_b(result,queue,original,phase_a_sha,task,validator,phase_a_reviewer_id,admitted_extra_evidence=()):
 need(validator.is_valid(result),"EXPERT_RESPONSE_SCHEMA")
 need(result["case_ordinal"]==queue["ordinal"] and result["reference_record_sha256"]==queue["reference_record_sha256"] and result["source_packet_sha256"]==task["source_packet_sha256"] and result["source_only_freeze_sha256"]==phase_a_sha,"EXPERT_BINDING")
 need(result["reviewer_id"]==phase_a_reviewer_id,"PHASE_A_REVIEWER_BINDING")
 need(result["no_rank_access"] is True and result["scientific_release_authorized"] is False,"EXPERT_SCOPE")
 need(all(result[k].strip() for k in ("reviewer_id","qualification_basis","conflict_of_interest","prior_exposure","signed_attestation")),"EXPERT_ATTESTATION")
 expected=expected_items(queue)
 need(set(expected)=={("source_dimensions",k) for k in original["source_dimensions"]}|{(f,str(i)) for f in ("independent_candidates","hard_negatives") for i in range(len(original[f]))},"EXPERT_QUEUE_ORIGINAL_CLOSURE")
 need(len(result["items"])==len(expected),"EXPERT_ITEM_COUNT")
 actual={}
 for d in result["items"]:
  k=(d["field"],d["item_key"])
  need(k in expected and k not in actual,"EXPERT_ITEM_CLOSURE");actual[k]=d
 need(set(actual)==set(expected),"EXPERT_ITEM_CLOSURE")
 # New evidence must be independently verified by operator and passed in
 # through an explicitly authorized addendum; no arbitrary evidence accepted.
 available={canonical(e) for e in original["evidence"]}|{canonical(e) for e in admitted_extra_evidence}
 stats=Counter()
 for k,d in actual.items():
  field,item=k;decision=d["decision"];reason=d["reason_code"];stats[decision]+=1
  need(d["rationale"].strip() and all(canonical(e) in available for e in d["evidence"]),"EXPERT_EVIDENCE_CARRIER")
  roles={e["role"] for e in d["evidence"]}
  if decision in ("UNRESOLVED","ABSTAIN"):continue
  old=original[field][item if field=="source_dimensions" else int(item)]
  if field=="source_dimensions":
   v=old if decision=="ACCEPT" else d["proposed_judgment"]
   if decision=="REVISE":need(set(v)=={"value","state"},"DIMENSION_REVISION_FIELDS")
   state=v["state"];val=v["value"]
   need(state!="UNRESOLVED" and isinstance(val,str) and val.strip(),"USE_EXPLICIT_UNRESOLVED_DECISION")
   need("SOURCE_EXPLICIT" in roles,"DIMENSION_SOURCE_ANCHOR")
   if state=="EXTERNAL_SUPPORTED":need("EXTERNAL_DOCUMENTATION" in roles,"EXTERNAL_DIMENSION_PROOF_REQUIRED")
   continue
  need({"SOURCE_EXPLICIT","TARGET_EXPLICIT"}<=roles,"EDGE_DOUBLE_ANCHOR")
  # A selected target anchor must actually be that target, not another edge.
  need(any(e["role"]=="TARGET_EXPLICIT" and e["locator"]==old["target_locator"] for e in d["evidence"]),"EDGE_TARGET_ANCHOR")
  if decision=="ACCEPT":
   if field=="hard_negatives":
    need(old["conflict_type"]!="UNRESOLVED_OTHER","UNRESOLVED_NOT_ACCEPTED_NEGATIVE")
    if old["conflict_type"]=="TARGET_SPECIFIC_CONDITION":need(reason=="EXPLICIT_CONFLICT","CONDITION_UNKNOWN_NOT_NEGATIVE")
   else:
    need(old["relation"]!="RELATED" or old["applicability"]=="RELATED_ONLY","RELATED_APPLICABILITY")
    need(old["applicability"]!="RELATED_ONLY" or old["relation"]=="RELATED","RELATED_APPLICABILITY")
   continue
  v=d["proposed_judgment"];disp=v.get("edge_disposition")
  if disp=="SUPPORTED_CANDIDATE":
   need(set(v)=={"edge_disposition","relation","applicability","conditions"},"SUPPORTED_REVISION_FIELDS")
   rel=v["relation"];app=v["applicability"]
   need(rel in SUPPORT and app!="UNRESOLVED","SUPPORTED_RELATION")
   need((rel=="RELATED")== (app=="RELATED_ONLY"),"RELATED_APPLICABILITY")
   if rel=="CONDITIONAL" or app=="CONDITIONAL_CONCEPT_CANDIDATE":need(bool(v["conditions"]) and app=="CONDITIONAL_CONCEPT_CANDIDATE","CONDITIONAL_SUPPORT")
  elif disp=="VERIFIED_NEGATIVE":
   need(set(v)=={"edge_disposition","conflict_type"} and v["conflict_type"]!="UNRESOLVED_OTHER","NEGATIVE_REVISION_FIELDS")
   if v["conflict_type"]=="TARGET_SPECIFIC_CONDITION":need(reason=="EXPLICIT_CONFLICT","CONDITION_UNKNOWN_NOT_NEGATIVE")
  elif disp=="REVIEWED_UNRESOLVED":need(set(v)=={"edge_disposition"},"UNRESOLVED_REVISION_FIELDS")
  else:raise ValueError("EDGE_DISPOSITION")
 return {"items_verified":len(expected),"decisions":dict(stats),"scientific_truth_validated":False,"scientific_release_authorized":False}
