#!/usr/bin/env python3
"""B2 candidate generation. Lexical retrieval and bounded authored bilingual proposals.
No semantic equivalence, model confidence, independent expert judgment or release.
"""
import collections as C, math,re,unicodedata,heapq
from functools import lru_cache
from vocabulary import obj,ref,require,ContractError,canon,digest,VERSION
FOODON="foodon:2026-09-20:food_product"
SR="fdc:sr_legacy:2018-04"
FNDDS="fndds:2015-16:fdc_carrier"
NDI="nutridata:ingredient";NDD="nutridata:dish"
# Authored lexical seed translations only; no expert approval, no ontology-ID hardcoding.
SEEDS={
"苹果":"apple","梨":"pear","香蕉":"banana","橙子":"orange","柑橘":"citrus","草莓":"strawberry","葡萄":"grape","西瓜":"watermelon","菠萝":"pineapple","桃":"peach","柠檬":"lemon",
"牛奶":"milk","鸡蛋":"chicken egg","豆腐":"tofu","大豆":"soybean","黄豆":"soybean","花生":"peanut","核桃":"walnut",
"大米":"rice","米饭":"cooked rice","白米饭":"cooked rice","小麦":"wheat","面粉":"wheat flour","燕麦":"oat","土豆":"potato","马铃薯":"potato","红薯":"sweet potato","玉米":"corn",
"胡萝卜":"carrot","黄瓜":"cucumber","番茄":"tomato","西红柿":"tomato","菠菜":"spinach","白菜":"chinese cabbage","西兰花":"broccoli","洋葱":"onion","大蒜":"garlic",
"猪肉":"pork","牛肉":"beef","鸡肉":"chicken meat","鸡胸肉":"chicken breast","羊肉":"mutton","三文鱼":"salmon","虾":"shrimp","盐":"salt","白糖":"sugar","食用油":"edible oil","橄榄油":"olive oil","豆浆":"soy milk","酸奶":"yogurt","面包":"bread",
"蛋炒饭":"egg fried rice","炒饭":"fried rice","宫保鸡丁":"kung pao chicken","麻婆豆腐":"mapo tofu","红烧肉":"red braised pork","糖醋排骨":"sweet and sour pork ribs","西红柿炒鸡蛋":"tomato scrambled egg","番茄炒蛋":"tomato scrambled egg","饺子":"dumpling","馒头":"steamed bread","包子":"steamed bun","面条":"noodles","牛肉面":"beef noodles","炸鸡":"fried chicken","汉堡":"hamburger","披萨":"pizza","粥":"congee","小米粥":"millet porridge","炒面":"fried noodles","春卷":"spring roll","馄饨":"wonton","寿司":"sushi","蛋糕":"cake"}
@lru_cache(maxsize=100000)
def normalize(s):
 # Preserve lexical tokens and all qualifiers; punctuation separators only.
 s=unicodedata.normalize("NFKC",s).casefold()
 return " ".join(re.findall(r"[\w]+",s.replace("_"," "),flags=re.UNICODE))
@lru_cache(maxsize=100000)
def words(s):
 n=normalize(s)
 return set(re.findall(r"[a-z0-9]+|[\u3400-\u9fff]",n))
@lru_cache(maxsize=100000)
def grams(s):
 n=normalize(s);w=words(s);g={"w:"+x for x in w}
 # Exclude single alphabet character grams; keep CJK one-character tokens only as candidate features.
 v=n.replace(" ","")
 g.update("g:"+v[i:i+2] for i in range(max(0,len(v)-1)))
 return g
QUALS={
 "raw":("raw","uncooked","生"),"cooked":("cooked","boiled","steamed","熟","煮","蒸"),
 "fried":("fried","deep fried","油炸","炸","炒"),"dried":("dried","dehydrated","干","脱水"),
 "sweetened":("sweetened","added sugar","加糖"),"unsweetened":("unsweetened","no added sugar","无糖"),
 "peeled":("peeled","skinless","去皮"),"unpeeled":("unpeeled","with skin","带皮"),
 "salted":("salted","加盐"),"unsalted":("unsalted","无盐")}
@lru_cache(maxsize=100000)
def qualifier_set(s):
 n=normalize(s);out=set()
 for key,vals in QUALS.items():
  for v in vals:
   if re.search(r"[\u3400-\u9fff]",v):
    if v=="生":
     # single-character 生 occurs in 花生 and 生菜; do not infer raw from it.
     if s.endswith("（生）") or s.endswith("(生)"):out.add(key)
    elif v=="干":
     if s.endswith("（干）") or s.endswith("(干)"):out.add(key)
    elif v in s:out.add(key)
   elif re.search(r"(?:^| )"+re.escape(v)+r"(?: |$)",n):out.add(key)
 return out
