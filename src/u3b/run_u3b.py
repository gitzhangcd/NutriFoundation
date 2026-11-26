#!/usr/bin/env python3
"""U3-B local multilingual development retrieval; no independent Gold or release.
Pinned U2-C admission validates all endpoint objects. Original Critic packets untouched.
"""
import argparse, pathlib as P, sys, json, copy, collections as C, math, time, re, hashlib
from datetime import datetime,timezone
HERE=P.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"u2c"),str(HERE.parent/"b0")]
from core import *
from runtime import verify
from admission import Admission
from profile_nutridata_core_links import read_core
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from jsonschema import Draft202012Validator,FormatChecker
V="UDF-U3B-PILOT-0.1"
def readj(p):return json.loads(p.read_text(encoding="utf8"))
def file(root,path,h):
 p=(root/path).resolve();require(p.is_relative_to(root) and p.is_file() and not p.is_symlink() and sha(p)==h,"PINNED_INPUT_DRIFT");return p
def linesout(p,rs):
 with p.open("x",encoding="utf8") as f:
  for x in rs:f.write(canon(x)+"\n")
def shape(props):return {"type":"object","properties":props,"required":list(props),"additionalProperties":False}
def make_schema(root):
 # Version extension of the U2-C CommonEnvelope; prior 42-kind schema is not edited.
 s=readj(root/"schemas/udf/u2c/UDF_U2C_UnifiedContract_v0.1.schema.json");defs={k:copy.deepcopy(s["$defs"][k]) for k in ("ref","slot","CommonEnvelope")}
 e=defs["CommonEnvelope"]["properties"];e["kind"]={"enum":["PilotMethod","QueryContextRecord","SemanticCandidateRecord"]}
 e["schema_version"]={"const":V};e["contract_version"]={"const":V}
 e["governance"]["properties"]["stage"]={"const":"U3-B"};e["governance"]["properties"]["policy_version"]={"const":V}
 S={"type":"string"};R={"$ref":"#/$defs/ref"};H={"type":"string","pattern":"^[a-f0-9]{64}$"}
 STR={"type":"array","items":S};N={"type":"number","minimum":-1.000001,"maximum":1.000001}
 nullable_rank={"type":["integer","null"],"minimum":1}
 payloads={
 "PilotMethod":shape({"profile_sha256":H,"model_manifest_sha256":H,"model_revision":S,"model_name":S,"model_sha256":H,"tokenizer_sha256":H,
 "target_count":{"type":"integer","minimum":1},"target_scope_counts":{"type":"object","additionalProperties":{"type":"integer","minimum":1}},
 "model_execution":S,"score_interpretation":S,"top_k_pool":{"type":"integer","minimum":1},"top_k_shortlist":{"type":"integer","minimum":1},"retrieval_method":S}),
 "QueryContextRecord":shape({"source_ref":R,"source_legacy_ref":R,"source_anchor_ref":R,"source_scope":S,"source_grain":S,"cohort":{"enum":["PAIRED_DEV","FRESH_DEV"]},
 "native_label":S,"native_alias_raw":STR,"native_ingredient_names":STR,"state_tokens":STR,"artifact_sha256":H,
 "source_locator":{"type":"object"},"context_locator":{"type":"object"},"label_query":S,"context_query":S,
 "baseline_candidate_count":{"type":["integer","null"],"minimum":0},"context_qualification":{"const":"SOURCE_LABEL_AND_REFERENCE_RECIPE_ONLY"}}),
 "SemanticCandidateRecord":shape({"source_ref":R,"target_ref":R,"source_legacy_ref":R,"target_legacy_ref":R,"query_ref":R,"method_ref":R,
 "source_anchor_ref":R,"target_anchor_ref":R,"source_grain":S,"target_grain":S,"target_scope":S,
 "label_rank":nullable_rank,"context_rank":nullable_rank,"label_cosine":N,"context_cosine":N,
 "fusion_score":{"type":"number","minimum":0},"pool_rank":{"type":"integer","minimum":1},
 "selected_rank":nullable_rank,"review_route":{"enum":["AMBER","RED"]},"risk_flags":STR,
 "candidate_status":{"enum":["SHORTLIST_PENDING","HARD_NEGATIVE_CANDIDATE","UNSELECTED_POOL"]},
 "source_relation_to_target":{"const":"UNRESOLVED"},"direction":{"const":"SOURCE_RELATION_TO_TARGET"},
 "review_status":{"const":"PENDING"},"accepted_equivalence":{"const":False},"physical_instance_link":{"const":False},
 "measurement_qualification":{"const":"HOLD"},"permitted_purposes":{"const":["CURATION_DEV"]},"score_interpretation":{"const":"RANK_ONLY_NOT_PROBABILITY"}})}
 for k,p in payloads.items():defs[k]={"allOf":[{"$ref":"#/$defs/CommonEnvelope"},{"properties":{"kind":{"const":k},"payload":p}}]}
 x={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:nutrifoundation:udf:u3b:pilot:0.1","$defs":defs,
 "oneOf":[{"$ref":"#/$defs/"+k} for k in payloads]}
 Draft202012Validator.check_schema(x);return x
