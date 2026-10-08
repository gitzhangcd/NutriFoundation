from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from old_c2_fixtures import fake_authority
from authority import ScientificAdapter

@pytest.fixture
def adapter():return ScientificAdapter(Path('.'),test_authority=fake_authority())
