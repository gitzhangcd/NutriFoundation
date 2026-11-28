"""A2.8-Q1 deterministic, source-grounded query reconstruction.
Not a generative LLM, translation truth, or semantic alignment assertion.
Only source-native inputs, original source query context and a frozen component lexicon.
"""
import re,unicodedata
VERSION="A2.8-SOURCE-QUERY-v0.1"
FIELDS={"review_id","source_ref","source_scope","source_native_label","native_kind","source_locator","artifact_sha256","source_anchor_ref","native_aliases","reference_recipe_ingredient_names","context_locator","context_note","question","status"}
CTX_FIELDS={"label_query","context_query","state_tokens"}
ROLE={"INGREDIENT_REFERENCE":"food ingredient","RECIPE_REFERENCE":"reference recipe dish"}
def need(x,c):
 if not x:raise ValueError(c)
def nonempty(x):return isinstance(x,str) and bool(x.strip())
def exact(x,keys):need(isinstance(x,dict) and set(x)==set(keys),"FIELD_SCOPE")
def clean(s):return " ".join(unicodedata.normalize("NFKC",s).split())
def hypothesis(s,field,index,lex):
 pat=re.compile("|".join(map(re.escape,sorted(lex,key=lambda x:(-len(x),x)))))
 return [{"field":field,"index":index,"start":m.start(),"end":m.end(),"source_span":m.group(),"english_hypothesis":lex[m.group()],"status":"DEVELOPMENT_HYPOTHESIS"} for m in pat.finditer(s)]
def validate_source(s,ctx,lex):
 exact(s,FIELDS);exact(ctx,CTX_FIELDS)
 need(s["status"]=="NOT_REVIEWED" and s["native_kind"] in ROLE,"SOURCE_SCOPE")
 need(all(nonempty(s[k]) for k in ("review_id","source_ref","source_native_label","source_anchor_ref")),"SOURCE_ID")
 need(isinstance(s["artifact_sha256"],str) and re.fullmatch("[0-9a-f]{64}",s["artifact_sha256"]) is not None,"SOURCE_HASH")
 need(isinstance(s["native_aliases"],list) and all(isinstance(a,dict) and set(a)=={"text","type"} and nonempty(a["text"]) and nonempty(a["type"]) for a in s["native_aliases"]),"ALIAS_SCHEMA")
 need(isinstance(s["reference_recipe_ingredient_names"],list) and all(nonempty(x) for x in s["reference_recipe_ingredient_names"]),"COMPONENT_SCHEMA")
 need(ctx["label_query"]=="query: "+s["source_native_label"] and nonempty(ctx["context_query"]) and ctx["context_query"].startswith(ctx["label_query"]),"HISTORICAL_QUERY_IDENTITY")
 need(isinstance(ctx["state_tokens"],list) and all(nonempty(x) for x in ctx["state_tokens"]),"STATE_SCHEMA")
 need(isinstance(lex,dict) and lex and all(nonempty(k) and nonempty(v) for k,v in lex.items()),"LEXICON")
def reconstruct(s,ctx,lex):
 validate_source(s,ctx,lex)
 label=s["source_native_label"];aliases=[a["text"] for a in s["native_aliases"]];ingredients=s["reference_recipe_ingredient_names"][:5]
 hy=hypothesis(label,"source_native_label",None,lex)
 for i,a in enumerate(aliases):hy+=hypothesis(a,"native_aliases",i,lex)
 for i,a in enumerate(ingredients):hy+=hypothesis(a,"reference_recipe_ingredient_names",i,lex)
 def terms(field):
  return list(dict.fromkeys(clean(h["english_hypothesis"]) for h in hy if h["field"]==field))
 label_h=terms("source_native_label")
 alias_h=terms("native_aliases")
 component_h=terms("reference_recipe_ingredient_names")
 base=["query: "+label,ROLE[s["native_kind"]]]
 if label_h:base.append("name hypotheses: "+"; ".join(label_h))
 # Two views in both treatments; keep the full native label first in each.
 identity=" | ".join(base)
 context=list(base)
 if ctx["state_tokens"]:context.append("explicit label states: "+", ".join(ctx["state_tokens"]))
 if aliases:context.append("native aliases: "+"; ".join(aliases))
 if alias_h:context.append("alias hypotheses: "+"; ".join(alias_h))
 if ingredients:context.append("reference recipe ingredients: "+"; ".join(ingredients))
 if component_h:context.append("ingredient hypotheses: "+"; ".join(component_h))
 return {"version":VERSION,"review_id":s["review_id"],"source_ref":s["source_ref"],"artifact_sha256":s["artifact_sha256"],"source_anchor_ref":s["source_anchor_ref"],"source_locator":s["source_locator"],"native_kind":s["native_kind"],"native_label":label,"native_aliases":aliases,"reference_recipe_ingredients":ingredients,"state_mentions":ctx["state_tokens"],"hypotheses":hy,"q0":[ctx["label_query"],ctx["context_query"]],"q1":[identity," | ".join(context)],"identity_role":"SOURCE_NATIVE_KIND","translation_status":"HYPOTHESIS_ONLY","composition_status":"REFERENCE_RECIPE_NOT_PHYSICAL_COMPOSITION","accepted_equivalence":False,"mapping_release":False}
def surface(label,aliases,defs):
 # A second native target surface: same label plus up to 3 source-defined aliases
 # and first source-defined definition. Deterministic order, no generated synonyms.
 need(nonempty(label) and isinstance(aliases,list) and isinstance(defs,list),"TARGET_SURFACE")
 al=sorted(set(clean(x) for x in aliases if nonempty(x) and clean(x)!=clean(label)),key=lambda x:(x.casefold(),x))[:3]
 de=next((clean(x) for x in defs if nonempty(x)),"")
 p="passage: "+label
 if not al and not de:return p,None
 x=[p]
 if al:x.append("native aliases: "+"; ".join(al))
 if de:x.append("native definition: "+de)
 return p," | ".join(x)
def fused(top_a,top_b,budget,sim_a,sim_b):
 # target IDs are indices in the fixed sorted universe; same tie rule for all arms.
 a={x:i+1 for i,x in enumerate(top_a)};b={x:i+1 for i,x in enumerate(top_b)}
 return sorted(a.keys()|b.keys(),key=lambda j:(-((1/(60+a[j]) if j in a else 0)+(1/(60+b[j]) if j in b else 0)),-max(float(sim_a[j]),float(sim_b[j])),j))[:budget]