def validator(s):
 defs=s["$defs"];return {k:Draft202012Validator({"$schema":s["$schema"],"$defs":defs,"$ref":"#/$defs/"+k},format_checker=FormatChecker()) for k in ("PilotMethod","QueryContextRecord","SemanticCandidateRecord")}
def obj(kind,key,p,clock,prov,dep,rights):
 o={"object_id":"u3b:"+kind+":"+digest([V,key])[:40],"kind":kind,"schema_version":V,"contract_version":V,
 "lifecycle":"DRAFT","producer_role":"U3B_LOCAL_GENERATOR","created_time":clock,"clock_axis":"AUDIT_UTC",
 "provenance_refs":uniq(prov),"dependency_refs":uniq(dep),"source_class":"REAL_DATA","instance_class":"MIXED_CONSTRUCTED",
 "purpose_release_ref":pending("no research release authorized"),"purpose":"CURATION_DEV","supersedes_ref":na("first U3-B pilot revision"),"payload":p,
 "governance":{"legacy_ref":None,"legacy_schema_version":None,"stage":"U3-B","construction_class":"DRV","verification_scope":"PINNED_U2C_ADMISSION_AND_LOCAL_RETRIEVAL",
 "rights_domains":sorted(set(rights)),"release_status":"HOLD","policy_version":V}}
 return seal(o)
