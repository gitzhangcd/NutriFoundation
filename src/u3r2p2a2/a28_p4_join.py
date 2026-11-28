#!/usr/bin/env python3
"""Join 7 sealed source-only LLM batches. No target lookup, no reference read."""
from pathlib import Path
import json,collections,hashlib,os
from a28_p4_channels import evidence,validate,channel_views,need,CHANNELS
from a28_p4_run import B,RT,SOURCE,TOK,CONTRACT,SMOKE,REAL,pin,j,sha,save
OUT=B/"p4_query_hypothesis_freeze_001"
def main(contract_sha,runtime_sha,smoke_sha):
 from tokenizers import Tokenizer
 need(not OUT.exists(),"OUTPUT_EXISTS")
 ct=j(CONTRACT,contract_sha)
 for p,h in ct["code_sha256"].items():pin(p,h)
 rt=j(RT/"RuntimeManifest.json",runtime_sha)
 sm=j(SMOKE/"SmokeReceipt.json",smoke_sha)
 need(sm["status"]=="PASS_LOCAL_GENERATION_SMOKE","SMOKE")
 sr=j(SOURCE/"ProjectionReceipt.json",ct["source_projection_receipt_sha256"])
 p=j(SOURCE/"PrivateSourceOnly51.json",sr["source_only_packet_sha256"])
 expected=sorted(p["rows"],key=lambda x:(x["cohort"],x["source"]["review_id"]))
 tok=Tokenizer.from_str(pin(TOK,ct["e5_tokenizer_sha256"]).decode());tok.no_truncation();tok.no_padding()
 n=lambda s:len(tok.encode(s).ids)
 summary=collections.defaultdict(collections.Counter);rows=[];receipts={}
 for k,count in enumerate(ct["expected_batch_sizes"],1):
  dest=REAL/("batch_"+str(k).zfill(2));raw=(dest/"BatchReceipt.json").read_bytes();br=json.loads(raw)
  need(br["status"]=="PASS_SOURCE_ONLY_BATCH_FREEZE" and br["batch"]==k and br["contract_sha256"]==contract_sha and br["runtime_manifest_sha256"]==runtime_sha and br["smoke_receipt_sha256"]==smoke_sha and br["source_projection_receipt_sha256"]==ct["source_projection_receipt_sha256"],"BATCH_BINDING")
  need(br["reference_outputs_read"]==br["target_inputs_read"]==br["application_io_denials"]==br["mapping_release"]==0,"BATCH_SCOPE")
  need(len(br["case_file_hashes"])==br["counts"]["cases"]==count,"BATCH_COUNT")
  receipts[str(k)]=sha(raw);bc=collections.Counter()
  for name,h in sorted(br["case_file_hashes"].items()):
   idx=len(rows);need(name=="Case_"+str(idx+1).zfill(3)+".json","CASE_ORDER")
   x=j(dest/name,h);it=expected[idx];s=it["source"];ctx=it["context"];ev=evidence(s)
   need(x["review_id"]==s["review_id"] and x["cohort"]==it["cohort"] and x["source_ref"]==s["source_ref"] and x["source_artifact_sha256"]==s["artifact_sha256"] and x["evidence"]==ev,"SOURCE_BINDING")
   need(x["completion_sha256"]==sha(x["raw_completion"].encode()),"RAW_HASH")
   try:hy=validate(x["raw_completion"],ev);err=None
   except ValueError as ex:hy=None;err=str(ex)
   need((hy,err)==(x["hypotheses"],x["validation_error"]) and x["structure_valid"]==(err is None),"VALIDATION_DRIFT")
   v,st=channel_views(hy,ev,[ctx["label_query"],ctx["context_query"]],n)
   need(v==x["views"] and st==x["view_stats"],"CHANNEL_DRIFT")
   need(x["model_output_hypothesis_only"] and x["scientific_mapping_release"] is False,"OUTPUT_RELEASE")
   row={"review_id":x["review_id"],"cohort":x["cohort"],"source_ref":x["source_ref"],"source_artifact_sha256":x["source_artifact_sha256"],"case_record_sha256":h,"structure_valid":x["structure_valid"],"views":v,"view_stats":st}
   rows.append(row)
   c=summary[it["cohort"]];bc["cases"]+=1;bc["valid"]+=x["structure_valid"];bc["identity_abstain"]+=st["identity_abstain"];bc["monolithic_truncated_views"]+=st["monolithic_truncated_views"];bc["omitted_segment_terms"]+=st["omitted_segment_terms"]
   for ch in CHANNELS:bc[ch+"_nonempty"]+=bool(hy and hy[ch])
   c["cases"]+=1;c["valid"]+=x["structure_valid"];c["identity_abstain"]+=st["identity_abstain"];c["monolithic_truncated_views"]+=st["monolithic_truncated_views"];c["omitted_segment_terms"]+=st["omitted_segment_terms"]
   for ch in CHANNELS:c[ch+"_nonempty"]+=bool(hy and hy[ch])
   if err:c["invalid_"+err]+=1
  need(dict(bc)==br["counts"],"BATCH_AGGREGATE")
 need(len(rows)==51 and len({x["review_id"] for x in rows})==51,"ALL_CASES")
 OUT.mkdir(mode=0o700)
 rh=save(OUT/"PrivateLLMChannelViews51.json",{"version":"A2.8-P4-CHANNEL-VIEWS-v0.1","rows":rows,"budgets":p["budgets"],"reference_outputs_included":False,"mapping_release":False})
 rc={"status":"PASS_SOURCE_ONLY_LLM_HYPOTHESIS_FREEZE","contract_sha256":contract_sha,"runtime_manifest_sha256":runtime_sha,"smoke_receipt_sha256":smoke_sha,"batch_receipt_sha256":receipts,"private_views_sha256":rh,"cases":len(rows),"cohorts":dict(summary),"reference_outputs_read":0,"target_inputs_read":0,"new_confirmation_set":False,"scientific_reference_qualified":False,"mapping_release":0}
 print(json.dumps({**rc,"receipt_sha256":save(OUT/"LLMQueryFreezeReceipt.json",rc)},ensure_ascii=False))
if __name__=="__main__":
 import sys
 main(*sys.argv[1:])
