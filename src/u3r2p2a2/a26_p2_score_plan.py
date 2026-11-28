"""Pure prespecified P2 three-report aggregation. No file IO or real-data CLI.
Real use requires a separately authorized sealed-import scoring controller.
Return reports and private per-case outputs; not a scientific Gold judgment.
"""
from copy import deepcopy
from a26_p1_semantic_policy import conservative_projection,ROUTE,need
from score_a2 import score
REPORTS=("RAW_PRIMARY","RAW_NONRELATED","CONSERVATIVE_SECONDARY")
DEMOTIONS={"TARGET_SPECIFIC_CONDITION":88,"UNRESOLVED_OTHER":1}

def score_three(bundle):
 need(bundle["version"]=="A2.6-P1-SEALED-IMPORT-v0.1" and bundle["semantic_route"]==ROUTE and bundle["comparison_executed"] is False and bundle["scoring_authorized"] is False and bundle["mapping_release"] is False,"SEALED_BUNDLE_SCOPE")
 ids=bundle["expected_ids"];refs=bundle["references"];ranks=bundle["ranks"]
 need(len(ids)==len(set(ids))==32 and len(refs)==32 and len(ranks)==384,"FROZEN_CASE_RANK_COUNTS")
 original=set(map(tuple,bundle["original"]));extension=set(map(tuple,bundle["extension"]))
 need(len(original)==len(bundle["original"])==28845 and len(extension)==len(bundle["extension"])==1174,"FROZEN_UNIVERSES")
 projected,counts=conservative_projection(refs)
 need(counts==DEMOTIONS,"FROZEN_DEMOTION_COUNTS")
 outputs={};private={}
 for name,records,sensitivity in zip(REPORTS,(refs,refs,projected),(False,True,True)):
  outputs[name],private[name]=score(ranks,records,original,extension,ids,sensitivity=sensitivity)
  need(len(outputs[name]["metrics"])==30 and len(outputs[name]["paired_at12"])==4 and len(private[name])==960,"REPORT_CLOSURE")
 return {"reports":outputs,"conservative_demotions":counts,"primary":"RAW_PRIMARY","scientific_precision_recall":"NOT_ESTIMABLE","scientific_mapping_release":False},private
