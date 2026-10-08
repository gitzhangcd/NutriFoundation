from pathlib import Path
import pytest
from authority import ScientificAdapter
from source_packet import compare_r0_r2,view_binding_check
from gates import assess
REPO=Path(__file__).resolve().parents[4]

@pytest.mark.skipif(not (REPO/'runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json').exists(),reason='isolated local checkout; full git checkout must execute')
def test_official_ten_blob_source_packet():
    adapter=ScientificAdapter(REPO)
    model=compare_r0_r2(adapter)
    assert len(model['sources'])==6
    assert model['case_ref']=='D2-NHANES-L-0001:r3'
    assert all(s['representation'].startswith('FROZEN_BOUNDED') for s in model['sources'])

@pytest.mark.skipif(not (REPO/'runs/NDF/D2/Case_0001/Materialized_Projection_Views_v0.2.json').exists(),reason='isolated local checkout; full git checkout must execute')
def test_case_projection_ref_discrepancy_is_blocked():
    checked=view_binding_check(REPO)
    assert checked['referenced_case_ref']=='D2-NHANES-L-0001:r2'
    assert checked['target_workpack_case_ref']=='D2-NHANES-L-0001:r3'
    assert checked['decision']=='BLOCK_REQUIRES_SCIENTIFIC_OWNER_RECONCILIATION'
    result=assess(REPO)
    assert result['formal_NDS_R1_experiment'].startswith('NO_GO')