def validate_obj(o,vs,registry):
 err=next(vs[o["kind"]].iter_errors(o),None)
 require(err is None,"U3B_SCHEMA:"+("" if err is None else str(err.validator)+":"+"/".join(map(str,err.absolute_path))))
 revision_ok(o)
 require(all(r in registry for r in o["dependency_refs"]+o["provenance_refs"]),"U3B_ORPHAN_REF")
 p=o["payload"]
 if o["kind"]=="SemanticCandidateRecord":
  a=registry[p["source_ref"]];b=registry[p["target_ref"]];q=registry[p["query_ref"]];m=registry[p["method_ref"]]
  require(a["kind"]==b["kind"]=="NativeVocabularyRecord" and q["kind"]=="QueryContextRecord" and m["kind"]=="PilotMethod","U3B_ENDPOINT_TYPE")
  require(q["payload"]["source_ref"]==p["source_ref"] and a["payload"]["source_anchor_ref"]==p["source_anchor_ref"] and b["payload"]["source_anchor_ref"]==p["target_anchor_ref"],"U3B_ANCHOR_MISMATCH")
  require(p["source_legacy_ref"]==a["governance"]["legacy_ref"] and p["target_legacy_ref"]==b["governance"]["legacy_ref"] and p["source_grain"]==a["payload"]["native_kind"] and p["target_grain"]==b["payload"]["native_kind"] and p["target_scope"]==b["payload"]["native_namespace"],"U3B_ENDPOINT_MISMATCH")
  require({p["source_ref"],p["target_ref"],p["query_ref"],p["method_ref"]}<=set(o["dependency_refs"]) and {p["source_anchor_ref"],p["target_anchor_ref"]}<=set(o["provenance_refs"]),"U3B_REQUIRED_DEPENDENCY")
  # Recompute rule-based explicit conflicts from admitted native labels, never trust a proposed flag.
  conflict=conflicts(a["payload"]["native_label"],b["payload"]["native_label"])
  require(all("STATE_CONFLICT:"+x in p["risk_flags"] for x in conflict),"U3B_CONFLICT_OMITTED")
  require(not conflict or (p["review_route"]=="RED" and p["selected_rank"] is None and p["candidate_status"]=="HARD_NEGATIVE_CANDIDATE"),"U3B_CONFLICT_SHORTLISTED")
  require((p["selected_rank"] is not None)==(p["candidate_status"]=="SHORTLIST_PENDING"),"U3B_SELECTED_STATUS")
  require((p["review_route"]=="RED")== (p["candidate_status"]=="HARD_NEGATIVE_CANDIDATE"),"U3B_ROUTE_STATUS")
  require(p["label_rank"] is not None or p["context_rank"] is not None,"U3B_NO_RETRIEVAL_EVIDENCE")
  require(set(a["governance"]["rights_domains"]+b["governance"]["rights_domains"])<=set(o["governance"]["rights_domains"]),"U3B_RIGHTS_DEPENDENCY")
 elif o["kind"]=="QueryContextRecord":
  a=registry[p["source_ref"]]
  require(a["kind"]=="NativeVocabularyRecord" and p["source_legacy_ref"]==a["governance"]["legacy_ref"] and p["source_anchor_ref"]==a["payload"]["source_anchor_ref"] and p["native_label"]==a["payload"]["native_label"] and p["artifact_sha256"]==a["payload"]["artifact_sha256"] and p["source_locator"]==a["payload"]["source_locator"],"U3B_QUERY_SOURCE")
 return True
def semantic_state(label):
 # Keep explicit states and cautious qualifiers, no scientific inference.
 return sorted(qualifiers(label))
def risk(a,b):
 s=a["payload"];t=b["payload"];x=conflicts(s["native_label"],t["native_label"])
 flags=["STATE_CONFLICT:"+z for z in x]
 if not semantic_state(s["native_label"]) or not semantic_state(t["native_label"]):flags.append("STATE_DIMENSION_UNRESOLVED")
 if s["native_kind"]!=t["native_kind"]:flags.append("GRAIN_OR_REFERENCE_ROLE_DIFFERENCE")
 if s["native_kind"]=="RECIPE_REFERENCE":flags.append("REFERENCE_RECIPE_NOT_TARGET_INSTANCE")
 return sorted(set(flags)),bool(x)
class Encoder:
 def __init__(self,model_dir,profile):
  opt=ort.SessionOptions();opt.intra_op_num_threads=profile["threads"];opt.inter_op_num_threads=1
  self.session=ort.InferenceSession(str(model_dir/"model_quantized.onnx"),sess_options=opt,providers=["CPUExecutionProvider"])
  self.tokenizer=Tokenizer.from_file(str(model_dir/"tokenizer.json"));self.tokenizer.enable_truncation(max_length=profile["max_tokens"])
  self.tokenizer.enable_padding(pad_id=self.tokenizer.token_to_id("<pad>"),pad_token="<pad>")
  self.bs=profile["batch_size"]
 def encode(self,texts):
  out=[]
  for start in range(0,len(texts),self.bs):
   z=self.tokenizer.encode_batch(texts[start:start+self.bs]);m=np.array([x.attention_mask for x in z],dtype=np.int64)
   v={"input_ids":np.array([x.ids for x in z],dtype=np.int64),"attention_mask":m,"token_type_ids":np.array([x.type_ids for x in z],dtype=np.int64)}
   a=self.session.run(None,{x.name:v[x.name] for x in self.session.get_inputs()})[0]
   b=((a*m[:,:,None]).sum(1)/m.sum(1)[:,None]).astype(np.float32);n=np.linalg.norm(b,axis=1,keepdims=True)
   require(np.isfinite(b).all() and (n>0).all(),"EMBEDDING_INVALID");out.append(b/n)
  return np.concatenate(out,axis=0)
