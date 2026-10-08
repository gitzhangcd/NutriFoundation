"""Immutable Git-blob-bound NDS-R1 adapter; no silent workpack migration."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

BASE_SHA = '2259fdac9502541909a70d5d79c3460cecb6f657'
PINNED = {
    'runs/NDS/R1/P0/Role_Input_Surface_Contract_v0.1.json':'6ff4acdd45ba0d750ad362f41cdf1f817fc1bb47',
    'runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json':'ba43d882ac85bd63c61c008ee8ddddc6f787d36c',
    'runs/NDS/R1/P0.1/Judgment_Freeze_Contract_v0.1.json':'adcf4f3c1a67354bf26438f53b6ab585d941f9d5',
    'runs/NDS/R1/P0.1/Expert_Slot_Binding_Registry_v0.1.json':'2c4eac75204d0a6f9b3283d6561bb82837f680e2',
    'runs/NDS/R1/P0.1/Expert_Qualification_Instance_Registry_v0.1.json':'0ddcd6f9672fb78109db4f49fa6e3e3683034e63',
    'runs/NDS/R1/P0/Reconciliation_Exposure_Templates_v0.1.json':'b69d2987f88b073927f21f82ad6685496473f09a',
    'runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json':'a38d000f9962dac35e00d407f1d984721bc031ef',
    'runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.2.json':'4cbf9830e1f6b02c0414374fd4c964141ea59974',
    'runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.2.json':'3f0a06daa90562b79660d8423e5832caf20ff289',
    'runs/NDS/R1/P0.1/R1_AgentFirst_Verification_HoldPack_v0.1.json':'02bffb41358666a02f6eb46aaa79c5ca94eaae23',
}
CASE_REF='D2-NHANES-L-0001:r3'
SCIENTIFIC_PACKET='runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json'

def blob_sha(data:bytes)->str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

class ContractError(RuntimeError): pass

class ScientificAdapter:
    def __init__(self, repo_root:Path, *, test_authority:dict|None=None):
        self.test_authority=test_authority is not None
        if test_authority is not None:
            # TEST-ONLY isolated injected fixtures; never accepted as authoritative runtime.
            self.docs=test_authority
        else:
            self.docs={}
            for relative,expected in PINNED.items():
                data=(Path(repo_root)/relative).read_bytes()
                if blob_sha(data)!=expected:
                    raise ContractError('SCIENTIFIC_BLOB_MISMATCH:'+relative)
                self.docs[relative]=json.loads(data)
        self._validate()

    def by(self,filename:str)->dict:
        found=[v for k,v in self.docs.items() if k.endswith('/'+filename)]
        if len(found)!=1:raise ContractError('MISSING_OR_DUPLICATE_CONTRACT:'+filename)
        return found[0]

    def _validate(self)->None:
        role=self.by('Role_Input_Surface_Contract_v0.1.json')
        lock=self.by('Exposure_Lock_Registry_v0.1.json')
        freeze=self.by('Judgment_Freeze_Contract_v0.1.json')
        r0=self.by('R0_Human_DeNovo_Workpack_v0.2.json')
        r2=self.by('R2_PreAI_Workpack_v0.2.json')
        r1=self.by('R1_AgentFirst_Verification_HoldPack_v0.1.json')
        packet=self.by('Human_Baseline_Source_Packet_v0.2.json')
        slots=self.by('Expert_Slot_Binding_Registry_v0.1.json')
        if role.get('status')!='FROZEN' or lock.get('status')!='FROZEN' or freeze.get('status')!='FROZEN':
            raise ContractError('NOT_FROZEN')
        for v in (role,lock,r0,r2,r1,packet,slots):
            if v.get('case_ref')!=CASE_REF:raise ContractError('CASE_REF_MISMATCH')
        if [x['workflow'] for x in lock['locks']]!=['R0','R1','R2']:
            raise ContractError('EXPOSURE_LOCK_SEMANTIC_DELTA')
        if lock['locks'][0]['state']!='PERMANENT_NO_AGENT_EXPOSURE' or lock['locks'][2]['state']!='HARD_LOCK_AGENT_UNTIL_J_PREAI_FREEZE':
            raise ContractError('EXPOSURE_LOCK_SEMANTIC_DELTA')
        if 'AGENT_CANDIDATE_SET' not in role['arm_surfaces']['R1']['expert_initial'] or 'FROZEN_J_PREAI' not in role['arm_surfaces']['R2']['expert_post_ai']:
            raise ContractError('ROLE_PROJECTION_SEMANTIC_DELTA')
        target={t['workflow']:t for t in freeze['freeze_targets']}
        if set(target)!={'R0','R2'} or target['R2']['target']!='J_preAI' or target['R0']['target']!='J_human_de_novo':
            raise ContractError('FREEZE_TARGET_DELTA')
        # Explicit, reviewed v0.1 path -> v0.2 payload binding; never rewriting upstream.
        for arm,pack in [('R0',r0),('R2',r2)]:
            original=target[arm]['source_workpack']
            if not original.endswith('_v0.1.json') or pack.get('supersedes')!=original:
                raise ContractError('BLOCK_CONTRACT_CONFLICT:'+arm)
        if r0['response']!=r2['J_preAI'] or len(r0['response']['reference_set'])!=7:
            raise ContractError('RESPONSE_PAYLOAD_CONFLICT')
        if r0['input_surface']!=r2['input_surface']:
            raise ContractError('R0_R2_SOURCE_INEQUALITY')
        for arm,slot in [('R0','EXP-R1P0-A'),('R1','EXP-R1P0-B'),('R2','EXP-R1P0-C')]:
            matches=[v for v in slots['slots'] if v['workflow']==arm]
            if len(matches)!=1 or matches[0]['expert_slot']!=slot or matches[0]['identity_status']!='UNBOUND':
                raise ContractError('EXPERT_SLOT_DELTA')
        self.response_schema=r0['response']
        self.case_view=r0['input_surface']['visible_case']
        self.source_packet=packet
        self.packet_identity=hashlib.sha256(json.dumps(packet,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        self.slots={'R0':'EXP-R1P0-A','R1':'EXP-R1P0-B','R2':'EXP-R1P0-C'}

    def human_projection(self)->dict:
        packet=self.source_packet
        # Only explicit, bounded source entries; do not include SRS synthesis/labels.
        return {'case_ref':CASE_REF,'case_view':self.case_view,
                'source_packet_id':packet['packet_id'],'source_packet_digest':self.packet_identity,
                'scientific_sources':packet['scientific_sources'],
                'synthetic_engineering':True}
