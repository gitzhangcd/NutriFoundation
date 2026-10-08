from pathlib import Path
import pytest
from authority import ScientificAdapter,PINNED,blob_sha,ContractError

def test_exact_real_scientific_contract_binding():
    repo=Path(__file__).resolve().parents[4]
    required=repo/'runs/NDS/R1/P0.1/Judgment_Freeze_Contract_v0.1.json'
    if not required.is_file():pytest.skip('Isolated artifact test; checked again in GitHub full checkout')
    a=ScientificAdapter(repo)
    assert len(a.docs)==10
    assert a.by('R2_PreAI_Workpack_v0.2.json')['version']=='v0.2'
    assert a.slots['R2']=='EXP-R1P0-C'
    assert a.response_schema==a.by('R2_PreAI_Workpack_v0.2.json')['J_preAI']

def test_real_contract_tamper_is_rejected(tmp_path):
    repo=Path(__file__).resolve().parents[4]
    required=repo/'runs/NDS/R1/P0.1/Judgment_Freeze_Contract_v0.1.json'
    if not required.is_file():pytest.skip('Isolated artifact test; checked again in GitHub full checkout')
    import shutil
    for rel in PINNED:
        dest=tmp_path/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(repo/rel,dest)
    modified=tmp_path/'runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json'
    modified.write_bytes(modified.read_bytes()+b' ')
    with pytest.raises(ContractError,match='SCIENTIFIC_BLOB_MISMATCH'):
        ScientificAdapter(tmp_path)