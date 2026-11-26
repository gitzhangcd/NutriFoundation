"""C2-R1: complete-surface evidence and conservative state/role routing.
Mentions, normalization and authored bilingual pairs support review only.
No substring can authorize review. No semantic or scientific equivalence is minted.
"""
import re,unicodedata
from functools import lru_cache
def norm(s):
 return re.sub(r"[\W_]+"," ",unicodedata.normalize("NFKC",str(s)).casefold()).strip()
def word(s,t):
 return bool(re.search(r"(?<![a-z0-9])"+re.escape(norm(t))+r"(?![a-z0-9])",norm(s)))
def phrase_table(policy):
 out={}
 for a,b in policy["whole_label_aliases"]:
  a,b=norm(a),norm(b)
  if a in out and out[a]!=b:raise ValueError("WHOLE_ALIAS_COLLISION")
  out[a]=b
 return out
@lru_cache(maxsize=100000)
def features(label):
 raw=unicodedata.normalize("NFKC",str(label)).casefold()
 s=raw;origin=[];negative=[];uncertain=[]
 # Food source/ingredient history is not the current product state.
 pat=r"\b(?:made\s+)?from\s+(fresh|frozen|dried|raw|canned)\b"
 for m in re.finditer(pat,s):origin.append(m.group(1))
 s=re.sub(pat," ",s)
 neg_en=[(r"\b(?:non[- ]fried|not\s+fried|no\s+frying)\b","NOT_FRIED"),(r"\b(?:not\s+cooked|not\s+fully\s+cooked|undercooked)\b","COOK_STATE_UNRESOLVED"),
 (r"\b(?:no\s+added\s+salt|no\s+salt\s+added|without\s+added\s+salt)\b","NO_ADDED_SALT"),(r"\b(?:no\s+added\s+sugar|no\s+sugar\s+added)\b","NO_ADDED_SUGAR")]
 neg_zh=[("非油炸","NOT_FRIED"),("不油炸","NOT_FRIED"),("未煮熟","COOK_STATE_UNRESOLVED"),("未熟透","COOK_STATE_UNRESOLVED"),("未熟","COOK_STATE_UNRESOLVED"),("不加盐","NO_ADDED_SALT"),("未加盐","NO_ADDED_SALT"),("不加糖","NO_ADDED_SUGAR"),("未加糖","NO_ADDED_SUGAR")]
 for p,t in neg_en:
  if re.search(p,s):negative.append(t);s=re.sub(p," ",s)
 for p,t in neg_zh:
  if p in s:negative.append(t);s=s.replace(p," ")
 # Explicit terms only. Chinese single characters recognized only as standalone
 # parenthetical qualifiers (or restricted explicit prefix constructions).
 en={"raw":["raw","uncooked"],"cooked":["cooked"],"boiled":["boiled"],"steamed":["steamed"],"fried":["fried","deep fried"],"baked":["baked"],"roasted":["roasted"],"braised":["braised","stewed"],"frozen":["frozen"],"fresh":["fresh"],"dried":["dried","dehydrated"],"canned":["canned"],"blanched":["blanched"]}
 zh={"raw":["生制"],"cooked":["熟制"],"boiled":["水煮"],"steamed":["清蒸"],"fried":["油炸","煎制","炒制"],"baked":["烘焙"],"roasted":["烤制"],"braised":["红烧","炖制","卤制"],"frozen":["冷冻","冰冻"],"fresh":["新鲜"],"dried":["干制","脱水"],"canned":["罐头"],"blanched":["焯水"]}
 tags=set(k for k,terms in en.items() if any(word(s,t) for t in terms))
 tags.update(k for k,terms in zh.items() if any(t in s for t in terms))
 for char,t in {"生":"raw","熟":"cooked","煮":"boiled","蒸":"steamed","炒":"fried","炸":"fried","烤":"roasted","干":"dried"}.items():
  if re.search(r"\(\s*"+char+r"\s*\)",s):tags.add(t)
 if re.match(r"^生(?:鸡肉|鸭肉|猪肉|牛肉|羊肉|鱼肉|虾仁|鸡蛋)",s):tags.add("raw")
 # Do not convert a named dish (tartare) or unprepared mix to explicit raw.
 if word(s,"tartare") or word(s,"unprepared"):uncertain.append("DISH_OR_PREPARATION_STATE_NEEDS_EVIDENCE")
 if "COOK_STATE_UNRESOLVED" in negative:
  tags-={"cooked","boiled","steamed","fried","roasted","baked","braised"};uncertain.append("NEGATED_OR_INCOMPLETE_COOK_STATE")
 if "NOT_FRIED" in negative:tags.discard("fried")
 salted=word(s,"salted") or "加盐" in s
 unsalted=word(s,"unsalted") or "无盐" in s
 sweetened=word(s,"sweetened") or "加糖" in s
 unsweetened=word(s,"unsweetened") or "无糖" in s
 if salted:tags.add("salted")
 if unsalted:tags.add("unsalted")
 if sweetened:tags.add("sweetened")
 if unsweetened:tags.add("unsweetened")
 cooked=bool(tags&{"cooked","boiled","steamed","fried","baked","roasted","braised","blanched"})
 state="AMBIGUOUS" if "raw" in tags and cooked else "RAW_EXPLICIT" if "raw" in tags else "COOKED_EXPLICIT" if cooked else "UNKNOWN"
 # Forms are signals for diagnostics; full label residual is never dropped.
 form_lex={"SANDWICH":["sandwich","on bun","三明治","汉堡"],"DRESSING":["dressing","沙拉酱"],"FILLING":["filling","馅料"],"JUICE":["juice","果汁"],"POWDER":["powder","粉末"],"JAM":["jam","果酱"],"CREAMED":["creamed"],"DRY":["dry","dried"],"SPECIAL_TYPE":["gluten free","lowfat","rye","white bread","corn oil","gingelly oil"]}
 forms=sorted(k for k,terms in form_lex.items() if any((t in raw if re.search(r"[\u3400-\u9fff]",t) else word(raw,t)) for t in terms))
 return {"normalized_complete_label":norm(raw),"current_state":state,"explicit_mentions":sorted(tags),"origin_mentions":sorted(set(origin)),"negative_mentions":sorted(set(negative)),"unresolved_state":sorted(set(uncertain)),"form_mentions":forms}
