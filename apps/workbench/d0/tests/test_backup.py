import sqlite3
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backup import backup,restore

def test_backup_requires_quiescence_and_restore_integrity(tmp_path):
    root=tmp_path/'data';root.mkdir()
    with sqlite3.connect(root/'c2_synthetic.sqlite') as db:
        db.execute('CREATE TABLE drafts(value TEXT)');db.execute("INSERT INTO drafts VALUES('synthetic saved judgment')")
    sources=root/'sources';sources.mkdir();(sources/'original.pdf').write_bytes(b'%PDF-synthetic')
    with pytest.raises(RuntimeError,match='OFFLINE_REQUIRED'):backup(root,tmp_path/'bad',offline=False)
    dest=backup(root,tmp_path/'backup',offline=True)
    assert (dest/'manifest.json').exists()
    restore(dest,tmp_path/'restored')
    with sqlite3.connect(tmp_path/'restored/c2_synthetic.sqlite') as db:
        assert db.execute('SELECT value FROM drafts').fetchone()[0]=='synthetic saved judgment'
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert (tmp_path/'restored/sources/original.pdf').read_bytes()==b'%PDF-synthetic'
    with pytest.raises(FileExistsError):restore(dest,tmp_path/'restored')
    (dest/'sources/original.pdf').write_bytes(b'corrupted')
    with pytest.raises(RuntimeError,match='BACKUP_INTEGRITY'):restore(dest,tmp_path/'corrupt')

def test_encrypted_backup_roundtrip_and_tamper(tmp_path):
    from cryptography.fernet import Fernet,InvalidToken
    import backup
    source=tmp_path/'source';source.mkdir();(source/'fixture.txt').write_text('synthetic only')
    snapshot=backup.backup(source,tmp_path/'snapshot',offline=True)
    key=Fernet.generate_key()
    assert hasattr(backup,'seal_backup'), 'encrypted backup support required'
    sealed=backup.seal_backup(snapshot,tmp_path/'backup.fernet',key)
    assert b'synthetic only' not in sealed.read_bytes()
    backup.open_backup(sealed,tmp_path/'restored',key)
    assert (tmp_path/'restored/fixture.txt').read_text()=='synthetic only'
    blob=bytearray(sealed.read_bytes());blob[25]^=1;sealed.write_bytes(blob)
    with pytest.raises(InvalidToken):backup.open_backup(sealed,tmp_path/'tampered',key)

def test_missing_and_empty_root_never_report_success(tmp_path):
    import backup
    with pytest.raises(RuntimeError,match='BACKUP_SOURCE_REQUIRED'):
        backup.backup(tmp_path/'missing',tmp_path/'missing-backup',offline=True)
    empty=tmp_path/'empty';empty.mkdir()
    with pytest.raises(RuntimeError,match='BACKUP_SOURCE_REQUIRED'):
        backup.backup(empty,tmp_path/'empty-backup',offline=True)