def hard_conflicts(a,b):
 l=qualifier_set(a);r=qualifier_set(b)
 pairs=[("raw","cooked"),("raw","fried"),("sweetened","unsweetened"),("peeled","unpeeled"),("salted","unsalted")]
 return sorted(x+"<>"+y for x,y in pairs if (x in l and y in r) or (y in l and x in r))
def translations(label):
 n=normalize(label)
 if n in SEEDS:return [(SEEDS[n],"AUTHORED_BILINGUAL_EXACT_SURFACE",False)]
 # Keep all parenthetical qualifiers on source; base-head retrieval only, candidate broader possible.
 m=re.match(r"^([^（(]+)[（(].+[）)]$",label.strip())
 if m and normalize(m.group(1)) in SEEDS:
  return [(SEEDS[normalize(m.group(1))],"AUTHORED_BILINGUAL_HEAD_WITH_QUALIFIER_RETAINED",True)]
 return []
def forms(o):
 p=o["payload"];res=[(p["native_label"],"PRIMARY_LABEL")]
 for a in p["native_aliases"]:
  # Only exact synonym asserted by ontology used as synonym. Native unparsed/ARS
  # alias can be indexed as literal whole text, never as exact semantic synonyms.
  if a["type"] in ("hasExactSynonym","NATIVE_ALIAS_RAW_UNPARSED","ARS_ADDITIONAL_DESCRIPTION_RAW"):
   res.append((a["text"],a["type"]))
 return res
class Index:
 def __init__(self,rows):
  self.rows=rows;self.docs=[];self.inv=C.defaultdict(list);self.exact=C.defaultdict(list)
  for o in rows:
   for text,typ in forms(o):
    n=normalize(text);g=grams(text)
    if not n or not g:continue
    i=len(self.docs);self.docs.append((o,text,typ,g,n));self.exact[n].append(i)
    for v in sorted(g):self.inv[v].append(i)
  self.idf={v:math.log((len(self.docs)+1)/(len(ids)+1))+1 for v,ids in self.inv.items()}
 def rank(self,query,k=3):
  n=normalize(query);g=grams(query)
  if not n or not g:return []
  # Weighted lexical overlap candidate search; cap candidate pool deterministically.
  counts=C.Counter()
  for v in sorted(g):
   for i in self.inv.get(v,[]):counts[i]+=self.idf[v]
  pool=set(i for i,_ in counts.most_common(160))|set(self.exact.get(n,[]))
  by={}
  for i in pool:
   o,t,typ,h,n2=self.docs[i]
   inter=g&h;union=g|h
   a=sum(self.idf.get(v,1.0) for v in sorted(inter));b=sum(self.idf.get(v,1.0) for v in sorted(union))
   j=a/b if b else 0
   exact=n==n2
   if not exact and j<0.12:continue
   score=1.0 if exact else j
   # Prefer primary labels over synonyms in ties, and hard-conflict-free candidates.
   bad=hard_conflicts(query,t)
   key=ref(o);candidate=(score,typ=="PRIMARY_LABEL",not bad,t,typ,bad,o)
   if key not in by or candidate[:5]>by[key][:5]:by[key]=candidate
  ranked=sorted(by.values(),key=lambda x:(-int(x[2]),-x[0],-int(x[1]),x[6]["object_id"]))[:k]
  return [{"target":x[6],"matched_form":x[3],"matched_form_type":x[4],"score":round(x[0],8),"query_target_conflicts":x[5]} for x in ranked]
