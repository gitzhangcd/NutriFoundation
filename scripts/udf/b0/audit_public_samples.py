#!/usr/bin/env python3
"""Validate bounded public sample run; emit aggregate-only evidence, never raw records."""
import pathlib as P,json,csv,collections as C,hashlib,re,urllib.parse as U,argparse,datetime as DT
from decimal import Decimal,InvalidOperation
ROOT=P.Path("source_data/public_samples")
RUN=P.Path("runs/B0/U1-A/public_samples_001")
def load(p):return json.loads(p.read_text(encoding="utf8"))
def rows(p):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.reader(f))
def dic(p):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def txt(p):return [l.strip() for l in p.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
def distinct(rows,key):
 return len({r[key] for r in rows if r.get(key,"").strip()})
def num(v):
 try:return Decimal(v.strip()).is_finite()
 except (InvalidOperation,AttributeError,ValueError):return False
def viewer(p):
 a=load(p); rr=[x["row"] for x in a["rows"]]
 return {"rows":len(rr),"fields":list(rr[0]) if rr else [],"viewer_total_reported":a.get("num_rows_total"),"class_label_count":[len(x.get("type",{}).get("names",[])) for x in a.get("features",[]) if x.get("type",{}).get("_type")=="ClassLabel"]}
def main():
 a=ROOT/"20261125_run001";b=ROOT/"20261125_run002"
 m1=load(RUN/"NativeAcquisitionManifest_private.json");m2=load(RUN/"NativeAcquisitionFollowup_private.json")
 mm=[(a,m1),(b,m2)]
 issues=[];rmap=C.defaultdict(list);allfiles=[]
 for base,m in mm:
  for r in m["records"]:
   rmap[r["asset_id"]].append((base,r))
   for x in r["files"]:
    f=base/r["asset_id"]/x["file"]
    if not f.is_file() or f.stat().st_size!=x["bytes"] or sha(f)!=x["sha256"]:issues.append({"asset":r["asset_id"],"file":x["file"],"issue":"integrity mismatch"})
    # Strip query strings, no signed URLs/row values/private absolute paths.
    u=U.urlsplit(x["source_url"]);stable=U.urlunsplit((u.scheme,u.netloc,u.path,"",""))
    allfiles.append({"asset_id":r["asset_id"],"run":base.name,"file":x["file"],"source_url_no_query":stable,"role":x["role"],"bytes":x["bytes"],"sha256":x["sha256"]})
 if len(m1["records"])!=22 or len(rmap)!=22:issues.append({"issue":"source inventory cardinality"})
 p=lambda i,base=a:base/f"NDF-G{i:03d}"
 checks={}
 # Food101 exact published metadata checksum.
 f=p(1)/"train.txt";raw=txt(f);inf=load(p(1)/"dataset_infos.json")
 classes=inf["default"]["features"]["label"]["names"]
 checks["G001"]={"train_index_rows":len(raw),"train_index_unique":len(set(raw)),"class_vocabulary":len(classes),"published_train_sha256_match":sha(f)=="2920f7d55473974492b41a01241ccfd71df1b74d29d27b617337f840f58f77ab","viewer":viewer(p(1)/"hf_rows.json")}
 for i in (2,3):
  q=p(i);cat=next(x for x in q.glob("*.txt") if x.name.endswith("_category.txt"))
  labels=txt(cat);idset={l.split(None,1)[0] for l in labels[1:]};bb=[]
  for x in q.glob("*bb_info.txt"):
   ls=txt(x);n=len(ls)-1
   ok=0
   for l in ls[1:]:
    z=l.split()
    try:
     if len(z)==5:
      x1,y1,x2,y2=map(int,z[1:]);ok+=x2>=x1 and y2>=y1 and x1>=0 and y1>=0
    except ValueError:pass
   bb.append({"rows":n,"numeric_ordered_nonnegative":ok})
  checks[f"G{i:03d}"]={"category_rows_excluding_header":len(labels)-1,"distinct_category_ids":len(idset),"bbox_file_profiles":bb,"sample_images":len(list(q.glob("*.jpg"))),"identity":"mirror archive, local original version not compared"}
 # SNAPMe keep individual IDs private, count only.
 s=dic(p(4,b)/"master_SNAPME_linkfile.csv");k=rows(p(4,b)/"master_SNAPME_linkfile.csv")
 ck={}
 for ks in [["subject_id","snapme_study_day","FoodNum1"],["subject_id","snapme_study_day","Occ_No","FoodNum1"]]:
  keys=[tuple(x.get(z,"") for z in ks) for x in s];ck["+".join(ks)]={"unique":len(set(keys)),"missing_key_rows":sum(any(not y.strip() for y in v) for v in keys)}
 checks["G004"]={"rows":len(s),"fields":len(k[0]),"width_hist":dict(C.Counter(len(x) for x in k[1:])),"subjects":distinct(s,"subject_id"),"subject_days":len({(x["subject_id"],x["snapme_study_day"]) for x in s}),"distinct_nonblank_raw_filename_strings":distinct(s,"filename"),"food_codes":distinct(s,"FoodCode"),"candidate_keys":ck,"field_names":k[0],"foodamt_numeric_rows":sum(num(x["FoodAmt"]) for x in s),"foodamt1_numeric_rows":sum(num(x["FoodAmt.1"]) for x in s),"foodamt_equal_raw_rows":sum(x["FoodAmt"]==x["FoodAmt.1"] for x in s)}
 c=txt(p(5)/"zip_01_ISIAFood500_classLabel.txt")
 checks["G005"]={"class_rows":len(c),"unique_last_field_ids":len({x.rsplit(None,1)[-1] for x in c}),"val_finetune_rows":len(txt(p(5)/"zip_03_val_finetune.txt")),"note":"native metadata; validation rows exposed for development; not an independent evaluation release"}
 for i,expected in [(6,16643),(14,5000)]:
  z=load(p(i,b)/"archive_class_index.json");g=z["group_hist"];checks[f"G{i:03d}"]={"rejected_first_viewer":viewer(p(i)/"hf_rows.json"),"corrected_archive_images":z["image_member_count"],"matches_published_image_count":z["image_member_count"]==expected,"group_hist":g,"corrected_media_samples":len(list(p(i,b).glob("image_*")))}
 t=rows(p(7)/"train_info_dirty.csv")
 checks["G007"]={"mirror_rows":len(t),"width_hist":dict(C.Counter(len(x) for x in t)),"unique_first_column":len({x[0] for x in t}),"numeric_second_column":sum(len(x)==2 and x[1].strip().isdigit() for x in t),"provisional":True}
 d=load(p(9)/"training_categories.json");dirs=[x["name"] for x in d if x.get("type")=="dir"]
 checks["G009"]={"training_directories":len(dirs),"casefold_unique":len({x.casefold() for x in dirs}),"sample_images":len(list(p(9).glob("*.jpg"))),"note":"image/metadata releases not proven paired"}
 checks["G011"]={"author_processed_files":[{"file":x["file"],"variables":x["profile"].get("variables",[])} for _,r in rmap["NDF-G011"] for x in r["files"] if x["file"].endswith(".mat")],"raw_353_ingredient_labels":"NOT_ACQUIRED"}
 checks["G012"]=viewer(p(12)/"hf_rows.json")
 # Nutrition5k fallback: six fixed fields then seven per ingredient. Metadata uses integer ids.
 d=[r for f in sorted(p(13).glob("dish_metadata_*.csv")) for r in rows(f)]
 ing=rows(p(13)/"ingredients_metadata.csv");parent={"ingr_"+x[1].zfill(10) for x in ing[1:] if len(x)>1 and x[1].isdigit()}
 ids={r[0] for r in d};refs=[];bad=0
 for r in d:
  if len(r)<13 or (len(r)-6)%7:bad+=1;continue
  refs.extend(r[j] for j in range(6,len(r),7))
 spl={}
 for kind in ("rgb","depth"):
  tr=set(txt(p(13)/(kind+"_train_ids.txt")));te=set(txt(p(13)/(kind+"_test_ids.txt")))
  spl[kind]={"train":len(tr),"test":len(te),"overlap":len(tr&te),"unknown":len((tr|te)-ids)}
 checks["G013"]={"fallback_source":"official Nutrition5k","native_N5k360_scene_data":"NOT_ACQUIRED","dish_rows":len(d),"unique_dishes":len(ids),"shape_mismatch":bad,"ingredient_metadata_rows":len(ing)-1,"ingredient_parent_ids":len(parent),"ingredient_line_count":len(refs),"ingredient_id_match_after_explicit_zero_pad":sum(v in parent for v in refs),"ingredient_id_unmatched":sum(v not in parent for v in refs),"splits":spl,"sample_media":len(list(p(13).glob("fallback*.png")))}
 off=load(p(16)/"product_737628064502.json");more=load(p(16)/"search_breakfast_cereals.json")
 pp=[off["product"]]+more["products"]
 checks["G016"]={"records":len(pp),"distinct_codes":len({x.get("code") for x in pp}),"nutriments_object_count":sum(isinstance(x.get("nutriments"),dict) for x in pp),"basis_strings":dict(C.Counter(str(x.get("nutrition_data_per","UNSPECIFIED")) for x in pp))}
 lab=[list(filter(None,(x.strip() for x in l.split(";")))) for l in txt(p(17)/"zip_00_labels.txt")];im=[list(filter(None,(x.strip() for x in l.split(";")))) for l in txt(p(17)/"zip_02_items_info.txt")][1:];keys={x[1] for x in im if len(x)>=2};occ=[k for l in lab for k in l[1:]]
 checks["G017"]={"image_label_records":len(lab),"unique_image_keys":len({x[0] for x in lab}),"menu_rows":len(im),"label_occurrences":len(occ),"matched_label_occurrences":sum(x in keys for x in occ),"distinct_menu_labels":len(keys)}
 checks["G018"]={"rejected_for_native_schema_first":viewer(p(18)/"hf_rows.json"),"alternative":viewer(p(18,b)/"hf_rows.json"),"version_equivalence":"UNRESOLVED"}
 z=load(p(20)/"official_val.json")["data"]
 checks["G020"]={"validation_questions":len(z),"qid_unique":len({str(x.get("qid")) for x in z}),"recipe_ids":len({str(x.get("recipe_id")) for x in z}),"task_counts":dict(C.Counter(str(x.get("task")) for x in z)),"field_names":list(z[0]),"purpose":"CURATION_DEV; validation exposure"}
 shapes=[]
 for f in sorted(p(21).glob("*.json")):
  z=load(f)
  if all(k in z for k in ("images","annotations","categories")):
   ims={x.get("id") for x in z["images"]};cats={x.get("id") for x in z["categories"]}
   shapes.append({"file":f.name,"format":"COCO-like transformed","images":len(z["images"]),"annotations":len(z["annotations"]),"categories":len(z["categories"]),"orphan_images":sum(x.get("image_id") not in ims for x in z["annotations"]),"orphan_categories":sum(x.get("category_id") not in cats for x in z["annotations"])})
  else:
   shapes.append({"file":f.name,"format":"image-keyed JSON mirror","image_keys":len(z),"list_item_count":sum(len(x) for x in z.values() if isinstance(x,list))})
 checks["G021"]={"mirror_shapes":shapes,"original_mat_and_polygon_files":"NOT_QUALIFIED"}
 e=p(22);rr=dic(e/"EPIC_100_train.csv");verb={x["id"] for x in dic(e/"EPIC_100_verb_classes.csv")};noun={x["id"] for x in dic(e/"EPIC_100_noun_classes.csv")};vid={x["video_id"] for x in dic(e/"EPIC_100_video_info.csv")}
 checks["G022"]={"training_rows":len(rr),"unique_narration_id":distinct(rr,"narration_id"),"participants":distinct(rr,"participant_id"),"verb_vocab":len(verb),"noun_vocab":len(noun),"video_metadata":len(vid),"orphan_verb":sum(x["verb_class"] not in verb for x in rr),"orphan_noun":sum(x["noun_class"] not in noun for x in rr),"orphan_video":sum(x["video_id"] not in vid for x in rr),"start_stop_frame_invalid":sum(not(x["start_frame"].isdigit() and x["stop_frame"].isdigit() and int(x["start_frame"])<=int(x["stop_frame"])) for x in rr)}
 status={1:"OFFICIAL_NATIVE_SAMPLE",2:"MIRROR_ARCHIVE_PROVISIONAL",3:"MIRROR_ARCHIVE_PROVISIONAL",4:"OFFICIAL_NATIVE_LINKFILE",5:"OFFICIAL_NATIVE_METADATA",6:"CORRECTED_MIRROR_ARCHIVE",7:"MIRROR_ANNOTATION_PROVISIONAL",8:"HOLD_TERMS_OR_NATIVE_FILES",9:"OFFICIAL_NATIVE_SAMPLE",10:"HOLD_NATIVE_FILES_NOT_FOUND",11:"AUTHOR_PROCESSED_TOY_SAMPLE",12:"MIRROR_SAMPLE_PROVISIONAL",13:"FALLBACK_NUTRITION5K_NATIVE_N5K360_HOLD",14:"CORRECTED_MIRROR_ARCHIVE",15:"HOLD_GATED",16:"OFFICIAL_CURRENT_API_SAMPLE",17:"OFFICIAL_NATIVE_METADATA",18:"ALTERNATIVE_MIRROR_PROVISIONAL",19:"HOLD_NO_PUBLIC_NATIVE_RECORDS",20:"OFFICIAL_NATIVE_VALIDATION_EXPOSED",21:"MIRROR_ANNOTATION_PROVISIONAL",22:"OFFICIAL_NATIVE_TRAIN_METADATA"}
 sr=[]
 for i in range(1,23):
  k=f"NDF-G{i:03d}";f=[x for x in allfiles if x["asset_id"]==k];rr=rmap[k]
  sr.append({"asset_id":k,"name":rr[0][1]["name"],"status":status[i],"purpose":"CURATION_DEV_ONLY","saved_files":len(f),"saved_bytes":sum(x["bytes"] for x in f),"files":f,"profile":checks.get(k[4:],{}),"attempt_count":sum(len(r["attempts"]) for _,r in rr),"local_original_version_match":"UNRESOLVED","qualified_for_release":False})
 res={"run_id":"B0-public-samples-20261125-001","authority":"AI Nutri UDF v2.1","purpose":"CURATION_DEV_ONLY","utc":DT.datetime.now(DT.timezone.utc).isoformat(),"source_count":len(sr),"actual_target_sample_or_metadata_sources":sum(not x["status"].startswith(("HOLD","FALLBACK")) for x in sr),"fallback_sources":sum(x["status"].startswith("FALLBACK") for x in sr),"hold_sources":sum(x["status"].startswith("HOLD") for x in sr),"files":len(allfiles),"bytes":sum(x["bytes"] for x in allfiles),"file_integrity_issues":issues,"records":sr,"warning":"Retrieved data, metadata, and transformed mirrors are not equivalent to the user's original version, qualified research assets or independent evaluation. Raw sample files and private acquisition manifests remain local; no raw record values or signed URLs included."}
 out=RUN/"PublicSampleAudit_shareable.json"
 with out.open("x",encoding="utf8") as h:json.dump(res,h,ensure_ascii=False,indent=2)
 print(json.dumps({k:res[k] for k in ("source_count","actual_target_sample_or_metadata_sources","fallback_sources","hold_sources","files","bytes","file_integrity_issues")},ensure_ascii=False))
 for x in sr:print(x["asset_id"],x["status"],x["saved_files"],x["saved_bytes"],json.dumps(x["profile"],ensure_ascii=False,separators=(",",":"))[:2400])
if __name__=="__main__":main()