def evaluate(source,target,policy,scope_status=None,prior_red=False):
 a=features(source["label"]);b=features(target["label"]);s=a["normalized_complete_label"];t=b["normalized_complete_label"]
 table=phrase_table(policy)
 left=table.get(s,s);right=table.get(t,t);same=bool(s and s==t);authored=bool(s and t and left==right and not same and (s in table or t in table))
 full=same or authored
 hard=[];conditions=[];role=[]
 A=set(a["explicit_mentions"]);B=set(b["explicit_mentions"])
 if {a["current_state"],b["current_state"]}=={"RAW_EXPLICIT","COOKED_EXPLICIT"}:hard.append("EXPLICIT_RAW_COOKED")
 for x,y in (("fresh","frozen"),("fresh","dried"),("salted","unsalted"),("sweetened","unsweetened")):
  if (x in A and y in B) or (y in A and x in B):hard.append("EXPLICIT_"+x.upper()+"_"+y.upper())
 if prior_red:conditions.append("UPSTREAM_RED_REQUIRES_REVIEW_NEVER_AUTO_CLEAR")
 if not full:conditions.append("UNRESOLVED_COMPLETE_LABEL_RESIDUAL")
 if a["form_mentions"]!=b["form_mentions"]:conditions.append("PRODUCT_FORM_OR_COMPONENT_DIFFERENCE")
 if a["origin_mentions"]!=b["origin_mentions"]:conditions.append("SOURCE_ORIGIN_CONDITION_DIFFERS")
 if a["negative_mentions"]!=b["negative_mentions"]:conditions.append("NEGATED_OR_ABSENT_CONDITION_DIFFERS")
 if A!=B:conditions.append("EXPLICIT_QUALIFIER_MENTIONS_DIFFER")
 if a["current_state"]!=b["current_state"]:conditions.append("STATE_CONDITION_DIFFERS_OR_UNKNOWN")
 if a["unresolved_state"] or b["unresolved_state"]:conditions.append("STATE_REQUIRES_EXPERT_EVIDENCE")
 if a["current_state"]=="UNKNOWN" or b["current_state"]=="UNKNOWN":conditions.append("STATE_UNRESOLVED_FOR_SCIENTIFIC_USE")
 if "AMBIGUOUS" in (a["current_state"],b["current_state"]):conditions.append("INTERNAL_STATE_AMBIGUITY")
 g=(source["grain"],target["grain"]);rp=policy["role_policy"]
 if scope_status=="DUAL_ROLE_ORGANISM_REVIEW_ONLY":role.append("ONTOLOGY_ORGANISM_FOOD_DUAL_ROLE")
 elif scope_status=="EXTENSION_TYPED_RETRIEVAL_ONLY":role.append("TYPED_SCOPE_CONDITIONAL_ONLY")
 elif scope_status is not None and scope_status!="CORE_RETAINED_DEV":role.append("SCOPE_NOT_ADMITTED")
 if g[0]==g[1] or g==("INGREDIENT_REFERENCE","ONTOLOGY_FOOD_PRODUCT_CLASS"):mode="COMPLETE_SURFACE_REVIEW"
 elif list(g) in rp["other_pairs"]:mode="CONDITIONAL_RELATION_REVIEW_ONLY";role.append("CROSS_ROLE_RELATION_NOT_IDENTITY")
 else:mode="NOT_REGISTERED";role.append("ROLE_PAIR_NOT_REGISTERED")
 if "ONTOLOGY_ORGANISM_FOOD_DUAL_ROLE" in role or "TYPED_SCOPE_CONDITIONAL_ONLY" in role:
  if mode!="NOT_REGISTERED":mode="CONDITIONAL_RELATION_REVIEW_ONLY"
 blockers={"UNRESOLVED_COMPLETE_LABEL_RESIDUAL","PRODUCT_FORM_OR_COMPONENT_DIFFERENCE","SOURCE_ORIGIN_CONDITION_DIFFERS","NEGATED_OR_ABSENT_CONDITION_DIFFERS","EXPLICIT_QUALIFIER_MENTIONS_DIFFER","STATE_CONDITION_DIFFERS_OR_UNKNOWN","STATE_REQUIRES_EXPERT_EVIDENCE","INTERNAL_STATE_AMBIGUITY","UPSTREAM_RED_REQUIRES_REVIEW_NEVER_AUTO_CLEAR"}
 # Authored bilingual full pairs may carry different lexical feature tokens. Only
 # explicit conditions consistent in both labels can pass. No suffix deletion.
 if hard:disp="BLOCK_EXPLICIT_CONFLICT"
 elif "SCOPE_NOT_ADMITTED" in role or mode=="NOT_REGISTERED":disp="HOLD_SCOPE_OR_UNREGISTERED_ROLE"
 elif not full or blockers.intersection(conditions):disp="HOLD_UNRESOLVED_CONDITIONS"
 elif mode=="CONDITIONAL_RELATION_REVIEW_ONLY":disp="CONDITIONAL_RELATION_REVIEW_ONLY"
 else:disp="COMPLETE_SURFACE_REVIEW_ONLY"
 return {"source_dimensions":a,"target_dimensions":b,"full_label_evidence":"NORMALIZED_COMPLETE_SURFACE" if same else "AUTHORED_COMPLETE_BILINGUAL_PAIR" if authored else "NONE","explicit_conflicts":sorted(set(hard)),"unresolved_conditions":sorted(set(conditions)),"role_conditions":sorted(set(role)),"role_policy_mode":mode,"disposition":disp,"review_eligible":disp in ("CONDITIONAL_RELATION_REVIEW_ONLY","COMPLETE_SURFACE_REVIEW_ONLY"),"scientific_equivalence":"HOLD","nutrient_transfer":"HOLD","physical_identity":"HOLD","training":"HOLD","mapping_release":"HOLD","relation":"UNRESOLVED"}
