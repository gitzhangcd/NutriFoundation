#!/usr/bin/env python3
"""B1 U2-A real-source thin slice. No network, no source edits, no research release.
Run from NutriOne root. The B0 manifests are the input admission fences.
"""
import argparse
import collections as C
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import pathlib as P
import re
import sys
import zipfile
import xml.etree.ElementTree as E

from contract import *
sys.path.insert(0,str(P.Path(__file__).resolve().parent.parent/"b0"))
from profile_nutridata import M, sheets, read_rows, json_obj

PUBLIC_ROOT=P.Path("source_data/public_samples")
B0_ND=P.Path("runs/B0/U1-A/NutriData_real_001/private/NativeFileManifest.json")
B0_PUBLIC=P.Path("runs/B0/U1-A/public_samples_001/PublicSampleAudit_shareable.json")
CORE_NUTRIENTS={"能量","蛋白质","脂肪","碳水化合物","钠"}
def readj(p):return json.loads(p.read_text(encoding="utf8"))
def file_sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def atomic_json(p,v):
    with p.open("x",encoding="utf8") as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
def take(seq,n):
    if len(seq)<=n:return list(seq)
    if n==1:return [seq[0]]
    return [seq[i*(len(seq)-1)//(n-1)] for i in range(n)]
def xlsx_rows(p):
    result=[]
    with zipfile.ZipFile(p) as z:
        ss=["".join(t.text or "" for t in s.iter(M+"t")) for s in E.fromstring(z.read("xl/sharedStrings.xml"))] if "xl/sharedStrings.xml" in z.namelist() else []
        for sh,_,path in sheets(z):
            hdr=None
            for rn,row in read_rows(z,path,ss):
                if not any(v[0] not in (None,"") for v in row.values()):continue
                if hdr is None:
                    hdr={c:v[0] for c,v in row.items() if v[0] not in (None,"")}
                    require(len(set(hdr.values()))==len(hdr),"DUPLICATE_HEADER");continue
                require(not any(c not in hdr and v[0] not in (None,"") for c,v in row.items()),"EXTRA_COLUMN")
                fields={n:row.get(c,(None,"absent",False))[0] for c,n in hdr.items()}
                raw={"fields":fields,"cells":{c:{"raw":v[0],"ooxml_type":v[1],"formula_present":v[2]} for c,v in row.items()},"header":hdr}
                for k in ("detail_json","list_json"):
                    st,j=json_obj(fields.get(k));require(st=="object","CORE_JSON_INVALID");raw[k]=j
                result.append(({"sheet":sh,"excel_row":rn},raw))
    return result
def csv_rows(p,header=True):
    with p.open(encoding="utf-8-sig",newline="") as f:r=list(csv.reader(f))
    if header:
        names=r[0];require(len(names)==len(set(names)),"DUPLICATE_HEADER")
        require(all(len(x)==len(names) for x in r[1:]),"RAGGED_CSV")
        return [({"csv_record":i+2},{"header":names,"tokens":x,"fields":dict(zip(names,x))}) for i,x in enumerate(r[1:])]
    return [({"csv_record":i+1},{"tokens":x}) for i,x in enumerate(r)]
def line_rows(p,style):
    out=[]
    with p.open(encoding="utf-8-sig",newline="") as f:
        for i,line in enumerate(f,1):
            text=line.rstrip("\r\n")
            if not text.strip():continue
            if style in ("category","bbox","menu") and i==1:continue
            if style=="food101":
                a=text.split("/",1);require(len(a)==2,"FOOD101_PATH");fields={"label":a[0],"path":text}
            elif style=="category":
                a=text.split(None,1);require(len(a)==2 and a[0].isdigit(),"CATEGORY_ROW");fields={"label_id":a[0],"label":a[1]}
            elif style=="isia":
                a=text.rsplit(None,1);require(len(a)==2 and a[1].isdigit(),"ISIA_ROW");fields={"label_id":a[1],"label":a[0]}
            elif style=="bbox":
                a=text.split();require(len(a)==5,"BBOX_WIDTH")
                v=list(map(int,a[1:]));require(min(v)>=0 and v[2]>=v[0] and v[3]>=v[1],"BBOX_ORDER")
                fields={"image_key":a[0],"x1":a[1],"y1":a[2],"x2":a[3],"y2":a[4]}
            elif style in ("menu","menu_labels"):
                a=[v.strip() for v in text.split(";") if v.strip()]
                if style=="menu":
                    require(len(a)==4,"MENU_WIDTH");fields=dict(zip(("menu_name","menu_key","calorie","restaurant"),a))
                else:
                    require(len(a)>=2,"MENU_LABEL_WIDTH");fields={"image_key":a[0],"labels":a[1:]}
            else:raise ContractError("UNKNOWN_LINE_STYLE")
            out.append(({"line":i},{"line_text":line,"fields":fields}))
    return out
def json_rows(p,style):
    x=readj(p)
    if style=="viewer":return [({"json_pointer":"/rows/"+str(i)},v) for i,v in enumerate(x["rows"])]
    if style=="product":return [({"json_pointer":"/product"},x["product"])]
    if style=="products":return [({"json_pointer":"/products/"+str(i)},v) for i,v in enumerate(x["products"])]
    if style=="qa":return [({"json_pointer":"/data/"+str(i)},v) for i,v in enumerate(x["data"])]
    raise ContractError("JSON_STYLE")
@dataclass
class Spec:
    key:str
    asset:str
    namespace:str
    path:P.Path
    expected_sha:str
    role:str
    parser:object
    grain:str
    records:object=None
    artifact:object=None
    def read(self):return self.parser(self.path)
class Builder:
    def __init__(self,root,when):
        self.root=root;self.when=when;self.specs={};self.objects=[];self.byref={};self.native={};self.selected=C.Counter();self.links=C.Counter();self.measurements=C.Counter()
        self.nd={x["file"]:x for x in readj(root/B0_ND)}
        self.pub={}
        for r in readj(root/B0_PUBLIC)["records"]:
            for f in r["files"]:self.pub[(r["asset_id"],f["run"],f["file"])]=f
    def add(self,o):
        r=ref(o);require(r not in self.byref,"DUPLICATE_OBJECT_BUILD");self.objects.append(o);self.byref[r]=o;return r
    def make(self,kind,oid,payload,prov=(),deps=()):
        return self.add(create(kind,oid,payload,self.when,prov,deps))
    def spec(self,key,asset,namespace,filename,parser,grain,run="20261125_run001"):
        if asset.startswith("NDF-G023"):
            m=self.nd[filename];path=self.root/"source_data/excel-Nutridata"/filename;role="NUTRIDATA_NATIVE"
            require(m["asset_id"]==asset,"B0_ADMISSION_ASSET_MISMATCH")
        else:
            m=self.pub[(asset,run,filename)];path=self.root/PUBLIC_ROOT/run/asset/filename;role=m["role"]
        require(path.is_file() and not path.is_symlink(),"SOURCE_NOT_REGULAR_FILE")
        require(file_sha(path)==m["sha256"],"B0_SOURCE_HASH_CHANGED")
        s=Spec(key,asset,namespace,path,m["sha256"],role,parser,grain)
        self.specs[key]=s
        p={"namespace":namespace,"file_sha256":s.expected_sha,"bytes":path.stat().st_size,"source_role":role,"version_status":"B0_VERIFIED_LOCAL_SNAPSHOT; ORIGINAL_VERSION_NOT_CLAIMED"}
        s.artifact=self.make("SourceArtifact","artifact:"+key+":"+s.expected_sha,p)
        s.records=s.read()
        require(len({canon(loc) for loc,_ in s.records})==len(s.records),"DUPLICATE_SOURCE_LOCATOR")
        return s
    def n(self,s,item):
        loc,raw=item
        key=(s.key,canon(loc))
        if key in self.native:return self.native[key]
        suffix=digest([self.byref[s.artifact]['object_id'],loc])[:32]
        anch=self.make("SourceAnchor","anchor:"+suffix,{"source_ref":s.artifact,"locator":loc,"integrity":s.expected_sha,"content":unavailable("WITHHELD","source bytes and raw record retained locally"),"source_class":"REAL_DATA"},(s.artifact,))
        nr=self.make("NativeRecord","native:"+suffix,{"artifact_ref":s.artifact,"anchor_ref":anch,"locator":loc,"raw":raw,"raw_sha256":digest(raw),"native_format":s.path.suffix.lower(),"grain":s.grain},(anch,),(s.artifact,))
        self.native[key]=nr;self.selected[s.key]+=1
        return nr
    def d(self,kind,native,mapping,extra,suffix="",deps=()):
        np=self.byref[native]["payload"]
        b={k:binding(np["raw"],v) for k,v in mapping.items()}
        pay={"native_ref":native,"bindings":b,**extra}
        oid=kind+":"+digest([self.byref[native]['object_id'],kind,suffix])[:32]
        return self.make(kind,oid,pay,(np["anchor_ref"],),tuple(dict.fromkeys((native,)+tuple(deps))))
    def measurement(self,n,subject,component,valpath,unit,basis,method,profile,extra_bindings=None):
        raw=self.byref[n]["payload"]["raw"]
        p={"subject_ref":subject,"component_key":component,"original_value":raw_numeric_slot(ptr(raw,valpath)),"original_unit":unit,"original_basis":basis,"normalized_value":pending("unit, basis, state and reference qualification required before normalization"),"preparation":pending("food preparation or state not fully established"),"source_method":method,"reference_profile":profile,"qualification":pending("CURATION_DEV; not qualified for scientific measurement or calculation")}
        m={"value":valpath,**(extra_bindings or {})}
        self.measurements[profile]+=1
        return self.d("NutrientMeasurementDraft",n,m,p,component+":"+valpath,(subject,))
    def link(self,n,l,r,keypath,suffix):
        self.links["native_candidate"]+=1
        return self.d("NativeLinkDraft",n,{"source_key":keypath},{"relation_type":"NATIVE_CANDIDATE_LINK","left_ref":l,"right_ref":r,"status":"STRUCTURALLY_MATCHED","semantic_qualification":"PENDING"},suffix,(l,r))
    def nutrition_map(self,n,subject,namespace):
        raw=self.byref[n]["payload"]["raw"]
        for group,vs in raw["detail_json"]["nutritionMap"].items():
            for i,v in enumerate(vs):
                if v.get("desc") not in CORE_NUTRIENTS:continue
                base="/detail_json/nutritionMap/"+esc(group)+"/"+str(i)
                self.measurement(n,subject,namespace+":"+v["desc"],base+"/value",slot_value(v["unit"]) if v.get("unit") else pending("unit missing"),pending("original denominator not established"),pending("original measurement versus derived source unresolved"),"Q-COMPOSITION_SOURCE_UNQUALIFIED",{"component":base+"/desc","unit":base+"/unit"})
    def nutridata(self):
        s=self.spec("nutridata_ingredient","NDF-G023-01","nutridata:ingredient","01-食物成分库.xlsx",xlsx_rows,"source ingredient composition record")
        t=self.spec("nutridata_dish","NDF-G023-02","nutridata:dish","02-菜肴库.xlsx",xlsx_rows,"source recipe record")
        idx={}
        for item in s.records:
            raw=item[1];k=raw["fields"]["item_id"]
            require(k not in idx and str(raw["detail_json"]["id"])==str(k),"INGREDIENT_BUSINESS_ID")
            idx[k]=item
        # Deliberately cover missing parents and name differences in development examples, not representative.
        orphans=[];different=[]
        for it in t.records:
            ls=it[1]["detail_json"]["major"]
            if any(str(x["ingrId"]) not in idx for x in ls):orphans.append(it)
            elif any(x["name"]!=idx[str(x["ingrId"])][1]["detail_json"]["name"] for x in ls):different.append(it)
        chosen={canon(it[0]):it for it in take(t.records,24)+take(orphans,6)+take(different,6)}
        parents={it[1]["fields"]["item_id"]:it for it in take(s.records,32)}
        for it in chosen.values():
            for x in it[1]["detail_json"]["major"]:
                k=str(x["ingrId"])
                if k in idx:parents[k]=idx[k]
        p_refs={}
        for k,it in sorted(parents.items()):
            n=self.n(s,it)
            r=self.d("FoodEntityDraft",n,{"business_id":"/fields/item_id","internal_row_id":"/fields/id","name":"/detail_json/name","code":"/detail_json/code","source":"/detail_json/source"},{"entity_type":"SOURCE_INGREDIENT_CONCEPT_CANDIDATE","identity_scope":"SOURCE_SCOPED_ONLY"})
            p_refs[k]=r;self.nutrition_map(n,r,s.namespace)
        for it in chosen.values():
            n=self.n(t,it);raw=it[1]
            r=self.d("RecipeDraft",n,{"business_id":"/fields/item_id","internal_row_id":"/fields/id","name":"/detail_json/name","portion_list":"/detail_json/unit","steps":"/detail_json/dishCooksteps"},{"recipe_scope":"SOURCE_RECIPE_NOT_FOOD_INSTANCE","quantity_semantics":"PENDING_NOTE_UNIT_AND_BASIS"})
            self.nutrition_map(n,r,t.namespace)
            for i,x in enumerate(raw["detail_json"]["major"]):
                k=str(x["ingrId"]);path="/detail_json/major/"+str(i)
                q=idx.get(k)
                ok=q is not None and x["code"]==q[1]["detail_json"]["code"]
                parent=p_refs[k] if ok else None
                self.links["nutridata_matched" if ok else "nutridata_hold"]+=1
                if ok and x["name"]!=q[1]["detail_json"]["name"]:self.links["nutridata_name_difference"]+=1
                self.d("RecipeIngredientDraft",n,{"ingredient_id":path+"/ingrId","code":path+"/code","name":path+"/name","amount":path+"/note"},{"recipe_ref":r,"quantity":raw_numeric_slot(x["note"]),"unit":pending("note unit not declared"),"basis":pending("recipe input versus edible amount unresolved"),"parent_ref":slot_value(parent) if ok else pending("no matching business ID plus code"),"link_status":"CANDIDATE_ID_AND_CODE" if ok else "HOLD_UNMATCHED_OR_CONFLICT"},str(i),(r,)+((parent,) if ok else ()))
    def nutrition5k(self):
        # G013 is fallback only; preserve an independent namespace, not N5k360.
        a=self.spec("n5k_ingredient","NDF-G013","fallback:Nutrition5k:ingredient","ingredients_metadata.csv",csv_rows,"per-gram ingredient metadata")
        ds=[self.spec("n5k_dish"+str(i),"NDF-G013","fallback:Nutrition5k:dish","dish_metadata_cafe"+str(i)+".csv",lambda p:csv_rows(p,False),"dish scan metadata") for i in (1,2)]
        ip={x[1]["fields"]["id"]:x for x in a.records}
        require(len(ip)==len(a.records),"N5K_PARENT_DUPLICATE")
        picks=[(s,it) for s in ds for it in take(s.records,16)]
        # Include the dish for which B0 downloaded RGB-D, not a claim of calibrated NeRF geometry.
        for s in ds:
            for it in s.records:
                if it[1]["tokens"][0]=="dish_1558641037" and all(it[0]!=v[0] or s.key!=z.key for z,v in picks):picks.append((s,it))
        pkeys={x[1]["fields"]["id"] for x in take(a.records,16)}
        for _,it in picks:
            v=it[1]["tokens"];require((len(v)-6)%7==0 and len(v)>=13,"N5K_VARIABLE_WIDTH")
            for j in range(6,len(v),7):
                k=v[j];require(re.fullmatch(r"ingr_\d{10}",k) is not None,"N5K_ID_FORMAT")
                # Explicit documented transform: integer metadata ID -> padded string.
                m=str(int(k[5:]));require(m in ip and k=="ingr_"+m.zfill(10),"N5K_PARENT_KEY")
                pkeys.add(m)
        parents={}
        for k in sorted(pkeys):
            n=self.n(a,ip[k])
            r=self.d("FoodEntityDraft",n,{"business_id":"/fields/id","name":"/fields/ingr"},{"entity_type":"SOURCE_INGREDIENT_CONCEPT_CANDIDATE","identity_scope":"SOURCE_SCOPED_ONLY"})
            parents[k]=r
            for c,u in (("cal/g","kcal/g"),("fat(g)","g/g"),("carb(g)","g/g"),("protein(g)","g/g")):
                self.measurement(n,r,a.namespace+":"+c,"/fields/"+esc(c),slot_value(u),slot_value("PER_GRAM_SOURCE_INGREDIENT"),slot_value("SOURCE_REPORTED_USDA_COMPOSITION"),"Q-COMMON-CALC_CANDIDATE")
        for s,it in picks:
            n=self.n(s,it);v=it[1]["tokens"]
            r=self.d("FoodInstanceDraft",n,{"dish_id":"/tokens/0"},{"instance_scope":"NUTRITION5K_SCAN","identity_status":"NATIVE_SCAN_ONLY_GROUP_UNRESOLVED"})
            for j,(c,u) in enumerate((("energy","kcal"),("mass","g"),("fat","g"),("carb","g"),("protein","g")),1):
                self.measurement(n,r,s.namespace+":"+c,"/tokens/"+str(j),slot_value(u),slot_value("TOTAL_SOURCE_SCAN"),slot_value("SOURCE_REPORTED_MASS" if c=="mass" else "SOURCE_REPORTED_COMPOSITION"),"Q-MASS_CANDIDATE" if c=="mass" else "Q-COMMON-CALC_CANDIDATE")
            for j in range(6,len(v),7):
                k=str(int(v[j][5:]));self.link(n,r,parents[k],"/tokens/"+str(j),"ingredient:"+str(j))
                self.links["nutrition5k_parent"]+=1
                # Preserve per-ingredient measures distinctly by source tuple index.
                for off,(c,u) in enumerate((("mass","g"),("energy","kcal"),("fat","g"),("carb","g"),("protein","g")),2):
                    self.measurement(n,r,s.namespace+":ingredient:"+c,"/tokens/"+str(j+off),slot_value(u),slot_value("SOURCE_INGREDIENT_LINE:"+str((j-6)//7)),slot_value("SOURCE_REPORTED_MASS" if c=="mass" else "SOURCE_REPORTED_COMPOSITION"),"Q-MASS_CANDIDATE" if c=="mass" else "Q-COMMON-CALC_CANDIDATE",{"ingredient_id":"/tokens/"+str(j),"ingredient_name":"/tokens/"+str(j+1)})
    def snapme(self):
        s=self.spec("snapme","NDF-G004","snapme:linkfile","master_SNAPME_linkfile.csv",csv_rows,"source linkfile row, not unique intake event",run="20261125_run002")
        groups=C.defaultdict(list)
        for it in s.records:
            f=it[1]["fields"];groups[tuple(f[k] for k in ("subject_id","snapme_study_day","Occ_No","FoodNum1"))].append(it)
        repeats=[v for v in groups.values() if len(v)>1]
        chosen={canon(it[0]):it for it in take(s.records,24)}
        for g in take(repeats,6):
            for it in g[:3]:chosen[canon(it[0])]=it
        for it in chosen.values():
            n=self.n(s,it)
            r=self.d("DietaryObservationDraft",n,{k:"/fields/"+esc(k) for k in ("subject_id","snapme_study_day","filename","FoodCode","FoodNum1","Occ_No","FoodAmt","FoodAmt.1","Food_Description")},{"identity_scope":"SOURCE_PRIVATE_NAMESPACE_ONLY","observation_window":"SOURCE_REPORTED_DAY_NOT_HABITUAL","measurement_role":"REPORTED_DIETARY_LINK_RECORD","aggregation_status":"HOLD_DUPLICATE_GRAIN_UNRESOLVED"})
            for c in ("KCAL","PROT","TFAT","CARB","SODI"):
                self.measurement(n,r,s.namespace+":"+c,"/fields/"+c,pending("source unit dictionary required"),pending("reported record aggregation unresolved"),slot_value("SOURCE_REPORTED_DIETARY_NUTRIENT"),"Q-RECALL_CANDIDATE")
        self.links["snapme_full_nonunique_group_count"]=len(repeats)
        self.links["snapme_sample_duplicate_group_members"]=sum(v for v in C.Counter(tuple(it[1]["fields"][k] for k in ("subject_id","snapme_study_day","Occ_No","FoodNum1")) for it in chosen.values()).values() if v>1)
    def labels(self):
        f=self.spec("food101_train","NDF-G001","food101:class","train.txt",lambda p:line_rows(p,"food101"),"training image index")
        for it in take(f.records,32):
            n=self.n(f,it);self.d("FoodLabelDraft",n,{"label":"/fields/label","image_path":"/fields/path"},{"label_namespace":f.namespace,"label_role":"NATIVE_CLASS_INDEX"})
        for asset,cat,bb in (("NDF-G002","zip_02_category.txt","zip_04_bb_info.txt"),("NDF-G003","zip_01_category.txt","zip_02_bb_info.txt")):
            ns=asset+":mirror"
            f=self.spec(asset+"_category",asset,ns,cat,lambda p:line_rows(p,"category"),"category vocabulary")
            for it in take(f.records,24):
                n=self.n(f,it);self.d("FoodLabelDraft",n,{"business_id":"/fields/label_id","label":"/fields/label"},{"label_namespace":ns,"label_role":"MIRROR_CATEGORY_VOCAB"})
            f=self.spec(asset+"_bbox",asset,ns,bb,lambda p:line_rows(p,"bbox"),"one annotation row in selected archive member")
            for it in take(f.records,24):
                n=self.n(f,it);self.d("MediaObservationDraft",n,{k:"/fields/"+k for k in ("image_key","x1","y1","x2","y2")},{"annotation_kind":"SOURCE_BBOX","media_identity_status":"HOLD_IMAGE_SIZE_AND_MEMBER_CONTEXT"})
        f=self.spec("isia_class","NDF-G005","isia500:class","zip_01_ISIAFood500_classLabel.txt",lambda p:line_rows(p,"isia"),"category vocabulary")
        for it in take(f.records,32):
            n=self.n(f,it);self.d("FoodLabelDraft",n,{"business_id":"/fields/label_id","label":"/fields/label"},{"label_namespace":f.namespace,"label_role":"NATIVE_CATEGORY_VOCAB"})
    def recipe_mirrors(self):
        for asset,ns,run,fields in (("NDF-G012","xiachufang:mirror","20261125_run001",("name","dish","recipeIngredient","recipeInstructions")),("NDF-G018","recipenlg:alternative_mirror","20261125_run002",("title","ingredients","directions","link","source","NER"))):
            s=self.spec(asset+"_recipe",asset,ns,"hf_rows.json",lambda p:json_rows(p,"viewer"),"mirror viewer row",run)
            for it in s.records:
                n=self.n(s,it)
                self.d("RecipeDraft",n,{k:"/row/"+esc(k) for k in fields},{"recipe_scope":"MIRROR_RECIPE_NOT_ORIGINAL_VERSION_OR_FOOD_INSTANCE","quantity_semantics":"RAW_LIST_OR_STRING_ONLY"})
    def off(self):
        for key,fn,style in (("off_single","product_737628064502.json","product"),("off_search","search_breakfast_cereals.json","products")):
            s=self.spec(key,"NDF-G016","off:api_snapshot",fn,lambda p,style=style:json_rows(p,style),"product API record")
            for it in s.records:
                n=self.n(s,it);x=it[1]
                r=self.d("ProductVersionDraft",n,{k:"/"+esc(k) for k in ("code","product_name","nutrition_data_per","nutriments") if k in x},{"product_identity_status":"BARCODE_PLUS_SNAPSHOT_NOT_HISTORICAL_VERSION","nutrition_basis":"SOURCE_API_BASIS_UNQUALIFIED"})
                for c in ("energy-kcal","proteins","fat","carbohydrates","sodium"):
                    v=c+"_100g";u=c+"_unit"
                    if v not in x["nutriments"]:continue
                    extra={"basis":"/nutrition_data_per"}
                    if u in x["nutriments"]:extra["display_unit"]="/nutriments/"+esc(u)
                    self.measurement(n,r,s.namespace+":"+c,"/nutriments/"+esc(v),pending("display unit may differ from unit of normalized API suffix value"),slot_value("SOURCE_SUFFIX_100G"),slot_value("SOURCE_LABEL_DERIVED_API_VALUE"),"Q-LABEL_CANDIDATE",extra)
    def menu(self):
        s=self.spec("menu_items","NDF-G017","menumatch:menu","zip_02_items_info.txt",lambda p:line_rows(p,"menu"),"menu item label and calorie reference")
        p={}
        for it in s.records:
            n=self.n(s,it);key=it[1]["fields"]["menu_key"];require(key not in p,"MENU_DUPLICATE")
            r=self.d("FoodEntityDraft",n,{"business_id":"/fields/menu_key","name":"/fields/menu_name","restaurant":"/fields/restaurant"},{"entity_type":"SOURCE_MENU_ITEM_CANDIDATE","identity_scope":"SOURCE_SCOPED_ONLY"})
            p[key]=r
            self.measurement(n,r,s.namespace+":calories","/fields/calorie",slot_value("kcal"),pending("menu portion denominator not verified"),slot_value("MENU_LABEL_REFERENCE"),"Q-MENU_CANDIDATE")
        s=self.spec("menu_labels","NDF-G017","menumatch:labels","zip_00_labels.txt",lambda p:line_rows(p,"menu_labels"),"image to menu item labels")
        for it in take(s.records,24):
            n=self.n(s,it);r=self.d("MediaObservationDraft",n,{"image_key":"/fields/image_key","labels":"/fields/labels"},{"annotation_kind":"MENU_ITEM_MULTI_LABEL","media_identity_status":"SOURCE_IMAGE_KEY_ONLY"})
            for i,k in enumerate(it[1]["fields"]["labels"]):
                require(k in p,"MENU_ORPHAN")
                self.link(n,r,p[k],"/fields/labels/"+str(i),str(i));self.links["menu_parent"]+=1
    def qa_epic(self):
        s=self.spec("recipeqa","NDF-G020","recipeqa:val","official_val.json",lambda p:json_rows(p,"qa"),"validation question, already exposed")
        for it in take(s.records,24):
            n=self.n(s,it)
            self.d("QARecordDraft",n,{k:"/"+k for k in ("recipe_id","qid","context","choice_list","answer","task","question")},{"exposure_status":"DEVELOPMENT_EXPOSED"})
        s=self.spec("epic_train","NDF-G022","epic100:train","EPIC_100_train.csv",csv_rows,"narrated action segment")
        selected=take(s.records,32);keys={k:{it[1]["fields"][k] for it in selected} for k in ("verb_class","noun_class","video_id")}
        parents={}
        for k,fn,idcol,namecol in (("verb_class","EPIC_100_verb_classes.csv","id","key"),("noun_class","EPIC_100_noun_classes.csv","id","key"),("video_id","EPIC_100_video_info.csv","video_id","video_id")):
            t=self.spec("epic_"+k,"NDF-G022","epic100:"+k,fn,csv_rows,"source "+k+" metadata")
            idx={it[1]["fields"][idcol]:it for it in t.records}
            require(len(idx)==len(t.records),"EPIC_PARENT_DUPLICATE")
            for val in sorted(keys[k]):
                require(val in idx,"EPIC_ORPHAN")
                n=self.n(t,idx[val])
                if k=="video_id":
                    parents[(k,val)]=self.d("VideoMetadataDraft",n,{"business_id":"/fields/"+idcol,"duration":"/fields/duration","fps":"/fields/fps","resolution":"/fields/resolution"},{"media_scope":"SOURCE_VIDEO_METADATA_NOT_MEDIA_BYTES","time_basis":"SOURCE_VIDEO_RELATIVE"})
                else:
                    parents[(k,val)]=self.d("ProcessVocabularyDraft",n,{"business_id":"/fields/"+idcol,"label":"/fields/"+namecol},{"label_namespace":t.namespace,"vocabulary_role":k})
        for it in selected:
            n=self.n(s,it)
            r=self.d("ProcessObservationDraft",n,{k:"/fields/"+k for k in ("narration_id","video_id","start_timestamp","stop_timestamp","start_frame","stop_frame","verb_class","noun_class","narration")},{"event_role":"SOURCE_NARRATED_ACTION_NOT_CONSUMPTION","time_basis":"SOURCE_VIDEO_RELATIVE"})
            for k in ("verb_class","noun_class","video_id"):
                self.link(n,r,parents[(k,it[1]["fields"][k])],"/fields/"+k,k);self.links["epic_parent"]+=1
    def build(self):
        self.nutridata();self.nutrition5k();self.snapme();self.labels();self.recipe_mirrors();self.off();self.menu();self.qa_epic()
        return self
def read_back(folder):
    objs=[]
    for path in sorted(folder.glob("*.jsonl")):
        with path.open(encoding="utf8") as f:
            for line in f:
                o=json.loads(line);require(path.stem==o["kind"],"TYPED_COLLECTION_MISMATCH");objs.append(o)
    return objs
def main(root,out):
    root=root.resolve();out=out.resolve()
    require(not out.exists() and not out.is_relative_to(root/"source_data"),"OUTPUT_OVERWRITE_OR_SOURCE")
    when=datetime.now(timezone.utc).isoformat()
    b=Builder(root,when).build()
    idx=validate_set(b.objects)
    out.mkdir(parents=True);private=out/"private";private.mkdir();tables=private/"typed_collections";tables.mkdir()
    counts=C.Counter(o["kind"] for o in b.objects)
    for k in sorted(counts):
        with (tables/(k+".jsonl")).open("x",encoding="utf8") as f:
            for o in b.objects:
                if o["kind"]==k:f.write(canon(o)+"\n")
    # File fence and explicit local artifact resolver; not exposed to public consumers.
    atomic_json(private/"source_resolver.json",{s.artifact:{"path":str(s.path.relative_to(root)),"sha256":s.expected_sha,"asset_id":s.asset,"namespace":s.namespace} for s in b.specs.values()})
    read=read_back(tables);ridx=validate_set(read)
    require(set(idx)==set(ridx) and all(canon(idx[k])==canon(ridx[k]) for k in idx),"SERIALIZATION_ROUND_TRIP")
    # Reopen actual source files; verify the input hash, exact logical record and source locator.
    source_records=0;anchors=0;fields=0;replayed=C.Counter()
    for s in b.specs.values():
        require(file_sha(s.path)==s.expected_sha,"SOURCE_CHANGED")
        fresh={canon(loc):raw for loc,raw in s.read()}
        require(len(fresh)==len(s.records),"SOURCE_REOPEN_COUNT")
        for (key,loc),r in b.native.items():
            if key!=s.key:continue
            o=resolve(ridx,r,"NativeRecord");p=o["payload"]
            require(loc in fresh and canon(fresh[loc])==canon(p["raw"]),"SOURCE_RECORD_ROUND_TRIP")
            require(digest(fresh[loc])==p["raw_sha256"],"SOURCE_RECORD_HASH")
            a=resolve(ridx,p["anchor_ref"],"SourceAnchor")
            require(a["payload"]["integrity"]==s.expected_sha and a["payload"]["locator"]==p["locator"],"SOURCE_ANCHOR_ROUND_TRIP")
            source_records+=1;anchors+=1;replayed[s.key]+=1
    # Canonical reverse check: use only serialized typed bindings; each path/value must match reopened record.
    # This is selected-field reversibility; no claim of reconstructing an entire record from canonical alone.
    fresh_by_native={r:resolve(ridx,r,"NativeRecord")["payload"]["raw"] for r in b.native.values()}
    for o in read:
        p=o["payload"]
        if "bindings" in p:
            raw=fresh_by_native[p["native_ref"]]
            for bind in p["bindings"].values():
                require(canon(ptr(raw,bind["path"]))==canon(bind["raw_value"]),"FIELD_ROUND_TRIP")
                fields+=1
        validate_dev_projection(dev_projection(o))
    # Rebuild with same audit clock and real sources independently of serialized outputs.
    # Detect wrong/missing paths, not merely compare copied raw payloads.
    rebuilt=Builder(root,when).build();bidx=validate_set(rebuilt.objects)
    require(set(bidx)==set(ridx) and all(canon(bidx[k])==canon(ridx[k]) for k in bidx),"ADAPTER_REPLAY_DRIFT")
    # Re-execute under a distinct audit clock: identities must remain stable; revisions may change.
    second_clock=datetime.now(timezone.utc).isoformat()
    require(second_clock!=when,"CLOCK_NOT_DISTINCT")
    del rebuilt,bidx
    later=Builder(root,second_clock).build();lidx=validate_set(later.objects)
    require({o["object_id"] for o in later.objects}=={o["object_id"] for o in read},"CROSS_RUN_OBJECT_ID_DRIFT")
    require(not (set(ridx)&set(lidx)),"CLOCK_REVISION_NOT_VERSIONED")
    stable_id_count=len({o["object_id"] for o in later.objects})
    del later,lidx
    artifact_count=len(b.specs)
    require(source_records==sum(b.selected.values())==counts["NativeRecord"]==anchors,"ROUNDTRIP_DENOMINATOR")
    atomic_json(private/"collection_manifest.json",{p.name:{"bytes":p.stat().st_size,"sha256":file_sha(p),"rows":counts[p.stem]} for p in tables.glob("*.jsonl")})
    report={"run_id":"B1-U2A-"+out.name,"contract_version":VERSION,"audit_time_utc":when,"status":"PASS_BOUNDED_DEVELOPMENT_ROUNDTRIP","global_B0_pass":False,"global_B1_frozen":False,"release_assets":0,"source_artifact_count":artifact_count,"source_assets":sorted({s.asset for s in b.specs.values()}),"source_scope_count":len({s.asset for s in b.specs.values()}),"sources":[{"adapter":s.key,"asset_id":s.asset,"namespace":s.namespace,"source_role":s.role,"filename":s.path.name,"sha256":s.expected_sha,"source_records_examined":len(s.records),"selected_records":b.selected[s.key],"replayed_records":replayed[s.key]} for s in b.specs.values()],"objects_by_kind":dict(counts),"objects_total":len(read),"native_record_roundtrips":source_records,"source_anchor_roundtrips":anchors,"canonical_field_roundtrips":fields,"serialization_roundtrip_objects":len(read),"deterministic_adapter_replay_objects":len(ridx),"cross_audit_clock_stable_object_ids":stable_id_count,"verified_source_files_before_after":artifact_count,"structural_candidate_links":dict(b.links),"measurement_reference_profile_counts":dict(b.measurements),"scientific_kinds_delegated_uninstantiated":list(SCIENTIFIC_DELEGATED),"purpose":"CURATION_DEV_ONLY","selection":"deterministic spread, deliberate orphan/alias/duplicate cases and dependent parent closure; not random, representative or independent evaluation","limitations":["source hash and exact logical record, not byte reconstruction from canonical alone","shared scientific D0 remains authoritative; no new SCI qualification","no unit/denominator inference, no standardized nutrient calculation, no entity equivalence, no physical scale for N5k360","real-source grounded mirror rows are facts about retrieved mirror, not verified original version","no raw data in shared report"]}
    atomic_json(out/"RealSampleRoundTripReport.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="sources"},ensure_ascii=False))
    for s in report["sources"]:print("SOURCE",s["adapter"],s["source_records_examined"],s["selected_records"],s["replayed_records"])
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--out",type=P.Path,required=True);a=p.parse_args();main(a.root,a.out)