def spread(rows,n):
 if not rows:return []
 if len(rows)<=n:return list(rows)
 return [rows[i*(len(rows)-1)//(n-1)] for i in range(n)]
def mapping_guard(p):
 require(p["relation_type"]=="UNRESOLVED" and p["source_relation_to_target"]=="UNRESOLVED" and p["review_status"]=="PENDING" and not p["accepted_equivalence"],"UNREVIEWED_EQUIVALENCE")
 require(isinstance(p["ranking_score"],(float,int)) and 0<=p["ranking_score"]<=1,"INVALID_RANK_SCORE")
 require(p["direction"]=="SOURCE_RELATION_TO_TARGET","RELATION_DIRECTION")
 require(p["proposed_relation"] in ("CLOSE","BROADER_TARGET","RELATED","AMBIGUOUS"),"CANDIDATE_RELATION")
 require(p["permitted_purposes"]==["CURATION_DEV"] and p["score_interpretation"]=="LEXICAL_RANKING_NOT_PROBABILITY","UNQUALIFIED_RELEASE_OR_SCORE")
 require(not p["physical_instance_link"],"INSTANCE_PROMOTION")
 if p["hard_conflicts"]:require(p["review_route"]=="RED","HARD_CONFLICT_NOT_HELD")
def proposal(src,tgt,query,method,head,rank,match,methodref):
 s=src["payload"];t=tgt["payload"];conf=sorted(set(hard_conflicts(s["native_label"],t["native_label"])+match["query_target_conflicts"]))
 score=match["score"]
 if conf:rel="AMBIGUOUS";route="RED"
 elif head and score==1:rel="BROADER_TARGET";route="AMBER"
 elif score==1:rel="CLOSE";route="AMBER"
 elif score>=0.45:rel="RELATED";route="AMBER"
 else:rel="AMBIGUOUS";route="AMBER"
 # A source recipe vs a generic product/composition record is not exact physical identity.
 p={"source_ref":ref(src),"target_ref":ref(tgt),"source_grain":s["native_kind"],"target_grain":t["native_kind"],
    "source_relation_to_target":"UNRESOLVED","direction":"SOURCE_RELATION_TO_TARGET","relation_type":"UNRESOLVED",
    "proposed_relation":rel,"mechanism":"SEMANTIC_CANDIDATE","scope":"SOURCE_SCOPED_CONCEPT_OR_REFERENCE_LABEL",
    "conditions":["food state, grain and source applicability require review","no recipe/instance or measurement promotion"],
    "source_anchor_refs":src["provenance_refs"]+tgt["provenance_refs"],"input_dependency_refs":[ref(src),ref(tgt)],
    "method_version_ref":methodref,"review_status":"PENDING","review_route":route,"hard_conflicts":conf,
    "query_form":query,"query_method":method,"matched_target_form":match["matched_form"],"matched_form_type":match["matched_form_type"],
    "rank":rank,"ranking_score":score,"score_interpretation":"LEXICAL_RANKING_NOT_PROBABILITY",
    "uncertainty":{"status":"UNCALIBRATED","semantic_review":"NOT_PERFORMED"},"permitted_purposes":["CURATION_DEV"],
    "prohibited_purposes":["TRAIN","LOCKED_EVALUATION","GOLD","NUTRIENT_CALCULATION","CLINICAL_DECISION"],"accepted_equivalence":False,"physical_instance_link":False}
 mapping_guard(p)
 return obj("AlignmentRecord",[src["object_id"],tgt["object_id"],methodref.split("@")[0]],p,tuple(dict.fromkeys(src["provenance_refs"]+tgt["provenance_refs"])),(ref(src),ref(tgt),methodref),origin="DRV")
def align(v):
 method=obj("MappingMethod",VERSION,{"method":"weighted token/bigram Jaccard, exact lookup and manually authored bilingual surface seeds","top_k":3,"pool_limit":160,"min_score":0.12,
       "seed_count":len(SEEDS),"bilingual_seed_status":"AUTHORED_NOT_EXPERT_GOLD","normalization":"NFKC casefold punctuation tokenization; retains qualifiers and original labels",
       "review":"PENDING; no independent critic or expert review completed","score":"rank-only; not probability"},tuple(ref(v.snapshot_objects[s]) for s in (NDI,NDD,FOODON,SR,FNDDS)))
 mref=ref(method)
 targets={s:Index(v.by_scope[s]) for s in (NDI,NDD,FOODON,SR,FNDDS)}
 qscopes=["food101:class","uec2:mirror:class","uec3:mirror:class","isia500:class","food11:corrected_mirror","fruits360:current_directory","nutrition5k:ingredient","menumatch:menu","xiachufang:mirror","recipenlg:alternative_mirror"]
 queries=[o for s in qscopes for o in v.by_scope[s]]
 # Bounded Chinese source slice: deterministic spread plus exact/qualified-head seed availability.
 for s,n in ((NDI,48),(NDD,48)):
  rr=v.by_scope[s];sel={ref(o):o for o in spread(rr,n)}
  # Every seed contributes at most three native source rows; retain variants rather than merge.
  per=C.Counter()
  for o in rr:
   ts=translations(o["payload"]["native_label"])
   if ts and per[ts[0][0]]<3:sel[ref(o)]=o;per[ts[0][0]]+=1
  queries+=list(sel.values())
 # Register explicit exclusions rather than invent food class identities.
 excluded={s:len(v.by_scope[s]) for s in ("food5k:corrected_mirror","foodx251:mirror_class_ids","off:single","off:search","epic100:noun")}
 edges=[];routes=[];counts=C.defaultdict(C.Counter);coverage=C.defaultdict(C.Counter)
 for o in queries:
  p=o["payload"];s=p["native_namespace"];label=p["native_label"]
  zh=p["label_language"]=="zh_or_mixed";formsq=[]
  if zh:
   formsq.append((label,"RAW_ZH_LEXICAL",False,[NDI,NDD]))
   for q,m,h in translations(label):formsq.append((q,m,h,[FOODON,SR,FNDDS]))
  else:
   formsq.append((label,"RAW_NON_ZH_LEXICAL",False,[FOODON,SR,FNDDS]))
   # Reverse bilingual query only on complete seed surface; ambiguous multiple CN variants retained.
   cn=sorted(k for k,val in SEEDS.items() if normalize(val)==normalize(label))
   for q in cn[:3]:formsq.append((q,"AUTHORED_BILINGUAL_REVERSE_SURFACE",False,[NDI,NDD]))
  # Deduplicate target candidates across lexical routes, keep best rank, no self edges.
  best={};attempted=set()
  for query,m,h,ts in formsq:
   for target in ts:
    if target==s:continue
    attempted.add(target)
    # Chinese recipe/dish to local dish hub, ingredient to local ingredient hub.
    if target in (NDI,NDD):
     if p["native_kind"] in ("RECIPE_REFERENCE","RECIPE_VARIANT_LABEL") and target!=NDD:continue
     if p["native_kind"]=="INGREDIENT_REFERENCE" and target!=NDI:continue
    for rank,r in enumerate(targets[target].rank(query),1):
     t=r["target"];k=ref(t)
     if k==ref(o):continue
     e=proposal(o,t,query,m,h,rank,r,mref);pay=e["payload"]
     sort=(not bool(pay["hard_conflicts"]),pay["ranking_score"],-rank)
     if k not in best or sort>best[k][0]:best[k]=(sort,e)
  cand=[e for _,e in best.values()];cand.sort(key=lambda e:(e["payload"]["target_ref"],e["object_id"]))
  edges+=cand;coverage[s]["queries"]+=1
  coverage[s]["queries_with_candidate"]+=bool(cand)
  coverage[s]["queries_with_exact_surface_candidate"]+=any(e["payload"]["ranking_score"]==1 for e in cand)
  coverage[s]["queries_without_candidate"]+=not cand
  for e in cand:
   t=e["payload"]["target_ref"];counts[s][e["payload"]["review_route"]]+=1
  routes.append({"source_ref":ref(o),"source_scope":s,"candidate_count":len(cand),"targets_attempted":sorted(attempted),
     "status":"CANDIDATES_PENDING" if cand else "UNRESOLVED_NO_CANDIDATE","candidate_refs":[ref(e) for e in cand]})
 # Hub local IDs for referenced ND and FoodOn anchors, no automatic merging of same labels.
 idx={ref(o):o for o in v.records}
 targetrefs={p["target_ref"] for p in (e["payload"] for e in edges)}
 srcrefs={p["source_ref"] for p in routes}
 anchors=[]
 for r in sorted(targetrefs|srcrefs):
  o=idx[r];p=o["payload"]
  if p["native_namespace"] not in (NDI,NDD,FOODON):continue
  anchors.append(obj("CanonicalFoodConceptCandidate",o["object_id"],{"seed_native_ref":r,"proposed_label":p["native_label"],"grain":p["native_kind"],
      "identity_scope":"SOURCE_ANCHORED_CANDIDATE","equivalence_class":"NOT_ASSIGNED","review_status":"PENDING","food_state":"UNRESOLVED_UNLESS_NATIVE_DEFINITION_REVIEWED"},
      tuple(o["provenance_refs"]),(r,),origin="DRV"))
 # Review manifest separates source-only prompts from candidate payload. This is a queue, not completed expert review.
 strata=C.defaultdict(list)
 for x in routes:
  s=x["source_scope"];status="NO_CANDIDATE" if not x["candidate_count"] else "HAS_CANDIDATE"
  strata[(s,status)].append(x)
 queue=[]
 for k in sorted(strata):
  rr=strata[k]
  queue+=spread(rr,min(2,len(rr)))
 # Fill to a fixed 40-source development queue with additional candidate / HOLD strata.
 picked={x["source_ref"] for x in queue}
 for x in spread(routes,min(80,len(routes))):
  if len(queue)>=40:break
  if x["source_ref"] not in picked:queue.append(x);picked.add(x["source_ref"])
 queue=queue[:48]
 blind=[{"review_id":"B2-DEV-"+str(i+1).zfill(3),"source_ref":x["source_ref"],"source_scope":x["source_scope"],
      "source_native_label":idx[x["source_ref"]]["payload"]["native_label"],"native_kind":idx[x["source_ref"]]["payload"]["native_kind"],
      "question":"Independently propose concept/definition and permissible directional relation, or unresolved; do not use candidate output.",
      "status":"NOT_REVIEWED"} for i,x in enumerate(queue)]
 hidden=[{"review_id":b["review_id"],"candidate_refs":x["candidate_refs"]} for b,x in zip(blind,queue)]
 stats={"queries":len(queries),"queries_with_candidate":sum(bool(r["candidate_count"]) for r in routes),"candidate_edges":len(edges),
    "source_coverage":{k:dict(v) for k,v in coverage.items()},"review_route_counts":dict(C.Counter(e["payload"]["review_route"] for e in edges)),
    "proposed_relation_counts":dict(C.Counter(e["payload"]["proposed_relation"] for e in edges)),
    "review_queue_size":len(blind),"review_completed":0,"excluded_source_vocab_counts":excluded,
    "canonical_anchor_candidates":len(anchors),"accepted_semantic_equivalence":0,
    "precision_recall_status":"NOT_ESTIMABLE_WITHOUT_INDEPENDENT_REFERENCE; retrieval coverage is not recall",
    "query_selection":"all eligible small vocabularies and bounded ND source slice with curated surface seeds; not representative"}
 return method,edges,routes,anchors,blind,hidden,stats

# IDs are verified against real FDC dictionary. Candidate field links do not establish
# identical analytical method, edible denominator, unit conversion, or scientific truth.
COMPONENT_IDS={
"能量":["1008","2047","2048"],"蛋白质":["1003"],"脂肪":["1004"],"碳水化合物":["1005","1050","2039"],
"钠":["1093"],"铁":["1089"],"锌":["1095"],"钙":["1087"],"钾":["1092"],"镁":["1090"],"磷":["1091"],
"硫胺素":["1165"],"核黄素":["1166"],"烟酸":["1167"],"维生素C":["1162"],"维生素B6":["1175"],"维生素E":["1158"],
"叶酸":["1177","1186","1187","1190"],"维生素B12":["1178"],"铜":["1098"],"维生素D":["1114","1111","1112"],
"维生素K":["1185","1183","1184"],"锰":["1101"],"胆固醇":["1253"],"硒":["1103"],"维生素A":["1106"],"碘":["1100"],
"泛酸":["1170"],"生物素":["1176"],"单不饱和脂肪酸":["1292"],"多不饱和脂肪酸":["1293"],"饱和脂肪酸":["1258"],
"膳食纤维":["1079"],"异亮氨酸":["1212"],"亮氨酸":["1213"],"赖氨酸":["1214"],"蛋氨酸":["1215"],"胱氨酸":["1216"],
"苯丙氨酸":["1217"],"酪氨酸":["1218"],"色氨酸":["1210"],"缬氨酸":["1219"],"苏氨酸":["1211"],"DHA":["1272"],"总胆碱":["1180"]}
PREVIOUS={"能量":"ENERGY","蛋白质":"PROTEIN_DECLARED","脂肪":"FAT_DECLARED","碳水化合物":"CARBOHYDRATE_UNSPECIFIED","钠":"SODIUM","膳食纤维":"DIETARY_FIBER","维生素A":"VITAMIN_A_RAE","GI":"GI","可利用碳水":"CARBOHYDRATE_AVAILABLE"}
def unit_class(s):
 s=unicodedata.normalize("NFKC",s).strip().upper().replace("Μ","U").replace("μ","U").replace("µ","U")
 # Keep equivalence terms distinct; do not normalize RAE, RE, ATE, DFE to mass.
 if s in ("G","MG","UG","MCG"):return "MASS"
 if s in ("KCAL","KJ"):return "ENERGY"
 if "RAE" in s:return "RAE"
 if "RE" in s:return "RE"
 if "ATE" in s or "Α-TE" in s or "ΑTE" in s:return "ALPHA_TE"
 if "DFE" in s:return "DFE"
 return "OTHER_OR_UNRESOLVED"
def components(v,method):
 fields=[];fdc={}
 sr=v.snapshot_objects[SR];srref=ref(sr);md=ref(method)
 for k,x in sorted(v.fdc_nutrients.items()):
  o=obj("ComponentNativeField",[v.art[SR]["snapshot_id"],k],{"native_namespace":"fdc:sr_legacy:2018-04:nutrient","native_id":k,"native_name":x["name"],"native_unit":x["unit_name"],"nutrient_nbr":x["nutrient_nbr"],"source_locator":{"member":"nutrient.csv","id":k},
     "observed_food_nutrient_rows":v.fdc_nutrient_counts.get(k,0),"scientific_qualification":"HOLD"},(srref,),(srref,),real=True,origin="OBS")
  fields.append(o);fdc[k]=o
 nd=[];maps=[];local={};cstats=C.Counter()
 for (scope,name,unit),n in sorted(v.component_counter.items()):
  snap=ref(v.snapshot_objects[scope])
  a=obj("ComponentNativeField",[v.art[scope]["snapshot_id"],name,unit],{"native_namespace":scope,"native_id":name+" | "+unit,"native_name":name,"native_unit":unit,"occurrences":n,
       "source_locator":{"path":"detail_json.nutritionMap[*][*].desc/unit","name":name,"unit":unit},"scientific_qualification":"HOLD"},(snap,),(snap,),real=True,origin="DRV")
  fields.append(a);nd.append(a)
  # Each source attribute stays separately anchored; link to U2-B prior only as a candidate.
  prior=PREVIOUS.get(name)
  b=obj("ComponentConceptCandidate",a["object_id"],{"source_field_ref":ref(a),"declared_label":name,"native_unit":unit,
       "prior_u2b_component_id":"cc:"+prior if prior else None,"prior_u2b_registry_blob":"538c6c107e52589d230c932634e9dcc1e8bdf2b5",
       "prior_relation":"CANDIDATE_DECLARED_FAMILY" if prior else "UNRESOLVED_LOCAL_EXTENSION","review_status":"PENDING","global_exact":False},(snap,),(ref(a),),origin="CON")
  local[ref(a)]=b
  ids=COMPONENT_IDS.get(name,[]);valid=[k for k in ids if k in fdc]
  if not valid:cstats["native_fields_without_fdc_candidate"]+=1;continue
  cstats["native_fields_with_fdc_candidate"]+=1
  for k in valid:
   t=fdc[k];p=t["payload"];status="AMBIGUOUS" if len(valid)>1 else "CLOSE"
   unitmatch=unit_class(unit)==unit_class(p["native_unit"])
   # FDC name 'Vitamin A, RAE' uses UG, its quantity kind is RAE, not ordinary mass.
   if k=="1106":unitmatch="RAE" in unit.upper()
   if k=="1158":unitmatch="TE" in unit.upper()
   if k=="1190":unitmatch=False
   m={"source_ref":ref(a),"target_ref":ref(t),"source_grain":"SOURCE_ATTRIBUTE_FIELD","target_grain":"FDC_NUTRIENT_DEFINITION",
      "relation_type":"UNRESOLVED","proposed_relation":status,"direction":"SOURCE_RELATION_TO_TARGET","mechanism":"SEMANTIC_CANDIDATE",
      "source_unit":unit,"target_unit":p["native_unit"],"unit_dimension_candidate_match":bool(unitmatch),
      "review_route":"RED" if not unitmatch or len(valid)>1 else "AMBER","review_status":"PENDING","target_present_in_sr_food_nutrient":p["observed_food_nutrient_rows"]>0,
      "source_basis":"PENDING","conversion":"NOT_AUTHORIZED","source_method":"PENDING","accepted_equivalence":False,
      "measurement_qualification":"HOLD","method_version_ref":md,"permitted_purposes":["CURATION_DEV"]}
   maps.append(obj("ComponentAlignmentCandidate",[a["object_id"],t["object_id"]],m,(snap,srref),(ref(a),ref(t),ref(b),md),origin="DRV"))
 cstats.update({"fdc_dictionary_records":len(fdc),"nd_native_attribute_fields":len(nd),"local_component_candidates":len(local),"candidate_edges":len(maps),"accepted_equivalence":0})
 return fields,list(local.values()),maps,dict(cstats)