def top(scores,k,ids):
 # Exact dense search, deterministic tie-break by immutable target ID.
 return sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))[:k]
def get_ctx(root,rt,selected,profile):
 wanted=C.defaultdict(dict);result={}
 for o in selected:
  p=o["payload"];wanted[p["native_namespace"]][str(p["native_key"])]=o
 for ns,keys in wanted.items():
  files=[v for v in rt.b.resolver.values() if v["namespace"]==ns];require(len(files)==1,"NUTRIDATA_SOURCE_RESOLVER")
  f=files[0];path=file(root,f["path"],f["sha256"])
  for rn,row,j,l in read_core(path):
   key=str(row["item_id"])
   if key not in keys:continue
   o=keys[key];p=o["payload"];require(str(j["name"])==p["native_label"] and p["artifact_sha256"]==f["sha256"] and p["source_locator"]["excel_row"]==rn,"QUERY_CONTEXT_SOURCE_DRIFT")
   al=[j["alias"]] if isinstance(j.get("alias"),str) and j["alias"].strip() else []
   names=[]
   if ns.endswith(":dish"):
    for x in j.get("major",[])[:profile["context_ingredient_name_limit"]]:
     if isinstance(x.get("name"),str) and x["name"].strip():names.append(x["name"])
   result[ref(o)]={"aliases":al,"ingredients":names,"locator":{"excel_row":rn,"fields":["detail_json.name","detail_json.alias"]+(["detail_json.major[*].name"] if ns.endswith(":dish") else []),"ingredient_limit":profile["context_ingredient_name_limit"],"quantity_not_used":True}}
  require(sha(path)==f["sha256"],"QUERY_SOURCE_CHANGED")
 require(len(result)==len(selected),"CONTEXT_COMPLETENESS");return result
