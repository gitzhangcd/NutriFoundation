"""Manifest-based reader and typed semantic constraints for the U2-C runtime.
The historical profile is data, not hard-coded in validators. All reads are scoped
to the project; original objects/references are resolved by immutable revision.
"""
from core import *
import collections as C
import csv
from datetime import datetime,timezone
POLICY=P_POLICY=Path("configs/udf/u2c/U2C_Policy_v0.1.json")
SCHEMA=Path("schemas/udf/u2c/UDF_U2C_UnifiedContract_v0.1.schema.json")
def local(root,p):
    p=root/Path(p);q=p.resolve()
    require(q.is_relative_to(root) and p.is_file() and not p.is_symlink(),"UNAUTHORIZED_INPUT_PATH")
    return q
def file_check(root,p,h):
    q=local(root,p);require(sha(q)==h,"INPUT_HASH_MISMATCH");return q
def build_manifest(root,profile_path,out):
    root=root.resolve();profile=load(local(root,profile_path))
    files={}
    def pin(p,h=None,git=None):
        q=local(root,p);v=sha(q)
        if h:require(v==h,"BASELINE_HASH_MISMATCH")
        if git:require(blob(q)==git,"BASELINE_BLOB_MISMATCH")
        files[str(Path(p))]={"sha256":v,"bytes":q.stat().st_size}
        return q
    for p in (profile_path,POLICY,SCHEMA):pin(p)
    pin("docs/AI_Nutri_Unified_Data_Foundation_v2.1.md",git=profile["master_blob"])
    for p,h in profile["legacy_code_blobs"].items():pin(p,git=h)
    for s in profile["stages"]:
        base=Path(s["run"]);p=base/"private/collection_manifest.json"
        m=load(pin(p,s["collection_manifest_sha256"]))
        require(len(m)==s["expected_kinds"] and sum(v["rows"] for v in m.values())==s["expected_objects"],"BASELINE_COUNTS")
        require(set(m)=={q.name for q in (root/base/"private/typed_collections").glob("*.jsonl")},"BASELINE_COLLECTION_SET")
        for name,x in m.items():pin(base/"private/typed_collections"/name,x["sha256"])
        pin(base/s["receipt"],git=s["receipt_git_blob"])
    for x in profile["private_inputs"].values():pin(x["path"],x["sha256"])
    sr=load(root/profile["private_inputs"]["source_resolver"]["path"])
    for x in sr.values():pin(x["path"],x["sha256"])
    for p in profile["authority_paths"].values():pin(p)
    # B2 source snapshots carry explicit file versions; verify each against its source bytes.
    for s in profile["stages"]:
        p=root/s["run"]/"private/typed_collections/SourceSnapshotDraft.jsonl"
        if not p.is_file():continue
        for o in lines(p):
            v=o["payload"];pin(v["path"],v["sha256"])
    off=load(root/profile["private_inputs"]["off_acquisition"]["path"])
    for x in off["attempts"]:
        if x.get("http")==200:
            p=Path(profile["private_inputs"]["off_acquisition"]["path"]).parent/x["file"]
            pin(p,x["sha256"])
    # Runtime source hashes included independently of profile expectations.
    # Repository distribution uses the same filenames under scripts/udf/u2c.
    for p in sorted((root/"src/u2c").glob("*.py")):pin(p.relative_to(root))
    manifest={"manifest_version":"UDF-U2C-RUN-MANIFEST-0.1","profile":str(profile_path),"profile_id":profile["profile_id"],
              "base_commit":profile["base_commit"],"audit_clock":datetime.now(timezone.utc).isoformat(),"policy_path":str(POLICY),"schema_path":str(SCHEMA),
              "files":files,"purpose":"CURATION_DEV_ONLY","release_authorized":False}
    put(out,manifest);return manifest
