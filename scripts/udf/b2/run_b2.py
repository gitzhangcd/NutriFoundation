#!/usr/bin/env python3
"""Execute and persist B2/U3-A bounded development vocabulary and candidate retrieval."""
import argparse,pathlib as P,json,collections as C,sys,copy,hashlib,re
from vocabulary import *
from alignment import align,components,mapping_guard,FOODON,SR,FNDDS,NDI,NDD,Index,normalize,hard_conflicts,SEEDS

def closure_check(edges,nodes):
 indegree={k:0 for k in nodes};adj=C.defaultdict(list)
 for a,b in edges:
  require(a in nodes and b in nodes and a!=b,"ONTOLOGY_EDGE")
  indegree[b]+=1;adj[a].append(b)
 q=[k for k,n in indegree.items() if n==0];seen=0
 while q:
  a=q.pop();seen+=1
  for b in adj[a]:
   indegree[b]-=1
   if indegree[b]==0:q.append(b)
 require(seen==len(nodes),"ONTOLOGY_CYCLE")
 return seen
def ensure_ref(p,idx,k):require(p in idx and idx[p]["kind"]==k,"TYPED_REF_MISMATCH")
def guard_component(p):
 require(p["accepted_equivalence"] is False and p["relation_type"]=="UNRESOLVED" and p["review_status"]=="PENDING","COMPONENT_EQUIVALENCE_NOT_QUALIFIED")
 require(p["conversion"]=="NOT_AUTHORIZED" and p["measurement_qualification"]=="HOLD" and p["permitted_purposes"]==["CURATION_DEV"],"COMPONENT_CONVERSION_HOLD")
 if not p["unit_dimension_candidate_match"]:require(p["review_route"]=="RED","UNIT_CONFLICT_NOT_HELD")
def guard_code(p):
 require(p["target_cycle"]=="2015-16" and p["measurement_and_aggregation"]=="HOLD" and p["same_physical_instance"] is False,"FNDDS_CYCLE_OR_GRAIN")
 if p["status"]=="SAME_CYCLE_CODE_MATCH_CANDIDATE":
  require(re.fullmatch(r"[0-9]{8}",p["native_code"]) is not None and p["target_ars_ref"] and p["target_fdc_ref"],"FNDDS_CODE_KEY")
 else:require(p["status"].startswith(("HOLD","ARS_ONLY")),"CODE_STATUS")
 if p["status"]=="HOLD_CODE_DOMAIN_UNRESOLVED":
  require(p["target_ars_ref"] is None and p["target_fdc_ref"] is None,"SHORT_CODE_JOIN")