def main(root,profile_path,out):
 root=root.resolve();out=out.resolve();require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B"),"NEW_PILOT_RUN_REQUIRED")
 p=readj(profile_path);require(p["release_authorized"] is False,"PILOT_RELEASE")
 b=p["baseline"];mp=file(root,b["manifest"],b["manifest_sha256"]);file(root,b["receipt"],b["receipt_sha256"]);file(root,b["integration"],b["integration_sha256"])
 run=root/b["run"];file(root,str((run/"U2CExecutionReport.json").relative_to(root)),b["execution_sha256"]);file(root,str((run/"private/partition_manifest.json").relative_to(root)),b["partition_manifest_sha256"])
 rt,vr=verify(root,mp,run);adm=Admission(rt)
 print("U2C_FULL_REPLAY",vr["all_replayed"],flush=True)
 original_q=[]
 for x in p["excluded_queues"]:original_q+=readj(file(root,x["path"],x["sha256"]))
 excluded={x["source_ref"] for x in original_q};require(len(excluded)==len(original_q)==44,"FROZEN_QUEUE_COUNT")
 route_file=file(root,p["old_routes"]["path"],p["old_routes"]["sha256"]);old={x["source_ref"]:x for x in lines(route_file)}
 allv={ref(o):o for o in rt.b.by["NativeVocabularyRecord"]}
 paired=[r for r,x in old.items() if x["source_scope"] in p["query_scopes"] and r not in excluded]
 fresh=[]
 for ns in p["query_scopes"]:
  pool=[r for r,o in allv.items() if o["payload"]["native_namespace"]==ns and r not in old and r not in excluded]
  fresh+=sorted(pool,key=lambda r:digest([p["selection_salt"],allv[r]["object_id"]]))[:p["fresh_per_scope"]]
 selected=paired+fresh;require(len(selected)==len(set(selected)) and not set(selected)&excluded,"QUERY_ISOLATION")
 target_ids={ns:sorted([r for r,o in allv.items() if o["payload"]["native_namespace"]==ns],key=lambda r:allv[r]["object_id"]) for ns in p["target_scopes"]}
 # Admitted projections, including exact legacy and new revision identities. No direct scientific consumption.
 projections={};registry=dict(rt.b.idx)
 for r in selected+[x for ids in target_ids.values() for x in ids]:
  o=adm.view(r);projections[r]=o;registry[ref(o)]=o
 require(adm.request("inspect",selected)["decision"]=="ALLOW","U2C_INSPECTION_DENIED")
 print("ADMITTED_VOCABULARY",len(projections),"queries",len(selected),flush=True)
 ctx=get_ctx(root,rt,[projections[r] for r in selected],p)
 model_dir=root/p["model_dir"];mm=readj(file(root,str((model_dir/"ModelManifest.json").relative_to(root)),p["model_manifest_sha256"]))
 require(mm["revision"]==p["model_revision"] and len(mm["files"])==3,"MODEL_REVISION")
 for x in mm["files"]:require(x["status"]=="DOWNLOADED_HASH_MATCH" and sha(model_dir/x["file"])==x["sha256"],"MODEL_HASH")
 model_files={x["file"]:x["sha256"] for x in mm["files"]}
 clock=datetime.now(timezone.utc).isoformat();schema=make_schema(root);vs=validator(schema);enc=Encoder(model_dir,p)
 method=obj("PilotMethod",[p["version"],sha(profile_path),p["model_manifest_sha256"]],{"profile_sha256":sha(profile_path),"model_manifest_sha256":p["model_manifest_sha256"],"model_revision":mm["revision"],"model_name":mm["model"],"model_sha256":model_files["model_quantized.onnx"],"tokenizer_sha256":model_files["tokenizer.json"],
 "target_count":sum(map(len,target_ids.values())),"target_scope_counts":{k:len(v) for k,v in target_ids.items()},"model_execution":"ONNX CPU, masked mean pooling and L2 normalization; query/passage prefixes","score_interpretation":p["score_interpretation"],
 "top_k_pool":p["pre_rank_top_k_per_form_per_scope"],"top_k_shortlist":p["output_top_k_per_scope"],"retrieval_method":"two query forms, exact dense cosine top-k, union before conflict screening, RRF k=60; no LLM relation adjudication"},clock,[],[],["MODEL_LICENSE_REVIEW"])
 validate_obj(method,vs,registry);registry[ref(method)]=method
 queries=[];query_by={}
 for r in selected:
  o=projections[r];a=o["payload"];x=ctx[ref(o)];state=semantic_state(a["native_label"])
  label="query: "+a["native_label"];extra=[]
  if x["aliases"]:extra.append("别名："+ "；".join(x["aliases"]))
  if x["ingredients"]:extra.append("参考配方食材（原生顺序，非实物组成）："+"、".join(x["ingredients"]))
  if state:extra.append("explicit label state: "+", ".join(state))
  contextual=label+("；"+"；".join(extra) if extra else "")
  pay={"source_ref":ref(o),"source_legacy_ref":r,"source_anchor_ref":a["source_anchor_ref"],"source_scope":a["native_namespace"],"source_grain":a["native_kind"],"cohort":"PAIRED_DEV" if r in old else "FRESH_DEV","native_label":a["native_label"],
       "native_alias_raw":x["aliases"],"native_ingredient_names":x["ingredients"],"state_tokens":state,"artifact_sha256":a["artifact_sha256"],"source_locator":a["source_locator"],"context_locator":x["locator"],
       "label_query":label,"context_query":contextual,"baseline_candidate_count":old[r]["candidate_count"] if r in old else None,"context_qualification":"SOURCE_LABEL_AND_REFERENCE_RECIPE_ONLY"}
  q=obj("QueryContextRecord",[o["object_id"],p["version"]],pay,clock,[a["source_anchor_ref"]],[ref(o),ref(method)],o["governance"]["rights_domains"]+["MODEL_LICENSE_REVIEW"])
  validate_obj(q,vs,registry);registry[ref(q)]=q;queries.append(q);query_by[r]=q
 qmat=enc.encode([q["payload"]["label_query"] for q in queries]+[q["payload"]["context_query"] for q in queries]);nq=len(queries)
 print("ENCODED_QUERIES",qmat.shape,flush=True)
 # Persist full top-k pool after exact similarity search; don't discard high-scoring conflicts.
 edges=[];per=C.defaultdict(C.Counter);selected_edges=C.defaultdict(list);all_edges=C.defaultdict(list);metrics=C.Counter();scope_report={};kpool=p["pre_rank_top_k_per_form_per_scope"];kout=p["output_top_k_per_scope"]
 for ns,ids in target_ids.items():
  tm=enc.encode(["passage: "+projections[r]["payload"]["native_label"] for r in ids])
  scores=qmat@tm.T;scope_counts=C.Counter()
  for i,r in enumerate(selected):
   q=query_by[r];qo=q["payload"];src=projections[r]
   a=top(scores[i],kpool,ids);b=top(scores[i+nq],kpool,ids);ar={j:k+1 for k,j in enumerate(a)};br={j:k+1 for k,j in enumerate(b)}
   f=lambda j:(1/(60+ar[j]) if j in ar else 0)+(1/(60+br[j]) if j in br else 0)
   pool=sorted(set(a)|set(b),key=lambda j:(-f(j),-max(float(scores[i,j]),float(scores[i+nq,j])),ids[j]))
   scope_counts["query_scope_pairs"]+=1;scope_counts["top20_intersection"]+=len(set(a)&set(b));scope_counts["top20_union"]+=len(pool)
   scope_counts["top1_changed"]+=a[0]!=b[0];pos=0
   for rank,j in enumerate(pool,1):
    t=projections[ids[j]];flags,red=risk(src,t)
    chosen=not red and pos<kout
    if chosen:pos+=1
    pay={"source_ref":ref(src),"target_ref":ref(t),"source_legacy_ref":r,"target_legacy_ref":ids[j],"query_ref":ref(q),"method_ref":ref(method),
         "source_anchor_ref":src["payload"]["source_anchor_ref"],"target_anchor_ref":t["payload"]["source_anchor_ref"],"source_grain":src["payload"]["native_kind"],"target_grain":t["payload"]["native_kind"],"target_scope":ns,
         "label_rank":ar.get(j),"context_rank":br.get(j),"label_cosine":float(scores[i,j]),"context_cosine":float(scores[i+nq,j]),"fusion_score":f(j),"pool_rank":rank,
         "selected_rank":pos if chosen else None,"review_route":"RED" if red else "AMBER","risk_flags":flags,"candidate_status":"HARD_NEGATIVE_CANDIDATE" if red else "SHORTLIST_PENDING" if chosen else "UNSELECTED_POOL",
         "source_relation_to_target":"UNRESOLVED","direction":"SOURCE_RELATION_TO_TARGET","review_status":"PENDING","accepted_equivalence":False,"physical_instance_link":False,"measurement_qualification":"HOLD","permitted_purposes":["CURATION_DEV"],"score_interpretation":"RANK_ONLY_NOT_PROBABILITY"}
    e=obj("SemanticCandidateRecord",[q["object_id"],t["object_id"],method["object_id"]],pay,clock,[pay["source_anchor_ref"],pay["target_anchor_ref"]],[ref(src),ref(t),ref(q),ref(method)],src["governance"]["rights_domains"]+t["governance"]["rights_domains"]+["MODEL_LICENSE_REVIEW"])
    validate_obj(e,vs,registry);registry[ref(e)]=e;edges.append(e);all_edges[r].append(ref(e));scope_counts["pool_edges"]+=1
    if red:scope_counts["hard_negative_candidates"]+=1;metrics["red_edges"]+=1
    if chosen:selected_edges[r].append(ref(e));scope_counts["shortlist_edges"]+=1
   scope_counts["query_scope_pairs_with_shortlist"]+=pos>0
  scope_report[ns]=dict(scope_counts)
  print("RETRIEVAL_SCOPE",ns,dict(scope_counts),flush=True)
 for q in queries:
  x=q["payload"];r=x["source_legacy_ref"];z=per[(x["cohort"],x["source_scope"])];z["queries"]+=1;z["old_has_candidate"]+=bool(x["baseline_candidate_count"]);z["new_has_shortlist"]+=bool(selected_edges[r]);z["queries_with_context_expansion"]+=x["label_query"]!=x["context_query"];z["pool_edges"]+=len(all_edges[r]);z["shortlist_edges"]+=len(selected_edges[r]);z["queries_with_red_pool"]+=any(registry[e]["payload"]["review_route"]=="RED" for e in all_edges[r])
 # New independent review preparation, separate from the frozen Gemini 44. Read only admitted legacy candidate records.
 old_red=set();high=set();old_edge_refs=C.defaultdict(list)
 for x in rt.b.by["AlignmentRecord"]:
  r=x["payload"]["source_ref"];o=rt.project(x,validate=False);p0=o["payload"]
  old_edge_refs[r].append(ref(o))
  if p0["review_route"]=="RED":old_red.add(r)
  elif p0["ranking_score"]>=0.9:high.add(r)
 rev_sources=[];strata={}
 for r in sorted(old_red-excluded):rev_sources.append(r);strata[r]="NEW_U2C_RULE_RED"
 for r in sorted(high-excluded-set(rev_sources),key=lambda r:digest([p["selection_salt"],"HIGH_AMBER",r]))[:p["review_queue"]["high_score_amber_sources"]]:rev_sources.append(r);strata[r]="HIGH_SCORE_AMBER"
 for ns in p["query_scopes"]:
  rr=[r for r in fresh if allv[r]["payload"]["native_namespace"]==ns and r not in rev_sources]
  for r in sorted(rr,key=lambda r:digest([p["selection_salt"],"FRESH_REVIEW",r]))[:p["review_queue"]["fresh_query_sources_per_scope"]]:rev_sources.append(r);strata[r]="FRESH_CHINESE_"+ns.rsplit(":",1)[-1]
 require(len(rev_sources)==len(set(rev_sources)) and not set(rev_sources)&excluded,"REVIEW_QUEUE_ISOLATION")
 blind=[];hidden=[]
 for i,r in enumerate(rev_sources,1):
  o=projections.get(r) or adm.view(r);a=o["payload"];rid="U3B-DEV-"+str(i).zfill(3)
  blind.append({"review_id":rid,"source_ref":r,"source_scope":a["native_namespace"],"source_native_label":a["native_label"],"native_kind":a["native_kind"],
    "question":"Independently recover source meaning, retrieve actual target IDs and directional relations, or unresolved; no generator result provided.","status":"NOT_REVIEWED"})
  hidden.append({"review_id":rid,"stratum":strata[r],"new_shortlist_refs":selected_edges[r],"new_pre_rank_pool_refs":all_edges[r],"u2c_prior_candidate_refs":old_edge_refs[r]})
 # Only now write new run. No original queue or independent Critic file accessed.
 out.mkdir(parents=True);private=out/"private";private.mkdir();tree=private/"typed_partitions";tree.mkdir()
 by=C.defaultdict(list)
 for o in [method]+queries+edges:
  d=o["governance"]["rights_domains"];part=d[0] if len(d)==1 else "MIXED_RESTRICTED_"+digest(d)[:16];by[part+"/"+o["kind"]+".jsonl"].append(o)
 fm={}
 for rel,rs in sorted(by.items()):
  f=tree/rel;f.parent.mkdir(parents=True,exist_ok=True);linesout(f,rs);fm[rel]={"rows":len(rs),"bytes":f.stat().st_size,"sha256":sha(f)}
 put(private/"partition_manifest.json",fm);put(private/"ReviewSourceOnlyQueue.json",blind);put(private/"ReviewCandidatesHidden.json",hidden)
 put(out/"U3B_PilotContract.schema.json",schema)
 require(all(sha(root/x["path"])==x["sha256"] for x in p["excluded_queues"]) and sha(route_file)==p["old_routes"]["sha256"],"UPSTREAM_MUTATION")
 rt.b.verify_files()
 summary={"status":"PASS_BOUNDED_MULTILINGUAL_GENERATOR_PILOT","contract_version":V,"utc":clock,"u2c_replayed_objects":vr["all_replayed"],"u2c_admitted_vocabulary_endpoints":len(projections),
 "query_cohort_counts":[{"cohort":k[0],"source_scope":k[1],**dict(v)} for k,v in sorted(per.items())],"paired_queries":len(paired),"fresh_queries":len(fresh),"excluded_old_queue":len(excluded),"excluded_paired_overlap":sum(r in excluded and x["source_scope"] in p["query_scopes"] for r,x in old.items()),
 "model":{"name":mm["model"],"revision":mm["revision"],"dimension":int(qmat.shape[1]),"local_inference":True,"onnxruntime":ort.__version__,"numpy":np.__version__,"file_hashes":model_files,"manifest_sha256":p["model_manifest_sha256"]},
 "target_scope_counts":{k:len(v) for k,v in target_ids.items()},"query_count":nq,"embedding_query_forms":2*nq,"target_count":sum(map(len,target_ids.values())),"scope_retrieval":scope_report,"pre_rank_pool_edges":len(edges),"shortlist_edges":sum(map(len,selected_edges.values())),"rule_hard_negative_candidates":metrics["red_edges"],
 "unique_queries_with_shortlist":sum(bool(selected_edges[r]) for r in selected),"typed_objects":1+len(queries)+len(edges),"rights_partitions":len({x.split("/")[0] for x in fm}),
 "review_queue":{"new_sources":len(blind),"strata":dict(C.Counter(strata.values())),"old_44_unchanged":True,"completed":0,"independent_critic_freeze_receipt_seen_at_start":(root/p["critique_dir"]/"CriticFreezeReceipt.json").is_file(),"no_critic_content_read":True},
 "mapping_release_count":0,"accepted_equivalence":0,"science_qualified":0,"reference_status":"HOLD_NO_INDEPENDENT_ADJUDICATED_REFERENCE","metrics_limit":"Fixed top-k neighbors imply coverage, not accuracy/recall. Paired cohort not independent, fresh cohort exploratory. No calibrated confidence.",
 "profile_sha256":sha(profile_path),"model_manifest_sha256":p["model_manifest_sha256"],"partition_manifest_sha256":sha(private/"partition_manifest.json"),"source_inputs_unchanged":True,
 "limitations":["no independent Critic or expert review yet; no actual mapping qualification","explicit state rules incomplete; grain differences unresolved","no original Food2K/VIREO raw labels; target universe limited to 3 pinned releases","reference recipe ingredients used as context only; no physical/quantity truth","dense retrieval uses primary target labels, no LLM semantic adjudication"]}
 put(out/"U3BGeneratorReport.json",summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile.resolve(),x.out)
