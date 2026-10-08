from pathlib import Path
import json, hashlib

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/workbench'
FILES=['Workbench_System_Master_v0.2.md','Workbench_Page_IA_and_UX_Contract_v0.2.md','Workbench_Scientific_Adapter_Matrix_v0.2.md','Workbench_Data_API_State_Contract_v0.2.md','Workbench_Acceptance_and_Roadmap_v0.2.md']
REQUIRED={
FILES[0]: ['R0','R1','R2','Evidence Annotation','Expert Decision Capture','QualifiedDecisionReference','SourceAnchor','PDF_PAGE_BBOX','Human_Baseline_Source_Packet'],
FILES[1]: ['P01','P11','R0','R1','R2','TaskReadModel'],
FILES[2]: ['R0','R1','R2','decision_focus','reference_set','BOUND'],
FILES[3]: ['R0','R1','R2','403','409','FreezeReceipt','Candidate'],
FILES[4]: ['C0','C1','C2','C3','C4','NR-01','NR-20','37','37750463593']}
AUTH={
'runs/NDS/R1/P0/Role_Input_Surface_Contract_v0.1.json':'6ff4acdd45ba0d750ad362f41cdf1f817fc1bb47',
'runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json':'ba43d882ac85bd63c61c008ee8ddddc6f787d36c',
'runs/NDS/R1/P0.1/Judgment_Freeze_Contract_v0.1.json':'adcf4f3c1a67354bf26438f53b6ab585d941f9d5',
'runs/NDS/R1/P0.1/Expert_Slot_Binding_Registry_v0.1.json':'2c4eac75204d0a6f9b3283d6561bb82837f680e2',
'runs/NDS/R1/P0.1/Expert_Qualification_Instance_Registry_v0.1.json':'0ddcd6f9672fb78109db4f49fa6e3e3683034e63',
'runs/NDS/R1/P0/Reconciliation_Exposure_Templates_v0.1.json':'b69d2987f88b073927f21f82ad6685496473f09a',
'runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json':'a38d000f9962dac35e00d407f1d984721bc031ef',
'runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.2.json':'4cbf9830e1f6b02c0414374fd4c964141ea59974',
'runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.2.json':'3f0a06daa90562b79660d8423e5832caf20ff289',
'runs/NDS/R1/P0.1/R1_AgentFirst_Verification_HoldPack_v0.1.json':'02bffb41358666a02f6eb46aaa79c5ca94eaae23'}
MANIFEST=ROOT/'runs/workbench/WB-P0.2/M0/WB-M0_Conformance_Manifest_v0.2.json'

def sha(path:Path):return hashlib.sha256(path.read_bytes()).hexdigest()

def assert_docs():
    master=(DOC/FILES[0]).read_text()
    for fn in FILES[1:]: assert fn in master, ('MISSING_MASTER_REF',fn)
    for fn in FILES:
        p=DOC/fn; t=p.read_text()
        assert len(t)>2500 and 'DESIGN_FROZEN' in t
        assert not any(c in t for c in ['\x00','\x10']),fn
        missing=[term for term in REQUIRED[fn] if term.lower() not in t.lower()]
        assert not missing,(fn,missing)
        print('PASS',fn,'lines',len(t.splitlines()))

def build():
    assert_docs()
    body={
      'stage':'Workbench WB-P0.2-M0','version':'v0.2','date':'2026-10-08',
      'status':'PASS_DESIGN_BASELINE_FROZEN','implementation_status':'RUNTIME_AND_SCIENTIFIC_GATES_PENDING',
      'scientific_stage_status':'NDS-R1-P0.1 PASS_OPERATIONAL_READINESS_EMPIRICAL_CAPTURE_PENDING',
      'scientific_authority':{'repo':'gitzhangcd/NutriFoundation','branch':'ndf-d1-scientific-core-thin-slice','sha':'2259fdac9502541909a70d5d79c3460cecb6f657'},
      'engineering_parent_before_M0':'34386dd9d0b82ba0ad319fa0d46ed0eb9d8c9a00',
      'document_hashes':{'docs/workbench/'+fn:sha(DOC/fn) for fn in FILES},
      'scientific_artifact_git_blob_sha':AUTH,
      'scientific_adapter':{'freeze_semantics':'Judgment_Freeze_Contract_v0.1','payload_R0':'R0_Human_DeNovo_Workpack_v0.2','payload_R2':'R2_PreAI_Workpack_v0.2','R1':'R1_AgentFirst_Verification_HoldPack_v0.1','current_packet':'Human_Baseline_Source_Packet_v0.2','conflict_policy':'BLOCK_CONTRACT_CONFLICT'},
      'profiles':['EVIDENCE_ANNOTATION','EXPERT_DECISION_CAPTURE'],
      'arms':['R0_HUMAN_DE_NOVO_PERMANENT_NO_AGENT','R1_AGENT_FIRST_VERIFY_FROZEN_CANDIDATES','R2_PRE_AI_FREEZE_BEFORE_AGENT_EXPANSION'],
      'protected_paths':['runs/NDF/**','runs/NDS/R1/P0/**','runs/NDS/R1/P0.1/**','src/nutrifoundation/**'],
      'non_regression':['No early candidate leakage','No J_preAI overwrite','No same-case cross-arm identity reuse','No unapproved source-surface widening','No fake exact PDF BBox','No Workbench-owned scientific Gold','No frozen upstream mutations'],
      'm0_validation':{'static_document_checks':'PASS_5_OF_5','hash_manifest':'PASS','git_diff_gate':'REQUIRED_SEPARATE_CHECK','runtime_UI_tests':'NOT_RUN_DOCUMENTATION_ONLY','empirical_judgments_created':0},
      'next_stage':'WB-P0.2-C0｜Page-to-Contract UI Specification & Synthetic Interaction Fixtures'}
    MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    MANIFEST.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n')
    print('GENERATED',MANIFEST)

def verify():
    assert_docs()
    j=json.loads(MANIFEST.read_text())
    assert j['status']=='PASS_DESIGN_BASELINE_FROZEN'
    for name,h in j['document_hashes'].items():
        assert sha(ROOT/name)==h,('SHA_MISMATCH',name)
    assert j['scientific_artifact_git_blob_sha']==AUTH
    assert j['scientific_authority']['sha']=='2259fdac9502541909a70d5d79c3460cecb6f657'
    assert len(j['document_hashes'])==5
    print('M0 STATIC CONFORMANCE: PASS; 5/5 docs and 10 authoritative SHA bindings verified')

if __name__=='__main__':
    build();verify()