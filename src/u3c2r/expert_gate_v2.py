"""Expert draft submission gate. No qualified reviewer registry is bundled.
Trust anchor is a separately PI-approved authority manifest hash, not a reviewer
self-assertion. Evidence and candidate identities are checked; scientific validity
still requires a qualified expert and independent adjudication.
"""
import sys,pathlib as P,json,hashlib
from jsonschema import Draft202012Validator,FormatChecker
from prepare_expert_v2 import require,sha,canon,load,digest
HERE=P.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"u3c1"))
from run_c1 import parse_standards,key
SCHEMA="schemas/udf/u3c2r/ExpertAdjudicationResponse_v0.2.schema.json"
SYSTEM_VERSION={"FoodOn":"2026-09-20","FDC_SR_Legacy":"2018-04","FNDDS":"2015-16"}
class StandardInput:
 def __init__(self,root):self.root=root
def checked(root,path,h):
 q=root/path;p=q.resolve();require(p.is_relative_to(root) and q.is_file() and not q.is_symlink(),"AUTHORITY_OR_EVIDENCE_PATH")
 require(sha(p)==h,"AUTHORITY_OR_EVIDENCE_HASH");return p
def validate_schema(response,schema):
 e=next(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(response),None)
 require(e is None,"EXPERT_RESPONSE_SCHEMA")
def indexed(response,refs):
 require(isinstance(refs,list) and all(type(i) is int and 0<=i<len(response["evidence"]) for i in refs),"EVIDENCE_INDEX_OUT_OF_RANGE")
 return [response["evidence"][i] for i in refs]
def validate_bound_content(response,task,vocab,target_inputs):
 require(response["task_ref"]==task["task_ref"] and response["review_id"]==task["review_id"] and response["source_legacy_ref"]==task["source_legacy_ref"],"EXPERT_TASK_IDENTITY")
 source_hash=task["source_artifact_sha256"];source_loc=canon(task["source_locator"])
 allowed={x["sha256"] for x in target_inputs}
 require(all(x["source_sha256"] in allowed|{source_hash} for x in response["evidence"]),"EVIDENCE_SOURCE_NOT_ALLOWED")
 # For source-explicit assertions, require the exact task source and locator.
 # Other source evidence can be human inference; the gate does not adjudicate its truth.
 for x in response["evidence"]:
  if x["evidence_role"]=="SOURCE_EXPLICIT":
   require(x["source_sha256"]==source_hash and x["source_locator"]==source_loc,"SOURCE_EVIDENCE_LOCATOR")
 if response["phase"]=="INITIAL_SOURCE_FIRST":
  for dim in response["source_reconstruction"].values():
   ev=indexed(response,dim["evidence_refs"])
   if dim["state"]=="SOURCE_EXPLICIT":require(any(x["evidence_role"]=="SOURCE_EXPLICIT" and x["source_sha256"]==source_hash and x["source_locator"]==source_loc for x in ev),"SOURCE_EXPLICIT_EVIDENCE_MISSING")
  candidates=set()
  for c in response["independent_candidates"]:
   sys=c["target_system"];require(c["target_version"]==SYSTEM_VERSION[sys],"EXPERT_TARGET_VERSION")
   k=key(sys,c["target_native_id"]);require(k in vocab and k not in candidates,"EXPERT_TARGET_ID_UNVERIFIED")
   candidates.add(k);z=vocab[k]
   require(not z["deprecated"] and c["target_label"].strip()==z["label"].strip() and c["target_locator"]==z["locator"],"EXPERT_TARGET_LABEL_LOCATOR")
   ev=indexed(response,c["evidence_refs"])
   target_hashes={x["sha256"] for x in target_inputs if x["path"] in z["locator"]}
   require(bool(target_hashes) and any(x["evidence_role"]=="TARGET_EXPLICIT" and x["source_sha256"] in target_hashes and x["source_locator"]==z["locator"] for x in ev),"TARGET_EVIDENCE_LOCATOR")
 else:
  for c in response["edge_judgments"]:indexed(response,c["evidence_refs"])