def validate_objects(objects):
 idx={}
 for o in objects:
  verify_obj(o);r=ref(o);require(r not in idx,"DUPLICATE_REVISION");idx[r]=o
  require(o["instance_class"] in ("REAL_SOURCE_GROUNDED","MIXED_CONSTRUCTED"),"INSTANCE_CLASS")
  require(o["purpose_release_ref"]["tag"]=="PENDING","UNAUTHORIZED_RELEASE")
 for r,o in idx.items():
  p=o["payload"];k=o["kind"]
  for x in o["dependency_refs"]+o["provenance_refs"]:
   require(x in idx and x!=r,"ORPHAN_OR_SELF_REF")
   if o["instance_class"]=="REAL_SOURCE_GROUNDED":require(idx[x]["instance_class"]=="REAL_SOURCE_GROUNDED","REAL_CONSTRUCTION_INFLATION")
  if k=="NativeVocabularyRecord":
   ensure_ref(p["source_anchor_ref"],idx,"VocabularyAnchorDraft");a=idx[p["source_anchor_ref"]]["payload"]
   require(p["native_key"]==a["native_key"] and p["artifact_sha256"]==a["artifact_sha256"] and p["source_locator"]==a["locator"] and p["native_namespace"]==a["scope"],"VOCAB_ANCHOR_MISMATCH")
  elif k=="VocabularyAnchorDraft":
   ensure_ref(p["source_snapshot_ref"],idx,"SourceSnapshotDraft")
   a=idx[p["source_snapshot_ref"]]["payload"];require(a["scope"]==p["scope"] and a["sha256"]==p["artifact_sha256"],"ANCHOR_SNAPSHOT_MISMATCH")
  elif k=="AlignmentRecord":
   mapping_guard(p)
   ensure_ref(p["source_ref"],idx,"NativeVocabularyRecord");ensure_ref(p["target_ref"],idx,"NativeVocabularyRecord");ensure_ref(p["method_version_ref"],idx,"MappingMethod")
   s=idx[p["source_ref"]]["payload"];t=idx[p["target_ref"]]["payload"]
   require(s["native_namespace"]!=t["native_namespace"] and s["native_kind"]==p["source_grain"] and t["native_kind"]==p["target_grain"],"MAPPING_NAMESPACE_GRAIN")
   require(set(p["source_anchor_refs"])=={s["source_anchor_ref"],t["source_anchor_ref"]},"MAPPING_ANCHOR")
   require(o["instance_class"]=="MIXED_CONSTRUCTED","MAPPING_REAL_INFLATION")
  elif k=="ComponentAlignmentCandidate":
   guard_component(p);ensure_ref(p["source_ref"],idx,"ComponentNativeField");ensure_ref(p["target_ref"],idx,"ComponentNativeField")
   require(p["source_unit"]==idx[p["source_ref"]]["payload"]["native_unit"] and p["target_unit"]==idx[p["target_ref"]]["payload"]["native_unit"],"COMPONENT_UNIT_DRIFT")
  elif k=="NativeCodeLinkCandidate":
   guard_code(p)
   if p["status"]=="SAME_CYCLE_CODE_MATCH_CANDIDATE":
    for key in ("target_ars_ref","target_fdc_ref"):ensure_ref(p[key],idx,"NativeVocabularyRecord")
    a=idx[p["target_ars_ref"]]["payload"];b=idx[p["target_fdc_ref"]]["payload"]
    require(a["native_key"]==b["native_key"]==p["native_code"] and a["native_label"].strip()==b["native_label"].strip(),"FNDDS_CODE_CARRIER_CONFLICT")
  elif k=="FNDDSCarrierCrosswalk":
   a=idx[p["ars_ref"]]["payload"];b=idx[p["fdc_ref"]]["payload"]
   require(p["cycle"]=="2015-16" and a["native_key"]==b["native_key"]==p["food_code"] and a["native_label"].strip()==b["native_label"].strip(),"FNDDS_CODE_CARRIER_CONFLICT")
   require(p["description_comparison"]==("RAW_EXACT" if a["native_label"]==b["native_label"] else "TRIMMED_EXACT_ONLY"),"CARRIER_DESCRIPTION_STATUS")
   require(p["same_release_not_independent"] and not p["semantic_equivalence_accepted"],"CARRIER_INDEPENDENCE_INFLATION")
  elif k=="SourceFamilyBinding":
   ensure_ref(p["native_ref"],idx,"NativeVocabularyRecord");ensure_ref(p["source_family_ref"],idx,"SourceFamily")
  elif k=="CanonicalFoodConceptCandidate":
   ensure_ref(p["seed_native_ref"],idx,"NativeVocabularyRecord")
   require(p["equivalence_class"]=="NOT_ASSIGNED" and p["review_status"]=="PENDING","CANONICAL_PROMOTION")
  elif k=="ComponentConceptCandidate":
   ensure_ref(p["source_field_ref"],idx,"ComponentNativeField");require(p["global_exact"] is False,"COMPONENT_PROMOTION")
 return idx
