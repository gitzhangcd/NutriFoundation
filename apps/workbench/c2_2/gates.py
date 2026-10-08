"""Readiness gate: independent evidence needed; untrusted checkboxes never turn it green."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from authority import ScientificAdapter
from source_packet import compare_r0_r2,view_binding_check

# These are external controls, not self-declarations accepted from an HTTP request.
EXTERNAL_RECEIPTS={
 'IDENTITY_PROVIDER_PRODUCTION_CONFIGURATION':'Verified IdP keys, audience, MFA and trusted token handling',
 'REAL_EXPERT_CREDENTIALS_QUALIFIED':'Reviewer-verified professional license/role and expertise, no sham identity',
 'EXPERT_PRIOR_EXPOSURE_AND_ARM_BINDING':'Signed screen and same-case cross-arm exclusion',
 'IRB_ETHICS_CONSENT_APPLICABILITY':'Research governance determination, informed consent and study approval where applicable',
 'SOURCE_SNAPSHOT_AND_RIGHTS':'Version-specific source excerpts, copyright/license, permission and date proof',
 'SOURCE_CASE_VIEW_R3_RECONCILIATION':'Scientific owner resolution of r2 referenced view versus r3 active workpacks',
 'DEPLOYMENT_SECURITY_AND_PRIVACY':'Production pen test, TLS, backup/recovery, data retention/privacy and logging controls',
 'RESEARCH_SEPARATION_FROM_USABILITY':'Separate UX synthetic cases/participants and formal scientific R0/R1/R2 eligibility'
}

def assess(repo_root:Path,external_receipts:dict|None=None)->dict:
    a=ScientificAdapter(repo_root)
    human=compare_r0_r2(a)
    conflict=view_binding_check(repo_root)
    # No self-attested web form can qualify a real deployment. A future gate
    # must integrate cryptographically signed independent receipts and policy.
    pending=[{'gate':k,'status':'PENDING_INDEPENDENT_EVIDENCE','requirement':v} for k,v in EXTERNAL_RECEIPTS.items()]
    if conflict['same_case_ref'] is False:
        pending[5]['status']='BLOCK_UPSTREAM_SCIENTIFIC_VERSION_CONFLICT'
    # For C2.2 never accept any caller-supplied positive statuses as proof.
    return {'stage':'WB-P0.2-C2.2','authority':'PINNED_10_NDS_BLOBS',
      'scientific_case_ref':human['case_ref'],'scientific_source_packet_id':human['source_packet_id'],
      'source_count':len(human['sources']),'R0_R2_shared_packet_sha256':human['projection_sha256'],
      'fulltext_qualified':False,'bounded_projection_contract':'PASS',
      'case_projection_binding':conflict,
      'external_requirements':pending,
      'engineering_prototype':'CAN_TEST_SYNTHETIC_WITHOUT_HUMAN_CAPTURE',
      'real_person_ux_pilot':'NO_GO_PENDING_IDENTITY_ETHICS_DEPLOYMENT_EVIDENCE',
      'formal_NDS_R1_experiment':'NO_GO_EMPIRICAL_CAPTURE_PENDING',
      'real_expert_bindings_created':0,'real_j_preai_created':0,
      'warning':'Do not upload an extra 5:2 paper, fetch full website HTML or infer case-specific labels into this R0/R2 projection.'}