class ExpertResponseGate:
 """Real submission entry. No ability to authorize dispatch itself.
 An authority bundle must be issued by the trusted controller after actual
 reviewer qualification and isolation verification; caller supplies expected
 SHA256 from that independent authorization channel. No such bundle exists yet.
 """
 def __init__(self,root,packet,packet_report_sha,authority_path=None,authority_sha=None):
  self.root=root.resolve();self.packet=packet.resolve()
  require(self.packet.is_relative_to(self.root/"runs/B2/U3-B/C2/R1"),"PACKET_PATH")
  require(authority_path is not None and authority_sha is not None,"EXPERT_AUTHORITY_NOT_PROVISIONED")
  authority=checked(self.root,authority_path,authority_sha)
  a=load(authority)
  require(a["status"]=="CONTROLLER_AUTHORIZED_EXPERT_DRAFT_REVIEW" and a["reviewer_access_isolation_verified"] is True and a["scientific_release"] is False,"EXPERT_DISPATCH_NOT_AUTHORIZED")
  require(a["packet_report_sha256"]==packet_report_sha and a["packet_path"]==str(self.packet.relative_to(self.root)),"EXPERT_PACKET_AUTHORITY")
  rpt=checked(self.root,str((self.packet/"ExpertPacketR1Report.json").relative_to(self.root)),packet_report_sha);self.report=load(rpt)
  self.schema=load(checked(self.root,SCHEMA,self.report["response_schema_sha256"]))
  phasea=self.packet/"reviewer_source_only";phaseb=self.packet/"controller_restricted"
  qp=checked(self.root,str((phasea/"ExpertSourceFirstQueue.json").relative_to(self.root)),self.report["phase_a_queue_sha256"])
  mp=checked(self.root,str((phasea/"TargetReferenceManifest.json").relative_to(self.root)),self.report["phase_a_reference_manifest_sha256"])
  self.tasks={x["task_ref"]:x for x in load(qp)};self.target_inputs=load(mp)["reference_inputs"]
  for x in self.target_inputs:checked(self.root,x["path"],x["sha256"])
  self.vocab,_=parse_standards(StandardInput(self.root));self.authority=a
  self._comparison_path=phaseb/"ExpertComparisonHidden.json"
  self._assignments={}
  for x in a["assignments"]:
   require(x["task_ref"] in self.tasks and x["task_ref"] not in self._assignments,"EXPERT_ASSIGNMENT_TASK")
   require(x["reviewer_role"] in self.tasks[x["task_ref"]]["required_roles"],"EXPERT_ASSIGNMENT_ROLE")
   q=checked(self.root,x["qualification_evidence_path"],x["qualification_evidence_sha256"])
   require(x["qualification_evidence_ref"]==str(q.relative_to(self.root))+"@"+x["qualification_evidence_sha256"],"QUALIFICATION_EVIDENCE_IDENTITY")
   self._assignments[x["task_ref"]]=x
 def initial(self,response):
  validate_schema(response,self.schema);require(response["phase"]=="INITIAL_SOURCE_FIRST","INITIAL_PHASE")
  task=self.tasks.get(response["task_ref"]);assignment=self._assignments.get(response["task_ref"])
  require(task is not None and assignment is not None,"EXPERT_NOT_ASSIGNED")
  require(all(response[k]==assignment[k] for k in ("reviewer_id","reviewer_role","qualification_evidence_ref")),"EXPERT_ASSIGNMENT_IDENTITY")
  require(response["prior_candidate_exposure"]!="UNKNOWN","EXPERT_EXPOSURE_UNRESOLVED")
  checked(self.root,task["source_access"]["path"],task["source_artifact_sha256"])
  validate_bound_content(response,task,self.vocab,self.target_inputs)
  return {"decision":"ACCEPT_DRAFT_FOR_CONTROLLER_REVIEW","scientific_reference_qualified":False,"mapping_release_authorized":False}
 def post(self,response):
  validate_schema(response,self.schema);require(response["phase"]=="POST_INITIAL_COMPARISON","POST_PHASE")
  t=response["task_ref"];task=self.tasks.get(t);a=self._assignments.get(t)
  require(task is not None and a is not None and all(response[k]==a[k] for k in ("reviewer_id","reviewer_role","qualification_evidence_ref")),"EXPERT_ASSIGNMENT_IDENTITY")
  # Crucially, no hidden comparison file is opened until an approved explicit
  # unblind record binds this exact case, initial freeze and packet.
  matches=[x for x in self.authority.get("unblind_authorizations",[]) if x["task_ref"]==t]
  require(len(matches)==1,"UNBLIND_NOT_AUTHORIZED")
  u=matches[0];require(response["explicit_unblind_authorization_ref"]==u["authorization_ref"] and response["initial_frozen_sha256"]==u["initial_frozen_sha256"] and response["comparison_packet_sha256"]==u["comparison_packet_sha256"]==self.report["phase_b_packet_sha256"],"UNBLIND_IDENTITY")
  freeze=load(checked(self.root,u["initial_freeze_receipt_path"],u["initial_freeze_receipt_sha256"]))
  require(freeze["status"]=="INITIAL_EXPERT_DRAFT_FROZEN" and freeze["task_ref"]==t and freeze["response_sha256"]==u["initial_frozen_sha256"],"INITIAL_FREEZE_RECEIPT")
  initial=load(checked(self.root,freeze["response_path"],freeze["response_sha256"]));self.initial(initial)
  cp=checked(self.root,str(self._comparison_path.relative_to(self.root)),u["comparison_packet_sha256"]);cc=[x for x in load(cp) if x["task_ref"]==t];require(len(cc)==1,"POST_PACKET_TASK")
  keys={x["comparison_evidence_key"] for x in cc[0]["priority_evidence"]}
  submitted=[x["comparison_evidence_key"] for x in response["edge_judgments"]]
  require(len(submitted)==len(set(submitted)) and set(submitted)==keys,"POST_EDGE_EVIDENCE_CLOSURE")
  validate_bound_content(response,task,self.vocab,self.target_inputs)
  return {"decision":"ACCEPT_POST_INITIAL_DRAFT_FOR_CONTROLLER_REVIEW","scientific_reference_qualified":False,"mapping_release_authorized":False}