class Baseline:
    def __init__(self,root,manifest):
        self.root=root.resolve();self.manifest=manifest
        require(manifest["manifest_version"]=="UDF-U2C-RUN-MANIFEST-0.1" and manifest["release_authorized"] is False,"RUN_MANIFEST")
        self.verify_files()
        self.profile=load(local(self.root,manifest["profile"]));self.policy=load(local(self.root,manifest["policy_path"]))
        require(self.profile["profile_id"]==manifest["profile_id"] and self.profile["base_commit"]==manifest["base_commit"],"PROFILE_IDENTITY")
        self.schemas=Schemas(local(self.root,manifest["schema_path"]))
        self.idx={};self.stage={};self.by=C.defaultdict(list);self.source_counts={}
        for s in self.profile["stages"]:
            run=Path(s["run"]);m=load(file_check(self.root,run/"private/collection_manifest.json",s["collection_manifest_sha256"]))
            require(blob(local(self.root,run/s["receipt"]))==s["receipt_git_blob"],"UPSTREAM_RECEIPT_BLOB")
            n=0
            for fn,v in sorted(m.items()):
                p=file_check(self.root,run/"private/typed_collections"/fn,v["sha256"]);nr=0
                for o in lines(p):
                    revision_ok(o);r=ref(o)
                    require(r not in self.idx and o["kind"]==p.stem,"LEGACY_TYPE_OR_DUPLICATE")
                    require(o["lifecycle"]=="DRAFT" and o["purpose"]=="CURATION_DEV","LEGACY_RELEASE")
                    require(o["purpose_release_ref"]["tag"]=="PENDING","LEGACY_RELEASE_REF")
                    self.idx[r]=o;self.stage[r]=s["stage"];self.by[o["kind"]].append(o);nr+=1
                require(nr==v["rows"],"LEGACY_COLLECTION_COUNT");n+=nr
            require(n==s["expected_objects"] and len(m)==s["expected_kinds"],"HISTORICAL_REGRESSION_COUNT")
            self.source_counts[s["stage"]]=n
        self.resolver=load(self.input("source_resolver"))
        require(set(self.resolver)=={ref(o) for o in self.by["SourceArtifact"]},"SOURCE_RESOLVER_CLOSURE")
        for r,x in self.resolver.items():
            a=self.idx[r]["payload"]
            require(a["file_sha256"]==x["sha256"] and a["namespace"]==x["namespace"],"SOURCE_RESOLVER_IDENTITY")
            file_check(self.root,x["path"],x["sha256"])
        for o in self.by["SourceSnapshotDraft"]:
            p=o["payload"];file_check(self.root,p["path"],p["sha256"])
        for o in self.by["AuthoritySnapshot"]:
            p=o["payload"];key=p["authority_key"]
            if key in self.profile["authority_paths"]:
                file_check(self.root,self.profile["authority_paths"][key],p["sha256"])
                require(p["verification"]=="LOCAL_SOURCE_BYTES_VERIFIED","AUTHORITY_VERIFICATION_STATE")
            else:require(p["verification"]=="PROJECT_UPSTREAM_DOCUMENT_HASH_RECORDED_CLOUD","AUTHORITY_VERIFICATION_STATE")
        self.concepts={o["payload"]["component_id"]:o for o in self.by["ComponentConcept"]}
        self.definitions={ref(o):o for o in self.by["MeasurementDefinition"]}
        self.interpretations={o["payload"]["source_measurement_ref"]:o for o in self.by["MeasurementInterpretation"]}
        require(len(self.interpretations)==len(self.by["MeasurementInterpretation"]),"MEASUREMENT_INTERPRETATION_DUPLICATE")
        self.ns_cache={};self.dom_cache={};self._domains_visiting=set();self.quality={};self.quality_by_measurement={}
    def input(self,key):
        p=self.profile["private_inputs"][key];return file_check(self.root,p["path"],p["sha256"])
    def verify_files(self):
        for p,v in self.manifest["files"].items():
            q=file_check(self.root,p,v["sha256"]);require(q.stat().st_size==v["bytes"],"INPUT_SIZE_CHANGED")
    def ns(self,o):
        r=ref(o)
        if r not in self.ns_cache:self.ns_cache[r]=legacy_ns(self.idx,o)
        return self.ns_cache[r]
    def domains(self,r):
        if r in self.dom_cache:return self.dom_cache[r]
        require(r not in self._domains_visiting,"DEPENDENCY_CYCLE")
        self._domains_visiting.add(r);o=lookup(self.idx,r);p=o["payload"];k=o["kind"]
        if k=="SourceArtifact":s={namespace_domain(self.policy,p["namespace"])}
        elif k=="SourceSnapshotDraft":s={namespace_domain(self.policy,p["scope"])}
        elif k=="AuthoritySnapshot":s={"AUTHORITY_SOURCE_REVIEW"}
        else:s=set()
        for rr in o["dependency_refs"]+o["provenance_refs"]:s.update(self.domains(rr))
        if not s:s={self.policy["default_rights_domain"]}
        a=tuple(sorted(s));self.dom_cache[r]=a;self._domains_visiting.remove(r);return a
    def family_guard(self,o):
        p=o["payload"]
        require(p["independent_measurement_claim"] is False and p["independence_status"] in ("POTENTIAL_SHARED_UPSTREAM","INDEPENDENCE_UNRESOLVED"),"FAMILY_INDEPENDENCE_UNQUALIFIED")
        expect=expected_family(self.policy,p["carrier_scope"],p["reported_source_label"])
        require(expect is not None and p["potential_family"]==expect,"SOURCE_FAMILY_POLICY_MISMATCH")
        s=[lookup(self.idx,r,"SourceSnapshotDraft") for r in o["dependency_refs"]]
        require(len(s)==1 and s[0]["payload"]["scope"]==p["carrier_scope"],"FAMILY_CARRIER_MISMATCH")
        prov(o,[ref(s[0])])
    def validate_legacy(self,o):
        """Type/edge/scientific checks independent of revision sealing.
        Schema shape is separately validated on every projected record.
        """
        revision_ok(o);p=o["payload"];k=o["kind"];ix=self.idx
        require(o["purpose"]=="CURATION_DEV" and o["lifecycle"]=="DRAFT" and o["purpose_release_ref"]["tag"]=="PENDING","RELEASE_BLOCKED")
        for key in ("provenance_refs","dependency_refs"):
            require(isinstance(o[key],list) and len(set(o[key]))==len(o[key]),"IMMUTABLE_REFS")
            for rr in o[key]:
                a=lookup(ix,rr);require(rr!=ref(o),"SELF_REFERENCE")
                if o["instance_class"]=="REAL_SOURCE_GROUNDED":require(a["instance_class"]=="REAL_SOURCE_GROUNDED","REAL_DEPENDS_ON_NONREAL")
        if k=="SourceAnchor":
            a=lookup(ix,p["source_ref"],"SourceArtifact");prov(o,[p["source_ref"]]);require(p["integrity"]==a["payload"]["file_sha256"],"ANCHOR_INTEGRITY")
        elif k=="NativeRecord":
            a=lookup(ix,p["artifact_ref"],"SourceArtifact");b=lookup(ix,p["anchor_ref"],"SourceAnchor")
            deps(o,[p["artifact_ref"]]);prov(o,[p["anchor_ref"]])
            require(b["payload"]["source_ref"]==p["artifact_ref"] and b["payload"]["locator"]==p["locator"] and digest(p["raw"])==p["raw_sha256"],"NATIVE_RECORD_ANCHOR_OR_DIGEST")
        elif "native_ref" in p and "bindings" in p:
            n=lookup(ix,p["native_ref"],"NativeRecord");deps(o,[p["native_ref"]]);prov(o,[n["payload"]["anchor_ref"]])
            for b in p["bindings"].values():require(canon(pointer(n["payload"]["raw"],b["path"]))==canon(b["raw_value"]),"CANONICAL_SOURCE_DRIFT")
            if k=="RecipeIngredientDraft":
                recipe=lookup(ix,p["recipe_ref"],"RecipeDraft");deps(o,[p["recipe_ref"]])
                require(recipe["payload"]["native_ref"]==p["native_ref"],"RECIPE_SOURCE_MISMATCH")
                rule=recipe_policy(self.policy,self.ns(o))
                require(rule["quantity_policy"]=="PENDING_UNIT_AND_BASIS" and p["unit"]["tag"]==p["basis"]["tag"]=="PENDING","RECIPE_NOTE_UNIT_BASIS_HOLD")
                q=number(bound(o,"amount"))
                if q is not None:require(p["quantity"]["tag"]=="VALUE" and number(p["quantity"]["value"])==q,"RECIPE_QUANTITY_DRIFT")
                else:require(p["quantity"]["tag"]!="VALUE","RECIPE_QUANTITY_DRIFT")
                if p["parent_ref"]["tag"]=="VALUE":
                    r=p["parent_ref"]["value"];a=lookup(ix,r,rule["parent_kind"]);deps(o,[r])
                    require(self.ns(a)==rule["parent_namespace"] and p["link_status"]=="CANDIDATE_ID_AND_CODE","RECIPE_PARENT_POLICY")
                    key_transform(bound(o,rule["child_key"]),bound(a,rule["parent_key"]),rule["transform"])
                    require(bound(o,rule["crosscheck_key"])==bound(a,rule["crosscheck_key"]),"BUSINESS_KEY_CODE_MISMATCH")
                else:require(p["link_status"]=="HOLD_UNMATCHED_OR_CONFLICT","RECIPE_LINK_STATUS")
            elif k=="NativeLinkDraft":
                a=lookup(ix,p["left_ref"]);b=lookup(ix,p["right_ref"]);deps(o,[p["left_ref"],p["right_ref"]])
                require(a["payload"]["native_ref"]==p["native_ref"] and p["relation_type"]=="NATIVE_CANDIDATE_LINK" and p["semantic_qualification"]=="PENDING","LINK_PROMOTION")
                rule=link_policy(self.policy,self.ns(a),self.ns(b),a["kind"],b["kind"],p["bindings"]["source_key"]["path"])
                key_transform(bound(o,"source_key"),bound(b,"business_id"),rule["transform"])
            elif k=="NutrientMeasurementDraft":
                a=lookup(ix,p["subject_ref"]);deps(o,[p["subject_ref"]]);require(a["payload"]["native_ref"]==p["native_ref"],"MEASUREMENT_SUBJECT_MISMATCH")
                require(p["qualification"]["tag"]==p["normalized_value"]["tag"]=="PENDING","MEASUREMENT_PROMOTION")
                require(p["component_key"].startswith(self.ns(o)+":"),"MEASUREMENT_NAMESPACE")
                q=number(bound(o,"value"))
                if q is not None:require(p["original_value"]["tag"]=="VALUE" and number(p["original_value"]["value"])==q,"MEASUREMENT_VALUE_DRIFT")
                else:require(p["original_value"]["tag"]!="VALUE","MEASUREMENT_VALUE_DRIFT")
            elif k=="DietaryObservationDraft":require(p["aggregation_status"]=="HOLD_DUPLICATE_GRAIN_UNRESOLVED" and p["observation_window"]=="SOURCE_REPORTED_DAY_NOT_HABITUAL","DIETARY_STATE_INFLATION")
            elif k=="QARecordDraft":require(p["exposure_status"]=="DEVELOPMENT_EXPOSED","EXPOSURE_STATE")
        elif k=="MeasurementDefinition":
            r=ref(self.concepts[p["component_ref"]]);deps(o,[r])
            require(p["validity"]["tag"]=="PENDING" and p["qualification"]!="SCIENCE_CALCULATION_QUALIFIED","MEASUREMENT_PROMOTION")
        elif k=="MeasurementInterpretation":
            a=lookup(ix,p["source_measurement_ref"],"NutrientMeasurementDraft");d=lookup(ix,p["measurement_definition_ref"],"MeasurementDefinition")
            deps(o,[p["source_measurement_ref"],p["measurement_definition_ref"]])
            require(a["payload"]["component_key"]==d["payload"]["concept_key"] and p["source_native_ref"]==a["payload"]["native_ref"] and canon(p["source_raw"])==canon(bound(a,"value")),"MEASUREMENT_INTERPRETATION_DRIFT")
            require(p["qualification"]=="HOLD_NOT_SCIENTIFICALLY_QUALIFIED" and p["normalized_food_value"]["tag"]=="PENDING","MEASUREMENT_PROMOTION")
            if p["conversion_ref"]["tag"]=="VALUE":
                r=p["conversion_ref"]["value"];c=lookup(ix,r,"RepresentationConversion");deps(o,[r])
                require(c["payload"]["source_measurement_ref"]==p["source_measurement_ref"] and c["payload"]["measurement_definition_ref"]==p["measurement_definition_ref"],"CONVERSION_DEPENDENCY")
        elif k=="RepresentationConversion":
            a=lookup(ix,p["source_measurement_ref"],"NutrientMeasurementDraft");d=lookup(ix,p["measurement_definition_ref"],"MeasurementDefinition")
            deps(o,[p["source_measurement_ref"],p["measurement_definition_ref"]])
            require(p["qualification"]=="REPRESENTATION_ONLY" and number(p["input"])==number(bound(a,"value")) and number(p["value"])==number(p["input"])*number(p["factor"]),"CONVERSION_DRIFT")
            op=p["operation"];basis=p["output_basis"]
            if op=="SAME_SOURCE_DENOMINATOR_SCALE_1G_TO_100G":
                require(number(p["factor"])==Decimal(100) and d["payload"]["basis"]==val("PER_GRAM_SOURCE_INGREDIENT") and basis=="PER_100G_SAME_SOURCE_INGREDIENT_REFERENCE","CONVERSION_BASIS")
            elif op=="SAME_SOURCE_NUMERATOR_MG_TO_G":
                require(number(p["factor"])==Decimal("0.001") and d["payload"]["unit"]==val("mg") and p["numerator_unit"]=="g","CONVERSION_UNIT")
            else:raise ContractError("CONVERSION_POLICY_UNREGISTERED")
        elif k=="QuantityInterpretation":
            a=lookup(ix,p["source_object_ref"],("RecipeIngredientDraft","DietaryObservationDraft"));deps(o,[p["source_object_ref"],p["measurement_definition_ref"]])
            lookup(ix,p["measurement_definition_ref"],"MeasurementDefinition")
            if a["kind"]=="RecipeIngredientDraft":
                require(canon(p["source_raw"])==canon(bound(a,"amount")) and p["unit"]["tag"]==p["basis"]["tag"]=="PENDING","QUANTITY_DRIFT")
            else:require(canon(p["source_raw"])==canon(bound(a,"FoodAmt")) and canon(p["duplicate_raw_column_retained"])==canon(bound(a,"FoodAmt.1")) and p["aggregation"]=="NO_AGGREGATION_ONE_FIELD_NOT_TWO","QUANTITY_AGGREGATION")
        elif k=="NativeNamespace":
            require(bool(p["snapshot_artifact_refs"]),"NAMESPACE_EMPTY")
            for rr in p["snapshot_artifact_refs"]:
                a=lookup(ix,rr,"SourceArtifact");require(a["payload"]["namespace"]==p["native_namespace"],"NAMESPACE_ARTIFACT_MISMATCH")
            prov(o,p["snapshot_artifact_refs"])
        elif k=="NamespaceBinding":
            n=lookup(ix,p["native_ref"],"NativeRecord");a=lookup(ix,p["artifact_ref"],"SourceArtifact");q=lookup(ix,p["namespace_ref"],"NativeNamespace");deps(o,[p["native_ref"],p["namespace_ref"]])
            require(p["artifact_ref"]==n["payload"]["artifact_ref"] and canon(p["key_value"])==canon(n["payload"]["locator"]) and a["payload"]["namespace"]==q["payload"]["native_namespace"] and p["global_entity"] is False,"NAMESPACE_BINDING_MISMATCH")
        elif k=="NamespaceKeyBinding":
            a=lookup(ix,p["source_object_ref"]);q=lookup(ix,p["namespace_ref"],"NativeNamespace");deps(o,[p["source_object_ref"],p["namespace_ref"]])
            require(self.ns(a)==q["payload"]["native_namespace"] and p["namespace_id"]==q["payload"]["namespace_id"] and canon(p["key_value"])==canon(bound(a,p["key_field"])),"NAMESPACE_KEY_MISMATCH")
        elif k=="NamespaceLinkQualification":
            a=lookup(ix,p["source_candidate_ref"],("NativeLinkDraft","RecipeIngredientDraft"));deps(o,[p["source_candidate_ref"]])
            require(p["same_physical_instance"] is False,"INSTANCE_PROMOTION")
            z=a["payload"]
            if a["kind"]=="RecipeIngredientDraft":
                require(z["parent_ref"]["tag"]=="VALUE","RECIPE_PARENT_HOLD");parent=lookup(ix,z["parent_ref"]["value"])
                rule=recipe_policy(self.policy,self.ns(a),self.ns(parent));require(p["left_namespace"]==self.ns(a) and p["right_namespace"]==self.ns(parent) and p["rule"]=="BUSINESS_ID_AND_CODE","NAMESPACE_LINK_MISMATCH")
            else:
                l=lookup(ix,z["left_ref"]);r=lookup(ix,z["right_ref"]);rule=link_policy(self.policy,self.ns(l),self.ns(r),l["kind"],r["kind"],z["bindings"]["source_key"]["path"])
                require(p["left_namespace"]==self.ns(l) and p["right_namespace"]==self.ns(r) and p["rule"]==rule["rule"],"NAMESPACE_LINK_MISMATCH")
        elif k=="VocabularyAnchorDraft":
            a=lookup(ix,p["source_snapshot_ref"],"SourceSnapshotDraft");deps(o,[p["source_snapshot_ref"]]);prov(o,[p["source_snapshot_ref"]])
            require(a["payload"]["scope"]==p["scope"] and a["payload"]["sha256"]==p["artifact_sha256"],"ANCHOR_SNAPSHOT_MISMATCH")
        elif k=="NativeVocabularyRecord":
            a=lookup(ix,p["source_anchor_ref"],"VocabularyAnchorDraft");deps(o,[p["source_anchor_ref"],a["payload"]["source_snapshot_ref"]]);prov(o,[p["source_anchor_ref"]])
            b=a["payload"];require(p["native_key"]==b["native_key"] and p["artifact_sha256"]==b["artifact_sha256"] and p["source_locator"]==b["locator"] and p["native_namespace"]==b["scope"],"VOCAB_ANCHOR_MISMATCH")
        elif k=="SourceFamily":self.family_guard(o)
        elif k=="SourceFamilyBinding":
            n=lookup(ix,p["native_ref"],"NativeVocabularyRecord");f=lookup(ix,p["source_family_ref"],"SourceFamily");deps(o,[p["native_ref"],p["source_family_ref"]]);self.family_guard(f)
            a=n["payload"];b=f["payload"];require(a["native_namespace"]==b["carrier_scope"],"FAMILY_CARRIER_MISMATCH")
            if a["native_namespace"].startswith("nutridata:"):require(a["metadata"].get("source_label","")==b["reported_source_label"],"FAMILY_SOURCE_LABEL_MISMATCH")
        elif k=="AlignmentRecord":
            a=lookup(ix,p["source_ref"],"NativeVocabularyRecord");b=lookup(ix,p["target_ref"],"NativeVocabularyRecord");lookup(ix,p["method_version_ref"],"MappingMethod")
            deps(o,[p["source_ref"],p["target_ref"],p["method_version_ref"]]);prov(o,[a["payload"]["source_anchor_ref"],b["payload"]["source_anchor_ref"]])
            require(set(p["input_dependency_refs"])=={p["source_ref"],p["target_ref"]} and set(p["source_anchor_refs"])=={a["payload"]["source_anchor_ref"],b["payload"]["source_anchor_ref"]},"MAPPING_DEPENDENCY_MISMATCH")
            require(p["source_grain"]==a["payload"]["native_kind"] and p["target_grain"]==b["payload"]["native_kind"] and a["payload"]["native_namespace"]!=b["payload"]["native_namespace"],"MAPPING_NAMESPACE_GRAIN")
            require(p["direction"]=="SOURCE_RELATION_TO_TARGET" and p["relation_type"]==p["source_relation_to_target"]=="UNRESOLVED" and p["accepted_equivalence"] is False and p["physical_instance_link"] is False and p["review_status"]=="PENDING","UNREVIEWED_EQUIVALENCE")
        elif k=="ComponentConceptCandidate":
            a=lookup(ix,p["source_field_ref"],"ComponentNativeField");deps(o,[p["source_field_ref"]]);z=a["payload"]
            require(p["declared_label"]==z["native_name"] and p["native_unit"]==z["native_unit"],"COMPONENT_SOURCE_DRIFT")
            require(p["prior_u2b_component_id"]==component_prior(self.policy,z["native_name"],z["native_unit"]),"COMPONENT_PRIOR_UNIT_MISMATCH")
            require(p["global_exact"] is False and p["review_status"]=="PENDING","COMPONENT_PROMOTION")
        elif k=="ComponentAlignmentCandidate":
            a=lookup(ix,p["source_ref"],"ComponentNativeField");b=lookup(ix,p["target_ref"],"ComponentNativeField");lookup(ix,p["method_version_ref"],"MappingMethod")
            deps(o,[p["source_ref"],p["target_ref"],p["method_version_ref"]])
            require(p["source_unit"]==a["payload"]["native_unit"] and p["target_unit"]==b["payload"]["native_unit"],"COMPONENT_UNIT_DRIFT")
            require(p["accepted_equivalence"] is False and p["conversion"]=="NOT_AUTHORIZED" and p["measurement_qualification"]=="HOLD","COMPONENT_PROMOTION")
        elif k=="CanonicalFoodConceptCandidate":
            lookup(ix,p["seed_native_ref"],"NativeVocabularyRecord");deps(o,[p["seed_native_ref"]]);require(p["equivalence_class"]=="NOT_ASSIGNED","CANONICAL_PROMOTION")
        elif k=="FNDDSCarrierCrosswalk":
            a=lookup(ix,p["ars_ref"],"NativeVocabularyRecord")["payload"];b=lookup(ix,p["fdc_ref"],"NativeVocabularyRecord")["payload"];deps(o,[p["ars_ref"],p["fdc_ref"]])
            require(p["cycle"]=="2015-16" and a["native_key"]==b["native_key"]==p["food_code"] and a["native_label"].strip()==b["native_label"].strip(),"FNDDS_CODE_CARRIER_CONFLICT")
            require(p["same_release_not_independent"] and not p["semantic_equivalence_accepted"],"CARRIER_INDEPENDENCE_INFLATION")
        elif k=="NativeCodeLinkCandidate":
            require(p["target_cycle"]=="2015-16" and p["same_physical_instance"] is False and p["measurement_and_aggregation"]=="HOLD","FNDDS_CYCLE_OR_GRAIN")
            if p["status"]=="SAME_CYCLE_CODE_MATCH_CANDIDATE":
                a=lookup(ix,p["target_ars_ref"],"NativeVocabularyRecord")["payload"];b=lookup(ix,p["target_fdc_ref"],"NativeVocabularyRecord")["payload"]
                deps(o,[p["target_ars_ref"],p["target_fdc_ref"]]);require(re.fullmatch(r"[0-9]{8}",p["native_code"]) and a["native_key"]==b["native_key"]==p["native_code"] and a["native_label"].strip()==b["native_label"].strip(),"FNDDS_CODE_CARRIER_CONFLICT")
            elif p["status"]=="HOLD_CODE_DOMAIN_UNRESOLVED":require(p["target_ars_ref"] is None and p["target_fdc_ref"] is None,"SHORT_CODE_JOIN")
        return True