def main(root,out):
 root=root.resolve();out=out.resolve();require(not out.exists() and not out.is_relative_to(root/"source_data"),"OUTPUT_OVERWRITE_OR_SOURCE")
 v=Inventory(root).run()
 print("INVENTORY",len(v.records),"anchors",len(v.anchors),"scope",len(v.by_scope),flush=True)
 nodes=closure_check(v.foodon_edges,set(v.foodon_classes));print("FOODON_DAG",nodes,flush=True)
 method,edges,routes,anchors,blind,hidden,astats=align(v)
 print("ALIGNMENT",json.dumps({k:x for k,x in astats.items() if k!="source_coverage"},ensure_ascii=False),flush=True)
 fields,local,cmaps,cstats=components(v,method)
 carriers=[]
 for code in sorted(v.fndds_ars):
  a=v.fndds_ars[code];b=v.fndds_fdc[code]
  al=a["payload"]["native_label"];bl=b["payload"]["native_label"]
  require(al.strip()==bl.strip(),"CARRIER_LABEL_CONFLICT")
  carriers.append(obj("FNDDSCarrierCrosswalk",[a["object_id"],b["object_id"]],{"ars_ref":ref(a),"fdc_ref":ref(b),"food_code":code,"cycle":"2015-16",
      "status":"SAME_CYCLE_NATIVE_KEY_AND_DESCRIPTION_MATCH","description_comparison":"RAW_EXACT" if al==bl else "TRIMMED_EXACT_ONLY","same_release_not_independent":True,"semantic_equivalence_accepted":False,"measurement_qualification":"HOLD"},
      tuple(a["provenance_refs"]+b["provenance_refs"]),(ref(a),ref(b)),origin="DRV"))
 objects=list(v.snapshot_objects.values())+v.anchors+v.records+list(v.family_records.values())+v.family_links+v.snapme_links+carriers+[method]+edges+anchors+fields+local+cmaps
 idx=validate_objects(objects);print("VALIDATED",len(idx),flush=True)
 out.mkdir(parents=True);private=out/"private";private.mkdir();tbl=private/"typed_collections";tbl.mkdir()
 by=C.defaultdict(list)
 for o in objects:by[o["kind"]].append(o)
 manifest={}
 for k,rows in sorted(by.items()):
  p=tbl/(k+".jsonl");write_lines(p,rows);manifest[p.name]={"rows":len(rows),"bytes":p.stat().st_size,"sha256":sha(p)}
 # Independent on-disk readback, per-record byte-semantic and revision checks.
 seen=set()
 for n,m in manifest.items():
  p=tbl/n;require(sha(p)==m["sha256"],"COLLECTION_HASH");count=0
  with p.open(encoding="utf8") as h:
   for line in h:
    o=json.loads(line);r=ref(o);verify_obj(o)
    require(o["kind"]==p.stem and r in idx and r not in seen and canon(o)==canon(idx[r]),"PERSISTED_OBJECT_DRIFT")
    seen.add(r);count+=1
  require(count==m["rows"],"COLLECTION_ROW_COUNT")
 require(len(seen)==len(idx),"PERSISTED_CLOSURE")
 write_json(private/"collection_manifest.json",manifest)
 write_lines(private/"CandidateQueryRoutes.jsonl",routes);write_json(private/"ReviewSourceOnlyQueue.json",blind)
 write_json(private/"ReviewCandidatesHidden.json",hidden)
 write_json(private/"BilingualSeedDictionary.json",{"status":"AUTHORED_DEVELOPMENT_ONLY","seeds":SEEDS})
 write_lines(private/"FoodOnAssertedNamedParentEdges.jsonl",[{"child_iri":a,"parent_iri":b,"direction":"CHILD_TO_PARENT","source_relation_to_target":"BROADER_TARGET","assertion_scope":"ASSERTED_NAMED_SUBCLASS_ONLY","mapping_equivalence":False} for a,b in v.foodon_edges])
 # Aggregate-only reports. Do not publish raw names, individual IDs, anchor hashes tied to rows,
 # candidate values, or source-private metadata. Source snapshot file fingerprints are public receipts.
 public_art=[{k:x for k,x in a.items() if k!="path"} for a in v.art.values()]
 write_json(out/"SourceSnapshotRegistry.json",public_art)
 family_counts=C.Counter();family_declarations=C.Counter();by_family={}
 for f in v.family_records.values():
  p=f["payload"];by_family[ref(f)]=p["potential_family"];family_declarations[p["potential_family"]]+=1
 for x in v.family_links:family_counts[by_family[x["payload"]["source_family_ref"]]]+=1
 write_json(out/"SourceFamilyRegistrySummary.json",{"family_declarations":len(v.family_records),"potential_families":len(family_declarations),"record_bindings":len(v.family_links),
     "families":[{"potential_family":k,"declarations":n,"record_bindings":family_counts[k],"independent_measurement_status":"NOT_QUALIFIED"} for k,n in sorted(family_declarations.items())],
     "nutridata_ingredient_source_labels":sum(s==NDI for s,k in v.nd_sources),"nutridata_ingredient_usda_reported_rows":v.nd_sources[(NDI,"美国农业部食物营养成分数据")],
     "nutridata_dish_source_label_empty_rows":v.nd_sources[(NDD,"")],
     "governance":"potential dependency only, not exact underlying sample identity; same family or unresolved lineage cannot be counted as independent evidence; same-release FNDDS carriers dependent"})
 # Full FDC dictionary rows and ND values stay local; expose counts only and code definitions from own authored rules.
 write_json(out/"ExternalStandardAudit.json",v.stats)
 write_json(out/"CandidateAlignmentReport.json",astats)
 write_json(out/"ComponentAlignmentReport.json",dict(cstats,review_route_counts=dict(C.Counter(e["payload"]["review_route"] for e in cmaps)),
      target_ids_present_in_sr_values=sum(e["payload"]["target_present_in_sr_food_nutrient"] for e in cmaps),scientific_calculation_qualified=0,
      unresolved_definition_reason="native component name and unit do not establish analyte definition or denominator equivalence"))
 source_counts={k:len(vv) for k,vv in v.by_scope.items()}
 v.verify();verify_inputs(root)
 report={"run_id":"B2-U3A-"+out.name,"utc":NOW,"contract_version":VERSION,"status":"PASS_BOUNDED_NATIVE_VOCAB_AND_CANDIDATE_GENERATION",
    "snapshot_scopes":len(v.art),"native_vocab_records":len(v.records),"native_anchors":len(v.anchors),"vocabulary_scopes":len(v.by_scope),"source_counts":source_counts,
    "foodon_asserted_dag_nodes":nodes,"foodon_asserted_edges":len(v.foodon_edges),"canonical_food_candidate_anchors":len(anchors),
    "alignment_queries":astats["queries"],"queries_with_candidate":astats["queries_with_candidate"],"alignment_candidates":len(edges),
    "review_queue":len(blind),"review_completed":0,"component_native_fields":len(fields),"component_local_candidates":len(local),"component_candidates":len(cmaps),
    "family_records":len(v.family_records),"family_bindings":len(v.family_links),"fndds_carrier_crosswalks":len(carriers),
    "snapme_native_code_links":len(v.snapme_links),"snapme_same_cycle_candidate":v.stats["snapme"]["status_rows"]["SAME_CYCLE_CODE_MATCH_CANDIDATE"],
    "typed_objects":len(idx),"typed_collections":{k:len(x) for k,x in by.items()},"persisted_roundtrips":len(seen),
    "accepted_cross_source_equivalence":0,"scientific_measurements_qualified":0,"mapping_release_count":0,"research_releases":0,
    "global_b0_pass":False,"global_b1_frozen":False,"u3_global_frozen":False,
    "hold":["Food2K raw vocabulary and VIREO raw 172/353 labels not acquired after targeted public-source check","G008/G015/G019 original samples remain held","FNDDS short codes and intake grain; no aggregation","NutriData note and denominator semantics, measurement and independent source lineage","lexical retrieval not independent review; no calibrated precision/recall, no external semantic exact equivalence","original user archive versions remain unresolved"]}
 write_json(out/"B2RunReport.json",report);print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--out",type=P.Path,required=True);a=p.parse_args();main(a.root,a.out)
