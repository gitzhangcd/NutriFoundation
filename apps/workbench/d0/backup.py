"""Consistent offline snapshots of synthetic data; restore only to a new path.

Stop the single application worker first. Account/session files live outside
this data root, so backup does not copy passwords or revive sessions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import io
import tarfile
import tempfile
from pathlib import Path


def checksum(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def backup(root:Path,destination:Path,*,offline:bool=False)->Path:
    if offline is not True:raise RuntimeError('OFFLINE_REQUIRED_STOP_ALL_WRITERS')
    root=Path(root).resolve();destination=Path(destination)
    if not root.is_dir() or not any(p.is_file() for p in root.rglob('*')):raise RuntimeError('BACKUP_SOURCE_REQUIRED')
    if root==destination.resolve() or root in destination.resolve().parents:raise RuntimeError('BACKUP_MUST_BE_OUTSIDE_DATA_ROOT')
    destination.mkdir(mode=0o700,parents=True,exist_ok=False)
    for source in sorted(root.rglob('*')):
        if source.is_symlink():raise RuntimeError('BACKUP_SYMLINK_FORBIDDEN')
        relative=source.relative_to(root);target=destination/relative
        if source.is_dir():target.mkdir(exist_ok=True,mode=0o700);continue
        if source.name.endswith(('-wal','-shm','-journal')):continue
        if source.suffix in ('.sqlite','.sqlite3','.db'):
            with sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True) as incoming,sqlite3.connect(target) as outgoing:
                incoming.backup(outgoing)
                if outgoing.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('SQLITE_INTEGRITY_FAILURE')
        else:shutil.copyfile(source,target)
        target.chmod(0o600)
    files={str(p.relative_to(destination)):checksum(p) for p in sorted(destination.rglob('*')) if p.is_file()}
    manifest=destination/'manifest.json'
    manifest.write_text(json.dumps({'mode':'SYNTHETIC_OFFLINE_BACKUP','files':files},indent=2)+'\n')
    manifest.chmod(0o600)
    return destination

def restore(snapshot:Path,destination:Path):
    snapshot=Path(snapshot).resolve();destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    manifest=json.loads((snapshot/'manifest.json').read_text())
    actual={str(p.relative_to(snapshot)) for p in snapshot.rglob('*') if p.is_file() and p.name!='manifest.json'}
    if actual!=set(manifest['files']):raise RuntimeError('BACKUP_INTEGRITY_FILE_SET')
    for relative,expected in manifest['files'].items():
        p=snapshot/relative
        if p.is_symlink() or snapshot not in p.resolve().parents or checksum(p)!=expected:raise RuntimeError('BACKUP_INTEGRITY_SHA256')
    destination.mkdir(mode=0o700,parents=True)
    for relative in manifest['files']:
        source=snapshot/relative;target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        shutil.copyfile(source,target);target.chmod(0o600)
        if target.suffix in ('.sqlite','.sqlite3','.db'):
            with sqlite3.connect(target) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('RESTORE_SQLITE_INTEGRITY')

def seal_backup(snapshot:Path,destination:Path,key:bytes)->Path:
    from cryptography.fernet import Fernet
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as tar:
        tar.add(snapshot,arcname='snapshot')
    destination=Path(destination)
    with destination.open('xb') as f:f.write(Fernet(key).encrypt(stream.getvalue()))
    destination.chmod(0o600)
    return destination

def open_backup(sealed:Path,destination:Path,key:bytes):
    from cryptography.fernet import Fernet
    payload=Fernet(key).decrypt(Path(sealed).read_bytes())
    with tempfile.TemporaryDirectory(prefix='nutri-backup-verify-') as td:
        with tarfile.open(fileobj=io.BytesIO(payload),mode='r:gz') as tar:
            for member in tar.getmembers():
                if member.name.startswith('/') or '..' in Path(member.name).parts or not (member.isfile() or member.isdir()):
                    raise RuntimeError('BACKUP_ARCHIVE_UNSAFE')
            tar.extractall(td,filter='data')
        restore(Path(td)/'snapshot',destination)

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('action',choices=['backup','restore']);p.add_argument('source',type=Path);p.add_argument('destination',type=Path);p.add_argument('--offline',action='store_true')
    a=p.parse_args()
    if a.action=='backup':backup(a.source,a.destination,offline=a.offline)
    else:restore(a.source,a.destination)
    print(a.action.upper()+'_VERIFIED')
if __name__=='__main__':main()
